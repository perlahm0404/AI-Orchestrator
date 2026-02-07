"""
Validation Metrics Schema for Multi-Agent System

Phase 5, Step 5.1: Defines metrics collected during validation runs:
- TaskExecutionMetrics: Per-task execution data
- SpecialistMetrics: Per-specialist performance data
- ValidationRunMetrics: Aggregate run statistics
- QualityMetrics: Code quality indicators
- CostMetrics: Cost tracking and ROI

Author: Claude Code
Date: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class TaskExecutionMetrics:
    """
    Metrics for a single task execution.

    Tracks timing, cost, and outcome for validation analysis.
    """
    task_id: str
    project: str
    started_at: datetime
    completed_at: datetime
    status: str  # "completed", "failed", "blocked", "timeout"

    # Optional fields with defaults
    iterations_used: int = 0
    specialists_used: List[str] = field(default_factory=list)
    total_cost: float = 0.0
    verdict: str = ""
    error_message: str = ""

    @property
    def duration_seconds(self) -> float:
        """Calculate duration from timestamps."""
        delta = self.completed_at - self.started_at
        return delta.total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_id": self.task_id,
            "project": self.project,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "iterations_used": self.iterations_used,
            "specialists_used": self.specialists_used,
            "total_cost": self.total_cost,
            "verdict": self.verdict,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskExecutionMetrics":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            project=data["project"],
            started_at=datetime.fromisoformat(data["started_at"]) if isinstance(data["started_at"], str) else data["started_at"],
            completed_at=datetime.fromisoformat(data["completed_at"]) if isinstance(data["completed_at"], str) else data["completed_at"],
            status=data["status"],
            iterations_used=data.get("iterations_used", 0),
            specialists_used=data.get("specialists_used", []),
            total_cost=data.get("total_cost", 0.0),
            verdict=data.get("verdict", ""),
            error_message=data.get("error_message", ""),
        )


@dataclass
class SpecialistMetrics:
    """
    Metrics for a single specialist execution.

    Tracks performance and cost for each specialist agent.
    """
    specialist_type: str
    task_id: str

    # Performance metrics
    iterations_used: int = 0
    max_iterations: int = 15
    duration_seconds: float = 0.0
    verdict: str = ""

    # Cost metrics
    cost: float = 0.0
    mcp_costs: Dict[str, float] = field(default_factory=dict)

    @property
    def iteration_efficiency(self) -> float:
        """Calculate iteration efficiency (lower is better)."""
        if self.max_iterations == 0:
            return 0.0
        return self.iterations_used / self.max_iterations

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "specialist_type": self.specialist_type,
            "task_id": self.task_id,
            "iterations_used": self.iterations_used,
            "max_iterations": self.max_iterations,
            "iteration_efficiency": self.iteration_efficiency,
            "duration_seconds": self.duration_seconds,
            "verdict": self.verdict,
            "cost": self.cost,
            "mcp_costs": self.mcp_costs,
        }


@dataclass
class ValidationRunMetrics:
    """
    Aggregate metrics for a validation run.

    Tracks overall performance across multiple tasks.
    """
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Task counts
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_blocked: int = 0

    # Aggregate costs
    total_cost: float = 0.0
    total_value: float = 0.0

    # Task metrics list
    task_metrics: List[TaskExecutionMetrics] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.tasks_total == 0:
            return 0.0
        return self.tasks_completed / self.tasks_total

    @property
    def duration_seconds(self) -> float:
        """Calculate total run duration."""
        if self.completed_at is None:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()

    def add_task_metrics(self, task: TaskExecutionMetrics) -> None:
        """Add task metrics and update aggregates."""
        self.task_metrics.append(task)
        self.tasks_total += 1
        self.total_cost += task.total_cost

        if task.status == "completed":
            self.tasks_completed += 1
        elif task.status == "failed":
            self.tasks_failed += 1
        elif task.status == "blocked":
            self.tasks_blocked += 1

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "tasks_total": self.tasks_total,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_blocked": self.tasks_blocked,
            "success_rate": self.success_rate,
            "total_cost": self.total_cost,
            "total_value": self.total_value,
            "task_metrics": [t.to_dict() for t in self.task_metrics],
        }


@dataclass
class QualityMetrics:
    """
    Code quality metrics for a task.

    Tracks tests, lint errors, and coverage changes.
    """
    task_id: str

    # Test metrics
    tests_added: int = 0
    tests_passing: int = 0
    tests_failing: int = 0

    # Code quality
    lint_errors_fixed: int = 0
    type_errors_fixed: int = 0
    code_coverage_delta: float = 0.0  # Percentage points change

    @property
    def test_pass_rate(self) -> float:
        """Calculate test pass rate."""
        if self.tests_added == 0:
            return 1.0  # No tests = 100% pass
        return self.tests_passing / self.tests_added

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_id": self.task_id,
            "tests_added": self.tests_added,
            "tests_passing": self.tests_passing,
            "tests_failing": self.tests_failing,
            "test_pass_rate": self.test_pass_rate,
            "lint_errors_fixed": self.lint_errors_fixed,
            "type_errors_fixed": self.type_errors_fixed,
            "code_coverage_delta": self.code_coverage_delta,
        }


@dataclass
class CostMetrics:
    """
    Cost tracking metrics for a task.

    Tracks costs by component and calculates ROI.
    """
    task_id: str

    # Cost components
    analysis_cost: float = 0.0
    specialist_costs: Dict[str, float] = field(default_factory=dict)
    synthesis_cost: float = 0.0

    # Value estimation
    estimated_value: float = 0.0

    @property
    def total_cost(self) -> float:
        """Calculate total cost from components."""
        specialist_total = sum(self.specialist_costs.values())
        return self.analysis_cost + specialist_total + self.synthesis_cost

    @property
    def roi(self) -> float:
        """Calculate return on investment."""
        if self.total_cost == 0:
            return float('inf') if self.estimated_value > 0 else 0.0
        return (self.estimated_value - self.total_cost) / self.total_cost

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_id": self.task_id,
            "analysis_cost": self.analysis_cost,
            "specialist_costs": self.specialist_costs,
            "synthesis_cost": self.synthesis_cost,
            "total_cost": self.total_cost,
            "estimated_value": self.estimated_value,
            "roi": self.roi,
        }


# ============================================================================
# Aggregation Functions
# ============================================================================

def aggregate_by_specialist(
    metrics: List[SpecialistMetrics]
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate specialist metrics by type.

    Args:
        metrics: List of SpecialistMetrics

    Returns:
        Dict mapping specialist_type to aggregated stats
    """
    aggregated: Dict[str, Dict[str, Any]] = {}

    for m in metrics:
        if m.specialist_type not in aggregated:
            aggregated[m.specialist_type] = {
                "total_cost": 0.0,
                "total_iterations": 0,
                "count": 0,
                "avg_iterations": 0.0,
                "avg_cost": 0.0,
            }

        agg = aggregated[m.specialist_type]
        agg["total_cost"] += m.cost
        agg["total_iterations"] += m.iterations_used
        agg["count"] += 1

    # Calculate averages
    for specialist_type, agg in aggregated.items():
        if agg["count"] > 0:
            agg["avg_iterations"] = agg["total_iterations"] / agg["count"]
            agg["avg_cost"] = agg["total_cost"] / agg["count"]

    return aggregated


def aggregate_by_project(
    metrics: List[TaskExecutionMetrics]
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate task metrics by project.

    Args:
        metrics: List of TaskExecutionMetrics

    Returns:
        Dict mapping project to aggregated stats
    """
    aggregated: Dict[str, Dict[str, Any]] = {}

    for m in metrics:
        if m.project not in aggregated:
            aggregated[m.project] = {
                "task_count": 0,
                "total_cost": 0.0,
                "total_duration": 0.0,
                "completed": 0,
                "failed": 0,
            }

        agg = aggregated[m.project]
        agg["task_count"] += 1
        agg["total_cost"] += m.total_cost
        agg["total_duration"] += m.duration_seconds

        if m.status == "completed":
            agg["completed"] += 1
        elif m.status == "failed":
            agg["failed"] += 1

    # Calculate averages
    for project, agg in aggregated.items():
        if agg["task_count"] > 0:
            agg["avg_cost"] = agg["total_cost"] / agg["task_count"]
            agg["avg_duration"] = agg["total_duration"] / agg["task_count"]
            agg["success_rate"] = agg["completed"] / agg["task_count"]

    return aggregated
