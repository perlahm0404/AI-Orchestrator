"""
Advisor to ADR Bridge

Determines when advisor consultations should trigger ADR creation
and builds the context needed for ADR generation.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from tasks.work_queue import WorkQueue
from orchestration.adr_generator import ADRContext
from orchestration.adr_registry import ADRRegistry

logger = logging.getLogger(__name__)


# Strategic domains that always trigger ADR creation
STRATEGIC_DOMAINS = {
    "security",
    "external_dependency",
    "data_schema",
    "infrastructure",
    "compliance",
    "cost"
}


def should_create_adr(
    task: Any,  # Task object
    result: Any,  # IterationResult object
    advisor_result: Dict[str, Any],
    changed_files: List[str]
) -> bool:
    """
    Determine if task warrants ADR creation.

    Returns True if ANY of these criteria are met:
    1. Strategic domain detected
    2. Multi-iteration learning (2-10 iterations + success + confidence ≥75%)
    3. ADR conflict detected
    4. Escalation resolved
    5. High impact scope (confidence ≥85% AND files ≥3)

    Exclusions:
    - Single iteration fixes (no learning pattern)
    - Tactical domain + auto-approval + <3 files (routine work)
    - Test-only changes

    Args:
        task: Task object with id, description, file
        result: IterationResult with iterations, verdict, status
        advisor_result: Advisor analysis result
        changed_files: List of changed file paths

    Returns:
        True if ADR should be created, False otherwise
    """
    # Must have advisor analysis
    if not advisor_result or not advisor_result.get("needs_advisor"):
        return False

    analysis = advisor_result.get("analysis", {})

    # Extract domain tags from analysis
    domain_tags = set(analysis.get("domain_tags", []))

    # Criterion 1: Strategic domain
    if domain_tags & STRATEGIC_DOMAINS:
        logger.info(f"ADR trigger: Strategic domain detected ({domain_tags & STRATEGIC_DOMAINS})")
        return True

    # Criterion 2: Multi-iteration learning
    iterations = getattr(result, 'iterations', 0)
    confidence = analysis.get("confidence", 0.0)

    if 2 <= iterations <= 10 and result.status == "completed" and confidence >= 0.75:
        logger.info(f"ADR trigger: Multi-iteration learning ({iterations} iterations, {confidence:.0%} confidence)")
        return True

    # Criterion 3: ADR conflict
    conflicting_adrs = analysis.get("conflicting_adrs", [])
    if conflicting_adrs:
        logger.info(f"ADR trigger: Conflict with {conflicting_adrs}")
        return True

    # Criterion 4: Escalation resolved
    escalations = advisor_result.get("escalations", [])
    if escalations and result.status == "completed":
        logger.info(f"ADR trigger: Escalation resolved ({len(escalations)} escalations)")
        return True

    # Criterion 5: High impact scope
    file_count = len(changed_files)
    if confidence >= 0.85 and file_count >= 3:
        logger.info(f"ADR trigger: High impact ({confidence:.0%} confidence, {file_count} files)")
        return True

    # Exclusions

    # Single iteration (no learning)
    if iterations <= 1:
        logger.debug("No ADR: Single iteration, no learning pattern")
        return False

    # Test-only changes
    if all("test" in f.lower() for f in changed_files):
        logger.debug("No ADR: Test-only changes")
        return False

    # Tactical domain with routine work
    if not domain_tags & STRATEGIC_DOMAINS and file_count < 3:
        logger.debug("No ADR: Tactical domain with small scope")
        return False

    return False


def build_adr_context(
    task: Any,
    result: Any,
    advisor_result: Dict[str, Any],
    changed_files: List[str]
) -> ADRContext:
    """
    Build complete context for ADR generation.

    Extracts all necessary data from task, result, and advisor analysis.

    Args:
        task: Task object
        result: IterationResult object
        advisor_result: Advisor analysis result
        changed_files: List of changed files

    Returns:
        ADRContext with all fields populated
    """
    analysis = advisor_result.get("analysis", {})

    # Extract domain tags
    domain_tags = analysis.get("domain_tags", [])

    # Determine decision type
    decision_type = "strategic" if set(domain_tags) & STRATEGIC_DOMAINS else "tactical"

    # Extract advisor type from analysis or recommendations
    advisor_type = _infer_advisor_type(analysis, advisor_result.get("recommendations", []))

    # Extract aligned/conflicting ADRs
    aligned_adrs = analysis.get("aligned_adrs", [])
    conflicting_adrs = analysis.get("conflicting_adrs", [])

    # Get recommendation text
    recommendations = advisor_result.get("recommendations", [])
    recommendation = "\n\n".join(recommendations) if recommendations else task.description

    # Check if escalated
    escalations = advisor_result.get("escalations", [])
    escalated = len(escalations) > 0
    escalation_reason = escalations[0] if escalations else None

    # Compute fingerprint
    fingerprint = _compute_fingerprint(task.description, domain_tags, decision_type)

    return ADRContext(
        task_id=task.id,
        description=task.description,
        decision_type=decision_type,
        advisor_type=advisor_type,
        confidence=analysis.get("confidence", 0.75),
        domain_tags=domain_tags,
        aligned_adrs=aligned_adrs,
        conflicting_adrs=conflicting_adrs,
        recommendation=recommendation,
        iterations=getattr(result, 'iterations', 1),
        files_changed=changed_files,
        escalated=escalated,
        escalation_reason=escalation_reason,
        fingerprint=fingerprint
    )


def register_adr_creation_task(
    task: Any,
    result: Any,
    advisor_result: Dict[str, Any],
    changed_files: List[str],
    work_queue: WorkQueue,
    project_root: Path
) -> Optional[str]:
    """
    Register admin task to create ADR.

    Steps:
    1. Check fingerprint against registry
    2. If duplicate, return None
    3. Build ADR context
    4. Call work_queue.register_discovered_task()
    5. Store context in task.adr_context field
    6. Save queue
    7. Return task_id

    Args:
        task: Task object
        result: IterationResult object
        advisor_result: Advisor analysis result
        changed_files: List of changed files
        work_queue: WorkQueue instance
        project_root: Project root path

    Returns:
        Task ID if created, None if duplicate
    """
    # Build context
    context = build_adr_context(task, result, advisor_result, changed_files)

    # Check for duplicate
    registry = ADRRegistry(project_root)
    existing_adr = registry.check_duplicate_fingerprint(context.fingerprint)
    if existing_adr:
        logger.info(f"Skipping ADR creation: duplicate fingerprint (existing: {existing_adr})")
        return None

    # Determine project from queue file path
    project = work_queue.project if hasattr(work_queue, 'project') else "AI_Orchestrator"

    # Create admin task description
    description = f"Create ADR draft: {context.description[:80]}"

    # Register task
    task_id = work_queue.register_discovered_task(
        source="AUTONOMOUS-DECISION",
        description=description,
        file="AI-Team-Plans/decisions/ADR-DRAFT.md",  # Placeholder, real path computed by agent
        discovered_by="autonomous-loop",
        priority=1,  # P1 - informational, not blocking
        task_type="admin"
    )

    if task_id:
        # Store context in task for agent to use
        # Find the task we just created
        for feature in work_queue.features:
            if feature.id == task_id:
                # Store context as dict
                feature.adr_context = {
                    "task_id": context.task_id,
                    "description": context.description,
                    "decision_type": context.decision_type,
                    "advisor_type": context.advisor_type,
                    "confidence": context.confidence,
                    "domain_tags": context.domain_tags,
                    "aligned_adrs": context.aligned_adrs,
                    "conflicting_adrs": context.conflicting_adrs,
                    "recommendation": context.recommendation,
                    "iterations": context.iterations,
                    "files_changed": context.files_changed,
                    "escalated": context.escalated,
                    "escalation_reason": context.escalation_reason,
                    "fingerprint": context.fingerprint,
                    "project": project
                }
                break

        logger.info(f"Registered ADR creation task: {task_id}")

    return task_id


def _infer_advisor_type(analysis: Dict[str, Any], recommendations: List[str]) -> str:
    """Infer which advisor type from analysis or recommendations."""
    domain_tags = set(analysis.get("domain_tags", []))

    # Check for data advisor keywords
    data_keywords = {"database", "schema", "migration", "query", "sql", "data_model"}
    if domain_tags & data_keywords:
        return "data"

    # Check for UI/UX advisor keywords
    uiux_keywords = {"ui", "ux", "component", "accessibility", "frontend", "react", "css"}
    if domain_tags & uiux_keywords:
        return "uiux"

    # Default to app advisor
    return "app"


def _compute_fingerprint(description: str, domain_tags: List[str], decision_type: str) -> str:
    """
    Compute SHA256 fingerprint for deduplication.

    Format: SHA256(description:domain_tags:decision_type)[:16]

    Args:
        description: Task description
        domain_tags: List of domain tags
        decision_type: "strategic" or "tactical"

    Returns:
        16-character hex fingerprint
    """
    # Normalize inputs
    normalized_desc = description.lower().strip()
    normalized_tags = ",".join(sorted(domain_tags))

    # Compute hash
    data = f"{normalized_desc}:{normalized_tags}:{decision_type}"
    hash_obj = hashlib.sha256(data.encode('utf-8'))
    fingerprint = hash_obj.hexdigest()[:16]

    return fingerprint
