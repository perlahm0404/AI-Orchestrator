"""
CLI Process Manager - Handles serialization and cleanup for Claude CLI processes

Provides:
- Serialization queue to prevent concurrent CLI runs ("database locked" errors)
- Zombie process cleanup to prevent accumulation
- Thread-safe process management

Based on patterns from OpenClaw (anthropics/universal-orchestration)
"""

import asyncio
import os
import signal
import subprocess
from typing import Any, Awaitable, Callable, Dict, TypeVar, Optional

T = TypeVar("T")


class CliProcessManager:
    """
    Manages Claude CLI process execution with serialization and cleanup.

    Prevents concurrent CLI runs which can cause "database locked" errors
    when multiple processes access the same SQLite session database.
    """

    _lock: asyncio.Lock = asyncio.Lock()
    _cleanup_interval: int = 10  # Run cleanup every N CLI executions

    def __init__(self) -> None:
        """Initialize the CLI process manager."""
        self._execution_count = 0

    @classmethod
    async def run_serialized(
        cls,
        task_fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Run a task with serialization (one CLI process at a time).

        This prevents "database locked" errors when multiple Claude CLI
        processes try to access the same session database simultaneously.

        Args:
            task_fn: Async function to execute
            *args: Positional arguments for task_fn
            **kwargs: Keyword arguments for task_fn

        Returns:
            Result from task_fn execution
        """
        async with cls._lock:
            result = await task_fn(*args, **kwargs)

            # Periodically cleanup zombie processes
            cls._execution_count = getattr(cls, "_execution_count", 0) + 1
            if cls._execution_count % cls._cleanup_interval == 0:
                cls.cleanup_zombie_processes()

            return result

    @staticmethod
    def cleanup_zombie_processes() -> None:
        """
        Kill zombie Claude processes (status 'T' = stopped/suspended).

        Zombie processes can accumulate when CLI sessions are interrupted
        or not properly closed. This prevents process accumulation and
        potential resource exhaustion.

        Tries to use psutil if available, falls back to manual cleanup.
        """
        try:
            # Try using psutil for better process detection
            import psutil  # type: ignore[import-untyped]

            killed_count = 0
            for proc in psutil.process_iter(["pid", "name", "status"]):
                try:
                    if (
                        proc.info["name"] == "claude"
                        and proc.info["status"] == psutil.STATUS_STOPPED
                    ):
                        proc.kill()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed_count > 0:
                print(f"🧹 Cleaned up {killed_count} zombie Claude process(es)")

        except ImportError:
            # Fallback: Try to kill processes using ps and kill commands (Unix-like systems)
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "claude"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.stdout:
                    pids = result.stdout.strip().split("\n")
                    for pid in pids:
                        if pid:
                            try:
                                os.kill(int(pid), signal.SIGTERM)
                            except (ProcessLookupError, ValueError):
                                pass
            except (FileNotFoundError, subprocess.TimeoutExpired):
                # pgrep not available or timeout
                pass
        except Exception as e:
            # Silently fail - cleanup is best-effort
            pass

    @staticmethod
    def get_active_claude_processes() -> int:
        """
        Get the number of currently active Claude CLI processes.

        Returns:
            Number of active Claude processes
        """
        try:
            import psutil

            count = 0
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == "claude":
                    count += 1
            return count
        except (ImportError, Exception):
            # Fall back to manual counting
            try:
                result = subprocess.run(
                    ["pgrep", "-c", "-f", "claude"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return int(result.stdout.strip()) if result.stdout.strip() else 0
            except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
                return 0
