"""
Test SQLite schema for work queue.

TDD: These tests are written BEFORE the schema implementation.
They define the expected behavior of our database schema.
"""

import pytest
import sqlite3
from pathlib import Path


@pytest.fixture
def db_connection(tmp_path):
    """Create a temporary SQLite database for testing."""
    db_path = tmp_path / "test_queue.db"
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()


@pytest.fixture
def schema_db(db_connection, tmp_path):
    """Apply schema to test database."""
    # This will fail initially (RED) because schema.sql doesn't exist yet
    schema_path = Path(__file__).parent.parent.parent / "tasks" / "schema.sql"

    if schema_path.exists():
        with open(schema_path) as f:
            db_connection.executescript(f.read())

    return db_connection


class TestSchemaStructure:
    """Test that all required tables and columns exist."""

    def test_epics_table_exists(self, schema_db):
        """Epics table should exist with correct columns."""
        cursor = schema_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='epics'"
        )
        assert cursor.fetchone() is not None, "epics table should exist"

    def test_epics_columns(self, schema_db):
        """Epics table should have all required columns."""
        cursor = schema_db.execute("PRAGMA table_info(epics)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type

        assert "id" in columns, "epics should have id column"
        assert "name" in columns, "epics should have name column"
        assert "description" in columns, "epics should have description column"
        assert "status" in columns, "epics should have status column"
        assert "created_at" in columns, "epics should have created_at column"
        assert "updated_at" in columns, "epics should have updated_at column"

    def test_features_table_exists(self, schema_db):
        """Features table should exist with correct columns."""
        cursor = schema_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='features'"
        )
        assert cursor.fetchone() is not None, "features table should exist"

    def test_features_columns(self, schema_db):
        """Features table should have all required columns."""
        cursor = schema_db.execute("PRAGMA table_info(features)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "epic_id" in columns, "features should have epic_id FK"
        assert "name" in columns
        assert "description" in columns
        assert "status" in columns
        assert "priority" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_tasks_table_exists(self, schema_db):
        """Tasks table should exist with correct columns."""
        cursor = schema_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
        )
        assert cursor.fetchone() is not None, "tasks table should exist"

    def test_tasks_columns(self, schema_db):
        """Tasks table should have all required columns."""
        cursor = schema_db.execute("PRAGMA table_info(tasks)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "feature_id" in columns, "tasks should have feature_id FK"
        assert "description" in columns
        assert "status" in columns
        assert "retry_budget" in columns, "tasks should track retry budget"
        assert "retries_used" in columns, "tasks should track retries used"
        assert "created_at" in columns
        assert "updated_at" in columns
        assert "completed_at" in columns

    def test_test_cases_table_exists(self, schema_db):
        """Test cases table should exist."""
        cursor = schema_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_cases'"
        )
        assert cursor.fetchone() is not None, "test_cases table should exist"

    def test_test_cases_columns(self, schema_db):
        """Test cases table should have all required columns."""
        cursor = schema_db.execute("PRAGMA table_info(test_cases)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "task_id" in columns
        assert "feature_id" in columns
        assert "description" in columns
        assert "status" in columns
        assert "created_at" in columns


class TestForeignKeys:
    """Test that foreign key constraints are properly defined."""

    def test_features_epic_fk(self, schema_db):
        """Features should have FK to epics with CASCADE delete."""
        cursor = schema_db.execute("PRAGMA foreign_key_list(features)")
        fks = cursor.fetchall()

        epic_fk = [fk for fk in fks if fk[2] == 'epics' and fk[3] == 'epic_id']
        assert len(epic_fk) > 0, "features should have FK to epics"

    def test_tasks_feature_fk(self, schema_db):
        """Tasks should have FK to features with CASCADE delete."""
        cursor = schema_db.execute("PRAGMA foreign_key_list(tasks)")
        fks = cursor.fetchall()

        feature_fk = [fk for fk in fks if fk[2] == 'features' and fk[3] == 'feature_id']
        assert len(feature_fk) > 0, "tasks should have FK to features"

    def test_test_cases_task_fk(self, schema_db):
        """Test cases should have FK to tasks."""
        cursor = schema_db.execute("PRAGMA foreign_key_list(test_cases)")
        fks = cursor.fetchall()

        task_fk = [fk for fk in fks if fk[2] == 'tasks']
        assert len(task_fk) > 0, "test_cases should have FK to tasks"


class TestIndexes:
    """Test that indexes exist for performance."""

    def test_features_epic_id_index(self, schema_db):
        """Features should have index on epic_id for fast lookups."""
        cursor = schema_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='features'"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        # Check for index on epic_id (name may vary)
        has_epic_index = any('epic' in idx.lower() for idx in indexes if idx)
        assert has_epic_index, "features should have index on epic_id"

    def test_tasks_feature_id_index(self, schema_db):
        """Tasks should have index on feature_id."""
        cursor = schema_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='tasks'"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        has_feature_index = any('feature' in idx.lower() for idx in indexes if idx)
        assert has_feature_index, "tasks should have index on feature_id"

    def test_tasks_status_index(self, schema_db):
        """Tasks should have index on status for filtering."""
        cursor = schema_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='tasks'"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        has_status_index = any('status' in idx.lower() for idx in indexes if idx)
        assert has_status_index, "tasks should have index on status"


class TestDataIntegrity:
    """Test that data integrity constraints work."""

    def test_epic_status_values(self, schema_db):
        """Epic status should only accept valid values."""
        schema_db.execute(
            "INSERT INTO epics (id, name, status) VALUES ('epic-1', 'Test Epic', 'pending')"
        )

        # Valid statuses should work
        for status in ['pending', 'in_progress', 'completed', 'blocked']:
            schema_db.execute(
                f"UPDATE epics SET status = '{status}' WHERE id = 'epic-1'"
            )

        # Invalid status should fail
        with pytest.raises(sqlite3.IntegrityError):
            schema_db.execute(
                "UPDATE epics SET status = 'invalid_status' WHERE id = 'epic-1'"
            )

    def test_cascade_delete_epic_to_features(self, schema_db):
        """Deleting an epic should cascade delete its features."""
        # Create epic and feature
        schema_db.execute(
            "INSERT INTO epics (id, name, status) VALUES ('epic-1', 'Test', 'pending')"
        )
        schema_db.execute(
            "INSERT INTO features (id, epic_id, name, status, priority) VALUES ('feat-1', 'epic-1', 'Test', 'pending', 2)"
        )

        # Delete epic
        schema_db.execute("DELETE FROM epics WHERE id = 'epic-1'")

        # Feature should be deleted
        cursor = schema_db.execute("SELECT COUNT(*) FROM features WHERE id = 'feat-1'")
        assert cursor.fetchone()[0] == 0, "features should be cascade deleted"

    def test_default_values(self, schema_db):
        """Test that default values are set correctly."""
        # Insert minimal epic
        schema_db.execute(
            "INSERT INTO epics (id, name, status) VALUES ('epic-1', 'Test', 'pending')"
        )

        # Check defaults
        cursor = schema_db.execute("SELECT created_at, updated_at FROM epics WHERE id = 'epic-1'")
        row = cursor.fetchone()

        assert row[0] is not None, "created_at should have default value"
        assert row[1] is not None, "updated_at should have default value"


class TestSchemaVersion:
    """Test schema versioning for migrations."""

    def test_schema_version_table_exists(self, schema_db):
        """Schema version table should exist for tracking migrations."""
        cursor = schema_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        assert cursor.fetchone() is not None, "schema_version table should exist"

    def test_schema_version_columns(self, schema_db):
        """Schema version table should have version and applied_at columns."""
        cursor = schema_db.execute("PRAGMA table_info(schema_version)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "version" in columns
        assert "applied_at" in columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
