"""
Test autonomous_loop.py feature hierarchy integration.

TDD: These tests verify that autonomous_loop processes tasks by feature.
"""

import pytest
from pathlib import Path
from orchestration.queue_manager import WorkQueueManager
from orchestration.models import Epic, Feature, Task


@pytest.fixture
def manager(tmp_path, monkeypatch):
    """Create WorkQueueManager with SQLite backend."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tasks").mkdir()
    (tmp_path / ".aibrain").mkdir()

    return WorkQueueManager(project="test", use_db=True)


@pytest.fixture
def multi_feature_hierarchy(manager):
    """Create hierarchy with multiple features and tasks."""
    # Create epic
    epic_id = manager.add_epic(name="Test Epic", description="Test")

    # Create features with different priorities
    feat1_id = manager.add_feature(epic_id=epic_id, name="Feature 1 (P0)", priority=0)
    feat2_id = manager.add_feature(epic_id=epic_id, name="Feature 2 (P1)", priority=1)

    # Add tasks to Feature 1 (P0)
    task1_id = manager.add_task(feature_id=feat1_id, description="Task 1.1", priority=0)
    task2_id = manager.add_task(feature_id=feat1_id, description="Task 1.2", priority=0)

    # Add tasks to Feature 2 (P1)
    task3_id = manager.add_task(feature_id=feat2_id, description="Task 2.1", priority=1)
    task4_id = manager.add_task(feature_id=feat2_id, description="Task 2.2", priority=1)

    return {
        "manager": manager,
        "epic_id": epic_id,
        "feat1_id": feat1_id,
        "feat2_id": feat2_id,
        "task1_id": task1_id,
        "task2_id": task2_id,
        "task3_id": task3_id,
        "task4_id": task4_id,
    }


class TestFeatureBasedTaskRetrieval:
    """Test that tasks are retrieved by feature priority."""

    def test_get_next_task_returns_highest_priority_feature_task(self, multi_feature_hierarchy):
        """Next task should come from highest priority feature (P0)."""
        manager = multi_feature_hierarchy["manager"]
        task1_id = multi_feature_hierarchy["task1_id"]

        next_task = manager.get_next_task()

        assert next_task is not None
        assert next_task["id"] == task1_id
        assert next_task["feature_id"] == multi_feature_hierarchy["feat1_id"]

    def test_all_tasks_in_feature_processed_before_next_feature(self, multi_feature_hierarchy):
        """All tasks in P0 feature should be processed before P1 feature tasks."""
        manager = multi_feature_hierarchy["manager"]
        task1_id = multi_feature_hierarchy["task1_id"]
        task2_id = multi_feature_hierarchy["task2_id"]
        task3_id = multi_feature_hierarchy["task3_id"]

        # Get first task (should be from P0 feature)
        next_task = manager.get_next_task()
        assert next_task["id"] == task1_id

        # Complete first task
        manager.update_status(task1_id, "completed")

        # Get next task (should still be from P0 feature)
        next_task = manager.get_next_task()
        assert next_task["id"] == task2_id
        assert next_task["feature_id"] == multi_feature_hierarchy["feat1_id"]

        # Complete second task
        manager.update_status(task2_id, "completed")

        # Now next task should be from P1 feature
        next_task = manager.get_next_task()
        assert next_task["id"] == task3_id
        assert next_task["feature_id"] == multi_feature_hierarchy["feat2_id"]


class TestFeatureStatusUpdate:
    """Test that feature status updates when all tasks complete."""

    def test_feature_status_updates_via_triggers(self, multi_feature_hierarchy):
        """Feature status should update automatically via triggers."""
        manager = multi_feature_hierarchy["manager"]
        feat1_id = multi_feature_hierarchy["feat1_id"]
        task1_id = multi_feature_hierarchy["task1_id"]
        task2_id = multi_feature_hierarchy["task2_id"]

        # Complete first task
        manager.update_status(task1_id, "completed")

        # Feature should be in_progress
        with manager._get_session() as session:
            feature = session.query(Feature).filter_by(id=feat1_id).first()
            assert feature.status == "in_progress"

        # Complete second task
        manager.update_status(task2_id, "completed")

        # Feature should be completed
        with manager._get_session() as session:
            feature = session.query(Feature).filter_by(id=feat1_id).first()
            assert feature.status == "completed"


class TestEpicFiltering:
    """Test filtering tasks by epic."""

    def test_get_tasks_by_epic(self, multi_feature_hierarchy):
        """Should be able to filter tasks by epic_id."""
        manager = multi_feature_hierarchy["manager"]
        epic_id = multi_feature_hierarchy["epic_id"]

        # Get all features in epic
        with manager._get_session() as session:
            features = session.query(Feature).filter_by(epic_id=epic_id).all()
            assert len(features) == 2

            # Get all tasks across all features in epic
            all_tasks = []
            for feature in features:
                tasks = session.query(Task).filter_by(feature_id=feature.id).all()
                all_tasks.extend(tasks)

            assert len(all_tasks) == 4  # 2 tasks per feature * 2 features


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
