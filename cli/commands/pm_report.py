"""
PM Report Command - Generate product manager status reports

Usage:
    aibrain pm report --project credentialmate         # Generate report for project
    aibrain pm report --project credentialmate --save  # Save to work/reports/

Generates comprehensive PM status reports with:
- Task summary (pending, in-progress, complete, blocked)
- ADR rollup with progress tracking
- Evidence coverage metrics
- Blockers requiring attention

Outputs in 3 formats:
- Markdown (human-readable with emojis)
- Grid (plain ASCII tables, parseable)
- JSON (machine-readable)
"""

import argparse
import sys
from pathlib import Path
from typing import Any, cast

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.pm_reporting import ReportGenerator


def pm_report_command(args: Any) -> int:
    """Generate PM status report for a project"""

    project = args.project

    print(f"\n📊 Generating PM status report for {project}...\n")

    # Initialize generator
    generator = ReportGenerator()

    try:
        # Generate report
        report_data = generator.generate_report(project)

        # Display markdown to console
        from orchestration.pm_reporting import ReportFormatter
        formatter = ReportFormatter()
        markdown_output = formatter.format_markdown(report_data)

        print(markdown_output)

        # Save if requested
        if args.save:
            print("\n💾 Saving reports in all 3 formats...")
            paths = generator.generate_and_save(project)

            print(f"\n✅ Reports saved:")
            print(f"   📄 Markdown: {paths['markdown']}")
            print(f"   📊 Grid:     {paths['grid']}")
            print(f"   📋 JSON:     {paths['json']}")
            print()

        return 0

    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1


def setup_parser(subparsers: Any) -> None:
    """Setup PM report command parser"""

    # Main pm group
    pm_parser = subparsers.add_parser(
        'pm',
        help='Product Manager commands'
    )

    pm_subparsers = pm_parser.add_subparsers(
        dest='pm_command',
        help='PM subcommand to run'
    )

    # Report command
    report_parser = pm_subparsers.add_parser(
        'report',
        help='Generate PM status report'
    )

    report_parser.add_argument(
        '--project',
        required=True,
        help='Project name (credentialmate, karematch, orchestrator)'
    )

    report_parser.add_argument(
        '--save',
        action='store_true',
        help='Save report to work/reports/ (markdown + grid + JSON)'
    )

    report_parser.set_defaults(func=pm_report_command)


def main() -> int:
    """Standalone entry point for testing"""
    parser = argparse.ArgumentParser(description='PM Report Generator')
    subparsers = parser.add_subparsers(dest='command')
    setup_parser(subparsers)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        return cast(int, args.func(args))
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
