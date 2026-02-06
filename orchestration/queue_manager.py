"""
WorkQueueManager: Hybrid SQLite/JSON work queue persistence.

Supports two modes:
- SQLite mode (use_db=True): ACID transactions with full hierarchy
- JSON fallback mode (use_db=False): Compatible with existing work_queue_*.json

Reference: KO-aio-002 (SQLite persistence), KO-aio-004 (Feature hierarchy)
"""

import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from orchestration.models import Base, Epic, Feature, Task


class WorkQueueManager:
    """Manages work queue with dual SQLite/JSON backend support."""

    def __init__(self, project: str, use_db: bool = True):
        """
        Initialize work queue manager.

        Args:
            project: Project name
            use_db: Use SQLite backend (True) or JSON fallback (False)
        """
        self.project = project
        self.use_db = use_db

        # Setup paths
        self.root_dir = Path.cwd()
        self.tasks_dir = self.root_dir / "tasks"
        self.db_dir = self.root_dir / ".aibrain"

        # Ensure directories exist
        self.tasks_dir.mkdir(exist_ok=True)
        self.db_dir.mkdir(exist_ok=True)

        if use_db:
            # SQLite mode
            self.db_path = self.db_dir / f"work_queue_{project}.db"
            self.engine = create_engine(f"sqlite:///{self.db_path}")
            self.SessionLocal = sessionmaker(bind=self.engine)

            # Initialize schema
            self._initialize_schema()
        else:
            # JSON mode
            self.json_path = self.tasks_dir / f"work_queue_{project}.json"
            self._ensure_json_file()

    def _initialize_schema(self) -> None:
        """Create database schema if not exists."""
        # Apply schema from schema.sql
        schema_path = self.root_dir / "tasks" / "schema.sql"

        if schema_path.exists():
            # Execute schema.sql
            with open(schema_path) as f:
                schema_sql = f.read()

            with self.engine.begin() as conn:
                # SQLAlchemy execute needs statements split
                for statement in schema_sql.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        conn.execute(text(statement))
        else:
            # Fallback: use SQLAlchemy models + create schema_version table + triggers
            Base.metadata.create_all(self.engine)

            with self.engine.begin() as conn:
                # Create schema_version table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """))

                # Insert initial version
                conn.execute(text("""
                    INSERT OR IGNORE INTO schema_version (version, description)
                    VALUES (1, 'Initial schema via SQLAlchemy models')
                """))

                # Add progress rollup triggers (critical for status updates)
                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS update_feature_status_on_task_complete
                    AFTER UPDATE ON tasks
                    WHEN NEW.status = 'completed'
                    BEGIN
                        UPDATE features
                        SET
                            status = CASE
                                WHEN (SELECT COUNT(*) FROM tasks WHERE feature_id = NEW.feature_id AND status != 'completed') = 0
                                THEN 'completed'
                                ELSE 'in_progress'
                            END,
                            updated_at = datetime('now')
                        WHERE id = NEW.feature_id;
                    END
                """))

                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS update_epic_status_on_feature_complete
                    AFTER UPDATE ON features
                    WHEN NEW.status = 'completed'
                    BEGIN
                        UPDATE epics
                        SET
                            status = CASE
                                WHEN (SELECT COUNT(*) FROM features WHERE epic_id = NEW.epic_id AND status != 'completed') = 0
                                THEN 'completed'
                                ELSE 'in_progress'
                            END,
                            updated_at = datetime('now')
                        WHERE id = NEW.epic_id;
                    END
                """))

    def _ensure_json_file(self) -> None:
        """Ensure JSON file exists with basic structure."""
        if not self.json_path.exists():
            data = {
                "project": self.project,
                "tasks": []
            }
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=2)

    @contextmanager
    def _get_session(self) -> Session:
        """Get database session with transaction management."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _load_json(self) -> Dict[str, Any]:
        """Load JSON work queue data."""
        with open(self.json_path) as f:
            return json.load(f)

    def _save_json(self, data: Dict[str, Any]) -> None:
        """Save JSON work queue data."""
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_epic(self, name: str, description: str = None, status: str = "pending") -> str:
        """
        Add epic (SQLite mode only).

        Args:
            name: Epic name
            description: Optional description
            status: Initial status

        Returns:
            Epic ID
        """
        if not self.use_db:
            raise NotImplementedError("Epics not supported in JSON mode")

        epic_id = f"EPIC-{uuid.uuid4().hex[:8].upper()}"

        with self._get_session() as session:
            epic = Epic(
                id=epic_id,
                name=name,
                description=description,
                status=status
            )
            session.add(epic)

        return epic_id

    def add_feature(
        self,
        name: str,
        epic_id: Optional[str] = None,
        description: str = None,
        priority: int = 2,
        status: str = "pending"
    ) -> str:
        """
        Add feature (SQLite mode only).

        Args:
            name: Feature name
            epic_id: Parent epic ID
            description: Optional description
            priority: Priority (0=P0, 1=P1, 2=P2)
            status: Initial status

        Returns:
            Feature ID
        """
        if not self.use_db:
            raise NotImplementedError("Features not supported in JSON mode")

        feature_id = f"FEAT-{uuid.uuid4().hex[:8].upper()}"

        with self._get_session() as session:
            feature = Feature(
                id=feature_id,
                epic_id=epic_id,
                name=name,
                description=description,
                priority=priority,
                status=status
            )
            session.add(feature)

        return feature_id

    def add_task(
        self,
        description: str,
        feature_id: Optional[str] = None,
        priority: int = 2,
        status: str = "pending",
        retry_budget: int = 15,
        retries_used: int = 0
    ) -> str:
        """
        Add task to queue.

        Args:
            description: Task description
            feature_id: Parent feature ID (SQLite mode only)
            priority: Task priority (used in JSON mode, or for feature in SQLite)
            status: Initial status
            retry_budget: Max retry attempts
            retries_used: Current retry count

        Returns:
            Task ID
        """
        task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"

        if self.use_db:
            # SQLite mode
            if not feature_id:
                raise ValueError("feature_id required in SQLite mode")

            with self._get_session() as session:
                # Check if feature already exists
                feature = session.query(Feature).filter_by(id=feature_id).first()

                if not feature:
                    # Feature doesn't exist - auto-create with priority-based ID
                    actual_feature_id = feature_id
                    if priority != 2:
                        # Append priority to feature ID for separation
                        actual_feature_id = f"{feature_id}-P{priority}"

                    # Auto-create feature with priority from parameter
                    feature = Feature(
                        id=actual_feature_id,
                        name=f"Auto-created feature {actual_feature_id}",
                        priority=priority,
                        status="pending"
                    )
                    session.add(feature)
                    feature_id = actual_feature_id

                task = Task(
                    id=task_id,
                    feature_id=feature_id,
                    description=description,
                    status=status,
                    retry_budget=retry_budget,
                    retries_used=retries_used
                )
                session.add(task)
        else:
            # JSON mode
            data = self._load_json()
            task = {
                "id": task_id,
                "description": description,
                "status": status,
                "priority": priority,
                "attempts": retries_used,
                "retry_budget": retry_budget
            }
            data["tasks"].append(task)
            self._save_json(data)

        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task dict or None if not found
        """
        if self.use_db:
            with self._get_session() as session:
                task = session.query(Task).filter_by(id=task_id).first()
                if not task:
                    return None

                return {
                    "id": task.id,
                    "feature_id": task.feature_id,
                    "description": task.description,
                    "status": task.status,
                    "retry_budget": task.retry_budget,
                    "retries_used": task.retries_used,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
        else:
            data = self._load_json()
            for task in data["tasks"]:
                if task["id"] == task_id:
                    return task
            return None

    def update_status(self, task_id: str, status: str) -> bool:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status

        Returns:
            True if updated, False if task not found
        """
        if self.use_db:
            with self._get_session() as session:
                task = session.query(Task).filter_by(id=task_id).first()
                if not task:
                    return False

                task.status = status
                if status == "completed":
                    task.completed_at = datetime.utcnow()

                return True
        else:
            data = self._load_json()
            for task in data["tasks"]:
                if task["id"] == task_id:
                    task["status"] = status
                    self._save_json(data)
                    return True
            return False

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Get next pending task by priority.

        Returns:
            Task dict or None if no pending tasks
        """
        if self.use_db:
            with self._get_session() as session:
                # Get task via feature (for priority)
                task = session.query(Task).join(Feature).filter(
                    Task.status == "pending"
                ).order_by(
                    Feature.priority.asc(),
                    Task.created_at.asc()
                ).first()

                if not task:
                    return None

                return {
                    "id": task.id,
                    "feature_id": task.feature_id,
                    "description": task.description,
                    "status": task.status,
                    "retry_budget": task.retry_budget,
                    "retries_used": task.retries_used
                }
        else:
            data = self._load_json()
            pending = [t for t in data["tasks"] if t["status"] == "pending"]
            if not pending:
                return None

            # Sort by priority
            pending.sort(key=lambda t: t.get("priority", 2))
            return pending[0]

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks.

        Returns:
            List of task dicts
        """
        if self.use_db:
            with self._get_session() as session:
                tasks = session.query(Task).all()
                return [
                    {
                        "id": t.id,
                        "feature_id": t.feature_id,
                        "description": t.description,
                        "status": t.status,
                        "retry_budget": t.retry_budget,
                        "retries_used": t.retries_used
                    }
                    for t in tasks
                ]
        else:
            data = self._load_json()
            return data["tasks"]

    def get_tasks_by_feature(self, feature_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks for a feature (SQLite mode only).

        Args:
            feature_id: Feature ID

        Returns:
            List of task dicts
        """
        if not self.use_db:
            raise NotImplementedError("Feature filtering not supported in JSON mode")

        with self._get_session() as session:
            tasks = session.query(Task).filter_by(feature_id=feature_id).all()
            return [
                {
                    "id": t.id,
                    "feature_id": t.feature_id,
                    "description": t.description,
                    "status": t.status
                }
                for t in tasks
            ]

    def get_schema_version(self) -> int:
        """
        Get current schema version (SQLite mode only).

        Returns:
            Schema version number (0 if table doesn't exist)
        """
        if not self.use_db:
            raise NotImplementedError("Schema versioning not supported in JSON mode")

        try:
            with self._get_session() as session:
                result = session.execute(
                    text("SELECT MAX(version) FROM schema_version")
                ).fetchone()
                return result[0] if result and result[0] else 0
        except Exception:
            # schema_version table doesn't exist yet
            return 0

    def migrate(self) -> None:
        """
        Run database migrations (SQLite mode only).

        Applies any pending migration scripts from tasks/migrations/
        """
        if not self.use_db:
            raise NotImplementedError("Migrations not supported in JSON mode")

        migrations_dir = self.root_dir / "tasks" / "migrations"
        if not migrations_dir.exists():
            migrations_dir.mkdir(parents=True)
            return  # No migrations to run

        current_version = self.get_schema_version()

        # Find migration files
        migration_files = sorted(migrations_dir.glob("*.sql"))

        for migration_file in migration_files:
            # Extract version from filename (e.g., "002_add_indexes.sql" -> 2)
            try:
                file_version = int(migration_file.stem.split('_')[0])
            except (ValueError, IndexError):
                continue

            if file_version > current_version:
                # Apply migration
                with open(migration_file) as f:
                    migration_sql = f.read()

                with self.engine.begin() as conn:
                    for statement in migration_sql.split(';'):
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            conn.execute(text(statement))

    def export_snapshot(self) -> Path:
        """
        Export SQLite data to JSON snapshot (SQLite mode only).

        Returns:
            Path to exported JSON file
        """
        if not self.use_db:
            raise NotImplementedError("Export only works from SQLite mode")

        export_path = self.tasks_dir / f"work_queue_{self.project}_snapshot.json"

        with self._get_session() as session:
            tasks = session.query(Task).all()

            data = {
                "project": self.project,
                "exported_at": datetime.utcnow().isoformat(),
                "tasks": [
                    {
                        "id": t.id,
                        "feature_id": t.feature_id,
                        "description": t.description,
                        "status": t.status,
                        "retry_budget": t.retry_budget,
                        "retries_used": t.retries_used,
                        "created_at": t.created_at.isoformat() if t.created_at else None
                    }
                    for t in tasks
                ]
            }

        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2)

        return export_path

    def import_snapshot(self, json_path: Path) -> None:
        """
        Import JSON snapshot into SQLite (SQLite mode only).

        Args:
            json_path: Path to JSON file
        """
        if not self.use_db:
            raise NotImplementedError("Import only works in SQLite mode")

        with open(json_path) as f:
            data = json.load(f)

        with self._get_session() as session:
            for task_data in data.get("tasks", []):
                # Check if task already exists
                existing = session.query(Task).filter_by(id=task_data["id"]).first()
                if existing:
                    continue

                # Ensure feature exists (create minimal feature if needed)
                feature_id = task_data.get("feature_id")
                if feature_id:
                    feature = session.query(Feature).filter_by(id=feature_id).first()
                    if not feature:
                        # Create minimal feature
                        feature = Feature(
                            id=feature_id,
                            name=f"Auto-imported feature {feature_id}",
                            status="pending"
                        )
                        session.add(feature)

                # Import task
                task = Task(
                    id=task_data["id"],
                    feature_id=feature_id or "FEAT-UNKNOWN",
                    description=task_data["description"],
                    status=task_data.get("status", "pending"),
                    retry_budget=task_data.get("retry_budget", 15),
                    retries_used=task_data.get("retries_used", 0)
                )
                session.add(task)
