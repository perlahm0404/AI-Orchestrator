"""
Work Queue System - Simple JSON-based task queue

Replaces complex orchestration with Anthropic's proven pattern:
- Tasks stored in work_queue.json
- Simple get_next() interface
- Status tracking: pending, in_progress, complete, blocked
"""

import json
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass, asdict
from datetime import datetime


TaskStatus = Literal["pending", "in_progress", "complete", "blocked"]


@dataclass
class Task:
    """Individual task in the work queue"""
    id: str
    description: str
    file: str
    status: TaskStatus
    tests: list[str]
    passes: bool
    error: Optional[str] = None
    attempts: int = 0
    last_attempt: Optional[str] = None
    completed_at: Optional[str] = None
    # Wiggum integration fields
    completion_promise: Optional[str] = None  # Expected completion signal (e.g., "BUGFIX_COMPLETE")
    max_iterations: Optional[int] = None      # Override default iteration budget per task
    # Verification audit trail
    verification_verdict: Optional[str] = None  # "PASS", "FAIL", "BLOCKED", or None
    files_actually_changed: Optional[list[str]] = None  # What files were actually modified


@dataclass
class WorkQueue:
    """Work queue containing tasks for a project"""
    project: str
    features: list[Task]

    @classmethod
    def load(cls, path: Path) -> "WorkQueue":
        """Load work queue from JSON file"""
        if not path.exists():
            raise FileNotFoundError(f"Work queue not found: {path}")

        data = json.loads(path.read_text())
        features = [Task(**f) for f in data["features"]]
        return cls(project=data["project"], features=features)

    def save(self, path: Path) -> None:
        """Save work queue to JSON file"""
        data = {
            "project": self.project,
            "features": [asdict(task) for task in self.features]
        }
        path.write_text(json.dumps(data, indent=2))

    def get_next_pending(self) -> Optional[Task]:
        """Get next pending task"""
        for task in self.features:
            if task.status == "pending":
                return task
        return None

    def get_in_progress(self) -> Optional[Task]:
        """Get currently in-progress task"""
        for task in self.features:
            if task.status == "in_progress":
                return task
        return None

    def mark_in_progress(self, task_id: str) -> None:
        """Mark task as in progress"""
        for task in self.features:
            if task.id == task_id:
                task.status = "in_progress"
                task.attempts += 1
                task.last_attempt = datetime.now().isoformat()
                break

    def mark_complete(self, task_id: str, verdict: Optional[str] = None, files_changed: Optional[list[str]] = None) -> None:
        """
        Mark task as complete with verification verdict.

        Args:
            task_id: Task identifier
            verdict: Verification verdict ("PASS", "FAIL", "BLOCKED", or None)
            files_changed: List of files that were actually modified
        """
        for task in self.features:
            if task.id == task_id:
                task.status = "complete"
                task.passes = (verdict == "PASS") if verdict else True
                task.verification_verdict = verdict
                task.files_actually_changed = files_changed
                task.completed_at = datetime.now().isoformat()
                break

    def mark_blocked(self, task_id: str, error: str) -> None:
        """Mark task as blocked"""
        for task in self.features:
            if task.id == task_id:
                task.status = "blocked"
                task.error = error
                break

    def update_progress(self, task_id: str, error: Optional[str] = None) -> None:
        """Update task progress (failed attempt but can retry)"""
        for task in self.features:
            if task.id == task_id:
                task.error = error
                # Keep status as in_progress so it can retry
                break

    def get_stats(self) -> dict[str, int]:
        """Get queue statistics"""
        return {
            "total": len(self.features),
            "pending": sum(1 for t in self.features if t.status == "pending"),
            "in_progress": sum(1 for t in self.features if t.status == "in_progress"),
            "complete": sum(1 for t in self.features if t.status == "complete"),
            "blocked": sum(1 for t in self.features if t.status == "blocked"),
        }

    def validate_tasks(self, project_dir: Path) -> list[str]:
        """
        Validate that task file paths and test files exist.

        Args:
            project_dir: Root directory of the project

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []

        for task in self.features:
            # Check if target file exists
            file_path = project_dir / task.file
            if not file_path.exists():
                errors.append(f"Task {task.id}: Target file not found: {task.file}")

            # Check if test files exist
            for test_file in task.tests:
                test_path = project_dir / test_file
                if not test_path.exists():
                    errors.append(f"Task {task.id}: Test file not found: {test_file}")

        return errors
