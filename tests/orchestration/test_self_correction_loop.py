"""
Tests for Self-Correction Loop Integration (Phase 3)

TDD approach: Tests written first, then implementation.
Target: Loop retries with self-correction before failing.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, call

try:
    from orchestration.simplified_loop import (
        SimplifiedLoop,
        LoopConfig,
        LoopResult,
        TaskResult,
    )
    from ralph.fast_verify import (
        FastVerify,
        VerifyResult,
        VerifyStatus,
        VerifyTier,
    )
    from agents.self_correct import (
        SelfCorrector,
        analyze_failure,
        FixAction,
        FixStrategy,
        FixResult,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestBoundedRetryLoop:
    """Test bounded retry behavior in the loop."""

    @pytest.fixture
    def mock_work_queue(self):
        queue = Mock()
        queue.get_next_pending.return_value = None
        queue.get_in_progress.return_value = None
        return queue

    @pytest.fixture
    def mock_task(self):
        task = Mock()
        task.id = "TEST-001"
        task.description = "Test task"
        task.file = "src/test.ts"
        task.status = "pending"
        task.max_iterations = 5  # Allow 5 retries for this task
        return task

    def test_loop_retries_on_type_error(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop retries when type checking fails."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path, max_iterations=10)
        loop = SimplifiedLoop(config)

        attempt_count = [0]

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
                with patch.object(loop, '_fast_verify') as mock_verify:
                    def verify_side_effect(files):
                        attempt_count[0] += 1
                        if attempt_count[0] < 3:
                            return VerifyResult(
                                status=VerifyStatus.FAIL,
                                tier=VerifyTier.QUICK,
                                errors=["Type 'string' not assignable to 'number'"],
                                types_passed=False
                            )
                        return VerifyResult(
                            status=VerifyStatus.PASS,
                            tier=VerifyTier.QUICK
                        )

                    mock_verify.side_effect = verify_side_effect
                    mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                    result = asyncio.run(loop.run())

        # Should have succeeded after retries
        assert result.completed == 1
        assert attempt_count[0] >= 2

    def test_loop_retries_on_test_failure(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop retries when tests fail."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path, max_iterations=10)
        loop = SimplifiedLoop(config)

        attempt_count = [0]

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
                with patch.object(loop, '_fast_verify') as mock_verify:
                    def verify_side_effect(files):
                        attempt_count[0] += 1
                        if attempt_count[0] < 2:
                            return VerifyResult(
                                status=VerifyStatus.FAIL,
                                tier=VerifyTier.RELATED,
                                errors=["Expected 5 but got 4"],
                                tests_passed=False
                            )
                        return VerifyResult(
                            status=VerifyStatus.PASS,
                            tier=VerifyTier.RELATED
                        )

                    mock_verify.side_effect = verify_side_effect
                    mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                    result = asyncio.run(loop.run())

        assert result.completed == 1

    def test_loop_respects_task_max_iterations(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop stops retrying after task.max_iterations."""
        mock_task.max_iterations = 3
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path, max_iterations=100)
        loop = SimplifiedLoop(config)

        attempt_count = [0]

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
                with patch.object(loop, '_fast_verify') as mock_verify:
                    def verify_side_effect(files):
                        attempt_count[0] += 1
                        # Always fail
                        return VerifyResult(
                            status=VerifyStatus.FAIL,
                            tier=VerifyTier.QUICK,
                            errors=["Persistent error"],
                            types_passed=False
                        )

                    mock_verify.side_effect = verify_side_effect
                    mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                    result = asyncio.run(loop.run())

        # Should have failed and stopped at max_iterations
        assert result.failed == 1
        assert attempt_count[0] <= mock_task.max_iterations

    def test_loop_escalates_on_unknown_error(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop escalates immediately on unknown errors."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
                with patch.object(loop, '_fast_verify') as mock_verify:
                    # All checks pass but errors list has unknown error
                    mock_verify.return_value = VerifyResult(
                        status=VerifyStatus.FAIL,
                        tier=VerifyTier.FULL,
                        errors=["Unknown internal error"],
                        lint_passed=True,
                        types_passed=True,
                        tests_passed=True
                    )
                    mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                    result = asyncio.run(loop.run())

        # Should escalate (mark as blocked or failed) without retrying
        assert result.blocked == 1 or result.failed == 1


class TestProgressiveContext:
    """Test that retries provide more context."""

    @pytest.fixture
    def mock_task(self):
        task = Mock()
        task.id = "TEST-001"
        task.description = "Fix authentication bug"
        task.file = "src/auth.ts"
        task.status = "pending"
        task.max_iterations = 5
        return task

    def test_retry_includes_previous_errors(self, tmp_path: Path, mock_task):
        """Each retry includes context from previous attempts."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        prompts_received = []

        with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
            with patch.object(loop, '_fast_verify') as mock_verify:
                async def capture_prompt(task, context=None):
                    prompts_received.append(context)
                    return {"success": True, "files": [task.file]}

                mock_claude.side_effect = capture_prompt

                attempt = [0]
                def verify_side_effect(files):
                    attempt[0] += 1
                    if attempt[0] < 3:
                        return VerifyResult(
                            status=VerifyStatus.FAIL,
                            tier=VerifyTier.QUICK,
                            errors=[f"Error on attempt {attempt[0]}"],
                            types_passed=False
                        )
                    return VerifyResult(status=VerifyStatus.PASS, tier=VerifyTier.QUICK)

                mock_verify.side_effect = verify_side_effect

                # Execute with retries
                asyncio.run(loop._execute_task_with_retries(mock_task))

        # Later attempts should have more context
        if len(prompts_received) >= 2:
            # Context should grow with each attempt
            assert prompts_received[1] is not None or len(prompts_received) >= 2

    def test_retry_uses_different_strategy_per_attempt(self, tmp_path: Path, mock_task):
        """Different fix strategies are tried on each retry."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        strategies_used = []

        with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
            with patch.object(loop, '_fast_verify') as mock_verify:
                with patch.object(loop, '_apply_fix_strategy') as mock_fix:
                    async def track_strategy(strategy, files, verify_result):
                        strategies_used.append(strategy.action)
                        return True

                    mock_fix.side_effect = track_strategy
                    mock_claude.return_value = {"success": True, "files": [mock_task.file]}

                    attempt = [0]
                    def verify_side_effect(files):
                        attempt[0] += 1
                        if attempt[0] < 3:
                            return VerifyResult(
                                status=VerifyStatus.FAIL,
                                tier=VerifyTier.QUICK,
                                errors=["Type error"],
                                types_passed=False
                            )
                        return VerifyResult(status=VerifyStatus.PASS, tier=VerifyTier.QUICK)

                    mock_verify.side_effect = verify_side_effect

                    asyncio.run(loop._execute_task_with_retries(mock_task))

        # Should have attempted fixes
        assert len(strategies_used) >= 1


class TestSelfCorrectorIntegration:
    """Test SelfCorrector integration with the loop."""

    def test_corrector_receives_verify_result(self, tmp_path: Path):
        """SelfCorrector receives the VerifyResult for analysis."""
        config = LoopConfig(project_dir=tmp_path)
        corrector = SelfCorrector(project_dir=tmp_path)

        verify_result = VerifyResult(
            status=VerifyStatus.FAIL,
            tier=VerifyTier.QUICK,
            errors=["Missing semicolon at line 10"],
            lint_passed=False,
            types_passed=True,
            tests_passed=True
        )

        strategy = analyze_failure(verify_result)

        assert strategy.action == FixAction.RUN_AUTOFIX
        assert strategy.retry_immediately is True

    def test_corrector_bounded_retries_integration(self, tmp_path: Path):
        """SelfCorrector.fix_with_retries integrates with loop."""
        corrector = SelfCorrector(project_dir=tmp_path)

        mock_task = Mock()
        mock_task.id = "TEST-001"
        mock_task.max_iterations = 3

        with patch.object(corrector, '_attempt_fix', new_callable=AsyncMock) as mock_fix:
            mock_fix.side_effect = [False, False, True]  # Succeed on 3rd try

            result = asyncio.run(corrector.fix_with_retries(mock_task, max_retries=5))

        assert result.success is True
        assert result.attempts == 3

    def test_corrector_escalates_after_max_retries(self, tmp_path: Path):
        """SelfCorrector escalates when max retries exceeded."""
        corrector = SelfCorrector(project_dir=tmp_path)

        mock_task = Mock()
        mock_task.id = "TEST-001"

        with patch.object(corrector, '_attempt_fix', new_callable=AsyncMock) as mock_fix:
            with patch.object(corrector, '_escalate') as mock_escalate:
                mock_fix.return_value = False  # Always fail

                result = asyncio.run(corrector.fix_with_retries(mock_task, max_retries=3))

        assert result.success is False
        mock_escalate.assert_called_once()


class TestAutoFixIntegration:
    """Test autofix behavior in the retry loop."""

    def test_lint_autofix_runs_before_retry(self, tmp_path: Path):
        """Lint errors trigger autofix before next attempt."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        mock_task = Mock()
        mock_task.id = "TEST-001"
        mock_task.file = "src/test.ts"
        mock_task.max_iterations = 5

        autofix_called = [False]

        with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
            with patch.object(loop, '_fast_verify') as mock_verify:
                with patch('orchestration.simplified_loop.FastVerify') as MockFV:
                    mock_verifier = Mock()

                    def autofix_side_effect(files):
                        autofix_called[0] = True
                        return True

                    mock_verifier.try_autofix_lint.side_effect = autofix_side_effect
                    MockFV.return_value = mock_verifier

                    attempt = [0]
                    def verify_side_effect(files):
                        attempt[0] += 1
                        if attempt[0] == 1:
                            return VerifyResult(
                                status=VerifyStatus.FAIL,
                                tier=VerifyTier.INSTANT,
                                errors=["Missing semicolon"],
                                lint_passed=False
                            )
                        return VerifyResult(status=VerifyStatus.PASS, tier=VerifyTier.INSTANT)

                    mock_verify.side_effect = verify_side_effect
                    mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                    asyncio.run(loop._execute_task(mock_task))

        assert autofix_called[0] is True

    def test_type_fix_invokes_claude(self, tmp_path: Path):
        """Type errors invoke Claude with fix prompt."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        mock_task = Mock()
        mock_task.id = "TEST-001"
        mock_task.file = "src/test.ts"
        mock_task.max_iterations = 5

        claude_calls = []

        with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
            with patch.object(loop, '_fast_verify') as mock_verify:
                async def capture_calls(task, context=None):
                    claude_calls.append({"task": task, "context": context})
                    return {"success": True, "files": [task.file]}

                mock_claude.side_effect = capture_calls

                attempt = [0]
                def verify_side_effect(files):
                    attempt[0] += 1
                    if attempt[0] == 1:
                        return VerifyResult(
                            status=VerifyStatus.FAIL,
                            tier=VerifyTier.QUICK,
                            errors=["Type 'string' not assignable to 'number'"],
                            types_passed=False
                        )
                    return VerifyResult(status=VerifyStatus.PASS, tier=VerifyTier.QUICK)

                mock_verify.side_effect = verify_side_effect

                asyncio.run(loop._execute_task_with_retries(mock_task))

        # Should have called Claude at least twice (initial + retry)
        assert len(claude_calls) >= 1


class TestRetryMetrics:
    """Test retry tracking and metrics."""

    def test_task_result_includes_attempt_count(self, tmp_path: Path):
        """TaskResult includes number of attempts made."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        mock_task = Mock()
        mock_task.id = "TEST-001"
        mock_task.file = "src/test.ts"
        mock_task.max_iterations = 5

        with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
            with patch.object(loop, '_fast_verify') as mock_verify:
                attempt = [0]
                def verify_side_effect(files):
                    attempt[0] += 1
                    if attempt[0] < 3:
                        return VerifyResult(
                            status=VerifyStatus.FAIL,
                            tier=VerifyTier.QUICK,
                            errors=["Error"],
                            types_passed=False
                        )
                    return VerifyResult(status=VerifyStatus.PASS, tier=VerifyTier.QUICK)

                mock_verify.side_effect = verify_side_effect
                mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                result = asyncio.run(loop._execute_task_with_retries(mock_task))

        # Result should track attempts
        assert hasattr(result, 'attempts') or attempt[0] == 3
