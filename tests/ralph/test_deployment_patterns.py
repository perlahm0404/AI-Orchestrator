"""
Tests for deployment_patterns.py

Verifies SQL and S3 safety scanners detect dangerous patterns.

Test Coverage:
- SQL patterns: DROP DATABASE, DROP TABLE, TRUNCATE, DELETE without WHERE
- S3 patterns: Bucket deletion, bulk object deletion
- Safety-exception markers
- Violation reporting

Implementation: Phase 2 - Operator Team
"""

import pytest
from pathlib import Path
import tempfile
import os

from ralph.guardrails.deployment_patterns import (
    DeploymentViolation,
    scan_sql_for_violations,
    scan_code_for_s3_violations,
    scan_migration_file,
    scan_directory_for_s3_violations,
    format_violation_report,
)


class TestSQLSafetyScanner:
    """Tests for SQL safety pattern detection."""

    def test_drop_database_detected(self):
        """DROP DATABASE should be detected."""
        sql_content = """
        -- Migration script
        DROP DATABASE old_database;
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        assert len(violations) > 0
        assert any("DROP DATABASE" in v.reason for v in violations)
        assert any(v.risk_level == "CRITICAL" for v in violations)

    def test_drop_table_detected(self):
        """DROP TABLE should be detected."""
        sql_content = """
        ALTER TABLE users ADD COLUMN email VARCHAR(255);
        DROP TABLE old_users;
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        assert len(violations) > 0
        assert any("DROP TABLE" in v.reason for v in violations)
        assert any(v.risk_level == "CRITICAL" for v in violations)

    def test_truncate_table_detected(self):
        """TRUNCATE TABLE should be detected."""
        sql_content = """
        TRUNCATE TABLE logs;
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        assert len(violations) > 0
        assert any("TRUNCATE" in v.reason for v in violations)
        assert any(v.risk_level == "CRITICAL" for v in violations)

    def test_truncate_without_table_keyword_detected(self):
        """TRUNCATE without TABLE keyword should be detected."""
        sql_content = """
        TRUNCATE logs;
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        assert len(violations) > 0
        assert any("TRUNCATE" in v.reason for v in violations)

    def test_delete_without_where_detected(self):
        """DELETE without WHERE clause should be detected."""
        sql_content = """
        DELETE FROM users;
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        assert len(violations) > 0
        assert any("DELETE without WHERE" in v.reason for v in violations)
        assert any(v.risk_level == "CRITICAL" for v in violations)

    def test_delete_with_where_allowed(self):
        """DELETE with WHERE clause should be allowed (with warning)."""
        sql_content = """
        DELETE FROM users WHERE id = 123;
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        # May have HIGH risk warning, but not CRITICAL
        critical_violations = [v for v in violations if v.risk_level == "CRITICAL"]
        assert len(critical_violations) == 0

    def test_update_without_where_detected(self):
        """UPDATE without WHERE clause should be detected."""
        sql_content = """
        UPDATE users SET active = false;
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        # Should have at least a warning
        assert len(violations) > 0

    def test_case_insensitive_detection(self):
        """SQL patterns should be case-insensitive."""
        sql_content = """
        drop table old_users;
        DELETE FROM logs;
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        assert len(violations) >= 2

    def test_comments_ignored(self):
        """SQL comments should be ignored."""
        sql_content = """
        -- DROP TABLE users;  # This is just a comment
        # DELETE FROM logs;   # Also a comment
        CREATE TABLE new_users (id INT);
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        # No violations from commented code
        assert len(violations) == 0

    def test_safety_exception_marker(self):
        """Lines with safety-exception marker should be skipped."""
        sql_content = """
        DROP TABLE temp_table;  -- safety-exception: temporary test table
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        assert len(violations) == 0

    def test_multiple_violations_detected(self):
        """Multiple violations in same content should all be detected."""
        sql_content = """
        DROP TABLE old_users;
        TRUNCATE logs;
        DELETE FROM sessions;
        """

        violations = scan_sql_for_violations(sql_content, "test_migration.sql")

        assert len(violations) >= 3


class TestS3SafetyScanner:
    """Tests for S3 safety pattern detection."""

    def test_delete_bucket_detected(self):
        """S3 delete_bucket should be detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import boto3
s3 = boto3.client('s3')
s3.delete_bucket(Bucket='my-bucket')
            """)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_code_for_s3_violations(file_path)

            assert len(violations) > 0
            assert any("bucket deletion" in v.reason.lower() for v in violations)
            assert any(v.risk_level == "CRITICAL" for v in violations)

        finally:
            os.unlink(file_path)

    def test_boto3_delete_bucket_detected(self):
        """boto3 delete_bucket should be detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import boto3
client = boto3.client('s3')
response = client.delete_bucket(Bucket='old-bucket')
            """)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_code_for_s3_violations(file_path)

            assert len(violations) > 0
            assert any(v.risk_level == "CRITICAL" for v in violations)

        finally:
            os.unlink(file_path)

    def test_awslocal_s3_rb_detected(self):
        """awslocal s3 rb (remove bucket) should be detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write("""
#!/bin/bash
awslocal s3 rb s3://my-bucket --force
            """)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_code_for_s3_violations(file_path)

            assert len(violations) > 0
            assert any("remove bucket" in v.reason.lower() for v in violations)
            assert any(v.risk_level == "CRITICAL" for v in violations)

        finally:
            os.unlink(file_path)

    def test_aws_s3_rb_detected(self):
        """aws s3 rb (remove bucket) should be detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write("""
#!/bin/bash
aws s3 rb s3://production-bucket
            """)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_code_for_s3_violations(file_path)

            assert len(violations) > 0
            assert any(v.risk_level == "CRITICAL" for v in violations)

        finally:
            os.unlink(file_path)

    def test_delete_objects_detected(self):
        """S3 delete_objects (bulk deletion) should be detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
s3_client.delete_objects(
    Bucket='my-bucket',
    Delete={'Objects': objects_to_delete}
)
            """)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_code_for_s3_violations(file_path)

            assert len(violations) > 0
            assert any("bulk" in v.reason.lower() for v in violations)

        finally:
            os.unlink(file_path)

    def test_safety_exception_marker_s3(self):
        """Lines with safety-exception marker should be skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
s3.delete_bucket(Bucket='test-bucket')  # safety-exception: test cleanup
            """)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_code_for_s3_violations(file_path)

            assert len(violations) == 0

        finally:
            os.unlink(file_path)

    def test_comments_ignored_s3(self):
        """Comments should be ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
# s3.delete_bucket(Bucket='my-bucket')
// s3.delete_bucket(Bucket='another-bucket')
# This is just documentation about delete_bucket
            """)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_code_for_s3_violations(file_path)

            assert len(violations) == 0

        finally:
            os.unlink(file_path)


class TestMigrationFileScanning:
    """Tests for migration file scanning."""

    def test_scan_migration_file_detects_violations(self):
        """scan_migration_file should detect SQL violations."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def upgrade():
    op.execute('DROP TABLE old_users')

def downgrade():
    pass
            """)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_migration_file(file_path)

            assert len(violations) > 0
            assert any("DROP TABLE" in v.reason for v in violations)

        finally:
            os.unlink(file_path)

    def test_scan_nonexistent_file(self):
        """scan_migration_file should handle nonexistent files gracefully."""
        violations = scan_migration_file(Path("/nonexistent/migration.py"))

        assert len(violations) == 0


class TestDirectoryScanning:
    """Tests for directory scanning."""

    def test_scan_directory_for_s3_violations(self):
        """scan_directory_for_s3_violations should scan all files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test file with violation
            test_file = tmpdir_path / "test.py"
            test_file.write_text("""
import boto3
s3 = boto3.client('s3')
s3.delete_bucket(Bucket='my-bucket')
            """)

            violations = scan_directory_for_s3_violations(tmpdir_path, tmpdir_path)

            assert len(violations) > 0
            assert any("bucket deletion" in v.reason.lower() for v in violations)

    def test_scan_nonexistent_directory(self):
        """scan_directory_for_s3_violations should handle nonexistent dirs."""
        violations = scan_directory_for_s3_violations(Path("/nonexistent"))

        assert len(violations) == 0


class TestViolationReporting:
    """Tests for violation report formatting."""

    def test_format_empty_violations(self):
        """format_violation_report should handle empty list."""
        report = format_violation_report([])

        assert "No deployment safety violations detected" in report

    def test_format_critical_violations(self):
        """format_violation_report should highlight CRITICAL violations."""
        violations = [
            DeploymentViolation(
                file_path="migration.sql",
                line_number=10,
                pattern="DROP TABLE",
                line_content="DROP TABLE users;",
                reason="DROP TABLE causes irreversible data loss",
                risk_level="CRITICAL"
            )
        ]

        report = format_violation_report(violations)

        assert "CRITICAL" in report
        assert "DROP TABLE" in report
        assert "migration.sql:10" in report

    def test_format_multiple_risk_levels(self):
        """format_violation_report should group by risk level."""
        violations = [
            DeploymentViolation(
                file_path="migration.sql",
                line_number=10,
                pattern="DROP TABLE",
                line_content="DROP TABLE users;",
                reason="DROP TABLE causes irreversible data loss",
                risk_level="CRITICAL"
            ),
            DeploymentViolation(
                file_path="migration.sql",
                line_number=15,
                pattern="DELETE FROM",
                line_content="DELETE FROM logs WHERE id > 100;",
                reason="DELETE with WHERE - review required",
                risk_level="HIGH"
            ),
            DeploymentViolation(
                file_path="service.py",
                line_number=25,
                pattern="delete_object",
                line_content="s3.delete_object(Key='file.txt')",
                reason="S3 object deletion - ensure soft delete",
                risk_level="MEDIUM"
            )
        ]

        report = format_violation_report(violations)

        assert "CRITICAL" in report
        assert "HIGH" in report
        assert "MEDIUM" in report
        assert report.index("CRITICAL") < report.index("HIGH")
        assert report.index("HIGH") < report.index("MEDIUM")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
