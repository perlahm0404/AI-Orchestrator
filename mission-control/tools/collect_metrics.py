#!/usr/bin/env python3
"""
Metrics Collection Tool - Gathers performance metrics from agents and repos

Usage:
    python mission-control/tools/collect_metrics.py
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class AgentMetrics:
    """Metrics for a single agent"""
    agent_id: str
    agent_type: str
    total_tasks: int
    success_count: int
    blocked_count: int
    failed_count: int
    success_rate: float
    avg_iterations: float
    escalation_count: int
    escalation_rate: float
    last_active: Optional[str]


@dataclass
class RepoMetrics:
    """Metrics for a single repo"""
    repo_name: str
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    completed_tasks: int
    autonomy_pct: float
    human_interventions: int
    avg_completion_time_hours: Optional[float]
    last_updated: str


class MetricsCollector:
    """Collects metrics from agents and repos"""

    def __init__(self, ai_orchestrator_root: Path):
        self.root = ai_orchestrator_root
        self.mission_control = self.root / "mission-control"
        self.metrics_dir = self.mission_control / "metrics"
        self.work_queues_dir = self.mission_control / "work-queues"

        # Ensure directories exist
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # Agent performance tracking file
        self.agent_perf_file = self.root / "governance" / "metrics" / "agent_performance.jsonl"

    def collect_agent_metrics(self, window_days: int = 30) -> List[AgentMetrics]:
        """Collect agent performance metrics"""
        metrics_by_agent = {}
        cutoff_date = datetime.now() - timedelta(days=window_days)

        # Load agent performance records
        if self.agent_perf_file.exists():
            try:
                with open(self.agent_perf_file) as f:
                    for line in f:
                        try:
                            record = json.loads(line.strip())
                            agent_id = record.get("agent_id", "unknown")

                            # Filter by date
                            completed_at = record.get("completed_at")
                            if completed_at:
                                record_date = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                                if record_date < cutoff_date:
                                    continue

                            # Initialize agent metrics
                            if agent_id not in metrics_by_agent:
                                metrics_by_agent[agent_id] = {
                                    "agent_id": agent_id,
                                    "agent_type": record.get("agent_type", agent_id),
                                    "total_tasks": 0,
                                    "success_count": 0,
                                    "blocked_count": 0,
                                    "failed_count": 0,
                                    "iterations": [],
                                    "escalations": 0,
                                    "last_active": completed_at
                                }

                            agent_data = metrics_by_agent[agent_id]
                            agent_data["total_tasks"] += 1

                            # Count by status
                            status = record.get("status", "unknown")
                            if status == "success":
                                agent_data["success_count"] += 1
                            elif status == "blocked":
                                agent_data["blocked_count"] += 1
                            else:
                                agent_data["failed_count"] += 1

                            # Track iterations
                            iterations = record.get("iterations", 0)
                            agent_data["iterations"].append(iterations)

                            # Track escalations
                            if record.get("escalated", False):
                                agent_data["escalations"] += 1

                            # Update last active
                            if completed_at and (not agent_data["last_active"] or completed_at > agent_data["last_active"]):
                                agent_data["last_active"] = completed_at

                        except Exception as e:
                            print(f"Warning: Failed to parse agent record: {e}")
                            continue
            except Exception as e:
                print(f"Warning: Failed to read agent performance file: {e}")

        # Calculate aggregate metrics
        agent_metrics = []
        for agent_id, data in metrics_by_agent.items():
            total = data["total_tasks"]
            success_rate = (data["success_count"] / total * 100) if total > 0 else 0.0

            iterations = data["iterations"]
            avg_iterations = sum(iterations) / len(iterations) if iterations else 0.0

            escalation_rate = (data["escalations"] / total * 100) if total > 0 else 0.0

            metrics = AgentMetrics(
                agent_id=agent_id,
                agent_type=data["agent_type"],
                total_tasks=total,
                success_count=data["success_count"],
                blocked_count=data["blocked_count"],
                failed_count=data["failed_count"],
                success_rate=success_rate,
                avg_iterations=avg_iterations,
                escalation_count=data["escalations"],
                escalation_rate=escalation_rate,
                last_active=data["last_active"]
            )
            agent_metrics.append(metrics)

        return agent_metrics

    def collect_repo_metrics(self) -> List[RepoMetrics]:
        """Collect repo-level metrics from work queues"""
        repo_metrics = []

        # Check for aggregate view first
        aggregate_file = self.work_queues_dir / "aggregate-view.json"
        if not aggregate_file.exists():
            print("Warning: aggregate-view.json not found, run sync_work_queues.py first")
            return []

        try:
            with open(aggregate_file) as f:
                aggregate = json.load(f)

            last_sync = aggregate.get("last_sync", datetime.now().isoformat())

            for repo_name, stats in aggregate.get("repos", {}).items():
                total = stats.get("total", 0)
                pending = stats.get("pending", 0)
                in_progress = stats.get("in_progress", 0)
                blocked = stats.get("blocked", 0)
                completed = stats.get("completed", 0)

                # Calculate autonomy percentage
                # Autonomy = tasks completed without human intervention
                # For now, assume all completed tasks were autonomous (will enhance later)
                autonomy_pct = (completed / total * 100) if total > 0 else 0.0

                # Human interventions (from blocked tasks requiring decisions)
                human_interventions = blocked

                metrics = RepoMetrics(
                    repo_name=repo_name,
                    total_tasks=total,
                    pending_tasks=pending,
                    in_progress_tasks=in_progress,
                    blocked_tasks=blocked,
                    completed_tasks=completed,
                    autonomy_pct=autonomy_pct,
                    human_interventions=human_interventions,
                    avg_completion_time_hours=None,  # TODO: Track task timestamps
                    last_updated=last_sync
                )
                repo_metrics.append(metrics)

        except Exception as e:
            print(f"Warning: Failed to collect repo metrics: {e}")

        return repo_metrics

    def collect_autonomy_trends(self, window_days: int = 30) -> dict[str, Any]:
        """Collect autonomy trends over time"""
        # For now, return current snapshot
        # TODO: Implement time-series tracking with hourly snapshots

        repo_metrics = self.collect_repo_metrics()

        trends = {
            "last_updated": datetime.now().isoformat(),
            "window_days": window_days,
            "current_autonomy": {},
            "trend_7_day": {},
            "trend_30_day": {}
        }

        for repo in repo_metrics:
            trends["current_autonomy"][repo.repo_name] = repo.autonomy_pct
            # Placeholder for historical data
            trends["trend_7_day"][repo.repo_name] = repo.autonomy_pct
            trends["trend_30_day"][repo.repo_name] = repo.autonomy_pct

        return trends

    def save_metrics(self, agent_metrics: List[AgentMetrics], repo_metrics: List[RepoMetrics], autonomy_trends: Dict):
        """Save collected metrics to files"""

        # Save agent performance
        agent_perf_file = self.metrics_dir / "agent-performance.json"
        with open(agent_perf_file, "w") as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "agents": [asdict(m) for m in agent_metrics]
            }, f, indent=2)

        # Save repo performance
        repo_perf_file = self.metrics_dir / "repo-performance.json"
        with open(repo_perf_file, "w") as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "repos": [asdict(m) for m in repo_metrics]
            }, f, indent=2)

        # Save autonomy trends
        autonomy_file = self.metrics_dir / "autonomy-trends.json"
        with open(autonomy_file, "w") as f:
            json.dump(autonomy_trends, f, indent=2)

        return agent_perf_file, repo_perf_file, autonomy_file

    def generate_performance_summary(self, agent_metrics: List[AgentMetrics], repo_metrics: List[RepoMetrics]) -> str:
        """Generate text summary of performance"""
        lines = []
        lines.append("# Performance Summary")
        lines.append(f"Generated: {datetime.now().isoformat()}\n")

        # Agent performance
        if agent_metrics:
            lines.append("## Agent Performance\n")
            lines.append("| Agent | Tasks | Success Rate | Avg Iterations | Escalations |")
            lines.append("|---|---|---|---|---|")

            for agent in sorted(agent_metrics, key=lambda a: a.success_rate, reverse=True):
                status_icon = "🟢" if agent.success_rate >= 85 else "🟡" if agent.success_rate >= 70 else "🔴"
                lines.append(
                    f"| {status_icon} {agent.agent_type} | {agent.total_tasks} | "
                    f"{agent.success_rate:.1f}% | {agent.avg_iterations:.1f} | "
                    f"{agent.escalation_count} ({agent.escalation_rate:.1f}%) |"
                )
            lines.append("")

        # Repo performance
        if repo_metrics:
            lines.append("## Repo Performance\n")
            lines.append("| Repo | Tasks | Completed | Autonomy | Blocked |")
            lines.append("|---|---|---|---|---|")

            for repo in sorted(repo_metrics, key=lambda r: r.autonomy_pct, reverse=True):
                status_icon = "🟢" if repo.autonomy_pct >= 85 else "🟡" if repo.autonomy_pct >= 70 else "🔴"
                lines.append(
                    f"| {status_icon} {repo.repo_name} | {repo.total_tasks} | "
                    f"{repo.completed_tasks} | {repo.autonomy_pct:.1f}% | {repo.blocked_tasks} |"
                )
            lines.append("")

        return "\n".join(lines)


def main():
    # Get AI_Orchestrator root
    ai_orch_root = Path(__file__).parent.parent.parent

    collector = MetricsCollector(ai_orch_root)

    print("📊 Collecting metrics...")

    # Collect metrics
    agent_metrics = collector.collect_agent_metrics(window_days=30)
    repo_metrics = collector.collect_repo_metrics()
    autonomy_trends = collector.collect_autonomy_trends(window_days=30)

    # Save metrics
    agent_file, repo_file, autonomy_file = collector.save_metrics(
        agent_metrics, repo_metrics, autonomy_trends
    )

    print(f"✅ Saved agent metrics: {agent_file}")
    print(f"✅ Saved repo metrics: {repo_file}")
    print(f"✅ Saved autonomy trends: {autonomy_file}")

    # Print summary
    print(f"\n{collector.generate_performance_summary(agent_metrics, repo_metrics)}")


if __name__ == "__main__":
    main()
