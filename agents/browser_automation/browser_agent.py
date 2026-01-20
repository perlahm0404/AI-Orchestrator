"""
Browser Automation Agent

Autonomous agent for credentialing portal verification using browser automation.
Integrates with Wiggum (iteration control) and Ralph (verification).
"""

from typing import Any, Optional
from pathlib import Path
import logging

from agents.base import BaseAgent, AgentConfig
from adapters.browser_automation import BrowserAutomationClient

logger = logging.getLogger(__name__)


class BrowserAutomationAgent(BaseAgent):
    """
    Agent for browser-based credentialing portal verification.

    Features:
    - Browser automation via Playwright
    - License verification across multiple portals
    - HIPAA-compliant credential handling
    - Retry logic on navigation failures (Wiggum integration)
    - Data validation with Ralph
    """

    def __init__(
        self,
        app_adapter: Any,
        config: Optional[AgentConfig] = None
    ):
        """
        Initialize browser automation agent.

        Args:
            app_adapter: Application adapter (provides project context)
            config: Agent configuration (autonomy level, iteration limits)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context() if hasattr(app_adapter, 'get_context') else {}

        # Default config if not provided
        self.config = config or AgentConfig(
            project_name=getattr(app_adapter, 'project_name', 'unknown'),
            agent_name="browser_automation",
            expected_completion_signal="VERIFICATION_COMPLETE",
            max_iterations=5  # Lower iteration count for browser automation
        )

        # Initialize browser automation client
        self.client = BrowserAutomationClient()

        # Iteration tracking (for Wiggum integration)
        self.current_iteration = 0
        self.iteration_history: list[dict[str, Any]] = []

        # Session tracking
        self.active_session_id: Optional[str] = None

    def execute(self, task_id: str) -> dict[str, Any]:
        """
        Execute browser automation task.

        Args:
            task_id: Task identifier (e.g., "verify-license-A12345")

        Returns:
            Result dict with:
            - status: "completed" | "blocked" | "failed"
            - output: Human-readable summary
            - evidence: Extracted data and artifacts
            - verdict: Ralph verification result (if applicable)
        """
        self.current_iteration += 1

        logger.info(f"BrowserAutomationAgent executing task: {task_id} (iteration {self.current_iteration})")

        try:
            # Parse task (format: "verify-license-<adapter>-<license_number>")
            # Example: "verify-license-california-medical-board-A12345"
            parts = task_id.split("-")

            if len(parts) < 4 or parts[0] != "verify" or parts[1] != "license":
                raise ValueError(f"Invalid task format: {task_id}. Expected: verify-license-<adapter>-<license_number>")

            adapter_name = "-".join(parts[2:-1])  # May contain hyphens
            license_number = parts[-1]

            logger.info(f"Verifying license {license_number} via {adapter_name}")

            # Create browser session
            session_id = self.client.create_session({
                "sessionId": f"agent-{task_id}-{self.current_iteration}",
                "headless": True,
                "auditLogPath": f"./audit-logs/{task_id}.jsonl"
            })
            self.active_session_id = session_id

            # Extract license info
            license_info = self.client.extract_license_info(
                session_id=session_id,
                adapter=adapter_name,
                license_number=license_number
            )

            # Cleanup session
            self.client.cleanup_session(session_id)
            self.active_session_id = None

            # Validate extracted data (Ralph integration)
            verdict = self._validate_extraction(license_info)

            # Build result
            result = {
                "status": "completed" if verdict.get("valid", True) else "failed",
                "output": self._format_output(license_info),
                "evidence": {
                    "license_info": license_info,
                    "audit_log": f"./audit-logs/{task_id}.jsonl"
                },
                "verdict": verdict
            }

            # Check for completion signal
            if result["status"] == "completed":
                output_str: str = str(result["output"])
                result["output"] = output_str + "\n\n<promise>VERIFICATION_COMPLETE</promise>"

            logger.info(f"Task {task_id} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")

            # Cleanup session if still active
            if self.active_session_id:
                try:
                    self.client.cleanup_session(self.active_session_id)
                except Exception as cleanup_error:
                    logger.warning(f"Session cleanup failed: {cleanup_error}")
                finally:
                    self.active_session_id = None

            return {
                "status": "failed",
                "output": f"Browser automation failed: {str(e)}",
                "evidence": {},
                "verdict": {"valid": False, "error": str(e)}
            }

    def _validate_extraction(self, license_info: dict[str, Any]) -> dict[str, Any]:
        """
        Validate extracted license data.

        Uses Ralph-style validation to check data quality.

        Args:
            license_info: Extracted license information

        Returns:
            Verdict dict with validation results
        """
        issues: list[str] = []
        verdict: dict[str, Any] = {
            "valid": True,
            "issues": issues
        }

        # Check required fields
        required_fields = ["licenseNumber", "status", "holderName", "licenseType"]
        for field in required_fields:
            if field not in license_info or not license_info[field]:
                verdict["valid"] = False
                issues.append(f"Missing required field: {field}")

        # Check status validity
        valid_statuses = ["active", "inactive", "expired", "suspended", "revoked"]
        if license_info.get("status") not in valid_statuses:
            verdict["valid"] = False
            issues.append(f"Invalid status: {license_info.get('status')}")

        # Check for "not found" indicator
        if license_info.get("metadata", {}).get("found") == False:
            verdict["valid"] = False
            issues.append("License not found in portal")

        return verdict

    def _format_output(self, license_info: dict[str, Any]) -> str:
        """
        Format license info as human-readable output.

        Args:
            license_info: Extracted license information

        Returns:
            Formatted string
        """
        lines = []
        lines.append("License Verification Results:")
        lines.append(f"  License Number: {license_info.get('licenseNumber', 'Unknown')}")
        lines.append(f"  Status: {license_info.get('status', 'Unknown')}")
        lines.append(f"  Holder: {license_info.get('holderName', 'Unknown')}")
        lines.append(f"  Type: {license_info.get('licenseType', 'Unknown')}")

        if license_info.get('expirationDate'):
            lines.append(f"  Expiration: {license_info['expirationDate']}")

        if license_info.get('disciplinaryActions'):
            count = len(license_info['disciplinaryActions'])
            lines.append(f"  Disciplinary Actions: {count}")

        return "\n".join(lines)

    def checkpoint(self) -> dict[str, Any]:
        """
        Save agent state for resume capability.

        Returns:
            Checkpoint dict with:
            - iteration: Current iteration number
            - active_session: Active session ID (if any)
            - history: Iteration history
        """
        return {
            "iteration": self.current_iteration,
            "active_session": self.active_session_id,
            "history": self.iteration_history,
            "config": {
                "project_name": self.config.project_name,
                "agent_name": self.config.agent_name,
                "max_iterations": self.config.max_iterations
            }
        }

    def halt(self, reason: str) -> None:
        """
        Gracefully stop agent execution.

        Args:
            reason: Why the agent is halting
        """
        logger.info(f"BrowserAutomationAgent halting: {reason}")

        # Cleanup active session if any
        if self.active_session_id:
            try:
                self.client.cleanup_session(self.active_session_id)
                logger.info(f"Cleaned up session: {self.active_session_id}")
            except Exception as e:
                logger.warning(f"Failed to cleanup session during halt: {e}")
            finally:
                self.active_session_id = None
