"""
CMO Agent (Growth Engine)

Meta-coordinator for GTM strategy, demand capture, messaging, channel experiments.

Workflow:
1. Read task description from work queue
2. Check if task is GTM-related (conditional gate)
3. Review messaging alignment
4. Validate demand evidence (if fake-door test)
5. Decision: APPROVED / PROPOSE_ALTERNATIVE
6. Manage weekly experiment backlog
7. Track pipeline metrics (lead → demo → pilot → paid)
8. Log decision with <promise>CMO_REVIEW_COMPLETE</promise>

Implementation: Phase 6 - Meta-Agent System (CMO)
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from governance.kill_switch import mode
from governance import contract
from agents.base import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


@dataclass
class CMOReview:
    """CMO review result."""
    decision: str  # "APPROVED" | "PROPOSE_ALTERNATIVE"
    reason: str
    messaging_aligned: bool = False
    has_demand_evidence: bool = False
    proposed_alternative: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


class CMOAgent(BaseAgent):
    """
    CMO Agent (Growth Engine) for GTM strategy, demand capture, and messaging.

    Enhanced with Ralph-Wiggum iteration patterns.
    """

    def __init__(self, app_adapter, config: Optional[AgentConfig] = None):
        """
        Initialize CMO agent.

        Args:
            app_adapter: Application adapter (provides project context)
            config: Optional AgentConfig (will be created from contract if not provided)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract
        self.contract = contract.load("cmo-agent-simple")

        # Create or use provided config
        if config is None:
            self.config = AgentConfig(
                project_name=self.app_context.project_name,
                agent_name="cmo-agent",
                expected_completion_signal="CMO_REVIEW_COMPLETE",
                max_iterations=self.contract.limits.get("max_iterations", 5),
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

    def execute(self, task_id: str, task_description: str, task_data: Optional[Dict[str, Any]] = None) -> CMOReview:
        """
        Execute CMO review.

        Args:
            task_id: The task ID to review (e.g., "TASK-LANDING-001")
            task_description: Task description text
            task_data: Optional task metadata (is_gtm_related, etc.)

        Returns:
            CMOReview with decision and recommendations
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract: can we execute this action?
        contract.require_allowed(self.contract, "create_messaging_matrix")

        # Track iteration
        self.current_iteration += 1

        # Check iteration budget
        if self.current_iteration > self.config.max_iterations:
            logger.warning(f"Max iterations ({self.config.max_iterations}) reached")
            return CMOReview(
                decision="APPROVED",  # Default to approved (don't block work)
                reason=f"Max iterations ({self.config.max_iterations}) reached - auto-approved"
            )

        logger.info(f"📈 CMO Agent reviewing task {task_id} (iteration {self.current_iteration}/{self.config.max_iterations})")

        try:
            # Step 1: Check if this task requires CMO review (conditional gate)
            is_gtm_related = task_data.get("is_gtm_related", False) if task_data else False

            # Check for GTM keywords in description
            description_lower = task_description.lower()
            gtm_keywords = [
                "landing page", "messaging", "positioning", "onboarding", "activation",
                "conversion", "demo", "pilot", "marketing", "email", "webinar",
                "case study", "roi calculator", "trust", "proof", "testimonial"
            ]

            is_gtm_related = is_gtm_related or any(keyword in description_lower for keyword in gtm_keywords)

            # Auto-approve non-GTM tasks (low CMO value)
            if not is_gtm_related:
                logger.info(f"✅ Task {task_id} auto-approved (not GTM-related)")
                return CMOReview(
                    decision="APPROVED",
                    reason="Auto-approved: not GTM-related (product/engineering task)",
                    messaging_aligned=True
                )

            # Step 2: Check messaging alignment
            messaging_aligned = self._check_messaging_alignment(task_description)

            # Step 3: Check for demand evidence (if fake-door test)
            has_demand_evidence = self._has_demand_evidence(task_description, task_data)

            # Step 4: Make decision
            if "fake door" in description_lower or "demand test" in description_lower:
                # Ensure fake-door tests have honest messaging
                if "coming soon" in description_lower or "waitlist" in description_lower:
                    decision = "APPROVED"
                    reason = "Fake-door test with honest messaging ('coming soon')"
                    recommendations = [
                        "Link to PM backlog (if demand proven → PM prioritizes build)",
                        "Track waitlist size as demand signal"
                    ]
                else:
                    decision = "PROPOSE_ALTERNATIVE"
                    reason = "Fake-door test lacks honest 'coming soon' messaging"
                    proposed_alternative = "Add 'Coming soon - join waitlist' language to avoid false claims"
                    recommendations = [
                        "Governance enforces honest messaging",
                        "Use 'Join waitlist' instead of 'Buy now'",
                        "Link to PM backlog for prioritization after validation"
                    ]
            elif not messaging_aligned:
                # Messaging doesn't match current positioning
                decision = "PROPOSE_ALTERNATIVE"
                reason = "Messaging doesn't align with current positioning matrix"
                proposed_alternative = "Review messaging matrix and align language"
                recommendations = [
                    "Review messaging matrix (update monthly)",
                    "Use segment-specific value props (NP vs PA vs MD)",
                    "Capture user language from objections/wins"
                ]
            else:
                # Approve
                decision = "APPROVED"
                reason = "GTM task aligned with messaging and positioning"
                recommendations = []

            # Success output
            output = f"""CMO review complete for task {task_id}.

Decision: {decision}
Reason: {reason}
Messaging aligned: {messaging_aligned}
Has demand evidence: {has_demand_evidence}

Recommendations:
{chr(10).join(f"  - {r}" for r in recommendations) if recommendations else "  - None"}

<promise>CMO_REVIEW_COMPLETE</promise>"""

            logger.info(f"✅ CMO review complete: {task_id} → {decision}")

            return CMOReview(
                decision=decision,
                reason=reason,
                messaging_aligned=messaging_aligned,
                has_demand_evidence=has_demand_evidence,
                proposed_alternative=proposed_alternative if decision == "PROPOSE_ALTERNATIVE" else None,
                recommendations=recommendations
            )

        except Exception as e:
            error_msg = f"CMO review failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return CMOReview(
                decision="APPROVED",  # Default to approved (don't block work on CMO failure)
                reason=f"Auto-approved due to error: {error_msg}"
            )

    def _check_messaging_alignment(self, task_description: str) -> bool:
        """
        Check if task messaging aligns with current positioning matrix.

        Returns:
            True if aligned, False otherwise
        """
        # Look for messaging matrix file
        messaging_matrix_path = self.orchestrator_root / "messaging_matrix.md"

        if not messaging_matrix_path.exists():
            # No messaging matrix found - default to aligned (don't block without matrix)
            logger.warning("No messaging matrix found - defaulting to aligned")
            return True

        # Simple check: does task description use language from messaging matrix?
        matrix_content = messaging_matrix_path.read_text()
        description_lower = task_description.lower()

        # Check for key value prop keywords
        value_prop_keywords = [
            "never miss", "deadline", "accurate", "cme", "multi-state",
            "license renewal", "automated tracking", "compliance", "hipaa"
        ]

        matches = sum(1 for keyword in value_prop_keywords if keyword in description_lower and keyword in matrix_content.lower())

        # At least 2 keyword matches = aligned
        return matches >= 2

    def _has_demand_evidence(self, task_description: str, task_data: Optional[Dict[str, Any]]) -> bool:
        """
        Check if task has demand evidence (for fake-door tests).

        Returns:
            True if demand evidence exists, False otherwise
        """
        # Check task_data first
        if task_data and "demand_evidence" in task_data:
            return bool(task_data["demand_evidence"])

        # Check for demand keywords in description
        description_lower = task_description.lower()
        demand_keywords = [
            "waitlist", "pilot", "loi", "letter of intent", "demo", "user requested",
            "customer feedback", "objection", "conversion", "activation"
        ]

        return any(keyword in description_lower for keyword in demand_keywords)

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
        logger.warning(f"CMO Agent halting: {reason}")
        logger.info(f"Completed {self.current_iteration} iterations")
        logger.info(f"Iteration history: {len(self.iteration_history)} records")
