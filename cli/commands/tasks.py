from typing import Any

"""
CLI commands for task management (ADR-003).

Usage:
    aibrain tasks list --project credentialmate              # List all tasks
    aibrain tasks list --project credentialmate --status pending  # Filter by status
    aibrain tasks add --project credentialmate --description "..." --file "..."
    aibrain tasks show TASK-ID --project credentialmate      # Show task details

Autonomous Task Registration:
- Tasks can be registered programmatically by agents
- Deduplication via SHA256 fingerprinting
- Auto-classification by task type
- Timestamped task IDs: {YYYYMMDD}-{HHMM}-{TYPE}-{SOURCE}-{SEQ}
"""

import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tasks.work_queue import WorkQueue


def tasks_list_command(args: Any) -> int:
    """List tasks in work queue."""
    project = args.project
    status_filter = args.status

    queue_path = Path(f"tasks/work_queue_{project}.json")
    if not queue_path.exists():
        print(f"\n❌ No work queue found for project: {project}")
        print(f"   Expected path: {queue_path}")
        return 1

    queue = WorkQueue.load(queue_path)
    stats = queue.get_stats()

    print(f"\n{'='*60}")
    print(f"📋 WORK QUEUE: {project}")
    print(f"{'='*60}")
    print(f"Total: {stats['total']} | Pending: {stats['pending']} | "
          f"In Progress: {stats['in_progress']} | "
          f"Complete: {stats['complete']} | Blocked: {stats['blocked']}")
    print(f"{'='*60}\n")

    # Priority icons
    priority_icons = {0: "🔴", 1: "🟡", 2: "🟢"}

    # Status icons
    status_icons = {
        "pending": "⏳",
        "in_progress": "🔄",
        "complete": "✅",
        "blocked": "🚫"
    }

    # Filter and display tasks
    displayed = 0
    for task in queue.features:
        if status_filter and task.status != status_filter:
            continue

        priority_icon = priority_icons.get(task.priority if task.priority is not None else -1, "⚪")
        status_icon = status_icons.get(task.status, "❓")
        priority_str = f"P{task.priority}" if task.priority is not None else "P?"

        print(f"{status_icon} [{priority_icon} {priority_str}] {task.id}")
        print(f"   {task.description[:60]}{'...' if len(task.description) > 60 else ''}")
        print(f"   File: {task.file}")
        if task.source:
            print(f"   Source: {task.source}")
        if task.discovered_by:
            print(f"   Discovered by: {task.discovered_by}")
        print()
        displayed += 1

    if displayed == 0:
        if status_filter:
            print(f"No tasks with status: {status_filter}")
        else:
            print("Work queue is empty.")

    print(f"\nView task details: aibrain tasks show <TASK-ID> --project {project}")

    return 0


def tasks_add_command(args: Any) -> int:
    """Add a task to the work queue."""
    project = args.project
    description = args.description
    file = args.file
    source = args.source
    priority = args.priority
    task_type = args.type

    queue_path = Path(f"tasks/work_queue_{project}.json")

    # Load or create queue
    if queue_path.exists():
        queue = WorkQueue.load(queue_path)
    else:
        print(f"\n📝 Creating new work queue for project: {project}")
        queue = WorkQueue(project=project, features=[])

    # Register the task
    task_id = queue.register_discovered_task(
        source=source,
        description=description,
        file=file,
        discovered_by="cli",
        priority=priority,
        task_type=task_type,
    )

    if task_id:
        # Save the queue
        queue.save(queue_path)

        # Get the task for display
        task = queue.features[-1]

        print(f"\n{'='*60}")
        print(f"✅ TASK CREATED")
        print(f"{'='*60}\n")
        print(f"ID: {task_id}")
        print(f"Description: {description}")
        print(f"File: {file}")
        print(f"Type: {task.type}")
        print(f"Agent: {task.agent}")
        print(f"Priority: P{task.priority}")
        print(f"Source: {task.source}")
        print(f"Fingerprint: {task.fingerprint}")
        print(f"\nQueue saved to: {queue_path}")
        print(f"{'='*60}\n")
        return 0
    else:
        print(f"\n{'='*60}")
        print(f"⚠️  TASK NOT CREATED (Duplicate)")
        print(f"{'='*60}\n")
        print(f"A similar task already exists in the queue.")
        print(f"File: {file}")
        print(f"Description: {description[:50]}...")
        print(f"\nUse 'aibrain tasks list --project {project}' to view existing tasks.")
        print(f"{'='*60}\n")
        return 0


def tasks_show_command(args: Any) -> int:
    """Show task details."""
    task_id = args.task_id
    project = args.project

    queue_path = Path(f"tasks/work_queue_{project}.json")
    if not queue_path.exists():
        print(f"\n❌ No work queue found for project: {project}")
        return 1

    queue = WorkQueue.load(queue_path)

    # Find the task
    task = None
    for t in queue.features:
        if t.id == task_id:
            task = t
            break

    if not task:
        print(f"\n❌ Task not found: {task_id}")
        print(f"   Use 'aibrain tasks list --project {project}' to see available tasks")
        return 1

    # Priority icons
    priority_icons = {0: "🔴 P0 (Critical)", 1: "🟡 P1 (Important)", 2: "🟢 P2 (Normal)"}
    priority_str = priority_icons.get(task.priority, f"⚪ P{task.priority}") if task.priority is not None else "⚪ P?"

    # Status icons
    status_icons = {
        "pending": "⏳ Pending",
        "in_progress": "🔄 In Progress",
        "complete": "✅ Complete",
        "blocked": "🚫 Blocked"
    }
    status_str = status_icons.get(task.status, task.status)

    print(f"\n{'='*60}")
    print(f"📋 TASK: {task.id}")
    print(f"{'='*60}\n")

    print(f"Status: {status_str}")
    print(f"Priority: {priority_str}")
    print(f"Type: {task.type}")
    print(f"Agent: {task.agent or 'Not assigned'}")
    print()

    print(f"Description:")
    print(f"   {task.description}")
    print()

    print(f"File: {task.file}")
    if task.tests:
        print(f"Tests: {', '.join(task.tests)}")
    print()

    print(f"Completion Promise: {task.completion_promise}")
    print(f"Max Iterations: {task.max_iterations}")
    print()

    if task.attempts > 0:
        print(f"Attempts: {task.attempts}")
        print(f"Last Attempt: {task.last_attempt}")
        if task.error:
            print(f"Last Error: {task.error}")
        print()

    if task.verification_verdict:
        print(f"Verification Verdict: {task.verification_verdict}")
        if task.files_actually_changed:
            print(f"Files Changed: {', '.join(task.files_actually_changed)}")
        print()

    # ADR-003 metadata
    if task.source or task.discovered_by or task.fingerprint:
        print(f"--- Discovery Metadata (ADR-003) ---")
        if task.source:
            print(f"Source: {task.source}")
        if task.discovered_by:
            print(f"Discovered By: {task.discovered_by}")
        if task.fingerprint:
            print(f"Fingerprint: {task.fingerprint}")
        print()

    if task.completed_at:
        print(f"Completed At: {task.completed_at}")

    print(f"{'='*60}\n")

    return 0


def setup_parser(subparsers: Any) -> None:
    """Setup argparse for tasks commands."""

    # Main 'tasks' command
    tasks_parser = subparsers.add_parser(
        "tasks",
        help="Manage work queue tasks",
        description="List, add, and show tasks in the work queue (ADR-003)"
    )

    tasks_subparsers = tasks_parser.add_subparsers(
        dest='tasks_command',
        help='Tasks subcommand'
    )

    # tasks list
    list_parser = tasks_subparsers.add_parser(
        "list",
        help="List tasks in work queue"
    )
    list_parser.add_argument(
        "--project",
        required=True,
        help="Project name (e.g., credentialmate, karematch)"
    )
    list_parser.add_argument(
        "--status",
        choices=["pending", "in_progress", "complete", "blocked"],
        help="Filter by status"
    )
    list_parser.set_defaults(func=tasks_list_command)

    # tasks add
    add_parser = tasks_subparsers.add_parser(
        "add",
        help="Add a task to the work queue"
    )
    add_parser.add_argument(
        "--project",
        required=True,
        help="Project name (e.g., credentialmate, karematch)"
    )
    add_parser.add_argument(
        "--description",
        required=True,
        help="Task description"
    )
    add_parser.add_argument(
        "--file",
        required=True,
        help="Target file path"
    )
    add_parser.add_argument(
        "--source",
        default="manual",
        help="Task source (default: manual)"
    )
    add_parser.add_argument(
        "--priority",
        type=int,
        choices=[0, 1, 2],
        help="Priority: 0=P0 (critical), 1=P1 (important), 2=P2 (normal)"
    )
    add_parser.add_argument(
        "--type",
        choices=["bugfix", "feature", "test", "refactor", "codequality"],
        help="Task type (auto-inferred if not specified)"
    )
    add_parser.set_defaults(func=tasks_add_command)

    # tasks show
    show_parser = tasks_subparsers.add_parser(
        "show",
        help="Show task details"
    )
    show_parser.add_argument(
        "task_id",
        help="Task ID"
    )
    show_parser.add_argument(
        "--project",
        required=True,
        help="Project name"
    )
    show_parser.set_defaults(func=tasks_show_command)
