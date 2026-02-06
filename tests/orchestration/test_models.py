"""
Test SQLAlchemy models for work queue.

TDD: These tests are written BEFORE the model implementation.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime


@pytest.fixture
def engine():
    """Create in-memory SQLite database for testing."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture
def session(engine):
    """Create database session."""
    # This will fail initially because models.py doesn't exist
    try:
        from orchestration.models import Base
        Base.metadata.create_all(engine)
    except ImportError:
        pass  # Expected during RED phase

    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestEpicModel:
    """Test Epic model."""

    def test_create_epic(self, session):
        """Should create epic with required fields."""
        from orchestration.models import Epic

        epic = Epic(
            id="epic-001",
            name="User Authentication System",
            status="pending"
        )
        session.add(epic)
        session.commit()

        assert epic.id == "epic-001"
        assert epic.name == "User Authentication System"
        assert epic.status == "pending"

    def test_epic_defaults(self, session):
        """Should set default values for timestamps."""
        from orchestration.models import Epic

        epic = Epic(id="epic-001", name="Test", status="pending")
        session.add(epic)
        session.commit()

        assert epic.created_at is not None
        assert epic.updated_at is not None
        assert isinstance(epic.created_at, datetime)

    def test_epic_with_description(self, session):
        """Should allow optional description."""
        from orchestration.models import Epic

        epic = Epic(
            id="epic-001",
            name="Test Epic",
            description="This is a test epic",
            status="pending"
        )
        session.add(epic)
        session.commit()

        assert epic.description == "This is a test epic"

    def test_epic_status_values(self, session):
        """Should accept valid status values."""
        from orchestration.models import Epic

        for status in ["pending", "in_progress", "completed", "blocked"]:
            epic = Epic(id=f"epic-{status}", name="Test", status=status)
            session.add(epic)
            session.commit()
            assert epic.status == status


class TestFeatureModel:
    """Test Feature model."""

    def test_create_feature(self, session):
        """Should create feature with required fields."""
        from orchestration.models import Epic, Feature

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(
            id="feat-001",
            epic_id="epic-001",
            name="OAuth Integration",
            status="pending"
        )
        session.add(epic)
        session.add(feature)
        session.commit()

        assert feature.id == "feat-001"
        assert feature.epic_id == "epic-001"
        assert feature.name == "OAuth Integration"

    def test_feature_default_priority(self, session):
        """Should default to priority 2."""
        from orchestration.models import Epic, Feature

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(
            id="feat-001",
            epic_id="epic-001",
            name="Test",
            status="pending"
        )
        session.add(epic)
        session.add(feature)
        session.commit()

        assert feature.priority == 2

    def test_feature_epic_relationship(self, session):
        """Should have relationship to epic."""
        from orchestration.models import Epic, Feature

        epic = Epic(id="epic-001", name="Test Epic", status="pending")
        feature = Feature(
            id="feat-001",
            epic_id="epic-001",
            name="Test Feature",
            status="pending"
        )
        session.add(epic)
        session.add(feature)
        session.commit()

        # Access relationship
        assert feature.epic is not None
        assert feature.epic.name == "Test Epic"

        # Reverse relationship
        assert len(epic.features) == 1
        assert epic.features[0].name == "Test Feature"


class TestTaskModel:
    """Test Task model."""

    def test_create_task(self, session):
        """Should create task with required fields."""
        from orchestration.models import Epic, Feature, Task

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(
            id="feat-001",
            epic_id="epic-001",
            name="Test",
            status="pending"
        )
        task = Task(
            id="task-001",
            feature_id="feat-001",
            description="Implement OAuth provider configuration",
            status="pending"
        )
        session.add_all([epic, feature, task])
        session.commit()

        assert task.id == "task-001"
        assert task.feature_id == "feat-001"
        assert task.description == "Implement OAuth provider configuration"

    def test_task_default_retry_budget(self, session):
        """Should default to retry_budget=15."""
        from orchestration.models import Epic, Feature, Task

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(id="feat-001", epic_id="epic-001", name="Test", status="pending")
        task = Task(
            id="task-001",
            feature_id="feat-001",
            description="Test",
            status="pending"
        )
        session.add_all([epic, feature, task])
        session.commit()

        assert task.retry_budget == 15
        assert task.retries_used == 0

    def test_task_feature_relationship(self, session):
        """Should have relationship to feature."""
        from orchestration.models import Epic, Feature, Task

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(id="feat-001", epic_id="epic-001", name="Test Feature", status="pending")
        task = Task(id="task-001", feature_id="feat-001", description="Test Task", status="pending")
        session.add_all([epic, feature, task])
        session.commit()

        # Access relationship
        assert task.feature is not None
        assert task.feature.name == "Test Feature"

        # Reverse relationship
        assert len(feature.tasks) == 1
        assert feature.tasks[0].description == "Test Task"

    def test_task_completed_at_null_initially(self, session):
        """Should have completed_at=NULL for non-completed tasks."""
        from orchestration.models import Epic, Feature, Task

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(id="feat-001", epic_id="epic-001", name="Test", status="pending")
        task = Task(id="task-001", feature_id="feat-001", description="Test", status="pending")
        session.add_all([epic, feature, task])
        session.commit()

        assert task.completed_at is None


class TestTestCaseModel:
    """Test TestCase model."""

    def test_create_test_case(self, session):
        """Should create test case with required fields."""
        from orchestration.models import Epic, Feature, Task, TestCase

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(id="feat-001", epic_id="epic-001", name="Test", status="pending")
        task = Task(id="task-001", feature_id="feat-001", description="Test", status="pending")
        test_case = TestCase(
            id="test-001",
            task_id="task-001",
            description="Should redirect to OAuth provider",
            status="pending"
        )
        session.add_all([epic, feature, task, test_case])
        session.commit()

        assert test_case.id == "test-001"
        assert test_case.task_id == "task-001"
        assert test_case.description == "Should redirect to OAuth provider"

    def test_test_case_task_relationship(self, session):
        """Should have relationship to task."""
        from orchestration.models import Epic, Feature, Task, TestCase

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(id="feat-001", epic_id="epic-001", name="Test", status="pending")
        task = Task(id="task-001", feature_id="feat-001", description="Test Task", status="pending")
        test_case = TestCase(
            id="test-001",
            task_id="task-001",
            description="Test case",
            status="pending"
        )
        session.add_all([epic, feature, task, test_case])
        session.commit()

        # Access relationship
        assert test_case.task is not None
        assert test_case.task.description == "Test Task"

        # Reverse relationship
        assert len(task.test_cases) == 1
        assert task.test_cases[0].description == "Test case"


class TestCascadeDeletes:
    """Test cascade delete behavior."""

    def test_delete_epic_cascades_to_features(self, session):
        """Deleting epic should delete its features."""
        from orchestration.models import Epic, Feature

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(id="feat-001", epic_id="epic-001", name="Test", status="pending")
        session.add_all([epic, feature])
        session.commit()

        # Delete epic
        session.delete(epic)
        session.commit()

        # Feature should be gone
        assert session.query(Feature).filter_by(id="feat-001").first() is None

    def test_delete_feature_cascades_to_tasks(self, session):
        """Deleting feature should delete its tasks."""
        from orchestration.models import Epic, Feature, Task

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(id="feat-001", epic_id="epic-001", name="Test", status="pending")
        task = Task(id="task-001", feature_id="feat-001", description="Test", status="pending")
        session.add_all([epic, feature, task])
        session.commit()

        # Delete feature
        session.delete(feature)
        session.commit()

        # Task should be gone
        assert session.query(Task).filter_by(id="task-001").first() is None


class TestQueryOperations:
    """Test common query patterns."""

    def test_filter_by_status(self, session):
        """Should filter tasks by status."""
        from orchestration.models import Epic, Feature, Task

        epic = Epic(id="epic-001", name="Test", status="pending")
        feature = Feature(id="feat-001", epic_id="epic-001", name="Test", status="pending")
        task1 = Task(id="task-001", feature_id="feat-001", description="Task 1", status="pending")
        task2 = Task(id="task-002", feature_id="feat-001", description="Task 2", status="completed")
        session.add_all([epic, feature, task1, task2])
        session.commit()

        pending_tasks = session.query(Task).filter_by(status="pending").all()
        assert len(pending_tasks) == 1
        assert pending_tasks[0].id == "task-001"

    def test_filter_by_priority(self, session):
        """Should filter features by priority."""
        from orchestration.models import Epic, Feature

        epic = Epic(id="epic-001", name="Test", status="pending")
        feat1 = Feature(id="feat-001", epic_id="epic-001", name="P0", status="pending", priority=0)
        feat2 = Feature(id="feat-002", epic_id="epic-001", name="P1", status="pending", priority=1)
        feat3 = Feature(id="feat-003", epic_id="epic-001", name="P2", status="pending", priority=2)
        session.add_all([epic, feat1, feat2, feat3])
        session.commit()

        p0_features = session.query(Feature).filter_by(priority=0).all()
        assert len(p0_features) == 1
        assert p0_features[0].name == "P0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
