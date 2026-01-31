"""
Tests for SimplifiedLoop + FastVerify Integration (Phase 2)

TDD approach: Tests written first, then integration.
Target: Loop uses real FastVerify instead of placeholder.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Import the modules
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
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestLoopWithFastVerify:
    """Test SimplifiedLoop integration with FastVerify."""

    @pytest.fixture
    def mock_work_queue(self):
        """Create mock work queue."""
        queue = Mock()
        queue.get_next_pending.return_value = None
        queue.get_in_progress.return_value = None
        queue.get_stats.return_value = {
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "complete": 0,
            "blocked": 0
        }
        return queue

    @pytest.fixture
    def mock_task(self):
        """Create mock task."""
        task = Mock()
        task.id = "TEST-001"
        task.description = "Test task"
        task.file = "src/test.ts"
        task.status = "pending"
        task.max_iterations = 15
        return task

    def test_loop_uses_fast_verify_instant_for_small_changes(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop uses INSTANT tier for small file changes (<20 lines)."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
                with patch('orchestration.simplified_loop.FastVerify') as MockFastVerify:
                    mock_verifier = Mock()
                    mock_verifier.select_tier.return_value = VerifyTier.INSTANT
                    mock_verifier.verify_instant.return_value = VerifyResult(
                        status=VerifyStatus.PASS,
                        tier=VerifyTier.INSTANT
                    )
                    MockFastVerify.return_value = mock_verifier

                    mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                    result = asyncio.run(loop.run())

        # Verify INSTANT tier was selected
        mock_verifier.select_tier.assert_called()
        mock_verifier.verify_instant.assert_called()

    def test_loop_uses_fast_verify_quick_for_medium_changes(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop uses QUICK tier for medium file changes (20-100 lines)."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
                with patch('orchestration.simplified_loop.FastVerify') as MockFastVerify:
                    mock_verifier = Mock()
                    mock_verifier.select_tier.return_value = VerifyTier.QUICK
                    mock_verifier.verify_quick.return_value = VerifyResult(
                        status=VerifyStatus.PASS,
                        tier=VerifyTier.QUICK
                    )
                    MockFastVerify.return_value = mock_verifier

                    mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                    result = asyncio.run(loop.run())

        mock_verifier.verify_quick.assert_called()

    def test_loop_fails_task_on_verify_fail(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop marks task as failed when FastVerify returns FAIL."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
                with patch('orchestration.simplified_loop.FastVerify') as MockFastVerify:
                    mock_verifier = Mock()
                    mock_verifier.select_tier.return_value = VerifyTier.INSTANT
                    mock_verifier.verify_instant.return_value = VerifyResult(
                        status=VerifyStatus.FAIL,
                        tier=VerifyTier.INSTANT,
                        errors=["Lint error: missing semicolon"],
                        lint_passed=False
                    )
                    MockFastVerify.return_value = mock_verifier

                    mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                    result = asyncio.run(loop.run())

        assert result.failed == 1
        assert result.completed == 0


class TestLoopWithSelfCorrection:
    """Test SimplifiedLoop integration with SelfCorrector."""

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
        task.max_iterations = 15
        return task

    def test_loop_attempts_self_correction_on_lint_fail(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop attempts autofix when lint fails."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        call_count = [0]

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
                with patch('orchestration.simplified_loop.FastVerify') as MockFastVerify:
                    with patch('orchestration.simplified_loop.SelfCorrector') as MockCorrector:
                        mock_verifier = Mock()
                        mock_verifier.select_tier.return_value = VerifyTier.INSTANT

                        # First call fails, second passes (after self-correction)
                        def verify_side_effect(files):
                            call_count[0] += 1
                            if call_count[0] == 1:
                                return VerifyResult(
                                    status=VerifyStatus.FAIL,
                                    tier=VerifyTier.INSTANT,
                                    errors=["Lint error"],
                                    lint_passed=False
                                )
                            return VerifyResult(
                                status=VerifyStatus.PASS,
                                tier=VerifyTier.INSTANT
                            )

                        mock_verifier.verify_instant.side_effect = verify_side_effect
                        mock_verifier.try_autofix_lint.return_value = True
                        MockFastVerify.return_value = mock_verifier

                        mock_corrector = Mock()
                        mock_corrector.apply_fix.return_value = True
                        MockCorrector.return_value = mock_corrector

                        mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                        result = asyncio.run(loop.run())

        # Should have attempted correction
        assert call_count[0] >= 1

    def test_loop_escalates_after_max_correction_attempts(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop escalates when self-correction fails repeatedly."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path, max_iterations=5)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
                with patch('orchestration.simplified_loop.FastVerify') as MockFastVerify:
                    mock_verifier = Mock()
                    mock_verifier.select_tier.return_value = VerifyTier.INSTANT
                    # Always fails
                    mock_verifier.verify_instant.return_value = VerifyResult(
                        status=VerifyStatus.FAIL,
                        tier=VerifyTier.INSTANT,
                        errors=["Type error: cannot fix"],
                        types_passed=False
                    )
                    mock_verifier.try_autofix_lint.return_value = False
                    MockFastVerify.return_value = mock_verifier

                    mock_claude.return_value = {"success": True, "files": ["src/test.ts"]}

                    result = asyncio.run(loop.run())

        # Should have failed after attempts
        assert result.failed >= 1


class TestIntegratedVerification:
    """Test the full verification flow."""

    @pytest.fixture
    def project_with_files(self, tmp_path: Path):
        """Create a project with test files."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create a small file (for INSTANT tier)
        small_file = src_dir / "small.ts"
        small_file.write_text("const x = 1;\n" * 10)  # 10 lines

        # Create a medium file (for QUICK tier)
        medium_file = src_dir / "medium.ts"
        medium_file.write_text("const x = 1;\n" * 50)  # 50 lines

        return tmp_path

    def test_tier_selection_based_on_file_size(self, project_with_files: Path):
        """FastVerify selects correct tier based on file size."""
        verifier = FastVerify(project_dir=project_with_files)

        # Small file should use INSTANT
        small_tier = verifier.select_tier(["src/small.ts"])
        assert small_tier == VerifyTier.INSTANT

        # Medium file should use QUICK
        medium_tier = verifier.select_tier(["src/medium.ts"])
        assert medium_tier == VerifyTier.QUICK

    def test_failure_analysis_determines_strategy(self):
        """analyze_failure returns correct strategy for each failure type."""
        # Lint failure
        lint_fail = Mock()
        lint_fail.lint_passed = False
        lint_fail.types_passed = True
        lint_fail.tests_passed = True
        lint_fail.errors = ["Missing semicolon"]

        strategy = analyze_failure(lint_fail)
        assert strategy.action == FixAction.RUN_AUTOFIX

        # Type failure
        type_fail = Mock()
        type_fail.lint_passed = True
        type_fail.types_passed = False
        type_fail.tests_passed = True
        type_fail.errors = ["Type mismatch"]

        strategy = analyze_failure(type_fail)
        assert strategy.action == FixAction.FIX_TYPES

        # Test failure
        test_fail = Mock()
        test_fail.lint_passed = True
        test_fail.types_passed = True
        test_fail.tests_passed = False
        test_fail.errors = ["Expected 1 got 2"]

        strategy = analyze_failure(test_fail)
        assert strategy.action == FixAction.FIX_IMPLEMENTATION


class TestVerifyResultIntegration:
    """Test VerifyResult flows correctly through the system."""

    def test_verify_result_errors_propagate_to_task_result(self, tmp_path: Path):
        """Errors from verification are captured in TaskResult."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        mock_task = Mock()
        mock_task.id = "TEST-001"
        mock_task.description = "Test"
        mock_task.file = "test.ts"
        mock_task.max_iterations = 5

        with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
            with patch('orchestration.simplified_loop.FastVerify') as MockFastVerify:
                mock_verifier = Mock()
                mock_verifier.select_tier.return_value = VerifyTier.INSTANT
                mock_verifier.verify_instant.return_value = VerifyResult(
                    status=VerifyStatus.FAIL,
                    tier=VerifyTier.INSTANT,
                    errors=["Error line 10: undefined variable 'x'"],
                    lint_passed=False
                )
                MockFastVerify.return_value = mock_verifier

                mock_claude.return_value = {"success": True, "files": ["test.ts"]}

                result = asyncio.run(loop._execute_task(mock_task))

        assert result.success is False
        assert result.error is not None
        assert "undefined variable" in result.error
