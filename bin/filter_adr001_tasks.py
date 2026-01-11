#!/usr/bin/env python3
"""
Filter ADR-001 tasks to only include those that can be autonomously implemented.

Remove manual infrastructure tasks:
- TASK-ADR001-001: Database migration (requires manual Alembic setup)
- TASK-ADR001-003: S3 bucket provisioning (requires AWS account access)
- TASK-ADR001-015: Tests (will be created during implementation)

Keep code implementation tasks that agents can complete.
"""

import json
from pathlib import Path


def filter_implementable_tasks():
    """Filter work queue to only include agent-implementable tasks."""

    queue_path = Path(__file__).parent / "tasks" / "work_queue_credentialmate_features.json"

    with open(queue_path, 'r') as f:
        data = json.load(f)

    # Manual tasks that require human intervention
    manual_tasks = [
        "TASK-ADR001-001",  # Database migration
        "TASK-ADR001-003",  # S3 bucket provisioning (AWS)
    ]

    # Filter out manual tasks
    original_count = len(data["features"])
    data["features"] = [f for f in data["features"] if f["id"] not in manual_tasks]
    filtered_count = len(data["features"])

    # Update summary
    data["sequence"] = filtered_count

    # Save filtered queue
    with open(queue_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Filtered work queue")
    print(f"   Original tasks: {original_count}")
    print(f"   Filtered tasks: {filtered_count}")
    print(f"   Removed: {original_count - filtered_count}")
    print()

    print("Removed tasks (require manual setup):")
    for task_id in manual_tasks:
        print(f"   - {task_id}")
    print()

    print("Remaining tasks (agent-implementable):")
    for feature in data["features"]:
        agent = feature.get("agent", "unknown")
        print(f"   - {feature['id']}: {agent}")
    print()

    return data


if __name__ == "__main__":
    filter_implementable_tasks()
