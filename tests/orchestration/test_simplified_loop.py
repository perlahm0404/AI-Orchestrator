"""
Tests for Simplified Autonomous Loop (Phase 1)

TDD approach: Tests written first, then implementation.
Target: <100 lines for core loop logic.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import Optional

# These imports will fail until we implement the modules
# That's expected with TDD - tests first!
try:
    from orchestration.simplified_loop import (
        SimplifiedLoop,
        LoopConfig,
        LoopResult,
        TaskResult,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    # Create placeholder classes for test definition
    @dataclass
    class LoopConfig:
        project_dir: Path
        max_iterations: int = 50
        auto_commit: bool = True

    @dataclass
    class TaskResult:
        task_id: str
        success: bool
        error: Optional[str] = None
        files_changed: list = None

    @dataclass
    class LoopResult:
        completed: int
        failed: int
        blocked: int
        iterations: int


# Skip all tests if implementation doesn't exist yet
pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestLoopConfig:
    """Test LoopConfig dataclass."""

    def test_default_values(self, tmp_path: Path):
        """Config has sensible defaults."""
        config = LoopConfig(project_dir=tmp_path)

        assert config.project_dir == tmp_path
        assert config.max_iterations == 50
        assert config.auto_commit is True

    def test_custom_values(self, tmp_path: Path):
        """Config accepts custom values."""
        config = LoopConfig(
            project_dir=tmp_path,
            max_iterations=100,
            auto_commit=False
        )

        assert config.max_iterations == 100
        assert config.auto_commit is False


class TestSimplifiedLoop:
    """Test SimplifiedLoop class."""

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

    def test_loop_initialization(self, tmp_path: Path):
        """Loop initializes with config."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        assert loop.config == config
        assert loop.iterations == 0

    def test_loop_exits_when_queue_empty(self, tmp_path: Path, mock_work_queue):
        """Loop exits cleanly when no tasks."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            result = asyncio.run(loop.run())

        assert result.completed == 0
        assert result.iterations == 0

    def test_loop_processes_pending_task(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop processes a pending task."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path, max_iterations=5)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_execute_task', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = TaskResult(
                    task_id="TEST-001",
                    success=True,
                    files_changed=["src/test.ts"]
                )
                result = asyncio.run(loop.run())

        assert result.completed == 1
        mock_work_queue.mark_complete.assert_called_once()

    def test_loop_resumes_in_progress_task(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop resumes an in-progress task."""
        mock_task.status = "in_progress"
        # Return task once, then None (task completed)
        mock_work_queue.get_in_progress.side_effect = [mock_task, None]
        mock_work_queue.get_next_pending.return_value = None

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_execute_task', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = TaskResult(
                    task_id="TEST-001",
                    success=True
                )
                result = asyncio.run(loop.run())

        # Should process the in-progress task
        mock_exec.assert_called_once()

    def test_loop_respects_max_iterations(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop stops after max iterations."""
        # Always return a pending task
        mock_work_queue.get_next_pending.return_value = mock_task
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path, max_iterations=3)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_execute_task', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = TaskResult(
                    task_id="TEST-001",
                    success=True
                )
                result = asyncio.run(loop.run())

        assert result.iterations <= 3

    def test_loop_handles_task_failure(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop handles failed task execution."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_execute_task', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = TaskResult(
                    task_id="TEST-001",
                    success=False,
                    error="Test failure"
                )
                result = asyncio.run(loop.run())

        assert result.failed == 1
        mock_work_queue.update_progress.assert_called()

    def test_loop_blocks_on_guardrail_violation(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop marks task as blocked on guardrail violation."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_execute_task', new_callable=AsyncMock) as mock_exec:
                mock_exec.side_effect = Exception("BLOCKED: Guardrail violation")
                result = asyncio.run(loop.run())

        assert result.blocked == 1
        mock_work_queue.mark_blocked.assert_called()

    def test_loop_commits_on_success(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop commits after successful task when auto_commit=True."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path, auto_commit=True)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_execute_task', new_callable=AsyncMock) as mock_exec:
                with patch.object(loop, '_git_commit', new_callable=AsyncMock) as mock_commit:
                    mock_exec.return_value = TaskResult(
                        task_id="TEST-001",
                        success=True,
                        files_changed=["src/test.ts"]
                    )
                    asyncio.run(loop.run())

        mock_commit.assert_called_once()

    def test_loop_skips_commit_when_disabled(self, tmp_path: Path, mock_work_queue, mock_task):
        """Loop does not commit when auto_commit=False."""
        mock_work_queue.get_next_pending.side_effect = [mock_task, None]
        mock_work_queue.get_in_progress.return_value = None

        config = LoopConfig(project_dir=tmp_path, auto_commit=False)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue', return_value=mock_work_queue):
            with patch.object(loop, '_execute_task', new_callable=AsyncMock) as mock_exec:
                with patch.object(loop, '_git_commit', new_callable=AsyncMock) as mock_commit:
                    mock_exec.return_value = TaskResult(
                        task_id="TEST-001",
                        success=True,
                        files_changed=["src/test.ts"]
                    )
                    asyncio.run(loop.run())

        mock_commit.assert_not_called()


class TestProgressTracking:
    """Test progress file tracking."""

    def test_progress_file_created(self, tmp_path: Path):
        """Progress file is created on first run."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_load_queue') as mock_load:
            mock_queue = Mock()
            mock_queue.get_next_pending.return_value = None
            mock_queue.get_in_progress.return_value = None
            mock_load.return_value = mock_queue

            asyncio.run(loop.run())

        progress_file = tmp_path / "claude-progress.txt"
        assert progress_file.exists()

    def test_progress_updated_on_task_complete(self, tmp_path: Path):
        """Progress file is updated when task completes."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        mock_task = Mock()
        mock_task.id = "TEST-001"
        mock_task.description = "Test task"
        mock_task.file = "test.py"
        mock_task.status = "pending"
        mock_task.max_iterations = 15

        with patch.object(loop, '_load_queue') as mock_load:
            mock_queue = Mock()
            mock_queue.get_next_pending.side_effect = [mock_task, None]
            mock_queue.get_in_progress.return_value = None
            mock_load.return_value = mock_queue

            with patch.object(loop, '_execute_task', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = TaskResult(
                    task_id="TEST-001",
                    success=True
                )
                asyncio.run(loop.run())

        progress_file = tmp_path / "claude-progress.txt"
        content = progress_file.read_text()
        assert "TEST-001" in content
        assert "Complete" in content or "✅" in content


class TestTaskExecution:
    """Test task execution logic."""

    def test_execute_task_returns_result(self, tmp_path: Path):
        """Task execution returns TaskResult."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        mock_task = Mock()
        mock_task.id = "TEST-001"
        mock_task.description = "Test"
        mock_task.file = "test.py"
        mock_task.max_iterations = 5

        with patch.object(loop, '_run_claude_code', new_callable=AsyncMock) as mock_claude:
            with patch.object(loop, '_fast_verify') as mock_verify:
                mock_claude.return_value = {"success": True, "files": ["test.py"]}
                mock_verify.return_value = Mock(passed=True)

                result = asyncio.run(loop._execute_task(mock_task))

        assert isinstance(result, TaskResult)
        assert result.task_id == "TEST-001"


class TestLoopResult:
    """Test LoopResult dataclass."""

    def test_loop_result_fields(self):
        """LoopResult has expected fields."""
        result = LoopResult(
            completed=5,
            failed=2,
            blocked=1,
            iterations=10
        )

        assert result.completed == 5
        assert result.failed == 2
        assert result.blocked == 1
        assert result.iterations == 10

    def test_loop_result_summary(self):
        """LoopResult can generate summary."""
        result = LoopResult(
            completed=5,
            failed=2,
            blocked=1,
            iterations=10
        )

        # If summary method exists
        if hasattr(result, 'summary'):
            summary = result.summary()
            assert "5" in summary  # completed count
            assert "2" in summary  # failed count
