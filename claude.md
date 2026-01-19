# AI Orchestrator (AI Brain v5)

## What This Is

AI Orchestrator is an autonomous multi-agent system for governed code quality improvement, feature development, AND safe deployments. It deploys **three specialized teams** of AI agents:

| Team | Mission | Autonomy |
|------|---------|----------|
| **QA Team** | Maintain code quality on stable code | L2 (higher) |
| **Dev Team** | Build new features in isolation | L1 (stricter) |
| **Operator Team** | Deploy applications and migrations safely | L0.5 (strictest) |

### Core Principles

- **Evidence-based completion** - No task marked done without proof (tests pass, Ralph verifies)
- **Human-in-the-loop approval** - Agents execute, humans approve what ships
- **Institutional memory** - Knowledge Objects capture learning that survives sessions
- **Explicit governance** - Autonomy contracts define what agents can/cannot do
- **Team isolation** - QA and Dev work on separate branches, merge at defined points

## Repository Location

```
/Users/tmac/1_REPOS/AI_Orchestrator   # This repo (execution engine: agents, ralph, orchestration)
/Users/tmac/1_REPOS/karematch         # Target app (L2 autonomy)
/Users/tmac/1_REPOS/credentialmate    # Target app (L1 autonomy, HIPAA)
```

## Knowledge Vault Location

**Vault Path**: `/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/`

**When to Consult**: Historical context, strategic planning, governance documentation, cross-project learnings

**How to Access**:
```python
from agents.core.context import get_vault_path, detect_context
vault_path = get_vault_path(detect_context())
```

**When NOT to Use**: Runtime execution, current state (use STATE.md), governance contracts (use `governance/contracts/*.yaml`)

## Current Status

**Version**: v6.0 - Cross-Repo Memory Continuity (91% autonomy achieved)

**Implemented Systems**:
- ✅ v5.1 - Wiggum iteration control + autonomous loop integration
- ✅ v5.2 - Automated bug discovery with turborepo support
- ✅ v5.3 - Knowledge Object enhancements (cache, metrics, CLI)
- ✅ v6.0 - Cross-repo memory continuity + 9-step startup protocol

**Key Metrics**:
- Autonomy: 91% (up from 60%)
- Tasks per session: 30-50 (target: 100+ with v6.0 optimizations)
- KO query speed: 457x faster (caching)
- Retry budget: 15-50 per task (agent-specific)

### Key Documents

| Document | Purpose |
|----------|---------|
| [docs/03-knowledge/README.md](./docs/03-knowledge/README.md) | Complete KO system documentation |
| [STATE.md](./STATE.md) | Current implementation status |
| [CATALOG.md](./CATALOG.md) | Documentation index |

### Autonomy Contracts

**See**: `governance/contracts/` for complete team permissions

| Contract | Team | File |
|----------|------|------|
| QA Team | BugFix, CodeQuality, TestFixer | `governance/contracts/qa-team.yaml` |
| Dev Team | FeatureBuilder, TestWriter | `governance/contracts/dev-team.yaml` |
| Operator Team | Deployment, Migration, Rollback | `governance/contracts/operator-team.yaml` |

---

## Agent Memory Protocol

**CRITICAL**: Sessions are stateless. All memory is externalized. The 9-step startup protocol loads context automatically.

### Memory Files

| File | Purpose | When to Update |
|------|---------|----------------|
| [CATALOG.md](./CATALOG.md) | Master documentation index | When adding new doc categories |
| [STATE.md](./STATE.md) | Current build state, what's done/blocked/next | Every significant change |
| [sessions/latest.md](./sessions/latest.md) | Most recent session handoff (if present) | End of every session |

### Automatic Checkpoint System

**IMPORTANT**: A hook runs after every Write/Edit operation and tracks tool call count.

**When you see the CHECKPOINT REMINDER banner:**
1. **STOP** current work
2. **UPDATE** STATE.md or relevant session file
3. **RESET** counter: `echo 0 > .claude/hooks/.checkpoint_counter`
4. **CONTINUE** work

**Why this matters:** If session crashes, only work since last checkpoint is lost.

### Session Documentation Protocol

When conducting research or multi-step exploration:

1. **Create session file EARLY** (not at the end):
   ```
   sessions/{repo}/active/{YYYYMMDD-HHMM}-{topic}.md
   ```
   - Repo options: `karematch`, `credentialmate`, `ai-orchestrator`, `cross-repo`
   - Use the template at `sessions/templates/session-template.md`

2. **Write findings AS YOU GO**:
   - Don't print walls of research text to terminal
   - Write directly to the session file
   - Update as you discover new information

3. **At session end**: Session file should already be complete
   - If resuming later: leave in `active/`
   - If complete: move to `archive/` (or auto-archive after 30 days)

---

## Autonomous System

### Running the Autonomous Loop

```bash
# Start autonomous loop
python autonomous_loop.py --project karematch --max-iterations 100

# What happens:
# 1. Loads tasks/work_queue_{project}.json
# 2. For each pending task:
#    a. Run IterationLoop with Wiggum control (15-50 retries)
#    b. On BLOCKED, ask human for R/O/A decision (unless --non-interactive)
#    c. On COMPLETED, commit to git and continue
# 3. Continues until queue empty or max iterations reached
```

**Note**: Human interaction can still be required (governance gates, advisor escalations, guardrail decisions).
Use `--non-interactive` to auto-revert guardrail violations and auto-approve required prompts.

### Session Resume

If interrupted (Ctrl+C, crash):

```bash
# Simply run the same command again - automatically resumes
python autonomous_loop.py --project karematch --max-iterations 100
```

System reads `.aibrain/agent-loop.local.md` state file and resumes from last iteration.

---

## Core Concepts

### Dual-Team Architecture

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
8. **Agents iterate until done** - Stop hook enables self-correction loops

---

## Wiggum System

**Status**: ✅ Production Ready

**Purpose**: Iteration control for agents, enabling them to iteratively improve work until Ralph verification passes or a completion signal is detected.

**Documentation**: See `docs/14-orchestration/wiggum.md` for complete details

### Core Components

1. **Completion Signals**: Agents signal task completion with `<promise>` tags
   ```python
   "All tests passing, bug fixed. <promise>COMPLETE</promise>"
   ```

2. **Iteration Budgets**: BugFix (15), CodeQuality (20), FeatureBuilder (50), TestWriter (15)

3. **Stop Hook System**: Blocks agent exit, decides whether to continue iterating based on Ralph verdict

**Auto-Detection**: System auto-detects task type and applies appropriate completion signal (80% reduction in manual signal specification)

---

## Knowledge Object System

**Status**: ✅ Production Ready

**Purpose**: Institutional memory that survives sessions, captures learning from agent work

**Documentation**: See `knowledge/README.md` for complete details

### Key Features

- **In-Memory Caching**: 457x speedup for repeated queries
- **Tag Index**: O(1) hash lookups
- **Effectiveness Metrics**: Tracks consultations, success rates
- **Auto-Approval**: 70% of KOs auto-approved (high-confidence only)

### Quick Reference

```bash
aibrain ko list                   # List all approved KOs
aibrain ko search --tags X,Y      # Search by tags (OR semantics)
aibrain ko pending                # List drafts awaiting approval
```

---

## Automated Bug Discovery

**Status**: ✅ Production Ready

**Purpose**: Scans codebases for bugs across 4 sources (ESLint, TypeScript, Vitest, Guardrails) and generates prioritized work queue tasks

**Documentation**: See `docs/16-testing/bug-discovery.md` for complete details

### Key Features

- **Baseline Tracking**: Detects new regressions vs. pre-existing issues
- **Impact-Based Priority**: P0 (blocks users), P1 (degrades UX), P2 (tech debt)
- **File Grouping**: Groups bugs in same file (reduces task count 50-70%)
- **Turborepo Support**: Auto-detects and handles monorepo structure

```bash
aibrain discover-bugs --project karematch  # Scan and generate tasks
```

---

## Team Permissions

**See governance contracts for complete details**: `governance/contracts/*.yaml`

Quick summary:
- **QA Team**: Fix bugs on main/fix/* branches, Ralph verification every commit, max 100 lines/5 files
- **Dev Team**: Build features on feature/* branches, Ralph verification on PR only, max 500 lines/20 files
- **Operator Team**: Deploy to dev/staging/prod with environment-specific gates, production requires human approval

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
