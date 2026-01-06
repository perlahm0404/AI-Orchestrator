# AI Orchestrator (AI Brain v4)

## What This Is

AI Orchestrator is an autonomous multi-agent system for governed code quality improvement. It deploys AI agents that fix bugs and improve code quality with:

- **Evidence-based completion** - No task marked done without proof (tests pass, Ralph verifies)
- **Human-in-the-loop approval** - Agents execute, humans approve what ships
- **Institutional memory** - Knowledge Objects capture learning that survives sessions
- **Explicit governance** - Autonomy contracts define what agents can/cannot do

## Repository Location

```
/Users/tmac/Vaults/AI_Orchestrator    # This repo (standalone governance + orchestration)
/Users/tmac/Vaults/AI_Brain           # Research vault with 30+ analyzed repos
/Users/tmac/karematch                 # Target app (L2 autonomy)
/Users/tmac/credentialmate            # Target app (L1 autonomy, HIPAA)
```

## Quick Start

### Current Phase: Pre-Implementation (Planning Complete)

All v4 planning artifacts are finalized. Next step is Phase -1 Trust Calibration.

### Key Planning Documents

| Document | Purpose |
|----------|---------|
| [v4 Planning.md](./v4%20Planning.md) | Complete implementation plan |
| [v4-PRD-AI-Brain-v1.md](./v4-PRD-AI-Brain-v1.md) | Product requirements |
| [v4-HITL-PROJECT-PLAN.md](./v4-HITL-PROJECT-PLAN.md) | Operational project plan with repo structure |
| [v4-RALPH-GOVERNANCE-ENGINE.md](./v4-RALPH-GOVERNANCE-ENGINE.md) | Ralph governance engine specification |
| [v4-KNOWLEDGE-OBJECTS-v1.md](./v4-KNOWLEDGE-OBJECTS-v1.md) | Knowledge Object specification |
| [v4-DECISION-v4-recommendations.md](./v4-DECISION-v4-recommendations.md) | Design decisions and rationale |

---

## Agent Memory Protocol

**CRITICAL**: Sessions are stateless. All memory is externalized. Read these files on every session start.

### Session Startup Checklist

```
1. Read STATE.md           → What's the current state?
2. Read DECISIONS.md       → What decisions were already made?
3. Read sessions/latest.md → What happened last session?
4. Proceed with work
5. Before ending: Update STATE.md and create session handoff
```

### Memory Files

| File | Purpose | When to Update |
|------|---------|----------------|
| [STATE.md](./STATE.md) | Current build state, what's done/blocked/next | Every significant change |
| [DECISIONS.md](./DECISIONS.md) | Build-time decisions with rationale | When making implementation choices |
| [sessions/latest.md](./sessions/latest.md) | Most recent session handoff | End of every session |

### Session Handoff Protocol

At the end of each work session, create `sessions/YYYY-MM-DD-{topic}.md`:

```markdown
# Session: YYYY-MM-DD - Topic

**Session ID**: {unique-id}
**Outcome**: {one-line summary}

## What Was Accomplished
- Item 1
- Item 2

## What Was NOT Done
- Item 1 (reason)

## Blockers / Open Questions
1. Question 1
2. Question 2

## Files Modified
| File | Action |
|------|--------|
| file1 | Created/Modified/Deleted |

## Handoff Notes
{Context the next session needs to continue work}
```

Then update the symlink: `ln -sf {new-file}.md latest.md`

---

## Core Concepts

### Governance Hierarchy

```
Kill-Switch (global: OFF/SAFE/NORMAL/PAUSED)
    │
    ▼
Autonomy Contract (per-agent: allowed/forbidden/approval-required)
    │
    ▼
Governance Rules (per-task-type)
    │
    ▼
Ralph Verification (per-change: PASS/FAIL/BLOCKED)
    │
    ▼
Human Approval (per-fix)
```

### Target Applications

| App | Autonomy Level | Stack |
|-----|---------------|-------|
| **KareMatch** | L2 (higher autonomy) | Node/TS monorepo, Vitest, Playwright |
| **CredentialMate** | L1 (HIPAA, stricter) | FastAPI + Next.js + PostgreSQL |

### Key Invariants

1. **Sessions are stateless** - Agents reconstruct context from external artifacts
2. **Memory is externalized** - Database, files, tests (not in-memory state)
3. **Agents act within contracts** - Explicit YAML policy, enforced by hooks
4. **Humans approve promotion** - Agents execute, humans decide what ships
5. **TDD is primary memory** - Tests encode behavior; if not tested, doesn't exist
6. **Ralph is the law** - PASS/FAIL/BLOCKED verdicts are canonical

---

## Planned Directory Structure

```
ai-orchestrator/
├── agents/
│   ├── base.py                    # Shared agent protocol
│   ├── bugfix.py                  # BugFix agent
│   ├── codequality.py             # CodeQuality agent
│   └── refactor.py                # Refactor agent (Phase 2)
├── ralph/
│   ├── engine.py                  # Core verification engine
│   ├── verdict.py                 # PASS/FAIL/BLOCKED semantics
│   ├── policy/
│   │   └── v1.yaml                # Policy set v1 (immutable once released)
│   ├── guardrails/                # Shortcut/suppression detection
│   └── steps/                     # Lint, typecheck, test, coverage steps
├── governance/
│   ├── contracts/
│   │   ├── bugfix.yaml            # Autonomy contract
│   │   ├── codequality.yaml
│   │   └── refactor.yaml
│   ├── guardrails/
│   │   ├── bash_security.py       # Command allowlist
│   │   └── no_new_features.py     # Scope creep detection
│   └── kill_switch/
│       └── mode.py                # OFF/SAFE/NORMAL/PAUSED
├── knowledge/
│   ├── approved/                  # Markdown mirrors (synced from DB)
│   ├── drafts/
│   └── service.py                 # CRUD, matching, consultation
├── orchestration/
│   ├── session.py                 # Session lifecycle
│   ├── checkpoint.py              # Resume capability
│   └── circuit_breaker.py         # Failure handling
├── adapters/
│   ├── base.py                    # Adapter interface
│   ├── karematch/                 # KareMatch-specific config + Ralph invocation
│   └── credentialmate/            # CredentialMate-specific config
├── audit/
│   ├── logger.py                  # Action logging with causality
│   └── queries.py                 # Causality chain queries
├── db/
│   └── migrations/
├── cli/
│   └── commands/                  # aibrain status, approve, reject, etc.
├── tests/
│   ├── governance/
│   │   └── test_negative_capabilities.py
│   └── integration/
└── docs/
```

---

## Implementation Phases

### Phase -1: Trust Calibration (1 week)
- Fix 3 trivial + 1 medium bug manually
- Test that guardrails block forbidden actions
- Calibrate thresholds
- Go/No-Go decision

### Phase 0: Governance Foundation (2 weeks)
- Implement autonomy contracts (YAML)
- Implement kill-switch and safe mode
- Deploy enhanced audit schema
- Write and pass negative capability tests

### Phase 1: BugFix + CodeQuality Agents (4-6 weeks)
- Deploy BugFix agent on KareMatch
- First real bug fixed with full evidence
- Deploy CodeQuality agent
- Exit: 10 bugs fixed, 50 quality issues fixed, zero regressions

---

## Research Context

The `/Users/tmac/Vaults/AI_Brain` vault contains 30+ analyzed repositories that informed this design:

### Key Pattern Sources

| Folder | What Was Extracted |
|--------|-------------------|
| `amado/` | Orchestrator patterns, session management |
| `karematch-ai/` | Ralph Wiggum governance, evidence workflows |
| `credentialmate/` | HIPAA compliance patterns, L1 autonomy |
| `execution-patterns/` | Checkpoint/resume, circuit breaker |
| `error-patterns/` | Failure handling, escalation |

### Design Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Repo structure | Standalone | Single brain manages multiple projects |
| Ralph ownership | Centralized in AI Brain | Apps provide context, not policy |
| Policy versioning | Immutable (v1 locked forever) | Trust requires stability |
| Knowledge matching | Tag-based (no vectors) | Simple, sufficient for v1 |
| Schema approach | Pragmatic (not OpenTelemetry) | Right-sized for 2 apps |

---

## CLI Commands (Planned)

```bash
# Status
aibrain status                    # Overall system status
aibrain status TASK-123           # Specific task status

# Approvals
aibrain approve TASK-123          # Approve fix, merge PR
aibrain reject TASK-123 "reason"  # Reject fix, close PR

# Knowledge Objects
aibrain ko approve KO-km-001      # Approve Knowledge Object
aibrain ko pending                # List pending KOs

# Emergency Controls
aibrain emergency-stop            # AI_BRAIN_MODE=OFF
aibrain pause                     # AI_BRAIN_MODE=PAUSED
aibrain resume                    # AI_BRAIN_MODE=NORMAL
```

---

## What Agents Can/Cannot Do

### BugFix Agent

**Allowed**:
- Read files, write files
- Run tests, run Ralph
- Create branches, commit changes
- Generate REVIEW.md

**Forbidden**:
- Modify migrations
- Modify CI config
- Push to main
- Deploy anything

**Limits**:
- Max 100 lines added
- Max 5 files changed
- Must halt on Ralph BLOCKED

### CodeQuality Agent

**Allowed**:
- Auto-fix lint/type issues
- Run in batches (max 20)
- Rollback on test failure

**Forbidden**:
- Change behavior (test count must stay same)
- Add new features
- Remove tests

---

## Success Metrics

### Phase 1 Targets

| Metric | Target |
|--------|--------|
| Real bugs fixed | >= 10 |
| Quality issues fixed | >= 50 |
| Regressions introduced | 0 |
| Human review time per fix | < 5 minutes |
| Approval rate | > 80% |

---

## Next Steps

1. [ ] Review and approve V4 plan
2. [ ] Set up Phase -1 calibration environment
3. [ ] Select 3 trivial + 1 medium bug from KareMatch
4. [ ] Execute Trust Calibration Sprint
5. [ ] Make Go/No-Go decision for Phase 0