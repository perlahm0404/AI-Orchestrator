"""
Ralph Core Verification Engine

Entry point for all verification requests.

Usage:
    from ralph import engine

    verdict = engine.verify(
        project="karematch",
        changes=["src/auth.ts", "tests/auth.test.ts"],
        session_id="abc-123"
    )

    if verdict.type == VerdictType.BLOCKED:
        # Halt immediately, cannot proceed
        agent.halt(verdict.reason)
    elif verdict.type == VerdictType.FAIL:
        # Can retry after fixing issues
        handle_failures(verdict.failures)
    else:
        # PASS - safe to proceed
        proceed_with_merge()

Implementation: Phase 0
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class VerdictType(Enum):
    """Verification outcome types."""
    PASS = "PASS"       # All steps succeeded
    FAIL = "FAIL"       # One or more steps failed (fixable)
    BLOCKED = "BLOCKED" # Guardrail violation (not fixable)


@dataclass
class StepResult:
    """Result of a single verification step."""
    step: str           # e.g., "guardrails", "lint", "typecheck"
    passed: bool
    output: str
    duration_ms: int


@dataclass
class Verdict:
    """
    Complete verification result.

    This is the canonical output of Ralph verification.
    """
    type: VerdictType
    steps: list[StepResult]
    reason: str | None = None  # For BLOCKED/FAIL
    evidence: dict[str, Any] | None = None


def verify(
    project: str,
    changes: list[str],
    session_id: str,
    policy_version: str = "v1",
    app_context: Any = None
) -> Verdict:
    """
    Run full verification pipeline.

    Args:
        project: Target project (e.g., "karematch")
        changes: List of changed file paths
        session_id: Current session ID for audit
        policy_version: Policy version to use (default "v1")
        app_context: AppContext with project-specific config (optional)

    Returns:
        Verdict with PASS/FAIL/BLOCKED and evidence
    """
    from pathlib import Path
    from ralph.steps import run_step, StepConfig
    from ralph.guardrails import scan_for_violations

    # For MVP, if no app_context provided, return a placeholder
    if app_context is None:
        return Verdict(
            type=VerdictType.FAIL,
            steps=[],
            reason="No app_context provided",
            evidence={"error": "app_context required"}
        )

    project_path = Path(app_context.project_path)
    steps_results = []

    # Step 0: Guardrail scan (CRITICAL - runs first)
    violations = scan_for_violations(
        project_path=project_path,
        changed_files=changes,
        source_paths=app_context.source_paths
    )

    if violations:
        # BLOCKED verdict - guardrail violations detected
        violation_summary = "\n".join([
            f"  {v.file_path}:{v.line_number} - {v.pattern} ({v.reason})"
            for v in violations[:10]  # Limit to first 10
        ])

        guardrail_step = StepResult(
            step="guardrails",
            passed=False,
            output=f"Guardrail violations detected:\n{violation_summary}",
            duration_ms=0
        )
        steps_results.append(guardrail_step)

        return Verdict(
            type=VerdictType.BLOCKED,
            steps=steps_results,
            reason=f"{len(violations)} guardrail violation(s) detected",
            evidence={
                "project": project,
                "changes": changes,
                "session_id": session_id,
                "policy_version": policy_version,
                "violations": [
                    {
                        "file": v.file_path,
                        "line": v.line_number,
                        "pattern": v.pattern,
                        "reason": v.reason
                    }
                    for v in violations
                ]
            }
        )

    # Guardrails passed
    guardrail_step = StepResult(
        step="guardrails",
        passed=True,
        output="No guardrail violations detected",
        duration_ms=0
    )
    steps_results.append(guardrail_step)

    # Step 1: Lint
    if app_context.lint_command:
        lint_result = run_step(StepConfig(
            name="lint",
            command=app_context.lint_command,
            cwd=project_path
        ))
        steps_results.append(lint_result)

    # Step 2: Typecheck
    if app_context.typecheck_command:
        typecheck_result = run_step(StepConfig(
            name="typecheck",
            command=app_context.typecheck_command,
            cwd=project_path
        ))
        steps_results.append(typecheck_result)

    # Step 3: Tests
    if app_context.test_command:
        test_result = run_step(StepConfig(
            name="test",
            command=app_context.test_command,
            cwd=project_path
        ))
        steps_results.append(test_result)

    # Determine verdict type
    all_passed = all(step.passed for step in steps_results)

    if all_passed:
        verdict_type = VerdictType.PASS
        reason = None
    else:
        # Find first failed step
        failed_step = next((s for s in steps_results if not s.passed), None)
        verdict_type = VerdictType.FAIL
        reason = f"Step '{failed_step.step}' failed" if failed_step else "Unknown failure"

    return Verdict(
        type=verdict_type,
        steps=steps_results,
        reason=reason,
        evidence={
            "project": project,
            "changes": changes,
            "session_id": session_id,
            "policy_version": policy_version
        }
    )
