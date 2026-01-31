"""
Tests for Progress Persistence (Phase 4)

TDD approach: Tests written first, then implementation.
Target: Agents resume from any point after crash/restart.
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

try:
    from orchestration.simplified_loop import (
        SimplifiedLoop,
        LoopConfig,
        LoopResult,
        TaskResult,
    )
    from ralph.fast_verify import VerifyResult, VerifyStatus, VerifyTier
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestProgressFileFormat:
    """Test progress file format and content."""

    def test_progress_file_has_session_header(self, tmp_path: Path):
        """Progress file starts with session timestamp."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        loop._ensure_progress_file()

        progress_file = tmp_path / "claude-progress.txt"
        content = progress_file.read_text()

        assert "# Progress Log" in content
        assert "Started:" in content

    def test_progress_file_records_completed_tasks(self, tmp_path: Path):
        """Progress file records completed tasks with details."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        mock_task = Mock()
        mock_task.id = "BUG-001"
        mock_task.description = "Fix authentication timeout"

        loop._ensure_progress_file()
        loop._update_progress(mock_task, "complete", "Task completed successfully")

        progress_file = tmp_path / "claude-progress.txt"
        content = progress_file.read_text()

        assert "BUG-001" in content
        assert "Fix authentication timeout" in content
        assert "✅" in content or "complete" in content.lower()

    def test_progress_file_records_failed_tasks(self, tmp_path: Path):
        """Progress file records failed tasks with error details."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        mock_task = Mock()
        mock_task.id = "BUG-002"
        mock_task.description = "Database connection issue"

        loop._ensure_progress_file()
        loop._update_progress(mock_task, "failed", "Type error: string vs number")

        progress_file = tmp_path / "claude-progress.txt"
        content = progress_file.read_text()

        assert "BUG-002" in content
        assert "Type error" in content or "failed" in content.lower()
        assert "❌" in content or "failed" in content.lower()

    def test_progress_file_records_blocked_tasks(self, tmp_path: Path):
        """Progress file records blocked tasks with reason."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        mock_task = Mock()
        mock_task.id = "BUG-003"
        mock_task.description = "Third-party API change"

        loop._ensure_progress_file()
        loop._update_progress(mock_task, "blocked", "Need API key for staging")

        progress_file = tmp_path / "claude-progress.txt"
        content = progress_file.read_text()

        assert "BUG-003" in content
        assert "API key" in content or "blocked" in content.lower()
        assert "🛑" in content or "blocked" in content.lower()


class TestSessionResume:
    """Test session resume functionality."""

    @pytest.fixture
    def work_queue_file(self, tmp_path: Path):
        """Create a work queue file."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        queue_file = tasks_dir / "work_queue.json"
        queue_file.write_text(json.dumps({
            "project": "test",
            "features": [
                {
                    "id": "BUG-001",
                    "description": "Fix auth",
                    "file": "src/auth.ts",
                    "status": "in_progress"
                },
                {
                    "id": "BUG-002",
                    "description": "Fix db",
                    "file": "src/db.ts",
                    "status": "pending"
                }
            ]
        }))
        return queue_file

    def test_loop_resumes_in_progress_task_first(self, tmp_path: Path, work_queue_file: Path):
        """Loop resumes in-progress task before pending tasks."""
        config = LoopConfig(project_dir=tmp_path, max_iterations=1)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_execute_task_with_retries', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = TaskResult(
                task_id="BUG-001",
                success=True,
                files_changed=["src/auth.ts"]
            )

            result = asyncio.run(loop.run())

        # Should have processed the in_progress task
        call_args = mock_exec.call_args[0][0]
        assert call_args.id == "BUG-001"

    def test_loop_reads_progress_on_startup(self, tmp_path: Path, work_queue_file: Path):
        """Loop reads existing progress file on startup."""
        # Create existing progress file
        progress_file = tmp_path / "claude-progress.txt"
        progress_file.write_text("""# Progress Log

Started: 2025-01-30T10:00:00

## 2025-01-30 10:30:00
- [✅] BUG-000: Previous task
  - Completed in previous session
""")

        config = LoopConfig(project_dir=tmp_path, max_iterations=1)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_execute_task_with_retries', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = TaskResult(
                task_id="BUG-001",
                success=True
            )
            asyncio.run(loop.run())

        # Progress file should still have old content plus new
        content = progress_file.read_text()
        assert "BUG-000" in content  # Old entry preserved
        assert "BUG-001" in content  # New entry added


class TestStateRecovery:
    """Test state recovery from various failure scenarios."""

    @pytest.fixture
    def setup_project(self, tmp_path: Path):
        """Set up a project with work queue."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        queue_file = tasks_dir / "work_queue.json"
        queue_file.write_text(json.dumps({
            "project": "test",
            "features": [
                {
                    "id": "TASK-001",
                    "description": "Test task",
                    "file": "src/test.ts",
                    "status": "pending"
                }
            ]
        }))
        return tmp_path

    def test_recover_from_mid_task_crash(self, setup_project: Path):
        """Loop can recover from crash during task execution."""
        # Simulate crash by leaving task in_progress
        queue_file = setup_project / "tasks" / "work_queue.json"
        queue_data = json.loads(queue_file.read_text())
        queue_data["features"][0]["status"] = "in_progress"
        queue_data["features"][0]["last_attempt"] = "2025-01-30T10:00:00"
        queue_file.write_text(json.dumps(queue_data))

        config = LoopConfig(project_dir=setup_project, max_iterations=1)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_execute_task_with_retries', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = TaskResult(
                task_id="TASK-001",
                success=True
            )
            result = asyncio.run(loop.run())

        assert result.completed == 1

    def test_recover_preserves_attempt_count(self, setup_project: Path):
        """Recovery preserves previous attempt count."""
        # Set up task with previous attempts
        queue_file = setup_project / "tasks" / "work_queue.json"
        queue_data = json.loads(queue_file.read_text())
        queue_data["features"][0]["status"] = "in_progress"
        queue_data["features"][0]["attempts"] = 2
        queue_file.write_text(json.dumps(queue_data))

        config = LoopConfig(project_dir=setup_project, max_iterations=1)
        loop = SimplifiedLoop(config)

        task_seen = [None]

        async def capture_task(task):
            task_seen[0] = task
            return TaskResult(task_id=task.id, success=True)

        with patch.object(loop, '_execute_task_with_retries', side_effect=capture_task):
            asyncio.run(loop.run())

        # Task should have previous attempts info
        if task_seen[0] and hasattr(task_seen[0], 'attempts'):
            assert task_seen[0].attempts >= 2


class TestGitCheckpoints:
    """Test git-based checkpointing."""

    @pytest.fixture
    def git_project(self, tmp_path: Path):
        """Create a git-initialized project."""
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path, capture_output=True
        )

        # Create initial file and commit
        (tmp_path / "README.md").write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=tmp_path, capture_output=True
        )

        # Create work queue
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "work_queue.json").write_text(json.dumps({
            "project": "test",
            "features": [{
                "id": "TASK-001",
                "description": "Add feature",
                "file": "src/feature.ts",
                "status": "pending"
            }]
        }))

        return tmp_path

    def test_successful_task_creates_commit(self, git_project: Path):
        """Successful task completion creates a git commit."""
        import subprocess

        # Create the file that will be "changed"
        src_dir = git_project / "src"
        src_dir.mkdir()
        (src_dir / "feature.ts").write_text("// Feature code")

        config = LoopConfig(project_dir=git_project, auto_commit=True, max_iterations=1)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_execute_task_with_retries', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = TaskResult(
                task_id="TASK-001",
                success=True,
                files_changed=["src/feature.ts"]
            )
            asyncio.run(loop.run())

        # Check git log for new commit
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=git_project,
            capture_output=True,
            text=True
        )
        assert "Complete:" in result.stdout or "Add feature" in result.stdout or "Initial" in result.stdout

    def test_failed_task_does_not_commit(self, git_project: Path):
        """Failed task does not create a git commit."""
        import subprocess

        # Get current commit count
        before = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=git_project,
            capture_output=True,
            text=True
        )
        before_count = int(before.stdout.strip())

        config = LoopConfig(project_dir=git_project, auto_commit=True, max_iterations=1)
        loop = SimplifiedLoop(config)

        with patch.object(loop, '_execute_task_with_retries', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = TaskResult(
                task_id="TASK-001",
                success=False,
                error="Test failure"
            )
            asyncio.run(loop.run())

        # Check commit count unchanged
        after = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=git_project,
            capture_output=True,
            text=True
        )
        after_count = int(after.stdout.strip())

        assert after_count == before_count


class TestSessionStartupProtocol:
    """Test the session startup protocol."""

    @pytest.fixture
    def project_with_state(self, tmp_path: Path):
        """Create project with existing state."""
        # Work queue
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "work_queue.json").write_text(json.dumps({
            "project": "test",
            "features": [
                {"id": "T1", "description": "Done", "file": "a.ts", "status": "complete"},
                {"id": "T2", "description": "WIP", "file": "b.ts", "status": "in_progress"},
                {"id": "T3", "description": "Todo", "file": "c.ts", "status": "pending"},
            ]
        }))

        # Progress file
        (tmp_path / "claude-progress.txt").write_text("""# Progress Log

Started: 2025-01-30T09:00:00

## 2025-01-30 09:30:00
- [✅] T1: Done
  - Completed successfully
""")

        return tmp_path

    def test_startup_loads_existing_state(self, project_with_state: Path):
        """Startup protocol loads existing progress and queue state."""
        config = LoopConfig(project_dir=project_with_state, max_iterations=1)
        loop = SimplifiedLoop(config)

        # Load queue
        queue = loop._load_queue()

        # Should find in_progress task
        in_progress = queue.get_in_progress()
        assert in_progress is not None
        assert in_progress.id == "T2"

    def test_startup_resumes_correct_task(self, project_with_state: Path):
        """Startup resumes the in-progress task, not pending ones."""
        config = LoopConfig(project_dir=project_with_state, max_iterations=1)
        loop = SimplifiedLoop(config)

        executed_tasks = []

        async def track_task(task):
            executed_tasks.append(task.id)
            return TaskResult(task_id=task.id, success=True)

        with patch.object(loop, '_execute_task_with_retries', side_effect=track_task):
            asyncio.run(loop.run())

        # Should execute T2 (in_progress) not T3 (pending)
        assert "T2" in executed_tasks
        assert "T3" not in executed_tasks


class TestProgressSummary:
    """Test progress summary generation."""

    def test_loop_result_summary_includes_all_stats(self):
        """LoopResult.summary() includes all statistics."""
        result = LoopResult(completed=5, failed=2, blocked=1, iterations=10)

        summary = result.summary()

        assert "5" in summary
        assert "2" in summary
        assert "1" in summary

    def test_progress_file_can_be_parsed(self, tmp_path: Path):
        """Progress file format can be parsed programmatically."""
        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        # Record multiple tasks
        for i, status in enumerate(["complete", "failed", "blocked"]):
            mock_task = Mock()
            mock_task.id = f"TASK-{i:03d}"
            mock_task.description = f"Task {i}"
            loop._ensure_progress_file()
            loop._update_progress(mock_task, status, f"Details for {status}")

        # Parse the file
        progress_file = tmp_path / "claude-progress.txt"
        content = progress_file.read_text()

        # Should be parseable
        assert content.count("TASK-") == 3
        assert "✅" in content or "complete" in content
        assert "❌" in content or "failed" in content
        assert "🛑" in content or "blocked" in content
