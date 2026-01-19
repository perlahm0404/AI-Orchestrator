#!/usr/bin/env python3
"""
Dashboard Generator - Creates human-readable DASHBOARD.md from mission control data

Usage:
    python mission-control/tools/generate_dashboard.py
    python mission-control/tools/generate_dashboard.py --force
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Any, List, Optional


class DashboardGenerator:
    """Generates DASHBOARD.md from mission control metrics"""

    def __init__(self, mission_control_dir: Path):
        self.mission_control = mission_control_dir
        self.work_queues_dir = self.mission_control / "work-queues"
        self.metrics_dir = self.mission_control / "metrics"
        self.vibe_kanban_dir = self.mission_control / "vibe-kanban"
        self.dashboard_file = self.mission_control / "DASHBOARD.md"

    def load_aggregate_view(self) -> Optional[dict[str, Any]]:
        """Load work queue aggregate view"""
        aggregate_file = self.work_queues_dir / "aggregate-view.json"
        if not aggregate_file.exists():
            return None

        try:
            with open(aggregate_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except Exception as e:
            print(f"Warning: Failed to load aggregate view: {e}")
            return None

    def load_agent_metrics(self) -> Optional[dict[str, Any]]:
        """Load agent performance metrics"""
        metrics_file = self.metrics_dir / "agent-performance.json"
        if not metrics_file.exists():
            return None

        try:
            with open(metrics_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except Exception as e:
            print(f"Warning: Failed to load agent metrics: {e}")
            return None

    def load_repo_metrics(self) -> Optional[dict[str, Any]]:
        """Load repo performance metrics"""
        metrics_file = self.metrics_dir / "repo-performance.json"
        if not metrics_file.exists():
            return None

        try:
            with open(metrics_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except Exception as e:
            print(f"Warning: Failed to load repo metrics: {e}")
            return None

    def load_unified_board(self) -> Optional[dict[str, Any]]:
        """Load unified kanban board"""
        board_file = self.vibe_kanban_dir / "unified-board.json"
        if not board_file.exists():
            return None

        try:
            with open(board_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except Exception as e:
            print(f"Warning: Failed to load unified board: {e}")
            return None

    def calculate_system_health(self, aggregate: Optional[dict[str, Any]], repo_metrics: Optional[dict[str, Any]]) -> str:
        """Calculate overall system health status"""
        if not aggregate or not repo_metrics:
            return "🟡 DEGRADED"

        summary = aggregate.get("summary", {})
        total_tasks = summary.get("total_tasks", 0)
        blocked = summary.get("blocked", 0)

        # Check for blockers
        if blocked > 0:
            return "🟡 DEGRADED"

        # Check autonomy (from repo metrics)
        repos = repo_metrics.get("repos", [])
        if repos:
            avg_autonomy = sum(r.get("autonomy_pct", 0) for r in repos) / len(repos)
            if avg_autonomy >= 85:
                return "🟢 HEALTHY"
            elif avg_autonomy >= 70:
                return "🟡 DEGRADED"
            else:
                return "🔴 CRITICAL"

        return "🟡 DEGRADED"

    def generate_header(self) -> List[str]:
        """Generate dashboard header"""
        lines = []
        lines.append("# Mission Control Dashboard")
        lines.append("")
        lines.append(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("**Version**: AI Orchestrator v6.0")
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def generate_system_health_section(self, aggregate: Optional[dict[str, Any]], repo_metrics: Optional[dict[str, Any]]) -> List[str]:
        """Generate system health section"""
        lines = []
        health_status = self.calculate_system_health(aggregate or {}, repo_metrics or {})

        lines.append("## System Health")
        lines.append("")
        lines.append(f"**Status**: {health_status}")
        lines.append("")

        # Calculate key metrics
        if aggregate:
            summary = aggregate.get("summary", {})
            lines.append("| Metric | Value |")
            lines.append("|---|---|")
            lines.append(f"| Total Tasks | {summary.get('total_tasks', 0)} |")
            lines.append(f"| Pending | {summary.get('pending', 0)} |")
            lines.append(f"| In Progress | {summary.get('in_progress', 0)} |")
            lines.append(f"| Blocked | {summary.get('blocked', 0)} |")
            lines.append(f"| Completed | {summary.get('completed', 0)} |")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def generate_repo_status_section(self, aggregate: Optional[dict[str, Any]], repo_metrics: Optional[dict[str, Any]]) -> List[str]:
        """Generate repo status section"""
        lines = []
        lines.append("## Repo Status")
        lines.append("")

        if not repo_metrics:
            lines.append("*No metrics available*")
            lines.append("")
            return lines

        lines.append("| Repo | Total | Pending | In Progress | Blocked | Completed | Autonomy |")
        lines.append("|---|---|---|---|---|---|---|")

        for repo in repo_metrics.get("repos", []):
            repo_name = repo.get("repo_name", "unknown")
            total = repo.get("total_tasks", 0)
            pending = repo.get("pending_tasks", 0)
            in_progress = repo.get("in_progress_tasks", 0)
            blocked = repo.get("blocked_tasks", 0)
            completed = repo.get("completed_tasks", 0)
            autonomy = repo.get("autonomy_pct", 0.0)

            # Status icon
            icon = "🟢" if autonomy >= 85 else "🟡" if autonomy >= 70 else "🔴"

            lines.append(
                f"| {icon} {repo_name} | {total} | {pending} | {in_progress} | "
                f"{blocked} | {completed} | {autonomy:.1f}% |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def generate_agent_performance_section(self, agent_metrics: Optional[dict[str, Any]]) -> List[str]:
        """Generate agent performance section"""
        lines = []
        lines.append("## Agent Performance")
        lines.append("")

        if not agent_metrics or not agent_metrics.get("agents"):
            lines.append("*No agent metrics available*")
            lines.append("")
            return lines

        lines.append("| Agent | Tasks | Success Rate | Avg Iterations | Escalations |")
        lines.append("|---|---|---|---|---|")

        for agent in agent_metrics.get("agents", []):
            agent_type = agent.get("agent_type", "unknown")
            total = agent.get("total_tasks", 0)
            success_rate = agent.get("success_rate", 0.0)
            avg_iterations = agent.get("avg_iterations", 0.0)
            escalations = agent.get("escalation_count", 0)
            escalation_rate = agent.get("escalation_rate", 0.0)

            # Status icon
            icon = "🟢" if success_rate >= 85 else "🟡" if success_rate >= 70 else "🔴"

            lines.append(
                f"| {icon} {agent_type} | {total} | {success_rate:.1f}% | "
                f"{avg_iterations:.1f} | {escalations} ({escalation_rate:.1f}%) |"
            )

        lines.append("")
        lines.append("**Thresholds**: 🟢 ≥85% | 🟡 70-85% | 🔴 <70%")
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def generate_kanban_overview_section(self, unified_board: Optional[dict[str, Any]]) -> List[str]:
        """Generate vibe kanban overview section"""
        lines = []
        lines.append("## Vibe Kanban Overview")
        lines.append("")

        if not unified_board:
            lines.append("*No kanban data available*")
            lines.append("")
            return lines

        summary = unified_board.get("summary", {})
        objectives = unified_board.get("objectives", [])

        lines.append(f"- **Objectives**: {summary.get('total_objectives', 0)}")
        lines.append(f"- **ADRs**: {summary.get('total_adrs', 0)}")
        lines.append(f"- **Tasks**: {summary.get('total_tasks', 0)}")
        lines.append("")

        if objectives:
            lines.append("### Active Objectives")
            lines.append("")
            lines.append("| ID | Repo | Title | Progress | Tasks |")
            lines.append("|---|---|---|---|---|")

            for obj in objectives[:10]:  # Show first 10
                progress_pct = obj.get("completion_pct", 0.0)
                progress_bar = self._generate_progress_bar(progress_pct)

                lines.append(
                    f"| {obj.get('id', 'unknown')} | {obj.get('repo', 'unknown')} | "
                    f"{obj.get('title', 'Untitled')} | {progress_bar} | "
                    f"{obj.get('tasks_complete', 0)}/{obj.get('tasks_total', 0)} |"
                )

            if len(objectives) > 10:
                lines.append(f"| ... | ... | *+{len(objectives) - 10} more* | ... | ... |")

        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def generate_alerts_section(self, aggregate: Optional[dict[str, Any]]) -> List[str]:
        """Generate alerts and issues section"""
        lines = []
        lines.append("## Alerts & Issues")
        lines.append("")

        if not aggregate:
            lines.append("*No alerts*")
            lines.append("")
            return lines

        alerts = aggregate.get("alerts", [])

        if not alerts:
            lines.append("✅ No active alerts")
            lines.append("")
        else:
            lines.append(f"⚠️  **{len(alerts)} alert(s) detected**")
            lines.append("")

            for alert in alerts[:10]:  # Show first 10
                alert_type = alert.get("type", "unknown")
                task_id = alert.get("task_id", "unknown")
                repo = alert.get("repo", "unknown")
                title = alert.get("title", "Unknown task")

                if alert_type == "blocked_task":
                    lines.append(f"- 🔴 **Blocked Task**: {title} (`{task_id}`) in `{repo}`")
                else:
                    lines.append(f"- ⚠️ **{alert_type}**: {title} (`{task_id}`)")

            if len(alerts) > 10:
                lines.append(f"- _(+{len(alerts) - 10} more alerts)_")

            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def generate_quick_actions_section(self) -> List[str]:
        """Generate quick actions section"""
        lines = []
        lines.append("## Quick Actions")
        lines.append("")
        lines.append("```bash")
        lines.append("# Refresh all data")
        lines.append("python mission-control/tools/sync_work_queues.py --all")
        lines.append("python mission-control/tools/aggregate_kanban.py")
        lines.append("python mission-control/tools/collect_metrics.py")
        lines.append("python mission-control/tools/generate_dashboard.py")
        lines.append("")
        lines.append("# View specific data")
        lines.append("cat mission-control/work-queues/aggregate-view.json")
        lines.append("cat mission-control/vibe-kanban/unified-board.md")
        lines.append("cat mission-control/metrics/agent-performance.json")
        lines.append("```")
        lines.append("")
        return lines

    def _generate_progress_bar(self, percentage: float, width: int = 10) -> str:
        """Generate text-based progress bar"""
        filled = int(percentage / 100 * width)
        empty = width - filled
        return f"{'█' * filled}{'░' * empty} {percentage:.0f}%"

    def generate_dashboard(self) -> str:
        """Generate complete dashboard"""
        # Load data
        aggregate = self.load_aggregate_view()
        agent_metrics = self.load_agent_metrics()
        repo_metrics = self.load_repo_metrics()
        unified_board = self.load_unified_board()

        # Build dashboard sections
        lines = []
        lines.extend(self.generate_header())
        lines.extend(self.generate_system_health_section(aggregate, repo_metrics))
        lines.extend(self.generate_repo_status_section(aggregate, repo_metrics))
        lines.extend(self.generate_agent_performance_section(agent_metrics))
        lines.extend(self.generate_kanban_overview_section(unified_board))
        lines.extend(self.generate_alerts_section(aggregate))
        lines.extend(self.generate_quick_actions_section())

        return "\n".join(lines)

    def save_dashboard(self) -> Path:
        """Generate and save dashboard"""
        content = self.generate_dashboard()

        with open(self.dashboard_file, "w") as f:
            f.write(content)

        return self.dashboard_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mission control dashboard")
    parser.add_argument("--force", action="store_true", help="Force regeneration")
    args = parser.parse_args()

    # Get mission control directory
    mission_control_dir = Path(__file__).parent.parent

    generator = DashboardGenerator(mission_control_dir)

    print("📊 Generating dashboard...")

    dashboard_file = generator.save_dashboard()

    print(f"✅ Dashboard saved: {dashboard_file}")
    print(f"\nView dashboard:")
    print(f"  cat {dashboard_file}")


if __name__ == "__main__":
    main()
