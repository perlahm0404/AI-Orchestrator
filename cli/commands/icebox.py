"""
CLI commands for Icebox (Parking Lot) management.

Usage:
    aibrain icebox add --title "..." --project cm
    aibrain icebox list --project cm --status raw
    aibrain icebox show IDEA-xxx
    aibrain icebox promote IDEA-xxx --status parked
    aibrain icebox stale --days 30
    aibrain icebox archive IDEA-xxx --reason "Superseded"

Ideas are captured for later consideration without disrupting current work.
"""

import sys
from pathlib import Path
from typing import Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from parking.service import (
    capture_idea,
    list_ideas,
    get_idea,
    promote_to_parked_task,
    promote_to_pending_task,
    archive_idea,
    get_stale_ideas,
)


def icebox_add_command(args: Any) -> int:
    """Capture a new idea to the icebox."""
    title = args.title
    description = args.description or ""
    project = args.project

    # Parse optional fields
    category = getattr(args, "category", "improvement")
    priority = getattr(args, "priority", 2)
    effort = getattr(args, "effort", "M")
    tags = getattr(args, "tags", "").split(",") if getattr(args, "tags", None) else []
    tags = [t.strip() for t in tags if t.strip()]

    print(f"\n📝 Capturing idea to icebox...")

    idea = capture_idea(
        title=title,
        description=description,
        project=project,
        category=category,  # type: ignore[arg-type]
        priority=priority,
        effort_estimate=effort,  # type: ignore[arg-type]
        tags=tags,
        source="human",
        discovered_by="cli",
    )

    if not idea:
        print("⚠️  Duplicate idea detected - already in icebox")
        return 1

    print(f"✅ Idea captured: {idea.id}")
    print(f"   Title: {idea.title}")
    print(f"   Project: {idea.project}")
    print(f"   Category: {idea.category}")
    print(f"   Priority: P{idea.priority}")
    print(f"\n   View with: aibrain icebox show {idea.id}")
    print(f"   Promote with: aibrain icebox promote {idea.id} --status pending")

    return 0


def icebox_list_command(args: Any) -> int:
    """List ideas in the icebox."""
    project = getattr(args, "project", None)
    status = getattr(args, "status", None)
    category = getattr(args, "category", None)
    include_archived = getattr(args, "archived", False)

    ideas = list_ideas(
        project=project,
        status=status,
        category=category,
        include_archived=include_archived,
    )

    if not ideas:
        print("\n✨ No ideas in icebox")
        if project:
            print(f"   (filtered by project: {project})")
        return 0

    print(f"\n{'='*60}")
    print(f"📦 ICEBOX IDEAS ({len(ideas)})")
    if project:
        print(f"   Project: {project}")
    if status:
        print(f"   Status: {status}")
    print(f"{'='*60}\n")

    for idea in ideas:
        priority_emoji = ["🔴", "🟠", "🟡", "⚪"][min(idea.priority, 3)]
        status_emoji = {
            "raw": "📝",
            "reviewed": "👁️",
            "promoted": "✅",
            "archived": "📦",
        }.get(idea.status, "❓")

        print(f"{status_emoji} {idea.id} {priority_emoji} P{idea.priority}")
        print(f"   {idea.title}")
        print(f"   {idea.category} | {idea.effort_estimate} | {idea.project}")
        if idea.tags:
            print(f"   Tags: {', '.join(idea.tags)}")
        print()

    return 0


def icebox_show_command(args: Any) -> int:
    """Show details of a specific idea."""
    idea_id = args.idea_id

    idea = get_idea(idea_id)
    if not idea:
        print(f"\n❌ Idea not found: {idea_id}")
        print(f"   List ideas with: aibrain icebox list")
        return 1

    print(f"\n{'='*60}")
    print(f"📝 IDEA: {idea.id}")
    print(f"{'='*60}\n")

    print(f"Title: {idea.title}")
    print(f"Project: {idea.project}")
    print(f"Category: {idea.category}")
    print(f"Priority: P{idea.priority}")
    print(f"Effort: {idea.effort_estimate}")
    print(f"Status: {idea.status}")
    print()

    print(f"Source: {idea.source}")
    print(f"Discovered by: {idea.discovered_by}")
    print(f"Created: {idea.created_at}")
    if idea.last_reviewed:
        print(f"Last reviewed: {idea.last_reviewed}")
    print()

    if idea.tags:
        print(f"Tags: {', '.join(idea.tags)}")
    if idea.dependencies:
        print(f"Dependencies: {', '.join(idea.dependencies)}")
    print()

    print("Description:")
    print(f"  {idea.description}")
    print()

    if idea.promoted_to:
        print(f"Promoted to: {idea.promoted_to}")
    if idea.archived_reason:
        print(f"Archive reason: {idea.archived_reason}")

    print(f"\n{'='*60}")
    print(f"Actions:")
    print(f"  Promote: aibrain icebox promote {idea.id} --status pending")
    print(f"  Archive: aibrain icebox archive {idea.id} --reason 'reason'")
    print(f"{'='*60}\n")

    return 0


def icebox_promote_command(args: Any) -> int:
    """Promote an idea to the work queue."""
    idea_id = args.idea_id
    status = args.status
    project = getattr(args, "project", None)

    idea = get_idea(idea_id)
    if not idea:
        print(f"\n❌ Idea not found: {idea_id}")
        return 1

    # Use idea's project if not specified
    if not project:
        project = idea.project

    print(f"\n🚀 Promoting idea to work queue...")
    print(f"   Idea: {idea.title}")
    print(f"   Target status: {status}")
    print(f"   Project: {project}")

    if status == "pending":
        task_id = promote_to_pending_task(idea_id, project)
    else:
        task_id = promote_to_parked_task(idea_id, project)

    if not task_id:
        print(f"\n❌ Failed to promote idea")
        print(f"   Check that work queue exists for project: {project}")
        return 1

    print(f"\n✅ Idea promoted to task: {task_id}")
    print(f"   Status: {status}")
    print(f"   View with: aibrain tasks list --project {project}")

    return 0


def icebox_stale_command(args: Any) -> int:
    """Show stale ideas needing review."""
    days = args.days

    stale = get_stale_ideas(days=days)

    if not stale:
        print(f"\n✨ No stale ideas (older than {days} days)")
        return 0

    print(f"\n{'='*60}")
    print(f"⏰ STALE IDEAS ({len(stale)} older than {days} days)")
    print(f"{'='*60}\n")

    for idea in stale:
        print(f"📝 {idea.id}")
        print(f"   {idea.title}")
        print(f"   Created: {idea.created_at}")
        print(f"   Last reviewed: {idea.last_reviewed or 'Never'}")
        print()

    print(f"Actions:")
    print(f"  Review: aibrain icebox show <idea_id>")
    print(f"  Archive all: aibrain icebox cleanup --older-than {days}")

    return 0


def icebox_archive_command(args: Any) -> int:
    """Archive an idea."""
    idea_id = args.idea_id
    reason = args.reason

    idea = get_idea(idea_id)
    if not idea:
        print(f"\n❌ Idea not found: {idea_id}")
        return 1

    print(f"\n📦 Archiving idea...")
    print(f"   Idea: {idea.title}")
    print(f"   Reason: {reason}")

    success = archive_idea(idea_id, reason)

    if success:
        print(f"\n✅ Idea archived: {idea_id}")
    else:
        print(f"\n❌ Failed to archive idea")
        return 1

    return 0


def icebox_cleanup_command(args: Any) -> int:
    """Archive stale ideas in bulk."""
    days = args.older_than

    stale = get_stale_ideas(days=days)

    if not stale:
        print(f"\n✨ No stale ideas (older than {days} days)")
        return 0

    print(f"\n📦 Archiving {len(stale)} stale ideas...")

    archived = 0
    for idea in stale:
        reason = f"Auto-archived: no activity for {days}+ days"
        if archive_idea(idea.id, reason):
            print(f"   ✓ {idea.id}: {idea.title[:40]}...")
            archived += 1

    print(f"\n✅ Archived {archived} ideas")

    return 0


def setup_parser(subparsers: Any) -> None:
    """Setup argparse for icebox commands."""

    # Main 'icebox' command
    icebox_parser = subparsers.add_parser(
        "icebox",
        help="Manage Icebox (Parking Lot) ideas",
        description="Capture, list, promote, and archive ideas for future work"
    )

    icebox_subparsers = icebox_parser.add_subparsers(
        dest='icebox_command',
        help='Icebox subcommand'
    )

    # icebox add
    add_parser = icebox_subparsers.add_parser(
        "add",
        help="Capture a new idea"
    )
    add_parser.add_argument("--title", "-t", required=True, help="Idea title")
    add_parser.add_argument("--description", "-d", default="", help="Full description")
    add_parser.add_argument("--project", "-p", required=True,
                           help="Project (credentialmate, karematch, ai-orchestrator)")
    add_parser.add_argument("--category", "-c", default="improvement",
                           choices=["feature", "improvement", "research", "tech-debt", "bug"],
                           help="Idea category")
    add_parser.add_argument("--priority", type=int, default=2,
                           choices=[0, 1, 2, 3],
                           help="Priority (0=urgent, 3=someday)")
    add_parser.add_argument("--effort", "-e", default="M",
                           choices=["XS", "S", "M", "L", "XL"],
                           help="Effort estimate")
    add_parser.add_argument("--tags", help="Comma-separated tags")
    add_parser.set_defaults(func=icebox_add_command)

    # icebox list
    list_parser = icebox_subparsers.add_parser(
        "list",
        help="List ideas in the icebox"
    )
    list_parser.add_argument("--project", "-p", help="Filter by project")
    list_parser.add_argument("--status", "-s",
                            choices=["raw", "reviewed", "promoted", "archived"],
                            help="Filter by status")
    list_parser.add_argument("--category", "-c",
                            choices=["feature", "improvement", "research", "tech-debt", "bug"],
                            help="Filter by category")
    list_parser.add_argument("--archived", "-a", action="store_true",
                            help="Include archived ideas")
    list_parser.set_defaults(func=icebox_list_command)

    # icebox show
    show_parser = icebox_subparsers.add_parser(
        "show",
        help="Show idea details"
    )
    show_parser.add_argument("idea_id", help="Idea ID (e.g., IDEA-20260207-1430-001)")
    show_parser.set_defaults(func=icebox_show_command)

    # icebox promote
    promote_parser = icebox_subparsers.add_parser(
        "promote",
        help="Promote idea to work queue"
    )
    promote_parser.add_argument("idea_id", help="Idea ID to promote")
    promote_parser.add_argument("--status", "-s", required=True,
                               choices=["parked", "pending"],
                               help="Target status in work queue")
    promote_parser.add_argument("--project", "-p",
                               help="Override project for work queue")
    promote_parser.set_defaults(func=icebox_promote_command)

    # icebox stale
    stale_parser = icebox_subparsers.add_parser(
        "stale",
        help="Show stale ideas needing review"
    )
    stale_parser.add_argument("--days", "-d", type=int, default=30,
                             help="Days threshold (default: 30)")
    stale_parser.set_defaults(func=icebox_stale_command)

    # icebox archive
    archive_parser = icebox_subparsers.add_parser(
        "archive",
        help="Archive an idea"
    )
    archive_parser.add_argument("idea_id", help="Idea ID to archive")
    archive_parser.add_argument("--reason", "-r", required=True,
                               help="Why archiving (e.g., 'Superseded by FEAT-123')")
    archive_parser.set_defaults(func=icebox_archive_command)

    # icebox cleanup
    cleanup_parser = icebox_subparsers.add_parser(
        "cleanup",
        help="Archive stale ideas in bulk"
    )
    cleanup_parser.add_argument("--older-than", type=int, default=90,
                               help="Archive ideas older than N days (default: 90)")
    cleanup_parser.set_defaults(func=icebox_cleanup_command)

    # Set default function for bare 'icebox' command
    icebox_parser.set_defaults(func=lambda args: icebox_list_command(args))
