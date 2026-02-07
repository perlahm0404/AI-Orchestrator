"""
Tests for Phase 5 Step 5.4: ROI Calculator (TDD)

Tests the ROI calculation system:
- ROICalculator: Calculates return on investment
- Value estimation
- Cost-benefit analysis
- Break-even analysis
- Recommendations

Uses Test-Driven Development: Tests written BEFORE implementation.
"""

import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class TestROICalculation:
    """Tests for basic ROI calculation."""

    def test_calculate_simple_roi(self, tmp_path):
        """Should calculate simple ROI."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.02)

        calculator = ROICalculator(collector)
        calculator.set_task_value("TASK-001", 100.0)  # $100 value

        roi = calculator.calculate_roi("TASK-001")

        # ROI = (value - cost) / cost = (100 - 0.02) / 0.02
        expected = (100.0 - 0.02) / 0.02
        assert roi == pytest.approx(expected, rel=0.01)

    def test_calculate_run_roi(self, tmp_path):
        """Should calculate ROI for entire run."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        for i in range(5):
            collector.record_task_start(f"TASK-{i}", "test")
            collector.record_task_complete(f"TASK-{i}", "completed", "PASS", cost=0.02)

        calculator = ROICalculator(collector)
        for i in range(5):
            calculator.set_task_value(f"TASK-{i}", 50.0)

        run_roi = calculator.calculate_run_roi()

        # Total value: 5 * 50 = 250
        # Total cost: 5 * 0.02 = 0.10
        # ROI = (250 - 0.10) / 0.10
        expected = (250.0 - 0.10) / 0.10
        assert run_roi == pytest.approx(expected, rel=0.01)


class TestValueEstimation:
    """Tests for value estimation."""

    def test_estimate_value_from_priority(self, tmp_path):
        """Should estimate value based on task priority."""
        from orchestration.roi_calculator import ROICalculator, estimate_value_by_priority

        value_p0 = estimate_value_by_priority("P0")
        value_p1 = estimate_value_by_priority("P1")
        value_p2 = estimate_value_by_priority("P2")
        value_p3 = estimate_value_by_priority("P3")

        assert value_p0 > value_p1 > value_p2 > value_p3
        assert value_p0 >= 200  # P0 should be high value

    def test_estimate_value_from_type(self, tmp_path):
        """Should estimate value based on task type."""
        from orchestration.roi_calculator import estimate_value_by_type

        value_feature = estimate_value_by_type("feature")
        value_bug = estimate_value_by_type("bug")
        value_docs = estimate_value_by_type("docs")

        assert value_feature > value_bug > value_docs

    def test_auto_estimate_value(self, tmp_path):
        """Should auto-estimate value from task metadata."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.02)

        calculator = ROICalculator(collector)
        calculator.auto_estimate_value("TASK-001", priority="P1", task_type="feature")

        value = calculator.get_task_value("TASK-001")
        assert value > 0


class TestCostBenefitAnalysis:
    """Tests for cost-benefit analysis."""

    def test_calculate_net_benefit(self, tmp_path):
        """Should calculate net benefit (value - cost)."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.025)

        calculator = ROICalculator(collector)
        calculator.set_task_value("TASK-001", 100.0)

        benefit = calculator.calculate_net_benefit("TASK-001")

        assert benefit == pytest.approx(99.975, rel=0.01)

    def test_calculate_run_net_benefit(self, tmp_path):
        """Should calculate net benefit for run."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        for i in range(3):
            collector.record_task_start(f"TASK-{i}", "test")
            collector.record_task_complete(f"TASK-{i}", "completed", "PASS", cost=0.03)

        calculator = ROICalculator(collector)
        for i in range(3):
            calculator.set_task_value(f"TASK-{i}", 75.0)

        benefit = calculator.calculate_run_net_benefit()

        # Value: 3 * 75 = 225, Cost: 3 * 0.03 = 0.09
        expected = 225.0 - 0.09
        assert benefit == pytest.approx(expected, rel=0.01)

    def test_cost_per_value_unit(self, tmp_path):
        """Should calculate cost per value unit."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.05)

        calculator = ROICalculator(collector)
        calculator.set_task_value("TASK-001", 100.0)

        cost_per_value = calculator.cost_per_value_unit("TASK-001")

        # $0.05 to generate $100 value = 0.0005 per $1 value
        assert cost_per_value == pytest.approx(0.0005, rel=0.01)


class TestBreakEvenAnalysis:
    """Tests for break-even analysis."""

    def test_calculate_break_even_tasks(self, tmp_path):
        """Should calculate tasks needed to break even."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.02)

        calculator = ROICalculator(collector)
        calculator.set_task_value("TASK-001", 50.0)

        # If fixed cost is $10, and each task generates $50 - $0.02 net
        break_even = calculator.tasks_to_break_even(fixed_cost=10.0)

        # Net per task: 49.98, Need: 10 / 49.98 ~= 0.2 tasks
        assert break_even < 1  # Less than 1 task to break even

    def test_profitable_threshold(self, tmp_path):
        """Should determine minimum value for profitability."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)
        collector.record_task_start("TASK-001", "test")
        collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.05)

        calculator = ROICalculator(collector)

        # What's the minimum value for this task to be profitable?
        threshold = calculator.profitability_threshold("TASK-001")

        assert threshold == pytest.approx(0.05, rel=0.01)  # Must generate at least $0.05


class TestROIRecommendations:
    """Tests for ROI-based recommendations."""

    def test_recommend_multi_agent_based_on_roi(self, tmp_path):
        """Should recommend multi-agent based on expected ROI."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        calculator = ROICalculator(collector)

        # High value task should recommend multi-agent
        recommendation = calculator.recommend_approach(
            estimated_value=200.0,
            estimated_single_cost=0.03,
            estimated_multi_cost=0.08
        )

        assert recommendation["use_multi_agent"] is True
        assert recommendation["expected_roi"] > 0

    def test_recommend_single_agent_for_low_value(self, tmp_path):
        """Should recommend single-agent for low value tasks."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        calculator = ROICalculator(collector)

        # Low value task where multi-agent cost isn't justified
        recommendation = calculator.recommend_approach(
            estimated_value=0.10,  # Very low value
            estimated_single_cost=0.02,
            estimated_multi_cost=0.08
        )

        assert recommendation["use_multi_agent"] is False

    def test_recommend_with_quality_consideration(self, tmp_path):
        """Should factor in quality improvements."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        calculator = ROICalculator(collector)

        # Even with similar ROI, quality might tip the balance
        recommendation = calculator.recommend_approach(
            estimated_value=50.0,
            estimated_single_cost=0.02,
            estimated_multi_cost=0.05,
            single_quality_score=0.7,
            multi_quality_score=0.95  # Much better quality
        )

        # May recommend multi-agent due to quality
        assert "quality_adjusted_roi" in recommendation


class TestROIReport:
    """Tests for ROI reporting."""

    def test_generate_roi_report(self, tmp_path):
        """Should generate comprehensive ROI report."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        for i in range(5):
            collector.record_task_start(f"TASK-{i}", "test")
            collector.record_task_complete(f"TASK-{i}", "completed", "PASS", cost=0.02)

        calculator = ROICalculator(collector)
        for i in range(5):
            calculator.set_task_value(f"TASK-{i}", 50.0)

        report = calculator.generate_report()

        assert "total_value" in report
        assert "total_cost" in report
        assert "run_roi" in report
        assert "net_benefit" in report
        assert "tasks" in report

    def test_roi_report_by_specialist(self, tmp_path):
        """Should break down ROI by specialist type."""
        from orchestration.roi_calculator import ROICalculator
        from orchestration.metrics_collector import MetricsCollector

        collector = MetricsCollector(run_id="RUN-001", output_dir=tmp_path)

        collector.record_task_start("TASK-001", "test")
        collector.record_specialist_start("TASK-001", "bugfix", 15)
        collector.record_specialist_complete("TASK-001", "bugfix", 5, "PASS", 0.015)
        collector.record_task_complete("TASK-001", "completed", "PASS")

        calculator = ROICalculator(collector)
        calculator.set_task_value("TASK-001", 100.0)

        report = calculator.generate_report()

        assert "by_specialist" in report
        assert "bugfix" in report["by_specialist"]
