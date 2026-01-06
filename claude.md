# AI Orchestrator (AI Brain v5)

## What This Is

AI Orchestrator is an autonomous multi-agent system for governed code quality improvement AND feature development. It deploys **two specialized teams** of AI agents:

| Team | Mission | Autonomy |
|------|---------|----------|
| **QA Team** | Maintain code quality on stable code | L2 (higher) |
| **Dev Team** | Build new features in isolation | L1 (stricter) |

### Core Principles

- **Evidence-based completion** - No task marked done without proof (tests pass, Ralph verifies)
- **Human-in-the-loop approval** - Agents execute, humans approve what ships
- **Institutional memory** - Knowledge Objects capture learning that survives sessions
- **Explicit governance** - Autonomy contracts define what agents can/cannot do
- **Team isolation** - QA and Dev work on separate branches, merge at defined points

## Repository Location

```
/Users/tmac/Vaults/AI_Orchestrator    # This repo (standalone governance + orchestration)
/Users/tmac/Vaults/AI_Brain           # Research vault with 30+ analyzed repos
/Users/tmac/karematch                 # Target app (L2 autonomy)
/Users/tmac/credentialmate            # Target app (L1 autonomy, HIPAA)
```

## Quick Start

### Current Phase: v5.1 - Wiggum + Autonomous Integration

**Status**: 📋 Planning complete, ready for implementation

- ✅ v4 complete (all phases delivered)
- ✅ v5.0 complete (Dual-Team Architecture deployed, Wiggum iteration patterns implemented)
- ✅ autonomous_loop.py complete (work queue + fast verification + Claude CLI integration)
- 📋 v5.1 planned (Integrate Wiggum into autonomous_loop for 85% autonomy)

**v5.1 Integration Plan** (1-2 days):
- **Step 1**: Enhance task schema (completion promises) - 30min
- **Step 2**: Create agent factory - 45min
- **Step 3**: Integrate IterationLoop into autonomous_loop.py - 2hr
- **Step 4**: Update agent.execute() for promises - 1hr
- **Step 5**: Enhance progress tracking - 30min
- **Step 6**: Update CLI and docs - 45min
- **Testing**: Unit + Integration + Production - 7hr

**Key Insight**: Both systems fully implemented! Just need to integrate them (~400 new LOC, ~200 modified).

**Integration Benefits**:
- Retries per task: 3 → **15-50** (agent-specific budgets)
- Completion detection: Files only → **`<promise>` tags + verification**
- BLOCKED handling: Skip task → **Human R/O/A override**
- Session resume: Manual → **Automatic from state files**
- Iteration tracking: None → **Full audit trail**

**Success Metrics**:
- Autonomy: 60% → **85%**
- Tasks per session: 10-15 → **30-50**
- Verification: Already 30 seconds (Phase 2 complete)
- Self-correction: 3 retries → **15-50 retries** (agent-specific)

### Key Planning Documents

| Document | Purpose |
|----------|---------|
| [Wiggum + Autonomous Integration Plan](./docs/planning/wiggum-autonomous-integration-plan.md) | **v5.1 - Integration plan (6 steps, 1-2 days)** |
| [Autonomous Implementation Plan](./docs/planning/autonomous-implementation-plan.md) | Original v5.1 plan (superseded by integration) |
| [v5.1 Wiggum Plan](/.claude/plans/jaunty-humming-hartmanis.md) | ✅ COMPLETE - Wiggum iteration system |
| [RALPH-COMPARISON.md](./RALPH-COMPARISON.md) | Ralph vs Wiggum comparison |
| [v5-Planning.md](./docs/planning/v5-Planning.md) | Dual-Team Architecture spec |
| [KAREMATCH-WORK-ORGANIZATION-PLAN.md](./docs/planning/KAREMATCH-WORK-ORGANIZATION-PLAN.md) | KareMatch feature/QA coordination |
| [v4 Planning.md](./docs/planning/v4%20Planning.md) | Original implementation plan (complete) |
| [v4-RALPH-GOVERNANCE-ENGINE.md](./docs/planning/v4-RALPH-GOVERNANCE-ENGINE.md) | Ralph governance engine specification |
| [v4-KNOWLEDGE-OBJECTS-v1.md](./docs/planning/v4-KNOWLEDGE-OBJECTS-v1.md) | Knowledge Object specification |

### Autonomy Contracts

| Contract | Team | File |
|----------|------|------|
| QA Team | BugFix, CodeQuality, TestFixer | `governance/contracts/qa-team.yaml` |
| Dev Team | FeatureBuilder, TestWriter | `governance/contracts/dev-team.yaml` |
| BugFix (legacy) | Individual agent | `governance/contracts/bugfix.yaml` |

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

**Automated**: For autonomous agents (run_agent.py), session handoffs are generated automatically!

**Manual**: For interactive sessions, use the SessionReflection system:

```python
from orchestration.reflection import SessionResult, SessionStatus, create_session_handoff

result = SessionResult(
    task_id="TASK-123",
    status=SessionStatus.COMPLETED,
    accomplished=["Fixed bug X", "Added test Y"],
    verdict=verdict,
    handoff_notes="Ready for next session"
)

handoff = create_session_handoff("session-id", "agent-name", result)
# → Creates sessions/YYYY-MM-DD-TASK-123.md
# → Updates sessions/latest.md symlink
```

**Handoff includes**:
- What was accomplished
- What was NOT done
- Blockers encountered
- Ralph verdict details
- Files modified
- Test status
- Risk assessment
- Next steps

See [orchestration/handoff_template.md](./orchestration/handoff_template.md) for full format.

---

## Autonomous System (v5.1)

**Status**: 📋 Integration planned, ready for implementation

### Architecture Overview

The fully autonomous system combines two proven components:

```
┌─────────────────────────────────────────────────────────────────┐
│                   autonomous_loop.py (Orchestrator)              │
│                                                                  │
│  while tasks_remaining and iteration < max_global_iterations:   │
│      ┌──────────────────────────────────────────────┐           │
│      │  1. Pull next task from work_queue.json     │           │
│      └──────────────────────────────────────────────┘           │
│                          ▼                                       │
│      ┌──────────────────────────────────────────────┐           │
│      │  2. IterationLoop.run(task, max_iterations)  │           │
│      │                                               │           │
│      │  • Wiggum iteration control                  │           │
│      │  • 15-50 retries per task                    │           │
│      │  • Completion signal detection               │           │
│      │  • Human override on BLOCKED                 │           │
│      │  • State file persistence                    │           │
│      └──────────────────────────────────────────────┘           │
│                          ▼                                       │
│      ┌──────────────────────────────────────────────┐           │
│      │  3. Handle result                            │           │
│      │  • COMPLETED → mark_complete + git_commit   │           │
│      │  • BLOCKED → mark_blocked + continue        │           │
│      │  • ABORTED → mark_blocked + stop loop       │           │
│      └──────────────────────────────────────────────┘           │
│                                                                  │
│  Next task (loop continues)                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Key Capabilities

| Capability | How It Works |
|------------|--------------|
| **Work Discovery** | Pulls tasks from `tasks/work_queue.json` automatically |
| **Multi-Task Execution** | Processes 30-50 tasks per session (vs 10-15 previously) |
| **Smart Retry** | 15-50 retries per task based on agent type (BugFix: 15, Feature: 50) |
| **Completion Detection** | Agent outputs `<promise>TEXT</promise>` when done |
| **Self-Correction** | Fast verification (30s) + lint/type/test auto-fix |
| **Human Escalation** | Only on BLOCKED verdicts (guardrails), presents R/O/A options |
| **Session Persistence** | State files enable automatic resume after interruption |
| **Iteration Audit Trail** | Full history of attempts, verdicts, changes |

### Running the Autonomous Loop

```bash
# Start autonomous loop
python autonomous_loop.py --project karematch --max-iterations 100

# What happens:
# 1. Loads work_queue.json from tasks/
# 2. For each pending task:
#    a. Create agent with task-specific config
#    b. Run IterationLoop with Wiggum control
#    c. Agent retries until success or budget exhausted
#    d. On BLOCKED, ask human for R/O/A decision
#    e. On COMPLETED, commit to git and continue
# 3. Continues until queue empty or max iterations reached
```

### Work Queue Format

```json
{
  "project": "karematch",
  "features": [
    {
      "id": "BUG-001",
      "description": "Fix authentication timeout",
      "file": "src/auth/session.ts",
      "status": "pending",
      "tests": ["tests/auth/session.test.ts"],
      "completion_promise": "BUGFIX_COMPLETE",
      "max_iterations": 15
    }
  ]
}
```

### Session Resume

If interrupted (Ctrl+C, crash, network loss):

```bash
# Simply run the same command again
python autonomous_loop.py --project karematch --max-iterations 100

# System automatically:
# 1. Reads .aibrain/agent-loop.local.md state file
# 2. Resumes from last iteration of in-progress task
# 3. Continues work queue from where it left off
```

### Human Interaction Points

**BLOCKED Verdict (Guardrail Violation)**:
```
🚫 GUARDRAIL VIOLATION DETECTED
============================================================
Pattern: --no-verify detected (bypassing Ralph verification)
File: src/auth/session.ts
============================================================
OPTIONS:
  [R] Revert changes and exit
  [O] Override guardrail and continue
  [A] Abort session immediately
============================================================
Your choice [R/O/A]:
```

**That's it!** No other human interaction required. Agent handles:
- Lint errors → Auto-fix with `npm run lint:fix`
- Type errors → Retry with fix
- Test failures → Analyze and retry
- All other FAIL verdicts → Retry up to budget

### Success Metrics (Post-Integration)

| Metric | Before | After Target |
|--------|--------|--------------|
| Autonomy level | 60% | **85%** |
| Retries per task | 3 (fixed) | **15-50** (agent-specific) |
| Tasks per session | 10-15 | **30-50** |
| Session resume | Manual restart | **Automatic** |
| Completion detection | File changes only | **Promise tags + verification** |
| BLOCKED handling | Skip task | **Human R/O/A** |
| Iteration tracking | None | **Full audit trail** |

---

## Core Concepts

### Dual-Team Architecture (v5)

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Orchestrator                            │
│                                                                 │
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │    QA Team       │           │    Dev Team      │           │
│  │  (L2 autonomy)   │           │  (L1 autonomy)   │           │
│  │                  │           │                  │           │
│  │  - BugFix        │           │  - FeatureBuilder│           │
│  │  - CodeQuality   │           │  - TestWriter    │           │
│  │  - TestFixer     │           │                  │           │
│  └────────┬─────────┘           └────────┬─────────┘           │
│           │                              │                      │
│           ▼                              ▼                      │
│    ┌─────────────┐               ┌─────────────┐               │
│    │ main, fix/* │◄──────────────│  feature/*  │               │
│    │  branches   │  PR + Ralph   │  branches   │               │
│    └─────────────┘   PASS        └─────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Branch Ownership

| Branch Pattern | Owner | Ralph Timing |
|----------------|-------|--------------|
| `main` | Protected | Always |
| `fix/*` | QA Team | Every commit |
| `feature/*` | Dev Team | PR only |

### Governance Hierarchy

```
Kill-Switch (global: OFF/SAFE/NORMAL/PAUSED)
    │
    ▼
Team Contract (qa-team.yaml / dev-team.yaml)
    │
    ▼
Branch Restrictions (main/fix/* vs feature/*)
    │
    ▼
Ralph Verification (per-change: PASS/FAIL/BLOCKED)
    │
    ▼
Human Approval (per-merge)
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
4. **Teams stay in their lanes** - QA on main/fix/*, Dev on feature/*
5. **Humans approve promotion** - Agents execute, humans decide what ships
6. **TDD is primary memory** - Tests encode behavior; if not tested, doesn't exist
7. **Ralph is the law** - PASS/FAIL/BLOCKED verdicts are canonical
8. **Agents iterate until done** - Stop hook enables self-correction loops (v5.1)

---

## Wiggum System (v5.1)

**Status**: ✅ COMPLETE - Fully operational with Claude CLI integration

### What It Does

The Wiggum system provides iteration control for agents, enabling them to iteratively improve their work until Ralph verification passes or a completion signal is detected.

### Two Systems Working Together

| System | Purpose | When It Runs |
|--------|---------|--------------|
| **Ralph Verification** | Code quality gates (PASS/FAIL/BLOCKED) | Every iteration |
| **Wiggum** | Iteration control & self-correction | Session orchestration |

**Key Insight**: Ralph verifies quality, Wiggum manages iterations. They're complementary systems.

**Clear Separation**:
- **Ralph** = Verification (checks code quality, returns PASS/FAIL/BLOCKED)
- **Wiggum** = Iteration control (manages loops, calls Ralph for verification)

### Core Components

#### 1. Completion Signals
Agents signal task completion with `<promise>` tags:

```python
# Agent output when task is complete
"All tests passing, bug fixed. <promise>COMPLETE</promise>"

# System detects exact match
if promise == agent.config.expected_completion_signal:
    allow_exit()
```

**Requirements**:
- REQUIRED for all agents (no optional promises)
- Exact string matching (case-sensitive)
- Must match `expected_completion_signal` in agent config

#### 2. Iteration Budgets

Maximum iterations per agent type (safety mechanism):

| Agent Type | Max Iterations | Rationale |
|------------|---------------|-----------|
| BugFixAgent | 15 | Bugs should be fixable with reasonable attempts |
| CodeQualityAgent | 20 | Quality improvements may need more refinement |
| FeatureBuilder | 50 | Features are complex, need exploration budget |
| TestWriter | 15 | Tests are straightforward to write |

**Defined in contracts**: Each `governance/contracts/*.yaml` file specifies `max_iterations` in limits section.

#### 3. Stop Hook System

Blocks agent exit and decides whether to continue iterating:

```
Agent completes iteration
    │
    ▼
Stop Hook evaluates
    │
    ├─→ Completion signal detected? → ALLOW (exit)
    ├─→ Iteration budget exhausted? → ASK_HUMAN
    ├─→ Ralph PASS? → ALLOW (exit)
    ├─→ Ralph BLOCKED? → ASK_HUMAN (R/O/A prompt)
    ├─→ Ralph FAIL (pre-existing)? → ALLOW (safe to merge)
    └─→ Ralph FAIL (regression)? → BLOCK (continue iteration)
```

**Decision Types**:
- **ALLOW**: Agent can exit (task complete or safe to proceed)
- **BLOCK**: Agent retries (give chance to fix)
- **ASK_HUMAN**: Human approval needed (BLOCKED verdict or budget exhausted)

#### 4. Human Override (BLOCKED Verdicts)

When Ralph detects guardrail violation:

```
🚫 GUARDRAIL VIOLATION DETECTED
============================================================
[Verdict details shown]
============================================================
OPTIONS:
  [R] Revert changes and exit
  [O] Override guardrail and continue
  [A] Abort session immediately
============================================================
Your choice [R/O/A]:
```

**Human Choices**:
- **R (Revert)**: Roll back changes, exit safely
- **O (Override)**: Continue despite violation (with warning)
- **A (Abort)**: Stop session immediately

### Usage Example

```bash
# Wiggum CLI command
aibrain wiggum "Fix bug #123" \
  --agent bugfix \
  --project karematch \
  --max-iterations 15 \
  --promise "COMPLETE"

# Wiggum will:
# 1. Attempt fix (iteration 1)
# 2. Run Ralph verification
# 3. If FAIL → Fix issues (iteration 2)
# 4. Run Ralph again
# 5. Repeat until PASS or max iterations
# 6. Output <promise>COMPLETE</promise>
# 7. Exit
```

### Iteration History Tracking

Every iteration is recorded:

```python
{
  "iteration": 3,
  "timestamp": "2026-01-06T10:30:00",
  "verdict": "FAIL",
  "safe_to_merge": false,
  "regression": true,
  "changes": ["src/auth.ts", "tests/auth.test.ts"]
}
```

**Summary available at end**:
- Total iterations: 3
- Pass count: 0
- Fail count: 3
- Blocked count: 0

### Safety Mechanisms

1. **Iteration budgets** - Prevents infinite loops (15-50 max)
2. **Ralph verification** - Every iteration checked for quality
3. **Human override** - Can revert or override on BLOCKED
4. **Completion signals** - Explicit "done" criteria required
5. **Evidence tracking** - Full iteration history with verdicts

### Implementation Status

**Implementation**: ✅ Complete (all phases delivered)

| Phase | Deliverable | Status |
|-------|-------------|--------|
| Phase 1 | Completion signals (`<promise>` tags) | ✅ Complete |
| Phase 2 | Iteration budgets (contracts updated) | ✅ Complete |
| Phase 3 | Stop hook system | ✅ Complete |
| Phase 4 | State file format (Markdown + YAML) | ✅ Complete |
| Phase 5 | CLI `aibrain wiggum` command | ✅ Complete |
| Bonus | Claude CLI integration | ✅ Complete |

**References**:
- [Implementation Plan](/.claude/plans/jaunty-humming-hartmanis.md) - Full 5-phase plan
- [RALPH-COMPARISON.md](./RALPH-COMPARISON.md) - Detailed comparison of Ralph vs Wiggum
- [Session Handoff](./sessions/2026-01-06-ralph-wiggum-integration.md) - Planning session context

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

## What Teams Can/Cannot Do

### QA Team (BugFix, CodeQuality, TestFixer)

**Branches**: `main`, `fix/*`

**Allowed**:
- Read files, write files (existing only)
- Run tests, run Ralph (every commit)
- Create fix branches, commit changes
- Auto-fix lint/type issues

**Forbidden**:
- Modify migrations
- Modify CI config
- Push to main directly
- Deploy anything
- Create new files (features)
- Change behavior (test count stays same)
- **Use `--no-verify` flag** (NEVER bypass Ralph)

**Limits**:
- Max 100 lines added
- Max 5 files changed
- Must halt on Ralph BLOCKED

---

### Dev Team (FeatureBuilder, TestWriter)

**Branches**: `feature/*` ONLY

**Allowed**:
- Read files, write files, create files
- Run tests, run Ralph (PR only)
- Create feature branches
- Build new functionality
- Write new tests

**Forbidden**:
- Push to main or fix/* branches
- Modify migrations (requires approval)
- Modify CI config
- Deploy anything
- Delete existing tests
- **Use `--no-verify` flag** (NEVER bypass Ralph)

**Requires Approval**:
- New dependencies
- New API endpoints
- Schema changes
- External API integrations

**Limits**:
- Max 500 lines added
- Max 20 files changed
- Must halt on approval_required

---

## CRITICAL: Git Commit Rules

**NEVER use `--no-verify` or `-n` flags when committing.**

The pre-commit hook runs Ralph verification. Bypassing it:
1. Violates governance policy
2. Will be caught by CI anyway (wasted effort)
3. May result in session termination

If a commit is blocked by Ralph:
1. **Fix the issue** - don't bypass
2. If tests fail, fix the code
3. If guardrails trigger, remove the violation
4. If lint fails, run the linter fix

```bash
# CORRECT
git commit -m "Fix bug"

# FORBIDDEN - NEVER DO THIS
git commit --no-verify -m "Fix bug"
git commit -n -m "Fix bug"
```

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

### v5 Implementation (Current)

1. [x] Create v5 Planning document
2. [x] Create QA Team contract (qa-team.yaml)
3. [x] Create Dev Team contract (dev-team.yaml)
4. [x] Update STATE.md with v5 info
5. [x] Update CLAUDE.md with Dual-Team docs
6. [ ] Create session handoff
7. [ ] Begin Dev Team work on `feature/matching-algorithm`

### QA Team Queue (Parallel)

- [ ] Fix 72 test failures
- [ ] Process VERIFIED-BUGS.md (10 bugs)
- [ ] Console.error cleanup (4 items)

### Dev Team Queue (Parallel)

- [ ] P0: Matching algorithm (`feature/matching-algorithm`)
- [ ] P1: Admin dashboard (`feature/admin-dashboard`)
- [ ] P1: Credentialing APIs (`feature/credentialing-api`)
- [ ] P2: Email notifications (`feature/email-notifications`)