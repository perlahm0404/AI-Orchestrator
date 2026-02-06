"""
Test WorkQueueManager for hybrid SQLite/JSON work queue persistence.

TDD: These tests are written BEFORE the implementation.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project directory structure."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    db_dir = tmp_path / ".aibrain"
    db_dir.mkdir()
    return tmp_path


@pytest.fixture
def sample_json_queue(temp_project_dir):
    """Create sample JSON work queue file."""
    queue_data = {
        "project": "test-project",
        "tasks": [
            {
                "id": "TASK-001",
                "description": "Fix bug in login",
                "status": "pending",
                "priority": 0,
                "attempts": 0
            },
            {
                "id": "TASK-002",
                "description": "Add tests for auth",
                "status": "in_progress",
                "priority": 1,
                "attempts": 2
            }
        ]
    }

    json_path = temp_project_dir / "tasks" / "work_queue_test-project.json"
    with open(json_path, "w") as f:
        json.dump(queue_data, f, indent=2)

    return json_path


class TestQueueManagerConstruction:
    """Test WorkQueueManager initialization."""

    def test_create_with_sqlite_mode(self, temp_project_dir, monkeypatch):
        """Should create manager with SQLite backend."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        assert manager.project == "test"
        assert manager.use_db is True
        assert manager.db_path.exists()

    def test_create_with_json_mode(self, temp_project_dir, sample_json_queue, monkeypatch):
        """Should create manager with JSON backend."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test-project", use_db=False)

        assert manager.project == "test-project"
        assert manager.use_db is False
        assert manager.json_path.exists()

    def test_auto_initialize_database(self, temp_project_dir, monkeypatch):
        """Should auto-create schema on first use."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        # Check that tables exist
        with manager._get_session() as session:
            from orchestration.models import Epic
            # Query should not fail
            session.query(Epic).all()


class TestTaskOperations:
    """Test core task CRUD operations."""

    def test_add_task_sqlite_mode(self, temp_project_dir, monkeypatch):
        """Should add task to SQLite database."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        task_id = manager.add_task(
            feature_id="FEAT-001",
            description="Implement OAuth",
            priority=1
        )

        assert task_id is not None
        assert task_id.startswith("TASK-")

    def test_add_task_json_mode(self, temp_project_dir, sample_json_queue, monkeypatch):
        """Should add task to JSON file."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test-project", use_db=False)
        initial_count = len(manager.get_all_tasks())

        task_id = manager.add_task(
            description="New task",
            priority=2
        )

        assert task_id is not None
        assert len(manager.get_all_tasks()) == initial_count + 1

    def test_update_status_sqlite_mode(self, temp_project_dir, monkeypatch):
        """Should update task status in SQLite."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)
        task_id = manager.add_task(
            feature_id="FEAT-001",
            description="Test task",
            priority=1
        )

        manager.update_status(task_id, "in_progress")
        task = manager.get_task(task_id)

        assert task["status"] == "in_progress"

    def test_update_status_json_mode(self, temp_project_dir, sample_json_queue, monkeypatch):
        """Should update task status in JSON."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test-project", use_db=False)

        manager.update_status("TASK-001", "completed")
        task = manager.get_task("TASK-001")

        assert task["status"] == "completed"

    def test_get_next_task_sqlite_mode(self, temp_project_dir, monkeypatch):
        """Should get next pending task from SQLite by priority."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        # Add tasks with different priorities
        manager.add_task(feature_id="FEAT-001", description="P2 task", priority=2)
        manager.add_task(feature_id="FEAT-001", description="P0 task", priority=0)
        manager.add_task(feature_id="FEAT-001", description="P1 task", priority=1)

        next_task = manager.get_next_task()

        assert next_task is not None
        assert next_task["description"] == "P0 task"

    def test_get_next_task_json_mode(self, temp_project_dir, sample_json_queue, monkeypatch):
        """Should get next pending task from JSON."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test-project", use_db=False)

        next_task = manager.get_next_task()

        assert next_task is not None
        assert next_task["status"] == "pending"


class TestTransactions:
    """Test ACID transaction support in SQLite mode."""

    def test_transaction_rollback_on_error(self, temp_project_dir, monkeypatch):
        """Should rollback transaction on error."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)
        initial_count = len(manager.get_all_tasks())

        # Try to add task with invalid status (should fail)
        with pytest.raises(Exception):
            manager.add_task(
                feature_id="FEAT-001",
                description="Test",
                priority=1,
                status="invalid_status"  # Invalid
            )

        # Count should be unchanged
        assert len(manager.get_all_tasks()) == initial_count

    def test_atomic_status_update(self, temp_project_dir, monkeypatch):
        """Should update status atomically."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)
        task_id = manager.add_task(
            feature_id="FEAT-001",
            description="Test",
            priority=1
        )

        # Update should be atomic
        manager.update_status(task_id, "in_progress")
        manager.update_status(task_id, "completed")

        task = manager.get_task(task_id)
        assert task["status"] == "completed"


class TestMigrationSupport:
    """Test schema migration system."""

    def test_detect_schema_version(self, temp_project_dir, monkeypatch):
        """Should detect current schema version."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)
        version = manager.get_schema_version()

        assert version >= 1  # Initial schema

    def test_run_migration(self, temp_project_dir, monkeypatch):
        """Should run migration script."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        # Should not fail even if no migrations needed
        manager.migrate()

        version = manager.get_schema_version()
        assert version >= 1


class TestHybridMode:
    """Test hybrid SQLite + JSON export."""

    def test_export_snapshot_to_json(self, temp_project_dir, monkeypatch):
        """Should export SQLite data to JSON snapshot."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        # Add some tasks
        manager.add_task(feature_id="FEAT-001", description="Task 1", priority=1)
        manager.add_task(feature_id="FEAT-001", description="Task 2", priority=2)

        # Export to JSON
        json_path = manager.export_snapshot()

        assert json_path.exists()
        with open(json_path) as f:
            data = json.load(f)

        assert "tasks" in data
        assert len(data["tasks"]) == 2

    def test_import_from_json_snapshot(self, temp_project_dir, sample_json_queue, monkeypatch):
        """Should import JSON snapshot into SQLite."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        # Import from JSON
        manager.import_snapshot(sample_json_queue)

        tasks = manager.get_all_tasks()
        assert len(tasks) >= 2  # At least the 2 from sample


class TestFeatureHierarchy:
    """Test epic/feature/task hierarchy support."""

    def test_add_epic(self, temp_project_dir, monkeypatch):
        """Should add epic to SQLite."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        epic_id = manager.add_epic(
            name="User Authentication",
            description="Complete OAuth implementation"
        )

        assert epic_id is not None
        assert epic_id.startswith("EPIC-")

    def test_add_feature(self, temp_project_dir, monkeypatch):
        """Should add feature to epic."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        epic_id = manager.add_epic(name="Auth")
        feature_id = manager.add_feature(
            epic_id=epic_id,
            name="OAuth Provider",
            priority=0
        )

        assert feature_id is not None
        assert feature_id.startswith("FEAT-")

    def test_get_tasks_by_feature(self, temp_project_dir, monkeypatch):
        """Should filter tasks by feature_id."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        epic_id = manager.add_epic(name="Auth")
        feat1 = manager.add_feature(epic_id=epic_id, name="Feature 1")
        feat2 = manager.add_feature(epic_id=epic_id, name="Feature 2")

        manager.add_task(feature_id=feat1, description="Task 1")
        manager.add_task(feature_id=feat1, description="Task 2")
        manager.add_task(feature_id=feat2, description="Task 3")

        feat1_tasks = manager.get_tasks_by_feature(feat1)

        assert len(feat1_tasks) == 2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_get_nonexistent_task(self, temp_project_dir, monkeypatch):
        """Should return None for nonexistent task."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        task = manager.get_task("TASK-NONEXISTENT")

        assert task is None

    def test_update_nonexistent_task(self, temp_project_dir, monkeypatch):
        """Should handle update to nonexistent task gracefully."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        # Should not raise, just return False
        result = manager.update_status("TASK-NONEXISTENT", "completed")

        assert result is False

    def test_get_next_task_empty_queue(self, temp_project_dir, monkeypatch):
        """Should return None when no pending tasks."""
        monkeypatch.chdir(temp_project_dir)
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test", use_db=True)

        next_task = manager.get_next_task()

        assert next_task is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
