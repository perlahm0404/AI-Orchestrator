"""
Governance Hooks for AI Orchestrator

This module provides hooks for both the legacy CLI wrapper and the new SDK adapter:

Legacy (stop_hook.py):
- agent_stop_hook: Synchronous stop hook for CLI wrapper
- StopDecision: Enum for stop decisions
- StopHookResult: Dataclass for stop hook results

SDK (sdk_ralph_hook.py, sdk_stop_hook.py):
- ralph_post_tool_hook: Async PostToolUse hook for Ralph verification
- wiggum_stop_hook: Async Stop hook for iteration control
"""

# Legacy exports (for backward compatibility)
from governance.hooks.stop_hook import (
    agent_stop_hook,
    StopDecision,
    StopHookResult,
)

# SDK hook exports
from governance.hooks.sdk_ralph_hook import ralph_post_tool_hook
from governance.hooks.sdk_stop_hook import (
    wiggum_stop_hook,
    StopDecision as SDKStopDecision,
    StopHookResult as SDKStopHookResult,
)

__all__ = [
    # Legacy
    "agent_stop_hook",
    "StopDecision",
    "StopHookResult",
    # SDK
    "ralph_post_tool_hook",
    "wiggum_stop_hook",
    "SDKStopDecision",
    "SDKStopHookResult",
]
