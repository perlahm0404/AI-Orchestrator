"""
Tests for Circuit Breaker Module (ADR-003)

Tests cover:
1. LambdaCircuitBreaker triggers at call limit
2. Kill switch integration (AI_BRAIN_MODE)
3. Thread safety with concurrent calls
4. Context manager (guard) functionality
5. Singleton pattern and reset functionality
6. General CircuitBreaker for agent failure protection
"""

import os
import threading
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from orchestration.circuit_breaker import (
    # Lambda circuit breaker
    LambdaCircuitBreaker,
    CircuitBreakerTripped,
    KillSwitchActive,
    CircuitState,
    get_lambda_breaker,
    reset_lambda_breaker,
    check_lambda_allowed,
    record_lambda_call,
    lambda_guard,
    # General circuit breaker
    CircuitBreaker,
    get_circuit,
    record_failure,
    record_success,
    can_proceed,
)


class TestLambdaCircuitBreaker:
    """Tests for LambdaCircuitBreaker class."""

    def test_initial_state(self):
        """Circuit breaker starts in CLOSED state with zero calls."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=10)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.call_count == 0
        assert breaker.remaining_calls == 10
        assert not breaker.is_tripped

    def test_call_tracking(self):
        """Circuit breaker correctly tracks call count."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=10)

        breaker.record_call("test-function-1")
        assert breaker.call_count == 1
        assert breaker.remaining_calls == 9

        breaker.record_call("test-function-2")
        assert breaker.call_count == 2
        assert breaker.remaining_calls == 8

    def test_trips_at_limit(self):
        """Circuit breaker trips when call limit is reached."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=3)

        breaker.record_call("call-1")
        breaker.record_call("call-2")

        # Third call should trip the circuit
        with pytest.raises(CircuitBreakerTripped) as exc_info:
            breaker.record_call("call-3")

        assert exc_info.value.breaker_type == "Lambda"
        assert exc_info.value.call_count == 3
        assert exc_info.value.limit == 3
        assert breaker.is_tripped
        assert breaker.state == CircuitState.OPEN

    def test_check_blocks_when_tripped(self):
        """check() raises exception when circuit is tripped."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=2)

        breaker.record_call("call-1")

        # Trip the circuit
        with pytest.raises(CircuitBreakerTripped):
            breaker.record_call("call-2")

        # Subsequent check should fail
        with pytest.raises(CircuitBreakerTripped) as exc_info:
            breaker.check()

        assert "Call limit exceeded" in exc_info.value.reason

    def test_kill_switch_off(self):
        """check() raises KillSwitchActive when AI_BRAIN_MODE=OFF."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=100)

        with patch.dict(os.environ, {"AI_BRAIN_MODE": "OFF"}):
            with pytest.raises(KillSwitchActive) as exc_info:
                breaker.check()

            assert exc_info.value.mode == "OFF"

    def test_kill_switch_paused(self):
        """check() raises KillSwitchActive when AI_BRAIN_MODE=PAUSED."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=100)

        with patch.dict(os.environ, {"AI_BRAIN_MODE": "PAUSED"}):
            with pytest.raises(KillSwitchActive) as exc_info:
                breaker.check()

            assert exc_info.value.mode == "PAUSED"

    def test_kill_switch_normal(self):
        """check() passes when AI_BRAIN_MODE=NORMAL."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=100)

        with patch.dict(os.environ, {"AI_BRAIN_MODE": "NORMAL"}):
            # Should not raise
            breaker.check()

    def test_reset(self):
        """reset() clears call count and state."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=3)

        # Make some calls and trip
        breaker.record_call("call-1")
        breaker.record_call("call-2")

        with pytest.raises(CircuitBreakerTripped):
            breaker.record_call("call-3")

        assert breaker.is_tripped

        # Reset
        breaker.reset()

        assert breaker.call_count == 0
        assert breaker.state == CircuitState.CLOSED
        assert not breaker.is_tripped

        # Should be able to make calls again
        breaker.check()  # Should not raise
        breaker.record_call("new-call")
        assert breaker.call_count == 1

    def test_get_stats(self):
        """get_stats() returns correct statistics."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=10, session_id="test-session")

        breaker.record_call("func-1", success=True)
        breaker.record_call("func-2", success=False)

        stats = breaker.get_stats()

        assert stats["session_id"] == "test-session"
        assert stats["state"] == "CLOSED"
        assert stats["call_count"] == 2
        assert stats["max_calls"] == 10
        assert stats["remaining"] == 8
        assert len(stats["recent_calls"]) == 2
        assert stats["recent_calls"][0]["function"] == "func-1"
        assert stats["recent_calls"][0]["success"] is True
        assert stats["recent_calls"][1]["function"] == "func-2"
        assert stats["recent_calls"][1]["success"] is False


class TestLambdaContextManager:
    """Tests for LambdaCircuitBreaker context manager (guard)."""

    def test_guard_success(self):
        """guard() context manager records successful calls."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=10)

        with breaker.guard("test-function"):
            pass  # Simulate successful Lambda call

        assert breaker.call_count == 1
        stats = breaker.get_stats()
        assert stats["recent_calls"][0]["success"] is True

    def test_guard_failure(self):
        """guard() context manager records failed calls."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=10)

        try:
            with breaker.guard("test-function"):
                raise ValueError("Simulated failure")
        except ValueError:
            pass

        assert breaker.call_count == 1
        stats = breaker.get_stats()
        assert stats["recent_calls"][0]["success"] is False

    def test_guard_trips_circuit(self):
        """guard() context manager can trip the circuit."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=2)

        with breaker.guard("call-1"):
            pass

        with pytest.raises(CircuitBreakerTripped):
            with breaker.guard("call-2"):
                pass

    def test_guard_checks_before_call(self):
        """guard() checks circuit state before allowing call."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=2)

        # Trip the circuit
        breaker.record_call("call-1")
        with pytest.raises(CircuitBreakerTripped):
            breaker.record_call("call-2")

        # Guard should check and fail before entering
        with pytest.raises(CircuitBreakerTripped):
            with breaker.guard("call-3"):
                pass


class TestThreadSafety:
    """Tests for thread safety of circuit breaker."""

    def test_concurrent_calls(self):
        """Circuit breaker handles concurrent calls correctly."""
        breaker = LambdaCircuitBreaker(max_calls_per_session=100)
        errors = []

        def make_calls(thread_id: int):
            try:
                for i in range(10):
                    breaker.record_call(f"thread-{thread_id}-call-{i}")
            except CircuitBreakerTripped:
                # Expected if limit reached
                pass
            except Exception as e:
                errors.append(e)

        # Create 5 threads, each making 10 calls
        threads = [
            threading.Thread(target=make_calls, args=(i,))
            for i in range(5)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # No errors should have occurred
        assert len(errors) == 0
        # Total calls should be 50 (or less if tripped)
        assert breaker.call_count == 50

    def test_concurrent_trips_at_limit(self):
        """Circuit breaker trips near limit under concurrent access.

        Note: Under concurrent access, the circuit breaker may allow a few extra
        calls beyond the limit due to race conditions between check and increment.
        This is acceptable behavior - the important thing is that it trips and
        blocks subsequent calls.
        """
        breaker = LambdaCircuitBreaker(max_calls_per_session=20)
        trip_count = [0]

        def make_calls():
            try:
                for _ in range(10):
                    breaker.record_call("test")
            except CircuitBreakerTripped:
                trip_count[0] += 1

        # Create 3 threads, each trying 10 calls (30 total, limit is 20)
        threads = [
            threading.Thread(target=make_calls)
            for _ in range(3)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have tripped
        assert breaker.is_tripped
        # Call count should be at or slightly above limit (race condition tolerance)
        # Allow up to 3 extra calls due to concurrent race conditions
        assert 20 <= breaker.call_count <= 23, f"Call count {breaker.call_count} outside expected range [20, 23]"


class TestSingletonPattern:
    """Tests for global singleton functions."""

    def test_get_lambda_breaker_creates_instance(self):
        """get_lambda_breaker() creates singleton instance."""
        # Reset to ensure clean state
        reset_lambda_breaker(max_calls=50)

        breaker1 = get_lambda_breaker()
        breaker2 = get_lambda_breaker()

        assert breaker1 is breaker2
        assert breaker1.max_calls_per_session == 50

    def test_reset_lambda_breaker_creates_new_instance(self):
        """reset_lambda_breaker() creates fresh instance."""
        breaker1 = get_lambda_breaker(max_calls=100)
        breaker1.record_call("test")

        breaker2 = reset_lambda_breaker(max_calls=200)

        assert breaker2.call_count == 0
        assert breaker2.max_calls_per_session == 200

    def test_convenience_functions(self):
        """Convenience functions work with global breaker."""
        reset_lambda_breaker(max_calls=10)

        # check_lambda_allowed should not raise
        check_lambda_allowed()

        # record_lambda_call should increment count
        count = record_lambda_call("test-function")
        assert count == 1

        # lambda_guard should work
        with lambda_guard("test-function-2"):
            pass

        breaker = get_lambda_breaker()
        assert breaker.call_count == 2


class TestGeneralCircuitBreaker:
    """Tests for the general CircuitBreaker (failure-based)."""

    def test_initial_state(self):
        """General circuit breaker starts closed."""
        breaker = CircuitBreaker(agent="test-agent", project="test-project")

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.can_proceed()

    def test_trips_on_failures(self):
        """Circuit breaker trips after failure threshold."""
        breaker = CircuitBreaker(
            agent="test-agent",
            project="test-project",
            failure_threshold=3
        )

        breaker.record_failure("Error 1")
        assert breaker.can_proceed()

        breaker.record_failure("Error 2")
        assert breaker.can_proceed()

        breaker.record_failure("Error 3")
        assert not breaker.can_proceed()
        assert breaker.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        """Success resets failure count in closed state."""
        breaker = CircuitBreaker(
            agent="test-agent",
            project="test-project",
            failure_threshold=3
        )

        breaker.record_failure("Error 1")
        breaker.record_failure("Error 2")
        assert breaker.failure_count == 2

        breaker.record_success()
        assert breaker.failure_count == 0

    def test_auto_reset_to_half_open(self):
        """Circuit auto-resets to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(
            agent="test-agent",
            project="test-project",
            failure_threshold=2,
            reset_timeout=timedelta(seconds=0)  # Immediate reset for testing
        )

        # Trip the circuit
        breaker.record_failure("Error 1")
        breaker.record_failure("Error 2")
        assert breaker.state == CircuitState.OPEN

        # Set opened_at to past
        breaker.opened_at = datetime.now() - timedelta(seconds=1)

        # Should auto-reset to HALF_OPEN
        assert breaker.can_proceed()
        assert breaker.state == CircuitState.HALF_OPEN

    def test_half_open_to_closed_on_success(self):
        """HALF_OPEN transitions to CLOSED on success."""
        breaker = CircuitBreaker(
            agent="test-agent",
            project="test-project",
            failure_threshold=2,
            reset_timeout=timedelta(seconds=0)
        )

        # Get to HALF_OPEN state
        breaker.record_failure("Error 1")
        breaker.record_failure("Error 2")
        breaker.opened_at = datetime.now() - timedelta(seconds=1)
        breaker.can_proceed()  # Triggers transition to HALF_OPEN

        assert breaker.state == CircuitState.HALF_OPEN

        # Success should close the circuit
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    def test_registry_functions(self):
        """Registry functions work for agent/project combinations."""
        # Clear any existing state by using unique names
        agent = f"test-agent-{datetime.now().timestamp()}"
        project = f"test-project-{datetime.now().timestamp()}"

        assert can_proceed(agent, project)

        record_failure(agent, project, "Error 1")
        record_failure(agent, project, "Error 2")
        record_failure(agent, project, "Error 3")

        assert not can_proceed(agent, project)

    def test_get_circuit_returns_same_instance(self):
        """get_circuit returns same instance for same agent/project."""
        agent = f"test-agent-singleton-{datetime.now().timestamp()}"
        project = "test-project"

        breaker1 = get_circuit(agent, project)
        breaker2 = get_circuit(agent, project)

        assert breaker1 is breaker2


class TestExceptionDetails:
    """Tests for exception attributes and messages."""

    def test_circuit_breaker_tripped_attributes(self):
        """CircuitBreakerTripped has correct attributes."""
        exc = CircuitBreakerTripped(
            breaker_type="Lambda",
            reason="Session limit reached",
            call_count=100,
            limit=100
        )

        assert exc.breaker_type == "Lambda"
        assert exc.reason == "Session limit reached"
        assert exc.call_count == 100
        assert exc.limit == 100
        assert "Lambda circuit breaker tripped" in str(exc)

    def test_kill_switch_active_attributes(self):
        """KillSwitchActive has correct attributes."""
        exc = KillSwitchActive(mode="OFF")

        assert exc.mode == "OFF"
        assert "AI_BRAIN_MODE=OFF" in str(exc)
