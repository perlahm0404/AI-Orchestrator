"""
Ralph Guardrails

Pattern detection for forbidden code patterns that trigger BLOCKED verdicts.

Implementation: Phase 0 Week 1 Day 5
"""

from .patterns import scan_for_violations, GuardrailViolation

__all__ = ["scan_for_violations", "GuardrailViolation"]
