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

    # ==================== Multi-Agent Orchestration Events ====================

    async def multi_agent_analyzing(
        self,
        task_id: str,
        project: str,
        complexity: str,
        specialists: list[str],
        challenges: list[str]
    ) -> None:
        """
        Stream event when Team Lead starts analyzing task.

        Args:
            task_id: Task ID being analyzed
            project: Project name
            complexity: Estimated complexity (low, medium, high, critical)
            specialists: Recommended specialist types
            challenges: Key challenges identified
        """
        if not self.enabled or not self._stream_event:
            return

        await self._stream_event("multi_agent_analyzing", {
            "task_id": task_id,
            "project": project,
            "complexity": complexity,
            "specialists": specialists,
            "challenges": challenges
        })

    async def specialist_started(
        self,
        task_id: str,
        project: str,
        specialist_type: str,
        subtask_id: str,
        max_iterations: int
    ) -> None:
        """
        Stream event when a specialist agent is launched.

        Args:
            task_id: Parent task ID
            project: Project name
            specialist_type: Type of specialist (bugfix, featurebuilder, etc.)
            subtask_id: Subtask ID assigned to specialist
            max_iterations: Iteration budget for specialist
        """
        if not self.enabled or not self._stream_event:
            return

        await self._stream_event("specialist_started", {
            "task_id": task_id,
            "project": project,
            "specialist_type": specialist_type,
            "subtask_id": subtask_id,
            "max_iterations": max_iterations
        })

    async def specialist_iteration(
        self,
        task_id: str,
        project: str,
        specialist_type: str,
        iteration: int,
        max_iterations: int,
        verdict: Optional[str] = None,
        output_summary: str = ""
    ) -> None:
        """
        Stream event for specialist iteration progress.

        Args:
            task_id: Parent task ID
            project: Project name
            specialist_type: Type of specialist
            iteration: Current iteration number
            max_iterations: Maximum iterations allowed
            verdict: Ralph verdict if available (PASS, FAIL, BLOCKED)
            output_summary: Brief summary of iteration output
        """
        if not self.enabled or not self._stream_event:
            return

        severity = "info"
        if verdict == "FAIL":
            severity = "warning"
        elif verdict == "BLOCKED":
            severity = "error"

        await self._stream_event("specialist_iteration", {
            "task_id": task_id,
            "project": project,
            "specialist_type": specialist_type,
            "iteration": iteration,
            "max_iterations": max_iterations,
            "verdict": verdict,
            "output_summary": output_summary[:200]  # Truncate for WebSocket
        }, severity=severity)

    async def specialist_completed(
        self,
        task_id: str,
        project: str,
        specialist_type: str,
        status: str,
        verdict: str,
        iterations_used: int,
        duration_seconds: Optional[float] = None
    ) -> None:
        """
        Stream event when specialist completes.

        Args:
            task_id: Parent task ID
            project: Project name
            specialist_type: Type of specialist
            status: Final status (completed, blocked, timeout, failed)
            verdict: Final Ralph verdict
            iterations_used: Number of iterations used
            duration_seconds: Time taken
        """
        if not self.enabled or not self._stream_event:
            return

        severity = "info" if status == "completed" else "warning"
        if verdict == "BLOCKED":
            severity = "error"

        await self._stream_event("specialist_completed", {
            "task_id": task_id,
            "project": project,
            "specialist_type": specialist_type,
            "status": status,
            "verdict": verdict,
            "iterations_used": iterations_used,
            "duration_seconds": duration_seconds
        }, severity=severity)

    async def multi_agent_synthesis(
        self,
        task_id: str,
        project: str,
        specialists_completed: int,
        specialists_total: int
    ) -> None:
        """
        Stream event when Team Lead begins synthesis.

        Args:
            task_id: Task ID
            project: Project name
            specialists_completed: Number of specialists that completed successfully
            specialists_total: Total number of specialists launched
        """
        if not self.enabled or not self._stream_event:
            return

        await self._stream_event("multi_agent_synthesis", {
            "task_id": task_id,
            "project": project,
            "specialists_completed": specialists_completed,
            "specialists_total": specialists_total
        })

    async def multi_agent_verification(
        self,
        task_id: str,
        project: str,
        verdict: str,
        summary: str
    ) -> None:
        """
        Stream event for final multi-agent verification.

        Args:
            task_id: Task ID
            project: Project name
            verdict: Final Ralph verdict (PASS, FAIL, BLOCKED)
            summary: Verification summary
        """
        if not self.enabled or not self._stream_event:
            return

        severity = {
            "PASS": "info",
            "FAIL": "warning",
            "BLOCKED": "error"
        }.get(verdict, "info")

        await self._stream_event("multi_agent_verification", {
            "task_id": task_id,
            "project": project,
            "verdict": verdict,
            "summary": summary
        }, severity=severity)

    # ==================== Cost Tracking Events (Phase 4.4) ====================

    async def cost_update(
        self,
        task_id: str,
        project: str,
        specialist_type: str,
        cost_usd: float,
        accumulated_cost: float,
        operation: str = ""
    ) -> None:
        """
        Stream cost update event when a specialist incurs cost.

        Args:
            task_id: Task ID
            project: Project name
            specialist_type: Type of specialist
            cost_usd: Cost incurred in this operation
            accumulated_cost: Total accumulated cost for this specialist
            operation: Type of operation (e.g., "verification", "git_commit")
        """
        if not self.enabled or not self._stream_event:
            return

        await self._stream_event("cost_update", {
            "task_id": task_id,
            "project": project,
            "specialist_type": specialist_type,
            "cost_usd": cost_usd,
            "accumulated_cost": accumulated_cost,
            "operation": operation
        })

    async def cost_summary(
        self,
        task_id: str,
        project: str,
        analysis_cost: float,
        specialist_costs: dict[str, float],
        synthesis_cost: float,
        total_cost: float
    ) -> None:
        """
        Stream cost summary event at task completion.

        Args:
            task_id: Task ID
            project: Project name
            analysis_cost: Cost of task analysis
            specialist_costs: Cost breakdown by specialist
            synthesis_cost: Cost of result synthesis
            total_cost: Total task cost
        """
        if not self.enabled or not self._stream_event:
            return

        await self._stream_event("cost_summary", {
            "task_id": task_id,
            "project": project,
            "analysis_cost": analysis_cost,
            "specialist_costs": specialist_costs,
            "synthesis_cost": synthesis_cost,
            "total_cost": total_cost
        })

    async def cost_warning(
        self,
        task_id: str,
        project: str,
        specialist_type: str,
        current_cost: float,
        budget: float,
        percentage: float
    ) -> None:
        """
        Stream warning when cost approaches budget.

        Args:
            task_id: Task ID
            project: Project name
            specialist_type: Type of specialist
            current_cost: Current accumulated cost
            budget: Cost budget
            percentage: Percentage of budget used
        """
        if not self.enabled or not self._stream_event:
            return

        severity = "warning" if percentage >= 0.8 else "info"
        if percentage >= 0.95:
            severity = "error"

        await self._stream_event("cost_warning", {
            "task_id": task_id,
            "project": project,
            "specialist_type": specialist_type,
            "current_cost": current_cost,
            "budget": budget,
            "percentage": percentage
        }, severity=severity)

    async def efficiency_metrics(
        self,
        task_id: str,
        project: str,
        cost_per_iteration: float,
        roi: float,
        cost_to_value_ratio: float,
        value_generated: float,
        total_cost: float
    ) -> None:
        """
        Stream efficiency metrics at task completion.

        Args:
            task_id: Task ID
            project: Project name
            cost_per_iteration: Average cost per iteration
            roi: Return on investment ((value - cost) / cost)
            cost_to_value_ratio: Cost divided by value
            value_generated: Estimated value generated
            total_cost: Total cost incurred
        """
        if not self.enabled or not self._stream_event:
            return

        # ROI < 1 means we spent more than we generated - warning
        severity = "info" if roi >= 1.0 else "warning"
        if roi < 0:
            severity = "error"

        await self._stream_event("efficiency_metrics", {
            "task_id": task_id,
            "project": project,
            "cost_per_iteration": cost_per_iteration,
            "roi": roi,
            "cost_to_value_ratio": cost_to_value_ratio,
            "value_generated": value_generated,
            "total_cost": total_cost
        }, severity=severity)
