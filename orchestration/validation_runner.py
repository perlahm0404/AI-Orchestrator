"""
Validation Runner for Multi-Agent System

Phase 5, Step 5.5: Orchestrates task execution and metrics collection:
- Task execution with mocked or real TeamLead/SpecialistAgent
- Batch execution with parallelism control
- Real-time metrics streaming
- Report generation on completion
- ROI calculation integration
- Work queue file loading

Author: Claude Code
Date: 2026-02-07
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set

from orchestration.metrics_collector import MetricsCollector
from orchestration.validation_report import ValidationReportGenerator
from orchestration.roi_calculator import ROICalculator


class ValidationRunner:
    """
    Orchestrates validation task execution and metrics collection.

    Features:
    - Single and batch task execution
    - Parallelism control with max_parallel
    - Real-time metrics collection
    - Progress callbacks
    - Report generation (Markdown, JSON)
    - ROI calculation integration
    - Work queue file loading
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 3,
        run_id: Optional[str] = None,
    ):
        """
        Initialize validation runner.

        Args:
            output_dir: Directory for reports and metrics
            max_parallel: Maximum parallel task execution
            run_id: Optional run identifier (auto-generated if not provided)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.max_parallel = max_parallel

        # Initialize metrics collector
        self.collector = MetricsCollector(
            run_id=run_id,
            output_dir=self.output_dir,
            auto_save=True,
        )

        # Initialize ROI calculator
        self.roi_calculator = ROICalculator(self.collector)

        # Initialize report generator
        self.report_generator = ValidationReportGenerator(self.collector)

        # Track active tasks for parallelism control
        self._active_tasks: Set[str] = set()
        self._semaphore: Optional[asyncio.Semaphore] = None

    # =========================================================================
    # Task Execution
    # =========================================================================

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task and record metrics.

        Args:
            task: Task definition with task_id, project, title, type, etc.

        Returns:
            Execution result with status, verdict, cost, etc.
        """
        task_id = task.get("task_id", task.get("id", "UNKNOWN"))
        project = task.get("project", "unknown")
        priority = task.get("priority", "P2")
        task_type = task.get("type", "bug")

        # Record task start
        self.collector.record_task_start(task_id, project)

        # Auto-estimate value if not set
        if task_id not in self.roi_calculator.task_values:
            self.roi_calculator.auto_estimate_value(task_id, priority, task_type)

        try:
            # Execute the task
            result = await self._execute_task_internal(task)

            # Extract result details
            status = result.get("status", "completed")
            verdict = result.get("verdict", "PASS" if status == "completed" else "FAIL")
            iterations = result.get("iterations", 0)
            cost = result.get("cost", 0.0)
            error_message = result.get("error_message", "")

            # Record specialist metrics if available
            specialists = result.get("specialists", {})
            for spec_type, spec_data in specialists.items():
                self.collector.record_specialist_start(
                    task_id, spec_type, spec_data.get("max_iterations", 15)
                )
                self.collector.record_specialist_complete(
                    task_id,
                    spec_type,
                    spec_data.get("iterations", 0),
                    spec_data.get("verdict", "PASS"),
                    spec_data.get("cost", 0.0),
                )

            # Record task completion
            self.collector.record_task_complete(
                task_id=task_id,
                status=status,
                verdict=verdict,
                iterations=iterations,
                cost=cost,
                error_message=error_message,
            )

            return result

        except Exception as e:
            # Record failure
            self.collector.record_task_complete(
                task_id=task_id,
                status="failed",
                verdict="FAIL",
                error_message=str(e),
            )
            return {
                "status": "failed",
                "verdict": "FAIL",
                "error_message": str(e),
            }

    async def _execute_task_internal(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal task execution (to be mocked in tests or overridden).

        Args:
            task: Task definition

        Returns:
            Execution result
        """
        # Default implementation - override or mock for actual execution
        return {
            "status": "completed",
            "verdict": "PASS",
            "iterations": 1,
            "cost": 0.01,
        }

    # =========================================================================
    # Batch Execution
    # =========================================================================

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        generate_report: bool = False,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks with parallelism control.

        Args:
            tasks: List of task definitions
            generate_report: Whether to generate report on completion
            on_progress: Optional callback (completed, total, current_task_id)

        Returns:
            List of execution results
        """
        if not tasks:
            return []

        # Initialize semaphore for parallelism control
        self._semaphore = asyncio.Semaphore(self.max_parallel)

        results: List[Dict[str, Any]] = [None] * len(tasks)  # type: ignore
        completed = 0
        semaphore = self._semaphore  # Capture for closure

        async def execute_with_semaphore(idx: int, task: Dict[str, Any]) -> None:
            nonlocal completed
            task_id = task.get("task_id", task.get("id", f"TASK-{idx}"))

            assert semaphore is not None
            async with semaphore:
                self._active_tasks.add(task_id)
                try:
                    result = await self.execute_task(task)
                    results[idx] = result
                finally:
                    self._active_tasks.discard(task_id)
                    completed += 1
                    if on_progress:
                        on_progress(completed, len(tasks), task_id)

        # Execute all tasks
        await asyncio.gather(
            *[execute_with_semaphore(i, t) for i, t in enumerate(tasks)],
            return_exceptions=True,
        )

        # Generate report if requested
        if generate_report:
            self.save_reports()

        return results

    # =========================================================================
    # Reporting
    # =========================================================================

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate summary report from collected metrics.

        Returns:
            Summary report dictionary
        """
        return self.report_generator.generate_summary()

    def save_reports(self) -> Dict[str, Path]:
        """
        Save reports to files.

        Returns:
            Dict with paths to saved files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        md_path = self.output_dir / f"validation_report_{timestamp}.md"
        json_path = self.output_dir / f"validation_report_{timestamp}.json"

        self.report_generator.save_markdown(md_path)
        self.report_generator.save_json(json_path)

        return {
            "markdown": md_path,
            "json": json_path,
        }

    # =========================================================================
    # ROI Integration
    # =========================================================================

    def get_roi_report(self) -> Dict[str, Any]:
        """
        Get ROI report for the validation run.

        Returns:
            ROI report dictionary
        """
        return self.roi_calculator.generate_report()

    def set_task_value(self, task_id: str, value: float) -> None:
        """
        Set manual value estimate for a task.

        Args:
            task_id: Task identifier
            value: Estimated value in USD
        """
        self.roi_calculator.set_task_value(task_id, value)

    # =========================================================================
    # Progress Tracking
    # =========================================================================

    def get_live_stats(self) -> Dict[str, Any]:
        """
        Get live statistics during execution.

        Returns:
            Live stats dictionary
        """
        return self.collector.get_live_stats()

    # =========================================================================
    # Work Queue Integration
    # =========================================================================

    def load_from_work_queue(
        self,
        queue_file: Path,
        status_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Load tasks from a work queue JSON file.

        Args:
            queue_file: Path to work queue JSON file
            status_filter: Optional list of statuses to include

        Returns:
            List of task definitions
        """
        with open(queue_file) as f:
            data = json.load(f)

        project = data.get("project", "unknown")
        raw_tasks = data.get("tasks", [])

        tasks = []
        for raw in raw_tasks:
            # Check status filter
            status = raw.get("status", "pending")
            if status_filter and status not in status_filter:
                continue

            # Convert to standard format
            task = {
                "task_id": raw.get("id", raw.get("task_id")),
                "project": project,
                "title": raw.get("title", ""),
                "type": raw.get("type", "bug"),
                "priority": raw.get("priority", "P2"),
                "status": status,
            }
            tasks.append(task)

        return tasks
