"""
CLI commands for ADR (Architecture Decision Record) management.

Usage:
    aibrain adr pending [--project km]    # List draft ADRs awaiting approval
    aibrain adr show ADR-006              # Show full ADR details
    aibrain adr approve ADR-006           # Approve ADR and extract tasks
    aibrain adr reject ADR-006 "reason"   # Reject ADR draft

ADRs are created automatically after advisor consultations.
Approving an ADR extracts implementation tasks into the work queue.
"""

import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.adr_registry import ADRRegistry
from orchestration.adr_to_tasks import extract_tasks_from_adr, register_tasks_with_queue
from tasks.work_queue import WorkQueue


def adr_pending_command(args):
    """List all pending (draft) ADRs."""

    # Get AI Orchestrator root
    orchestrator_root = Path(__file__).parent.parent.parent
    registry = ADRRegistry(orchestrator_root)

    # Read index to find draft ADRs
    if not registry.index_path.exists():
        print("\n❌ ADR index not found")
        print(f"   Expected: {registry.index_path}")
        return 1

    content = registry.index_path.read_text()

    # Extract draft ADRs from registry table
    import re
    draft_pattern = r'\| (ADR-\d+) \| \[([^\]]+)\]\(([^\)]+)\) \| ([^\|]+) \| draft \| ([^\|]+) \| ([^\|]+) \|'

    drafts = []
    for match in re.finditer(draft_pattern, content):
        adr_id, title, file_path, project, date, advisor = match.groups()

        # Filter by project if specified
        if args.project and args.project.lower() not in project.lower():
            continue

        drafts.append({
            "id": adr_id.strip(),
            "title": title.strip(),
            "file_path": file_path.strip(),
            "project": project.strip(),
            "date": date.strip(),
            "advisor": advisor.strip()
        })

    if not drafts:
        project_msg = f" for project '{args.project}'" if args.project else ""
        print(f"\n✨ No pending ADRs{project_msg}")
        return 0

    print(f"\n{'='*60}")
    print(f"📝 PENDING ADRs ({len(drafts)})")
    if args.project:
        print(f"    Project: {args.project}")
    print(f"{'='*60}\n")

    for adr in drafts:
        print(f"ID: {adr['id']}")
        print(f"Title: {adr['title']}")
        print(f"Project: {adr['project']}")
        print(f"Date: {adr['date']}")
        print(f"Advisor: {adr['advisor']}")
        print(f"File: {adr['file_path']}")
        print()
        print(f"Commands:")
        print(f"  View: aibrain adr show {adr['id']}")
        print(f"  Approve: aibrain adr approve {adr['id']}")
        print(f"  Reject: aibrain adr reject {adr['id']} \"reason\"")
        print(f"{'='*60}\n")

    return 0


def adr_show_command(args):
    """Show full details of an ADR."""
    adr_id = args.adr_id

    # Get AI Orchestrator root
    orchestrator_root = Path(__file__).parent.parent.parent
    decisions_dir = orchestrator_root / "AI-Team-Plans" / "decisions"

    # Find ADR file
    adr_files = list(decisions_dir.glob(f"{adr_id}-*.md"))

    if not adr_files:
        print(f"\n❌ ADR not found: {adr_id}")
        print(f"   Searched in: {decisions_dir}")
        print(f"\n   Available commands:")
        print(f"   - aibrain adr pending  (list draft ADRs)")
        return 1

    adr_file = adr_files[0]

    # Read and display ADR
    content = adr_file.read_text()

    print(f"\n{'='*80}")
    print(f"📖 ADR: {adr_id}")
    print(f"{'='*80}\n")
    print(content)
    print(f"\n{'='*80}\n")

    return 0


def adr_approve_command(args):
    """Approve an ADR and extract implementation tasks."""
    adr_id = args.adr_id

    print(f"\n🔍 Approving ADR: {adr_id}...")

    # Get AI Orchestrator root
    orchestrator_root = Path(__file__).parent.parent.parent
    registry = ADRRegistry(orchestrator_root)
    decisions_dir = orchestrator_root / "AI-Team-Plans" / "decisions"

    # Find ADR file
    adr_files = list(decisions_dir.glob(f"{adr_id}-*.md"))

    if not adr_files:
        print(f"❌ ADR not found: {adr_id}")
        print(f"   Check pending ADRs with: aibrain adr pending")
        return 1

    adr_file = adr_files[0]

    # Update ADR status to "approved" in registry
    if not registry.index_path.exists():
        print(f"❌ ADR index not found: {registry.index_path}")
        return 1

    content = registry.index_path.read_text()

    # Update status from "draft" to "approved"
    import re
    pattern = rf'(\| {adr_id} \| [^\|]+ \| [^\|]+ \| )draft( \| [^\|]+ \| [^\|]+ \|)'
    replacement = r'\1✅ approved\2'
    updated_content = re.sub(pattern, replacement, content)

    if content == updated_content:
        print(f"⚠️  ADR {adr_id} may already be approved or not found in registry")
    else:
        registry.index_path.write_text(updated_content)
        print(f"✅ Updated ADR status to 'approved' in registry")

    # Extract implementation tasks
    print(f"\n📝 Extracting implementation tasks from ADR...")

    # Determine project from ADR content
    adr_content = adr_file.read_text()
    project_match = re.search(r'Project:\s*([^\n]+)', adr_content)
    project = project_match.group(1).strip() if project_match else "AI_Orchestrator"

    tasks = extract_tasks_from_adr(adr_file, adr_id, project)

    if not tasks:
        print(f"⚠️  No tasks found in ADR Implementation Notes")
        print(f"   ADR approved but no tasks registered")
        return 0

    print(f"   Found {len(tasks)} tasks")

    # Find work queue for project
    tasks_dir = orchestrator_root / "tasks"
    queue_path = tasks_dir / f"work_queue_{project.lower()}.json"

    if not queue_path.exists():
        queue_path = tasks_dir / "work_queue.json"

    if not queue_path.exists():
        print(f"❌ Work queue not found for project: {project}")
        print(f"   Searched: {queue_path}")
        return 1

    queue = WorkQueue.load(queue_path)

    # Register tasks
    task_ids = register_tasks_with_queue(tasks, adr_id, queue, queue_path)

    print(f"\n✅ Approved ADR: {adr_id}")
    print(f"   Registered {len(task_ids)} tasks:")
    for task_id in task_ids:
        print(f"   - {task_id}")
    print(f"\n   View tasks with: aibrain tasks list --project {project}")
    print(f"   Start work with: python autonomous_loop.py --project {project}\n")

    return 0


def adr_reject_command(args):
    """Reject an ADR draft."""
    adr_id = args.adr_id
    reason = args.reason

    print(f"\n🔍 Rejecting ADR: {adr_id}...")
    print(f"   Reason: {reason}")

    # Get AI Orchestrator root
    orchestrator_root = Path(__file__).parent.parent.parent
    registry = ADRRegistry(orchestrator_root)

    # Update ADR status to "rejected" in registry
    if not registry.index_path.exists():
        print(f"❌ ADR index not found: {registry.index_path}")
        return 1

    content = registry.index_path.read_text()

    # Update status from "draft" to "rejected"
    import re
    pattern = rf'(\| {adr_id} \| [^\|]+ \| [^\|]+ \| )draft( \| [^\|]+ \| [^\|]+ \|)'
    replacement = r'\1❌ rejected\2'
    updated_content = re.sub(pattern, replacement, content)

    if content == updated_content:
        print(f"⚠️  ADR {adr_id} not found in registry or already processed")
        return 1

    registry.index_path.write_text(updated_content)

    # Optionally add rejection comment to ADR file
    decisions_dir = orchestrator_root / "AI-Team-Plans" / "decisions"
    adr_files = list(decisions_dir.glob(f"{adr_id}-*.md"))

    if adr_files:
        adr_file = adr_files[0]
        adr_content = adr_file.read_text()

        # Append rejection note
        rejection_note = f"\n\n---\n\n## Rejection Note\n\n**Date**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}\n\n**Reason**: {reason}\n"
        adr_file.write_text(adr_content + rejection_note)

    print(f"✅ Rejected ADR: {adr_id}")
    print(f"   Status updated in registry")
    print(f"   Rejection note added to ADR file\n")

    return 0


def setup_parser(subparsers):
    """Setup argparse for ADR commands."""

    # Main 'adr' command
    adr_parser = subparsers.add_parser(
        "adr",
        help="Manage Architecture Decision Records",
        description="List, approve, reject, and view ADRs"
    )

    adr_subparsers = adr_parser.add_subparsers(
        dest='adr_command',
        help='ADR subcommand'
    )

    # adr pending
    pending_parser = adr_subparsers.add_parser(
        "pending",
        help="List pending (draft) ADRs"
    )
    pending_parser.add_argument("--project", help="Filter by project (karematch, credentialmate)")
    pending_parser.set_defaults(func=adr_pending_command)

    # adr show
    show_parser = adr_subparsers.add_parser(
        "show",
        help="Show full details of an ADR"
    )
    show_parser.add_argument("adr_id", help="ADR ID (e.g., ADR-006)")
    show_parser.set_defaults(func=adr_show_command)

    # adr approve
    approve_parser = adr_subparsers.add_parser(
        "approve",
        help="Approve an ADR and extract implementation tasks"
    )
    approve_parser.add_argument("adr_id", help="ADR ID (e.g., ADR-006)")
    approve_parser.set_defaults(func=adr_approve_command)

    # adr reject
    reject_parser = adr_subparsers.add_parser(
        "reject",
        help="Reject an ADR draft"
    )
    reject_parser.add_argument("adr_id", help="ADR ID (e.g., ADR-006)")
    reject_parser.add_argument("reason", help="Reason for rejection")
    reject_parser.set_defaults(func=adr_reject_command)
