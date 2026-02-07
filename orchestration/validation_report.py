"""
Validation Report Generator for Multi-Agent System

Phase 5, Step 5.3: Generates reports from validation metrics:
- Summary reports
- Detailed task breakdowns
- Specialist analysis
- Cost analysis
- Quality metrics
- Markdown and JSON output
- Run comparisons

Author: Claude Code
Date: 2026-02-07
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from orchestration.metrics_collector import MetricsCollector


class ValidationReportGenerator:
    """
    Generates validation reports from collected metrics.

    Supports:
    - Summary reports with key metrics
    - Detailed task-level breakdowns
    - Specialist performance analysis
    - Cost breakdowns
    - Quality metrics
    - Markdown and JSON output
    - Run comparisons
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize report generator.

        Args:
            collector: MetricsCollector with validation data
        """
        self.collector = collector

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate summary report with key metrics.

        Returns:
            Dict with summary metrics
        """
        run_metrics = self.collector.get_run_metrics()
        specialist_summary = self.collector.get_specialist_summary()

        # Calculate cost breakdown
        total_analysis = 0.0
        total_synthesis = 0.0
        total_specialist = 0.0

        for task_id, cost_metrics in self.collector.cost_metrics.items():
            total_analysis += cost_metrics.analysis_cost
            total_synthesis += cost_metrics.synthesis_cost
            total_specialist += sum(cost_metrics.specialist_costs.values())

        # Calculate quality totals
        total_tests_added = 0
        total_tests_passing = 0
        total_lint_fixed = 0

        for task_id, quality in self.collector.quality_metrics.items():
            total_tests_added += quality.tests_added
            total_tests_passing += quality.tests_passing
            total_lint_fixed += quality.lint_errors_fixed

        # Calculate averages
        task_count = run_metrics.tasks_total or 1
        avg_cost = run_metrics.total_cost / task_count

        return {
            "run_id": self.collector.run_id,
            "started_at": self.collector.run_started_at.isoformat(),
            "completed_at": self.collector.run_completed_at.isoformat() if self.collector.run_completed_at else None,
            "duration_seconds": run_metrics.duration_seconds,
            "tasks_total": run_metrics.tasks_total,
            "tasks_completed": run_metrics.tasks_completed,
            "tasks_failed": run_metrics.tasks_failed,
            "tasks_blocked": run_metrics.tasks_blocked,
            "success_rate": run_metrics.success_rate,
            "total_cost": run_metrics.total_cost,
            "avg_cost_per_task": avg_cost,
            "cost_breakdown": {
                "analysis": total_analysis,
                "specialists": total_specialist,
                "synthesis": total_synthesis,
            },
            "specialist_summary": specialist_summary,
            "quality": {
                "total_tests_added": total_tests_added,
                "total_tests_passing": total_tests_passing,
                "total_lint_errors_fixed": total_lint_fixed,
            },
        }

    def generate_detailed(self) -> Dict[str, Any]:
        """
        Generate detailed report with task-level breakdown.

        Returns:
            Dict with detailed metrics per task
        """
        summary = self.generate_summary()

        # Add task details
        tasks = {}
        for task_id, task_metrics in self.collector.task_metrics.items():
            task_data = task_metrics.to_dict()

            # Add specialist details for this task
            specialists = {}
            for (t_id, spec_type), spec_metrics in self.collector.specialist_metrics.items():
                if t_id == task_id:
                    specialists[spec_type] = {
                        "iterations_used": spec_metrics.iterations_used,
                        "max_iterations": spec_metrics.max_iterations,
                        "efficiency": spec_metrics.iteration_efficiency,
                        "cost": spec_metrics.cost,
                        "verdict": spec_metrics.verdict,
                        "mcp_costs": spec_metrics.mcp_costs,
                    }

            task_data["specialists"] = specialists

            # Add cost details
            if task_id in self.collector.cost_metrics:
                cost = self.collector.cost_metrics[task_id]
                task_data["cost_details"] = cost.to_dict()

            # Add quality details
            if task_id in self.collector.quality_metrics:
                quality = self.collector.quality_metrics[task_id]
                task_data["quality_details"] = quality.to_dict()

            tasks[task_id] = task_data

        return {
            **summary,
            "tasks": tasks,
        }

    def to_markdown(self) -> str:
        """
        Generate Markdown formatted report.

        Returns:
            Markdown string
        """
        report = self.generate_summary()

        lines = [
            "# Validation Run Report",
            "",
            f"**Run ID**: {report['run_id']}",
            f"**Started**: {report['started_at']}",
            f"**Completed**: {report['completed_at'] or 'In Progress'}",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Tasks Total | {report['tasks_total']} |",
            f"| Tasks Completed | {report['tasks_completed']} |",
            f"| Tasks Failed | {report['tasks_failed']} |",
            f"| Success Rate | {report['success_rate']:.1%} |",
            f"| Total Cost | ${report['total_cost']:.4f} |",
            f"| Avg Cost/Task | ${report['avg_cost_per_task']:.4f} |",
            "",
            "## Cost Breakdown",
            "",
            f"| Phase | Cost |",
            f"|-------|------|",
            f"| Analysis | ${report['cost_breakdown']['analysis']:.4f} |",
            f"| Specialists | ${report['cost_breakdown']['specialists']:.4f} |",
            f"| Synthesis | ${report['cost_breakdown']['synthesis']:.4f} |",
            "",
        ]

        # Specialist summary
        if report.get("specialist_summary"):
            lines.extend([
                "## Specialist Performance",
                "",
                "| Specialist | Count | Total Cost | Avg Iterations |",
                "|------------|-------|------------|----------------|",
            ])

            for spec_type, stats in report["specialist_summary"].items():
                lines.append(
                    f"| {spec_type} | {stats.get('count', 0)} | "
                    f"${stats.get('total_cost', 0):.4f} | "
                    f"{stats.get('avg_iterations', 0):.1f} |"
                )

            lines.append("")

        # Quality metrics
        if report.get("quality"):
            quality = report["quality"]
            lines.extend([
                "## Quality Metrics",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Tests Added | {quality['total_tests_added']} |",
                f"| Tests Passing | {quality['total_tests_passing']} |",
                f"| Lint Errors Fixed | {quality['total_lint_errors_fixed']} |",
                "",
            ])

        # Task table
        lines.extend([
            "## Tasks",
            "",
            "| Task ID | Status | Verdict | Cost | Iterations |",
            "|---------|--------|---------|------|------------|",
        ])

        for task_id, task_metrics in self.collector.task_metrics.items():
            lines.append(
                f"| {task_id} | {task_metrics.status} | {task_metrics.verdict} | "
                f"${task_metrics.total_cost:.4f} | {task_metrics.iterations_used} |"
            )

        lines.append("")
        lines.append(f"*Generated at {datetime.now().isoformat()}*")

        return "\n".join(lines)

    def save_markdown(self, path: Path) -> Path:
        """
        Save Markdown report to file.

        Args:
            path: Output file path

        Returns:
            Path to saved file
        """
        path = Path(path)
        path.write_text(self.to_markdown())
        return path

    def save_json(self, path: Path) -> Path:
        """
        Save JSON report to file.

        Args:
            path: Output file path

        Returns:
            Path to saved file
        """
        path = Path(path)
        report = self.generate_detailed()

        with open(path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        return path

    @staticmethod
    def compare_runs(
        run1: MetricsCollector,
        run2: MetricsCollector
    ) -> Dict[str, Any]:
        """
        Compare two validation runs.

        Args:
            run1: First (baseline) run
            run2: Second (comparison) run

        Returns:
            Comparison metrics
        """
        metrics1 = run1.get_run_metrics()
        metrics2 = run2.get_run_metrics()

        cost_change = metrics2.total_cost - metrics1.total_cost
        cost_change_percent = (
            (cost_change / metrics1.total_cost * 100)
            if metrics1.total_cost > 0 else 0.0
        )

        success_change = metrics2.success_rate - metrics1.success_rate
        success_change_percent = success_change * 100

        return {
            "baseline_run": run1.run_id,
            "comparison_run": run2.run_id,
            "cost_change": cost_change,
            "cost_change_percent": cost_change_percent,
            "success_rate_change": success_change,
            "success_rate_change_percent": success_change_percent,
            "baseline_metrics": {
                "total_cost": metrics1.total_cost,
                "success_rate": metrics1.success_rate,
                "tasks_total": metrics1.tasks_total,
            },
            "comparison_metrics": {
                "total_cost": metrics2.total_cost,
                "success_rate": metrics2.success_rate,
                "tasks_total": metrics2.tasks_total,
            },
            "improved": cost_change < 0 or success_change > 0,
        }
