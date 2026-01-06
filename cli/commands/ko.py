"""
CLI commands for Knowledge Object management.

Usage:
    aibrain ko pending              # List draft KOs awaiting approval
    aibrain ko approve KO-km-001    # Approve a draft KO
    aibrain ko list [--project km]  # List approved KOs
    aibrain ko search --tags auth   # Search KOs by tags
    aibrain ko show KO-km-001       # Show full KO details

Knowledge Objects capture institutional learning from agent sessions.
Drafts are created automatically after multi-iteration successes.
Humans approve KOs before they're used for agent consultation.
"""

import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge.service import (
    list_drafts,
    list_approved,
    approve,
    find_relevant,
    _load_ko_from_file,
    KO_DRAFTS_DIR,
    KO_APPROVED_DIR
)


def ko_pending_command(args):
    """List all pending (draft) Knowledge Objects."""
    drafts = list_drafts()

    if not drafts:
        print("\n✨ No pending Knowledge Objects")
        return 0

    print(f"\n{'='*60}")
    print(f"📝 PENDING KNOWLEDGE OBJECTS ({len(drafts)})")
    print(f"{'='*60}\n")

    for ko in drafts:
        print(f"ID: {ko.id}")
        print(f"Title: {ko.title}")
        print(f"Project: {ko.project}")
        print(f"Tags: {', '.join(ko.tags)}")
        print(f"Created: {ko.created_at}\n")
        print(f"What was learned:")
        print(f"  {ko.what_was_learned}\n")
        print(f"Prevention rule:")
        print(f"  {ko.prevention_rule}\n")
        print(f"Approve with: aibrain ko approve {ko.id}")
        print(f"{'='*60}\n")

    return 0


def ko_approve_command(args):
    """Approve a draft Knowledge Object."""
    ko_id = args.ko_id

    print(f"\n🔍 Approving Knowledge Object: {ko_id}...")

    ko = approve(ko_id)

    if not ko:
        print(f"❌ Knowledge Object not found: {ko_id}")
        print(f"   Check pending KOs with: aibrain ko pending")
        return 1

    print(f"✅ Approved: {ko.id}")
    print(f"   Title: {ko.title}")
    print(f"   Project: {ko.project}")
    print(f"   Tags: {', '.join(ko.tags)}")
    print(f"\nThis knowledge will now be consulted by agents.\n")

    return 0


def ko_list_command(args):
    """List approved Knowledge Objects."""
    approved = list_approved(project=args.project)

    if not approved:
        project_msg = f" for project '{args.project}'" if args.project else ""
        print(f"\n✨ No approved Knowledge Objects{project_msg}")
        return 0

    print(f"\n{'='*60}")
    print(f"📚 APPROVED KNOWLEDGE OBJECTS ({len(approved)})")
    if args.project:
        print(f"    Project: {args.project}")
    print(f"{'='*60}\n")

    for ko in approved:
        print(f"{ko.id}: {ko.title}")
        print(f"  Project: {ko.project}")
        print(f"  Tags: {', '.join(ko.tags)}")
        print(f"  Created: {ko.created_at[:10]}")
        print()

    print(f"View details with: aibrain ko show <ID>\n")

    return 0


def ko_search_command(args):
    """Search Knowledge Objects by tags."""
    tags = [tag.strip() for tag in args.tags.split(',')]

    print(f"\n🔍 Searching for KOs with tags: {', '.join(tags)}...")

    results = find_relevant(
        project=args.project,
        tags=tags
    )

    if not results:
        print(f"❌ No Knowledge Objects found matching tags: {', '.join(tags)}")
        return 0

    print(f"\n{'='*60}")
    print(f"📚 SEARCH RESULTS ({len(results)} found)")
    print(f"{'='*60}\n")

    for ko in results:
        print(f"{ko.id}: {ko.title}")
        print(f"  Tags: {', '.join(ko.tags)}")
        print(f"  Learned: {ko.what_was_learned[:80]}...")
        print()

    print(f"View details with: aibrain ko show <ID>\n")

    return 0


def ko_show_command(args):
    """Show full details of a Knowledge Object."""
    ko_id = args.ko_id

    # Check approved first
    ko_file = KO_APPROVED_DIR / f"{ko_id}.md"
    if not ko_file.exists():
        # Check drafts
        ko_file = KO_DRAFTS_DIR / f"{ko_id}.md"

    if not ko_file.exists():
        print(f"\n❌ Knowledge Object not found: {ko_id}")
        print(f"   Available commands:")
        print(f"   - aibrain ko pending     (list drafts)")
        print(f"   - aibrain ko list        (list approved)")
        return 1

    ko = _load_ko_from_file(ko_file)

    if not ko:
        print(f"\n❌ Failed to load Knowledge Object: {ko_id}")
        return 1

    # Display full KO
    print(f"\n{'='*60}")
    print(f"📖 KNOWLEDGE OBJECT: {ko.id}")
    print(f"{'='*60}\n")

    print(f"Title: {ko.title}")
    print(f"Project: {ko.project}")
    print(f"Status: {ko.status}")
    print(f"Created: {ko.created_at}")
    if ko.approved_at:
        print(f"Approved: {ko.approved_at}")
    print()

    print(f"Tags: {', '.join(ko.tags)}")
    print()

    print("What Was Learned:")
    print(f"  {ko.what_was_learned}")
    print()

    print("Why It Matters:")
    print(f"  {ko.why_it_matters}")
    print()

    print("Prevention Rule:")
    print(f"  {ko.prevention_rule}")
    print()

    if ko.detection_pattern:
        print("Detection Pattern:")
        print(f"  {ko.detection_pattern}")
        print()

    if ko.file_patterns:
        print("File Patterns:")
        for pattern in ko.file_patterns:
            print(f"  - {pattern}")
        print()

    print(f"{'='*60}\n")

    return 0


def setup_parser(subparsers):
    """Setup argparse for KO commands."""

    # Main 'ko' command
    ko_parser = subparsers.add_parser(
        "ko",
        help="Manage Knowledge Objects",
        description="Create, approve, list, and search Knowledge Objects"
    )

    ko_subparsers = ko_parser.add_subparsers(
        dest='ko_command',
        help='KO subcommand'
    )

    # ko pending
    pending_parser = ko_subparsers.add_parser(
        "pending",
        help="List pending (draft) Knowledge Objects"
    )
    pending_parser.set_defaults(func=ko_pending_command)

    # ko approve
    approve_parser = ko_subparsers.add_parser(
        "approve",
        help="Approve a draft Knowledge Object"
    )
    approve_parser.add_argument("ko_id", help="Knowledge Object ID (e.g., KO-km-001)")
    approve_parser.set_defaults(func=ko_approve_command)

    # ko list
    list_parser = ko_subparsers.add_parser(
        "list",
        help="List approved Knowledge Objects"
    )
    list_parser.add_argument("--project", help="Filter by project (karematch, credentialmate)")
    list_parser.set_defaults(func=ko_list_command)

    # ko search
    search_parser = ko_subparsers.add_parser(
        "search",
        help="Search Knowledge Objects by tags"
    )
    search_parser.add_argument("--tags", required=True, help="Comma-separated tags to search")
    search_parser.add_argument("--project", help="Filter by project")
    search_parser.set_defaults(func=ko_search_command)

    # ko show
    show_parser = ko_subparsers.add_parser(
        "show",
        help="Show full details of a Knowledge Object"
    )
    show_parser.add_argument("ko_id", help="Knowledge Object ID")
    show_parser.set_defaults(func=ko_show_command)
