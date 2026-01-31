"""
CLI commands for metrics dashboard.

Usage:
    aibrain metrics show --project karematch      # Show dashboard
    aibrain metrics export --project karematch    # Export as JSON
    aibrain metrics export --project karematch --format prometheus  # Prometheus format
"""

import argparse
import sys
from pathlib import Path
from typing import Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from monitoring.metrics import MetricsCollector, generate_dashboard


def get_metrics_dir(project: str) -> Path:
    """Get metrics directory for a project."""
    if project == "karematch":
        return Path("/Users/tmac/1_REPOS/karematch/.metrics")
    elif project == "credentialmate":
        return Path("/Users/tmac/1_REPOS/credentialmate/.metrics")
    else:
        # Default to AI_Orchestrator metrics
        return Path(__file__).parent.parent.parent / ".metrics"


def metrics_show_command(args: Any) -> int:
    """Show metrics dashboard."""
    project = args.project

    metrics_dir = get_metrics_dir(project)
    if not metrics_dir.exists():
        print(f"\n📊 No metrics data found for {project}")
        print(f"   Metrics directory: {metrics_dir}")
        print(f"\n   Run autonomous loop or parallel execution first to collect metrics.")
        return 0

    collector = MetricsCollector(storage_dir=metrics_dir)
    dashboard = generate_dashboard(collector)

    print(f"\n{'='*60}")
    print(f"📊 METRICS DASHBOARD: {project.upper()}")
    print(f"{'='*60}\n")

    # Task Statistics
    print("📈 TASK STATISTICS")
    print(f"   ┌{'─'*40}┐")
    print(f"   │ {'Total Tasks:':<25} {dashboard.total_tasks:>12} │")
    print(f"   │ {'Completed:':<25} {dashboard.completed_tasks:>12} │")
    print(f"   │ {'Failed:':<25} {dashboard.failed_tasks:>12} │")
    print(f"   │ {'Success Rate:':<25} {dashboard.success_rate:>11.1%} │")
    print(f"   │ {'Avg Duration:':<25} {dashboard.avg_task_duration_ms:>9}ms │")
    print(f"   └{'─'*40}┘")
    print()

    # Agent Utilization
    print("🤖 AGENT UTILIZATION")
    utilization_bar = "█" * int(dashboard.agent_utilization * 20) + "░" * (20 - int(dashboard.agent_utilization * 20))
    print(f"   [{utilization_bar}] {dashboard.agent_utilization:.1%}")
    print()

    # Error Breakdown
    if dashboard.error_breakdown:
        print("❌ ERROR BREAKDOWN")
        total_errors = sum(dashboard.error_breakdown.values())
        for error_type, count in sorted(dashboard.error_breakdown.items(), key=lambda x: -x[1]):
            pct = count / total_errors * 100 if total_errors > 0 else 0
            bar = "█" * int(pct / 5)
            print(f"   {error_type:<15} {count:>4} ({pct:>5.1f}%) {bar}")
    else:
        print("✅ NO ERRORS RECORDED")
    print()

    print(f"{'='*60}\n")

    return 0


def metrics_export_command(args: Any) -> int:
    """Export metrics in various formats."""
    project = args.project
    format_type = args.format
    output_file = args.output

    metrics_dir = get_metrics_dir(project)
    if not metrics_dir.exists():
        print(f"\n❌ No metrics data found for {project}")
        return 1

    collector = MetricsCollector(storage_dir=metrics_dir)

    if format_type == "json":
        data = collector.export_json()
    elif format_type == "prometheus":
        data = collector.export_prometheus()
    else:
        print(f"\n❌ Unknown format: {format_type}")
        return 1

    if output_file:
        Path(output_file).write_text(data)
        print(f"\n✅ Metrics exported to: {output_file}")
    else:
        print(data)

    return 0


def metrics_clear_command(args: Any) -> int:
    """Clear metrics data."""
    project = args.project
    force = args.force

    metrics_dir = get_metrics_dir(project)
    if not metrics_dir.exists():
        print(f"\n✅ No metrics data to clear for {project}")
        return 0

    if not force:
        print(f"\n⚠️  This will delete all metrics data for {project}")
        response = input("   Continue? [y/N]: ")
        if response.lower() != 'y':
            print("   Cancelled.")
            return 0

    # Remove metrics files
    for file in metrics_dir.glob("*"):
        file.unlink()

    print(f"\n✅ Cleared metrics data for {project}")
    return 0


def setup_parser(subparsers: Any) -> None:
    """Set up the metrics command parser."""
    metrics_parser = subparsers.add_parser(
        "metrics",
        help="Metrics dashboard",
        description="View and export execution metrics"
    )

    metrics_subparsers = metrics_parser.add_subparsers(dest="metrics_command")

    # Show command
    show_parser = metrics_subparsers.add_parser(
        "show",
        help="Show metrics dashboard"
    )
    show_parser.add_argument(
        "--project",
        required=True,
        choices=["karematch", "credentialmate", "orchestrator"],
        help="Project to show metrics for"
    )
    show_parser.set_defaults(func=metrics_show_command)

    # Export command
    export_parser = metrics_subparsers.add_parser(
        "export",
        help="Export metrics"
    )
    export_parser.add_argument(
        "--project",
        required=True,
        choices=["karematch", "credentialmate", "orchestrator"],
        help="Project to export metrics for"
    )
    export_parser.add_argument(
        "--format",
        choices=["json", "prometheus"],
        default="json",
        help="Export format (default: json)"
    )
    export_parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    export_parser.set_defaults(func=metrics_export_command)

    # Clear command
    clear_parser = metrics_subparsers.add_parser(
        "clear",
        help="Clear metrics data"
    )
    clear_parser.add_argument(
        "--project",
        required=True,
        choices=["karematch", "credentialmate", "orchestrator"],
        help="Project to clear metrics for"
    )
    clear_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt"
    )
    clear_parser.set_defaults(func=metrics_clear_command)


def main() -> int:
    """Main entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Metrics dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show dashboard")
    show_parser.add_argument("--project", required=True, choices=["karematch", "credentialmate", "orchestrator"])
    show_parser.set_defaults(func=metrics_show_command)

    # Export command
    export_parser = subparsers.add_parser("export", help="Export metrics")
    export_parser.add_argument("--project", required=True, choices=["karematch", "credentialmate", "orchestrator"])
    export_parser.add_argument("--format", choices=["json", "prometheus"], default="json")
    export_parser.add_argument("--output", "-o")
    export_parser.set_defaults(func=metrics_export_command)

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear metrics")
    clear_parser.add_argument("--project", required=True, choices=["karematch", "credentialmate", "orchestrator"])
    clear_parser.add_argument("--force", "-f", action="store_true")
    clear_parser.set_defaults(func=metrics_clear_command)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return 1

    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
