"""
Deployment Orchestrator

Manages deployment workflow with environment-gated automation.

Environment Gates:
- Development: Auto-deploy, auto-rollback
- Staging: First-time approval, auto-rollback
- Production: Always approval, manual rollback

Safety Features:
- Pre-deployment validation (tests, migrations, SQL/S3 safety)
- Health check monitoring
- Automatic rollback for dev/staging
- Human approval gates for production

Implementation: Phase 2 - Operator Team
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(Enum):
    """Deployment status."""
    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    DEPLOYING = "deploying"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class DeploymentConfig:
    """Configuration for a deployment."""
    environment: Environment
    version: str
    project_path: Path
    migrations_path: Optional[Path] = None
    run_migrations: bool = False
    skip_tests: bool = False


@dataclass
class DeploymentResult:
    """Result of a deployment attempt."""
    status: DeploymentStatus
    environment: Environment
    version: str
    started_at: datetime
    completed_at: Optional[datetime]
    errors: List[str]
    warnings: List[str]
    rollback_executed: bool = False
    approval_required: bool = False


class DeploymentOrchestrator:
    """
    Orchestrates deployment workflow with safety gates.
    """

    def __init__(self, project_path: Path):
        """
        Initialize deployment orchestrator.

        Args:
            project_path: Root path of project
        """
        self.project_path = project_path
        self.deployment_log_path = project_path / ".aibrain" / "deployments.json"
        self._ensure_log_directory()

    def _ensure_log_directory(self):
        """Ensure deployment log directory exists."""
        self.deployment_log_path.parent.mkdir(parents=True, exist_ok=True)

    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """
        Execute deployment with safety gates.

        Args:
            config: Deployment configuration

        Returns:
            DeploymentResult with outcome
        """
        result = DeploymentResult(
            status=DeploymentStatus.PENDING,
            environment=config.environment,
            version=config.version,
            started_at=datetime.now(),
            completed_at=None,
            errors=[],
            warnings=[]
        )

        try:
            # Step 1: Check if approval required
            if self._requires_approval(config):
                result.approval_required = True
                result.status = DeploymentStatus.PENDING
                result.warnings.append(
                    f"Deployment to {config.environment.value} requires human approval"
                )
                return result

            # Step 2: Pre-deployment validation
            result.status = DeploymentStatus.VALIDATING
            validation_errors = self._run_pre_deployment_validation(config)

            if validation_errors:
                result.status = DeploymentStatus.FAILED
                result.errors.extend(validation_errors)
                result.completed_at = datetime.now()
                return result

            # Step 3: Execute deployment
            result.status = DeploymentStatus.DEPLOYING
            deployment_success, deployment_errors = self._execute_deployment(config)

            if not deployment_success:
                result.status = DeploymentStatus.FAILED
                result.errors.extend(deployment_errors)

                # Auto-rollback for dev/staging
                if self._should_auto_rollback(config.environment):
                    rollback_success = self._execute_rollback(config)
                    result.rollback_executed = True
                    if rollback_success:
                        result.status = DeploymentStatus.ROLLED_BACK
                        result.warnings.append("Auto-rollback successful")
                    else:
                        result.errors.append("Auto-rollback FAILED")

                result.completed_at = datetime.now()
                return result

            # Step 4: Post-deployment health checks
            health_ok, health_errors = self._run_health_checks(config)

            if not health_ok:
                result.status = DeploymentStatus.FAILED
                result.errors.extend(health_errors)

                # Auto-rollback for dev/staging
                if self._should_auto_rollback(config.environment):
                    rollback_success = self._execute_rollback(config)
                    result.rollback_executed = True
                    if rollback_success:
                        result.status = DeploymentStatus.ROLLED_BACK
                        result.warnings.append("Auto-rollback successful after health check failure")
                    else:
                        result.errors.append("Auto-rollback FAILED")

                result.completed_at = datetime.now()
                return result

            # Success!
            result.status = DeploymentStatus.SUCCESS
            result.completed_at = datetime.now()

            # Log deployment
            self._log_deployment(result)

            return result

        except Exception as e:
            result.status = DeploymentStatus.FAILED
            result.errors.append(f"Unexpected error: {e}")
            result.completed_at = datetime.now()
            return result

    def _requires_approval(self, config: DeploymentConfig) -> bool:
        """
        Check if deployment requires human approval.

        Args:
            config: Deployment configuration

        Returns:
            True if approval required
        """
        # Production ALWAYS requires approval
        if config.environment == Environment.PRODUCTION:
            return True

        # Staging requires first-time approval
        if config.environment == Environment.STAGING:
            return not self._has_deployed_to_staging_before()

        # Development auto-deploys
        return False

    def _has_deployed_to_staging_before(self) -> bool:
        """Check if we've deployed to staging before."""
        if not self.deployment_log_path.exists():
            return False

        try:
            with open(self.deployment_log_path, 'r') as f:
                logs = json.load(f)

            # Check for successful staging deployments
            for log in logs.get("deployments", []):
                if log.get("environment") == "staging" and log.get("status") == "success":
                    return True

            return False

        except Exception:
            return False

    def _should_auto_rollback(self, environment: Environment) -> bool:
        """
        Check if auto-rollback is enabled for environment.

        Args:
            environment: Target environment

        Returns:
            True if auto-rollback enabled
        """
        # Auto-rollback for dev and staging
        if environment in [Environment.DEVELOPMENT, Environment.STAGING]:
            return True

        # Production requires manual rollback
        return False

    def _run_pre_deployment_validation(self, config: DeploymentConfig) -> List[str]:
        """
        Run pre-deployment validation checks.

        Args:
            config: Deployment configuration

        Returns:
            List of validation errors (empty if all pass)
        """
        errors = []

        # Run tests (unless skipped)
        if not config.skip_tests:
            test_success, test_errors = self._run_tests(config)
            if not test_success:
                errors.extend(test_errors)

        # Validate migrations (if any)
        if config.run_migrations and config.migrations_path:
            migration_errors = self._validate_migrations(config)
            if migration_errors:
                errors.extend(migration_errors)

        # SQL/S3 safety checks
        safety_errors = self._run_safety_checks(config)
        if safety_errors:
            errors.extend(safety_errors)

        return errors

    def _run_tests(self, config: DeploymentConfig) -> tuple[bool, List[str]]:
        """Run test suite."""
        try:
            result = subprocess.run(
                ["npm", "test"],
                cwd=config.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return False, [f"Tests failed: {result.stderr}"]

            return True, []

        except subprocess.TimeoutExpired:
            return False, ["Tests timed out after 5 minutes"]
        except Exception as e:
            return False, [f"Failed to run tests: {e}"]

    def _validate_migrations(self, config: DeploymentConfig) -> List[str]:
        """Validate database migrations."""
        from ralph.guardrails.migration_validator import validate_migration_directory

        errors = []

        if config.migrations_path and config.migrations_path.exists():
            result = validate_migration_directory(
                config.migrations_path,
                config.environment.value
            )

            if result["invalid"] > 0:
                errors.extend(result["errors"])

        return errors

    def _run_safety_checks(self, config: DeploymentConfig) -> List[str]:
        """Run SQL and S3 safety checks."""
        from ralph.guardrails.deployment_patterns import scan_directory_for_s3_violations

        errors = []

        # Scan for S3 violations
        violations = scan_directory_for_s3_violations(
            config.project_path,
            config.project_path
        )

        # CRITICAL violations block deployment
        critical = [v for v in violations if v.risk_level == "CRITICAL"]
        if critical:
            errors.append(f"Found {len(critical)} CRITICAL S3 safety violations")

        return errors

    def _execute_deployment(self, config: DeploymentConfig) -> tuple[bool, List[str]]:
        """Execute actual deployment."""
        errors = []

        try:
            # Build application
            build_result = subprocess.run(
                ["npm", "run", "build"],
                cwd=config.project_path,
                capture_output=True,
                text=True,
                timeout=600
            )

            if build_result.returncode != 0:
                return False, [f"Build failed: {build_result.stderr}"]

            # Run migrations (if configured)
            if config.run_migrations:
                migration_success, migration_errors = self._run_migrations(config)
                if not migration_success:
                    return False, migration_errors

            # Deploy based on environment
            # (This is a placeholder - actual deployment would use Docker, AWS, etc.)
            print(f"🚀 Deploying {config.version} to {config.environment.value}")

            return True, []

        except subprocess.TimeoutExpired:
            return False, ["Build timed out after 10 minutes"]
        except Exception as e:
            return False, [f"Deployment failed: {e}"]

    def _run_migrations(self, config: DeploymentConfig) -> tuple[bool, List[str]]:
        """Run database migrations."""
        try:
            # Placeholder for Alembic migration
            # In real implementation: alembic upgrade head
            print(f"📊 Running migrations in {config.environment.value}")
            return True, []

        except Exception as e:
            return False, [f"Migration failed: {e}"]

    def _run_health_checks(self, config: DeploymentConfig) -> tuple[bool, List[str]]:
        """Run post-deployment health checks."""
        try:
            # Placeholder for health check
            # In real implementation: check service health endpoints
            print(f"🏥 Running health checks for {config.environment.value}")
            return True, []

        except Exception as e:
            return False, [f"Health check failed: {e}"]

    def _execute_rollback(self, config: DeploymentConfig) -> bool:
        """Execute rollback to previous version."""
        try:
            print(f"⏪ Rolling back {config.environment.value} to previous version")

            # Placeholder for rollback
            # In real implementation: deploy previous version, rollback migrations

            return True

        except Exception:
            return False

    def _log_deployment(self, result: DeploymentResult):
        """Log deployment result to file."""
        try:
            # Load existing logs
            if self.deployment_log_path.exists():
                with open(self.deployment_log_path, 'r') as f:
                    logs = json.load(f)
            else:
                logs = {"deployments": []}

            # Add new deployment
            logs["deployments"].append({
                "environment": result.environment.value,
                "version": result.version,
                "status": result.status.value,
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "errors": result.errors,
                "warnings": result.warnings,
                "rollback_executed": result.rollback_executed
            })

            # Write logs
            with open(self.deployment_log_path, 'w') as f:
                json.dump(logs, f, indent=2)

        except Exception:
            # Don't fail deployment if logging fails
            pass
