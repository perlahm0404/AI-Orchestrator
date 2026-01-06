# AI Orchestrator - Claude Code Configuration

## Session Startup Protocol (MANDATORY)

**CRITICAL**: This project uses externalized memory. Sessions are stateless.

Before doing ANY work, you MUST read these files in order:

1. `STATE.md` - Current build state (what's done/blocked/next)
2. `DECISIONS.md` - Build-time decisions with rationale
3. `sessions/latest.md` - Most recent session handoff

**If you skip this, you will:**
- Re-implement completed work
- Re-litigate settled decisions
- Break continuity between sessions

## Core Principles

1. **Sessions are stateless** - All context comes from external artifacts
2. **Memory is externalized** - Database, files, tests (not in-memory state)
3. **Placeholders are intentional** - Don't implement Phase 0/1 work unless asked
4. **TDD is primary memory** - Tests encode behavior; if not tested, doesn't exist
5. **Ralph is the law** - PASS/FAIL/BLOCKED verdicts are canonical

## Session Handoff Protocol (MANDATORY at end of session)

At the end of each work session:

1. Create `sessions/YYYY-MM-DD-{topic}.md` with:
   - What was accomplished
   - What was NOT done (and why)
   - Blockers / open questions
   - Files modified
   - Handoff notes for next session

2. Update the symlink: `ln -sf {new-file}.md sessions/latest.md`

3. Update `STATE.md` if build status changed

4. Add decision to `DECISIONS.md` if implementation choice was made

## Key Planning Documents

These documents define the project architecture (READ-ONLY):

- `v4 Planning.md` - Complete implementation plan
- `v4-PRD-AI-Brain-v1.md` - Product requirements
- `v4-HITL-PROJECT-PLAN.md` - Operational project plan
- `v4-RALPH-GOVERNANCE-ENGINE.md` - Ralph specification
- `v4-KNOWLEDGE-OBJECTS-v1.md` - Knowledge Object spec
- `v4-DECISION-v4-recommendations.md` - Design decisions

## What NOT to Do

- Don't implement placeholder files (agents/, ralph/, etc.) unless explicitly asked
- Don't modify planning documents (v4-*.md files)
- Don't skip the session startup protocol
- Don't forget to create session handoff notes
- Don't add features beyond what's requested

## Target Repositories

- **KareMatch**: `/Users/tmac/karematch` (L2 autonomy)
- **CredentialMate**: `/Users/tmac/credentialmate` (L1 autonomy, HIPAA)

## Current Phase

Check `STATE.md` for current phase. As of 2026-01-05:
- Phase: Pre-Phase -1 (Scaffolding Complete)
- Next: Phase -1 Trust Calibration (select bugs from KareMatch)

## Governance Hierarchy

```
Kill-Switch (OFF/SAFE/NORMAL/PAUSED)
    ↓
Autonomy Contract (per-agent YAML)
    ↓
Governance Rules (per-task-type)
    ↓
Ralph Verification (PASS/FAIL/BLOCKED)
    ↓
Human Approval (per-fix)
```

## Quick Reference

- Autonomy contracts: `governance/contracts/*.yaml`
- Ralph policy: `ralph/policy/v1.yaml`
- Adapter configs: `adapters/{app}/config.yaml`
- Database schema: `db/migrations/001_initial_schema.sql`
