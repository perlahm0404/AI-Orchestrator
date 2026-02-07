"""
Deployment MCP Server (Phase 2A-4)

Wraps deployment operations as MCP server with:
- Environment gates (dev/staging/prod)
- Pre-deployment validation
- Cost tracking per deployment
- Rollback capability
- Thread-safe concurrent operations

Author: Claude Code (TDD Implementation)
Date: 2026-02-07
Version: 1.0
"""

import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class DeploymentResult:
    """Result from a deployment operation"""
    success: bool
    deployment_id: Optional[str] = None
    status: str = "pending"
    cost_usd: float = 0.0
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    requires_approval: bool = False


@dataclass
class RollbackResult:
    """Result from a rollback operation"""
    success: bool
    error: Optional[str] = None
    cost_usd: float = 0.0
    execution_time_ms: float = 0.0
    previous_version: Optional[str] = None


@dataclass
class ValidationResult:
    """Result from deployment validation"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_performed: List[str] = field(default_factory=list)


@dataclass
class DeploymentGate:
    """Deployment gate decision"""
    allowed: bool
    requires_approval: bool = False
    approval_required_role: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class VersionValidation:
    """Result from version validation"""
    valid: bool
    reason: Optional[str] = None


@dataclass
class ConfigurationValidation:
    """Result from configuration validation"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class DeploymentStatus:
    """Deployment status information"""
    deployment_id: str
    status: str  # pending, running, completed, failed
    service: str
    environment: str
    version: str
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class DeploymentMetric:
    """Metrics for a single deployment"""
    timestamp: datetime
    environment: str
    service: str
    execution_time_ms: float
    cost_usd: float
    success: bool


class DeploymentMCP:
    """MCP server wrapping deployment operations"""

    # Cost constants (estimated)
    COST_PER_DEPLOYMENT = {
        "dev": 0.001,
        "staging": 0.005,
        "prod": 0.025,
    }

    # Available environments
    ENVIRONMENTS = ["dev", "staging", "prod"]

    # Protected environments requiring approval
    PROTECTED_ENVIRONMENTS = ["prod"]

    def __init__(self) -> None:
        """Initialize Deployment MCP server"""
        self.available_environments = self.ENVIRONMENTS

        # Deployment tracking
        self._deployments: Dict[str, DeploymentStatus] = {}
        self._deployment_lock = threading.Lock()

        # Cost tracking
        self._total_cost = 0.0
        self._cost_lock = threading.Lock()

        # Metrics tracking
        self._metrics: List[DeploymentMetric] = []
        self._metrics_lock = threading.Lock()

    def validate_deployment(
        self,
        environment: str,
        service: str,
        version: str
    ) -> ValidationResult:
        """Validate deployment before execution"""
        errors: List[str] = []
        warnings: List[str] = []
        checks: List[str] = []

        # Validate environment
        checks.append("environment_validation")
        if environment not in self.ENVIRONMENTS:
            errors.append(f"Invalid environment: {environment}")

        # Validate service
        checks.append("service_validation")
        if not service or len(service) == 0:
            errors.append("Service name cannot be empty")

        # Validate version
        checks.append("version_validation")
        version_valid = self.validate_version(version)
        if not version_valid.valid:
            errors.append(f"Invalid version format: {version}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            checks_performed=checks
        )

    def check_deployment_gate(
        self,
        environment: str,
        service: str = "",  # Used for logging in production
        version: str = ""   # Used for logging in production
    ) -> DeploymentGate:
        """Check if deployment is allowed based on environment"""
        if environment not in self.ENVIRONMENTS:
            return DeploymentGate(
                allowed=False,
                reason=f"Invalid environment: {environment}"
            )

        if environment in self.PROTECTED_ENVIRONMENTS:
            return DeploymentGate(
                allowed=True,
                requires_approval=True,
                approval_required_role="operator",
                reason="Production deployments require operator approval"
            )

        return DeploymentGate(
            allowed=True,
            requires_approval=False
        )

    def validate_version(self, version: str) -> VersionValidation:
        """Validate semantic versioning"""
        pattern = r"^\d+\.\d+\.\d+$"

        if re.match(pattern, version):
            return VersionValidation(valid=True)
        else:
            return VersionValidation(
                valid=False,
                reason="Version must follow semantic versioning (X.Y.Z)"
            )

    def validate_configuration(
        self,
        configuration: Dict[str, Any]
    ) -> ConfigurationValidation:
        """Validate deployment configuration"""
        errors = []
        warnings = []

        # Validate CPU
        if "cpu" in configuration:
            try:
                cpu = int(configuration["cpu"])
                if cpu <= 0:
                    errors.append("CPU must be positive")
                elif cpu > 4096:
                    warnings.append("CPU request exceeds recommendation")
            except ValueError:
                errors.append("CPU must be numeric")

        # Validate memory
        if "memory" in configuration:
            try:
                memory = int(configuration["memory"])
                if memory <= 0:
                    errors.append("Memory must be positive")
                elif memory > 8192:
                    warnings.append("Memory request exceeds recommendation")
            except ValueError:
                errors.append("Memory must be numeric")

        # Validate replicas
        if "replicas" in configuration:
            try:
                replicas = int(configuration["replicas"])
                if replicas <= 0:
                    errors.append("Replicas must be at least 1")
                elif replicas > 10:
                    warnings.append("High replica count may increase costs")
            except ValueError:
                errors.append("Replicas must be numeric")

        return ConfigurationValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def deploy(
        self,
        environment: str,
        service: str,
        version: str,
        configuration: Optional[Dict[str, Any]] = None,
        approved_by: Optional[str] = None
    ) -> DeploymentResult:
        """Deploy a service"""
        start_time = time.time()

        # Validate deployment
        validation = self.validate_deployment(environment, service, version)
        if not validation.valid:
            return DeploymentResult(
                success=False,
                error=", ".join(validation.errors)
            )

        # Check gate
        gate = self.check_deployment_gate(environment, service, version)
        if not gate.allowed:
            return DeploymentResult(
                success=False,
                error=gate.reason or "Deployment not allowed"
            )

        if gate.requires_approval and not approved_by:
            return DeploymentResult(
                success=False,
                requires_approval=True,
                error="Approval required for production deployment"
            )

        # Validate configuration
        if configuration:
            config_valid = self.validate_configuration(configuration)
            if not config_valid.valid:
                return DeploymentResult(
                    success=False,
                    error=", ".join(config_valid.errors)
                )

        try:
            # Create deployment
            deployment_id = str(uuid.uuid4())
            execution_time_ms = (time.time() - start_time) * 1000
            cost = self.COST_PER_DEPLOYMENT.get(environment, 0.001)

            # Track deployment
            status = DeploymentStatus(
                deployment_id=deployment_id,
                status="completed",
                service=service,
                environment=environment,
                version=version
            )

            with self._deployment_lock:
                self._deployments[deployment_id] = status

            # Track cost
            with self._cost_lock:
                self._total_cost += cost

            # Track metric
            self._track_metric(
                environment=environment,
                service=service,
                execution_time_ms=execution_time_ms,
                cost=cost,
                success=True
            )

            return DeploymentResult(
                success=True,
                deployment_id=deployment_id,
                status="completed",
                cost_usd=cost,
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            return DeploymentResult(
                success=False,
                error=str(e)
            )

    def rollback(
        self,
        environment: str,
        service: str,
        deployment_id: str
    ) -> RollbackResult:
        """Rollback a deployment"""
        start_time = time.time()

        # Validate deployment exists
        with self._deployment_lock:
            if deployment_id not in self._deployments:
                return RollbackResult(
                    success=False,
                    error=f"Deployment not found: {deployment_id}"
                )

            deployment = self._deployments[deployment_id]

        try:
            execution_time_ms = (time.time() - start_time) * 1000
            cost = self.COST_PER_DEPLOYMENT.get(environment, 0.001) * 0.5

            # Track cost
            with self._cost_lock:
                self._total_cost += cost

            # Track metric
            self._track_metric(
                environment=environment,
                service=service,
                execution_time_ms=execution_time_ms,
                cost=cost,
                success=True
            )

            return RollbackResult(
                success=True,
                cost_usd=cost,
                execution_time_ms=execution_time_ms,
                previous_version=deployment.version
            )

        except Exception as e:
            return RollbackResult(
                success=False,
                error=str(e)
            )

    def get_deployment_status(
        self,
        deployment_id: str
    ) -> Optional[DeploymentStatus]:
        """Get deployment status"""
        with self._deployment_lock:
            return self._deployments.get(deployment_id)

    def get_deployment_history(
        self,
        environment: str,
        service: str
    ) -> List[DeploymentStatus]:
        """Get deployment history for a service"""
        with self._deployment_lock:
            return [
                d for d in self._deployments.values()
                if d.environment == environment and d.service == service
            ]

    def get_accumulated_cost(self) -> float:
        """Get total accumulated cost"""
        with self._cost_lock:
            return self._total_cost

    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics"""
        with self._metrics_lock:
            if not self._metrics:
                return {
                    "total_deployments": 0,
                    "total_cost_usd": 0.0,
                    "average_execution_time_ms": 0.0
                }

            total_time = sum(m.execution_time_ms for m in self._metrics)

            return {
                "total_deployments": len(self._metrics),
                "total_cost_usd": self.get_accumulated_cost(),
                "average_execution_time_ms": (
                    total_time / len(self._metrics) if self._metrics else 0
                )
            }

    def get_deployment_stats(self) -> Dict[str, Any]:
        """Get deployment statistics"""
        with self._metrics_lock:
            by_environment = {}
            success_count = 0

            for metric in self._metrics:
                env = metric.environment
                if env not in by_environment:
                    by_environment[env] = 0
                by_environment[env] += 1

                if metric.success:
                    success_count += 1

            return {
                "total_deployments": len(self._metrics),
                "success_count": success_count,
                "by_environment": by_environment
            }

    def get_mcp_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get MCP tool definitions"""
        return {
            "deploy": {
                "description": "Deploy a service",
                "parameters": {
                    "environment": "Target environment (dev/staging/prod)",
                    "service": "Service name",
                    "version": "Version to deploy",
                    "configuration": "Deployment configuration (optional)"
                }
            },
            "rollback": {
                "description": "Rollback a deployment",
                "parameters": {
                    "environment": "Environment",
                    "service": "Service name",
                    "deployment_id": "Deployment ID to rollback"
                }
            },
            "validate_deployment": {
                "description": "Validate deployment parameters",
                "parameters": {
                    "environment": "Target environment",
                    "service": "Service name",
                    "version": "Version to validate"
                }
            }
        }

    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get JSON schema for agent tool"""
        schemas = {
            "deploy": {
                "type": "object",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "environment": {"type": "string"},
                        "service": {"type": "string"},
                        "version": {"type": "string"},
                        "configuration": {"type": "object"},
                        "approved_by": {"type": "string"}
                    },
                    "required": ["environment", "service", "version"]
                }
            }
        }
        return schemas.get(tool_name, {})

    def invoke_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Invoke tool for agent use"""
        if tool_name == "deploy":
            return self.deploy(
                environment=arguments.get("environment", ""),
                service=arguments.get("service", ""),
                version=arguments.get("version", ""),
                configuration=arguments.get("configuration"),
                approved_by=arguments.get("approved_by")
            )
        elif tool_name == "rollback":
            return self.rollback(
                environment=arguments.get("environment", ""),
                service=arguments.get("service", ""),
                deployment_id=arguments.get("deployment_id", "")
            )
        elif tool_name == "validate_deployment":
            return self.validate_deployment(
                environment=arguments.get("environment", ""),
                service=arguments.get("service", ""),
                version=arguments.get("version", "")
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    # Private methods

    def _track_metric(
        self,
        environment: str,
        service: str,
        execution_time_ms: float,
        cost: float,
        success: bool
    ) -> None:
        """Track deployment metric"""
        metric = DeploymentMetric(
            timestamp=datetime.now(),
            environment=environment,
            service=service,
            execution_time_ms=execution_time_ms,
            cost_usd=cost,
            success=success
        )

        with self._metrics_lock:
            self._metrics.append(metric)
