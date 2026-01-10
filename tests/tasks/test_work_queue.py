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


# =============================================================================
# ADR-003: Autonomous Task Registration Tests
# =============================================================================

class TestTaskRegistration:
    """Tests for autonomous task registration (ADR-003)."""

    def test_register_task_creates_task(self):
        """Basic task registration works."""
        queue = WorkQueue(project="test", features=[])

        task_id = queue.register_discovered_task(
            source="ADR-002",
            description="Fix cycle calculation",
            file="app/calculators/cycle.py",
            discovered_by="app-advisor",
        )

        assert task_id is not None
        assert len(queue.features) == 1

        task = queue.features[0]
        assert task.id == task_id
        assert task.description == "Fix cycle calculation"
        assert task.file == "app/calculators/cycle.py"
        assert task.status == "pending"
        assert task.source == "ADR-002"
        assert task.discovered_by == "app-advisor"
        assert task.fingerprint is not None

    def test_duplicate_task_returns_none(self):
        """Duplicate registration is rejected."""
        queue = WorkQueue(project="test", features=[])

        task_id_1 = queue.register_discovered_task(
            source="ADR-002",
            description="Fix cycle calculation",
            file="app/calculators/cycle.py",
            discovered_by="app-advisor",
        )

        task_id_2 = queue.register_discovered_task(
            source="manual",
            description="Fix cycle calculation",  # Same description
            file="app/calculators/cycle.py",      # Same file
            discovered_by="cli",
        )

        assert task_id_1 is not None
        assert task_id_2 is None  # Duplicate
        assert len(queue.features) == 1

    def test_different_file_same_description_allowed(self):
        """Same description in different files is NOT duplicate."""
        queue = WorkQueue(project="test", features=[])

        task_id_1 = queue.register_discovered_task(
            source="manual",
            description="Add logging",
            file="app/auth.py",
            discovered_by="cli",
        )

        task_id_2 = queue.register_discovered_task(
            source="manual",
            description="Add logging",
            file="app/payments.py",  # Different file
            discovered_by="cli",
        )

        assert task_id_1 is not None
        assert task_id_2 is not None
        assert len(queue.features) == 2

    def test_auto_classification_bugfix(self):
        """Task type is auto-inferred as bugfix."""
        queue = WorkQueue(project="test", features=[])

        queue.register_discovered_task(
            source="test",
            description="Fix authentication bug",
            file="app/auth.py",
            discovered_by="test",
        )

        task = queue.features[-1]
        assert task.type == "bugfix"
        assert task.completion_promise == "BUGFIX_COMPLETE"
        assert task.agent == "BugFix"

    def test_auto_classification_feature(self):
        """Task type is auto-inferred as feature."""
        queue = WorkQueue(project="test", features=[])

        queue.register_discovered_task(
            source="test",
            description="Add user profile feature",
            file="app/profile.py",
            discovered_by="test",
        )

        task = queue.features[-1]
        assert task.type == "feature"
        assert task.completion_promise == "FEATURE_COMPLETE"
        assert task.agent == "FeatureBuilder"

    def test_auto_classification_test(self):
        """Task type is auto-inferred as test."""
        queue = WorkQueue(project="test", features=[])

        queue.register_discovered_task(
            source="test",
            description="Write tests for authentication",
            file="tests/auth_test.py",
            discovered_by="test",
        )

        task = queue.features[-1]
        assert task.type == "test"
        assert task.completion_promise == "TESTS_COMPLETE"
        assert task.agent == "TestWriter"

    def test_priority_p0_for_auth_path(self):
        """Priority is P0 for auth paths."""
        queue = WorkQueue(project="test", features=[])

        queue.register_discovered_task(
            source="test",
            description="Fix issue",
            file="app/auth/session.py",
            discovered_by="test",
        )

        assert queue.features[-1].priority == 0

    def test_priority_p0_for_security_keyword(self):
        """Priority is P0 for security keywords."""
        queue = WorkQueue(project="test", features=[])

        queue.register_discovered_task(
            source="test",
            description="Fix security vulnerability",
            file="app/utils/helpers.py",
            discovered_by="test",
        )

        assert queue.features[-1].priority == 0

    def test_priority_p1_for_bugfix(self):
        """Priority is P1 for regular bugfix."""
        queue = WorkQueue(project="test", features=[])

        queue.register_discovered_task(
            source="test",
            description="Fix display issue",
            file="app/utils/helpers.py",
            discovered_by="test",
        )

        assert queue.features[-1].priority == 1

    def test_priority_p2_for_refactor(self):
        """Priority is P2 for refactoring."""
        queue = WorkQueue(project="test", features=[])

        queue.register_discovered_task(
            source="test",
            description="Refactor utility functions",
            file="app/utils/helpers.py",
            discovered_by="test",
        )

        assert queue.features[-1].priority == 2

    def test_task_id_format(self):
        """Task ID follows timestamped format."""
        queue = WorkQueue(project="test", features=[])

        task_id = queue.register_discovered_task(
            source="ADR-003",
            description="Fix bug",
            file="app/test.py",
            discovered_by="cli",
        )

        # Format: {YYYYMMDD}-{HHMM}-{TYPE}-{SOURCE}-{SEQ}
        parts = task_id.split("-")
        assert len(parts) == 5

        # Date part should be 8 digits
        assert len(parts[0]) == 8
        assert parts[0].isdigit()

        # Time part should be 4 digits
        assert len(parts[1]) == 4
        assert parts[1].isdigit()

        # Type prefix
        assert parts[2] == "BUG"

        # Source (first 6 chars alphanumeric)
        assert parts[3] == "ADR003"

        # Sequence number (3 digits)
        assert len(parts[4]) == 3
        assert parts[4].isdigit()

    def test_sequence_increments(self):
        """Sequence number increments with each task."""
        queue = WorkQueue(project="test", features=[])

        task_id_1 = queue.register_discovered_task(
            source="test",
            description="First task",
            file="app/a.py",
            discovered_by="cli",
        )

        task_id_2 = queue.register_discovered_task(
            source="test",
            description="Second task",
            file="app/b.py",
            discovered_by="cli",
        )

        # Extract sequence numbers
        seq_1 = int(task_id_1.split("-")[-1])
        seq_2 = int(task_id_2.split("-")[-1])

        assert seq_2 == seq_1 + 1

    def test_fingerprint_persistence(self, tmp_path):
        """Fingerprints are saved and loaded correctly."""
        queue_file = tmp_path / "test_queue.json"

        # Create queue and register task
        queue = WorkQueue(project="test", features=[])
        queue.register_discovered_task(
            source="test",
            description="Test task",
            file="app/test.py",
            discovered_by="cli",
        )

        fingerprint = queue.features[0].fingerprint
        assert len(queue.fingerprints) == 1

        # Save
        queue.save(queue_file)

        # Load
        loaded_queue = WorkQueue.load(queue_file)

        assert len(loaded_queue.fingerprints) == 1
        assert fingerprint in loaded_queue.fingerprints

        # Try to add duplicate
        dup_id = loaded_queue.register_discovered_task(
            source="test",
            description="Test task",  # Same
            file="app/test.py",       # Same
            discovered_by="cli",
        )

        assert dup_id is None  # Should be rejected

    def test_infer_test_files_typescript(self):
        """Test file inference for TypeScript."""
        queue = WorkQueue(project="test", features=[])

        # Path must contain /src/ for inference to work
        queue.register_discovered_task(
            source="test",
            description="Fix issue",
            file="apps/frontend/src/components/Button.tsx",
            discovered_by="cli",
        )

        task = queue.features[-1]
        assert len(task.tests) == 1
        # Test file path should contain tests/ directory and .test.tsx extension
        assert "/tests/" in task.tests[0]
        assert ".test.tsx" in task.tests[0]

    def test_infer_test_files_python(self):
        """Test file inference for Python."""
        queue = WorkQueue(project="test", features=[])

        # Path must contain /app/ or /src/ for inference to work
        queue.register_discovered_task(
            source="test",
            description="Fix issue",
            file="backend/app/services/auth.py",
            discovered_by="cli",
        )

        task = queue.features[-1]
        assert len(task.tests) == 1
        assert "_test.py" in task.tests[0]

    def test_explicit_priority_overrides_auto(self):
        """Explicit priority overrides auto-computed."""
        queue = WorkQueue(project="test", features=[])

        queue.register_discovered_task(
            source="test",
            description="Security vulnerability",  # Would be P0
            file="app/utils/helpers.py",
            discovered_by="cli",
            priority=2,  # Explicitly set P2
        )

        assert queue.features[-1].priority == 2

    def test_explicit_type_overrides_auto(self):
        """Explicit task type overrides auto-inferred."""
        queue = WorkQueue(project="test", features=[])

        queue.register_discovered_task(
            source="test",
            description="Fix bug",  # Would be bugfix
            file="app/test.py",
            discovered_by="cli",
            task_type="feature",  # Explicitly set feature
        )

        task = queue.features[-1]
        assert task.type == "feature"
        assert task.agent == "FeatureBuilder"
