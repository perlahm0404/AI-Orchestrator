"""
Test progress rollup triggers and queries.

TDD: These tests verify that the triggers in schema.sql work correctly.
"""

import pytest
import time
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
def populated_hierarchy(manager):
    """Create epic → feature → task hierarchy."""
    # Create epic
    epic_id = manager.add_epic(name="Test Epic", description="Test")

    # Create features
    feat1_id = manager.add_feature(epic_id=epic_id, name="Feature 1", priority=0)
    feat2_id = manager.add_feature(epic_id=epic_id, name="Feature 2", priority=1)

    # Add tasks
    task1_id = manager.add_task(feature_id=feat1_id, description="Task 1", priority=0)
    task2_id = manager.add_task(feature_id=feat1_id, description="Task 2", priority=0)
    task3_id = manager.add_task(feature_id=feat2_id, description="Task 3", priority=1)

    return {
        "manager": manager,
        "epic_id": epic_id,
        "feat1_id": feat1_id,
        "feat2_id": feat2_id,
        "task1_id": task1_id,
        "task2_id": task2_id,
        "task3_id": task3_id,
    }


class TestFeatureStatusRollup:
    """Test feature status updates based on task completion."""

    def test_feature_becomes_in_progress_when_first_task_completes(self, populated_hierarchy):
        """Feature should become in_progress when first task completes."""
        manager = populated_hierarchy["manager"]
        feat1_id = populated_hierarchy["feat1_id"]
        task1_id = populated_hierarchy["task1_id"]

        # Complete one task
        manager.update_status(task1_id, "completed")

        with manager._get_session() as session:
            feature = session.query(Feature).filter_by(id=feat1_id).first()
            assert feature.status == "in_progress"

    def test_feature_becomes_completed_when_all_tasks_complete(self, populated_hierarchy):
        """Feature should become completed when all tasks complete."""
        manager = populated_hierarchy["manager"]
        feat1_id = populated_hierarchy["feat1_id"]
        task1_id = populated_hierarchy["task1_id"]
        task2_id = populated_hierarchy["task2_id"]

        # Complete all tasks
        manager.update_status(task1_id, "completed")
        manager.update_status(task2_id, "completed")

        with manager._get_session() as session:
            feature = session.query(Feature).filter_by(id=feat1_id).first()
            assert feature.status == "completed"


class TestEpicStatusRollup:
    """Test epic status updates based on feature completion."""

    def test_epic_becomes_in_progress_when_first_feature_completes(self, populated_hierarchy):
        """Epic should become in_progress when first feature completes."""
        manager = populated_hierarchy["manager"]
        epic_id = populated_hierarchy["epic_id"]
        task3_id = populated_hierarchy["task3_id"]

        # Complete all tasks in feature 2 (only 1 task)
        manager.update_status(task3_id, "completed")

        with manager._get_session() as session:
            epic = session.query(Epic).filter_by(id=epic_id).first()
            assert epic.status == "in_progress"

    def test_epic_becomes_completed_when_all_features_complete(self, populated_hierarchy):
        """Epic should become completed when all features complete."""
        manager = populated_hierarchy["manager"]
        epic_id = populated_hierarchy["epic_id"]

        # Complete all tasks in both features
        task1_id = populated_hierarchy["task1_id"]
        task2_id = populated_hierarchy["task2_id"]
        task3_id = populated_hierarchy["task3_id"]

        manager.update_status(task1_id, "completed")
        manager.update_status(task2_id, "completed")
        manager.update_status(task3_id, "completed")

        with manager._get_session() as session:
            epic = session.query(Epic).filter_by(id=epic_id).first()
            assert epic.status == "completed"


class TestProgressCalculations:
    """Test progress percentage calculations."""

    def test_feature_progress_calculation(self, populated_hierarchy):
        """Feature should show 50% progress with half tasks completed."""
        manager = populated_hierarchy["manager"]
        feat1_id = populated_hierarchy["feat1_id"]
        task1_id = populated_hierarchy["task1_id"]

        # Complete 1 of 2 tasks
        manager.update_status(task1_id, "completed")

        with manager._get_session() as session:
            tasks = session.query(Task).filter_by(feature_id=feat1_id).all()

            completed = sum(1 for t in tasks if t.status == "completed")
            total = len(tasks)
            progress = round((completed / total * 100) if total > 0 else 0)

            assert progress == 50

    def test_epic_progress_calculation(self, populated_hierarchy):
        """Epic progress should reflect all tasks across all features."""
        manager = populated_hierarchy["manager"]
        epic_id = populated_hierarchy["epic_id"]
        task1_id = populated_hierarchy["task1_id"]

        # Complete 1 of 3 total tasks
        manager.update_status(task1_id, "completed")

        with manager._get_session() as session:
            # Get all tasks across all features
            features = session.query(Feature).filter_by(epic_id=epic_id).all()
            all_tasks = []
            for feature in features:
                tasks = session.query(Task).filter_by(feature_id=feature.id).all()
                all_tasks.extend(tasks)

            completed = sum(1 for t in all_tasks if t.status == "completed")
            total = len(all_tasks)
            progress = round((completed / total * 100) if total > 0 else 0)

            assert progress == 33  # 1/3 = 33%


class TestUpdatedAtTimestamps:
    """Test that updated_at timestamps are updated."""

    def test_feature_updated_at_changes_on_task_complete(self, populated_hierarchy):
        """Feature updated_at should change when task completes."""
        manager = populated_hierarchy["manager"]
        feat1_id = populated_hierarchy["feat1_id"]
        task1_id = populated_hierarchy["task1_id"]

        # Get initial timestamp (truncate microseconds for comparison)
        with manager._get_session() as session:
            feature = session.query(Feature).filter_by(id=feat1_id).first()
            initial_updated = feature.updated_at.replace(microsecond=0)

        # Complete task (with small delay to ensure timestamp difference)
        time.sleep(1.1)  # Need >1 second since SQLite datetime() has second precision
        manager.update_status(task1_id, "completed")

        # Check timestamp changed (compare at second precision)
        with manager._get_session() as session:
            feature = session.query(Feature).filter_by(id=feat1_id).first()
            updated_at = feature.updated_at.replace(microsecond=0)
            assert updated_at > initial_updated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
