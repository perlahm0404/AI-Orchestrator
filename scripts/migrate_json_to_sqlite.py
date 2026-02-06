"""
Migrate existing JSON work queues to SQLite format.

Converts tasks/work_queue_*.json files to SQLite database with
epic → feature → task hierarchy.

Reference: KO-aio-002 (SQLite persistence)
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict


def migrate_work_queue(
    project: str,
    dry_run: bool = False,
    backup: bool = True,
    auto_group_features: bool = False,
    create_epic: bool = False
) -> Dict[str, Any]:
    """
    Migrate JSON work queue to SQLite.

    Args:
        project: Project name
        dry_run: If True, don't actually migrate (validation only)
        backup: Create backup of JSON file before migration
        auto_group_features: Group tasks into features by file path
        create_epic: Create epic for the project

    Returns:
        Migration result summary

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    # Locate JSON file
    json_path = Path.cwd() / "tasks" / f"work_queue_{project}.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Work queue not found: {json_path}")

    # Read JSON
    with open(json_path) as f:
        data = json.load(f)

    tasks = data.get("tasks", [])

    # Plan migration
    result = {
        "tasks_found": len(tasks),
        "tasks_migrated": 0,
        "features_created": 0,
        "epic_created": False,
        "epics_to_create": 1 if create_epic else 0,
        "features_to_create": 0,
        "dry_run": dry_run
    }

    if dry_run:
        # Dry run: just report what would be done
        if auto_group_features:
            feature_groups = _group_tasks_by_file(tasks)
            result["features_to_create"] = len(feature_groups)

        return result

    # Backup JSON file
    if backup:
        backup_path = json_path.parent / f"{json_path.stem}.backup.json"
        shutil.copy(json_path, backup_path)

    # Initialize WorkQueueManager
    from orchestration.queue_manager import WorkQueueManager

    manager = WorkQueueManager(project=project, use_db=True)

    # Create epic if requested
    epic_id = None
    if create_epic:
        epic_id = manager.add_epic(
            name=f"{project.title()} Migration",
            description=f"Migrated from JSON work queue"
        )
        result["epic_created"] = True

    # Group tasks into features
    if auto_group_features:
        feature_groups = _group_tasks_by_file(tasks)
        feature_map = {}

        for group_key, group_tasks in feature_groups.items():
            # Create feature for this group
            feature_name = group_key if group_key else "Ungrouped Tasks"

            # Determine priority (use highest priority task in group)
            priorities = [t.get("priority", 2) for t in group_tasks]
            priority = min(priorities) if priorities else 2

            feature_id = manager.add_feature(
                epic_id=epic_id,
                name=feature_name,
                priority=priority
            )
            feature_map[group_key] = feature_id
            result["features_created"] += 1

        # Migrate tasks
        for task in tasks:
            group_key = _get_task_group_key(task)
            feature_id = feature_map.get(group_key)

            if not feature_id:
                # Fallback: create default feature
                if "default" not in feature_map:
                    default_feature = manager.add_feature(
                        epic_id=epic_id,
                        name="Default Feature"
                    )
                    feature_map["default"] = default_feature
                    result["features_created"] += 1

                feature_id = feature_map["default"]

            _migrate_task(manager, task, feature_id)
            result["tasks_migrated"] += 1

    else:
        # No feature grouping - create one default feature
        default_feature = manager.add_feature(
            epic_id=epic_id,
            name=f"{project.title()} Tasks",
            description="All migrated tasks"
        )
        result["features_created"] = 1

        # Migrate all tasks to default feature
        for task in tasks:
            priority = task.get("priority", 2)
            _migrate_task(manager, task, default_feature, priority=priority)
            result["tasks_migrated"] += 1

    return result


def _group_tasks_by_file(tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group tasks by file path.

    Tasks with same directory become a feature.
    """
    groups = defaultdict(list)

    for task in tasks:
        file_path = task.get("file", "")

        if file_path:
            # Extract directory path
            parts = file_path.split("/")
            if len(parts) > 1:
                # Use first 2 path components as group key
                group_key = "/".join(parts[:2])
            else:
                group_key = "Root"
        else:
            group_key = "Ungrouped"

        groups[group_key].append(task)

    return dict(groups)


def _get_task_group_key(task: Dict[str, Any]) -> str:
    """Get group key for a task."""
    file_path = task.get("file", "")

    if file_path:
        parts = file_path.split("/")
        if len(parts) > 1:
            return "/".join(parts[:2])
        else:
            return "Root"
    else:
        return "Ungrouped"


def _migrate_task(
    manager,
    task: Dict[str, Any],
    feature_id: str,
    priority: Optional[int] = None
) -> str:
    """
    Migrate a single task to SQLite.

    Preserves: description, status, priority, retry_budget, retries_used
    """
    # Extract task data
    description = task.get("description", "")
    status = task.get("status", "pending")
    task_priority = priority if priority is not None else task.get("priority", 2)
    retry_budget = task.get("retry_budget", 15)
    retries_used = task.get("attempts", 0)

    # Add task
    task_id = manager.add_task(
        feature_id=feature_id,
        description=description,
        status=status,
        priority=task_priority,
        retry_budget=retry_budget,
        retries_used=retries_used
    )

    return task_id


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate JSON work queue to SQLite"
    )
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually migrating"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup of JSON file"
    )
    parser.add_argument(
        "--auto-group-features",
        action="store_true",
        help="Automatically group tasks into features by file path"
    )
    parser.add_argument(
        "--create-epic",
        action="store_true",
        help="Create epic for the project"
    )

    args = parser.parse_args()

    # Run migration
    result = migrate_work_queue(
        project=args.project,
        dry_run=args.dry_run,
        backup=not args.no_backup,
        auto_group_features=args.auto_group_features,
        create_epic=args.create_epic
    )

    # Print results
    print("\n" + "=" * 60)
    print("Migration Results")
    print("=" * 60)

    if result["dry_run"]:
        print("\n[DRY RUN - No changes made]")

    print(f"\nTasks found: {result['tasks_found']}")

    if not result["dry_run"]:
        print(f"Tasks migrated: {result['tasks_migrated']}")
        print(f"Features created: {result['features_created']}")
        print(f"Epic created: {'Yes' if result['epic_created'] else 'No'}")
        print("\n✅ Migration complete!")
    else:
        print(f"Epics to create: {result['epics_to_create']}")
        print(f"Features to create: {result['features_to_create']}")
        print("\nRun without --dry-run to perform migration.")

    print("=" * 60 + "\n")
