"""
Ralph Wiggum Governance Engine

Centralized verification system that produces PASS/FAIL/BLOCKED verdicts.

Ralph is the law:
- PASS: All steps succeeded, safe to proceed
- FAIL: One or more steps failed (fixable)
- BLOCKED: Guardrail violation (not fixable without removing violation)

Key invariants:
1. Ralph is the law - Verdicts are canonical
2. Policy is immutable - v1 is locked forever once released
3. Apps provide context - Commands, paths, not rules
4. Agents obey - BLOCKED means stop, no exceptions
5. Humans trust - PASS means verified, no re-checking needed
6. Audit is complete - Every verdict has evidence

See: v4-RALPH-GOVERNANCE-ENGINE.md for full specification
"""
