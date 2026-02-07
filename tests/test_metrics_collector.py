"""
Tests for Phase 5 Step 5.2: Metrics Collector (TDD)

Tests the metrics collection system:
- MetricsCollector: Collects and stores metrics during validation
- Real-time metric recording
- Persistence to JSON/SQLite
- Retrieval and querying

Uses Test-Driven Development: Tests written BEFORE implementation.
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any


class TestMetricsCollectorInitialization:
    """Tests for MetricsCollector initialization."""

    def test_collector_initializes_with_run_id(self, tmp_path):
        """MetricsCollector should initialize with a run ID."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(
            run_id="RUN-001",
            output_dir=tmp_path
        )

        assert collector.run_id == "RUN-001"
        assert collector.output_dir == tmp_path

    def test_collector_creates_output_directory(self, tmp_path):
        """MetricsCollector should create output directory if needed."""
        from orchestration.metrics_collector import MetricsCollector

        output_dir = tmp_path / "metrics"
        collector = MetricsCollector(
            run_id="RUN-001",
            output_dir=output_dir
        )

        assert output_dir.exists()

    def test_collector_auto_generates_run_id(self, tmp_path):
        """MetricsCollector should auto-generate run ID if not provided."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(output_dir=tmp_path)

        assert collector.run_id is not None
        assert len(collector.run_id) > 0


class TestTaskMetricsCollection:
    """Tests for collecting task execution metrics."""

    def test_record_task_start(self, tmp_path):
        """Should record task start with timestamp."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start(
            task_id="TASK-001",
            project="credentialmate"
        )

        assert "TASK-001" in collector.active_tasks
        assert collector.active_tasks["TASK-001"]["started_at"] is not None

    def test_record_task_complete(self, tmp_path):
        """Should record task completion with metrics."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete(
            task_id="TASK-001",
            status="completed",
            verdict="PASS",
            iterations=5,
            cost=0.025
        )

        metrics = collector.get_task_metrics("TASK-001")
        assert metrics is not None
        assert metrics.status == "completed"
        assert metrics.verdict == "PASS"
        assert metrics.iterations_used == 5
        assert metrics.total_cost == 0.025

    def test_record_task_with_specialists(self, tmp_path):
        """Should track specialists used in task."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_specialist_used("TASK-001", "bugfix")
        collector.record_specialist_used("TASK-001", "testwriter")
        collector.record_task_complete(
            task_id="TASK-001",
            status="completed",
            verdict="PASS"
        )

        metrics = collector.get_task_metrics("TASK-001")
        assert "bugfix" in metrics.specialists_used
        assert "testwriter" in metrics.specialists_used


class TestSpecialistMetricsCollection:
    """Tests for collecting specialist metrics."""

    def test_record_specialist_start(self, tmp_path):
        """Should record specialist execution start."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_specialist_start(
            task_id="TASK-001",
            specialist_type="bugfix",
            max_iterations=15
        )

        assert ("TASK-001", "bugfix") in collector.active_specialists

    def test_record_specialist_complete(self, tmp_path):
        """Should record specialist completion with metrics."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_specialist_start("TASK-001", "bugfix", 15)
        collector.record_specialist_complete(
            task_id="TASK-001",
            specialist_type="bugfix",
            iterations_used=5,
            verdict="PASS",
            cost=0.015
        )

        metrics = collector.get_specialist_metrics("TASK-001", "bugfix")
        assert metrics is not None
        assert metrics.iterations_used == 5
        assert metrics.cost == 0.015

    def test_record_specialist_mcp_cost(self, tmp_path):
        """Should track MCP costs for specialist."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_specialist_start("TASK-001", "bugfix", 15)
        collector.record_mcp_cost("TASK-001", "bugfix", "ralph_verification", 0.002)
        collector.record_mcp_cost("TASK-001", "bugfix", "git_operations", 0.001)
        collector.record_specialist_complete(
            task_id="TASK-001",
            specialist_type="bugfix",
            iterations_used=5,
            verdict="PASS"
        )

        metrics = collector.get_specialist_metrics("TASK-001", "bugfix")
        assert metrics.mcp_costs["ralph_verification"] == 0.002
        assert metrics.mcp_costs["git_operations"] == 0.001


class TestCostMetricsCollection:
    """Tests for collecting cost metrics."""

    def test_record_analysis_cost(self, tmp_path):
        """Should record analysis phase cost."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_analysis_cost("TASK-001", 0.005)

        cost_metrics = collector.get_cost_metrics("TASK-001")
        assert cost_metrics.analysis_cost == 0.005

    def test_record_synthesis_cost(self, tmp_path):
        """Should record synthesis phase cost."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_synthesis_cost("TASK-001", 0.003)

        cost_metrics = collector.get_cost_metrics("TASK-001")
        assert cost_metrics.synthesis_cost == 0.003

    def test_aggregate_costs(self, tmp_path):
        """Should aggregate all costs for a task."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_analysis_cost("TASK-001", 0.005)
        collector.record_specialist_start("TASK-001", "bugfix", 15)
        collector.record_specialist_complete(
            "TASK-001", "bugfix", 5, "PASS", 0.015
        )
        collector.record_synthesis_cost("TASK-001", 0.003)

        cost_metrics = collector.get_cost_metrics("TASK-001")
        expected_total = 0.005 + 0.015 + 0.003
        assert cost_metrics.total_cost == pytest.approx(expected_total, rel=0.01)


class TestQualityMetricsCollection:
    """Tests for collecting quality metrics."""

    def test_record_tests_added(self, tmp_path):
        """Should record tests added during task."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_tests_added("TASK-001", 5)
        collector.record_tests_passing("TASK-001", 4)

        quality = collector.get_quality_metrics("TASK-001")
        assert quality.tests_added == 5
        assert quality.tests_passing == 4

    def test_record_lint_errors_fixed(self, tmp_path):
        """Should record lint errors fixed."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_lint_errors_fixed("TASK-001", 10)

        quality = collector.get_quality_metrics("TASK-001")
        assert quality.lint_errors_fixed == 10


class TestPersistence:
    """Tests for metrics persistence."""

    def test_save_to_json(self, tmp_path):
        """Should save metrics to JSON file."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS")

        collector.save()

        json_file = tmp_path / "RUN-001.json"
        assert json_file.exists()

        with open(json_file) as f:
            data = json.load(f)

        assert data["run_id"] == "RUN-001"
        assert "tasks" in data

    def test_load_from_json(self, tmp_path):
        """Should load metrics from JSON file."""
        from orchestration.metrics_collector import MetricsCollector

        # Create and save
        collector1 = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector1.record_task_start("TASK-001", "test")
        collector1.record_task_complete("TASK-001", "completed", "PASS", cost=0.02)
        collector1.save()

        # Load
        collector2 = MetricsCollector.load(tmp_path / "RUN-001.json")

        assert collector2.run_id == "RUN-001"
        task_metrics = collector2.get_task_metrics("TASK-001")
        assert task_metrics is not None
        assert task_metrics.total_cost == 0.02

    def test_auto_save_on_task_complete(self, tmp_path):
        """Should auto-save after task completion when enabled."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(
            run_id="RUN-001",
            output_dir=tmp_path,
            auto_save=True
        )

        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS")

        json_file = tmp_path / "RUN-001.json"
        assert json_file.exists()


class TestRunAggregation:
    """Tests for run-level aggregation."""

    def test_get_run_metrics(self, tmp_path):
        """Should aggregate metrics at run level."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        # Record multiple tasks
        for i in range(5):
            collector.record_task_start(f"TASK-{i}", "test")
            status = "completed" if i < 4 else "failed"
            collector.record_task_complete(
                f"TASK-{i}",
                status=status,
                verdict="PASS" if status == "completed" else "FAIL",
                cost=0.01
            )

        run_metrics = collector.get_run_metrics()

        assert run_metrics.tasks_total == 5
        assert run_metrics.tasks_completed == 4
        assert run_metrics.tasks_failed == 1
        assert run_metrics.success_rate == pytest.approx(0.8, rel=0.01)
        assert run_metrics.total_cost == pytest.approx(0.05, rel=0.01)

    def test_get_specialist_summary(self, tmp_path):
        """Should provide specialist-level summary."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        # Multiple tasks with specialists
        for i in range(3):
            collector.record_task_start(f"TASK-{i}", "test")
            collector.record_specialist_start(f"TASK-{i}", "bugfix", 15)
            collector.record_specialist_complete(
                f"TASK-{i}", "bugfix", 5, "PASS", 0.015
            )
            collector.record_task_complete(f"TASK-{i}", "completed", "PASS")

        summary = collector.get_specialist_summary()

        assert "bugfix" in summary
        assert summary["bugfix"]["count"] == 3
        assert summary["bugfix"]["total_cost"] == pytest.approx(0.045, rel=0.01)


class TestRealTimeUpdates:
    """Tests for real-time metric updates."""

    def test_register_callback(self, tmp_path):
        """Should support callback registration for real-time updates."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        events = []

        def on_task_complete(task_id, metrics):
            events.append(("task_complete", task_id))

        collector.on_task_complete(on_task_complete)

        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS")

        assert len(events) == 1
        assert events[0] == ("task_complete", "TASK-001")

    def test_get_live_stats(self, tmp_path):
        """Should provide live statistics during run."""
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_task_start("TASK-002", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.02)

        stats = collector.get_live_stats()

        assert stats["tasks_in_progress"] == 1
        assert stats["tasks_completed"] == 1
        assert stats["current_cost"] == pytest.approx(0.02, rel=0.01)
