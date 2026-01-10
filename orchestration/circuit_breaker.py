"""
Circuit Breaker Module

Provides circuit breakers for:
1. General agent failure protection (CircuitBreaker)
2. Lambda invocation cost control (LambdaCircuitBreaker)

ADR-003: Lambda Cost Controls and Agentic Workflow Guardrails

Configuration:
- failure_threshold: Number of failures before tripping (default: 3)
- reset_timeout: Time before auto-reset (default: 30 minutes)
- max_calls_per_session: Lambda calls before tripping (default: 100)

States:
- CLOSED: Normal operation, failures/calls counted
- OPEN: Halted, all requests blocked
- HALF_OPEN: Testing if system recovered

Kill Switch Integration:
- Respects AI_BRAIN_MODE environment variable
- OFF/PAUSED = circuit always open
- NORMAL = normal operation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
import threading
import os
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Halted
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerTripped(Exception):
    """Raised when circuit breaker is tripped."""

    def __init__(self, breaker_type: str, reason: str, call_count: int = 0, limit: int = 0):
        self.breaker_type = breaker_type
        self.reason = reason
        self.call_count = call_count
        self.limit = limit
        super().__init__(f"{breaker_type} circuit breaker tripped: {reason}")


class KillSwitchActive(Exception):
    """Raised when kill switch is active (AI_BRAIN_MODE=OFF or PAUSED)."""

    def __init__(self, mode: str):
        self.mode = mode
        super().__init__(f"Kill switch active: AI_BRAIN_MODE={mode}")


# ═══════════════════════════════════════════════════════════════════════════════
# GENERAL CIRCUIT BREAKER (Failure-based)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CircuitBreaker:
    """
    Circuit breaker for general agent failure protection.

    Each agent/project combination has its own circuit breaker.
    Trips after consecutive failures, auto-resets after timeout.
    """
    agent: str
    project: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None

    failure_threshold: int = 3
    reset_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    half_open_success_threshold: int = 1

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record_failure(self, error: str = "") -> CircuitState:
        """Record a failure and potentially trip the circuit."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_at = datetime.now()
            self.success_count = 0

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.opened_at = datetime.now()
                logger.warning(
                    f"Circuit OPEN for {self.agent}/{self.project}: "
                    f"{self.failure_count} failures. Error: {error}"
                )

            return self.state

    def record_success(self) -> CircuitState:
        """Record a success, potentially resetting the circuit."""
        with self._lock:
            self.success_count += 1

            if self.state == CircuitState.HALF_OPEN:
                if self.success_count >= self.half_open_success_threshold:
                    self._reset()
                    logger.info(f"Circuit CLOSED for {self.agent}/{self.project}: recovered")
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

            return self.state

    def can_proceed(self) -> bool:
        """Check if agent can proceed (circuit not open)."""
        with self._lock:
            # Check for auto-reset
            if self.state == CircuitState.OPEN and self.opened_at:
                if datetime.now() - self.opened_at > self.reset_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit HALF_OPEN for {self.agent}/{self.project}: testing")

            return self.state != CircuitState.OPEN

    def _reset(self) -> None:
        """Reset circuit to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_at = None
        self.opened_at = None


# Circuit breaker registry
_circuit_registry: Dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit(agent: str, project: str) -> CircuitBreaker:
    """Get or create circuit breaker for agent/project."""
    key = f"{agent}:{project}"
    with _registry_lock:
        if key not in _circuit_registry:
            _circuit_registry[key] = CircuitBreaker(agent=agent, project=project)
        return _circuit_registry[key]


def record_failure(agent: str, project: str, error: str) -> CircuitState:
    """Record a failure and potentially trip the circuit."""
    return get_circuit(agent, project).record_failure(error)


def record_success(agent: str, project: str) -> CircuitState:
    """Record a success, potentially resetting the circuit."""
    return get_circuit(agent, project).record_success()


def can_proceed(agent: str, project: str) -> bool:
    """Check if agent can proceed (circuit not open)."""
    return get_circuit(agent, project).can_proceed()


# ═══════════════════════════════════════════════════════════════════════════════
# LAMBDA CIRCUIT BREAKER (Call-count based)
# ADR-003: Lambda Cost Controls
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LambdaCircuitBreaker:
    """
    Circuit breaker for Lambda invocation cost control.

    Tracks Lambda calls per session and trips when limit exceeded.
    Integrates with AI Orchestrator kill switch (AI_BRAIN_MODE).

    Usage:
        breaker = LambdaCircuitBreaker(max_calls=100)

        # Before each Lambda call
        breaker.check()  # Raises if tripped or kill switch active

        # After successful call
        breaker.record_call("function-name")

        # Or use context manager
        with breaker.guard("function-name"):
            lambda_client.invoke(...)

    ADR-003 Implementation:
    - TASK-003-004: This class
    - TASK-003-005: Integration with orchestration
    """

    max_calls_per_session: int = 100
    session_id: str = ""

    # Internal state
    _call_count: int = field(default=0, repr=False)
    _call_history: list = field(default_factory=list, repr=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _tripped_at: Optional[datetime] = field(default=None, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self):
        """Initialize session ID if not provided."""
        if not self.session_id:
            self.session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    @property
    def call_count(self) -> int:
        """Current call count (thread-safe)."""
        with self._lock:
            return self._call_count

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        with self._lock:
            return self._state

    @property
    def is_tripped(self) -> bool:
        """Check if circuit is tripped."""
        return self._state == CircuitState.OPEN

    @property
    def remaining_calls(self) -> int:
        """Number of remaining calls before trip."""
        with self._lock:
            return max(0, self.max_calls_per_session - self._call_count)

    def check_kill_switch(self) -> None:
        """
        Check if kill switch is active.

        Raises:
            KillSwitchActive: If AI_BRAIN_MODE is OFF or PAUSED
        """
        mode = os.environ.get("AI_BRAIN_MODE", "NORMAL").upper()
        if mode in ("OFF", "PAUSED"):
            logger.warning(f"Kill switch active: AI_BRAIN_MODE={mode}")
            raise KillSwitchActive(mode)

    def check(self) -> None:
        """
        Check if Lambda call is allowed.

        Call this BEFORE making a Lambda invocation.

        Raises:
            KillSwitchActive: If kill switch is active
            CircuitBreakerTripped: If call limit exceeded
        """
        # Check kill switch first
        self.check_kill_switch()

        # Check circuit state
        with self._lock:
            if self._state == CircuitState.OPEN:
                raise CircuitBreakerTripped(
                    breaker_type="Lambda",
                    reason=f"Call limit exceeded ({self._call_count}/{self.max_calls_per_session})",
                    call_count=self._call_count,
                    limit=self.max_calls_per_session
                )

    def record_call(self, function_name: str = "", success: bool = True) -> int:
        """
        Record a Lambda call.

        Call this AFTER making a Lambda invocation.

        Args:
            function_name: Name of Lambda function called
            success: Whether the call succeeded

        Returns:
            Current call count

        Raises:
            CircuitBreakerTripped: If this call trips the circuit
        """
        with self._lock:
            self._call_count += 1
            self._call_history.append({
                "function": function_name,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "call_number": self._call_count
            })

            # Check if we should trip
            if self._call_count >= self.max_calls_per_session:
                self._state = CircuitState.OPEN
                self._tripped_at = datetime.now()

                logger.warning(
                    f"Lambda circuit breaker TRIPPED: "
                    f"{self._call_count}/{self.max_calls_per_session} calls. "
                    f"Session: {self.session_id}"
                )

                raise CircuitBreakerTripped(
                    breaker_type="Lambda",
                    reason=f"Session limit reached ({self._call_count} calls)",
                    call_count=self._call_count,
                    limit=self.max_calls_per_session
                )

            # Log progress at intervals
            if self._call_count % 25 == 0:
                # Compute remaining inline to avoid nested lock acquisition
                remaining = max(0, self.max_calls_per_session - self._call_count)
                logger.info(
                    f"Lambda calls: {self._call_count}/{self.max_calls_per_session} "
                    f"({remaining} remaining)"
                )

            return self._call_count

    def guard(self, function_name: str = ""):
        """
        Context manager for guarded Lambda calls.

        Usage:
            with breaker.guard("my-function"):
                response = lambda_client.invoke(FunctionName="my-function", ...)
        """
        return _LambdaCallGuard(self, function_name)

    def reset(self) -> None:
        """Reset circuit breaker (for new session)."""
        with self._lock:
            self._call_count = 0
            self._call_history = []
            self._state = CircuitState.CLOSED
            self._tripped_at = None
            self.session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        logger.info(f"Lambda circuit breaker reset. New session: {self.session_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            # Compute remaining inline to avoid nested lock acquisition
            remaining = max(0, self.max_calls_per_session - self._call_count)
            return {
                "session_id": self.session_id,
                "state": self._state.value,
                "call_count": self._call_count,
                "max_calls": self.max_calls_per_session,
                "remaining": remaining,
                "tripped_at": self._tripped_at.isoformat() if self._tripped_at else None,
                "recent_calls": self._call_history[-10:] if self._call_history else []
            }


class _LambdaCallGuard:
    """Context manager for guarded Lambda calls."""

    def __init__(self, breaker: LambdaCircuitBreaker, function_name: str):
        self.breaker = breaker
        self.function_name = function_name
        self.success = True

    def __enter__(self):
        self.breaker.check()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ARG002
        self.success = exc_type is None
        try:
            self.breaker.record_call(self.function_name, self.success)
        except CircuitBreakerTripped:
            # Re-raise circuit breaker exception
            raise
        return False  # Don't suppress other exceptions


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE FOR ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

# Global Lambda circuit breaker for the current session
_lambda_breaker: Optional[LambdaCircuitBreaker] = None
_lambda_breaker_lock = threading.Lock()


def get_lambda_breaker(max_calls: int = 100) -> LambdaCircuitBreaker:
    """
    Get the global Lambda circuit breaker instance.

    Creates a new instance if none exists.

    Args:
        max_calls: Maximum calls per session (only used on creation)

    Returns:
        LambdaCircuitBreaker instance
    """
    global _lambda_breaker
    with _lambda_breaker_lock:
        if _lambda_breaker is None:
            _lambda_breaker = LambdaCircuitBreaker(max_calls_per_session=max_calls)
            logger.info(
                f"Created Lambda circuit breaker: "
                f"max_calls={max_calls}, session={_lambda_breaker.session_id}"
            )
        return _lambda_breaker


def reset_lambda_breaker(max_calls: int = 100) -> LambdaCircuitBreaker:
    """
    Reset the global Lambda circuit breaker for a new session.

    Args:
        max_calls: Maximum calls for new session

    Returns:
        Fresh LambdaCircuitBreaker instance
    """
    global _lambda_breaker
    with _lambda_breaker_lock:
        _lambda_breaker = LambdaCircuitBreaker(max_calls_per_session=max_calls)
        logger.info(
            f"Reset Lambda circuit breaker: "
            f"max_calls={max_calls}, session={_lambda_breaker.session_id}"
        )
        return _lambda_breaker


def check_lambda_allowed() -> None:
    """
    Check if Lambda call is allowed (convenience function).

    Raises:
        KillSwitchActive: If kill switch is active
        CircuitBreakerTripped: If call limit exceeded
    """
    get_lambda_breaker().check()


def record_lambda_call(function_name: str = "", success: bool = True) -> int:
    """
    Record a Lambda call (convenience function).

    Returns:
        Current call count
    """
    return get_lambda_breaker().record_call(function_name, success)


def lambda_guard(function_name: str = ""):
    """
    Context manager for guarded Lambda calls (convenience function).

    Usage:
        with lambda_guard("my-function"):
            response = lambda_client.invoke(...)
    """
    return get_lambda_breaker().guard(function_name)
