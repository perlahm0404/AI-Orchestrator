"""
Report Generator - Generate comprehensive PM status reports.

Combines task aggregation, evidence coverage, and meta-agent coordination
into unified weekly + on-demand reports.
"""

from dataclasses import asdict
from datetime import datetime
from typing import Dict, Any, List
from .task_aggregator import TaskAggregator, ProjectRollup, ADRStatus
from .report_formatter import ReportFormatter


class ReportGenerator:
    """Generate comprehensive PM status reports"""

    def __init__(self) -> None:
        self.aggregator = TaskAggregator()
        self.formatter = ReportFormatter()

    def generate_report(self, project: str) -> Dict[str, Any]:
        """Generate comprehensive status report for a project"""

        # Aggregate project data
        rollup = self.aggregator.aggregate_by_project(project)

        # Get current date
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        timestamp_str = now.strftime("%Y-%m-%d %A %H:%M")

        # Count task statuses across all ADRs
        tasks_pending = sum(adr.tasks_pending for adr in rollup.adrs)
        tasks_in_progress = sum(adr.tasks_in_progress for adr in rollup.adrs)
        tasks_completed = sum(adr.tasks_completed for adr in rollup.adrs)
        tasks_blocked = sum(adr.tasks_blocked for adr in rollup.adrs)

        # Find blockers
        blockers = self._identify_blockers(rollup)

        # Build report data
        report_data = {
            "project": project,
            "generated_at": timestamp_str,
            "date": date_str,

            # Task summary
            "total_tasks": rollup.total_tasks,
            "tasks_pending": tasks_pending,
            "tasks_in_progress": tasks_in_progress,
            "tasks_completed": tasks_completed,
            "tasks_blocked": tasks_blocked,

            # ADRs
            "adrs": [self._adr_to_dict(adr) for adr in rollup.adrs],

            # Evidence
            "evidence_coverage_pct": rollup.evidence_coverage_pct,
            "evidence_count": self.aggregator.count_evidence_items(),

            # Risk (placeholder for Governance agent)
            "high_risk_count": rollup.high_risk_count,

            # Blockers
            "blockers": blockers
        }

        return report_data

    def _adr_to_dict(self, adr: ADRStatus) -> Dict[str, Any]:
        """Convert ADRStatus to dict"""
        return {
            "adr_id": adr.adr_id,
            "title": adr.title,
            "project": adr.project,
            "status": adr.status,
            "total_tasks": adr.total_tasks,
            "tasks_pending": adr.tasks_pending,
            "tasks_in_progress": adr.tasks_in_progress,
            "tasks_completed": adr.tasks_completed,
            "tasks_blocked": adr.tasks_blocked,
            "evidence_refs": adr.evidence_refs,
            "progress_pct": adr.progress_pct
        }

    def _identify_blockers(self, rollup: ProjectRollup) -> List[Dict[str, str]]:
        """Identify blocked tasks from rollup"""
        blockers = []

        # Load all tasks for this project
        tasks = self.aggregator.load_all_queues(project=rollup.project)

        for task in tasks:
            if task.get("status") == "blocked" or task.get("verification_verdict") == "BLOCKED":
                # Find associated ADR
                source = task.get("source", "")
                adr_id = "Unknown"
                if "ADR-" in source:
                    import re
                    matches = re.findall(r'ADR-\d+', source)
                    if matches:
                        adr_id = matches[0]

                error_msg = task.get("error") or "No error message"
                blockers.append({
                    "task_id": task.get("id", "unknown"),
                    "adr": adr_id,
                    "reason": str(error_msg)[:100]
                })

        return blockers[:10]  # Top 10 blockers

    def generate_and_save(self, project: str, output_dir: str = "work/reports") -> Dict[str, str]:
        """Generate report and save in all three formats"""
        import os

        # Generate report data
        report_data = self.generate_report(project)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Generate filenames
        date_str = report_data["date"]
        base_filename = f"{project}-{date_str}"

        # Save markdown
        markdown_content = self.formatter.format_markdown(report_data)
        markdown_path = os.path.join(output_dir, f"{base_filename}.md")
        self.formatter.save_report(markdown_content, markdown_path)

        # Save grid
        grid_content = self.formatter.format_grid(report_data)
        grid_path = os.path.join(output_dir, f"{base_filename}-grid.txt")
        self.formatter.save_report(grid_content, grid_path)

        # Save JSON
        json_content = self.formatter.format_json(report_data)
        json_path = os.path.join(output_dir, f"{base_filename}.json")
        self.formatter.save_report(json_content, json_path)

        return {
            "markdown": markdown_path,
            "grid": grid_path,
            "json": json_path
        }
