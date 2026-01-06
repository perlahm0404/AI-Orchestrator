"""
AI Orchestrator - Agents Module

This module contains the autonomous agents that perform work:
- BugFix agent: Fixes bugs with evidence-based completion
- CodeQuality agent: Improves code quality in safe batches
- Refactor agent: Restructures code (Phase 2)

All agents:
- Are stateless (reconstruct context from external artifacts)
- Act within autonomy contracts (governance/contracts/*.yaml)
- Produce evidence for completion (Ralph verification)
- Halt on governance violations (BLOCKED verdict)

See: v4-HITL-PROJECT-PLAN.md for full specification
"""
