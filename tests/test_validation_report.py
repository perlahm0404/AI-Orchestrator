"""
Tests for Phase 5 Step 5.3: Validation Report Generator (TDD)

Tests the report generation system:
- ValidationReportGenerator: Creates reports from metrics
- Summary reports
- Detailed breakdowns
- Markdown/JSON output
- Comparison reports

Uses Test-Driven Development: Tests written BEFORE implementation.
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any


class TestReportGeneration:
    """Tests for basic report generation."""

    def test_generate_summary_report(self, tmp_path):
        """Should generate summary report from metrics."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        # Setup collector with data
        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        for i in range(5):
            collector.record_task_start(f"TASK-{i}", "test")
            collector.record_task_complete(f"TASK-{i}", "completed", "PASS", cost=0.02)

        # Generate report
        generator = ValidationReportGenerator(collector)
        report = generator.generate_summary()

        assert "run_id" in report
        assert report["run_id"] == "RUN-001"
        assert report["tasks_total"] == 5
        assert report["tasks_completed"] == 5
        assert report["success_rate"] == 1.0

    def test_generate_detailed_report(self, tmp_path):
        """Should generate detailed report with task breakdown."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_specialist_start("TASK-001", "bugfix", 15)
        collector.record_specialist_complete("TASK-001", "bugfix", 5, "PASS", 0.015)
        collector.record_task_complete("TASK-001", "completed", "PASS")

        generator = ValidationReportGenerator(collector)
        report = generator.generate_detailed()

        assert "tasks" in report
        assert "TASK-001" in report["tasks"]
        assert "specialists" in report["tasks"]["TASK-001"]

    def test_report_includes_cost_breakdown(self, tmp_path):
        """Report should include cost breakdown."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_analysis_cost("TASK-001", 0.005)
        collector.record_specialist_start("TASK-001", "bugfix", 15)
        collector.record_specialist_complete("TASK-001", "bugfix", 5, "PASS", 0.015)
        collector.record_synthesis_cost("TASK-001", 0.003)
        collector.record_task_complete("TASK-001", "completed", "PASS")

        generator = ValidationReportGenerator(collector)
        report = generator.generate_summary()

        assert "cost_breakdown" in report
        assert report["cost_breakdown"]["analysis"] > 0
        assert report["cost_breakdown"]["specialists"] > 0
        assert report["cost_breakdown"]["synthesis"] > 0


class TestMarkdownOutput:
    """Tests for Markdown report output."""

    def test_generate_markdown_report(self, tmp_path):
        """Should generate Markdown formatted report."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.02)

        generator = ValidationReportGenerator(collector)
        markdown = generator.to_markdown()

        assert "# Validation Run Report" in markdown
        assert "RUN-001" in markdown
        assert "## Summary" in markdown

    def test_markdown_includes_tables(self, tmp_path):
        """Markdown should include formatted tables."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        for i in range(3):
            collector.record_task_start(f"TASK-{i}", "test")
            collector.record_task_complete(f"TASK-{i}", "completed", "PASS")

        generator = ValidationReportGenerator(collector)
        markdown = generator.to_markdown()

        # Should have table formatting
        assert "|" in markdown
        assert "Task ID" in markdown or "task" in markdown.lower()

    def test_save_markdown_to_file(self, tmp_path):
        """Should save Markdown report to file."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS")

        generator = ValidationReportGenerator(collector)
        output_path = generator.save_markdown(tmp_path / "report.md")

        assert output_path.exists()
        content = output_path.read_text()
        assert "Validation Run Report" in content


class TestSpecialistAnalysis:
    """Tests for specialist-level analysis in reports."""

    def test_specialist_performance_summary(self, tmp_path):
        """Should include specialist performance summary."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        # Multiple specialists
        for i in range(3):
            collector.record_task_start(f"TASK-{i}", "test")
            collector.record_specialist_start(f"TASK-{i}", "bugfix", 15)
            collector.record_specialist_complete(f"TASK-{i}", "bugfix", 5 + i, "PASS", 0.01)
            collector.record_task_complete(f"TASK-{i}", "completed", "PASS")

        generator = ValidationReportGenerator(collector)
        report = generator.generate_summary()

        assert "specialist_summary" in report
        assert "bugfix" in report["specialist_summary"]
        assert report["specialist_summary"]["bugfix"]["count"] == 3

    def test_specialist_efficiency_metrics(self, tmp_path):
        """Should calculate specialist efficiency metrics."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_specialist_start("TASK-001", "bugfix", 15)
        collector.record_specialist_complete("TASK-001", "bugfix", 5, "PASS", 0.015)
        collector.record_task_complete("TASK-001", "completed", "PASS")

        generator = ValidationReportGenerator(collector)
        report = generator.generate_detailed()

        task_report = report["tasks"]["TASK-001"]
        assert "specialists" in task_report
        assert "bugfix" in task_report["specialists"]
        # Efficiency = 5/15 = 0.333
        assert task_report["specialists"]["bugfix"]["efficiency"] == pytest.approx(5/15, rel=0.01)


class TestCostAnalysis:
    """Tests for cost analysis in reports."""

    def test_total_cost_calculation(self, tmp_path):
        """Should calculate total costs correctly."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        for i in range(5):
            collector.record_task_start(f"TASK-{i}", "test")
            collector.record_task_complete(f"TASK-{i}", "completed", "PASS", cost=0.02)

        generator = ValidationReportGenerator(collector)
        report = generator.generate_summary()

        assert report["total_cost"] == pytest.approx(0.10, rel=0.01)

    def test_average_cost_per_task(self, tmp_path):
        """Should calculate average cost per task."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.03)
        collector.record_task_start("TASK-002", "test")
        collector.record_task_complete("TASK-002", "completed", "PASS", cost=0.01)

        generator = ValidationReportGenerator(collector)
        report = generator.generate_summary()

        assert report["avg_cost_per_task"] == pytest.approx(0.02, rel=0.01)

    def test_cost_by_specialist_type(self, tmp_path):
        """Should break down costs by specialist type."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_specialist_start("TASK-001", "bugfix", 15)
        collector.record_specialist_complete("TASK-001", "bugfix", 5, "PASS", 0.015)
        collector.record_specialist_start("TASK-001", "testwriter", 15)
        collector.record_specialist_complete("TASK-001", "testwriter", 3, "PASS", 0.010)
        collector.record_task_complete("TASK-001", "completed", "PASS")

        generator = ValidationReportGenerator(collector)
        report = generator.generate_summary()

        assert "specialist_summary" in report
        assert report["specialist_summary"]["bugfix"]["total_cost"] == pytest.approx(0.015, rel=0.01)
        assert report["specialist_summary"]["testwriter"]["total_cost"] == pytest.approx(0.010, rel=0.01)


class TestQualityAnalysis:
    """Tests for quality metrics in reports."""

    def test_include_quality_metrics(self, tmp_path):
        """Should include quality metrics in report."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_tests_added("TASK-001", 10)
        collector.record_tests_passing("TASK-001", 9)
        collector.record_lint_errors_fixed("TASK-001", 5)
        collector.record_task_complete("TASK-001", "completed", "PASS")

        generator = ValidationReportGenerator(collector)
        report = generator.generate_summary()

        assert "quality" in report
        assert report["quality"]["total_tests_added"] == 10
        assert report["quality"]["total_tests_passing"] == 9


class TestComparisonReports:
    """Tests for comparing validation runs."""

    def test_compare_two_runs(self, tmp_path):
        """Should compare two validation runs."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        # Run 1
        collector1 = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        for i in range(5):
            collector1.record_task_start(f"TASK-{i}", "test")
            collector1.record_task_complete(f"TASK-{i}", "completed", "PASS", cost=0.03)
        collector1.save()

        # Run 2 (better performance)
        collector2 = MetricsCollector(run_id="RUN-002", output_dir=tmp_path)
        for i in range(5):
            collector2.record_task_start(f"TASK-{i}", "test")
            collector2.record_task_complete(f"TASK-{i}", "completed", "PASS", cost=0.02)
        collector2.save()

        comparison = ValidationReportGenerator.compare_runs(
            MetricsCollector.load(tmp_path / "RUN-001.json"),
            MetricsCollector.load(tmp_path / "RUN-002.json")
        )

        assert "cost_change" in comparison
        assert comparison["cost_change"] < 0  # Cost decreased

    def test_comparison_includes_percentage_changes(self, tmp_path):
        """Comparison should include percentage changes."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector1 = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector1.record_task_start("TASK-001", "test")
        collector1.record_task_complete("TASK-001", "completed", "PASS", cost=0.10)
        collector1.save()

        collector2 = MetricsCollector(run_id="RUN-002", output_dir=tmp_path)
        collector2.record_task_start("TASK-001", "test")
        collector2.record_task_complete("TASK-001", "completed", "PASS", cost=0.05)
        collector2.save()

        comparison = ValidationReportGenerator.compare_runs(
            MetricsCollector.load(tmp_path / "RUN-001.json"),
            MetricsCollector.load(tmp_path / "RUN-002.json")
        )

        assert "cost_change_percent" in comparison
        # 50% reduction
        assert comparison["cost_change_percent"] == pytest.approx(-50.0, rel=1.0)


class TestReportExport:
    """Tests for exporting reports."""

    def test_export_to_json(self, tmp_path):
        """Should export report to JSON file."""
        from orchestration.validation_report import ValidationReportGenerator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS")

        generator = ValidationReportGenerator(collector)
        output_path = generator.save_json(tmp_path / "report.json")

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["run_id"] == "RUN-001"
