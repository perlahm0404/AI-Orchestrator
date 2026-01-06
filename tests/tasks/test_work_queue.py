"""Tests for work queue system"""

import json
import pytest
from pathlib import Path
from tasks.work_queue import WorkQueue, Task


def test_load_work_queue(tmp_path):
    """Test loading work queue from JSON"""
    queue_file = tmp_path / "test_queue.json"
    queue_data = {
        "project": "test_project",
        "features": [
            {
                "id": "TEST-001",
                "description": "Test task",
                "file": "src/test.ts",
                "status": "pending",
                "tests": ["tests/test.test.ts"],
                "passes": False,
                "error": None,
                "attempts": 0,
                "last_attempt": None,
                "completed_at": None
            }
        ]
    }
    queue_file.write_text(json.dumps(queue_data))

    queue = WorkQueue.load(queue_file)
    assert queue.project == "test_project"
    assert len(queue.features) == 1
    assert queue.features[0].id == "TEST-001"


def test_get_next_pending():
    """Test getting next pending task"""
    queue = WorkQueue(
        project="test",
        features=[
            Task(
                id="T1",
                description="First",
                file="a.ts",
                status="complete",
                tests=[],
                passes=True
            ),
            Task(
                id="T2",
                description="Second",
                file="b.ts",
                status="pending",
                tests=[],
                passes=False
            ),
            Task(
                id="T3",
                description="Third",
                file="c.ts",
                status="pending",
                tests=[],
                passes=False
            )
        ]
    )

    next_task = queue.get_next_pending()
    assert next_task is not None
    assert next_task.id == "T2"


def test_mark_complete():
    """Test marking task as complete"""
    task = Task(
        id="T1",
        description="Test",
        file="test.ts",
        status="in_progress",
        tests=[],
        passes=False
    )
    queue = WorkQueue(project="test", features=[task])

    queue.mark_complete("T1")

    assert task.status == "complete"
    assert task.passes is True
    assert task.completed_at is not None


def test_get_stats():
    """Test queue statistics"""
    queue = WorkQueue(
        project="test",
        features=[
            Task(id="T1", description="1", file="a.ts", status="pending", tests=[], passes=False),
            Task(id="T2", description="2", file="b.ts", status="in_progress", tests=[], passes=False),
            Task(id="T3", description="3", file="c.ts", status="complete", tests=[], passes=True),
            Task(id="T4", description="4", file="d.ts", status="blocked", tests=[], passes=False),
        ]
    )

    stats = queue.get_stats()
    assert stats["total"] == 4
    assert stats["pending"] == 1
    assert stats["in_progress"] == 1
    assert stats["complete"] == 1
    assert stats["blocked"] == 1
