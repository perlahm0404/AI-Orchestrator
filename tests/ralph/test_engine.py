"""
Tests for Ralph Verification Engine

Tests the core verify() function and step execution.

Implementation: Phase 0
"""

import pytest
import tempfile
from pathlib import Path
from dataclasses import dataclass

from ralph import engine
from ralph.engine import VerdictType, Verdict, StepResult


# Mock AppContext for testing
@dataclass
class MockAppContext:
    """Mock AppContext for testing."""
    project_name: str = "test-project"
    project_path: str = None
    language: str = "typescript"
    lint_command: str = "echo 'Lint passed'"
    typecheck_command: str = "echo 'Typecheck passed'"
    test_command: str = "echo 'Tests passed'"
    coverage_command: str = ""
    source_paths: list = None
    test_paths: list = None
    coverage_report_path: str = ""
    autonomy_level: str = "L2"

    def __post_init__(self):
        if self.source_paths is None:
            self.source_paths = []
        if self.test_paths is None:
            self.test_paths = []
        if self.project_path is None:
            # Use a temp directory that actually exists
            self.project_path = tempfile.gettempdir()


class TestRalphEngine:
    """Tests for Ralph verification engine."""

    def test_verify_without_context_returns_fail(self):
        """
        Calling verify() without app_context should return FAIL.
        """
        verdict = engine.verify(
            project="test",
            changes=["file.ts"],
            session_id="test-123"
        )

        assert verdict.type == VerdictType.FAIL
        assert verdict.reason == "No app_context provided"

    def test_verify_with_passing_steps_returns_pass(self):
        """
        When all steps pass, verdict should be PASS.
        """
        context = MockAppContext(
            lint_command="true",  # Unix command that always succeeds
            typecheck_command="true",
            test_command="true"
        )

        verdict = engine.verify(
            project="test",
            changes=["file.ts"],
            session_id="test-123",
            app_context=context
        )

        assert verdict.type == VerdictType.PASS
        assert verdict.reason is None
        assert len(verdict.steps) == 3  # lint, typecheck, test
        assert all(step.passed for step in verdict.steps)

    def test_verify_with_failing_lint_returns_fail(self):
        """
        When lint fails, verdict should be FAIL.
        """
        context = MockAppContext(
            lint_command="false",  # Unix command that always fails
            typecheck_command="true",
            test_command="true"
        )

        verdict = engine.verify(
            project="test",
            changes=["file.ts"],
            session_id="test-123",
            app_context=context
        )

        assert verdict.type == VerdictType.FAIL
        assert "lint" in verdict.reason.lower()
        assert len(verdict.steps) == 3
        assert verdict.steps[0].passed is False  # lint failed
        assert verdict.steps[0].step == "lint"

    def test_verify_with_failing_tests_returns_fail(self):
        """
        When tests fail, verdict should be FAIL.
        """
        context = MockAppContext(
            lint_command="true",
            typecheck_command="true",
            test_command="false"  # Tests fail
        )

        verdict = engine.verify(
            project="test",
            changes=["file.ts"],
            session_id="test-123",
            app_context=context
        )

        assert verdict.type == VerdictType.FAIL
        assert "test" in verdict.reason.lower()

    def test_verdict_includes_evidence(self):
        """
        Verdict should include evidence dict with metadata.
        """
        context = MockAppContext()

        verdict = engine.verify(
            project="karematch",
            changes=["src/auth.ts", "tests/auth.test.ts"],
            session_id="abc-123",
            app_context=context
        )

        assert verdict.evidence is not None
        assert verdict.evidence["project"] == "karematch"
        assert verdict.evidence["session_id"] == "abc-123"
        assert "src/auth.ts" in verdict.evidence["changes"]

    def test_step_results_include_duration(self):
        """
        Each step result should include duration_ms.
        """
        context = MockAppContext(
            lint_command="sleep 0.1 && true"  # Add slight delay
        )

        verdict = engine.verify(
            project="test",
            changes=["file.ts"],
            session_id="test-123",
            app_context=context
        )

        assert len(verdict.steps) > 0
        for step in verdict.steps:
            assert step.duration_ms > 0  # Should have measured time
            assert isinstance(step.duration_ms, int)

    def test_verdict_type_enum_values(self):
        """
        VerdictType enum should have PASS/FAIL/BLOCKED.
        """
        assert VerdictType.PASS.value == "PASS"
        assert VerdictType.FAIL.value == "FAIL"
        assert VerdictType.BLOCKED.value == "BLOCKED"

    def test_step_result_structure(self):
        """
        StepResult should have expected fields.
        """
        result = StepResult(
            step="lint",
            passed=True,
            output="All good",
            duration_ms=100
        )

        assert result.step == "lint"
        assert result.passed is True
        assert result.output == "All good"
        assert result.duration_ms == 100


class TestRalphStepRunner:
    """Tests for individual step runners."""

    def test_run_step_with_successful_command(self):
        """
        Running a successful command should return passed=True.
        """
        from ralph.steps import run_step, StepConfig

        config = StepConfig(
            name="test-step",
            command="echo 'Hello'",
            cwd=Path("/tmp")
        )

        result = run_step(config)

        assert result.passed is True
        assert result.step == "test-step"
        assert "Hello" in result.output

    def test_run_step_with_failing_command(self):
        """
        Running a failing command should return passed=False.
        """
        from ralph.steps import run_step, StepConfig

        config = StepConfig(
            name="fail-step",
            command="false",  # Always fails
            cwd=Path("/tmp")
        )

        result = run_step(config)

        assert result.passed is False
        assert result.step == "fail-step"

    def test_run_step_captures_stdout_and_stderr(self):
        """
        Step runner should capture both stdout and stderr.
        """
        from ralph.steps import run_step, StepConfig

        config = StepConfig(
            name="output-test",
            command="echo 'stdout message' && echo 'stderr message' >&2",
            cwd=Path("/tmp")
        )

        result = run_step(config)

        assert "stdout message" in result.output
        assert "stderr message" in result.output
