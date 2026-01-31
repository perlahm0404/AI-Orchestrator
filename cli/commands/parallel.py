"""
CLI commands for parallel agent execution.

Usage:
    aibrain parallel run --project karematch               # Run parallel agents
    aibrain parallel run --project karematch --max-agents 5  # With 5 agents
    aibrain parallel status                                # Show parallel execution status
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tasks.work_queue import WorkQueue
from orchestration.parallel_executor import (
    ParallelExecutor,
    ExecutorConfig,
    CoordinationStrategy,
)
from monitoring.metrics import MetricsCollector, generate_dashboard


def parallel_run_command(args: Any) -> int:
    """Run parallel agent execution."""
    project = args.project
    max_agents = args.max_agents
    strategy = args.strategy

    # Get project directory from adapters
    if project == "karematch":
        project_dir = Path("/Users/tmac/1_REPOS/karematch")
    elif project == "credentialmate":
        project_dir = Path("/Users/tmac/1_REPOS/credentialmate")
    else:
        print(f"\n❌ Unknown project: {project}")
        return 1

    # Load work queue
    queue_path = Path(__file__).parent.parent.parent / "tasks" / f"work_queue_{project}.json"
    if not queue_path.exists():
        print(f"\n❌ No work queue found: {queue_path}")
        return 1

    queue = WorkQueue.load(queue_path)
    pending_tasks = [t for t in queue.features if t.status == "pending"]

    if not pending_tasks:
        print("\n✅ No pending tasks to execute")
        return 0

    print(f"\n{'='*60}")
    print(f"🚀 PARALLEL AGENT EXECUTION")
    print(f"{'='*60}")
    print(f"Project: {project}")
    print(f"Directory: {project_dir}")
    print(f"Max agents: {max_agents}")
    print(f"Strategy: {strategy}")
    print(f"Pending tasks: {len(pending_tasks)}")
    print(f"{'='*60}\n")

    # Create executor config
    strategy_map = {
        "independent": CoordinationStrategy.INDEPENDENT,
        "file-lock": CoordinationStrategy.FILE_LOCK,
        "sequential": CoordinationStrategy.SEQUENTIAL_FALLBACK,
    }
    config = ExecutorConfig(
        max_parallel=max_agents,
        strategy=strategy_map.get(strategy, CoordinationStrategy.FILE_LOCK),
    )

    # Create executor and run
    executor = ParallelExecutor(project_dir=project_dir, config=config)

    print("🔄 Starting parallel execution...\n")

    try:
        result = asyncio.run(executor.execute(pending_tasks))

        print(f"\n{'='*60}")
        print(f"📊 RESULTS")
        print(f"{'='*60}")
        print(f"✅ Completed: {result.completed}")
        print(f"❌ Failed: {result.failed}")
        print(f"⏱️  Duration: {result.total_time_ms}ms")
        print(f"{'='*60}\n")

        return 0 if result.failed == 0 else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130


def parallel_status_command(args: Any) -> int:
    """Show parallel execution status and metrics."""
    project = args.project if hasattr(args, 'project') and args.project else "karematch"

    # Get project directory
    if project == "karematch":
        project_dir = Path("/Users/tmac/1_REPOS/karematch")
    else:
        project_dir = Path("/Users/tmac/1_REPOS/credentialmate")

    metrics_dir = project_dir / ".metrics"
    if not metrics_dir.exists():
        print(f"\n📊 No metrics data found for {project}")
        print(f"   Run 'aibrain parallel run' first to collect metrics")
        return 0

    collector = MetricsCollector(storage_dir=metrics_dir)
    dashboard = generate_dashboard(collector)

    print(f"\n{'='*60}")
    print(f"📊 PARALLEL EXECUTION METRICS")
    print(f"{'='*60}")
    print(f"Project: {project}")
    print(f"{'='*60}\n")

    print(f"📈 Task Statistics:")
    print(f"   Total tasks:      {dashboard.total_tasks}")
    print(f"   Completed:        {dashboard.completed_tasks}")
    print(f"   Failed:           {dashboard.failed_tasks}")
    print(f"   Success rate:     {dashboard.success_rate:.1%}")
    print(f"   Avg duration:     {dashboard.avg_task_duration_ms}ms")
    print()

    print(f"🤖 Agent Utilization: {dashboard.agent_utilization:.1%}")
    print()

    if dashboard.error_breakdown:
        print("❌ Error Breakdown:")
        for error_type, count in dashboard.error_breakdown.items():
            print(f"   {error_type}: {count}")
    print()

    return 0


def setup_parser(subparsers: Any) -> None:
    """Set up the parallel command parser."""
    parallel_parser = subparsers.add_parser(
        "parallel",
        help="Parallel agent execution",
        description="Run multiple agents in parallel with coordination"
    )

    parallel_subparsers = parallel_parser.add_subparsers(dest="parallel_command")

    # Run command
    run_parser = parallel_subparsers.add_parser(
        "run",
        help="Run parallel agent execution"
    )
    run_parser.add_argument(
        "--project",
        required=True,
        choices=["karematch", "credentialmate"],
        help="Project to run agents on"
    )
    run_parser.add_argument(
        "--max-agents",
        type=int,
        default=3,
        help="Maximum number of parallel agents (default: 3)"
    )
    run_parser.add_argument(
        "--strategy",
        choices=["independent", "file-lock", "sequential"],
        default="file-lock",
        help="Coordination strategy (default: file-lock)"
    )
    run_parser.set_defaults(func=parallel_run_command)

    # Status command
    status_parser = parallel_subparsers.add_parser(
        "status",
        help="Show parallel execution status and metrics"
    )
    status_parser.add_argument(
        "--project",
        choices=["karematch", "credentialmate"],
        default="karematch",
        help="Project to show status for (default: karematch)"
    )
    status_parser.set_defaults(func=parallel_status_command)


def main() -> int:
    """Main entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Parallel agent execution",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run parallel agents")
    run_parser.add_argument("--project", required=True, choices=["karematch", "credentialmate"])
    run_parser.add_argument("--max-agents", type=int, default=3)
    run_parser.add_argument("--strategy", choices=["independent", "file-lock", "sequential"], default="file-lock")
    run_parser.set_defaults(func=parallel_run_command)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show execution status")
    status_parser.add_argument("--project", choices=["karematch", "credentialmate"], default="karematch")
    status_parser.set_defaults(func=parallel_status_command)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return 1

    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
