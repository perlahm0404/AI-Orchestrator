"""
Rollback Agent

Handles rollback on deployment failure.

Responsibilities:
- Rollback application to previous version
- Rollback database migrations (if reversible)
- Verify rollback success
- Report rollback outcome

Governance: Operator Team (L0.5 autonomy)
- Dev/Staging: Auto-rollback on failure
- Production: Manual approval required for rollback

Implementation: Phase 2 - Operator Team
"""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class RollbackTask:
    """Task specification for rollback."""
    environment: str
    previous_version: Optional[str] = None  # Version to rollback to
    rollback_migrations: bool = False
    migration_target: Optional[str] = None  # Migration to rollback to (revision ID)


@dataclass
class RollbackResult:
    """Result of rollback execution."""
    success: bool
    environment: str
    rolled_back_at: datetime
    version_restored: Optional[str]
    migrations_rolled_back: List[str]
    errors: List[str]
    warnings: List[str]


class RollbackAgent:
    """
    Agent for rolling back failed deployments.
    """

    def __init__(self, project_path: Path):
        """
        Initialize rollback agent.

        Args:
            project_path: Root path of project
        """
        self.project_path = project_path

    def execute(self, task: RollbackTask) -> RollbackResult:
        """
        Execute rollback task.

        Args:
            task: Rollback task specification

        Returns:
            RollbackResult with outcome
        """
        errors = []
        warnings = []
        migrations_rolled_back = []

        # Rollback migrations first (if requested)
        if task.rollback_migrations:
            migration_success, migration_errors = self._rollback_migrations(
                task.migration_target
            )

            if not migration_success:
                errors.extend(migration_errors)
                return RollbackResult(
                    success=False,
                    environment=task.environment,
                    rolled_back_at=datetime.now(),
                    version_restored=None,
                    migrations_rolled_back=[],
                    errors=errors,
                    warnings=warnings
                )

            migrations_rolled_back.append(task.migration_target or "downgrade -1")

        # Rollback application deployment
        app_success, app_errors, version_restored = self._rollback_application(
            task.previous_version
        )

        if not app_success:
            errors.extend(app_errors)
            return RollbackResult(
                success=False,
                environment=task.environment,
                rolled_back_at=datetime.now(),
                version_restored=None,
                migrations_rolled_back=migrations_rolled_back,
                errors=errors,
                warnings=warnings
            )

        # Verify rollback
        verify_success, verify_errors = self._verify_rollback()

        if not verify_success:
            warnings.extend(verify_errors)
            warnings.append("Rollback completed but verification failed")

        return RollbackResult(
            success=True,
            environment=task.environment,
            rolled_back_at=datetime.now(),
            version_restored=version_restored,
            migrations_rolled_back=migrations_rolled_back,
            errors=[],
            warnings=warnings
        )

    def _rollback_migrations(
        self,
        target: Optional[str] = None
    ) -> tuple[bool, List[str]]:
        """
        Rollback database migrations.

        Args:
            target: Migration revision to rollback to (None = downgrade -1)

        Returns:
            (success, errors)
        """
        try:
            # Run Alembic downgrade
            if target:
                cmd = ["alembic", "downgrade", target]
            else:
                cmd = ["alembic", "downgrade", "-1"]

            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                return False, [f"Migration rollback failed: {result.stderr}"]

            return True, []

        except subprocess.TimeoutExpired:
            return False, ["Migration rollback timed out after 5 minutes"]

        except Exception as e:
            return False, [f"Unexpected error rolling back migrations: {e}"]

    def _rollback_application(
        self,
        previous_version: Optional[str] = None
    ) -> tuple[bool, List[str], Optional[str]]:
        """
        Rollback application to previous version.

        Args:
            previous_version: Version to restore (None = previous deployment)

        Returns:
            (success, errors, version_restored)
        """
        try:
            # In real implementation: redeploy previous version
            # For now, just a placeholder

            version = previous_version or "previous"
            print(f"⏪ Rolling back application to {version}")

            return True, [], version

        except Exception as e:
            return False, [f"Application rollback failed: {e}"], None

    def _verify_rollback(self) -> tuple[bool, List[str]]:
        """
        Verify rollback was successful.

        Returns:
            (success, errors)
        """
        try:
            # Run health checks
            # In real implementation: check service endpoints, database, etc.
            print("🏥 Verifying rollback health")

            return True, []

        except Exception as e:
            return False, [f"Rollback verification failed: {e}"]

    def get_approval_prompt(self, task: RollbackTask) -> str:
        """
        Generate approval prompt for rollback (production only).

        Args:
            task: Rollback task

        Returns:
            Formatted approval prompt
        """
        lines = []
        lines.append("=" * 60)
        lines.append("ROLLBACK APPROVAL REQUIRED")
        lines.append("=" * 60)
        lines.append(f"Environment: {task.environment.upper()}")

        if task.previous_version:
            lines.append(f"Target Version: {task.previous_version}")
        else:
            lines.append("Target Version: PREVIOUS")

        if task.rollback_migrations:
            if task.migration_target:
                lines.append(f"Migration Rollback: YES (to {task.migration_target})")
            else:
                lines.append("Migration Rollback: YES (downgrade -1)")
        else:
            lines.append("Migration Rollback: NO")

        lines.append("\n⚠️ WARNING: This will restore the previous deployment")
        lines.append("=" * 60)
        lines.append("\nProceed with rollback? [Y/N]")

        return "\n".join(lines)
