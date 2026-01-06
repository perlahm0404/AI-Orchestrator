"""
AI Brain CLI Entry Point

Usage:
    python -m cli status
    python -m cli approve TASK-123
    python -m cli emergency-stop

Or via installed command:
    aibrain status
    aibrain approve TASK-123
"""

import sys


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: aibrain <command> [args]")
        print()
        print("Commands:")
        print("  status [TASK-ID]     Show system or task status")
        print("  approve TASK-ID      Approve a fix")
        print("  reject TASK-ID       Reject a fix")
        print("  ko approve KO-ID     Approve Knowledge Object")
        print("  ko pending           List pending KOs")
        print("  emergency-stop       Stop all operations")
        print("  pause                Pause new work")
        print("  resume               Resume operations")
        sys.exit(1)

    command = sys.argv[1]

    # TODO: Implement commands in Phase 1
    print(f"Command '{command}' not yet implemented")
    sys.exit(1)


if __name__ == "__main__":
    main()
