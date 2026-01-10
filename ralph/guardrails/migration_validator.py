"""
Alembic Migration Validator

Validates database migrations for safety and reversibility.

Required elements:
- upgrade() method
- downgrade() method (reversibility)
- Clear description
- No forbidden SQL patterns

Forbidden in production:
- DROP TABLE
- TRUNCATE
- DELETE without WHERE
- Migrations without downgrade()

Implementation: Phase 2 - Operator Team
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ralph.guardrails.deployment_patterns import (
    DeploymentViolation,
    scan_sql_for_violations
)


@dataclass
class MigrationValidationResult:
    """Result of migration validation."""
    is_valid: bool
    is_reversible: bool
    has_upgrade: bool
    has_downgrade: bool
    has_description: bool
    sql_violations: List[DeploymentViolation]
    errors: List[str]
    warnings: List[str]


def validate_alembic_migration(
    migration_path: Path,
    environment: str = "development"
) -> MigrationValidationResult:
    """
    Validate an Alembic migration file for safety and reversibility.

    Args:
        migration_path: Path to migration file
        environment: Target environment (development, staging, production)

    Returns:
        MigrationValidationResult with validation details
    """
    errors = []
    warnings = []
    has_upgrade = False
    has_downgrade = False
    has_description = False
    sql_violations = []

    if not migration_path.exists():
        errors.append(f"Migration file not found: {migration_path}")
        return MigrationValidationResult(
            is_valid=False,
            is_reversible=False,
            has_upgrade=False,
            has_downgrade=False,
            has_description=False,
            sql_violations=[],
            errors=errors,
            warnings=warnings
        )

    try:
        with open(migration_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse Python AST to find functions
        tree = ast.parse(content)

        # Check for required functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == "upgrade":
                    has_upgrade = True
                elif node.name == "downgrade":
                    has_downgrade = True

        # Check for description/docstring
        if '"""' in content or "'''" in content:
            has_description = True
        elif "# Revision:" in content or "# Description:" in content:
            has_description = True

        # Scan for SQL safety violations
        sql_violations = scan_sql_for_violations(content, str(migration_path))

        # Validation rules
        if not has_upgrade:
            errors.append("Missing upgrade() function")

        if not has_downgrade:
            if environment == "production":
                errors.append("Missing downgrade() function - REQUIRED for production")
            else:
                warnings.append("Missing downgrade() function - migration is not reversible")

        if not has_description:
            warnings.append("Missing description/docstring - add migration context")

        # Production-specific rules
        if environment == "production":
            # CRITICAL violations block production deployments
            critical_violations = [v for v in sql_violations if v.risk_level == "CRITICAL"]
            if critical_violations:
                errors.append(f"Found {len(critical_violations)} CRITICAL SQL violations - BLOCKED for production")

            # Check for empty downgrade()
            if has_downgrade:
                if _has_empty_downgrade(content):
                    errors.append("downgrade() method is empty - migration is not reversible")

        # Development/staging rules
        else:
            # Warn but don't block
            if sql_violations:
                warnings.append(f"Found {len(sql_violations)} SQL safety concerns - review before production")

        # Determine overall validity
        is_valid = len(errors) == 0
        is_reversible = has_downgrade and not _has_empty_downgrade(content)

    except Exception as e:
        errors.append(f"Failed to parse migration file: {e}")
        is_valid = False
        is_reversible = False

    return MigrationValidationResult(
        is_valid=is_valid,
        is_reversible=is_reversible,
        has_upgrade=has_upgrade,
        has_downgrade=has_downgrade,
        has_description=has_description,
        sql_violations=sql_violations,
        errors=errors,
        warnings=warnings
    )


def _has_empty_downgrade(content: str) -> bool:
    """
    Check if downgrade() function is empty (just 'pass' or empty).

    Args:
        content: Migration file content

    Returns:
        True if downgrade() is empty
    """
    # Parse to find downgrade function
    try:
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "downgrade":
                # Check if body is just 'pass' or empty
                if len(node.body) == 0:
                    return True
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    return True
                # Check if body is just docstring + pass
                if len(node.body) == 2:
                    if isinstance(node.body[0], ast.Expr) and isinstance(node.body[1], ast.Pass):
                        return True

                return False

        # downgrade() not found
        return True

    except Exception:
        return True


def validate_migration_directory(
    migrations_dir: Path,
    environment: str = "development"
) -> dict:
    """
    Validate all migrations in a directory.

    Args:
        migrations_dir: Path to migrations directory (e.g., alembic/versions/)
        environment: Target environment

    Returns:
        Dict with validation summary
    """
    if not migrations_dir.exists():
        return {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "reversible": 0,
            "non_reversible": 0,
            "errors": [f"Migrations directory not found: {migrations_dir}"]
        }

    migration_files = list(migrations_dir.glob("*.py"))
    # Filter out __init__.py
    migration_files = [f for f in migration_files if f.name != "__init__.py"]

    results = {
        "total": len(migration_files),
        "valid": 0,
        "invalid": 0,
        "reversible": 0,
        "non_reversible": 0,
        "files": {},
        "errors": []
    }

    for migration_file in migration_files:
        result = validate_alembic_migration(migration_file, environment)

        results["files"][migration_file.name] = result

        if result.is_valid:
            results["valid"] += 1
        else:
            results["invalid"] += 1

        if result.is_reversible:
            results["reversible"] += 1
        else:
            results["non_reversible"] += 1

        # Collect errors
        if result.errors:
            results["errors"].extend([
                f"{migration_file.name}: {error}"
                for error in result.errors
            ])

    return results


def format_migration_validation_report(result: MigrationValidationResult) -> str:
    """
    Format migration validation result into human-readable report.

    Args:
        result: Validation result

    Returns:
        Formatted report string
    """
    lines = []

    # Header
    if result.is_valid:
        lines.append("✅ MIGRATION VALIDATION PASSED")
    else:
        lines.append("🚫 MIGRATION VALIDATION FAILED")

    lines.append("=" * 60)

    # Required elements check
    lines.append("\nRequired Elements:")
    lines.append(f"  upgrade():     {'✅' if result.has_upgrade else '❌'}")
    lines.append(f"  downgrade():   {'✅' if result.has_downgrade else '❌'}")
    lines.append(f"  description:   {'✅' if result.has_description else '⚠️'}")
    lines.append(f"  reversible:    {'✅' if result.is_reversible else '❌'}")

    # SQL violations
    if result.sql_violations:
        lines.append(f"\n🚫 SQL Safety Violations: {len(result.sql_violations)}")
        for v in result.sql_violations:
            lines.append(f"  Line {v.line_number}: {v.reason}")
            lines.append(f"    Code: {v.line_content}")

    # Errors
    if result.errors:
        lines.append(f"\n❌ Errors ({len(result.errors)}):")
        for error in result.errors:
            lines.append(f"  - {error}")

    # Warnings
    if result.warnings:
        lines.append(f"\n⚠️ Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            lines.append(f"  - {warning}")

    lines.append("\n" + "=" * 60)

    if result.is_valid:
        lines.append("✅ Migration is SAFE to deploy")
    else:
        lines.append("🚫 Migration BLOCKED - fix errors before deployment")

    return "\n".join(lines)
