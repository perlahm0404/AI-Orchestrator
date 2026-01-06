"""
Circuit Breaker

Auto-halt after repeated failures to prevent runaway agents.

Configuration:
- failure_threshold: Number of failures before tripping (default: 3)
- reset_timeout: Time before auto-reset (default: 30 minutes)
- half_open_requests: Test requests before full reset (default: 1)

States:
- CLOSED: Normal operation, failures counted
- OPEN: Halted, all requests blocked
- HALF_OPEN: Testing if system recovered

Implementation: Phase 0
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Halted
    HALF_OPEN = "HALF_OPEN" # Testing recovery


@dataclass
class CircuitBreaker:
    """
    Circuit breaker instance.

    Each agent/project combination has its own circuit breaker.
    """
    agent: str
    project: str
    state: CircuitState
    failure_count: int
    last_failure_at: datetime | None
    opened_at: datetime | None

    failure_threshold: int = 3
    reset_timeout: timedelta = timedelta(minutes=30)


def get_circuit(agent: str, project: str) -> CircuitBreaker:
    """
    Get circuit breaker for agent/project.

    Creates if not exists.
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Circuit breaker not yet implemented")


def record_failure(agent: str, project: str, error: str) -> CircuitState:
    """
    Record a failure and potentially trip the circuit.

    Returns:
        New circuit state
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Circuit breaker not yet implemented")


def record_success(agent: str, project: str) -> CircuitState:
    """
    Record a success, potentially resetting the circuit.

    Returns:
        New circuit state
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Circuit breaker not yet implemented")


def can_proceed(agent: str, project: str) -> bool:
    """
    Check if agent can proceed (circuit not open).

    Returns:
        True if allowed, False if blocked
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Circuit breaker not yet implemented")
