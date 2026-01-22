#!/usr/bin/env python3
"""
Issue Tracker - Centralized issue tracking across all repos

Usage:
    python mission-control/tools/issue_tracker.py list
    python mission-control/tools/issue_tracker.py create --title "..." --description "..." --priority P0
    python mission-control/tools/issue_tracker.py resolve ISS-2026-001 --resolution "..."
    python mission-control/tools/issue_tracker.py auto-detect
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Issue:
    """Represents an issue"""
    id: str
    title: str
    description: str
    priority: str  # P0, P1, P2
    status: str  # created, triaged, assigned, in_progress, resolved, closed
    created_at: str
    updated_at: str
    assigned_to: Optional[str]
    related_tasks: List[str]
    resolution: Optional[str]
    repo: Optional[str]
    issue_type: str  # blocked_task, escalation, governance_violation, manual


class IssueTracker:
    """Manages centralized issue tracking"""

    def __init__(self, mission_control_dir: Path):
        self.mission_control = mission_control_dir
        self.issues_dir = self.mission_control / "issues"
        self.work_queues_dir = self.mission_control / "work-queues"

        # Ensure directories exist
        self.issues_dir.mkdir(parents=True, exist_ok=True)

        self.issues_db_file = self.issues_dir / "issues-log.json"
        self.issues_md_file = self.issues_dir / "issues-log.md"

    def load_issues_db(self) -> dict[str, Any]:
        """Load issues database"""
        if not self.issues_db_file.exists():
            return {"issues": [], "next_id": 1}

        try:
            with open(self.issues_db_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except Exception as e:
            print(f"Warning: Failed to load issues DB: {e}")
            return {"issues": [], "next_id": 1}

    def save_issues_db(self, db: dict[str, Any]) -> None:
        """Save issues database"""
        with open(self.issues_db_file, "w") as f:
            json.dump(db, f, indent=2)

    def generate_issue_id(self, next_id: int) -> str:
        """Generate issue ID in format ISS-YYYY-NNN"""
        year = datetime.now().year
        return f"ISS-{year}-{next_id:03d}"

    def create_issue(
        self,
        title: str,
        description: str,
        priority: str = "P2",
        issue_type: str = "manual",
        repo: Optional[str] = None,
        related_tasks: Optional[List[str]] = None
    ) -> Issue:
        """Create a new issue"""
        db = self.load_issues_db()

        issue_id = self.generate_issue_id(db["next_id"])
        now = datetime.now().isoformat()

        issue = Issue(
            id=issue_id,
            title=title,
            description=description,
            priority=priority,
            status="created",
            created_at=now,
            updated_at=now,
            assigned_to=None,
            related_tasks=related_tasks or [],
            resolution=None,
            repo=repo,
            issue_type=issue_type
        )

        db["issues"].append(asdict(issue))
        db["next_id"] += 1

        self.save_issues_db(db)
        self.regenerate_markdown()

        return issue

    def update_issue(self, issue_id: str, **kwargs: Any) -> Optional[Issue]:
        """Update an existing issue"""
        db = self.load_issues_db()

        for issue_data in db["issues"]:
            if issue_data["id"] == issue_id:
                # Update fields
                for key, value in kwargs.items():
                    if key in issue_data:
                        issue_data[key] = value

                issue_data["updated_at"] = datetime.now().isoformat()

                self.save_issues_db(db)
                self.regenerate_markdown()

                return Issue(**issue_data)

        return None

    def resolve_issue(self, issue_id: str, resolution: str) -> Optional[Issue]:
        """Mark an issue as resolved"""
        return self.update_issue(
            issue_id,
            status="resolved",
            resolution=resolution
        )

    def close_issue(self, issue_id: str) -> Optional[Issue]:
        """Mark an issue as closed"""
        return self.update_issue(issue_id, status="closed")

    def list_issues(self, status: Optional[str] = None, priority: Optional[str] = None) -> List[Issue]:
        """List issues with optional filters"""
        db = self.load_issues_db()
        issues = []

        for issue_data in db["issues"]:
            if status and issue_data["status"] != status:
                continue
            if priority and issue_data["priority"] != priority:
                continue

            issues.append(Issue(**issue_data))

        return issues

    def auto_detect_issues(self) -> List[Issue]:
        """Auto-detect issues from work queues and alerts"""
        detected_issues: list[Issue] = []

        # Load aggregate view
        aggregate_file = self.work_queues_dir / "aggregate-view.json"
        if not aggregate_file.exists():
            print("Warning: aggregate-view.json not found")
            return detected_issues

        try:
            with open(aggregate_file) as f:
                aggregate = json.load(f)

            # Check for blocked tasks in alerts
            for alert in aggregate.get("alerts", []):
                if alert.get("type") == "blocked_task":
                    task_id = alert.get("task_id", "unknown")
                    repo = alert.get("repo", "unknown")
                    title = alert.get("title", "Unknown task")

                    # Check if issue already exists for this task
                    existing_issues = self.list_issues()
                    task_already_tracked = any(
                        task_id in issue.related_tasks
                        for issue in existing_issues
                        if issue.status not in ["resolved", "closed"]
                    )

                    if not task_already_tracked:
                        issue = self.create_issue(
                            title=f"Blocked Task: {title}",
                            description=f"Task `{task_id}` in `{repo}` has been blocked for >3 days",
                            priority="P1",
                            issue_type="blocked_task",
                            repo=repo,
                            related_tasks=[task_id]
                        )
                        detected_issues.append(issue)

        except Exception as e:
            print(f"Warning: Failed to auto-detect issues: {e}")

        return detected_issues

    def regenerate_markdown(self) -> None:
        """Regenerate issues-log.md from database"""
        db = self.load_issues_db()
        issues = [Issue(**i) for i in db["issues"]]

        with open(self.issues_md_file, "w") as f:
            f.write("# Issues Log\n\n")
            f.write(f"**Last Updated**: {datetime.now().isoformat()}\n\n")

            # Group by status
            statuses = ["created", "triaged", "assigned", "in_progress", "resolved", "closed"]

            for status in statuses:
                status_issues = [i for i in issues if i.status == status]

                if not status_issues:
                    continue

                f.write(f"## {status.replace('_', ' ').title()} ({len(status_issues)})\n\n")

                for issue in status_issues:
                    priority_icon = "🔴" if issue.priority == "P0" else "🟡" if issue.priority == "P1" else "🟢"

                    f.write(f"### {priority_icon} {issue.id}: {issue.title}\n\n")
                    f.write(f"- **Priority**: {issue.priority}\n")
                    f.write(f"- **Type**: {issue.issue_type}\n")
                    if issue.repo:
                        f.write(f"- **Repo**: {issue.repo}\n")
                    if issue.assigned_to:
                        f.write(f"- **Assigned To**: {issue.assigned_to}\n")
                    f.write(f"- **Created**: {issue.created_at}\n")
                    f.write(f"- **Updated**: {issue.updated_at}\n")

                    if issue.related_tasks:
                        f.write(f"- **Related Tasks**: {', '.join(f'`{t}`' for t in issue.related_tasks)}\n")

                    f.write(f"\n{issue.description}\n\n")

                    if issue.resolution:
                        f.write(f"**Resolution**: {issue.resolution}\n\n")

                    f.write("---\n\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Issue tracking for mission control")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List issues")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--priority", help="Filter by priority")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new issue")
    create_parser.add_argument("--title", required=True, help="Issue title")
    create_parser.add_argument("--description", required=True, help="Issue description")
    create_parser.add_argument("--priority", default="P2", choices=["P0", "P1", "P2"], help="Priority")
    create_parser.add_argument("--repo", help="Related repo")
    create_parser.add_argument("--tasks", help="Comma-separated task IDs")

    # Resolve command
    resolve_parser = subparsers.add_parser("resolve", help="Resolve an issue")
    resolve_parser.add_argument("issue_id", help="Issue ID to resolve")
    resolve_parser.add_argument("--resolution", required=True, help="Resolution description")

    # Close command
    close_parser = subparsers.add_parser("close", help="Close an issue")
    close_parser.add_argument("issue_id", help="Issue ID to close")

    # Auto-detect command
    auto_parser = subparsers.add_parser("auto-detect", help="Auto-detect issues from work queues")

    args = parser.parse_args()

    # Get mission control directory
    mission_control_dir = Path(__file__).parent.parent

    tracker = IssueTracker(mission_control_dir)

    if args.command == "list":
        issues = tracker.list_issues(status=args.status, priority=args.priority)
        if not issues:
            print("No issues found")
        else:
            print(f"\n{'ID':<20} {'Priority':<10} {'Status':<15} {'Title':<50}")
            print("-" * 95)
            for issue in issues:
                print(f"{issue.id:<20} {issue.priority:<10} {issue.status:<15} {issue.title[:47]:<50}")

    elif args.command == "create":
        related_tasks = args.tasks.split(",") if args.tasks else []
        issue = tracker.create_issue(
            title=args.title,
            description=args.description,
            priority=args.priority,
            repo=args.repo,
            related_tasks=related_tasks
        )
        print(f"✅ Created issue: {issue.id}")

    elif args.command == "resolve":
        resolved_issue: Optional[Issue] = tracker.resolve_issue(args.issue_id, args.resolution)
        if resolved_issue:
            print(f"✅ Resolved issue: {resolved_issue.id}")
        else:
            print(f"❌ Issue not found: {args.issue_id}")

    elif args.command == "close":
        closed_issue: Optional[Issue] = tracker.close_issue(args.issue_id)
        if closed_issue:
            print(f"✅ Closed issue: {closed_issue.id}")
        else:
            print(f"❌ Issue not found: {args.issue_id}")

    elif args.command == "auto-detect":
        print("🔍 Auto-detecting issues...")
        detected = tracker.auto_detect_issues()
        if detected:
            print(f"✅ Detected {len(detected)} new issue(s):")
            for issue in detected:
                print(f"   - {issue.id}: {issue.title}")
        else:
            print("✅ No new issues detected")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
