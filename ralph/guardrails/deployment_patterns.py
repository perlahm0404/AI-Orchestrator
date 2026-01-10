"""
Deployment Safety Pattern Detection

Scans code and migrations for dangerous deployment patterns.

SQL Safety:
- DROP DATABASE, DROP TABLE, TRUNCATE
- DELETE without WHERE clause
- UPDATE without WHERE clause

S3 Safety:
- Bucket deletion (delete_bucket, s3 rb)
- Bulk object deletion
- Irreversible operations

Implementation: Phase 2 - Operator Team
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class DeploymentViolation:
    """A detected deployment safety violation."""
    file_path: str
    line_number: int
    pattern: str
    line_content: str
    reason: str
    risk_level: str  # CRITICAL, HIGH, MEDIUM


# SQL Safety Patterns
SQL_PATTERNS = [
    {
        "pattern": r"DROP\s+DATABASE",
        "reason": "DROP DATABASE causes irreversible data loss",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"DROP\s+TABLE",
        "reason": "DROP TABLE causes irreversible data loss",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"TRUNCATE\s+TABLE",
        "reason": "TRUNCATE TABLE causes irreversible data deletion",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"TRUNCATE\s+\w+",  # TRUNCATE without TABLE keyword
        "reason": "TRUNCATE causes irreversible data deletion",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"DELETE\s+FROM\s+\w+\s*;",  # DELETE without WHERE
        "reason": "DELETE without WHERE clause deletes all rows",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"DELETE\s+FROM\s+\w+\s*$",  # DELETE at end of line without WHERE
        "reason": "DELETE without WHERE clause deletes all rows",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"UPDATE\s+\w+\s+SET\s+.*;\s*$",  # UPDATE without WHERE
        "reason": "UPDATE without WHERE clause affects all rows",
        "risk_level": "HIGH"
    },
]

# S3 Safety Patterns
S3_PATTERNS = [
    {
        "pattern": r"\.delete_bucket\(",
        "reason": "S3 bucket deletion is irreversible",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"boto3.*delete_bucket",
        "reason": "S3 bucket deletion is irreversible",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"awslocal\s+s3\s+rb",
        "reason": "S3 remove bucket command (rb) is irreversible",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"aws\s+s3\s+rb",
        "reason": "S3 remove bucket command (rb) is irreversible",
        "risk_level": "CRITICAL"
    },
    {
        "pattern": r"\.delete_objects\(",
        "reason": "S3 bulk object deletion can cause data loss",
        "risk_level": "HIGH"
    },
    {
        "pattern": r"s3.*delete_object\(",
        "reason": "S3 object deletion - ensure soft delete is preferred",
        "risk_level": "MEDIUM"
    },
]


def scan_sql_for_violations(
    content: str,
    file_path: str = "migration.sql"
) -> List[DeploymentViolation]:
    """
    Scan SQL content for dangerous patterns.

    Args:
        content: SQL content to scan (migration file, SQL string, etc.)
        file_path: File path for reporting (default: "migration.sql")

    Returns:
        List of DeploymentViolation objects
    """
    violations = []

    # Split content into lines for scanning
    lines = content.split('\n')

    for line_num, line in enumerate(lines, start=1):
        # Skip comments
        if line.strip().startswith('--') or line.strip().startswith('#'):
            continue

        # Skip safety-exception marker
        if "safety-exception" in line:
            continue

        # Check for SQL patterns (case-insensitive)
        for pattern_def in SQL_PATTERNS:
            pattern = pattern_def["pattern"]
            reason = pattern_def["reason"]
            risk_level = pattern_def["risk_level"]

            if re.search(pattern, line, re.IGNORECASE):
                violations.append(DeploymentViolation(
                    file_path=file_path,
                    line_number=line_num,
                    pattern=pattern,
                    line_content=line.strip(),
                    reason=reason,
                    risk_level=risk_level
                ))

    return violations


def scan_code_for_s3_violations(
    file_path: Path,
    project_path: Path = None
) -> List[DeploymentViolation]:
    """
    Scan code file for dangerous S3 operations.

    Args:
        file_path: Path to code file to scan
        project_path: Root path of project (for relative path reporting)

    Returns:
        List of DeploymentViolation objects
    """
    violations = []

    if not file_path.exists():
        return violations

    # Get relative path for reporting
    if project_path:
        try:
            rel_path = str(file_path.relative_to(project_path))
        except ValueError:
            rel_path = str(file_path)
    else:
        rel_path = str(file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                # Skip comments
                if line.strip().startswith('#') or line.strip().startswith('//'):
                    continue

                # Skip safety-exception marker
                if "safety-exception" in line:
                    continue

                # Check for S3 patterns
                for pattern_def in S3_PATTERNS:
                    pattern = pattern_def["pattern"]
                    reason = pattern_def["reason"]
                    risk_level = pattern_def["risk_level"]

                    if re.search(pattern, line):
                        violations.append(DeploymentViolation(
                            file_path=rel_path,
                            line_number=line_num,
                            pattern=pattern,
                            line_content=line.strip(),
                            reason=reason,
                            risk_level=risk_level
                        ))
    except Exception:
        # Skip files that can't be read
        pass

    return violations


def scan_migration_file(migration_path: Path) -> List[DeploymentViolation]:
    """
    Scan an Alembic migration file for SQL safety violations.

    Args:
        migration_path: Path to migration file

    Returns:
        List of DeploymentViolation objects
    """
    if not migration_path.exists():
        return []

    try:
        with open(migration_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Scan SQL content in the migration
        return scan_sql_for_violations(content, str(migration_path))

    except Exception:
        return []


def scan_directory_for_s3_violations(
    directory: Path,
    project_path: Path = None,
    file_patterns: List[str] = None
) -> List[DeploymentViolation]:
    """
    Scan directory for S3 safety violations.

    Args:
        directory: Directory to scan
        project_path: Root path of project (for relative path reporting)
        file_patterns: File patterns to scan (e.g., ["*.py", "*.sh"])

    Returns:
        List of DeploymentViolation objects
    """
    violations = []

    if not directory.exists() or not directory.is_dir():
        return violations

    # Default patterns if not specified
    if file_patterns is None:
        file_patterns = ["*.py", "*.js", "*.ts", "*.sh"]

    # Scan all matching files
    for pattern in file_patterns:
        for file_path in directory.rglob(pattern):
            if file_path.is_file():
                violations.extend(
                    scan_code_for_s3_violations(file_path, project_path)
                )

    return violations


def format_violation_report(violations: List[DeploymentViolation]) -> str:
    """
    Format violations into a human-readable report.

    Args:
        violations: List of violations to report

    Returns:
        Formatted report string
    """
    if not violations:
        return "✅ No deployment safety violations detected."

    # Group by risk level
    critical = [v for v in violations if v.risk_level == "CRITICAL"]
    high = [v for v in violations if v.risk_level == "HIGH"]
    medium = [v for v in violations if v.risk_level == "MEDIUM"]

    report = []
    report.append(f"🚫 {len(violations)} DEPLOYMENT SAFETY VIOLATIONS DETECTED")
    report.append("=" * 60)

    if critical:
        report.append(f"\n🔴 CRITICAL ({len(critical)}):")
        for v in critical:
            report.append(f"  {v.file_path}:{v.line_number}")
            report.append(f"    Pattern: {v.pattern}")
            report.append(f"    Reason: {v.reason}")
            report.append(f"    Code: {v.line_content}")

    if high:
        report.append(f"\n🟠 HIGH ({len(high)}):")
        for v in high:
            report.append(f"  {v.file_path}:{v.line_number}")
            report.append(f"    Pattern: {v.pattern}")
            report.append(f"    Reason: {v.reason}")
            report.append(f"    Code: {v.line_content}")

    if medium:
        report.append(f"\n🟡 MEDIUM ({len(medium)}):")
        for v in medium:
            report.append(f"  {v.file_path}:{v.line_number}")
            report.append(f"    Pattern: {v.pattern}")
            report.append(f"    Reason: {v.reason}")
            report.append(f"    Code: {v.line_content}")

    report.append("\n" + "=" * 60)
    report.append("ACTION REQUIRED: Fix violations before deployment")

    return "\n".join(report)
