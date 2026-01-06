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

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from governance.require_harness import require_harness


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

    Key fields:
    - type: PASS/FAIL/BLOCKED
    - safe_to_merge: Clear boolean signal for merge decisions
    - regression_detected: True if this change broke something that was working
    - pre_existing_failures: List of steps that were already failing before changes
    """
    type: VerdictType
    steps: list[StepResult]
    reason: Optional[str] = None  # For BLOCKED/FAIL
    evidence: Optional[dict[str, Any]] = None

    # Enhanced fields for clearer decision-making
    safe_to_merge: bool = False  # Clear signal: can this be merged?
    regression_detected: bool = False  # Did this change break something?
    pre_existing_failures: list[str] = field(default_factory=list)  # Steps already failing

    def summary(self) -> str:
        """
        Human-readable summary of the verdict.

        Returns a formatted string suitable for display.
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"RALPH VERDICT: {self.type.value}")
        lines.append("=" * 60)

        # Safe to merge signal (the most important field)
        if self.safe_to_merge:
            lines.append("✅ SAFE TO MERGE")
        else:
            lines.append("❌ NOT SAFE TO MERGE")

        lines.append("")

        # Step results
        for step in self.steps:
            icon = "✅" if step.passed else "❌"
            lines.append(f"{icon} {step.step}: {'PASS' if step.passed else 'FAIL'}")

        # Pre-existing failures notice
        if self.pre_existing_failures:
            lines.append("")
            lines.append("ℹ️  PRE-EXISTING FAILURES (not caused by this change):")
            for step in self.pre_existing_failures:
                lines.append(f"   - {step}")

        # Regression warning
        if self.regression_detected:
            lines.append("")
            lines.append("⚠️  REGRESSION DETECTED: This change made things worse")

        # Reason
        if self.reason:
            lines.append("")
            lines.append(f"Reason: {self.reason}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict for logging/API responses."""
        return {
            "type": self.type.value,
            "safe_to_merge": self.safe_to_merge,
            "regression_detected": self.regression_detected,
            "pre_existing_failures": self.pre_existing_failures,
            "reason": self.reason,
            "steps": [
                {
                    "step": s.step,
                    "passed": s.passed,
                    "duration_ms": s.duration_ms,
                }
                for s in self.steps
            ],
            "evidence": self.evidence,
        }


@require_harness
def verify(
    project: str,
    changes: list[str],
    session_id: str,
    policy_version: str = "v1",
    app_context: Any = None,
    baseline: Optional["Baseline"] = None,  # type: ignore
) -> Verdict:
    """
    Run full verification pipeline.

    Args:
        project: Target project (e.g., "karematch")
        changes: List of changed file paths
        session_id: Current session ID for audit
        policy_version: Policy version to use (default "v1")
        app_context: AppContext with project-specific config (optional)
        baseline: Pre-recorded baseline for regression detection (optional)

    Returns:
        Verdict with PASS/FAIL/BLOCKED and evidence

    The `safe_to_merge` field is set based on:
    - BLOCKED: Never safe (guardrail violation)
    - PASS: Always safe (everything passes)
    - FAIL: Safe only if all failures were pre-existing (no regressions)
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
            evidence={"error": "app_context required"},
            safe_to_merge=False,
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
            },
            safe_to_merge=False,  # BLOCKED is never safe
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

    # Determine verdict type and safe_to_merge
    all_passed = all(step.passed for step in steps_results)
    failed_steps = [s.step for s in steps_results if not s.passed]
    pre_existing_failures: list[str] = []
    regression_detected = False

    # Compare against baseline if provided
    if baseline is not None:
        # Check each failed step against baseline
        for step in steps_results:
            if not step.passed:
                baseline_step = baseline.steps.get(step.step)
                if baseline_step and baseline_step.status.value == "fail":
                    # This step was already failing - pre-existing failure
                    pre_existing_failures.append(step.step)
                else:
                    # This step was passing before - regression!
                    regression_detected = True

    if all_passed:
        verdict_type = VerdictType.PASS
        reason = None
        safe_to_merge = True
    else:
        # Find first failed step
        failed_step = next((s for s in steps_results if not s.passed), None)
        verdict_type = VerdictType.FAIL
        reason = f"Step '{failed_step.step}' failed" if failed_step else "Unknown failure"

        # Determine if safe to merge despite failures
        if regression_detected:
            # This change broke something - NOT safe
            safe_to_merge = False
            reason = f"REGRESSION: {reason}"
        elif baseline is not None and set(failed_steps) <= set(pre_existing_failures):
            # All failures are pre-existing - safe to merge
            safe_to_merge = True
            reason = f"Pre-existing failure in {failed_step.step} (not caused by this change)"
        else:
            # No baseline to compare against, be conservative
            safe_to_merge = False

    return Verdict(
        type=verdict_type,
        steps=steps_results,
        reason=reason,
        evidence={
            "project": project,
            "changes": changes,
            "session_id": session_id,
            "policy_version": policy_version,
            "baseline_commit": baseline.commit_hash if baseline else None,
        },
        safe_to_merge=safe_to_merge,
        regression_detected=regression_detected,
        pre_existing_failures=pre_existing_failures,
    )
