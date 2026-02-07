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

from orchestration.models import Base, Epic, Feature, Task, Checkpoint, WorkItem
from orchestration.session_state import SessionState


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

    # ==================== Phase 2: Checkpoint Methods ====================

    def checkpoint(
        self,
        task_id: str,
        iteration_count: int,
        verdict: str,
        session_ref: str,
        recoverable: bool = True,
        agent_output_summary: str = None,
        next_steps: List[str] = None,
        error_context: str = None
    ) -> str:
        """
        Create a checkpoint for task resumption (Phase 2: Stateless Memory).

        Args:
            task_id: Task ID being checkpointed
            iteration_count: Current iteration number
            verdict: Ralph verdict (PASS, FAIL, BLOCKED, RETRY_NEEDED)
            session_ref: Reference to session file (SESSION-{id})
            recoverable: Whether task can be resumed from this checkpoint
            agent_output_summary: Summarized agent output
            next_steps: List of next steps for resumption
            error_context: Error details if any

        Returns:
            Checkpoint ID
        """
        if not self.use_db:
            raise NotImplementedError("Checkpoints not supported in JSON mode")

        checkpoint_id = f"CP-{task_id}-{iteration_count}-{uuid.uuid4().hex[:8].upper()}"

        with self._get_session() as session:
            # Update task's session reference
            task = session.query(Task).filter_by(id=task_id).first()
            if task:
                task.session_ref = session_ref

            # Create checkpoint
            checkpoint = Checkpoint(
                id=checkpoint_id,
                task_id=task_id,
                iteration_count=iteration_count,
                verdict=verdict,
                session_ref=session_ref,
                recoverable=recoverable,
                agent_output_summary=agent_output_summary,
                next_steps=next_steps,
                error_context=error_context
            )
            session.add(checkpoint)

        return checkpoint_id

    def get_latest_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent checkpoint for a task.

        Args:
            task_id: Task ID

        Returns:
            Checkpoint dict or None if no checkpoints exist
        """
        if not self.use_db:
            raise NotImplementedError("Checkpoints not supported in JSON mode")

        with self._get_session() as session:
            checkpoint = session.query(Checkpoint).filter_by(
                task_id=task_id
            ).order_by(
                Checkpoint.timestamp.desc()
            ).first()

            if not checkpoint:
                return None

            return {
                "id": checkpoint.id,
                "task_id": checkpoint.task_id,
                "iteration_count": checkpoint.iteration_count,
                "verdict": checkpoint.verdict,
                "timestamp": checkpoint.timestamp.isoformat() if checkpoint.timestamp else None,
                "session_ref": checkpoint.session_ref,
                "recoverable": checkpoint.recoverable,
                "agent_output_summary": checkpoint.agent_output_summary,
                "next_steps": checkpoint.next_steps,
                "error_context": checkpoint.error_context
            }

    def get_all_checkpoints(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all checkpoints for a task.

        Args:
            task_id: Task ID

        Returns:
            List of checkpoint dicts ordered by timestamp (oldest first)
        """
        if not self.use_db:
            raise NotImplementedError("Checkpoints not supported in JSON mode")

        with self._get_session() as session:
            checkpoints = session.query(Checkpoint).filter_by(
                task_id=task_id
            ).order_by(
                Checkpoint.timestamp.asc()
            ).all()

            return [
                {
                    "id": cp.id,
                    "task_id": cp.task_id,
                    "iteration_count": cp.iteration_count,
                    "verdict": cp.verdict,
                    "timestamp": cp.timestamp.isoformat() if cp.timestamp else None,
                    "session_ref": cp.session_ref,
                    "recoverable": cp.recoverable
                }
                for cp in checkpoints
            ]

    def get_recoverable_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks that can be resumed (have recoverable checkpoints).

        Returns:
            List of task dicts with their latest checkpoint info
        """
        if not self.use_db:
            raise NotImplementedError("Checkpoints not supported in JSON mode")

        with self._get_session() as session:
            # Subquery for latest checkpoint per task
            from sqlalchemy import func
            latest_cp_subq = session.query(
                Checkpoint.task_id,
                func.max(Checkpoint.timestamp).label('max_timestamp')
            ).group_by(Checkpoint.task_id).subquery()

            # Join to get full checkpoint info
            results = session.query(Task, Checkpoint).join(
                Checkpoint, Task.id == Checkpoint.task_id
            ).join(
                latest_cp_subq,
                (Checkpoint.task_id == latest_cp_subq.c.task_id) &
                (Checkpoint.timestamp == latest_cp_subq.c.max_timestamp)
            ).filter(
                Checkpoint.recoverable == True,
                Task.status.in_(['in_progress', 'blocked'])
            ).all()

            return [
                {
                    "task_id": task.id,
                    "description": task.description,
                    "status": task.status,
                    "session_ref": task.session_ref,
                    "checkpoint": {
                        "id": cp.id,
                        "iteration_count": cp.iteration_count,
                        "verdict": cp.verdict,
                        "next_steps": cp.next_steps
                    }
                }
                for task, cp in results
            ]

    def mark_task_blocked(self, task_id: str, error_log: str = None) -> bool:
        """
        Mark a task as blocked (requires human decision).

        Args:
            task_id: Task ID
            error_log: Error context for the blockage

        Returns:
            True if updated, False if task not found
        """
        if self.use_db:
            with self._get_session() as session:
                task = session.query(Task).filter_by(id=task_id).first()
                if not task:
                    return False

                task.status = "blocked"
                if error_log:
                    task.error_log = error_log

                return True
        else:
            return self.update_status(task_id, "blocked")

    def mark_task_completed(self, task_id: str) -> bool:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID

        Returns:
            True if updated, False if task not found
        """
        return self.update_status(task_id, "completed")

    def get_task_session_ref(self, task_id: str) -> Optional[str]:
        """
        Get the session reference for a task.

        Args:
            task_id: Task ID

        Returns:
            Session reference (SESSION-{id}) or None
        """
        if not self.use_db:
            return None  # JSON mode doesn't support session refs

        with self._get_session() as session:
            task = session.query(Task).filter_by(id=task_id).first()
            return task.session_ref if task else None

    def set_task_session_ref(self, task_id: str, session_ref: str) -> bool:
        """
        Set the session reference for a task.

        Args:
            task_id: Task ID
            session_ref: Session reference (SESSION-{id})

        Returns:
            True if updated, False if task not found
        """
        if not self.use_db:
            return False  # JSON mode doesn't support session refs

        with self._get_session() as session:
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                return False

            task.session_ref = session_ref
            return True

    def get_next_ready(self) -> Optional[Dict[str, Any]]:
        """
        Get the next task ready for execution (pending or in_progress with recovery).

        This method is used by the autonomous loop to find tasks to work on.
        It skips blocked tasks unless they have a human decision.

        Returns:
            Task dict or None if no ready tasks
        """
        if self.use_db:
            with self._get_session() as session:
                # First, check for in_progress tasks that can be resumed
                in_progress = session.query(Task).join(Feature).filter(
                    Task.status == "in_progress",
                    Task.session_ref.isnot(None)
                ).order_by(
                    Feature.priority.asc(),
                    Task.updated_at.asc()
                ).first()

                if in_progress:
                    return {
                        "id": in_progress.id,
                        "feature_id": in_progress.feature_id,
                        "description": in_progress.description,
                        "status": in_progress.status,
                        "session_ref": in_progress.session_ref,
                        "retry_budget": in_progress.retry_budget,
                        "retries_used": in_progress.retries_used,
                        "resuming": True
                    }

                # Then, get next pending task
                return self.get_next_task()
        else:
            return self.get_next_task()

    # ==================== Phase 2: SessionState Integration ====================

    def checkpoint_with_session(
        self,
        task_id: str,
        iteration_count: int,
        verdict: str,
        session_data: Dict[str, Any],
        recoverable: bool = True,
        agent_output_summary: str = None,
        next_steps: List[str] = None,
        error_context: str = None
    ) -> str:
        """
        Create checkpoint and save session state atomically.

        This is the primary method for checkpointing in the autonomous loop.
        It creates a checkpoint in the database AND saves session data to disk.

        Args:
            task_id: Task ID being checkpointed
            iteration_count: Current iteration number
            verdict: Ralph verdict (PASS, FAIL, BLOCKED, RETRY_NEEDED)
            session_data: Dictionary with session state to save
            recoverable: Whether task can be resumed from this checkpoint
            agent_output_summary: Summarized agent output
            next_steps: List of next steps for resumption
            error_context: Error details if any

        Returns:
            Checkpoint ID
        """
        if not self.use_db:
            raise NotImplementedError("Session checkpointing not supported in JSON mode")

        # Create session state manager
        session = SessionState(task_id, self.project)

        # Ensure session data has required fields
        session_data.setdefault("iteration_count", iteration_count)
        session_data.setdefault("phase", "in_progress")
        session_data.setdefault("status", "in_progress" if verdict == "RETRY_NEEDED" else verdict.lower())

        # Save session state to disk
        session.save(session_data)

        # Get the session ID from the saved session
        try:
            saved_session = session.get_latest()
            session_ref = saved_session.get("id", f"SESSION-{task_id}")
        except FileNotFoundError:
            session_ref = f"SESSION-{task_id}"

        # Create checkpoint with session reference
        checkpoint_id = self.checkpoint(
            task_id=task_id,
            iteration_count=iteration_count,
            verdict=verdict,
            session_ref=session_ref,
            recoverable=recoverable,
            agent_output_summary=agent_output_summary,
            next_steps=next_steps,
            error_context=error_context
        )

        return checkpoint_id

    def load_session_for_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session state for a task.

        Retrieves the session data referenced by the task's session_ref.

        Args:
            task_id: Task ID

        Returns:
            Session data dictionary or None if not found
        """
        session_ref = self.get_task_session_ref(task_id)
        if not session_ref:
            return None

        try:
            return SessionState.load_by_id(session_ref)
        except FileNotFoundError:
            # Fallback: try loading by task_id with project
            try:
                return SessionState.load(task_id, self.project)
            except FileNotFoundError:
                return None

    def resume_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Prepare context for resuming a task.

        Combines task info, checkpoint info, and session state
        into a single context dictionary for the agent.

        Args:
            task_id: Task ID to resume

        Returns:
            Context dictionary for agent resumption, or None if not resumable
        """
        if not self.use_db:
            return None

        # Get task info
        task = self.get_task(task_id)
        if not task:
            return None

        # Get latest checkpoint
        checkpoint = self.get_latest_checkpoint(task_id)

        # Get session data
        session_data = self.load_session_for_task(task_id)

        # Build resumption context
        context = {
            "task_id": task_id,
            "description": task.get("description"),
            "status": task.get("status"),
            "resuming": True,
        }

        if checkpoint:
            context["checkpoint"] = {
                "iteration_count": checkpoint.get("iteration_count"),
                "verdict": checkpoint.get("verdict"),
                "next_steps": checkpoint.get("next_steps"),
            }

        if session_data:
            context["session"] = {
                "phase": session_data.get("phase"),
                "iteration_count": session_data.get("iteration_count"),
                "last_output": session_data.get("last_output"),
                "next_steps": session_data.get("next_steps"),
                "markdown_content": session_data.get("markdown_content"),
            }

        return context

    def mark_task_completed_with_cleanup(
        self,
        task_id: str,
        archive_session: bool = True
    ) -> bool:
        """
        Mark task as completed and optionally archive its session.

        Args:
            task_id: Task ID
            archive_session: Whether to archive the session file

        Returns:
            True if successful
        """
        if not self.update_status(task_id, "completed"):
            return False

        if archive_session:
            session = SessionState(task_id, self.project)
            session.archive()

        return True
