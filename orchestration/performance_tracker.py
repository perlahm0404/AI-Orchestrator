#!/usr/bin/env python3
"""
Agent Performance Tracker - Records and analyzes agent task performance

Tracks agent performance across all executions, including parallel workers.
Uses append-only JSONL format for durability.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AgentPerformanceRecord:
    """Single performance record for an agent task execution"""
    agent_id: str                   # Agent type (bugfix, featurebuilder, etc.)
    task_id: str                    # Task identifier
    started_at: str                 # ISO timestamp
    completed_at: str               # ISO timestamp
    status: str                     # "success" | "blocked" | "failed"
    iterations: int                 # Number of iterations taken
    ralph_verdict: Optional[str]    # "PASS" | "FAIL" | "BLOCKED" | None
    escalated: bool                 # Whether task was escalated
    escalation_reason: Optional[str]
    worker_id: Optional[str]        # Worker ID for parallel execution
    duration_seconds: float         # Total execution time
    error_message: Optional[str]    # Error if failed


class AgentPerformanceTracker:
    """Tracks and analyzes agent performance"""

    def __init__(self, governance_dir: Optional[Path] = None):
        """
        Initialize performance tracker

        Args:
            governance_dir: Path to governance directory (default: ./governance)
        """
        if governance_dir:
            self.governance_dir = governance_dir
        else:
            self.governance_dir = Path.cwd() / "governance"

        self.metrics_dir = self.governance_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self.performance_file = self.metrics_dir / "agent_performance.jsonl"

    def record_task_completion(
        self,
        agent_id: str,
        task: Dict,
        result: Dict,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        escalated: bool = False,
        escalation_reason: Optional[str] = None,
        worker_id: Optional[str] = None
    ):
        """
        Record a completed task execution

        Args:
            agent_id: Agent type that executed the task
            task: Task data
            result: Execution result
            started_at: Task start time
            completed_at: Task completion time (default: now)
            escalated: Whether task was escalated
            escalation_reason: Reason for escalation if escalated
            worker_id: Worker ID for parallel execution
        """
        completed_at = completed_at or datetime.now()

        # Calculate duration
        duration = (completed_at - started_at).total_seconds()

        # Create record
        record = AgentPerformanceRecord(
            agent_id=agent_id,
            task_id=task.get("id", "unknown"),
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            status=result.get("status", "unknown"),
            iterations=result.get("iterations", 0),
            ralph_verdict=result.get("ralph_verdict"),
            escalated=escalated,
            escalation_reason=escalation_reason,
            worker_id=worker_id,
            duration_seconds=duration,
            error_message=result.get("error")
        )

        # Append to JSONL file
        self._append_record(record)

    def _append_record(self, record: AgentPerformanceRecord):
        """Append record to JSONL file"""
        with open(self.performance_file, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")

    def load_records(
        self,
        agent_id: Optional[str] = None,
        days: Optional[int] = None
    ) -> List[AgentPerformanceRecord]:
        """
        Load performance records

        Args:
            agent_id: Filter by agent ID (None = all agents)
            days: Filter to last N days (None = all time)

        Returns:
            List of performance records
        """
        if not self.performance_file.exists():
            return []

        records = []
        cutoff_date = None

        if days:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

        with open(self.performance_file) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    record = AgentPerformanceRecord(**data)

                    # Filter by agent
                    if agent_id and record.agent_id != agent_id:
                        continue

                    # Filter by date
                    if cutoff_date:
                        record_date = datetime.fromisoformat(record.completed_at.replace("Z", "+00:00"))
                        if record_date < cutoff_date:
                            continue

                    records.append(record)
                except Exception as e:
                    # Skip malformed lines
                    continue

        return records

    def get_agent_stats(
        self,
        agent_id: str,
        days: int = 30
    ) -> Dict:
        """
        Get statistics for a specific agent

        Args:
            agent_id: Agent to analyze
            days: Number of days to analyze

        Returns:
            Dict with agent statistics
        """
        records = self.load_records(agent_id=agent_id, days=days)

        if not records:
            return {
                "agent_id": agent_id,
                "total_tasks": 0,
                "success_rate": 0.0,
                "avg_iterations": 0.0,
                "escalation_rate": 0.0,
                "avg_duration_seconds": 0.0
            }

        total = len(records)
        successes = sum(1 for r in records if r.status == "success")
        escalations = sum(1 for r in records if r.escalated)
        iterations = [r.iterations for r in records]
        durations = [r.duration_seconds for r in records]

        return {
            "agent_id": agent_id,
            "total_tasks": total,
            "success_count": successes,
            "success_rate": (successes / total * 100) if total > 0 else 0.0,
            "avg_iterations": sum(iterations) / len(iterations) if iterations else 0.0,
            "max_iterations": max(iterations) if iterations else 0,
            "escalation_count": escalations,
            "escalation_rate": (escalations / total * 100) if total > 0 else 0.0,
            "avg_duration_seconds": sum(durations) / len(durations) if durations else 0.0,
            "total_duration_seconds": sum(durations),
            "period_days": days
        }

    def get_all_agents_stats(self, days: int = 30) -> List[Dict]:
        """Get statistics for all agents"""
        records = self.load_records(days=days)

        # Get unique agent IDs
        agent_ids = set(r.agent_id for r in records)

        # Get stats for each
        return [
            self.get_agent_stats(agent_id, days)
            for agent_id in sorted(agent_ids)
        ]

    def get_comparative_report(self, days: int = 30) -> Dict:
        """
        Generate comparative report across all agents

        Args:
            days: Number of days to analyze

        Returns:
            Comparative report with rankings
        """
        all_stats = self.get_all_agents_stats(days)

        if not all_stats:
            return {
                "period_days": days,
                "total_agents": 0,
                "agents": [],
                "rankings": {}
            }

        # Sort by different metrics
        by_success_rate = sorted(all_stats, key=lambda x: x["success_rate"], reverse=True)
        by_total_tasks = sorted(all_stats, key=lambda x: x["total_tasks"], reverse=True)
        by_avg_iterations = sorted(all_stats, key=lambda x: x["avg_iterations"])

        return {
            "period_days": days,
            "total_agents": len(all_stats),
            "total_tasks": sum(s["total_tasks"] for s in all_stats),
            "agents": all_stats,
            "rankings": {
                "highest_success_rate": by_success_rate[0] if by_success_rate else None,
                "most_tasks_completed": by_total_tasks[0] if by_total_tasks else None,
                "most_efficient": by_avg_iterations[0] if by_avg_iterations else None
            }
        }

    def get_recent_failures(self, limit: int = 10) -> List[AgentPerformanceRecord]:
        """Get recent failed tasks"""
        records = self.load_records()
        failures = [r for r in records if r.status in ["failed", "blocked"]]
        # Sort by completion time, most recent first
        failures.sort(key=lambda r: r.completed_at, reverse=True)
        return failures[:limit]

    def get_escalation_patterns(self, days: int = 30) -> Dict:
        """
        Analyze escalation patterns

        Args:
            days: Number of days to analyze

        Returns:
            Escalation pattern analysis
        """
        records = self.load_records(days=days)
        escalations = [r for r in records if r.escalated]

        # Count by reason
        reasons = {}
        for record in escalations:
            reason = record.escalation_reason or "unknown"
            reasons[reason] = reasons.get(reason, 0) + 1

        # Count by agent
        by_agent = {}
        for record in escalations:
            agent = record.agent_id
            by_agent[agent] = by_agent.get(agent, 0) + 1

        return {
            "total_escalations": len(escalations),
            "escalation_rate": (len(escalations) / len(records) * 100) if records else 0.0,
            "by_reason": dict(sorted(reasons.items(), key=lambda x: x[1], reverse=True)),
            "by_agent": dict(sorted(by_agent.items(), key=lambda x: x[1], reverse=True)),
            "period_days": days
        }

    def export_summary(self, output_path: Optional[Path] = None) -> str:
        """
        Export performance summary to JSON

        Args:
            output_path: Optional path to write file

        Returns:
            JSON string
        """
        summary = {
            "generated_at": datetime.now().isoformat(),
            "performance_file": str(self.performance_file),
            "total_records": len(self.load_records()),
            "comparative_report_30d": self.get_comparative_report(days=30),
            "comparative_report_7d": self.get_comparative_report(days=7),
            "escalation_patterns": self.get_escalation_patterns(days=30),
            "recent_failures": [asdict(r) for r in self.get_recent_failures(limit=5)]
        }

        json_str = json.dumps(summary, indent=2)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(json_str)

        return json_str


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent Performance Tracker")
    parser.add_argument("command", choices=["stats", "report", "failures", "escalations", "export"])
    parser.add_argument("--agent", "-a", help="Agent ID")
    parser.add_argument("--days", "-d", type=int, default=30, help="Number of days")
    parser.add_argument("--output", "-o", help="Output file path")
    args = parser.parse_args()

    tracker = AgentPerformanceTracker()

    if args.command == "stats":
        if args.agent:
            stats = tracker.get_agent_stats(args.agent, args.days)
            print(f"\n📊 Performance Stats: {args.agent} (last {args.days} days)")
            print("=" * 60)
            print(f"Total Tasks: {stats['total_tasks']}")
            print(f"Success Rate: {stats['success_rate']:.1f}%")
            print(f"Avg Iterations: {stats['avg_iterations']:.1f}")
            print(f"Escalation Rate: {stats['escalation_rate']:.1f}%")
            print(f"Avg Duration: {stats['avg_duration_seconds']:.1f}s")
        else:
            all_stats = tracker.get_all_agents_stats(args.days)
            print(f"\n📊 All Agents Performance (last {args.days} days)")
            print("=" * 60)
            for stats in all_stats:
                print(f"\n{stats['agent_id']}:")
                print(f"  Tasks: {stats['total_tasks']}, Success: {stats['success_rate']:.1f}%")
                print(f"  Avg Iterations: {stats['avg_iterations']:.1f}, Escalations: {stats['escalation_rate']:.1f}%")

    elif args.command == "report":
        report = tracker.get_comparative_report(args.days)
        print(f"\n📈 Comparative Report (last {args.days} days)")
        print("=" * 60)
        print(f"Total Agents: {report['total_agents']}")
        print(f"Total Tasks: {report['total_tasks']}")
        print("\n🏆 Rankings:")
        if report['rankings']['highest_success_rate']:
            top = report['rankings']['highest_success_rate']
            print(f"  Best Success Rate: {top['agent_id']} ({top['success_rate']:.1f}%)")
        if report['rankings']['most_efficient']:
            eff = report['rankings']['most_efficient']
            print(f"  Most Efficient: {eff['agent_id']} ({eff['avg_iterations']:.1f} avg iterations)")

    elif args.command == "failures":
        failures = tracker.get_recent_failures(limit=10)
        print(f"\n❌ Recent Failures ({len(failures)} shown)")
        print("=" * 60)
        for failure in failures:
            print(f"\n{failure.task_id} ({failure.agent_id})")
            print(f"  Status: {failure.status}")
            print(f"  Time: {failure.completed_at}")
            if failure.error_message:
                print(f"  Error: {failure.error_message}")

    elif args.command == "escalations":
        patterns = tracker.get_escalation_patterns(args.days)
        print(f"\n⬆️  Escalation Patterns (last {args.days} days)")
        print("=" * 60)
        print(f"Total Escalations: {patterns['total_escalations']}")
        print(f"Escalation Rate: {patterns['escalation_rate']:.1f}%")
        print("\nBy Reason:")
        for reason, count in patterns['by_reason'].items():
            print(f"  {reason}: {count}")
        print("\nBy Agent:")
        for agent, count in patterns['by_agent'].items():
            print(f"  {agent}: {count}")

    elif args.command == "export":
        output = Path(args.output) if args.output else None
        summary = tracker.export_summary(output)
        if output:
            print(f"✅ Exported to {output}")
        else:
            print(summary)
