"""
Simplified Autonomous Loop (Phase 1)

A clean, minimal autonomous loop following Anthropic's proven patterns.
Target: <100 lines of core logic.

Usage:
    from orchestration.simplified_loop import SimplifiedLoop, LoopConfig

    config = LoopConfig(project_dir=Path("/path/to/project"))
    loop = SimplifiedLoop(config)
    result = await loop.run()
"""

import asyncio
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any

from tasks.work_queue import WorkQueue, Task


@dataclass
class LoopConfig:
    """Configuration for the simplified loop."""
    project_dir: Path
    max_iterations: int = 50
    auto_commit: bool = True
    work_queue_path: Optional[Path] = None

    def __post_init__(self) -> None:
        if self.work_queue_path is None:
            self.work_queue_path = self.project_dir / "tasks" / "work_queue.json"


@dataclass
class TaskResult:
    """Result of executing a single task."""
    task_id: str
    success: bool
    error: Optional[str] = None
    files_changed: Optional[List[str]] = field(default_factory=list)


@dataclass
class LoopResult:
    """Result of running the full loop."""
    completed: int = 0
    failed: int = 0
    blocked: int = 0
    iterations: int = 0

    def summary(self) -> str:
        return f"Completed: {self.completed}, Failed: {self.failed}, Blocked: {self.blocked}"


class SimplifiedLoop:
    """
    Simplified autonomous loop.

    Core loop:
    1. Load work queue
    2. Get next task (in-progress or pending)
    3. Execute task
    4. Verify result
    5. Commit on success
    6. Update progress
    7. Repeat until queue empty or max iterations
    """

    def __init__(self, config: LoopConfig):
        self.config = config
        self.iterations = 0
        self._result = LoopResult()

    async def run(self) -> LoopResult:
        """Run the autonomous loop."""
        queue = self._load_queue()
        self._ensure_progress_file()

        while self.iterations < self.config.max_iterations:
            # Get next task
            task = queue.get_in_progress() or queue.get_next_pending()
            if not task:
                break

            # Mark as in progress
            if task.status == "pending":
                queue.mark_in_progress(task.id)
                assert self.config.work_queue_path is not None
                queue.save(self.config.work_queue_path)

            # Execute task
            try:
                result = await self._execute_task(task)

                if result.success:
                    queue.mark_complete(task.id, "PASS", result.files_changed)
                    self._result.completed += 1
                    self._update_progress(task, "complete", "Task completed successfully")

                    if self.config.auto_commit and result.files_changed:
                        await self._git_commit(task, result.files_changed)
                else:
                    queue.update_progress(task.id, result.error)
                    self._result.failed += 1
                    self._update_progress(task, "failed", result.error or "Unknown error")

            except Exception as e:
                error_msg = str(e)
                if "BLOCKED" in error_msg:
                    queue.mark_blocked(task.id, error_msg)
                    self._result.blocked += 1
                    self._update_progress(task, "blocked", error_msg)
                else:
                    queue.update_progress(task.id, error_msg)
                    self._result.failed += 1

            assert self.config.work_queue_path is not None
            queue.save(self.config.work_queue_path)
            self.iterations += 1
            self._result.iterations = self.iterations

        return self._result

    def _load_queue(self) -> WorkQueue:
        """Load work queue from file."""
        assert self.config.work_queue_path is not None
        return WorkQueue.load(self.config.work_queue_path)

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute a single task."""
        # Run Claude Code to implement the task
        claude_result = await self._run_claude_code(task)

        # Verify the result
        verify_result = self._fast_verify(claude_result.get("files", []))

        return TaskResult(
            task_id=task.id,
            success=verify_result.passed if hasattr(verify_result, 'passed') else True,
            files_changed=claude_result.get("files", []),
            error=verify_result.error if hasattr(verify_result, 'error') else None
        )

    async def _run_claude_code(self, task: Task) -> dict[str, Any]:
        """Run Claude Code CLI for the task."""
        # Placeholder - would invoke Claude Code CLI
        return {"success": True, "files": [task.file]}

    def _fast_verify(self, files: List[str]) -> Any:
        """Fast verification of changes."""
        # Placeholder - would use FastVerify with files
        if files:  # Will be used when FastVerify is integrated
            pass
        result = type('VerifyResult', (), {'passed': True, 'error': None})()
        return result

    async def _git_commit(self, task: Task, files: List[str]) -> None:
        """Commit changes to git."""
        try:
            # Stage files
            subprocess.run(
                ["git", "add"] + files,
                cwd=self.config.project_dir,
                check=True,
                capture_output=True
            )
            # Commit
            subprocess.run(
                ["git", "commit", "-m", f"Complete: {task.description}"],
                cwd=self.config.project_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            pass  # Ignore commit failures (nothing to commit, etc.)

    def _ensure_progress_file(self) -> None:
        """Ensure progress file exists."""
        progress_file = self.config.project_dir / "claude-progress.txt"
        if not progress_file.exists():
            progress_file.write_text(f"# Progress Log\n\nStarted: {datetime.now().isoformat()}\n")

    def _update_progress(self, task: Task, status: str, details: str) -> None:
        """Update progress file with task status."""
        progress_file = self.config.project_dir / "claude-progress.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        status_emoji = {"complete": "✅", "failed": "❌", "blocked": "🛑"}.get(status, "🔄")
        entry = f"\n## {timestamp}\n- [{status_emoji}] {task.id}: {task.description}\n  - {details}\n"

        with progress_file.open("a") as f:
            f.write(entry)
