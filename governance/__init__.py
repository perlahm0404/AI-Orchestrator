"""
Governance Module

Enforces agent boundaries through:
- Autonomy Contracts: YAML policy defining allowed/forbidden actions
- Guardrails: Runtime checks that block dangerous operations
- Kill Switch: Global controls (OFF/SAFE/NORMAL/PAUSED)
- @require_harness: Decorator preventing code from running outside harness

Governance Hierarchy:
1. Kill-Switch (global)
2. Autonomy Contract (per-agent)
3. Governance Rules (per-task-type)
4. Ralph Verification (per-change)

See: v4 Planning.md Section "Autonomy Contracts"
"""

from governance.require_harness import (
    require_harness,
    require_harness_async,
    HarnessContext,
    HarnessRequiredError,
    is_harness_active,
    set_harness_active,
)

__all__ = [
    "require_harness",
    "require_harness_async",
    "HarnessContext",
    "HarnessRequiredError",
    "is_harness_active",
    "set_harness_active",
]
