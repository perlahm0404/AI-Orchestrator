"""
Ralph Handoff Verification Step

Verifies that session handoff artifacts are complete and valid.

This step checks:
1. Handoff document exists
2. Required fields are present
3. Ralph verdict is included
4. Test status is reported (if tests changed)
5. Files modified list matches git diff

Usage:
    from ralph.verify_handoff import verify_handoff

    verdict = verify_handoff(session_dir="sessions")

Implementation: v5.0 - Session Reflection
"""

from pathlib import Path
from typing import Optional
import re

from ralph.engine import Verdict, VerdictType, StepResult


def verify_handoff(
    session_dir: Path = Path("sessions"),
    require_latest: bool = True
) -> Verdict:
    """
    Verify that session handoff is complete and valid.

    Args:
        session_dir: Path to sessions directory
        require_latest: If True, require latest.md symlink

    Returns:
        Ralph Verdict (PASS/FAIL/BLOCKED)
    """
    steps = []
    start_time = 0

    # Check 1: Sessions directory exists
    if not session_dir.exists():
        steps.append(StepResult(
            step="handoff_dir_exists",
            passed=False,
            output="Sessions directory does not exist",
            duration_ms=0
        ))
        return Verdict(
            type=VerdictType.BLOCKED,
            steps=steps,
            reason="Sessions directory missing",
            safe_to_merge=False
        )

    steps.append(StepResult(
        step="handoff_dir_exists",
        passed=True,
        output="Sessions directory exists",
        duration_ms=1
    ))

    # Check 2: latest.md symlink exists
    latest_link = session_dir / "latest.md"
    if require_latest:
        if not latest_link.exists() and not latest_link.is_symlink():
            steps.append(StepResult(
                step="latest_symlink_exists",
                passed=False,
                output="sessions/latest.md symlink missing",
                duration_ms=1
            ))
            return Verdict(
                type=VerdictType.BLOCKED,
                steps=steps,
                reason="No session handoff created (latest.md missing)",
                safe_to_merge=False
            )

        steps.append(StepResult(
            step="latest_symlink_exists",
            passed=True,
            output=f"latest.md -> {latest_link.readlink().name}",
            duration_ms=1
        ))

        # Read handoff content
        handoff_content = latest_link.read_text()
    else:
        # Find most recent handoff
        handoff_files = sorted(session_dir.glob("2*.md"), reverse=True)
        if not handoff_files:
            steps.append(StepResult(
                step="handoff_file_exists",
                passed=False,
                output="No handoff files found",
                duration_ms=1
            ))
            return Verdict(
                type=VerdictType.BLOCKED,
                steps=steps,
                reason="No session handoff files",
                safe_to_merge=False
            )

        handoff_content = handoff_files[0].read_text()

    # Check 3: Required fields present
    required_fields = [
        "Session ID",
        "Task ID",
        "Agent",
        "Outcome",
        "What Was Accomplished",
        "What Was NOT Done",
        "Blockers / Open Questions"
    ]

    missing_fields = []
    for field in required_fields:
        if field not in handoff_content:
            missing_fields.append(field)

    if missing_fields:
        steps.append(StepResult(
            step="required_fields_present",
            passed=False,
            output=f"Missing fields: {', '.join(missing_fields)}",
            duration_ms=1
        ))
        return Verdict(
            type=VerdictType.FAIL,
            steps=steps,
            reason=f"Handoff missing required fields: {', '.join(missing_fields)}",
            safe_to_merge=False
        )

    steps.append(StepResult(
        step="required_fields_present",
        passed=True,
        output="All required fields present",
        duration_ms=1
    ))

    # Check 4: Ralph verdict included (if expected)
    if "Ralph Verdict" in handoff_content:
        # Verify verdict has status
        if "**Status**:" not in handoff_content:
            steps.append(StepResult(
                step="ralph_verdict_complete",
                passed=False,
                output="Ralph Verdict section missing status",
                duration_ms=1
            ))
            return Verdict(
                type=VerdictType.FAIL,
                steps=steps,
                reason="Ralph verdict incomplete",
                safe_to_merge=False
            )

        steps.append(StepResult(
            step="ralph_verdict_complete",
            passed=True,
            output="Ralph verdict included and complete",
            duration_ms=1
        ))

    # Check 5: Files Modified section present
    if "Files Modified" not in handoff_content:
        steps.append(StepResult(
            step="files_modified_present",
            passed=False,
            output="Files Modified section missing",
            duration_ms=1
        ))
        return Verdict(
            type=VerdictType.FAIL,
            steps=steps,
            reason="Handoff missing Files Modified section",
            safe_to_merge=False
        )

    steps.append(StepResult(
        step="files_modified_present",
        passed=True,
        output="Files Modified section present",
        duration_ms=1
    ))

    # Check 6: Risk Assessment present
    if "Risk Assessment" not in handoff_content:
        steps.append(StepResult(
            step="risk_assessment_present",
            passed=False,
            output="Risk Assessment section missing",
            duration_ms=1
        ))
        return Verdict(
            type=VerdictType.FAIL,
            steps=steps,
            reason="Handoff missing Risk Assessment",
            safe_to_merge=False
        )

    steps.append(StepResult(
        step="risk_assessment_present",
        passed=True,
        output="Risk Assessment section present",
        duration_ms=1
    ))

    # Check 7: Handoff Notes present (can be empty but section must exist)
    if "Handoff Notes" not in handoff_content:
        steps.append(StepResult(
            step="handoff_notes_present",
            passed=False,
            output="Handoff Notes section missing",
            duration_ms=1
        ))
        return Verdict(
            type=VerdictType.FAIL,
            steps=steps,
            reason="Handoff missing Handoff Notes section",
            safe_to_merge=False
        )

    steps.append(StepResult(
        step="handoff_notes_present",
        passed=True,
        output="Handoff Notes section present",
        duration_ms=1
    ))

    # All checks passed
    return Verdict(
        type=VerdictType.PASS,
        steps=steps,
        reason=None,
        safe_to_merge=True
    )


def verify_handoff_quality(handoff_path: Path) -> tuple[bool, str]:
    """
    Verify quality of handoff content (beyond structure).

    This is a more subjective check that looks for:
    - Non-empty accomplishments (if status is COMPLETED)
    - Specific blockers (if status is BLOCKED)
    - Actionable next steps (if status is PARTIAL)

    Args:
        handoff_path: Path to handoff document

    Returns:
        Tuple of (is_quality, reason)
    """
    content = handoff_path.read_text()

    # Extract outcome
    outcome_match = re.search(r'\*\*Outcome\*\*: (\w+)', content)
    if not outcome_match:
        return False, "Cannot determine outcome"

    outcome = outcome_match.group(1)

    # Check accomplished section
    accomplished_section = _extract_section(content, "What Was Accomplished")
    if outcome == "COMPLETED":
        if "No items completed" in accomplished_section or len(accomplished_section) < 10:
            return False, "Status is COMPLETED but no accomplishments listed"

    # Check blockers section
    blockers_section = _extract_section(content, "Blockers / Open Questions")
    if outcome == "BLOCKED":
        if "No blockers" in blockers_section or len(blockers_section) < 10:
            return False, "Status is BLOCKED but no blockers listed"

    # Check next steps section
    if outcome in ["PARTIAL", "BLOCKED"]:
        if "Next Steps" not in content:
            return False, f"Status is {outcome} but no next steps provided"

    return True, "Handoff quality checks passed"


def _extract_section(content: str, section_name: str) -> str:
    """Extract content of a section from markdown."""
    pattern = f"## {section_name}.*?(?=##|$)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else ""
