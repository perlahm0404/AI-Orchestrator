"""
Tests for Phase 5 Step 5.1: Validation Metrics Schema (TDD)

Tests the metrics schema for multi-agent validation:
- TaskExecutionMetrics: Per-task execution data
- SpecialistMetrics: Per-specialist performance data
- ValidationRunMetrics: Aggregate run statistics
- QualityMetrics: Code quality indicators
- CostMetrics: Cost tracking and ROI

Uses Test-Driven Development: Tests written BEFORE implementation.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List


class TestTaskExecutionMetrics:
    """Tests for per-task execution metrics."""

    def test_task_metrics_has_required_fields(self):
        """TaskExecutionMetrics should have all required fields."""
        from orchestration.validation_metrics import TaskExecutionMetrics

        metrics = TaskExecutionMetrics(
            task_id="TASK-001",
            project="credentialmate",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed"
        )

        assert hasattr(metrics, "task_id")
        assert hasattr(metrics, "project")
        assert hasattr(metrics, "started_at")
        assert hasattr(metrics, "completed_at")
        assert hasattr(metrics, "status")
        assert hasattr(metrics, "duration_seconds")
        assert hasattr(metrics, "iterations_used")
        assert hasattr(metrics, "specialists_used")
        assert hasattr(metrics, "total_cost")
        assert hasattr(metrics, "verdict")

    def test_task_metrics_calculates_duration(self):
        """TaskExecutionMetrics should calculate duration from timestamps."""
        from orchestration.validation_metrics import TaskExecutionMetrics

        start = datetime.now()
        end = start + timedelta(seconds=45.5)

        metrics = TaskExecutionMetrics(
            task_id="TASK-001",
            project="test",
            started_at=start,
            completed_at=end,
            status="completed"
        )

        assert metrics.duration_seconds == pytest.approx(45.5, rel=0.1)

    def test_task_metrics_tracks_specialists(self):
        """TaskExecutionMetrics should track which specialists were used."""
        from orchestration.validation_metrics import TaskExecutionMetrics

        metrics = TaskExecutionMetrics(
            task_id="TASK-001",
            project="test",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed",
            specialists_used=["bugfix", "testwriter"]
        )

        assert "bugfix" in metrics.specialists_used
        assert "testwriter" in metrics.specialists_used
        assert len(metrics.specialists_used) == 2

    def test_task_metrics_serializes_to_dict(self):
        """TaskExecutionMetrics should serialize to dictionary."""
        from orchestration.validation_metrics import TaskExecutionMetrics

        metrics = TaskExecutionMetrics(
            task_id="TASK-001",
            project="test",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed",
            total_cost=0.035,
            verdict="PASS"
        )

        data = metrics.to_dict()

        assert isinstance(data, dict)
        assert data["task_id"] == "TASK-001"
        assert data["total_cost"] == 0.035
        assert data["verdict"] == "PASS"


class TestSpecialistMetrics:
    """Tests for per-specialist performance metrics."""

    def test_specialist_metrics_has_required_fields(self):
        """SpecialistMetrics should have all required fields."""
        from orchestration.validation_metrics import SpecialistMetrics

        metrics = SpecialistMetrics(
            specialist_type="bugfix",
            task_id="TASK-001"
        )

        assert hasattr(metrics, "specialist_type")
        assert hasattr(metrics, "task_id")
        assert hasattr(metrics, "iterations_used")
        assert hasattr(metrics, "max_iterations")
        assert hasattr(metrics, "cost")
        assert hasattr(metrics, "verdict")
        assert hasattr(metrics, "duration_seconds")

    def test_specialist_metrics_calculates_efficiency(self):
        """SpecialistMetrics should calculate iteration efficiency."""
        from orchestration.validation_metrics import SpecialistMetrics

        metrics = SpecialistMetrics(
            specialist_type="bugfix",
            task_id="TASK-001",
            iterations_used=5,
            max_iterations=15
        )

        # Efficiency = iterations_used / max_iterations (lower is better)
        assert metrics.iteration_efficiency == pytest.approx(5 / 15, rel=0.01)

    def test_specialist_metrics_tracks_mcp_costs(self):
        """SpecialistMetrics should track MCP cost breakdown."""
        from orchestration.validation_metrics import SpecialistMetrics

        metrics = SpecialistMetrics(
            specialist_type="bugfix",
            task_id="TASK-001",
            mcp_costs={
                "ralph_verification": 0.002,
                "git_operations": 0.001
            }
        )

        assert metrics.mcp_costs["ralph_verification"] == 0.002
        assert metrics.mcp_costs["git_operations"] == 0.001


class TestValidationRunMetrics:
    """Tests for aggregate validation run metrics."""

    def test_run_metrics_has_required_fields(self):
        """ValidationRunMetrics should have all required fields."""
        from orchestration.validation_metrics import ValidationRunMetrics

        metrics = ValidationRunMetrics(
            run_id="RUN-001",
            started_at=datetime.now()
        )

        assert hasattr(metrics, "run_id")
        assert hasattr(metrics, "started_at")
        assert hasattr(metrics, "completed_at")
        assert hasattr(metrics, "tasks_total")
        assert hasattr(metrics, "tasks_completed")
        assert hasattr(metrics, "tasks_failed")
        assert hasattr(metrics, "tasks_blocked")
        assert hasattr(metrics, "total_cost")
        assert hasattr(metrics, "total_value")

    def test_run_metrics_calculates_success_rate(self):
        """ValidationRunMetrics should calculate success rate."""
        from orchestration.validation_metrics import ValidationRunMetrics

        metrics = ValidationRunMetrics(
            run_id="RUN-001",
            started_at=datetime.now(),
            tasks_total=10,
            tasks_completed=8,
            tasks_failed=1,
            tasks_blocked=1
        )

        assert metrics.success_rate == pytest.approx(0.8, rel=0.01)

    def test_run_metrics_aggregates_task_metrics(self):
        """ValidationRunMetrics should aggregate from task metrics."""
        from orchestration.validation_metrics import (
            ValidationRunMetrics,
            TaskExecutionMetrics
        )

        task1 = TaskExecutionMetrics(
            task_id="TASK-001",
            project="test",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed",
            total_cost=0.02
        )

        task2 = TaskExecutionMetrics(
            task_id="TASK-002",
            project="test",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed",
            total_cost=0.03
        )

        run_metrics = ValidationRunMetrics(
            run_id="RUN-001",
            started_at=datetime.now()
        )
        run_metrics.add_task_metrics(task1)
        run_metrics.add_task_metrics(task2)

        assert run_metrics.tasks_total == 2
        assert run_metrics.total_cost == pytest.approx(0.05, rel=0.01)


class TestQualityMetrics:
    """Tests for code quality metrics."""

    def test_quality_metrics_has_required_fields(self):
        """QualityMetrics should have all required fields."""
        from orchestration.validation_metrics import QualityMetrics

        metrics = QualityMetrics(task_id="TASK-001")

        assert hasattr(metrics, "task_id")
        assert hasattr(metrics, "tests_added")
        assert hasattr(metrics, "tests_passing")
        assert hasattr(metrics, "lint_errors_fixed")
        assert hasattr(metrics, "type_errors_fixed")
        assert hasattr(metrics, "code_coverage_delta")

    def test_quality_metrics_calculates_test_pass_rate(self):
        """QualityMetrics should calculate test pass rate."""
        from orchestration.validation_metrics import QualityMetrics

        metrics = QualityMetrics(
            task_id="TASK-001",
            tests_added=10,
            tests_passing=9
        )

        assert metrics.test_pass_rate == pytest.approx(0.9, rel=0.01)

    def test_quality_metrics_handles_no_tests(self):
        """QualityMetrics should handle case with no tests."""
        from orchestration.validation_metrics import QualityMetrics

        metrics = QualityMetrics(
            task_id="TASK-001",
            tests_added=0,
            tests_passing=0
        )

        assert metrics.test_pass_rate == 1.0  # No tests = 100% pass


class TestCostMetrics:
    """Tests for cost tracking metrics."""

    def test_cost_metrics_has_required_fields(self):
        """CostMetrics should have all required fields."""
        from orchestration.validation_metrics import CostMetrics

        metrics = CostMetrics(task_id="TASK-001")

        assert hasattr(metrics, "task_id")
        assert hasattr(metrics, "analysis_cost")
        assert hasattr(metrics, "specialist_costs")
        assert hasattr(metrics, "synthesis_cost")
        assert hasattr(metrics, "total_cost")
        assert hasattr(metrics, "estimated_value")
        assert hasattr(metrics, "roi")

    def test_cost_metrics_calculates_total(self):
        """CostMetrics should calculate total from components."""
        from orchestration.validation_metrics import CostMetrics

        metrics = CostMetrics(
            task_id="TASK-001",
            analysis_cost=0.005,
            specialist_costs={"bugfix": 0.015, "testwriter": 0.012},
            synthesis_cost=0.003
        )

        expected_total = 0.005 + 0.015 + 0.012 + 0.003
        assert metrics.total_cost == pytest.approx(expected_total, rel=0.01)

    def test_cost_metrics_calculates_roi(self):
        """CostMetrics should calculate ROI."""
        from orchestration.validation_metrics import CostMetrics

        metrics = CostMetrics(
            task_id="TASK-001",
            analysis_cost=0.005,
            specialist_costs={"bugfix": 0.015},
            synthesis_cost=0.003,
            estimated_value=100.0
        )

        # ROI = (value - cost) / cost
        total_cost = 0.005 + 0.015 + 0.003
        expected_roi = (100.0 - total_cost) / total_cost
        assert metrics.roi == pytest.approx(expected_roi, rel=0.01)

    def test_cost_metrics_handles_zero_cost(self):
        """CostMetrics should handle zero cost gracefully."""
        from orchestration.validation_metrics import CostMetrics

        metrics = CostMetrics(
            task_id="TASK-001",
            analysis_cost=0.0,
            specialist_costs={},
            synthesis_cost=0.0,
            estimated_value=50.0
        )

        assert metrics.total_cost == 0.0
        assert metrics.roi == float('inf')  # Infinite ROI with zero cost


class TestMetricsAggregation:
    """Tests for metrics aggregation utilities."""

    def test_aggregate_by_specialist_type(self):
        """Should aggregate metrics by specialist type."""
        from orchestration.validation_metrics import (
            SpecialistMetrics,
            aggregate_by_specialist
        )

        metrics = [
            SpecialistMetrics(
                specialist_type="bugfix",
                task_id="TASK-001",
                cost=0.015,
                iterations_used=5
            ),
            SpecialistMetrics(
                specialist_type="bugfix",
                task_id="TASK-002",
                cost=0.012,
                iterations_used=4
            ),
            SpecialistMetrics(
                specialist_type="testwriter",
                task_id="TASK-001",
                cost=0.010,
                iterations_used=3
            ),
        ]

        aggregated = aggregate_by_specialist(metrics)

        assert "bugfix" in aggregated
        assert "testwriter" in aggregated
        assert aggregated["bugfix"]["total_cost"] == pytest.approx(0.027, rel=0.01)
        assert aggregated["bugfix"]["avg_iterations"] == pytest.approx(4.5, rel=0.1)

    def test_aggregate_by_project(self):
        """Should aggregate metrics by project."""
        from orchestration.validation_metrics import (
            TaskExecutionMetrics,
            aggregate_by_project
        )

        metrics = [
            TaskExecutionMetrics(
                task_id="TASK-001",
                project="credentialmate",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                status="completed",
                total_cost=0.03
            ),
            TaskExecutionMetrics(
                task_id="TASK-002",
                project="credentialmate",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                status="completed",
                total_cost=0.02
            ),
            TaskExecutionMetrics(
                task_id="TASK-003",
                project="karematch",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                status="completed",
                total_cost=0.04
            ),
        ]

        aggregated = aggregate_by_project(metrics)

        assert "credentialmate" in aggregated
        assert "karematch" in aggregated
        assert aggregated["credentialmate"]["task_count"] == 2
        assert aggregated["credentialmate"]["total_cost"] == pytest.approx(0.05, rel=0.01)


class TestMetricsSerialization:
    """Tests for metrics serialization."""

    def test_metrics_serialize_to_json(self):
        """All metrics should serialize to JSON-compatible format."""
        import json
        from orchestration.validation_metrics import (
            TaskExecutionMetrics,
            SpecialistMetrics,
            ValidationRunMetrics
        )

        task = TaskExecutionMetrics(
            task_id="TASK-001",
            project="test",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed"
        )

        # Should not raise
        json_str = json.dumps(task.to_dict(), default=str)
        assert "TASK-001" in json_str

    def test_metrics_deserialize_from_dict(self):
        """Metrics should be recreatable from dictionary."""
        from orchestration.validation_metrics import TaskExecutionMetrics

        original = TaskExecutionMetrics(
            task_id="TASK-001",
            project="test",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed",
            total_cost=0.025
        )

        data = original.to_dict()
        restored = TaskExecutionMetrics.from_dict(data)

        assert restored.task_id == original.task_id
        assert restored.total_cost == original.total_cost
