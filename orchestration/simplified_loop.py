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
from ralph.fast_verify import FastVerify, VerifyResult, VerifyStatus, VerifyTier
from agents.self_correct import SelfCorrector, analyze_failure, FixAction
from monitoring.metrics import MetricsCollector, generate_dashboard, DashboardData


@dataclass
class LoopConfig:
    """Configuration for the simplified loop."""
    project_dir: Path
    max_iterations: int = 50
    auto_commit: bool = True
    work_queue_path: Optional[Path] = None
    enable_metrics: bool = True  # Enable metrics collection

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
    attempts: int = 1


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
        self._metrics: Optional[MetricsCollector] = None
        if config.enable_metrics:
            metrics_dir = config.project_dir / ".metrics"
            self._metrics = MetricsCollector(storage_dir=metrics_dir)

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

            # Execute task with retries
            start_time = datetime.now()
            if self._metrics:
                self._metrics.task_started(task.id, project=str(self.config.project_dir.name))

            try:
                result = await self._execute_task_with_retries(task)
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                if result.success:
                    queue.mark_complete(task.id, "PASS", result.files_changed)
                    self._result.completed += 1
                    self._update_progress(task, "complete", "Task completed successfully")
                    if self._metrics:
                        self._metrics.task_completed(task.id, duration_ms=duration_ms)

                    if self.config.auto_commit and result.files_changed:
                        await self._git_commit(task, result.files_changed)
                else:
                    queue.update_progress(task.id, result.error)
                    self._result.failed += 1
                    self._update_progress(task, "failed", result.error or "Unknown error")
                    if self._metrics:
                        self._metrics.task_failed(task.id, error_type="verification", error=result.error or "")

            except Exception as e:
                error_msg = str(e)
                if "BLOCKED" in error_msg:
                    queue.mark_blocked(task.id, error_msg)
                    self._result.blocked += 1
                    self._update_progress(task, "blocked", error_msg)
                    if self._metrics:
                        self._metrics.task_failed(task.id, error_type="blocked", error=error_msg)
                else:
                    queue.update_progress(task.id, error_msg)
                    self._result.failed += 1
                    if self._metrics:
                        self._metrics.task_failed(task.id, error_type="exception", error=error_msg)

            assert self.config.work_queue_path is not None
            queue.save(self.config.work_queue_path)
            self.iterations += 1
            self._result.iterations = self.iterations

        # Flush metrics at end of run
        if self._metrics:
            self._metrics.flush()

        return self._result

    def get_metrics_collector(self) -> Optional[MetricsCollector]:
        """Get the metrics collector for dashboard generation."""
        return self._metrics

    def get_dashboard(self) -> Optional[DashboardData]:
        """Generate dashboard data from collected metrics."""
        if self._metrics:
            return generate_dashboard(self._metrics)
        return None

    def _load_queue(self) -> WorkQueue:
        """Load work queue from file."""
        assert self.config.work_queue_path is not None
        return WorkQueue.load(self.config.work_queue_path)

    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute a single task with self-correction."""
        # Run Claude Code to implement the task
        claude_result = await self._run_claude_code(task)
        files = claude_result.get("files", [])

        # Verify the result
        verify_result = self._fast_verify(files)

        # Check if verification passed
        if verify_result.status == VerifyStatus.PASS:
            return TaskResult(
                task_id=task.id,
                success=True,
                files_changed=files
            )

        # Attempt self-correction
        corrector = SelfCorrector(self.config.project_dir)
        strategy = analyze_failure(verify_result)

        # Try autofix for lint errors
        if strategy.action == FixAction.RUN_AUTOFIX:
            verifier = FastVerify(self.config.project_dir)
            if verifier.try_autofix_lint(files):
                # Re-verify after autofix
                verify_result = self._fast_verify(files)
                if verify_result.status == VerifyStatus.PASS:
                    return TaskResult(
                        task_id=task.id,
                        success=True,
                        files_changed=files
                    )

        # Return failure with error details
        error_msg = "\n".join(verify_result.errors) if verify_result.errors else "Verification failed"
        return TaskResult(
            task_id=task.id,
            success=False,
            files_changed=files,
            error=error_msg
        )

    async def _execute_task_with_retries(self, task: Task) -> TaskResult:
        """Execute a task with bounded retries and self-correction."""
        max_retries = getattr(task, 'max_iterations', 5)
        previous_errors: List[str] = []
        files: List[str] = []

        for attempt in range(1, max_retries + 1):
            # Run Claude Code with context from previous attempts
            context = self._build_retry_context(previous_errors, attempt) if attempt > 1 else None
            claude_result = await self._run_claude_code(task, context=context)
            files = claude_result.get("files", [])

            # Verify the result
            verify_result = self._fast_verify(files)

            # Success - return immediately
            if verify_result.status == VerifyStatus.PASS:
                return TaskResult(
                    task_id=task.id,
                    success=True,
                    files_changed=files,
                    attempts=attempt
                )

            # Analyze failure and determine strategy
            strategy = analyze_failure(verify_result)

            # Escalate immediately for unknown errors
            if strategy.action == FixAction.ESCALATE:
                raise Exception(f"BLOCKED: {strategy.reason}")

            # Try to apply fix
            fix_success = await self._apply_fix_strategy(strategy, files, verify_result)

            if fix_success:
                # Re-verify after fix
                verify_result = self._fast_verify(files)
                if verify_result.status == VerifyStatus.PASS:
                    return TaskResult(
                        task_id=task.id,
                        success=True,
                        files_changed=files,
                        attempts=attempt
                    )

            # Track error for next attempt
            if verify_result.errors:
                previous_errors.extend(verify_result.errors)

        # Exhausted retries
        error_msg = "\n".join(previous_errors[-5:]) if previous_errors else "Max retries exceeded"
        return TaskResult(
            task_id=task.id,
            success=False,
            files_changed=files,
            error=error_msg,
            attempts=max_retries
        )

    async def _apply_fix_strategy(
        self, strategy: Any, files: List[str], verify_result: VerifyResult
    ) -> bool:
        """Apply a fix strategy and return success status."""
        if strategy.action == FixAction.RUN_AUTOFIX:
            verifier = FastVerify(self.config.project_dir)
            return verifier.try_autofix_lint(files)

        # For type/implementation fixes, we'll retry with Claude
        # The context will be passed in the next iteration
        return False

    def _build_retry_context(self, previous_errors: List[str], attempt: int) -> str:
        """Build context for retry attempts."""
        context_parts = [f"Retry attempt {attempt}."]
        if previous_errors:
            context_parts.append("Previous errors to fix:")
            for error in previous_errors[-3:]:  # Last 3 errors
                context_parts.append(f"  - {error}")
        return "\n".join(context_parts)

    async def _run_claude_code(
        self, task: Task, context: Optional[str] = None
    ) -> dict[str, Any]:
        """Run Claude Code CLI for the task."""
        # Build prompt for Claude
        prompt_parts = [
            f"Task: {task.description}",
            f"File: {task.file}",
        ]

        if hasattr(task, 'tests') and task.tests:
            prompt_parts.append(f"Tests: {', '.join(task.tests)}")

        if context:
            prompt_parts.append(f"\n{context}")

        prompt = "\n".join(prompt_parts)

        # Run Claude Code CLI
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--allowedTools", "Edit,Read,Bash,Write"],
                cwd=self.config.project_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Get changed files from git
            changed = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.config.project_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            files = [f.strip() for f in changed.stdout.split('\n') if f.strip()]

            return {
                "success": result.returncode == 0,
                "files": files if files else [task.file],
                "output": result.stdout
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "files": [], "error": "Claude CLI timeout"}
        except FileNotFoundError:
            # Claude CLI not installed - return mock for testing
            return {"success": True, "files": [task.file]}

    def _fast_verify(self, files: List[str]) -> VerifyResult:
        """Fast verification of changes using tiered verification."""
        verifier = FastVerify(self.config.project_dir)

        # Select appropriate tier based on change size
        tier = verifier.select_tier(files)

        # Run verification at selected tier
        if tier == VerifyTier.INSTANT:
            return verifier.verify_instant(files)
        elif tier == VerifyTier.QUICK:
            return verifier.verify_quick(files)
        elif tier == VerifyTier.RELATED:
            return verifier.verify_related(files)
        else:
            return verifier.verify_full()

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
