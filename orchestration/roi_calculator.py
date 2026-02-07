"""
ROI Calculator for Multi-Agent Validation

Phase 5, Step 5.4: Calculates return on investment for validation runs:
- Value estimation
- Cost-benefit analysis
- Break-even analysis
- Multi-agent vs single-agent recommendations
- ROI reporting

Author: Claude Code
Date: 2026-02-07
"""

from typing import Dict, Any, Optional

from orchestration.metrics_collector import MetricsCollector


# Value estimation tables
VALUE_BY_PRIORITY = {
    "P0": 200.0,
    "P1": 100.0,
    "P2": 50.0,
    "P3": 25.0,
}

VALUE_BY_TYPE = {
    "feature": 100.0,
    "deploy": 150.0,
    "migration": 150.0,
    "bug": 50.0,
    "refactor": 40.0,
    "test": 30.0,
    "docs": 20.0,
}

TYPE_MULTIPLIER = {
    "feature": 1.5,
    "deploy": 2.0,
    "migration": 2.0,
    "bug": 1.0,
    "refactor": 0.8,
    "test": 0.6,
    "docs": 0.4,
}


def estimate_value_by_priority(priority: str) -> float:
    """
    Estimate task value based on priority.

    Args:
        priority: Task priority (P0, P1, P2, P3)

    Returns:
        Estimated value in USD
    """
    return VALUE_BY_PRIORITY.get(priority, 50.0)


def estimate_value_by_type(task_type: str) -> float:
    """
    Estimate task value based on type.

    Args:
        task_type: Task type (feature, bug, etc.)

    Returns:
        Estimated value in USD
    """
    return VALUE_BY_TYPE.get(task_type, 50.0)


class ROICalculator:
    """
    Calculates return on investment for validation runs.

    Supports:
    - Per-task ROI calculation
    - Run-level ROI aggregation
    - Value estimation
    - Cost-benefit analysis
    - Break-even analysis
    - Approach recommendations
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize ROI calculator.

        Args:
            collector: MetricsCollector with validation data
        """
        self.collector = collector
        self.task_values: Dict[str, float] = {}

    def set_task_value(self, task_id: str, value: float) -> None:
        """
        Set the estimated value for a task.

        Args:
            task_id: Task identifier
            value: Estimated value in USD
        """
        self.task_values[task_id] = value

    def get_task_value(self, task_id: str) -> float:
        """Get the value for a task."""
        return self.task_values.get(task_id, 0.0)

    def auto_estimate_value(
        self,
        task_id: str,
        priority: str = "P2",
        task_type: str = "bug"
    ) -> float:
        """
        Auto-estimate value based on task metadata.

        Args:
            task_id: Task identifier
            priority: Task priority
            task_type: Task type

        Returns:
            Estimated value
        """
        base_value = estimate_value_by_priority(priority)
        multiplier = TYPE_MULTIPLIER.get(task_type, 1.0)
        value = base_value * multiplier

        self.set_task_value(task_id, value)
        return value

    # =========================================================================
    # ROI Calculations
    # =========================================================================

    def calculate_roi(self, task_id: str) -> float:
        """
        Calculate ROI for a specific task.

        Args:
            task_id: Task identifier

        Returns:
            ROI as a ratio (value - cost) / cost
        """
        task_metrics = self.collector.get_task_metrics(task_id)
        if not task_metrics:
            return 0.0

        cost = task_metrics.total_cost
        value = self.task_values.get(task_id, 0.0)

        if cost == 0:
            return float('inf') if value > 0 else 0.0

        return (value - cost) / cost

    def calculate_run_roi(self) -> float:
        """
        Calculate ROI for the entire run.

        Returns:
            Run-level ROI
        """
        total_value = sum(self.task_values.values())
        run_metrics = self.collector.get_run_metrics()
        total_cost = run_metrics.total_cost

        if total_cost == 0:
            return float('inf') if total_value > 0 else 0.0

        return (total_value - total_cost) / total_cost

    # =========================================================================
    # Cost-Benefit Analysis
    # =========================================================================

    def calculate_net_benefit(self, task_id: str) -> float:
        """
        Calculate net benefit (value - cost) for a task.

        Args:
            task_id: Task identifier

        Returns:
            Net benefit in USD
        """
        task_metrics = self.collector.get_task_metrics(task_id)
        if not task_metrics:
            return 0.0

        value = self.task_values.get(task_id, 0.0)
        return value - task_metrics.total_cost

    def calculate_run_net_benefit(self) -> float:
        """
        Calculate net benefit for entire run.

        Returns:
            Net benefit in USD
        """
        total_value = sum(self.task_values.values())
        run_metrics = self.collector.get_run_metrics()
        return total_value - run_metrics.total_cost

    def cost_per_value_unit(self, task_id: str) -> float:
        """
        Calculate cost per unit of value generated.

        Args:
            task_id: Task identifier

        Returns:
            Cost per $1 of value
        """
        task_metrics = self.collector.get_task_metrics(task_id)
        if not task_metrics:
            return 0.0

        value = self.task_values.get(task_id, 0.0)
        if value == 0:
            return float('inf')

        return task_metrics.total_cost / value

    # =========================================================================
    # Break-Even Analysis
    # =========================================================================

    def tasks_to_break_even(self, fixed_cost: float = 0.0) -> float:
        """
        Calculate number of tasks needed to break even.

        Args:
            fixed_cost: Fixed costs to recover

        Returns:
            Number of tasks needed
        """
        # Calculate average net benefit per task
        run_metrics = self.collector.get_run_metrics()
        task_count = run_metrics.tasks_total

        if task_count == 0:
            return float('inf')

        total_value = sum(self.task_values.values())
        total_cost = run_metrics.total_cost
        net_per_task = (total_value - total_cost) / task_count

        if net_per_task <= 0:
            return float('inf')

        return fixed_cost / net_per_task

    def profitability_threshold(self, task_id: str) -> float:
        """
        Calculate minimum value for a task to be profitable.

        Args:
            task_id: Task identifier

        Returns:
            Minimum value in USD
        """
        task_metrics = self.collector.get_task_metrics(task_id)
        if not task_metrics:
            return 0.0

        return task_metrics.total_cost  # Break-even point

    # =========================================================================
    # Recommendations
    # =========================================================================

    def recommend_approach(
        self,
        estimated_value: float,
        estimated_single_cost: float,
        estimated_multi_cost: float,
        single_quality_score: float = 0.8,
        multi_quality_score: float = 0.9
    ) -> Dict[str, Any]:
        """
        Recommend single-agent or multi-agent approach.

        Args:
            estimated_value: Expected value of task
            estimated_single_cost: Estimated cost with single agent
            estimated_multi_cost: Estimated cost with multi-agent
            single_quality_score: Expected quality with single agent (0-1)
            multi_quality_score: Expected quality with multi-agent (0-1)

        Returns:
            Recommendation with rationale
        """
        # Calculate ROI for each approach
        if estimated_single_cost > 0:
            single_roi = (estimated_value - estimated_single_cost) / estimated_single_cost
        else:
            single_roi = float('inf')

        if estimated_multi_cost > 0:
            multi_roi = (estimated_value - estimated_multi_cost) / estimated_multi_cost
        else:
            multi_roi = float('inf')

        # Quality-adjusted value
        single_adjusted_value = estimated_value * single_quality_score
        multi_adjusted_value = estimated_value * multi_quality_score

        if estimated_single_cost > 0:
            single_quality_roi = (single_adjusted_value - estimated_single_cost) / estimated_single_cost
        else:
            single_quality_roi = float('inf')

        if estimated_multi_cost > 0:
            multi_quality_roi = (multi_adjusted_value - estimated_multi_cost) / estimated_multi_cost
        else:
            multi_quality_roi = float('inf')

        # Calculate quality-adjusted net benefits
        single_net_benefit = single_adjusted_value - estimated_single_cost
        multi_net_benefit = multi_adjusted_value - estimated_multi_cost

        # Decision: When both are profitable, compare net benefits (absolute value)
        # This correctly handles high-value tasks where quality improvement justifies cost
        if single_quality_roi > 0 and multi_quality_roi > 0:
            # Both profitable: prefer higher net benefit
            use_multi_agent = multi_net_benefit >= single_net_benefit
        else:
            # One or both unprofitable: use ROI comparison
            use_multi_agent = multi_quality_roi >= single_quality_roi

        # Also consider absolute profitability
        if multi_quality_roi < 0 and single_quality_roi >= 0:
            use_multi_agent = False
        elif single_quality_roi < 0 and multi_quality_roi >= 0:
            use_multi_agent = True

        return {
            "use_multi_agent": use_multi_agent,
            "expected_roi": multi_roi if use_multi_agent else single_roi,
            "single_roi": single_roi,
            "multi_roi": multi_roi,
            "quality_adjusted_roi": multi_quality_roi if use_multi_agent else single_quality_roi,
            "single_quality_roi": single_quality_roi,
            "multi_quality_roi": multi_quality_roi,
            "rationale": self._generate_rationale(
                use_multi_agent, single_roi, multi_roi,
                single_quality_score, multi_quality_score
            ),
        }

    def _generate_rationale(
        self,
        use_multi_agent: bool,
        single_roi: float,
        multi_roi: float,
        single_quality: float,
        multi_quality: float
    ) -> str:
        """Generate human-readable rationale."""
        if use_multi_agent:
            if multi_roi > single_roi:
                return "Multi-agent has higher ROI"
            elif multi_quality > single_quality:
                return "Multi-agent provides better quality"
            else:
                return "Multi-agent recommended for complexity"
        else:
            if single_roi > multi_roi:
                return "Single-agent is more cost-effective"
            elif single_quality >= multi_quality:
                return "Single-agent provides adequate quality"
            else:
                return "Single-agent sufficient for task"

    # =========================================================================
    # Reporting
    # =========================================================================

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive ROI report.

        Returns:
            Report dictionary
        """
        run_metrics = self.collector.get_run_metrics()
        specialist_summary = self.collector.get_specialist_summary()

        # Task-level breakdown
        tasks = {}
        for task_id in self.task_values:
            task_metrics = self.collector.get_task_metrics(task_id)
            if task_metrics:
                tasks[task_id] = {
                    "value": self.task_values[task_id],
                    "cost": task_metrics.total_cost,
                    "roi": self.calculate_roi(task_id),
                    "net_benefit": self.calculate_net_benefit(task_id),
                }

        # Specialist breakdown
        by_specialist: Dict[str, Dict[str, Any]] = {}
        for spec_type, stats in specialist_summary.items():
            by_specialist[spec_type] = {
                "total_cost": stats.get("total_cost", 0.0),
                "avg_cost": stats.get("avg_cost", 0.0),
                "count": stats.get("count", 0),
            }

        return {
            "run_id": self.collector.run_id,
            "total_value": sum(self.task_values.values()),
            "total_cost": run_metrics.total_cost,
            "run_roi": self.calculate_run_roi(),
            "net_benefit": self.calculate_run_net_benefit(),
            "tasks_total": run_metrics.tasks_total,
            "tasks_completed": run_metrics.tasks_completed,
            "success_rate": run_metrics.success_rate,
            "tasks": tasks,
            "by_specialist": by_specialist,
        }
