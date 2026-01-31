"""
Metrics Collection and Dashboard (Priority 6)

Production monitoring with key metrics for autonomous agent execution.

Usage:
    from monitoring.metrics import MetricsCollector, generate_dashboard

    collector = MetricsCollector(storage_dir=Path("./metrics"))
    collector.record("tasks.completed", 1, tags={"project": "karematch"})

    dashboard = generate_dashboard(collector)
    print(f"Success rate: {dashboard.success_rate:.1%}")
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metric_type: str = MetricType.COUNTER

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "metric_type": self.metric_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricPoint":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            value=data["value"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tags=data["tags"],
            metric_type=data.get("metric_type", MetricType.COUNTER),
        )


@dataclass
class DashboardData:
    """Dashboard summary data."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    avg_task_duration_ms: int = 0
    agent_utilization: float = 0.0
    error_breakdown: Dict[str, int] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and stores metrics.

    Thread-safe for concurrent access.
    Persists to disk for durability.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("./metrics")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._points: List[MetricPoint] = []
        self._gauges: Dict[str, float] = {}
        self._counters: Dict[str, float] = {}
        self._lock = threading.Lock()

        # Load existing data
        self._load()

    def record(
        self,
        name: str,
        value: float,
        metric_type: str = MetricType.COUNTER,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Record a metric point.

        Args:
            name: Metric name (e.g., "tasks.completed")
            value: Metric value
            metric_type: Type of metric (counter, gauge, histogram)
            tags: Additional metadata tags
            timestamp: Timestamp (defaults to now)
        """
        with self._lock:
            point = MetricPoint(
                name=name,
                value=value,
                timestamp=timestamp or datetime.now(),
                tags=tags or {},
                metric_type=metric_type,
            )
            self._points.append(point)

            # Also update running totals for counters
            if metric_type == MetricType.COUNTER:
                self._counters[name] = self._counters.get(name, 0) + value

    def increment(self, name: str, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter by 1."""
        self.record(name, 1, metric_type=MetricType.COUNTER, tags=tags)

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge to a specific value."""
        with self._lock:
            self._gauges[name] = value
        self.record(name, value, metric_type=MetricType.GAUGE, tags=tags)

    def get_gauge(self, name: str) -> float:
        """Get current value of a gauge."""
        with self._lock:
            return self._gauges.get(name, 0.0)

    def get_total(self, name: str) -> float:
        """Get total value of a counter."""
        with self._lock:
            return self._counters.get(name, 0.0)

    def get_points(
        self,
        name: str,
        since: Optional[datetime] = None,
    ) -> List[MetricPoint]:
        """
        Get metric points by name.

        Args:
            name: Metric name to filter by
            since: Only return points after this time

        Returns:
            List of matching metric points
        """
        with self._lock:
            points = [p for p in self._points if p.name == name]
            if since:
                points = [p for p in points if p.timestamp >= since]
            return points

    def flush(self) -> None:
        """Flush metrics to disk."""
        with self._lock:
            metrics_file = self.storage_dir / "metrics.jsonl"
            with metrics_file.open("a") as f:
                for point in self._points:
                    f.write(json.dumps(point.to_dict()) + "\n")

            # Save gauges and counters
            state_file = self.storage_dir / "state.json"
            state_file.write_text(json.dumps({
                "gauges": self._gauges,
                "counters": self._counters,
            }))

    def _load(self) -> None:
        """Load metrics from disk."""
        # Load state
        state_file = self.storage_dir / "state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
            self._gauges = state.get("gauges", {})
            self._counters = state.get("counters", {})

        # Load points from last 24 hours
        metrics_file = self.storage_dir / "metrics.jsonl"
        if metrics_file.exists():
            cutoff = datetime.now() - timedelta(hours=24)
            with metrics_file.open() as f:
                for line in f:
                    if line.strip():
                        point = MetricPoint.from_dict(json.loads(line))
                        if point.timestamp >= cutoff:
                            self._points.append(point)

    def export_json(self) -> str:
        """Export metrics as JSON."""
        with self._lock:
            return json.dumps({
                "metrics": [p.to_dict() for p in self._points],
                "gauges": self._gauges,
                "counters": self._counters,
                "exported_at": datetime.now().isoformat(),
            }, indent=2)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        with self._lock:
            # Export counters
            for name, value in self._counters.items():
                prom_name = name.replace(".", "_")
                lines.append(f"{prom_name} {value}")

            # Export gauges
            for name, value in self._gauges.items():
                prom_name = name.replace(".", "_")
                lines.append(f"{prom_name} {value}")

        return "\n".join(lines)

    # Convenience methods for common operations

    def task_started(self, task_id: str, project: str = "") -> None:
        """Record task start."""
        self.record("task.started", 1, tags={"task_id": task_id, "project": project})

    def task_completed(self, task_id: str, duration_ms: int = 0) -> None:
        """Record task completion."""
        self.record("task.completed", 1, tags={"task_id": task_id})
        if duration_ms:
            self.record("task.duration_ms", duration_ms, tags={"task_id": task_id})

    def task_failed(self, task_id: str, error_type: str = "", error: str = "") -> None:
        """Record task failure."""
        self.record("task.failed", 1, tags={
            "task_id": task_id,
            "error_type": error_type,
            "error": error[:100],  # Truncate long errors
        })

    def agent_slot_acquired(self, agent_id: str, task_id: str = "") -> None:
        """Record agent slot acquisition."""
        self.record("agent.slot_acquired", 1, tags={
            "agent_id": agent_id,
            "task_id": task_id,
        })

    def agent_slot_released(self, agent_id: str) -> None:
        """Record agent slot release."""
        self.record("agent.slot_released", 1, tags={"agent_id": agent_id})


def generate_dashboard(collector: MetricsCollector) -> DashboardData:
    """
    Generate dashboard data from metrics.

    Args:
        collector: MetricsCollector with recorded metrics

    Returns:
        DashboardData with summary statistics
    """
    completed = int(collector.get_total("tasks.completed"))
    failed = int(collector.get_total("tasks.failed"))
    total = completed + failed

    # Calculate success rate
    success_rate = completed / total if total > 0 else 0.0

    # Calculate average duration
    duration_points = collector.get_points("task.duration_ms")
    avg_duration = 0
    if duration_points:
        avg_duration = int(sum(p.value for p in duration_points) / len(duration_points))

    # Calculate agent utilization
    active = collector.get_gauge("agent.active")
    total_agents = collector.get_gauge("agent.total")
    utilization = active / total_agents if total_agents > 0 else 0.0

    # Build error breakdown
    error_breakdown: Dict[str, int] = {}
    failed_points = collector.get_points("tasks.failed")
    for point in failed_points:
        error_type = point.tags.get("error_type", "unknown")
        error_breakdown[error_type] = error_breakdown.get(error_type, 0) + 1

    return DashboardData(
        total_tasks=total,
        completed_tasks=completed,
        failed_tasks=failed,
        success_rate=success_rate,
        avg_task_duration_ms=avg_duration,
        agent_utilization=utilization,
        error_breakdown=error_breakdown,
    )
