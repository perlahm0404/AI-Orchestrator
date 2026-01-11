"""
Product Manager Agent (Discovery & Prioritization)

Meta-coordinator for continuous discovery, evidence-driven prioritization.

Workflow:
1. Read task description from work queue
2. Check if task is user-facing or product-scope (conditional gate)
3. Read Evidence Repository for related evidence
4. Check roadmap alignment (PROJECT_HQ.md)
5. Validate outcome metrics defined
6. Decision: APPROVED / BLOCKED / MODIFIED
7. If BLOCKED: Provide reason + alternative recommendation
8. If MODIFIED: Update task description with acceptance criteria
9. Log decision with <promise>PM_REVIEW_COMPLETE</promise>

Implementation: Phase 6 - Meta-Agent System (PM)
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from governance.kill_switch import mode
from governance import contract
from agents.base import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


@dataclass
class PMValidation:
    """PM validation result."""
    decision: str  # "APPROVED" | "BLOCKED" | "MODIFIED"
    reason: str
    evidence_count: int = 0
    roadmap_aligned: bool = False
    has_outcome_metrics: bool = False
    modified_description: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


class ProductManagerAgent(BaseAgent):
    """
    Product Manager Agent for continuous discovery and evidence-driven prioritization.

    Enhanced with Ralph-Wiggum iteration patterns.
    """

    def __init__(self, app_adapter, config: Optional[AgentConfig] = None):
        """
        Initialize PM agent.

        Args:
            app_adapter: Application adapter (provides project context)
            config: Optional AgentConfig (will be created from contract if not provided)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract
        self.contract = contract.load("product-manager-simple")

        # Create or use provided config
        if config is None:
            self.config = AgentConfig(
                project_name=self.app_context.project_name,
                agent_name="product-manager",
                expected_completion_signal="PM_REVIEW_COMPLETE",
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

    def execute(self, task_id: str, task_description: str, task_data: Optional[Dict[str, Any]] = None) -> PMValidation:
        """
        Execute PM validation.

        Args:
            task_id: The task ID to validate (e.g., "TASK-CME-045")
            task_description: Task description text
            task_data: Optional task metadata (type, affects_user_experience, etc.)

        Returns:
            PMValidation with decision and recommendations
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract: can we execute this action?
        contract.require_allowed(self.contract, "validate_task")

        # Track iteration
        self.current_iteration += 1

        # Check iteration budget
        if self.current_iteration > self.config.max_iterations:
            logger.warning(f"Max iterations ({self.config.max_iterations}) reached")
            return PMValidation(
                decision="BLOCKED",
                reason=f"Max iterations ({self.config.max_iterations}) reached"
            )

        logger.info(f"📋 PM Agent validating task {task_id} (iteration {self.current_iteration}/{self.config.max_iterations})")

        try:
            # Step 1: Check if this task requires PM validation (conditional gate)
            task_type = task_data.get("type", "bugfix") if task_data else "bugfix"
            affects_user = task_data.get("affects_user_experience", False) if task_data else False

            # Auto-approve refactors and bugfixes (low PM value)
            if task_type not in ["feature", "enhancement"] and not affects_user:
                logger.info(f"✅ Task {task_id} auto-approved (type={task_type}, no user impact)")
                return PMValidation(
                    decision="APPROVED",
                    reason="Auto-approved: refactor/bugfix without user impact",
                    roadmap_aligned=True
                )

            # Step 2: Read Evidence Repository for related evidence
            evidence_items = self._find_related_evidence(task_id, task_description)
            logger.info(f"📊 Found {len(evidence_items)} related evidence items")

            # Step 3: Check roadmap alignment
            roadmap_aligned = self._check_roadmap_alignment(task_description)

            # Step 4: Check for outcome metrics
            has_outcome_metrics = self._has_outcome_metrics(task_description, task_data)

            # Step 5: Make decision
            if not evidence_items and task_type == "feature":
                # Block features without evidence
                decision = "BLOCKED"
                reason = "Feature lacks supporting evidence from users"
                recommendations = [
                    "Capture user evidence: aibrain evidence capture feature-request pilot-user",
                    "Link evidence to task: aibrain evidence link EVIDENCE-XXX {task_id}",
                    "Or provide rationale for building without evidence"
                ]
            elif not roadmap_aligned:
                # Block off-roadmap features
                decision = "BLOCKED"
                reason = "Feature not aligned with current roadmap (Q1 Focus)"
                recommendations = [
                    "Review roadmap: PROJECT_HQ.md",
                    "Update roadmap if this should be prioritized",
                    "Or defer to next quarter"
                ]
            elif not has_outcome_metrics:
                # Modify to add outcome metrics
                decision = "MODIFIED"
                reason = "Task lacks defined outcome metrics (how will we measure success?)"
                modified_description = self._add_outcome_metrics_template(task_description)
                recommendations = [
                    "Define success metrics (e.g., activation rate, retention, time-to-value)",
                    "Add acceptance criteria (what does 'done' look like?)",
                    "Link to evidence items showing user need"
                ]
            else:
                # Approve
                decision = "APPROVED"
                reason = f"Evidence-backed ({len(evidence_items)} items), roadmap-aligned, metrics defined"
                recommendations = []

            # Success output
            output = f"""PM validation complete for task {task_id}.

Decision: {decision}
Reason: {reason}
Evidence items: {len(evidence_items)}
Roadmap aligned: {roadmap_aligned}
Has outcome metrics: {has_outcome_metrics}

Recommendations:
{chr(10).join(f"  - {r}" for r in recommendations) if recommendations else "  - None"}

<promise>PM_REVIEW_COMPLETE</promise>"""

            logger.info(f"✅ PM validation complete: {task_id} → {decision}")

            return PMValidation(
                decision=decision,
                reason=reason,
                evidence_count=len(evidence_items),
                roadmap_aligned=roadmap_aligned,
                has_outcome_metrics=has_outcome_metrics,
                modified_description=modified_description if decision == "MODIFIED" else None,
                recommendations=recommendations
            )

        except Exception as e:
            error_msg = f"PM validation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return PMValidation(
                decision="BLOCKED",
                reason=error_msg
            )

    def _find_related_evidence(self, task_id: str, task_description: str) -> List[Dict[str, str]]:
        """
        Find evidence items related to this task.

        Returns:
            List of evidence items (dicts with id, summary, priority)
        """
        evidence_dir = self.orchestrator_root / "evidence"

        if not evidence_dir.exists():
            return []

        # Find all evidence files
        evidence_files = list(evidence_dir.glob("EVIDENCE-*.md"))
        evidence_files = [f for f in evidence_files if not f.parent.name == "examples"]

        related_items = []

        # Extract keywords from task description
        description_lower = task_description.lower()

        for evidence_file in evidence_files:
            try:
                content = evidence_file.read_text()

                # Extract summary
                summary_match = re.search(r'## Evidence Summary\n(.+?)(?:\n##|\Z)', content, re.DOTALL)
                summary = summary_match.group(1).strip() if summary_match else ""

                # Check if evidence is related (keyword matching)
                # Simple heuristic: if task description contains keywords from evidence summary
                summary_keywords = re.findall(r'\b\w{4,}\b', summary.lower())
                matches = sum(1 for keyword in summary_keywords if keyword in description_lower)

                if matches >= 2:  # At least 2 keyword matches
                    # Extract frontmatter ID
                    id_match = re.search(r'id:\s*([^\n]+)', content)
                    evidence_id = id_match.group(1).strip() if id_match else evidence_file.stem

                    # Extract priority
                    priority_match = re.search(r'priority:\s*([^\n]+)', content)
                    priority = priority_match.group(1).strip() if priority_match else "unknown"

                    related_items.append({
                        "id": evidence_id,
                        "summary": summary[:100],
                        "priority": priority,
                        "file": str(evidence_file)
                    })

            except Exception as e:
                logger.warning(f"Error reading evidence file {evidence_file}: {e}")
                continue

        return related_items

    def _check_roadmap_alignment(self, task_description: str) -> bool:
        """
        Check if task aligns with current roadmap.

        Returns:
            True if aligned with roadmap, False otherwise
        """
        # Find roadmap file
        roadmap_candidates = [
            self.orchestrator_root / "PROJECT_HQ.md",
            self.orchestrator_root / f"{self.config.project_name}_PROJECT_HQ.md",
        ]

        roadmap_content = None
        for roadmap_path in roadmap_candidates:
            if roadmap_path.exists():
                roadmap_content = roadmap_path.read_text()
                break

        if not roadmap_content:
            # No roadmap found - default to aligned (don't block without roadmap)
            logger.warning("No roadmap file found - defaulting to aligned")
            return True

        # Extract Q1 Focus section (simple keyword matching)
        # Look for keywords in task description that match roadmap focus areas
        description_lower = task_description.lower()

        # Common roadmap keywords for CredentialMate
        focus_keywords = [
            "cme tracking", "cme", "license renewal", "deadline", "multi-state",
            "compact state", "reciprocity", "np", "pa", "physician", "hipaa",
            "compliance", "accuracy"
        ]

        # If roadmap contains these keywords, check if task description also contains them
        roadmap_lower = roadmap_content.lower()

        for keyword in focus_keywords:
            if keyword in roadmap_lower and keyword in description_lower:
                return True  # Found matching focus area

        # If no matches found, might be off-roadmap
        # But be conservative - only block if roadmap explicitly exists and has focus areas
        if "q1 focus" in roadmap_lower or "roadmap" in roadmap_lower:
            return False  # Roadmap exists but task doesn't match
        else:
            return True  # No clear roadmap structure, default to aligned

    def _has_outcome_metrics(self, task_description: str, task_data: Optional[Dict[str, Any]]) -> bool:
        """
        Check if task has defined outcome metrics.

        Returns:
            True if outcome metrics defined, False otherwise
        """
        # Check task_data first
        if task_data and "outcome_metrics" in task_data:
            return bool(task_data["outcome_metrics"])

        # Check task description for metric keywords
        description_lower = task_description.lower()
        metric_keywords = [
            "measure", "metric", "kpi", "success criteria", "activation", "retention",
            "conversion", "time-to-value", "accuracy", "pass rate"
        ]

        return any(keyword in description_lower for keyword in metric_keywords)

    def _add_outcome_metrics_template(self, task_description: str) -> str:
        """
        Add outcome metrics template to task description.

        Returns:
            Modified task description with metrics template
        """
        template = """

## Outcome Metrics (Added by PM Agent)

Define how we'll measure success for this task:

**Primary Metric:**
- [ ] Define primary success metric (e.g., activation rate, retention, accuracy)

**Secondary Metrics:**
- [ ] Define 2-3 secondary metrics

**Acceptance Criteria:**
- [ ] What does "done" look like?
- [ ] How will we validate this works for users?

**Evidence:**
- [ ] Link to evidence items: EVIDENCE-XXX
"""
        return task_description + template

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
        logger.warning(f"PM Agent halting: {reason}")
        logger.info(f"Completed {self.current_iteration} iterations")
        logger.info(f"Iteration history: {len(self.iteration_history)} records")
