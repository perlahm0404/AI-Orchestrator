"""
Deployment Agent

Builds and deploys applications with safety gates.

Responsibilities:
- Run pre-deployment validation (tests, safety checks)
- Build application
- Deploy to target environment (dev/staging/production)
- Run post-deployment health checks

Governance: Operator Team (L0.5 autonomy)
- Dev: Auto-deploy
- Staging: First-time approval required
- Production: Always requires approval

Implementation: Phase 2 - Operator Team
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from orchestration.deployment_orchestrator import (
    DeploymentConfig,
    DeploymentOrchestrator,
    DeploymentResult,
    Environment
)


@dataclass
class DeploymentTask:
    """Task specification for deployment."""
    project_path: Path
    environment: str
    version: str
    run_migrations: bool = False
    migrations_path: Optional[Path] = None
    skip_tests: bool = False


class DeploymentAgent:
    """
    Agent for deploying applications with safety gates.
    """

    def __init__(self, project_path: Path):
        """
        Initialize deployment agent.

        Args:
            project_path: Root path of project
        """
        self.project_path = project_path
        self.orchestrator = DeploymentOrchestrator(project_path)

    def execute(self, task: DeploymentTask) -> DeploymentResult:
        """
        Execute deployment task.

        Args:
            task: Deployment task specification

        Returns:
            DeploymentResult with outcome
        """
        # Map environment string to enum
        env_map = {
            "development": Environment.DEVELOPMENT,
            "dev": Environment.DEVELOPMENT,
            "staging": Environment.STAGING,
            "stage": Environment.STAGING,
            "production": Environment.PRODUCTION,
            "prod": Environment.PRODUCTION,
        }

        environment = env_map.get(task.environment.lower())
        if not environment:
            raise ValueError(f"Invalid environment: {task.environment}")

        # Create deployment config
        config = DeploymentConfig(
            environment=environment,
            version=task.version,
            project_path=task.project_path,
            migrations_path=task.migrations_path,
            run_migrations=task.run_migrations,
            skip_tests=task.skip_tests
        )

        # Execute deployment
        return self.orchestrator.deploy(config)

    def get_approval_prompt(self, task: DeploymentTask) -> str:
        """
        Generate approval prompt for human review.

        Args:
            task: Deployment task

        Returns:
            Formatted approval prompt
        """
        lines = []
        lines.append("=" * 60)
        lines.append("DEPLOYMENT APPROVAL REQUIRED")
        lines.append("=" * 60)
        lines.append(f"Environment: {task.environment.upper()}")
        lines.append(f"Version: {task.version}")
        lines.append(f"Project: {task.project_path.name}")

        if task.run_migrations:
            lines.append(f"Migrations: YES (path: {task.migrations_path})")
        else:
            lines.append("Migrations: NO")

        lines.append("=" * 60)
        lines.append("\nProceed with deployment? [Y/N]")

        return "\n".join(lines)
