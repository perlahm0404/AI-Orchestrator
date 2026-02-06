"""
Test JSON → SQLite migration script.

TDD: These tests are written BEFORE the implementation.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime


@pytest.fixture
def temp_project_env(tmp_path, monkeypatch):
    """Set up temporary project environment with JSON work queue."""
    monkeypatch.chdir(tmp_path)

    # Create directories
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tmp_path / ".aibrain").mkdir()

    # Create sample JSON work queue
    work_queue = {
        "project": "test-project",
        "tasks": [
            {
                "id": "TASK-001",
                "description": "Fix login bug",
                "status": "pending",
                "priority": 0,
                "file": "src/auth/login.ts",
                "attempts": 0,
                "retry_budget": 15
            },
            {
                "id": "TASK-002",
                "description": "Add OAuth tests",
                "status": "in_progress",
                "priority": 1,
                "file": "tests/auth/oauth.test.ts",
                "attempts": 2,
                "retry_budget": 20
            },
            {
                "id": "TASK-003",
                "description": "Update docs",
                "status": "completed",
                "priority": 2,
                "file": "docs/auth.md",
                "attempts": 1,
                "retry_budget": 10
            }
        ]
    }

    json_path = tasks_dir / "work_queue_test-project.json"
    with open(json_path, 'w') as f:
        json.dump(work_queue, f, indent=2)

    return tmp_path, json_path


class TestMigrationBasics:
    """Test basic migration functionality."""

    def test_migrate_reads_json_file(self, temp_project_env):
        """Should read JSON work queue file."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate
        result = migrate_work_queue(project="test-project", dry_run=True)

        assert result is not None
        assert result["tasks_found"] == 3

    def test_migrate_creates_sqlite_db(self, temp_project_env):
        """Should create SQLite database."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate
        migrate_work_queue(project="test-project", dry_run=False)

        # Check database exists
        db_path = tmp_path / ".aibrain" / "work_queue_test-project.db"
        assert db_path.exists()

    def test_migrate_preserves_task_count(self, temp_project_env):
        """Should migrate all tasks."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate
        result = migrate_work_queue(project="test-project", dry_run=False)

        assert result["tasks_migrated"] == 3

        # Verify in database
        from orchestration.queue_manager import WorkQueueManager
        manager = WorkQueueManager(project="test-project", use_db=True)
        tasks = manager.get_all_tasks()

        assert len(tasks) == 3

    def test_migrate_preserves_task_data(self, temp_project_env):
        """Should preserve task descriptions and statuses."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate
        migrate_work_queue(project="test-project", dry_run=False)

        # Verify task data
        from orchestration.queue_manager import WorkQueueManager
        manager = WorkQueueManager(project="test-project", use_db=True)

        tasks = manager.get_all_tasks()
        task_by_desc = {t["description"]: t for t in tasks}

        assert "Fix login bug" in task_by_desc
        assert task_by_desc["Fix login bug"]["status"] == "pending"

        assert "Add OAuth tests" in task_by_desc
        assert task_by_desc["Add OAuth tests"]["status"] == "in_progress"


class TestFeatureGrouping:
    """Test automatic feature creation from task groupings."""

    def test_creates_features_from_file_paths(self, temp_project_env):
        """Should group tasks by file path into features."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate with feature grouping
        result = migrate_work_queue(
            project="test-project",
            dry_run=False,
            auto_group_features=True
        )

        assert result["features_created"] > 0

        # Verify features exist
        from orchestration.queue_manager import WorkQueueManager
        from orchestration.models import Feature

        manager = WorkQueueManager(project="test-project", use_db=True)
        with manager._get_session() as session:
            features = session.query(Feature).all()
            assert len(features) > 0

    def test_creates_epic_for_project(self, temp_project_env):
        """Should create epic for the project."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate with epic creation
        result = migrate_work_queue(
            project="test-project",
            dry_run=False,
            create_epic=True
        )

        assert result["epic_created"] is True

        # Verify epic exists
        from orchestration.queue_manager import WorkQueueManager
        from orchestration.models import Epic

        manager = WorkQueueManager(project="test-project", use_db=True)
        with manager._get_session() as session:
            epics = session.query(Epic).all()
            assert len(epics) >= 1


class TestDryRunMode:
    """Test dry-run mode for validation."""

    def test_dry_run_does_not_create_db(self, temp_project_env):
        """Should not create database in dry-run mode."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Dry run
        result = migrate_work_queue(project="test-project", dry_run=True)

        # Database should not exist
        db_path = tmp_path / ".aibrain" / "work_queue_test-project.db"
        assert not db_path.exists()

        # But should report what would be done
        assert result["tasks_found"] == 3

    def test_dry_run_shows_migration_plan(self, temp_project_env):
        """Should show what would be migrated."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Dry run
        result = migrate_work_queue(project="test-project", dry_run=True)

        assert "tasks_found" in result
        assert "epics_to_create" in result
        assert "features_to_create" in result


class TestBackupFunctionality:
    """Test JSON backup before migration."""

    def test_creates_backup_before_migration(self, temp_project_env):
        """Should backup JSON file before migration."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate with backup
        result = migrate_work_queue(
            project="test-project",
            dry_run=False,
            backup=True
        )

        # Backup should exist
        backup_path = json_path.parent / f"{json_path.stem}.backup.json"
        assert backup_path.exists()

        # Verify backup content matches original
        with open(backup_path) as f:
            backup_data = json.load(f)

        with open(json_path) as f:
            original_data = json.load(f)

        assert backup_data == original_data

    def test_skip_backup_when_disabled(self, temp_project_env):
        """Should not create backup when disabled."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate without backup
        migrate_work_queue(project="test-project", dry_run=False, backup=False)

        # Backup should not exist
        backup_path = json_path.parent / f"{json_path.stem}.backup.json"
        assert not backup_path.exists()


class TestPriorityPreservation:
    """Test that task priority is preserved."""

    def test_preserves_task_priority(self, temp_project_env):
        """Should preserve priority from JSON."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate
        migrate_work_queue(project="test-project", dry_run=False)

        # Verify priorities
        from orchestration.queue_manager import WorkQueueManager
        from orchestration.models import Feature, Task

        manager = WorkQueueManager(project="test-project", use_db=True)
        with manager._get_session() as session:
            # Task with priority 0 should be in P0 feature
            p0_features = session.query(Feature).filter_by(priority=0).all()
            if p0_features:
                p0_tasks = session.query(Task).filter_by(feature_id=p0_features[0].id).all()
                assert len(p0_tasks) > 0


class TestErrorHandling:
    """Test error handling for edge cases."""

    def test_handles_missing_json_file(self, tmp_path, monkeypatch):
        """Should handle missing JSON file gracefully."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tasks").mkdir()
        (tmp_path / ".aibrain").mkdir()

        from scripts.migrate_json_to_sqlite import migrate_work_queue

        with pytest.raises(FileNotFoundError):
            migrate_work_queue(project="nonexistent", dry_run=True)

    def test_handles_invalid_json(self, tmp_path, monkeypatch):
        """Should handle invalid JSON gracefully."""
        monkeypatch.chdir(tmp_path)

        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tmp_path / ".aibrain").mkdir()

        # Create invalid JSON
        json_path = tasks_dir / "work_queue_invalid.json"
        with open(json_path, 'w') as f:
            f.write("{ invalid json }")

        from scripts.migrate_json_to_sqlite import migrate_work_queue

        with pytest.raises(json.JSONDecodeError):
            migrate_work_queue(project="invalid", dry_run=True)


class TestRetryBudgetPreservation:
    """Test that retry budgets are preserved."""

    def test_preserves_retry_budget(self, temp_project_env):
        """Should preserve retry_budget from JSON."""
        from scripts.migrate_json_to_sqlite import migrate_work_queue

        tmp_path, json_path = temp_project_env

        # Migrate
        migrate_work_queue(project="test-project", dry_run=False)

        # Verify retry budgets
        from orchestration.queue_manager import WorkQueueManager

        manager = WorkQueueManager(project="test-project", use_db=True)
        tasks = manager.get_all_tasks()

        # Find task with custom retry budget
        oauth_task = next(t for t in tasks if "OAuth" in t["description"])
        assert oauth_task["retry_budget"] == 20  # From JSON


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
