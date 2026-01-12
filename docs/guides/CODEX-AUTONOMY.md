# Agent Autonomy Notes (Codex)

This file describes how Codex should operate autonomously in this repo.
It is tool-agnostic and intended to complement existing governance docs.

## Default Behavior

- Follow autonomy contracts in `governance/contracts/`.
- Use the governed harness (`run_agent.py` or `autonomous_loop.py`).
- Keep sessions stateless; rely on repo artifacts for context.

## Autonomous Mode (Non-Interactive)

Recommended for unattended runs:

```bash
python autonomous_loop.py --project karematch --max-iterations 50 --non-interactive
```

Notes:
- Guardrail violations auto-revert and the task is marked blocked.
- Governance approvals are auto-approved only where the loop already allows it.

## Claude CLI Permissions (Opt-In)

Claude CLI permission skipping is disabled by default.
To allow the wrapper to pass `--dangerously-skip-permissions`, set:

```bash
export AI_ORCHESTRATOR_CLAUDE_SKIP_PERMISSIONS=1
```

Leave unset for safer, permissioned behavior.

## Branching

- Use a dedicated branch for autonomous runs (e.g., `autonomy/*`).
- Avoid committing unrelated local changes.

## Escalation

If guardrails block progress repeatedly:
- Stop the loop.
- Create a human review task in the work queue.
