"""
SQLAlchemy models for work queue persistence.

Implements epic → feature → task → test_case hierarchy.
Reference: KO-aio-002 (SQLite persistence), KO-aio-004 (Feature hierarchy)
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint
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

    # Relationships
    feature = relationship('Feature', back_populates='tasks')
    test_cases = relationship('TestCase', back_populates='task', cascade='all, delete-orphan')

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
