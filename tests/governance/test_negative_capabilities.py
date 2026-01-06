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

    def test_load_bugfix_contract(self):
        """
        Can load bugfix contract from YAML.
        """
        from governance import contract

        bugfix = contract.load("bugfix")

        assert bugfix.agent == "bugfix"
        assert bugfix.version == "1.0"
        assert "write_file" in bugfix.allowed_actions
        assert "modify_migrations" in bugfix.forbidden_actions
        assert "merge_pr" in bugfix.requires_approval

    def test_load_codequality_contract(self):
        """
        Can load codequality contract from YAML.
        """
        from governance import contract

        codequality = contract.load("codequality")

        assert codequality.agent == "codequality"
        assert "run_lint_fix" in codequality.allowed_actions
        assert "add_new_features" in codequality.forbidden_actions
        assert codequality.invariants.get("test_count_unchanged") is True

    def test_forbidden_action_blocked(self):
        """
        Actions in forbidden_actions list must be blocked.
        """
        from governance import contract

        # Load bugfix contract
        bugfix = contract.load("bugfix")

        # Attempt a forbidden action
        with pytest.raises(contract.ContractViolation, match="forbidden"):
            contract.require_allowed(bugfix, "modify_migrations")

    def test_allowed_action_passes(self):
        """
        Actions in allowed_actions list should pass.
        """
        from governance import contract

        bugfix = contract.load("bugfix")

        # Should not raise
        contract.require_allowed(bugfix, "write_file")
        contract.require_allowed(bugfix, "run_tests")

    def test_unlisted_action_blocked(self):
        """
        Actions not in allowed list are blocked by default (safe default).
        """
        from governance import contract

        bugfix = contract.load("bugfix")

        # Attempt an action that's not listed
        with pytest.raises(contract.ContractViolation, match="not in allowed list"):
            contract.require_allowed(bugfix, "launch_missiles")

    def test_exceeding_lines_limit_blocked(self):
        """
        Exceeding max_lines_added limit must be blocked.
        """
        from governance import contract

        bugfix = contract.load("bugfix")

        # max_lines_added is 100 in bugfix contract
        # Exceeding it should raise
        with pytest.raises(contract.ContractViolation, match="Limit exceeded.*max_lines_added"):
            contract.check_limits(bugfix, lines_added=150)

    def test_within_lines_limit_passes(self):
        """
        Staying within max_lines_added limit should pass.
        """
        from governance import contract

        bugfix = contract.load("bugfix")

        # Should not raise
        contract.check_limits(bugfix, lines_added=50)

    def test_exceeding_files_limit_blocked(self):
        """
        Exceeding max_files_changed limit must be blocked.
        """
        from governance import contract

        bugfix = contract.load("bugfix")

        # max_files_changed is 5 in bugfix contract
        with pytest.raises(contract.ContractViolation, match="Limit exceeded.*max_files_changed"):
            contract.check_limits(bugfix, files_changed=10)

    def test_multiple_limits_checked(self):
        """
        Multiple limits can be checked simultaneously.
        """
        from governance import contract

        bugfix = contract.load("bugfix")

        # Both within limits - should pass
        contract.check_limits(bugfix, lines_added=50, files_changed=3)

        # One exceeds limit - should fail
        with pytest.raises(contract.ContractViolation):
            contract.check_limits(bugfix, lines_added=150, files_changed=3)

    def test_requires_approval_flag(self):
        """
        Can check if action requires approval.
        """
        from governance import contract

        bugfix = contract.load("bugfix")

        assert bugfix.requires_human_approval("merge_pr") is True
        assert bugfix.requires_human_approval("write_file") is False

    def test_invariants_violation_blocked(self):
        """
        Violating invariants must be blocked.
        """
        from governance import contract

        codequality = contract.load("codequality")

        # test_count_unchanged must be True
        with pytest.raises(contract.ContractViolation, match="Invariant violated"):
            contract.check_invariants(codequality, test_count_unchanged=False)


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
        import tempfile
        from pathlib import Path
        from ralph import engine
        from ralph.engine import VerdictType

        # Create temp project with test.skip() violation
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()

            # Create file with .skip() violation
            test_file = src_dir / "auth.test.ts"
            test_file.write_text("""
describe('Auth', () => {
  test.skip('should authenticate', () => {
    // This test is skipped - VIOLATION
  });
});
""")

            # Create mock app context
            from dataclasses import dataclass
            @dataclass
            class MockContext:
                project_name = "test"
                project_path = tmpdir
                language = "typescript"
                lint_command = "true"
                typecheck_command = "true"
                test_command = "true"
                source_paths = ["src"]
                test_paths = ["src"]
                coverage_report_path = ""
                autonomy_level = "L2"

            verdict = engine.verify(
                project="test",
                changes=["src/auth.test.ts"],
                session_id="test-123",
                app_context=MockContext()
            )

            # Should be BLOCKED due to test.skip()
            assert verdict.type == VerdictType.BLOCKED
            assert "guardrail" in verdict.reason.lower()
            assert len(verdict.evidence.get("violations", [])) > 0

    def test_eslint_disable_causes_blocked_verdict(self):
        """
        Introducing eslint-disable must cause BLOCKED verdict.
        """
        import tempfile
        from pathlib import Path
        from ralph import engine
        from ralph.engine import VerdictType

        # Create temp project with eslint-disable violation
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()

            # Create file with eslint-disable violation
            code_file = src_dir / "utils.js"
            code_file.write_text("""
// eslint-disable no-console
function debug(msg) {
  console.log(msg);  // VIOLATION: eslint disabled
}
""")

            # Create mock app context
            from dataclasses import dataclass
            @dataclass
            class MockContext:
                project_name = "test"
                project_path = tmpdir
                language = "javascript"
                lint_command = "true"
                typecheck_command = "true"
                test_command = "true"
                source_paths = ["src"]
                test_paths = ["src"]
                coverage_report_path = ""
                autonomy_level = "L2"

            verdict = engine.verify(
                project="test",
                changes=["src/utils.js"],
                session_id="test-123",
                app_context=MockContext()
            )

            # Should be BLOCKED due to eslint-disable
            assert verdict.type == VerdictType.BLOCKED
            assert "guardrail" in verdict.reason.lower()
            assert len(verdict.evidence.get("violations", [])) > 0


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
