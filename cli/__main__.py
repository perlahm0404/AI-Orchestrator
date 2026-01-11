"""
AI Brain CLI Entry Point

Usage:
    python -m cli status
    python -m cli approve TASK-123
    python -m cli wiggum "Fix bug" --agent bugfix --project karematch

Or via installed command:
    aibrain status
    aibrain wiggum "Fix bug" --agent bugfix --project karematch
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import command modules
from cli.commands import wiggum, ko, discover, tasks, adr, pm_report, oversight_setup


def create_parser():
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog='aibrain',
        description='AI Orchestrator - Autonomous agent management'
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Command to run'
    )

    # Register wiggum command
    wiggum.setup_parser(subparsers)

    # Register ko command
    ko.setup_parser(subparsers)

    # Register discover-bugs command
    discover.setup_parser(subparsers)

    # Register tasks command (ADR-003)
    tasks.setup_parser(subparsers)

    # Register adr command (Phase 4 - ADR Automation)
    adr.setup_parser(subparsers)

    # Register pm command (PM Coordination & Reporting - v6.1)
    pm_report.setup_parser(subparsers)

    # Register oversight command (Phase 2B - Strategic Oversight)
    oversight_setup.setup_parser(subparsers)

    # Placeholder commands (to be implemented)
    status_parser = subparsers.add_parser('status', help='Show system or task status')
    status_parser.add_argument('task_id', nargs='?', help='Task ID to check')
    status_parser.set_defaults(func=lambda args: print("Status command not yet implemented"))

    approve_parser = subparsers.add_parser('approve', help='Approve a fix')
    approve_parser.add_argument('task_id', help='Task ID to approve')
    approve_parser.set_defaults(func=lambda args: print("Approve command not yet implemented"))

    reject_parser = subparsers.add_parser('reject', help='Reject a fix')
    reject_parser.add_argument('task_id', help='Task ID to reject')
    reject_parser.add_argument('reason', help='Rejection reason')
    reject_parser.set_defaults(func=lambda args: print("Reject command not yet implemented"))

    # Emergency controls
    emergency_parser = subparsers.add_parser('emergency-stop', help='Stop all operations')
    emergency_parser.set_defaults(func=lambda args: print("Emergency stop command not yet implemented"))

    pause_parser = subparsers.add_parser('pause', help='Pause new work')
    pause_parser.set_defaults(func=lambda args: print("Pause command not yet implemented"))

    resume_parser = subparsers.add_parser('resume', help='Resume operations')
    resume_parser.set_defaults(func=lambda args: print("Resume command not yet implemented"))

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()

    # Show help if no command provided
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if hasattr(args, 'func'):
        try:
            exit_code = args.func(args)
            sys.exit(exit_code if exit_code is not None else 0)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
