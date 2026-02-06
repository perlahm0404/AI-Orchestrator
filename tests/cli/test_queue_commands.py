"""
Test CLI commands for SQLite work queue management.

TDD: These tests are written BEFORE the implementation.
"""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Create Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_project_env(tmp_path, monkeypatch):
    """Set up temporary project environment."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Create required directories
    (tmp_path / "tasks").mkdir()
    (tmp_path / ".aibrain").mkdir()

    return tmp_path


@pytest.fixture
def populated_queue(temp_project_env):
    """Create a populated work queue for testing."""
    from orchestration.queue_manager import WorkQueueManager

    manager = WorkQueueManager(project="test", use_db=True)

    # Create hierarchy
    epic_id = manager.add_epic(name="User Authentication", description="OAuth system")
    feat1_id = manager.add_feature(epic_id=epic_id, name="Google OAuth", priority=0)
    feat2_id = manager.add_feature(epic_id=epic_id, name="GitHub OAuth", priority=1)

    # Add tasks
    manager.add_task(feature_id=feat1_id, description="Implement OAuth flow", priority=0)
    manager.add_task(feature_id=feat1_id, description="Add callback handler", priority=0)
    manager.add_task(feature_id=feat2_id, description="Setup GitHub app", priority=1)

    return manager


class TestQueueListCommand:
    """Test 'aibrain queue list' command."""

    def test_list_empty_queue(self, cli_runner, temp_project_env):
        """Should show empty queue message."""
        from cli.commands.queue import queue_list

        result = cli_runner.invoke(queue_list, ["--project", "test"])

        assert result.exit_code == 0
        assert "No tasks found" in result.output or "empty" in result.output.lower()

    def test_list_with_tasks(self, cli_runner, temp_project_env, populated_queue):
        """Should list all tasks."""
        from cli.commands.queue import queue_list

        result = cli_runner.invoke(queue_list, ["--project", "test"])

        assert result.exit_code == 0
        assert "TASK-" in result.output
        assert "pending" in result.output.lower()

    def test_list_with_hierarchy(self, cli_runner, temp_project_env, populated_queue):
        """Should show hierarchical tree view."""
        from cli.commands.queue import queue_list

        result = cli_runner.invoke(queue_list, ["--project", "test", "--hierarchy"])

        assert result.exit_code == 0
        assert "User Authentication" in result.output
        assert "Google OAuth" in result.output
        assert "├──" in result.output or "└──" in result.output  # Tree characters


class TestQueueAddEpicCommand:
    """Test 'aibrain queue add-epic' command."""

    def test_add_epic_minimal(self, cli_runner, temp_project_env):
        """Should add epic with just name."""
        from cli.commands.queue import queue_add_epic

        result = cli_runner.invoke(queue_add_epic, [
            "--project", "test",
            "--name", "New Epic"
        ])

        assert result.exit_code == 0
        assert "EPIC-" in result.output
        assert "created" in result.output.lower()

    def test_add_epic_with_description(self, cli_runner, temp_project_env):
        """Should add epic with description."""
        from cli.commands.queue import queue_add_epic

        result = cli_runner.invoke(queue_add_epic, [
            "--project", "test",
            "--name", "New Epic",
            "--description", "This is a test epic"
        ])

        assert result.exit_code == 0
        assert "EPIC-" in result.output

    def test_add_epic_missing_name(self, cli_runner, temp_project_env):
        """Should fail without name."""
        from cli.commands.queue import queue_add_epic

        result = cli_runner.invoke(queue_add_epic, ["--project", "test"])

        assert result.exit_code != 0


class TestQueueAddFeatureCommand:
    """Test 'aibrain queue add-feature' command."""

    def test_add_feature_to_epic(self, cli_runner, temp_project_env, populated_queue):
        """Should add feature to existing epic."""
        from cli.commands.queue import queue_add_feature

        # Get epic ID from populated queue
        from orchestration.models import Epic
        with populated_queue._get_session() as session:
            epic = session.query(Epic).first()
            epic_id = epic.id

        result = cli_runner.invoke(queue_add_feature, [
            "--project", "test",
            "--epic", epic_id,
            "--name", "New Feature"
        ])

        assert result.exit_code == 0
        assert "FEAT-" in result.output

    def test_add_feature_with_priority(self, cli_runner, temp_project_env, populated_queue):
        """Should add feature with priority."""
        from cli.commands.queue import queue_add_feature
        from orchestration.models import Epic

        with populated_queue._get_session() as session:
            epic = session.query(Epic).first()
            epic_id = epic.id

        result = cli_runner.invoke(queue_add_feature, [
            "--project", "test",
            "--epic", epic_id,
            "--name", "P0 Feature",
            "--priority", "0"
        ])

        assert result.exit_code == 0
        assert "FEAT-" in result.output


class TestQueueAddTaskCommand:
    """Test 'aibrain queue add-task' command."""

    def test_add_task_to_feature(self, cli_runner, temp_project_env, populated_queue):
        """Should add task to existing feature."""
        from cli.commands.queue import queue_add_task
        from orchestration.models import Feature

        with populated_queue._get_session() as session:
            feature = session.query(Feature).first()
            feature_id = feature.id

        result = cli_runner.invoke(queue_add_task, [
            "--project", "test",
            "--feature", feature_id,
            "--description", "New task"
        ])

        assert result.exit_code == 0
        assert "TASK-" in result.output

    def test_add_task_with_priority(self, cli_runner, temp_project_env, populated_queue):
        """Should add task with priority."""
        from cli.commands.queue import queue_add_task
        from orchestration.models import Feature

        with populated_queue._get_session() as session:
            feature = session.query(Feature).first()
            feature_id = feature.id

        result = cli_runner.invoke(queue_add_task, [
            "--project", "test",
            "--feature", feature_id,
            "--description", "P0 task",
            "--priority", "0"
        ])

        assert result.exit_code == 0
        assert "TASK-" in result.output


class TestQueueProgressCommand:
    """Test 'aibrain queue progress' command."""

    def test_progress_for_epic(self, cli_runner, temp_project_env, populated_queue):
        """Should show progress stats for epic."""
        from cli.commands.queue import queue_progress
        from orchestration.models import Epic

        with populated_queue._get_session() as session:
            epic = session.query(Epic).first()
            epic_id = epic.id

        result = cli_runner.invoke(queue_progress, [
            "--project", "test",
            "--epic", epic_id
        ])

        assert result.exit_code == 0
        assert "pending" in result.output.lower()
        assert "%" in result.output or "tasks" in result.output.lower()

    def test_progress_for_feature(self, cli_runner, temp_project_env, populated_queue):
        """Should show progress stats for feature."""
        from cli.commands.queue import queue_progress
        from orchestration.models import Feature

        with populated_queue._get_session() as session:
            feature = session.query(Feature).first()
            feature_id = feature.id

        result = cli_runner.invoke(queue_progress, [
            "--project", "test",
            "--feature", feature_id
        ])

        assert result.exit_code == 0
        assert "tasks" in result.output.lower()


class TestQueueMigrateCommand:
    """Test 'aibrain queue migrate' command."""

    def test_migrate_no_migrations_needed(self, cli_runner, temp_project_env):
        """Should handle case with no migrations."""
        from cli.commands.queue import queue_migrate

        result = cli_runner.invoke(queue_migrate, ["--project", "test"])

        assert result.exit_code == 0
        assert "migration" in result.output.lower() or "up to date" in result.output.lower()


class TestQueueExportCommand:
    """Test 'aibrain queue export' command."""

    def test_export_to_json(self, cli_runner, temp_project_env, populated_queue):
        """Should export SQLite data to JSON."""
        from cli.commands.queue import queue_export

        result = cli_runner.invoke(queue_export, ["--project", "test"])

        assert result.exit_code == 0
        assert "exported" in result.output.lower() or "snapshot" in result.output.lower()

        # Verify JSON file exists
        snapshot_path = temp_project_env / "tasks" / "work_queue_test_snapshot.json"
        assert snapshot_path.exists()

        # Verify JSON is valid
        with open(snapshot_path) as f:
            data = json.load(f)

        assert "tasks" in data
        assert len(data["tasks"]) >= 3  # From populated_queue

    def test_export_custom_output(self, cli_runner, temp_project_env, populated_queue):
        """Should export to custom output path."""
        from cli.commands.queue import queue_export

        custom_path = "custom_export.json"
        result = cli_runner.invoke(queue_export, [
            "--project", "test",
            "--output", custom_path
        ])

        assert result.exit_code == 0
        assert (temp_project_env / custom_path).exists()


class TestQueueCommandIntegration:
    """Test CLI commands working together."""

    def test_add_epic_feature_task_workflow(self, cli_runner, temp_project_env):
        """Should create complete hierarchy via CLI."""
        from cli.commands.queue import queue_add_epic, queue_add_feature, queue_add_task

        # Add epic
        result = cli_runner.invoke(queue_add_epic, [
            "--project", "test",
            "--name", "CLI Test Epic"
        ])
        assert result.exit_code == 0
        epic_id = result.output.split("EPIC-")[1].split()[0]
        epic_id = f"EPIC-{epic_id}"

        # Add feature
        result = cli_runner.invoke(queue_add_feature, [
            "--project", "test",
            "--epic", epic_id,
            "--name", "CLI Test Feature"
        ])
        assert result.exit_code == 0
        feature_id = result.output.split("FEAT-")[1].split()[0]
        feature_id = f"FEAT-{feature_id}"

        # Add task
        result = cli_runner.invoke(queue_add_task, [
            "--project", "test",
            "--feature", feature_id,
            "--description", "CLI test task"
        ])
        assert result.exit_code == 0
        assert "TASK-" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
