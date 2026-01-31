"""
Tests for Metrics Dashboard (Priority 6)

TDD approach: Tests written first, then implementation.
Target: Production monitoring with key metrics.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import List, Optional, Dict

# These imports will fail until we implement the modules
try:
    from monitoring.metrics import (
        MetricsCollector,
        MetricPoint,
        MetricType,
        DashboardData,
        generate_dashboard,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

    # Placeholder classes for test definition
    class MetricType:
        COUNTER = "counter"
        GAUGE = "gauge"
        HISTOGRAM = "histogram"

    @dataclass
    class MetricPoint:
        name: str
        value: float
        timestamp: datetime
        tags: Dict[str, str]
        metric_type: str = "counter"

    @dataclass
    class DashboardData:
        total_tasks: int = 0
        completed_tasks: int = 0
        failed_tasks: int = 0
        success_rate: float = 0.0
        avg_task_duration_ms: int = 0
        agent_utilization: float = 0.0
        error_breakdown: Dict[str, int] = None


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestMetricPoint:
    """Test MetricPoint dataclass."""

    def test_point_has_required_fields(self):
        """Point has all required fields."""
        point = MetricPoint(
            name="tasks.completed",
            value=42.0,
            timestamp=datetime.now(),
            tags={"project": "karematch"},
            metric_type=MetricType.COUNTER
        )

        assert point.name == "tasks.completed"
        assert point.value == 42.0
        assert "project" in point.tags

    def test_point_defaults_to_counter(self):
        """Point defaults to counter type."""
        point = MetricPoint(
            name="test",
            value=1.0,
            timestamp=datetime.now(),
            tags={}
        )

        assert point.metric_type == MetricType.COUNTER


class TestMetricsCollector:
    """Test MetricsCollector class."""

    @pytest.fixture
    def collector(self, tmp_path: Path):
        return MetricsCollector(storage_dir=tmp_path)

    def test_collector_initializes(self, collector):
        """Collector initializes correctly."""
        assert collector is not None

    def test_record_counter(self, collector):
        """Record a counter metric."""
        collector.record("tasks.completed", 1, tags={"project": "karematch"})

        points = collector.get_points("tasks.completed")
        assert len(points) == 1
        assert points[0].value == 1

    def test_record_gauge(self, collector):
        """Record a gauge metric."""
        collector.record(
            "agent.utilization",
            0.75,
            metric_type=MetricType.GAUGE,
            tags={"agent": "agent-1"}
        )

        points = collector.get_points("agent.utilization")
        assert len(points) == 1
        assert points[0].value == 0.75

    def test_record_multiple_points(self, collector):
        """Record multiple points for same metric."""
        for i in range(5):
            collector.record("tasks.completed", 1, tags={"iteration": str(i)})

        points = collector.get_points("tasks.completed")
        assert len(points) == 5

    def test_get_points_with_time_range(self, collector):
        """Filter points by time range."""
        now = datetime.now()
        old = now - timedelta(hours=2)

        collector.record("tasks.completed", 1, timestamp=old)
        collector.record("tasks.completed", 1, timestamp=now)

        # Get only recent points
        recent = collector.get_points(
            "tasks.completed",
            since=now - timedelta(hours=1)
        )
        assert len(recent) == 1

    def test_increment_counter(self, collector):
        """Increment a counter metric."""
        collector.increment("tasks.completed")
        collector.increment("tasks.completed")
        collector.increment("tasks.completed")

        total = collector.get_total("tasks.completed")
        assert total == 3

    def test_set_gauge(self, collector):
        """Set a gauge to specific value."""
        collector.set_gauge("agent.active", 3)
        collector.set_gauge("agent.active", 2)

        current = collector.get_gauge("agent.active")
        assert current == 2

    def test_persistence(self, tmp_path: Path):
        """Metrics persist to disk."""
        collector1 = MetricsCollector(storage_dir=tmp_path)
        collector1.record("tasks.completed", 5)
        collector1.flush()

        collector2 = MetricsCollector(storage_dir=tmp_path)
        points = collector2.get_points("tasks.completed")
        assert len(points) >= 1


class TestDashboardData:
    """Test DashboardData dataclass."""

    def test_dashboard_has_key_metrics(self):
        """Dashboard has all key metrics."""
        dashboard = DashboardData(
            total_tasks=100,
            completed_tasks=85,
            failed_tasks=15,
            success_rate=0.85,
            avg_task_duration_ms=5000,
            agent_utilization=0.72,
            error_breakdown={"lint": 5, "test": 7, "type": 3}
        )

        assert dashboard.total_tasks == 100
        assert dashboard.success_rate == 0.85
        assert "lint" in dashboard.error_breakdown

    def test_dashboard_defaults(self):
        """Dashboard has sensible defaults."""
        dashboard = DashboardData()

        assert dashboard.total_tasks == 0
        assert dashboard.success_rate == 0.0


class TestGenerateDashboard:
    """Test dashboard generation."""

    @pytest.fixture
    def populated_collector(self, tmp_path: Path):
        """Create a collector with sample data."""
        collector = MetricsCollector(storage_dir=tmp_path)

        # Simulate task completions
        for i in range(85):
            collector.record("tasks.completed", 1, tags={"project": "karematch"})
            collector.record("task.duration_ms", 5000 + (i * 10))

        for i in range(15):
            collector.record("tasks.failed", 1, tags={"error_type": "lint" if i < 5 else "test"})

        collector.set_gauge("agent.active", 3)
        collector.set_gauge("agent.total", 4)

        return collector

    def test_generate_dashboard(self, populated_collector):
        """Generate dashboard from metrics."""
        dashboard = generate_dashboard(populated_collector)

        assert dashboard.total_tasks == 100
        assert dashboard.completed_tasks == 85
        assert dashboard.failed_tasks == 15
        assert 0.84 <= dashboard.success_rate <= 0.86

    def test_dashboard_error_breakdown(self, populated_collector):
        """Dashboard includes error breakdown."""
        dashboard = generate_dashboard(populated_collector)

        assert "lint" in dashboard.error_breakdown
        assert dashboard.error_breakdown["lint"] == 5

    def test_dashboard_agent_utilization(self, populated_collector):
        """Dashboard calculates agent utilization."""
        dashboard = generate_dashboard(populated_collector)

        # 3 active out of 4 total = 75%
        assert 0.74 <= dashboard.agent_utilization <= 0.76


class TestMetricsExport:
    """Test metrics export formats."""

    @pytest.fixture
    def collector(self, tmp_path: Path):
        collector = MetricsCollector(storage_dir=tmp_path)
        collector.record("tasks.completed", 10)
        collector.record("tasks.failed", 2)
        return collector

    def test_export_json(self, collector):
        """Export metrics as JSON."""
        data = collector.export_json()

        parsed = json.loads(data)
        assert "metrics" in parsed
        assert len(parsed["metrics"]) > 0

    def test_export_prometheus(self, collector):
        """Export metrics in Prometheus format."""
        data = collector.export_prometheus()

        assert "tasks_completed" in data
        assert "tasks_failed" in data


class TestRealTimeMetrics:
    """Test real-time metrics collection during execution."""

    @pytest.fixture
    def collector(self, tmp_path: Path):
        return MetricsCollector(storage_dir=tmp_path)

    def test_task_started_metric(self, collector):
        """Record when task starts."""
        collector.task_started("task-123", project="karematch")

        points = collector.get_points("task.started")
        assert len(points) == 1
        assert points[0].tags.get("task_id") == "task-123"

    def test_task_completed_metric(self, collector):
        """Record when task completes."""
        collector.task_started("task-123", project="karematch")
        collector.task_completed("task-123", duration_ms=5000)

        points = collector.get_points("task.completed")
        assert len(points) == 1

        duration_points = collector.get_points("task.duration_ms")
        assert duration_points[0].value == 5000

    def test_task_failed_metric(self, collector):
        """Record when task fails."""
        collector.task_started("task-123", project="karematch")
        collector.task_failed("task-123", error_type="lint", error="Unused import")

        points = collector.get_points("task.failed")
        assert len(points) == 1
        assert points[0].tags.get("error_type") == "lint"

    def test_agent_slot_metrics(self, collector):
        """Track agent slot utilization."""
        collector.agent_slot_acquired("agent-1", task_id="task-123")
        collector.agent_slot_released("agent-1")

        acquired = collector.get_points("agent.slot_acquired")
        released = collector.get_points("agent.slot_released")

        assert len(acquired) == 1
        assert len(released) == 1
