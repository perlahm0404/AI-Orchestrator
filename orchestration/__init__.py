"""
Orchestration Module

Manages agent lifecycle, resource limits, and domain advisor integration.

Key components:
- circuit_breaker.py: Auto-halt after repeated failures
- advisor_integration.py: Domain advisor integration for autonomous loop
- iteration_loop.py: Wiggum iteration control with completion signals
- state_file.py: Session state persistence for resume capability
- debate_context.py: Shared state for council debates
- debate_manifest.py: JSONL audit logging for debates
- message_bus.py: Inter-agent communication

Design principle: Sessions are stateless. All state is externalized
to state files, database, and git. An agent can be interrupted at any
time and resumed from the last state checkpoint.
"""

from .advisor_integration import (
    AutonomousAdvisorIntegration,
    AdvisorRouter,
    TaskAnalyzer,
    AdvisorType,
    analyze_task_for_advisors,
    create_advisor_integration,
)

# Council Pattern components
from .debate_context import Argument, DebateContext, EvidenceItem, Position
from .debate_manifest import DebateManifest
from .message_bus import Message, MessageBus
from .vote_aggregator import VoteAggregator
