"""
Runtime Guardrails

Pre-execution hooks that block dangerous operations before they happen.

Guardrails are checked:
- Before every bash command (bash_security.py)
- Before every file write (no_new_features.py)
- Before every commit (governance_rules.py)

A blocked guardrail causes immediate halt - no retry, no override.

See: v4 Planning.md Section "Governance Hooks"
"""
