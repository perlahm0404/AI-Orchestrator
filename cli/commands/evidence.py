"""
CLI commands for Evidence Repository management.

Usage:
    aibrain evidence capture <type> <source>
    aibrain evidence list [--state STATE] [--priority PRIORITY] [--status STATUS] [--tags TAGS]
    aibrain evidence link EVIDENCE-ID TASK-ID
    aibrain evidence show EVIDENCE-ID
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import re

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def evidence_capture_command(args):
    """Interactive capture of new evidence."""
    evidence_type = args.type
    source = args.source

    # Get AI Orchestrator root
    orchestrator_root = Path(__file__).parent.parent.parent
    evidence_dir = orchestrator_root / "evidence"

    # Find next evidence number
    existing_evidence = list(evidence_dir.glob("EVIDENCE-*.md"))
    if existing_evidence:
        numbers = []
        for e in existing_evidence:
            match = re.match(r'EVIDENCE-(\d+)', e.stem)
            if match:
                numbers.append(int(match.group(1)))
        next_num = max(numbers) + 1
    else:
        next_num = 1

    evidence_id = f"EVIDENCE-{next_num:03d}"

    print(f"\n{'='*60}")
    print(f"📝 CAPTURING NEW EVIDENCE: {evidence_id}")
    print(f"{'='*60}\n")

    # Interactive prompts
    print(f"Type: {evidence_type}")
    print(f"Source: {source}")

    summary = input("Evidence summary (1-2 sentences): ").strip()

    print("\nContext:")
    persona = input("  User persona [NP|PA|Physician|DO]: ").strip()
    state = input("  State [CA|TX|NY|FL|PA|...]: ").strip().upper()
    specialty = input("  Specialty [Family Medicine|Emergency|...]: ").strip()
    current_behavior = input("  Current behavior: ").strip()
    expected_behavior = input("  Expected behavior: ").strip()

    print("\nRaw Data:")
    user_quote = input("  User quote (optional): ").strip()
    links = input("  Links/URLs (optional): ").strip()

    print("\nImpact:")
    users_affected = input("  How many users affected? [1 user|common pattern|all {state} users]: ").strip()
    urgency = input("  Urgency [immediate|this quarter|backlog]: ").strip()
    business_value = input("  Business value [high-retention|nice-to-have|table-stakes]: ").strip()

    priority_input = input("\nPriority [p0-blocks-user|p1-degrades-trust|p2-improvement]: ").strip()

    tags_input = input("Tags (comma-separated, e.g., cme,california,np): ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]

    # Generate evidence file
    today = datetime.now().strftime("%Y-%m-%d")

    content = f"""---
id: {evidence_id}
date: {today}
type: {evidence_type}
source: {source}
project: credentialmate
tags: {tags}
priority: {priority_input}
linked_tasks: []
linked_adrs: []
status: captured
---

## Evidence Summary
{summary}

## Context
- User persona: {persona}
- State: {state}
- Specialty: {specialty}
- Current behavior: {current_behavior}
- Expected behavior: {expected_behavior}

## Raw Data
"""

    if user_quote:
        content += f"- User quote: \"{user_quote}\"\n"
    if links:
        content += f"- Links: {links}\n"

    content += f"""

## Impact Assessment
- How many users affected? {users_affected}
- Urgency: {urgency}
- Business value: {business_value}

## Linked Items
- Tasks: *(To be linked)*
- ADRs: *(None yet)*
- KOs: *(None yet)*

## Resolution (if implemented)
- Date resolved: *(Not yet resolved)*
- Implementation: *(Pending)*
- Validation: *(Pending)*
"""

    # Create filename slug
    slug = re.sub(r'[^\w\s-]', '', summary.lower())
    slug = re.sub(r'[-\s]+', '-', slug)[:40]

    filename = f"{evidence_id}-{slug}.md"
    evidence_file = evidence_dir / filename
    evidence_file.write_text(content)

    # Update index
    index_file = evidence_dir / "index.md"
    if index_file.exists():
        index_content = index_file.read_text()

        # Add to table
        new_row = f"| {evidence_id} | {today} | {evidence_type} | {state} | {priority_input} | captured | {summary[:60]} |"

        if "No evidence items yet" in index_content:
            # Replace placeholder
            index_content = index_content.replace(
                "| - | - | - | - | - | - | No evidence items yet |",
                new_row
            )
        else:
            # Add after header
            lines = index_content.split("\n")
            header_idx = next(i for i, line in enumerate(lines) if line.startswith("|----|"))
            lines.insert(header_idx + 1, new_row)
            index_content = "\n".join(lines)

        index_file.write_text(index_content)

    print(f"\n✅ Evidence captured: {evidence_file}")
    print(f"\nNext steps:")
    print(f"  - Review weekly on Friday")
    print(f"  - Link to task: aibrain evidence link {evidence_id} TASK-XXX")
    print(f"  - View: aibrain evidence show {evidence_id}\n")

    return 0


def evidence_list_command(args):
    """List evidence by filters."""
    orchestrator_root = Path(__file__).parent.parent.parent
    evidence_dir = orchestrator_root / "evidence"

    # Find all evidence files
    evidence_files = list(evidence_dir.glob("EVIDENCE-*.md"))
    evidence_files = [f for f in evidence_files if not f.parent.name == "examples"]

    if not evidence_files:
        print("\n✨ No evidence items yet")
        print("   Create first item: aibrain evidence capture <type> <source>\n")
        return 0

    # Parse frontmatter and filter
    items = []
    for evidence_file in evidence_files:
        content = evidence_file.read_text()

        # Extract frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]

                # Parse YAML-ish frontmatter
                metadata = {}
                for line in frontmatter.strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()

                # Apply filters
                if args.state and args.state.upper() not in metadata.get("tags", ""):
                    continue
                if args.priority and args.priority not in metadata.get("priority", ""):
                    continue
                if args.status and args.status not in metadata.get("status", ""):
                    continue
                if args.tags:
                    filter_tags = [t.strip() for t in args.tags.split(",")]
                    evidence_tags = metadata.get("tags", "")
                    if not any(tag in evidence_tags for tag in filter_tags):
                        continue

                # Extract summary
                summary_match = re.search(r'## Evidence Summary\n(.+?)(?:\n##|\Z)', content, re.DOTALL)
                summary = summary_match.group(1).strip() if summary_match else "No summary"

                items.append({
                    "id": metadata.get("id", "Unknown"),
                    "date": metadata.get("date", "Unknown"),
                    "type": metadata.get("type", "Unknown"),
                    "priority": metadata.get("priority", "Unknown"),
                    "status": metadata.get("status", "Unknown"),
                    "tags": metadata.get("tags", "[]"),
                    "summary": summary[:80]
                })

    if not items:
        print(f"\n✨ No evidence items matching filters")
        return 0

    # Display
    print(f"\n{'='*80}")
    print(f"📋 EVIDENCE ITEMS ({len(items)})")
    if args.state:
        print(f"    State: {args.state}")
    if args.priority:
        print(f"    Priority: {args.priority}")
    if args.status:
        print(f"    Status: {args.status}")
    if args.tags:
        print(f"    Tags: {args.tags}")
    print(f"{'='*80}\n")

    for item in items:
        print(f"ID: {item['id']}")
        print(f"Date: {item['date']}")
        print(f"Type: {item['type']}")
        print(f"Priority: {item['priority']}")
        print(f"Status: {item['status']}")
        print(f"Tags: {item['tags']}")
        print(f"Summary: {item['summary']}")
        print(f"\nCommands:")
        print(f"  View: aibrain evidence show {item['id']}")
        print(f"  Link: aibrain evidence link {item['id']} TASK-XXX")
        print(f"{'='*80}\n")

    return 0


def evidence_link_command(args):
    """Link evidence to task/ADR/KO."""
    evidence_id = args.evidence_id
    task_id = args.task_id

    orchestrator_root = Path(__file__).parent.parent.parent
    evidence_dir = orchestrator_root / "evidence"

    # Find evidence file
    evidence_files = list(evidence_dir.glob(f"{evidence_id}-*.md"))

    if not evidence_files:
        print(f"\n❌ Evidence not found: {evidence_id}")
        return 1

    evidence_file = evidence_files[0]
    content = evidence_file.read_text()

    # Update linked_tasks in frontmatter
    if "linked_tasks: []" in content:
        content = content.replace("linked_tasks: []", f"linked_tasks: [{task_id}]")
    elif "linked_tasks:" in content:
        # Append to existing list
        content = re.sub(
            r'linked_tasks: \[(.*?)\]',
            lambda m: f"linked_tasks: [{m.group(1)}, {task_id}]" if m.group(1) else f"linked_tasks: [{task_id}]",
            content
        )

    # Update "Linked Items" section
    content = re.sub(
        r'- Tasks: \*\(To be linked\)\*',
        f'- Tasks: {task_id}',
        content
    )
    content = re.sub(
        r'- Tasks: ([^\n]+)',
        lambda m: f'- Tasks: {m.group(1)}, {task_id}' if task_id not in m.group(1) else m.group(0),
        content
    )

    evidence_file.write_text(content)

    print(f"\n✅ Linked {evidence_id} → {task_id}")
    print(f"   Evidence file: {evidence_file}\n")

    return 0


def evidence_show_command(args):
    """Show full evidence details."""
    evidence_id = args.evidence_id

    orchestrator_root = Path(__file__).parent.parent.parent
    evidence_dir = orchestrator_root / "evidence"

    # Find evidence file
    evidence_files = list(evidence_dir.glob(f"{evidence_id}-*.md"))

    if not evidence_files:
        print(f"\n❌ Evidence not found: {evidence_id}")
        print(f"   Use: aibrain evidence list")
        return 1

    evidence_file = evidence_files[0]
    content = evidence_file.read_text()

    print(f"\n{'='*80}")
    print(f"📖 EVIDENCE: {evidence_id}")
    print(f"{'='*80}\n")
    print(content)
    print(f"\n{'='*80}\n")

    return 0


def setup_parser(subparsers):
    """Setup argparse for evidence commands."""

    # Main 'evidence' command
    evidence_parser = subparsers.add_parser(
        "evidence",
        help="Manage Evidence Repository (continuous discovery)",
        description="Capture, list, link, and review evidence items"
    )

    evidence_subparsers = evidence_parser.add_subparsers(
        dest='evidence_command',
        help='Evidence subcommand'
    )

    # evidence capture
    capture_parser = evidence_subparsers.add_parser(
        "capture",
        help="Capture new evidence item (interactive)"
    )
    capture_parser.add_argument("type", help="Evidence type (bug-report, feature-request, user-question, edge-case, state-variation)")
    capture_parser.add_argument("source", help="Evidence source (pilot-user, support-ticket, state-website, manual-testing)")
    capture_parser.set_defaults(func=evidence_capture_command)

    # evidence list
    list_parser = evidence_subparsers.add_parser(
        "list",
        help="List evidence items with filters"
    )
    list_parser.add_argument("--state", help="Filter by state (CA, TX, NY, ...)")
    list_parser.add_argument("--priority", help="Filter by priority (p0-blocks-user, p1-degrades-trust, p2-improvement)")
    list_parser.add_argument("--status", help="Filter by status (captured, analyzed, implemented, validated)")
    list_parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    list_parser.set_defaults(func=evidence_list_command)

    # evidence link
    link_parser = evidence_subparsers.add_parser(
        "link",
        help="Link evidence to task/ADR/KO"
    )
    link_parser.add_argument("evidence_id", help="Evidence ID (e.g., EVIDENCE-001)")
    link_parser.add_argument("task_id", help="Task ID (e.g., TASK-CME-045)")
    link_parser.set_defaults(func=evidence_link_command)

    # evidence show
    show_parser = evidence_subparsers.add_parser(
        "show",
        help="Show full evidence details"
    )
    show_parser.add_argument("evidence_id", help="Evidence ID (e.g., EVIDENCE-001)")
    show_parser.set_defaults(func=evidence_show_command)
