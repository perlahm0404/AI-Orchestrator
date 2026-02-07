"""
Metrics Collector for Multi-Agent Validation

Phase 5, Step 5.2: Collects and stores metrics during validation runs:
- Real-time metric recording
- Task and specialist tracking
- Cost aggregation
- Persistence to JSON
- Live statistics

Author: Claude Code
Date: 2026-02-07
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple

from orchestration.validation_metrics import (
    TaskExecutionMetrics,
    SpecialistMetrics,
    ValidationRunMetrics,
    QualityMetrics,
    CostMetrics,
    aggregate_by_specialist,
)


class MetricsCollector:
    """
    Collects and manages metrics during validation runs.

    Features:
    - Real-time task and specialist tracking
    - Cost aggregation by component
    - Quality metrics collection
    - JSON persistence
    - Live statistics
    - Callback support for real-time updates
    """

    def __init__(
        self,
        run_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
        auto_save: bool = False
    ):
        """
        Initialize metrics collector.

        Args:
            run_id: Unique run identifier (auto-generated if not provided)
            output_dir: Directory for saving metrics files
            auto_save: If True, save after each task completion
        """
        self.run_id = run_id or f"RUN-{uuid.uuid4().hex[:8].upper()}"
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / ".metrics"
        self.auto_save = auto_save

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Active tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.active_specialists: Dict[Tuple[str, str], Dict[str, Any]] = {}

        # Completed metrics
        self.task_metrics: Dict[str, TaskExecutionMetrics] = {}
        self.specialist_metrics: Dict[Tuple[str, str], SpecialistMetrics] = {}
        self.cost_metrics: Dict[str, CostMetrics] = {}
        self.quality_metrics: Dict[str, QualityMetrics] = {}

        # Run-level tracking
        self.run_started_at = datetime.now()
        self.run_completed_at: Optional[datetime] = None

        # Callbacks
        self._on_task_complete_callbacks: List[Callable[..., Any]] = []

    # =========================================================================
    # Task Recording
    # =========================================================================

    def record_task_start(self, task_id: str, project: str) -> None:
        """
        Record task execution start.

        Args:
            task_id: Task identifier
            project: Project name
        """
        self.active_tasks[task_id] = {
            "task_id": task_id,
            "project": project,
            "started_at": datetime.now(),
            "specialists_used": [],
        }

        # Initialize cost metrics
        self.cost_metrics[task_id] = CostMetrics(task_id=task_id)

        # Initialize quality metrics
        self.quality_metrics[task_id] = QualityMetrics(task_id=task_id)

    def record_specialist_used(self, task_id: str, specialist_type: str) -> None:
        """
        Record that a specialist was used for a task.

        Args:
            task_id: Task identifier
            specialist_type: Type of specialist
        """
        if task_id in self.active_tasks:
            if specialist_type not in self.active_tasks[task_id]["specialists_used"]:
                self.active_tasks[task_id]["specialists_used"].append(specialist_type)

    def record_task_complete(
        self,
        task_id: str,
        status: str,
        verdict: str,
        iterations: int = 0,
        cost: float = 0.0,
        error_message: str = ""
    ) -> None:
        """
        Record task completion.

        Args:
            task_id: Task identifier
            status: Final status
            verdict: Ralph verdict
            iterations: Total iterations used
            cost: Total cost
            error_message: Error message if failed
        """
        if task_id not in self.active_tasks:
            return

        task_data = self.active_tasks.pop(task_id)
        completed_at = datetime.now()

        # Update cost metrics if cost provided
        if cost > 0:
            self.cost_metrics[task_id].specialist_costs["total"] = cost

        metrics = TaskExecutionMetrics(
            task_id=task_id,
            project=task_data["project"],
            started_at=task_data["started_at"],
            completed_at=completed_at,
            status=status,
            verdict=verdict,
            iterations_used=iterations,
            specialists_used=task_data["specialists_used"],
            total_cost=cost if cost > 0 else self.cost_metrics[task_id].total_cost,
            error_message=error_message,
        )

        self.task_metrics[task_id] = metrics

        # Fire callbacks
        for callback in self._on_task_complete_callbacks:
            callback(task_id, metrics)

        # Auto-save if enabled
        if self.auto_save:
            self.save()

    def get_task_metrics(self, task_id: str) -> Optional[TaskExecutionMetrics]:
        """Get metrics for a specific task."""
        return self.task_metrics.get(task_id)

    # =========================================================================
    # Specialist Recording
    # =========================================================================

    def record_specialist_start(
        self,
        task_id: str,
        specialist_type: str,
        max_iterations: int
    ) -> None:
        """
        Record specialist execution start.

        Args:
            task_id: Parent task ID
            specialist_type: Type of specialist
            max_iterations: Maximum iterations allowed
        """
        key = (task_id, specialist_type)
        self.active_specialists[key] = {
            "task_id": task_id,
            "specialist_type": specialist_type,
            "started_at": datetime.now(),
            "max_iterations": max_iterations,
            "mcp_costs": {},
        }

        # Also track as used
        self.record_specialist_used(task_id, specialist_type)

    def record_mcp_cost(
        self,
        task_id: str,
        specialist_type: str,
        mcp_name: str,
        cost: float
    ) -> None:
        """
        Record MCP cost for a specialist.

        Args:
            task_id: Parent task ID
            specialist_type: Type of specialist
            mcp_name: Name of MCP server
            cost: Cost in USD
        """
        key = (task_id, specialist_type)
        if key in self.active_specialists:
            if mcp_name not in self.active_specialists[key]["mcp_costs"]:
                self.active_specialists[key]["mcp_costs"][mcp_name] = 0.0
            self.active_specialists[key]["mcp_costs"][mcp_name] += cost

    def record_specialist_complete(
        self,
        task_id: str,
        specialist_type: str,
        iterations_used: int,
        verdict: str,
        cost: float = 0.0
    ) -> None:
        """
        Record specialist completion.

        Args:
            task_id: Parent task ID
            specialist_type: Type of specialist
            iterations_used: Iterations used
            verdict: Final verdict
            cost: Total cost
        """
        key = (task_id, specialist_type)
        if key not in self.active_specialists:
            return

        specialist_data = self.active_specialists.pop(key)
        completed_at = datetime.now()
        duration = (completed_at - specialist_data["started_at"]).total_seconds()

        metrics = SpecialistMetrics(
            specialist_type=specialist_type,
            task_id=task_id,
            iterations_used=iterations_used,
            max_iterations=specialist_data["max_iterations"],
            duration_seconds=duration,
            verdict=verdict,
            cost=cost,
            mcp_costs=specialist_data["mcp_costs"],
        )

        self.specialist_metrics[key] = metrics

        # Update task cost metrics
        if task_id in self.cost_metrics:
            self.cost_metrics[task_id].specialist_costs[specialist_type] = cost

    def get_specialist_metrics(
        self,
        task_id: str,
        specialist_type: str
    ) -> Optional[SpecialistMetrics]:
        """Get metrics for a specific specialist."""
        return self.specialist_metrics.get((task_id, specialist_type))

    # =========================================================================
    # Cost Recording
    # =========================================================================

    def record_analysis_cost(self, task_id: str, cost: float) -> None:
        """Record analysis phase cost."""
        if task_id in self.cost_metrics:
            self.cost_metrics[task_id].analysis_cost += cost

    def record_synthesis_cost(self, task_id: str, cost: float) -> None:
        """Record synthesis phase cost."""
        if task_id in self.cost_metrics:
            self.cost_metrics[task_id].synthesis_cost += cost

    def get_cost_metrics(self, task_id: str) -> Optional[CostMetrics]:
        """Get cost metrics for a task."""
        return self.cost_metrics.get(task_id)

    # =========================================================================
    # Quality Recording
    # =========================================================================

    def record_tests_added(self, task_id: str, count: int) -> None:
        """Record tests added during task."""
        if task_id in self.quality_metrics:
            self.quality_metrics[task_id].tests_added = count

    def record_tests_passing(self, task_id: str, count: int) -> None:
        """Record passing tests."""
        if task_id in self.quality_metrics:
            self.quality_metrics[task_id].tests_passing = count

    def record_lint_errors_fixed(self, task_id: str, count: int) -> None:
        """Record lint errors fixed."""
        if task_id in self.quality_metrics:
            self.quality_metrics[task_id].lint_errors_fixed = count

    def get_quality_metrics(self, task_id: str) -> Optional[QualityMetrics]:
        """Get quality metrics for a task."""
        return self.quality_metrics.get(task_id)

    # =========================================================================
    # Run Aggregation
    # =========================================================================

    def get_run_metrics(self) -> ValidationRunMetrics:
        """Get aggregated run-level metrics."""
        run_metrics = ValidationRunMetrics(
            run_id=self.run_id,
            started_at=self.run_started_at,
            completed_at=self.run_completed_at or datetime.now(),
        )

        for task in self.task_metrics.values():
            run_metrics.add_task_metrics(task)

        return run_metrics

    def get_specialist_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary aggregated by specialist type."""
        return aggregate_by_specialist(list(self.specialist_metrics.values()))

    # =========================================================================
    # Live Statistics
    # =========================================================================

    def get_live_stats(self) -> Dict[str, Any]:
        """Get live statistics during run."""
        completed_count = len(self.task_metrics)
        in_progress_count = len(self.active_tasks)
        current_cost = sum(t.total_cost for t in self.task_metrics.values())

        return {
            "tasks_in_progress": in_progress_count,
            "tasks_completed": completed_count,
            "current_cost": current_cost,
            "run_duration_seconds": (datetime.now() - self.run_started_at).total_seconds(),
        }

    # =========================================================================
    # Callbacks
    # =========================================================================

    def on_task_complete(self, callback: Callable[..., Any]) -> None:
        """Register callback for task completion events."""
        self._on_task_complete_callbacks.append(callback)

    # =========================================================================
    # Persistence
    # =========================================================================

    def save(self) -> Path:
        """
        Save metrics to JSON file.

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / f"{self.run_id}.json"

        data = {
            "run_id": self.run_id,
            "started_at": self.run_started_at.isoformat(),
            "completed_at": self.run_completed_at.isoformat() if self.run_completed_at else None,
            "tasks": {
                task_id: metrics.to_dict()
                for task_id, metrics in self.task_metrics.items()
            },
            "specialists": {
                f"{key[0]}:{key[1]}": metrics.to_dict()
                for key, metrics in self.specialist_metrics.items()
            },
            "costs": {
                task_id: metrics.to_dict()
                for task_id, metrics in self.cost_metrics.items()
            },
            "quality": {
                task_id: metrics.to_dict()
                for task_id, metrics in self.quality_metrics.items()
            },
            "summary": self.get_run_metrics().to_dict(),
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return output_path

    @classmethod
    def load(cls, path: Path) -> "MetricsCollector":
        """
        Load metrics from JSON file.

        Args:
            path: Path to JSON file

        Returns:
            MetricsCollector with loaded data
        """
        with open(path) as f:
            data = json.load(f)

        collector = cls(
            run_id=data["run_id"],
            output_dir=path.parent
        )

        collector.run_started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            collector.run_completed_at = datetime.fromisoformat(data["completed_at"])

        # Load task metrics
        for task_id, task_data in data.get("tasks", {}).items():
            collector.task_metrics[task_id] = TaskExecutionMetrics.from_dict(task_data)

        # Load cost metrics
        for task_id, cost_data in data.get("costs", {}).items():
            collector.cost_metrics[task_id] = CostMetrics(
                task_id=task_id,
                analysis_cost=cost_data.get("analysis_cost", 0.0),
                specialist_costs=cost_data.get("specialist_costs", {}),
                synthesis_cost=cost_data.get("synthesis_cost", 0.0),
                estimated_value=cost_data.get("estimated_value", 0.0),
            )

        return collector

    def complete_run(self) -> None:
        """Mark the run as complete."""
        self.run_completed_at = datetime.now()
        self.save()
