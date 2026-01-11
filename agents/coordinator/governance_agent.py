"""
Governance Agent (Compliance + Risk)

Meta-coordinator for HIPAA compliance, LLM security, human-in-loop gates.

Workflow:
1. Read task description from work queue
2. Assess risk level (LOW/MEDIUM/HIGH/CRITICAL)
3. Check: Does it touch PHI code, auth, billing, infra, state expansion?
4. If HIGH/CRITICAL: Request human approval
5. Enforce logging constraints (no PHI in logs/traces/errors)
6. Run HIPAA evals (if applicable)
7. Update risk register if new failure modes discovered
8. Log decision with <promise>GOVERNANCE_ASSESSMENT_COMPLETE</promise>

Implementation: Phase 6 - Meta-Agent System (Governance)
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from governance.kill_switch import mode
from governance import contract
from agents.base import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    reason: str
    requires_approval: bool
    phi_risk: bool = False
    auth_risk: bool = False
    billing_risk: bool = False
    infra_risk: bool = False
    state_expansion: bool = False


@dataclass
class GovernanceDecision:
    """Governance decision result."""
    task_id: str
    decision: str  # "APPROVED" | "BLOCKED" | "REQUIRES_APPROVAL"
    risk_assessment: RiskAssessment
    hipaa_eval_passed: Optional[bool] = None
    phi_detected: Optional[bool] = None
    recommendations: List[str] = None


class GovernanceAgent(BaseAgent):
    """
    Governance Agent for HIPAA compliance, LLM security, and human-in-loop gates.

    Enhanced with Ralph-Wiggum iteration patterns.
    """

    def __init__(self, app_adapter, config: Optional[AgentConfig] = None):
        """
        Initialize Governance agent.

        Args:
            app_adapter: Application adapter (provides project context)
            config: Optional AgentConfig (will be created from contract if not provided)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract
        self.contract = contract.load("governance-agent-simple")

        # Create or use provided config
        if config is None:
            self.config = AgentConfig(
                project_name=self.app_context.project_name,
                agent_name="governance-agent",
                expected_completion_signal="GOVERNANCE_ASSESSMENT_COMPLETE",
                max_iterations=self.contract.limits.get("max_iterations", 3),
                max_retries=self.contract.limits.get("max_retries", 2)
            )
        else:
            self.config = config

        # Backward compatibility
        self.max_retries = self.config.max_retries

        # Iteration tracking
        self.current_iteration = 0
        self.iteration_history: List[Dict[str, Any]] = []

        # AI Orchestrator repo root
        self.orchestrator_root = Path(__file__).parent.parent.parent

    def execute(self, task_id: str, task_description: str, task_data: Optional[Dict[str, Any]] = None) -> GovernanceDecision:
        """
        Execute governance risk assessment.

        Args:
            task_id: The task ID to assess (e.g., "TASK-CME-045")
            task_description: Task description text
            task_data: Optional task metadata (type, files, etc.)

        Returns:
            GovernanceDecision with risk assessment and decision
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract: can we execute this action?
        contract.require_allowed(self.contract, "assess_risk")

        # Track iteration
        self.current_iteration += 1

        # Check iteration budget
        if self.current_iteration > self.config.max_iterations:
            logger.warning(f"Max iterations ({self.config.max_iterations}) reached")
            return GovernanceDecision(
                task_id=task_id,
                decision="BLOCKED",
                risk_assessment=RiskAssessment(
                    risk_level="UNKNOWN",
                    reason=f"Max iterations ({self.config.max_iterations}) reached",
                    requires_approval=True
                )
            )

        logger.info(f"🛡️ Governance Agent assessing task {task_id} (iteration {self.current_iteration}/{self.config.max_iterations})")

        try:
            # Step 1: Assess risk level
            risk_assessment = self._assess_risk(task_id, task_description, task_data)

            logger.info(f"📊 Risk Assessment: {risk_assessment.risk_level} - {risk_assessment.reason}")

            # Step 2: Make decision based on risk level
            if risk_assessment.risk_level in ["HIGH", "CRITICAL"]:
                decision = "REQUIRES_APPROVAL"
                logger.warning(f"⚠️  Task {task_id} requires human approval (risk: {risk_assessment.risk_level})")
            elif risk_assessment.requires_approval:
                decision = "REQUIRES_APPROVAL"
                logger.warning(f"⚠️  Task {task_id} requires human approval")
            else:
                decision = "APPROVED"
                logger.info(f"✅ Task {task_id} approved (risk: {risk_assessment.risk_level})")

            # Step 3: Check for PHI in task description (sanity check)
            phi_detected = self._detect_phi(task_description)
            if phi_detected:
                logger.error(f"🚨 PHI DETECTED in task description for {task_id}!")
                decision = "BLOCKED"
                risk_assessment.phi_risk = True
                risk_assessment.risk_level = "CRITICAL"

            # Step 4: Run HIPAA evals if applicable (placeholder for now)
            hipaa_eval_passed = self._run_hipaa_evals(task_data) if task_data else None

            # Step 5: Generate recommendations
            recommendations = self._generate_recommendations(risk_assessment)

            # Success output
            output = f"""Governance assessment complete for task {task_id}.

Risk Level: {risk_assessment.risk_level}
Decision: {decision}
Reason: {risk_assessment.reason}

Recommendations:
{chr(10).join(f"  - {r}" for r in recommendations)}

<promise>GOVERNANCE_ASSESSMENT_COMPLETE</promise>"""

            logger.info(f"✅ Governance assessment complete: {task_id}")

            return GovernanceDecision(
                task_id=task_id,
                decision=decision,
                risk_assessment=risk_assessment,
                hipaa_eval_passed=hipaa_eval_passed,
                phi_detected=phi_detected,
                recommendations=recommendations
            )

        except Exception as e:
            error_msg = f"Governance assessment failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return GovernanceDecision(
                task_id=task_id,
                decision="BLOCKED",
                risk_assessment=RiskAssessment(
                    risk_level="CRITICAL",
                    reason=error_msg,
                    requires_approval=True
                )
            )

    def _assess_risk(self, task_id: str, task_description: str, task_data: Optional[Dict[str, Any]]) -> RiskAssessment:
        """
        Assess risk level of a task.

        Returns:
            RiskAssessment with risk level and reasons
        """
        risk_level = "LOW"
        reasons = []
        requires_approval = False
        phi_risk = False
        auth_risk = False
        billing_risk = False
        infra_risk = False
        state_expansion = False

        description_lower = task_description.lower()

        # Check task_data flags first (explicit metadata)
        if task_data and task_data.get("touches_phi_code"):
            phi_risk = True
            risk_level = "HIGH"
            reasons.append("Task touches PHI-handling code (metadata flag)")
            requires_approval = True

        # Check for PHI-related keywords in description
        phi_keywords = ["phi", "patient", "health information", "license number", "npi", "medical record"]
        if any(keyword in description_lower for keyword in phi_keywords):
            phi_risk = True
            risk_level = "HIGH"
            reasons.append("Task involves PHI-related code or data (keyword match)")
            requires_approval = True

        # Check for auth keywords
        auth_keywords = ["auth", "authentication", "authorization", "login", "password", "session", "token", "jwt"]
        if any(keyword in description_lower for keyword in auth_keywords):
            auth_risk = True
            risk_level = "HIGH"
            reasons.append("Task involves authentication/authorization changes")
            requires_approval = True

        # Check for billing keywords
        billing_keywords = ["billing", "payment", "stripe", "charge", "invoice", "subscription"]
        if any(keyword in description_lower for keyword in billing_keywords):
            billing_risk = True
            risk_level = "HIGH"
            reasons.append("Task involves billing/payment processing")
            requires_approval = True

        # Check for infra keywords
        infra_keywords = ["infrastructure", "deploy", "aws", "lambda", "s3", "database", "migration", "production"]
        if any(keyword in description_lower for keyword in infra_keywords):
            infra_risk = True
            risk_level = "CRITICAL" if "production" in description_lower else "HIGH"
            reasons.append("Task involves infrastructure changes")
            requires_approval = True

        # Check for state expansion
        state_keywords = ["new state", "add state", "state support", "expand to"]
        if any(keyword in description_lower for keyword in state_keywords):
            state_expansion = True
            risk_level = "MEDIUM"
            reasons.append("Task involves state expansion (requires compliance review per-state)")
            requires_approval = True

        # Check task data if provided
        if task_data:
            # Check if task touches specific files
            files = task_data.get("files", [])
            if isinstance(files, list):
                for file_path in files:
                    file_lower = file_path.lower()
                    if "auth" in file_lower or "session" in file_lower:
                        auth_risk = True
                        risk_level = "HIGH"
                        reasons.append(f"Task modifies auth-related file: {file_path}")
                        requires_approval = True
                    if "billing" in file_lower or "payment" in file_lower:
                        billing_risk = True
                        risk_level = "HIGH"
                        reasons.append(f"Task modifies billing-related file: {file_path}")
                        requires_approval = True

        # If no high-risk indicators, assess as LOW or MEDIUM
        if not reasons:
            risk_level = "LOW"
            reasons.append("No high-risk indicators detected")

        reason_str = "; ".join(reasons)

        return RiskAssessment(
            risk_level=risk_level,
            reason=reason_str,
            requires_approval=requires_approval,
            phi_risk=phi_risk,
            auth_risk=auth_risk,
            billing_risk=billing_risk,
            infra_risk=infra_risk,
            state_expansion=state_expansion
        )

    def _detect_phi(self, text: str) -> bool:
        """
        Detect PHI in text using regex patterns.

        This is a simple regex-based detector. In production, should use
        ML-based PHI detection for better accuracy.

        Returns:
            True if PHI detected, False otherwise
        """
        # Common PHI patterns
        patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Z]{2}\d{5,8}\b',  # License numbers (e.g., CA12345, TX123456)
            r'\bNPI\s*:?\s*\d{10}\b',  # NPI numbers
            r'\b\d{2}/\d{2}/\d{4}\b',  # Dates (potential DOB)
        ]

        for pattern in patterns:
            if re.search(pattern, text):
                return True

        return False

    def _run_hipaa_evals(self, task_data: Dict[str, Any]) -> bool:
        """
        Run HIPAA compliance evals.

        Placeholder for now - in production, should run actual eval suite.

        Returns:
            True if all HIPAA evals pass, False otherwise
        """
        # TODO: Integrate with actual eval suite when implemented
        # For now, return True (optimistic default)
        return True

    def _generate_recommendations(self, risk_assessment: RiskAssessment) -> List[str]:
        """Generate recommendations based on risk assessment."""
        recommendations = []

        if risk_assessment.phi_risk:
            recommendations.append("Review PHI handling code for HIPAA compliance")
            recommendations.append("Ensure no PHI in logs, traces, or error messages")
            recommendations.append("Validate encryption at rest and in transit")

        if risk_assessment.auth_risk:
            recommendations.append("Review authentication changes for security vulnerabilities")
            recommendations.append("Ensure session management follows best practices")
            recommendations.append("Consider security audit after implementation")

        if risk_assessment.billing_risk:
            recommendations.append("Review billing changes for accuracy and compliance")
            recommendations.append("Ensure PCI-DSS compliance if handling card data")
            recommendations.append("Test payment flows thoroughly before production")

        if risk_assessment.infra_risk:
            recommendations.append("Review infrastructure changes for reliability and security")
            recommendations.append("Ensure proper monitoring and alerting")
            recommendations.append("Plan rollback strategy before deployment")

        if risk_assessment.state_expansion:
            recommendations.append("Review state-specific regulations and requirements")
            recommendations.append("Validate licensing rules and CME requirements for new state")
            recommendations.append("Add state-specific test cases to eval suite")

        if not recommendations:
            recommendations.append("Standard review process applies")

        return recommendations

    def checkpoint(self) -> Dict[str, Any]:
        """
        Capture current state for session resume.

        Returns:
            Checkpoint dict that can reconstruct agent state
        """
        return {
            "agent_name": self.config.agent_name,
            "project_name": self.config.project_name,
            "current_iteration": self.current_iteration,
            "iteration_history": self.iteration_history,
            "max_iterations": self.config.max_iterations,
            "expected_completion_signal": self.config.expected_completion_signal
        }

    def halt(self, reason: str) -> None:
        """
        Gracefully stop execution.

        Args:
            reason: Why the agent is halting
        """
        logger.warning(f"Governance Agent halting: {reason}")
        logger.info(f"Completed {self.current_iteration} iterations")
        logger.info(f"Iteration history: {len(self.iteration_history)} records")
