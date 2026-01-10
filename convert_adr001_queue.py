#!/usr/bin/env python3
"""
Convert ADR-001 task queue to WorkQueue format.

ADR-001 uses "tasks" key with detailed ADR structure.
WorkQueue expects "features" key with simpler Task dataclass format.
"""

import json
from pathlib import Path


def convert_adr_to_work_queue():
    """Convert ADR-001 queue to WorkQueue format."""

    # Read ADR-001 queue
    adr_queue_path = Path(__file__).parent / "tasks" / "work_queue_credentialmate_features.json"

    with open(adr_queue_path, 'r') as f:
        adr_data = json.load(f)

    # Convert tasks to features format
    features = []

    for task in adr_data["tasks"]:
        # Convert to WorkQueue Task format
        feature = {
            "id": task["id"],
            "description": f"{task['title']}\n\n{task['description']}",
            "file": task["files"][0] if task.get("files") else "",
            "status": task["status"],  # pending, in_progress, completed, blocked
            "tests": [],  # Will be determined during implementation
            "passes": False,
            "error": None,
            "attempts": task.get("iterations", 0),
            "last_attempt": task.get("started_at"),
            "completed_at": task.get("completed_at"),

            # Wiggum fields
            "completion_promise": task.get("completion_promise", "FEATURE_COMPLETE"),
            "max_iterations": task.get("max_iterations", 50),

            # Verification
            "verification_verdict": None,
            "files_actually_changed": None,

            # Priority
            "priority": 0 if task["priority"] == "P0" else (1 if task["priority"] == "P1" else 2),
            "bug_count": None,
            "is_new": None,

            # Feature development fields
            "type": task["type"],  # migration, feature, test
            "branch": f"feature/adr-001-report-generation",
            "agent": task.get("agent", "FeatureBuilder"),
            "requires_approval": None,

            # Source tracking
            "source": "ADR-001",
            "discovered_by": "app-advisor",
            "fingerprint": None,
        }

        features.append(feature)

    # Create WorkQueue-compatible format
    work_queue = {
        "project": "credentialmate",
        "features": features,
        "sequence": len(features),
        "fingerprints": []
    }

    # Save to new file
    output_path = Path(__file__).parent / "tasks" / "work_queue_credentialmate_features_converted.json"

    with open(output_path, 'w') as f:
        json.dump(work_queue, f, indent=2)

    print(f"✅ Converted {len(features)} tasks from ADR-001 queue")
    print(f"📝 Saved to: {output_path}")
    print()
    print("Summary:")
    print(f"  Total tasks: {len(features)}")
    print(f"  Pending: {sum(1 for f in features if f['status'] == 'pending')}")
    print(f"  In progress: {sum(1 for f in features if f['status'] == 'in_progress')}")
    print(f"  Completed: {sum(1 for f in features if f['status'] == 'completed')}")
    print()

    # Show task breakdown by type
    types = {}
    for f in features:
        t = f["type"]
        types[t] = types.get(t, 0) + 1

    print("Task types:")
    for task_type, count in types.items():
        print(f"  {task_type}: {count}")

    return output_path


if __name__ == "__main__":
    convert_adr_to_work_queue()
