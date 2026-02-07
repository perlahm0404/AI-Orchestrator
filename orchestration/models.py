"""
SQLAlchemy models for work queue persistence.

Implements epic → feature → task → test_case hierarchy.
Phase 2 adds: Checkpoint model for stateless memory resumption.

Reference: KO-aio-002 (SQLite persistence), KO-aio-004 (Feature hierarchy)
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Epic(Base):
    """Top-level organizational unit."""

    __tablename__ = 'epics'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(
        String,
        nullable=False,
        default='pending'
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    features = relationship('Feature', back_populates='epic', cascade='all, delete-orphan')

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'blocked')",
            name='check_epic_status'
        ),
    )


class Feature(Base):
    """Belongs to epic, has many tasks."""

    __tablename__ = 'features'

    id = Column(String, primary_key=True)
    epic_id = Column(String, ForeignKey('epics.id', ondelete='CASCADE'), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(
        String,
        nullable=False,
        default='pending'
    )
    priority = Column(Integer, default=2)  # 0=P0, 1=P1, 2=P2
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    epic = relationship('Epic', back_populates='features')
    tasks = relationship('Task', back_populates='feature', cascade='all, delete-orphan')

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'blocked')",
            name='check_feature_status'
        ),
    )


class Task(Base):
    """Belongs to feature."""

    __tablename__ = 'tasks'

    id = Column(String, primary_key=True)
    feature_id = Column(String, ForeignKey('features.id', ondelete='CASCADE'), nullable=False)
    description = Column(String, nullable=False)
    status = Column(
        String,
        nullable=False,
        default='pending'
    )
    retry_budget = Column(Integer, default=15)
    retries_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Phase 2: Session reference for stateless memory
    session_ref = Column(String, nullable=True)  # Points to SESSION-{id}
    agent_type = Column(String, nullable=True)   # Agent type assigned
    error_log = Column(Text, nullable=True)      # Recent error context
    extra_data = Column(JSON, nullable=True)       # Additional task metadata

    # Relationships
    feature = relationship('Feature', back_populates='tasks')
    test_cases = relationship('TestCase', back_populates='task', cascade='all, delete-orphan')
    checkpoints = relationship('Checkpoint', back_populates='task', cascade='all, delete-orphan')

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'blocked')",
            name='check_task_status'
        ),
    )


class TestCase(Base):
    """Belongs to task or feature."""

    __tablename__ = 'test_cases'

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True)
    feature_id = Column(String, ForeignKey('features.id', ondelete='CASCADE'), nullable=True)
    description = Column(String, nullable=False)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship('Task', back_populates='test_cases')

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'passing', 'failing')",
            name='check_test_case_status'
        ),
    )


class Checkpoint(Base):
    """
    Phase 2: Checkpoint for stateless memory resumption.

    Tracks iteration checkpoints for resuming interrupted tasks.
    Each checkpoint captures the state at a specific iteration,
    enabling agents to resume from the last known good state.
    """

    __tablename__ = 'checkpoints'

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    iteration_count = Column(Integer, nullable=False)
    verdict = Column(String, nullable=True)  # PASS, FAIL, BLOCKED, RETRY_NEEDED
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_ref = Column(String, nullable=True)  # Points to session file
    recoverable = Column(Boolean, default=True)  # Can task be resumed?
    agent_output_summary = Column(Text, nullable=True)  # Summarized agent output
    next_steps = Column(JSON, nullable=True)  # List of next steps
    error_context = Column(Text, nullable=True)  # Error details if any

    # Relationships
    task = relationship('Task', back_populates='checkpoints')

    __table_args__ = (
        CheckConstraint(
            "verdict IN ('PASS', 'FAIL', 'BLOCKED', 'RETRY_NEEDED')",
            name='check_checkpoint_verdict'
        ),
    )


class WorkItem(Base):
    """
    Phase 2: Work item for persistent task tracking.

    Provides a project-scoped view of tasks with session references
    and detailed status tracking for the autonomous loop.
    """

    __tablename__ = 'work_items'

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    project = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    agent_type = Column(String, nullable=True)
    priority = Column(Integer, default=2)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=15)
    session_ref = Column(String, nullable=True)
    error_log = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)

    # Relationships
    task = relationship('Task')

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'blocked', 'completed', 'failed')",
            name='check_work_item_status'
        ),
    )
