"""
Monitoring Integration for Autonomous Loop

Provides WebSocket event streaming integration for autonomous_loop.py
without modifying the core loop logic.

Usage:
    from orchestration.monitoring_integration import MonitoringIntegration

    # Initialize (starts WebSocket server in background)
    monitoring = MonitoringIntegration(enabled=True)
    await monitoring.start()

    # Stream events
    await monitoring.loop_start(project="karematch", max_iterations=100)
    await monitoring.task_start(task_id="task-001", description="Fix bug")
    await monitoring.task_complete(task_id="task-001", verdict="PASS", iterations=3)
    await monitoring.loop_complete(tasks_processed=10)

    # Cleanup
    await monitoring.stop()
"""

import asyncio
import logging
from typing import Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MonitoringIntegration:
    """
    Integration layer for autonomous loop monitoring.

    Starts WebSocket server and streams events to React dashboard.
    """

    def __init__(self, enabled: bool = False, port: int = 8080):
        """
        Initialize monitoring integration.

        Args:
            enabled: If True, start WebSocket server and stream events
            port: WebSocket server port (default: 8080)
        """
        self.enabled = enabled
        self.port = port
        self.server_task: Optional[asyncio.Task[Any]] = None
        self._stream_event: Optional[Any] = None  # Will be imported dynamically

    async def start(self) -> None:
        """
        Start WebSocket server in background.

        Only starts if enabled=True.
        """
        if not self.enabled:
            logger.info("📊 Monitoring disabled")
            return

        try:
            # Import WebSocket server components
            from orchestration.websocket_server import app, stream_event
            import uvicorn

            self._stream_event = stream_event

            # Start server in background task
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=self.port,
                log_level="warning"  # Reduce noise
            )
            server = uvicorn.Server(config)

            # Run server in background
            self.server_task = asyncio.create_task(server.serve())

            logger.info(f"✅ WebSocket server started at ws://localhost:{self.port}/ws")
            logger.info(f"📊 Monitoring dashboard: http://localhost:3000 (when UI is running)")

            # Give server time to start
            await asyncio.sleep(1)

        except ImportError as e:
            logger.error(f"❌ Failed to import WebSocket server: {e}")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Failed to start WebSocket server: {e}")
            self.enabled = False

    async def stop(self) -> None:
        """
        Stop WebSocket server.
        """
        if self.server_task and not self.server_task.done():
            logger.info("🛑 Stopping WebSocket server...")
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass

    async def loop_start(self, project: str, max_iterations: int, queue_type: str = "bugs") -> None:
        """
        Stream loop_start event.

        Args:
            project: Project name (karematch, credentialmate)
            max_iterations: Maximum iterations
            queue_type: Queue type (bugs, features)
        """
        if not self.enabled or not self._stream_event:
            return

        await self._stream_event("loop_start", {
            "project": project,
            "max_iterations": max_iterations,
            "queue_type": queue_type
        })

    async def task_start(
        self,
        task_id: str,
        description: str,
        file: str,
        attempts: int = 0,
        agent_type: str = "unknown"
    ) -> None:
        """
        Stream task_start event.

        Args:
            task_id: Task ID
            description: Task description
            file: Target file path
            attempts: Number of attempts so far
            agent_type: Agent type (bugfix, featurebuilder, etc.)
        """
        if not self.enabled or not self._stream_event:
            return

        await self._stream_event("task_start", {
            "task_id": task_id,
            "description": description,
            "file": file,
            "attempts": attempts,
            "agent_type": agent_type
        })

    async def task_complete(
        self,
        task_id: str,
        verdict: str,
        iterations: int,
        duration_seconds: Optional[float] = None,
        files_changed: Optional[list[str]] = None
    ) -> None:
        """
        Stream task_complete event.

        Args:
            task_id: Task ID
            verdict: Ralph verdict (PASS, FAIL, BLOCKED)
            iterations: Number of iterations taken
            duration_seconds: Task duration in seconds
            files_changed: List of files changed
        """
        if not self.enabled or not self._stream_event:
            return

        # Determine severity based on verdict
        severity = {
            "PASS": "info",
            "FAIL": "warning",
            "BLOCKED": "error"
        }.get(verdict, "info")

        await self._stream_event("task_complete", {
            "task_id": task_id,
            "verdict": verdict,
            "iterations": iterations,
            "duration_seconds": duration_seconds,
            "files_changed": files_changed or []
        }, severity=severity)

    async def ralph_verdict(
        self,
        task_id: str,
        verdict: str,
        iteration: int,
        summary: str
    ) -> None:
        """
        Stream ralph_verdict event.

        Args:
            task_id: Task ID
            verdict: Verdict type (PASS, FAIL, BLOCKED)
            iteration: Current iteration number
            summary: Verdict summary message
        """
        if not self.enabled or not self._stream_event:
            return

        severity = {
            "PASS": "info",
            "FAIL": "warning",
            "BLOCKED": "error"
        }.get(verdict, "info")

        await self._stream_event("ralph_verdict", {
            "task_id": task_id,
            "verdict": verdict,
            "iteration": iteration,
            "summary": summary
        }, severity=severity)

    async def loop_complete(
        self,
        tasks_processed: int,
        tasks_completed: int,
        tasks_failed: int,
        duration_seconds: Optional[float] = None
    ) -> None:
        """
        Stream loop_complete event.

        Args:
            tasks_processed: Total tasks processed
            tasks_completed: Tasks successfully completed
            tasks_failed: Tasks that failed
            duration_seconds: Total loop duration in seconds
        """
        if not self.enabled or not self._stream_event:
            return

        await self._stream_event("loop_complete", {
            "tasks_processed": tasks_processed,
            "tasks_completed": tasks_completed,
            "tasks_failed": tasks_failed,
            "duration_seconds": duration_seconds
        })

    async def agent_output(self, task_id: str, output: str) -> None:
        """
        Stream agent_output event (raw agent stdout/stderr).

        Args:
            task_id: Task ID
            output: Agent output text
        """
        if not self.enabled or not self._stream_event:
            return

        await self._stream_event("agent_output", {
            "task_id": task_id,
            "output": output
        })
