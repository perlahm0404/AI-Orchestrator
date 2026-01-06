"""
CLI command for automated bug discovery and work queue generation.

Usage:
    aibrain discover-bugs --project karematch
    aibrain discover-bugs --project karematch --sources lint,typecheck
    aibrain discover-bugs --project karematch --reset-baseline
    aibrain discover-bugs --project karematch --dry-run

This command:
- Scans codebase for bugs (lint, type, test, guardrails)
- Compares with baseline to detect new regressions
- Generates work queue tasks grouped by file
- Prioritizes by user impact (P0/P1/P2)
"""

import argparse
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from discovery import BugScanner, BaselineManager, TaskGenerator
from tasks.work_queue import WorkQueue
from adapters import get_adapter


def discover_bugs_command(args):
    """Execute bug discovery workflow."""
    project = args.project
    sources_str = args.sources
    reset_baseline = args.reset_baseline
    dry_run = args.dry_run

    print(f"\n{'='*80}")
    print(f"🔍 Bug Discovery - {project}")
    print(f"{'='*80}\n")

    # Load project adapter
    adapter = get_adapter(project)
    app_context = adapter.get_context()
    project_path = Path(app_context.project_path)
    language = app_context.language  # Get language from adapter

    # Get scanner-specific commands if available
    scanner_commands = getattr(adapter, 'scanner_commands', None) or adapter.config.get('scanner_commands', {})

    # Parse sources
    source_list = [s.strip() for s in sources_str.split(',')]

    # Step 1: Scan for bugs
    print("📊 Step 1: Scanning codebase...\n")
    scanner = BugScanner(project_path, project, language=language, scanner_commands=scanner_commands)

    try:
        scan_result = scanner.scan(source_list)
    except Exception as e:
        print(f"\n❌ Scan failed: {e}")
        return 1

    print(f"\n✅ Scan complete:")
    print(f"   Lint errors: {len(scan_result.lint_errors)}")
    print(f"   Type errors: {len(scan_result.type_errors)}")
    print(f"   Test failures: {len(scan_result.test_failures)}")
    print(f"   Guardrail violations: {len(scan_result.guardrail_violations)}")
    print(f"   Total: {scan_result.total_errors()}\n")

    # Step 2: Compare with baseline
    print("📊 Step 2: Comparing with baseline...\n")
    baseline_mgr = BaselineManager(project)

    if reset_baseline:
        baseline_mgr.create_baseline(scan_result)
        print("✅ Baseline reset\n")
        return 0

    new_bugs, baseline_bugs = baseline_mgr.compare_with_baseline(scan_result)

    # Step 3: Generate tasks
    print("\n📊 Step 3: Generating tasks...\n")
    task_gen = TaskGenerator(project)
    tasks = task_gen.generate_tasks(scan_result, new_bugs, baseline_bugs)

    print(f"✅ Generated {len(tasks)} tasks:")
    print(f"   P0 (blocks users): {sum(1 for t in tasks if t.priority == 0)}")
    print(f"   P1 (degrades UX): {sum(1 for t in tasks if t.priority == 1)}")
    print(f"   P2 (tech debt): {sum(1 for t in tasks if t.priority == 2)}\n")

    # Step 4: Display task summary
    print("📋 Task Summary (first 10):\n")
    for task in tasks[:10]:
        priority_label = ['P0', 'P1', 'P2'][task.priority] if task.priority is not None else 'P?'
        new_flag = '🆕' if task.is_new else '  '
        print(f"  {new_flag} [{priority_label}] {task.id}: {task.description}")

    if len(tasks) > 10:
        print(f"\n  ... and {len(tasks) - 10} more\n")

    # Step 5: Update work queue (unless dry run)
    if dry_run:
        print("\n🔍 DRY RUN - No changes made to work queue\n")
        return 0

    print("\n📊 Step 4: Updating work queue...\n")

    # Load or create work queue (project-specific)
    queue_path = Path(f'tasks/work_queue_{project}.json')

    if queue_path.exists():
        queue = WorkQueue.load(queue_path)

        # Ask user for merge strategy
        print(f"⚠️  Existing work queue has {len(queue.features)} tasks\n")
        print("Merge strategy:")
        print("  [A] Append (add new tasks to end)")
        print("  [R] Replace (clear existing and use new tasks)")
        print("  [M] Merge (deduplicate by file path)")

        choice = input("\nYour choice [A/R/M]: ").strip().upper()

        if choice == 'A':
            queue.features.extend(tasks)
            print(f"   Appended {len(tasks)} tasks")
        elif choice == 'R':
            queue.features = tasks
            print(f"   Replaced with {len(tasks)} tasks")
        elif choice == 'M':
            existing_files = {t.file for t in queue.features}
            new_tasks = [t for t in tasks if t.file not in existing_files]
            queue.features.extend(new_tasks)
            print(f"   Merged: {len(new_tasks)} new files, skipped {len(tasks) - len(new_tasks)} duplicates")
        else:
            print("   Invalid choice, aborting")
            return 1
    else:
        # Create new work queue
        queue = WorkQueue(project=project, features=tasks)
        print(f"   Created new work queue with {len(tasks)} tasks")

    # Save work queue
    queue.save(queue_path)

    stats = queue.get_stats()
    print(f"\n✅ Work queue updated: {queue_path}")
    print(f"   Total tasks: {stats['total']}")
    print(f"   Pending: {stats['pending']}")
    print(f"\n🚀 Ready to run: python autonomous_loop.py --project {project}\n")

    return 0


def setup_parser(subparsers):
    """Setup argparse for discover-bugs command."""
    parser = subparsers.add_parser(
        "discover-bugs",
        help="Scan codebase and generate work queue tasks",
        description="""
Automated bug discovery and work queue generation.

Scans project for lint/type/test/guardrail violations and automatically
generates tasks in work_queue.json for autonomous agent execution.

First run creates a baseline snapshot. Subsequent runs flag new bugs
as high priority (P0) and baseline bugs as lower priority (P1-P2).

Example:
    aibrain discover-bugs --project karematch
    aibrain discover-bugs --project karematch --sources lint,typecheck
    aibrain discover-bugs --project karematch --dry-run
    aibrain discover-bugs --project karematch --reset-baseline
        """
    )

    parser.add_argument(
        "--project",
        required=True,
        choices=["karematch", "credentialmate"],
        help="Project to scan"
    )

    parser.add_argument(
        "--sources",
        default="lint,typecheck,test,guardrails",
        help="Bug sources to scan (comma-separated, default: all)"
    )

    parser.add_argument(
        "--reset-baseline",
        action="store_true",
        help="Reset baseline snapshot (all bugs become baseline)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show tasks without modifying work queue"
    )

    parser.set_defaults(func=discover_bugs_command)
