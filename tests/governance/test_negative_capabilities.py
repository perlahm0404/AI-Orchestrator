"""
Negative Capability Tests

These tests prove that safety systems actually work by attempting
forbidden actions and verifying they are blocked.

A passing safety test suite without negative capability tests
provides false confidence. These tests are mandatory.

See: v4 Planning.md Section "Negative Capability Tests"

Implementation: Phase 0
"""

import pytest
import os
from governance.kill_switch import mode


class TestKillSwitch:
    """Tests for kill switch functionality."""

    def setup_method(self):
        """Save original mode before each test."""
        self.original_mode = os.environ.get(mode.ENV_VAR)

    def teardown_method(self):
        """Restore original mode after each test."""
        if self.original_mode:
            os.environ[mode.ENV_VAR] = self.original_mode
        elif mode.ENV_VAR in os.environ:
            del os.environ[mode.ENV_VAR]

    def test_off_mode_blocks_all_writes(self):
        """
        When AI_BRAIN_MODE=OFF, all write operations must be blocked.
        """
        # Set mode to OFF
        mode.set(mode.Mode.OFF)

        # Verify mode is OFF
        assert mode.get() == mode.Mode.OFF

        # Attempt a write operation (using require_not_off guard)
        with pytest.raises(RuntimeError, match="AI Brain is OFF"):
            mode.require_not_off()

    def test_off_mode_also_blocks_with_require_normal(self):
        """
        OFF mode should also be blocked by require_normal guard.
        """
        mode.set(mode.Mode.OFF)

        with pytest.raises(RuntimeError, match="Operation blocked.*OFF"):
            mode.require_normal()

    def test_safe_mode_allows_reads(self):
        """
        When AI_BRAIN_MODE=SAFE, read operations should work.
        """
        # Set mode to SAFE
        mode.set(mode.Mode.SAFE)

        # Verify mode is SAFE
        assert mode.get() == mode.Mode.SAFE

        # require_not_off should NOT raise (reads are allowed in SAFE mode)
        mode.require_not_off()  # Should pass

    def test_safe_mode_blocks_writes(self):
        """
        When AI_BRAIN_MODE=SAFE, write operations must be blocked.
        """
        # Set mode to SAFE
        mode.set(mode.Mode.SAFE)

        # Attempt a write operation (using require_normal guard)
        with pytest.raises(RuntimeError, match="Operation blocked.*SAFE"):
            mode.require_normal()

    def test_paused_mode_blocks_writes(self):
        """
        When AI_BRAIN_MODE=PAUSED, write operations must be blocked.
        """
        mode.set(mode.Mode.PAUSED)

        with pytest.raises(RuntimeError, match="Operation blocked.*PAUSED"):
            mode.require_normal()

    def test_normal_mode_allows_everything(self):
        """
        When AI_BRAIN_MODE=NORMAL, all operations should work.
        """
        mode.set(mode.Mode.NORMAL)

        # Both guards should pass
        mode.require_not_off()  # Should pass
        mode.require_normal()   # Should pass

    def test_default_mode_is_normal(self):
        """
        Default mode should be NORMAL when not explicitly set.
        """
        # Clear environment variable
        if mode.ENV_VAR in os.environ:
            del os.environ[mode.ENV_VAR]

        assert mode.get() == mode.Mode.NORMAL

    def test_invalid_mode_falls_back_to_default(self):
        """
        Invalid mode value should fall back to NORMAL (safe default).
        """
        os.environ[mode.ENV_VAR] = "INVALID_MODE"

        assert mode.get() == mode.Mode.NORMAL

    def test_mode_persists_across_get_calls(self):
        """
        Setting mode should persist across multiple get() calls.
        """
        mode.set(mode.Mode.SAFE)

        assert mode.get() == mode.Mode.SAFE
        assert mode.get() == mode.Mode.SAFE  # Second call
        assert mode.get() == mode.Mode.SAFE  # Third call


class TestAutonomyContracts:
    """Tests for autonomy contract enforcement."""

    def test_forbidden_action_blocked(self):
        """
        Actions in forbidden_actions list must be blocked.
        """
        # TODO: Implement in Phase 0
        # 1. Load bugfix contract
        # 2. Attempt a forbidden action (e.g., modify_migrations)
        # 3. Verify it raises a contract violation
        pytest.skip("Not yet implemented")

    def test_exceeding_limits_blocked(self):
        """
        Exceeding contract limits (max_lines, max_files) must be blocked.
        """
        # TODO: Implement in Phase 0
        pytest.skip("Not yet implemented")

    def test_requires_approval_halts(self):
        """
        Actions requiring approval must halt and wait.
        """
        # TODO: Implement in Phase 0
        pytest.skip("Not yet implemented")


class TestGuardrails:
    """Tests for runtime guardrails."""

    def test_dangerous_bash_blocked(self):
        """
        Dangerous bash commands (rm -rf, etc.) must be blocked.
        """
        # TODO: Implement in Phase 0
        pytest.skip("Not yet implemented")

    def test_test_skip_causes_blocked_verdict(self):
        """
        Introducing test.skip() must cause BLOCKED verdict from Ralph.
        """
        # TODO: Implement in Phase 0
        pytest.skip("Not yet implemented")

    def test_eslint_disable_causes_blocked_verdict(self):
        """
        Introducing eslint-disable must cause BLOCKED verdict.
        """
        # TODO: Implement in Phase 0
        pytest.skip("Not yet implemented")


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    def test_repeated_failures_trip_circuit(self):
        """
        After N failures, circuit should trip and block further requests.
        """
        # TODO: Implement in Phase 0
        pytest.skip("Not yet implemented")

    def test_tripped_circuit_blocks_requests(self):
        """
        When circuit is OPEN, all requests must be blocked.
        """
        # TODO: Implement in Phase 0
        pytest.skip("Not yet implemented")


class TestRalphVerdicts:
    """Tests for Ralph verdict enforcement."""

    def test_blocked_verdict_halts_agent(self):
        """
        A BLOCKED verdict must cause immediate agent halt.
        """
        # TODO: Implement in Phase 0
        pytest.skip("Not yet implemented")

    def test_blocked_verdict_cannot_be_bypassed(self):
        """
        There must be no way to proceed after BLOCKED verdict.
        """
        # TODO: Implement in Phase 0
        pytest.skip("Not yet implemented")
