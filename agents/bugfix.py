"""
BugFix Agent

Autonomously fixes bugs with evidence-based completion.

Workflow:
1. READ issue from database
2. CONSULT Knowledge Objects for related patterns
3. FIND or WRITE reproduction test (must fail)
4. ANALYZE root cause
5. APPLY minimal fix
6. RUN Ralph verification
7. CAPTURE evidence (before/after commits, test outputs)
8. GENERATE REVIEW.md
9. MARK issue as pending_review
10. HALT and wait for human approval

Constraints (from contracts/bugfix.yaml):
- Max 100 lines added
- Max 5 files changed
- Cannot modify migrations
- Cannot modify CI config
- Cannot push to main
- Must halt on Ralph BLOCKED

Implementation: Phase 1
"""

from .base import BaseAgent


class BugFixAgent(BaseAgent):
    """
    BugFix agent implementation.

    See module docstring for workflow.
    """

    def execute(self, task_id: str) -> dict:
        # TODO: Implement in Phase 1
        raise NotImplementedError("BugFixAgent not yet implemented")

    def checkpoint(self) -> dict:
        # TODO: Implement in Phase 1
        raise NotImplementedError("Checkpoint not yet implemented")

    def halt(self, reason: str) -> None:
        # TODO: Implement in Phase 1
        raise NotImplementedError("Halt not yet implemented")
