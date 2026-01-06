"""
Orchestration Module

Manages agent lifecycle, sessions, checkpoints, and circuit breakers.

Key components:
- session.py: Session lifecycle (start, checkpoint, resume, end)
- checkpoint.py: Save/restore state for resume capability
- circuit_breaker.py: Auto-halt after repeated failures

Design principle: Sessions are stateless. All state is externalized
to checkpoints, database, and git. An agent can be killed at any
time and resumed from the last checkpoint.

See: v4-HITL-PROJECT-PLAN.md Section "Session Survival"
"""
