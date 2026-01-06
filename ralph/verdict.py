"""
Verdict Types and Semantics

Defines the contract for Ralph verdicts.

PASS:
- All verification steps succeeded
- Safe to proceed with merge/deploy
- Human can trust without re-verification

FAIL:
- One or more steps failed
- Issues are fixable (lint errors, test failures)
- Agent should attempt to fix and re-verify

BLOCKED:
- Guardrail violation detected
- Cannot proceed without removing violation
- Examples: test.skip(), @ts-ignore, eslint-disable
- Agent must halt immediately

See: v4-RALPH-GOVERNANCE-ENGINE.md Section "Verdict Semantics"
"""

from .engine import VerdictType, Verdict, StepResult

__all__ = ["VerdictType", "Verdict", "StepResult"]
