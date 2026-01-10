"""
Migration Agent

Validates and executes database migrations safely.

Responsibilities:
- Validate migration files (check for downgrade(), SQL safety)
- Execute migrations in target environment
- Verify migration success
- Support rollback if migration fails

Governance: Operator Team (L0.5 autonomy)
- Production migrations ALWAYS require approval
- Must have downgrade() method for production
- No DROP/TRUNCATE in production migrations

Implementation: Phase 2 - Operator Team
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ralph.guardrails.migration_validator import (
    MigrationValidationResult,
    format_migration_validation_report,
    validate_alembic_migration,
    validate_migration_directory
)


@dataclass
class MigrationTask:
    """Task specification for migration."""
    migrations_path: Path
    environment: str
    migration_file: Optional[str] = None  # Specific migration, or None for all


@dataclass
class MigrationResult:
    """Result of migration execution."""
    success: bool
    migrations_run: List[str]
    validation_results: List[MigrationValidationResult]
    errors: List[str]
    warnings: List[str]


class MigrationAgent:
    """
    Agent for validating and executing database migrations.
    """

    def __init__(self, project_path: Path):
        """
        Initialize migration agent.

        Args:
            project_path: Root path of project
        """
        self.project_path = project_path

    def execute(self, task: MigrationTask) -> MigrationResult:
        """
        Execute migration task with validation.

        Args:
            task: Migration task specification

        Returns:
            MigrationResult with outcome
        """
        errors = []
        warnings = []
        migrations_run = []
        validation_results = []

        # Validate migrations first
        if task.migration_file:
            # Validate single migration
            migration_path = task.migrations_path / task.migration_file
            result = validate_alembic_migration(migration_path, task.environment)
            validation_results.append(result)

            if not result.is_valid:
                errors.append(f"Migration validation failed: {task.migration_file}")
                errors.extend(result.errors)
                return MigrationResult(
                    success=False,
                    migrations_run=[],
                    validation_results=validation_results,
                    errors=errors,
                    warnings=warnings
                )

        else:
            # Validate all migrations
            dir_result = validate_migration_directory(task.migrations_path, task.environment)

            if dir_result["invalid"] > 0:
                errors.extend(dir_result["errors"])
                return MigrationResult(
                    success=False,
                    migrations_run=[],
                    validation_results=[],
                    errors=errors,
                    warnings=warnings
                )

        # Execute migrations (if validation passed)
        try:
            # Run Alembic upgrade
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                errors.append(f"Migration execution failed: {result.stderr}")
                return MigrationResult(
                    success=False,
                    migrations_run=migrations_run,
                    validation_results=validation_results,
                    errors=errors,
                    warnings=warnings
                )

            # Parse output to extract migrations run
            # (Simplified - real implementation would parse Alembic output)
            migrations_run.append("upgrade completed")

            return MigrationResult(
                success=True,
                migrations_run=migrations_run,
                validation_results=validation_results,
                errors=[],
                warnings=warnings
            )

        except subprocess.TimeoutExpired:
            errors.append("Migration timed out after 10 minutes")
            return MigrationResult(
                success=False,
                migrations_run=migrations_run,
                validation_results=validation_results,
                errors=errors,
                warnings=warnings
            )

        except Exception as e:
            errors.append(f"Unexpected error running migrations: {e}")
            return MigrationResult(
                success=False,
                migrations_run=migrations_run,
                validation_results=validation_results,
                errors=errors,
                warnings=warnings
            )

    def validate_only(self, task: MigrationTask) -> MigrationResult:
        """
        Validate migrations without executing them.

        Args:
            task: Migration task specification

        Returns:
            MigrationResult with validation outcome
        """
        errors = []
        warnings = []
        validation_results = []

        if task.migration_file:
            # Validate single migration
            migration_path = task.migrations_path / task.migration_file
            result = validate_alembic_migration(migration_path, task.environment)
            validation_results.append(result)

            if not result.is_valid:
                errors.extend(result.errors)
            if result.warnings:
                warnings.extend(result.warnings)

        else:
            # Validate all migrations
            dir_result = validate_migration_directory(task.migrations_path, task.environment)

            if dir_result["invalid"] > 0:
                errors.extend(dir_result["errors"])

        return MigrationResult(
            success=len(errors) == 0,
            migrations_run=[],
            validation_results=validation_results,
            errors=errors,
            warnings=warnings
        )

    def get_approval_prompt(self, task: MigrationTask) -> str:
        """
        Generate approval prompt for migration.

        Args:
            task: Migration task

        Returns:
            Formatted approval prompt
        """
        lines = []
        lines.append("=" * 60)
        lines.append("MIGRATION APPROVAL REQUIRED")
        lines.append("=" * 60)
        lines.append(f"Environment: {task.environment.upper()}")
        lines.append(f"Migrations Path: {task.migrations_path}")

        if task.migration_file:
            lines.append(f"Target Migration: {task.migration_file}")
        else:
            lines.append("Target Migration: ALL (upgrade to head)")

        # Show validation summary
        validation = self.validate_only(task)

        if validation.validation_results:
            lines.append("\nValidation Results:")
            for result in validation.validation_results:
                report = format_migration_validation_report(result)
                lines.append(report)

        if validation.errors:
            lines.append(f"\n❌ Validation Errors: {len(validation.errors)}")
            for error in validation.errors:
                lines.append(f"  - {error}")

        if validation.warnings:
            lines.append(f"\n⚠️ Warnings: {len(validation.warnings)}")
            for warning in validation.warnings:
                lines.append(f"  - {warning}")

        lines.append("\n" + "=" * 60)
        lines.append("\nProceed with migration? [Y/N]")

        return "\n".join(lines)
