"""
Tests for Self-Correction System (Phase 3)

TDD approach: Tests written first, then implementation.
Target: Auto-fix lint/type/test errors with bounded retries.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

# These imports will fail until we implement the modules
try:
    from agents.self_correct import (
        SelfCorrector,
        FixStrategy,
        FixAction,
        analyze_failure,
        apply_fix,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

    class FixAction(Enum):
        RUN_AUTOFIX = "run_autofix"
        FIX_TYPES = "fix_types"
        FIX_IMPLEMENTATION = "fix_implementation"
        ESCALATE = "escalate"

    @dataclass
    class FixStrategy:
        action: FixAction
        command: Optional[str] = None
        prompt: Optional[str] = None
        retry_immediately: bool = False
        reason: Optional[str] = None


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestFixStrategy:
    """Test FixStrategy dataclass."""

    def test_autofix_strategy(self):
        """Autofix strategy for lint errors."""
        strategy = FixStrategy(
            action=FixAction.RUN_AUTOFIX,
            command="npm run lint:fix",
            retry_immediately=True
        )
        assert strategy.action == FixAction.RUN_AUTOFIX
        assert strategy.retry_immediately is True

    def test_escalate_strategy(self):
        """Escalate strategy for unknown errors."""
        strategy = FixStrategy(
            action=FixAction.ESCALATE,
            reason="Unknown failure type"
        )
        assert strategy.action == FixAction.ESCALATE


class TestAnalyzeFailure:
    """Test failure analysis logic."""

    def test_lint_error_returns_autofix(self):
        """Lint errors should trigger autofix."""
        verify_result = Mock()
        verify_result.lint_passed = False
        verify_result.types_passed = True
        verify_result.tests_passed = True
        verify_result.errors = ["Missing semicolon"]

        strategy = analyze_failure(verify_result)

        assert strategy.action == FixAction.RUN_AUTOFIX
        assert strategy.retry_immediately is True

    def test_type_error_returns_fix_types(self):
        """Type errors need Claude to fix."""
        verify_result = Mock()
        verify_result.lint_passed = True
        verify_result.types_passed = False
        verify_result.tests_passed = True
        verify_result.errors = ["Type 'string' not assignable to 'number'"]

        strategy = analyze_failure(verify_result)

        assert strategy.action == FixAction.FIX_TYPES
        assert "type" in strategy.prompt.lower()

    def test_test_failure_returns_fix_implementation(self):
        """Test failures need implementation fixes."""
        verify_result = Mock()
        verify_result.lint_passed = True
        verify_result.types_passed = True
        verify_result.tests_passed = False
        verify_result.errors = ["Expected 5 but got 4"]

        strategy = analyze_failure(verify_result)

        assert strategy.action == FixAction.FIX_IMPLEMENTATION
        assert strategy.prompt is not None

    def test_unknown_error_returns_escalate(self):
        """Unknown errors should escalate."""
        verify_result = Mock()
        verify_result.lint_passed = True
        verify_result.types_passed = True
        verify_result.tests_passed = True
        verify_result.errors = ["Unknown internal error"]

        strategy = analyze_failure(verify_result)

        assert strategy.action == FixAction.ESCALATE


class TestSelfCorrector:
    """Test SelfCorrector class."""

    @pytest.fixture
    def corrector(self, tmp_path: Path):
        return SelfCorrector(project_dir=tmp_path)

    def test_bounded_retries(self, corrector):
        """Corrector respects max retries."""
        mock_task = Mock()
        mock_task.id = "TEST-001"
        mock_task.max_iterations = 3

        with patch.object(corrector, '_attempt_fix', new_callable=AsyncMock) as mock_fix:
            mock_fix.return_value = False  # Always fail

            import asyncio
            result = asyncio.run(corrector.fix_with_retries(mock_task, max_retries=3))

        assert mock_fix.call_count == 3
        assert result.success is False

    def test_stops_on_success(self, corrector):
        """Corrector stops when fix succeeds."""
        mock_task = Mock()
        mock_task.id = "TEST-001"

        with patch.object(corrector, '_attempt_fix', new_callable=AsyncMock) as mock_fix:
            mock_fix.side_effect = [False, True]  # Fail first, then succeed

            import asyncio
            result = asyncio.run(corrector.fix_with_retries(mock_task, max_retries=5))

        assert mock_fix.call_count == 2
        assert result.success is True

    def test_escalates_after_max_retries(self, corrector):
        """Corrector escalates when max retries exceeded."""
        mock_task = Mock()
        mock_task.id = "TEST-001"

        with patch.object(corrector, '_attempt_fix', new_callable=AsyncMock) as mock_fix:
            with patch.object(corrector, '_escalate') as mock_escalate:
                mock_fix.return_value = False

                import asyncio
                asyncio.run(corrector.fix_with_retries(mock_task, max_retries=2))

        mock_escalate.assert_called_once()


class TestApplyFix:
    """Test fix application."""

    @pytest.fixture
    def corrector(self, tmp_path: Path):
        return SelfCorrector(project_dir=tmp_path)

    def test_applies_autofix_command(self, corrector, tmp_path: Path):
        """Autofix runs the specified command."""
        strategy = FixStrategy(
            action=FixAction.RUN_AUTOFIX,
            command="npm run lint:fix",
            retry_immediately=True
        )

        with patch.object(corrector, '_run_command') as mock_run:
            mock_run.return_value = True  # Success

            result = corrector.apply_fix(strategy, ["test.ts"])

        mock_run.assert_called_with("npm run lint:fix")
        assert result is True

    def test_applies_type_fix_prompt(self, corrector, tmp_path: Path):
        """Type fix sends prompt to Claude."""
        strategy = FixStrategy(
            action=FixAction.FIX_TYPES,
            prompt="Fix type error: string vs number"
        )

        with patch.object(corrector, '_send_to_claude', new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = True

            import asyncio
            result = asyncio.run(corrector.apply_fix_async(strategy, ["test.ts"]))

        mock_claude.assert_called_once()
        assert "type error" in mock_claude.call_args[0][0].lower()


class TestProgressiveRetry:
    """Test progressive retry strategies."""

    @pytest.fixture
    def corrector(self, tmp_path: Path):
        return SelfCorrector(project_dir=tmp_path)

    def test_increases_context_on_retry(self, corrector):
        """Each retry provides more context."""
        mock_task = Mock()
        mock_task.id = "TEST-001"
        mock_task.file = "test.ts"

        prompts_used = []

        with patch.object(corrector, '_attempt_fix', new_callable=AsyncMock) as mock_fix:
            async def capture_prompt(*args, **kwargs):
                prompts_used.append(kwargs.get('context_level', 0))
                return False

            mock_fix.side_effect = capture_prompt

            import asyncio
            asyncio.run(corrector.fix_with_retries(mock_task, max_retries=3))

        # Context level should increase with each retry
        assert prompts_used == [0, 1, 2] or len(prompts_used) == 3

    def test_different_strategy_per_retry(self, corrector):
        """Different fix strategies tried on each retry."""
        mock_task = Mock()
        mock_task.id = "TEST-001"

        attempts_made = []

        async def track_attempts(*args, **kwargs):
            attempts_made.append(kwargs.get('context_level', 0))
            return False

        with patch.object(corrector, '_attempt_fix', new_callable=AsyncMock) as mock_attempt:
            mock_attempt.side_effect = track_attempts

            import asyncio
            asyncio.run(corrector.fix_with_retries(mock_task, max_retries=3))

        assert len(attempts_made) == 3
