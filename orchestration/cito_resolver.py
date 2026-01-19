#!/usr/bin/env python3
"""
CITO Resolver - CLI for resolving human escalations

Allows humans to respond to CITO escalations with approve/modify/block decisions.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class CITOResolver:
    """Resolves CITO escalations based on human decisions"""

    def __init__(self, project_dir: Optional[Path] = None):
        """
        Initialize CITO resolver

        Args:
            project_dir: Project root directory
        """
        self.project_dir = project_dir or Path.cwd()
        self.escalations_dir = self.project_dir / "escalations"
        self.resolutions_dir = self.escalations_dir / "resolutions"

        # Ensure directories exist
        self.escalations_dir.mkdir(parents=True, exist_ok=True)
        self.resolutions_dir.mkdir(parents=True, exist_ok=True)

    def list_escalations(self, status: Optional[str] = None) -> list:
        """
        List all escalations

        Args:
            status: Filter by status (pending, resolved, all)

        Returns:
            List of escalation files
        """
        if not self.escalations_dir.exists():
            return []

        escalations = []

        # Get all .md files in escalations directory
        for escalation_file in self.escalations_dir.glob("*.md"):
            # Skip if in resolutions subdirectory
            if self.resolutions_dir in escalation_file.parents:
                continue

            # Check if resolved
            resolution_file = self.resolutions_dir / f"{escalation_file.stem}.json"
            is_resolved = resolution_file.exists()

            if status == "pending" and is_resolved:
                continue
            if status == "resolved" and not is_resolved:
                continue

            escalations.append({
                "file": escalation_file,
                "task_id": escalation_file.stem.split("-")[0],
                "resolved": is_resolved,
                "created": datetime.fromtimestamp(escalation_file.stat().st_mtime)
            })

        # Sort by creation time, newest first
        escalations.sort(key=lambda x: x["created"], reverse=True)

        return escalations

    def get_escalation_details(self, task_id: str) -> Optional[Dict]:
        """
        Get details of a specific escalation

        Args:
            task_id: Task ID

        Returns:
            Escalation details or None
        """
        # Find escalation file for this task
        pattern = f"{task_id}-*.md"
        files = list(self.escalations_dir.glob(pattern))

        if not files:
            return None

        escalation_file = files[0]  # Get most recent if multiple
        resolution_file = self.resolutions_dir / f"{escalation_file.stem}.json"

        details = {
            "task_id": task_id,
            "file": escalation_file,
            "content": escalation_file.read_text(),
            "created": datetime.fromtimestamp(escalation_file.stat().st_mtime),
            "resolved": resolution_file.exists()
        }

        if resolution_file.exists():
            details["resolution"] = json.loads(resolution_file.read_text())

        return details

    def resolve_escalation(
        self,
        task_id: str,
        action: str,
        iterations: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Resolve an escalation with a human decision

        Args:
            task_id: Task ID to resolve
            action: Action to take (approve, modify, block)
            iterations: New iteration limit (for modify action)
            notes: Optional human notes

        Returns:
            Resolution details
        """
        # Validate action
        if action not in ["approve", "modify", "block"]:
            raise ValueError(f"Invalid action: {action}. Must be approve, modify, or block.")

        # Find escalation
        escalation = self.get_escalation_details(task_id)
        if not escalation:
            raise ValueError(f"No escalation found for task: {task_id}")

        if escalation["resolved"]:
            raise ValueError(f"Escalation already resolved for task: {task_id}")

        # Create resolution
        resolution = {
            "task_id": task_id,
            "action": action,
            "resolved_at": datetime.now().isoformat(),
            "resolved_by": "human",
            "notes": notes
        }

        # Add modifications if action is modify
        if action == "modify":
            modifications = {}
            if iterations:
                modifications["max_iterations"] = iterations
            resolution["modifications"] = modifications

        # Save resolution
        resolution_file = self.resolutions_dir / f"{escalation['file'].stem}.json"
        with open(resolution_file, "w") as f:
            json.dump(resolution, f, indent=2)

        return resolution

    def get_pending_count(self) -> int:
        """Get count of pending escalations"""
        return len(self.list_escalations(status="pending"))

    def get_resolution_summary(self, days: int = 30) -> Dict:
        """
        Get summary of resolutions

        Args:
            days: Number of days to analyze

        Returns:
            Resolution summary
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)

        resolutions = []
        for resolution_file in self.resolutions_dir.glob("*.json"):
            try:
                with open(resolution_file) as f:
                    resolution = json.load(f)

                resolved_at = datetime.fromisoformat(resolution["resolved_at"])
                if resolved_at >= cutoff:
                    resolutions.append(resolution)
            except Exception:
                continue

        # Count by action
        actions = {}
        for resolution in resolutions:
            action = resolution["action"]
            actions[action] = actions.get(action, 0) + 1

        return {
            "total_resolutions": len(resolutions),
            "period_days": days,
            "by_action": actions,
            "avg_per_day": len(resolutions) / days if days > 0 else 0
        }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CITO Resolver - Resolve human escalations"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List escalations")
    list_parser.add_argument(
        "--status",
        choices=["all", "pending", "resolved"],
        default="pending",
        help="Filter by status"
    )

    # Show command
    show_parser = subparsers.add_parser("show", help="Show escalation details")
    show_parser.add_argument("task_id", help="Task ID to show")

    # Resolve command
    resolve_parser = subparsers.add_parser("resolve", help="Resolve an escalation")
    resolve_parser.add_argument("task_id", help="Task ID to resolve")
    resolve_parser.add_argument(
        "--action",
        required=True,
        choices=["approve", "modify", "block"],
        help="Action to take"
    )
    resolve_parser.add_argument(
        "--iterations",
        type=int,
        help="New iteration limit (for modify action)"
    )
    resolve_parser.add_argument(
        "--notes",
        help="Human notes about the decision"
    )

    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show resolution summary")
    summary_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze"
    )

    args = parser.parse_args()

    resolver = CITOResolver()

    if args.command == "list":
        escalations = resolver.list_escalations(
            status=args.status if args.status != "all" else None
        )

        if not escalations:
            print(f"No {args.status} escalations found")
            return

        print(f"\n🚨 {args.status.upper()} Escalations ({len(escalations)})\n")
        print(f"{'Task ID':<20} {'Created':<25} {'Status':<10}")
        print("=" * 60)

        for esc in escalations:
            status = "✅ Resolved" if esc["resolved"] else "⏳ Pending"
            created = esc["created"].strftime("%Y-%m-%d %H:%M:%S")
            print(f"{esc['task_id']:<20} {created:<25} {status:<10}")

    elif args.command == "show":
        details = resolver.get_escalation_details(args.task_id)

        if not details:
            print(f"❌ No escalation found for task: {args.task_id}")
            return

        print(f"\n📄 Escalation Details: {args.task_id}\n")
        print("=" * 60)
        print(f"File: {details['file']}")
        print(f"Created: {details['created'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Resolved: {'Yes' if details['resolved'] else 'No'}")
        print("\n" + "=" * 60 + "\n")
        print(details['content'])

        if details['resolved']:
            print("\n" + "=" * 60)
            print("RESOLUTION:")
            print(json.dumps(details['resolution'], indent=2))

    elif args.command == "resolve":
        try:
            resolution = resolver.resolve_escalation(
                args.task_id,
                args.action,
                iterations=args.iterations,
                notes=args.notes
            )

            print(f"\n✅ Escalation Resolved: {args.task_id}\n")
            print("=" * 60)
            print(f"Action: {resolution['action'].upper()}")
            if resolution.get('modifications'):
                print(f"Modifications: {resolution['modifications']}")
            if resolution.get('notes'):
                print(f"Notes: {resolution['notes']}")
            print(f"Resolved At: {resolution['resolved_at']}")

        except ValueError as e:
            print(f"❌ Error: {e}")

    elif args.command == "summary":
        summary = resolver.get_resolution_summary(args.days)

        print(f"\n📊 Resolution Summary (last {args.days} days)\n")
        print("=" * 60)
        print(f"Total Resolutions: {summary['total_resolutions']}")
        print(f"Avg Per Day: {summary['avg_per_day']:.1f}")
        print("\nBy Action:")
        for action, count in summary['by_action'].items():
            pct = (count / summary['total_resolutions'] * 100) if summary['total_resolutions'] > 0 else 0
            print(f"  {action}: {count} ({pct:.1f}%)")

        # Show pending count
        pending = resolver.get_pending_count()
        print(f"\n⏳ Pending: {pending}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
