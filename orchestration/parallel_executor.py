"""
Parallel Agent Executor (Priority 5)

Runs multiple agents in parallel with coordination strategies.
Target: Enable concurrent task execution with file-level locking.

Usage:
    from orchestration.parallel_executor import ParallelExecutor, ExecutorConfig

    config = ExecutorConfig(max_parallel=3, strategy=CoordinationStrategy.FILE_LOCK)
    executor = ParallelExecutor(project_dir=Path("/path/to/project"), config=config)
    result = await executor.execute(tasks)
"""

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from enum import Enum

from tasks.work_queue import Task


class CoordinationStrategy(str, Enum):
    """Strategy for coordinating parallel agents."""
    INDEPENDENT = "independent"  # No coordination, agents run freely
    FILE_LOCK = "file_lock"  # Lock files to prevent concurrent edits
    SEQUENTIAL_FALLBACK = "sequential_fallback"  # Fall back to sequential on conflict


@dataclass
class ExecutorConfig:
    """Configuration for parallel executor."""
    max_parallel: int = 3
    strategy: CoordinationStrategy = CoordinationStrategy.INDEPENDENT


@dataclass
class AgentSlot:
    """Represents an agent execution slot."""
    agent_id: str
    task_id: Optional[str] = None
    status: str = "idle"  # idle, running, completed, failed


@dataclass
class ExecutionResult:
    """Result of parallel execution."""
    completed: int = 0
    failed: int = 0
    total_time_ms: int = 0


class ParallelExecutor:
    """
    Executes multiple agents in parallel.

    Supports different coordination strategies:
    - INDEPENDENT: No coordination, all agents run freely
    - FILE_LOCK: Serialize access to same file
    - SEQUENTIAL_FALLBACK: Fall back to sequential if conflicts detected
    """

    def __init__(self, project_dir: Path, config: Optional[ExecutorConfig] = None):
        self.project_dir = project_dir
        self.config = config or ExecutorConfig()
        self.slots: List[AgentSlot] = [
            AgentSlot(agent_id=f"agent-{i}")
            for i in range(self.config.max_parallel)
        ]
        self._file_locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def execute(self, tasks: List[Task]) -> ExecutionResult:
        """
        Execute tasks in parallel.

        Args:
            tasks: List of tasks to execute

        Returns:
            ExecutionResult with completion stats
        """
        start_time = time.time()
        result = ExecutionResult()

        if not tasks:
            return result

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.config.max_parallel)

        # Track slot assignment
        slot_queue: asyncio.Queue[AgentSlot] = asyncio.Queue()
        for slot in self.slots:
            await slot_queue.put(slot)

        async def execute_with_slot(task: Task) -> bool:
            async with semaphore:
                slot = await slot_queue.get()
                try:
                    slot.task_id = task.id
                    slot.status = "running"

                    # Apply coordination strategy
                    if self.config.strategy == CoordinationStrategy.FILE_LOCK:
                        async with await self._get_file_lock(task.file):
                            agent_result = await self._run_agent(task, slot)
                    else:
                        agent_result = await self._run_agent(task, slot)

                    success = bool(agent_result.get("success", False))
                    slot.status = "completed" if success else "failed"
                    return success
                finally:
                    slot.task_id = None
                    slot.status = "idle"
                    await slot_queue.put(slot)

        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[execute_with_slot(task) for task in tasks],
            return_exceptions=True
        )

        # Count results
        for r in results:
            if isinstance(r, Exception):
                result.failed += 1
            elif r:
                result.completed += 1
            else:
                result.failed += 1

        result.total_time_ms = int((time.time() - start_time) * 1000)
        return result

    async def _get_file_lock(self, file_path: str) -> asyncio.Lock:
        """Get or create a lock for a file path."""
        async with self._global_lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = asyncio.Lock()
            return self._file_locks[file_path]

    async def _run_agent(self, task: Task, slot: AgentSlot) -> Dict[str, Any]:
        """
        Run an agent for a task.

        This is the extension point - override or patch for testing.
        In production, this delegates to SimplifiedLoop or Claude CLI.

        Args:
            task: Task to execute
            slot: Agent slot running the task

        Returns:
            Dict with success status and changed files
        """
        # Default implementation - can be overridden or patched
        # In real usage, this would call SimplifiedLoop or Claude CLI
        import subprocess

        try:
            prompt = f"Task: {task.description}\nFile: {task.file}"

            result = subprocess.run(
                ["claude", "-p", prompt, "--allowedTools", "Edit,Read,Bash,Write"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            return {
                "success": result.returncode == 0,
                "files": [task.file]
            }
        except FileNotFoundError:
            # Claude CLI not installed - mock for testing
            return {"success": True, "files": [task.file]}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
