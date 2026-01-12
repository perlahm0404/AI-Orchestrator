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

**Context**: This is a CODE REPO. Documentation is in the Obsidian vault.

**Vault Path**: `/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/`

**What's in This Repo**:
- Agent execution code (agents/, ralph/, orchestration/, discovery/, cli/)
- Runtime configuration (governance/contracts/, adapters/)
- Work queues and state (tasks/, .aibrain/)
- Knowledge Objects for runtime (knowledge/approved/)
- Tests (tests/)

**What's in the Vault**:
- Architecture documentation
- Session handoffs (historical)
- Strategic planning (DECISIONS.md, ROADMAP.md, etc.)
- Learning & analysis
- Knowledge Objects (reference copies)

### Agent Protocol: When to Consult the Vault

**If you are an AI agent, consult the vault when you need:**

1. **Historical Context**
   - Previous session outcomes → `Sessions/`
   - Past decisions and rationale → `DECISIONS.md`, `Plans/`
   - Architecture evolution → `Architecture/`

2. **Strategic Planning**
   - System roadmap → `ROADMAP.md`
   - Feature plans → `Plans/`
   - Architecture Decision Records → `Decisions/`

3. **Governance & Policy**
   - Team contracts explained → `Governance/`
   - Operational guides → `Operations/`
   - Troubleshooting guides → `Operations/`

4. **Cross-Project Learning**
   - Knowledge Objects (reference) → `Knowledge-Objects/`
   - Best practices → Vault `05-Knowledge-Base/`
   - Other project learnings → Vault `02-KareMatch/`, `03-CredentialMate/`

**How to Access Vault Files (on Mac)**:
```python
# Use the context detection system
from agents.core.context import get_vault_path, detect_context

context = detect_context()
vault_path = get_vault_path(context)
# Returns: /Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/

# Then read files normally
import os
sessions_dir = os.path.join(vault_path, "Sessions")
decisions_file = os.path.join(vault_path, "DECISIONS.md")
```

**When NOT to Use the Vault**:
- Runtime execution (use repo files)
- Governance contracts (use `governance/contracts/*.yaml`)
- Knowledge Object queries (use `knowledge/service.py`)
- Current state (use `STATE.md` in repo)

**Note**: On iOS, vault access requires Working Copy app or manual Obsidian viewing.

## Current Status

**Version**: v5.2 - Production Ready (89% autonomy achieved)

**Implemented Systems**:
- ✅ v5.1 - Wiggum iteration control + autonomous loop integration
- ✅ v5.2 - Automated bug discovery with turborepo support
- ✅ v5.3 - Knowledge Object enhancements (cache, metrics, CLI)

**Key Metrics**:
- Autonomy: 89% (up from 60%)
- Tasks per session: 30-50 (up from 10-15)
- KO query speed: 457x faster (caching)
- Retry budget: 15-50 per task (agent-specific)

### Key Documents

| Document | Purpose |
|----------|---------|
| [docs/03-knowledge/README.md](./docs/03-knowledge/README.md) | Complete KO system documentation |
| [STATE.md](./STATE.md) | Current implementation status |
| [DECISIONS.md](./DECISIONS.md) | Build decisions with rationale |

### Autonomy Contracts

| Contract | Team | File |
|----------|------|------|
| QA Team | BugFix, CodeQuality, TestFixer | `docs/02-governance/contracts/qa-team.yaml` |
| Dev Team | FeatureBuilder, TestWriter | `docs/02-governance/contracts/dev-team.yaml` |
| Operator Team | Deployment, Migration, Rollback | `docs/02-governance/contracts/operator-team.yaml` |

---

## Agent Memory Protocol

**CRITICAL**: Sessions are stateless. All memory is externalized. Read these files on every session start.

### Session Startup Checklist

```
1. Read CATALOG.md               → How is documentation organized?
2. Read USER-PREFERENCES.md      → How does tmac like to work?
3. Read STATE.md                 → What's the current state?
4. Read DECISIONS.md             → What decisions were already made?
5. Read sessions/latest.md (if present) → What happened last session?
6. Proceed with work
7. Before ending: Update STATE.md and create session handoff
```

### Memory Files

| File | Purpose | When to Update |
|------|---------|----------------|
| [CATALOG.md](./CATALOG.md) | Master documentation index, quick navigation | When adding new doc categories |
| [USER-PREFERENCES.md](./USER-PREFERENCES.md) | tmac's working preferences, communication style | When patterns change |
| [STATE.md](./STATE.md) | Current build state, what's done/blocked/next | Every significant change |
| [DECISIONS.md](./DECISIONS.md) | Build-time decisions with rationale | When making implementation choices |
| [sessions/latest.md](./sessions/latest.md) | Most recent session handoff (if present) | End of every session |

### Session Handoff Protocol

**Automated**: Not wired for `autonomous_loop.py` today. Use SessionReflection or add a hook if you want automatic handoffs.

**Manual**: For interactive sessions, use the SessionReflection system (see `orchestration/reflection.py`).

**Handoff includes**: What was accomplished, what was NOT done, blockers, Ralph verdict details, files modified, test status, risk assessment, next steps.

See [orchestration/handoff_template.md](./orchestration/handoff_template.md) for full format.

---

## Autonomous System

### Running the Autonomous Loop

```bash
# Start autonomous loop
python autonomous_loop.py --project karematch --max-iterations 100

# What happens:
# 1. Loads tasks/work_queue_{project}.json (or tasks/work_queue_{project}_features.json)
# 2. For each pending task:
#    a. Run IterationLoop with Wiggum control (15-50 retries)
#    b. On BLOCKED, ask human for R/O/A decision (unless --non-interactive)
#    c. On COMPLETED, commit to git and continue
# 3. Continues until queue empty or max iterations reached
```

**Note**: Human interaction can still be required (governance gates, advisor escalations, guardrail decisions).
Use `--non-interactive` to auto-revert guardrail violations and auto-approve required prompts.

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

If interrupted (Ctrl+C, crash):

```bash
# Simply run the same command again - automatically resumes
python autonomous_loop.py --project karematch --max-iterations 100
```

System reads `.aibrain/agent-loop.local.md` state file and resumes from last iteration.

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

**That's it!** No other human interaction required. Agent auto-handles lint/type/test failures.

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

The Wiggum system provides iteration control for agents, enabling them to iteratively improve their work until Ralph verification passes or a completion signal is detected.

### Two Systems Working Together

| System | Purpose | When It Runs |
|--------|---------|--------------|
| **Ralph Verification** | Code quality gates (PASS/FAIL/BLOCKED) | Every iteration |
| **Wiggum** | Iteration control & self-correction | Session orchestration |

**Clear Separation**:
- **Ralph** = Verification (checks code quality, returns PASS/FAIL/BLOCKED)
- **Wiggum** = Iteration control (manages loops, calls Ralph for verification)

### Core Components

#### 1. Completion Signals
Agents signal task completion with `<promise>` tags:

```python
# Agent output when task is complete
"All tests passing, bug fixed. <promise>COMPLETE</promise>"
```

**Requirements**: REQUIRED for all agents, exact string matching (case-sensitive).

#### 2. Iteration Budgets

| Agent Type | Max Iterations |
|------------|---------------|
| BugFixAgent | 15 |
| CodeQualityAgent | 20 |
| FeatureBuilder | 50 |
| TestWriter | 15 |

#### 3. Stop Hook System

Blocks agent exit and decides whether to continue iterating:

```
Agent completes iteration → Stop Hook evaluates:
  ├─→ Completion signal detected? → ALLOW (exit)
  ├─→ Iteration budget exhausted? → ASK_HUMAN
  ├─→ Ralph PASS? → ALLOW (exit)
  ├─→ Ralph BLOCKED? → ASK_HUMAN (R/O/A prompt)
  ├─→ Ralph FAIL (pre-existing)? → ALLOW (safe to merge)
  └─→ Ralph FAIL (regression)? → BLOCK (continue iteration)
```

### Completion Signal Templates (Auto-Detection)

System auto-detects task type from description and applies appropriate signal:

| Task Type | Completion Signal | Keywords |
|-----------|-------------------|----------|
| bugfix | `BUGFIX_COMPLETE` | bug, fix, error, issue |
| codequality | `CODEQUALITY_COMPLETE` | quality, lint, clean |
| feature | `FEATURE_COMPLETE` | feature, add, implement |
| test | `TESTS_COMPLETE` | test, spec, coverage |
| refactor | `REFACTOR_COMPLETE` | refactor, restructure |

**Impact**: 80% reduction in manual signal specification.

---

## Knowledge Object System

**Status**: ✅ Production Ready

**Comprehensive Documentation**: See [knowledge/README.md](./knowledge/README.md)

### Key Features

1. **In-Memory Caching**: 457x speedup for repeated queries (0.44ms → 0.001ms)
2. **Tag Index**: O(1) hash lookups instead of O(n) scans
3. **Effectiveness Metrics**: Tracks consultations, success rates, impact scores
4. **Configurable Auto-Approval**: Project-specific thresholds
5. **Tag Aliases**: Shortcuts like `ts` → `typescript`, `js` → `javascript`

### CLI Commands

```bash
aibrain ko list                   # List all approved KOs
aibrain ko show KO-ID             # Show full details
aibrain ko search --tags X,Y      # Search by tags (OR semantics)
aibrain ko pending                # List drafts awaiting approval
aibrain ko approve KO-ID          # Approve a draft KO
aibrain ko reject KO-ID "reason"  # Reject a draft KO
aibrain ko metrics [KO-ID]        # View effectiveness metrics
```

### Tag Matching Semantics

**IMPORTANT**: Uses **OR semantics** - returns KOs with ANY matching tag (not ALL).

```bash
aibrain ko search --tags "typescript,strict-mode"
# Returns KOs with EITHER typescript OR strict-mode (or both)
```

### Auto-Approval

KO system auto-approves drafts when:
- Ralph verdict = PASS
- Iterations = 2-10 (configurable)
- Auto-approval enabled in config

**Impact**: 70% of KOs auto-approved (high-confidence only).

---

## Automated Bug Discovery System

**Status**: ✅ Production Ready

**Autonomy Impact**: +2% (87% → 89%)

### What It Does

Scans codebases for bugs across 4 sources and generates prioritized work queue tasks:

| Source | What It Detects |
|--------|-----------------|
| **ESLint** | Unused imports, console logs, security issues |
| **TypeScript** | Type errors, missing annotations |
| **Vitest** | Test failures |
| **Guardrails** | @ts-ignore, eslint-disable, .only(), .skip() |

**Turborepo Support**: Auto-detects `turbo.json` and uses direct tool invocation (bypasses argument passing issues).

### CLI Usage

```bash
# First run: Create baseline
aibrain discover-bugs --project karematch

# Subsequent runs: Detect new bugs
aibrain discover-bugs --project karematch

# Dry run (preview only)
aibrain discover-bugs --project karematch --dry-run

# Scan specific sources
aibrain discover-bugs --project karematch --sources lint,typecheck
```

### Key Features

1. **Baseline Tracking**: First run creates fingerprint snapshot, subsequent runs detect new regressions
2. **Impact-Based Priority**: P0 (blocks users), P1 (degrades UX), P2 (tech debt)
3. **File Grouping**: Groups all bugs in same file into 1 task (reduces 50-70%)
4. **Agent Type Inference**: Auto-selects appropriate agent based on bug type

### Example Output

```
📋 Task Summary:
  🆕 [P0] TEST-LOGIN-001: Fix 2 test error(s) (NEW REGRESSION)
  🆕 [P0] TYPE-SESSION-002: Fix 1 typecheck error(s) (NEW REGRESSION)
     [P1] LINT-MATCHING-003: Fix 3 lint error(s) (baseline)
     [P2] GUARD-CONFIG-007: Fix 2 guardrails error(s) (baseline)
```

---

## Directory Structure

```
ai-orchestrator/
├── agents/              # Agent implementations (bugfix, codequality, etc.)
├── ralph/               # Verification engine (PASS/FAIL/BLOCKED)
├── docs/                # Priority-based documentation (01-10 daily, 10-19 weekly, 20-29 monthly)
│   ├── 01-quick-start/      # ⭐ Onboarding, getting started
│   ├── 02-governance/       # ⭐ Contracts, compliance, team policies
│   ├── 03-knowledge/        # ⭐ Knowledge Objects (approved/, drafts/, config/)
│   ├── 04-operations-daily/ # ⭐ Day-to-day operations, deployments
│   ├── 10-architecture/     # 📚 System design, agent architecture
│   ├── 11-plans/            # 📚 Strategic plans, PRDs, roadmaps
│   ├── 12-decisions/        # 📚 ADRs (Architecture Decision Records)
│   ├── 13-tasks/            # 📚 Task system, work queues
│   ├── 14-orchestration/    # 📚 Wiggum, Ralph, iteration control
│   ├── 15-agents/           # 📚 Agent implementation guides
│   ├── 16-testing/          # 📚 Test documentation, baselines
│   ├── 17-troubleshooting/  # 📚 Debug guides, issue resolution
│   ├── 20-analysis/         # 🔬 Cost analysis, token analysis
│   ├── 21-integration/      # 🔬 Claude Code, external tools
│   ├── 22-reports/          # 🔬 Generated reports, metrics
│   ├── 30-karematch/        # 🎯 KareMatch adapter documentation
│   ├── 31-credentialmate/   # 🎯 CredentialMate adapter documentation
│   ├── 90-archive-index/    # 📦 Pointer to archive/ location
│   └── 99-deprecated/       # 📦 Deprecation notices, sunset guides
├── orchestration/       # Session lifecycle, iteration control
├── discovery/           # Bug discovery system
│   ├── parsers/        # ESLint, TypeScript, Vitest, Guardrails
│   ├── scanner.py      # Orchestrates all scanners
│   ├── baseline.py     # Baseline tracking
│   └── task_generator.py
├── adapters/            # Project-specific configs (karematch, credentialmate)
├── cli/commands/        # aibrain commands
├── archive/             # Historical documentation (YYYY-MM/)
└── tests/
```

---

## CLI Commands

```bash
# Status
aibrain status                    # Overall system status
aibrain status TASK-123           # Specific task status

# Approvals
aibrain approve TASK-123          # Approve fix, merge PR
aibrain reject TASK-123 "reason"  # Reject fix, close PR

# Knowledge Objects
aibrain ko list                   # List all approved KOs
aibrain ko show KO-ID             # Show full KO details
aibrain ko search --tags X,Y      # Search by tags (OR semantics)
aibrain ko pending                # List pending KOs
aibrain ko approve KO-ID          # Approve Knowledge Object
aibrain ko metrics [KO-ID]        # View effectiveness metrics

# Bug Discovery
aibrain discover-bugs --project X # Scan for bugs and generate tasks

# Autonomous Loop
python autonomous_loop.py --project X --max-iterations 100

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

### Operator Team (Deployment, Migration, Rollback)

**Branches**: `deploy/*`, `migration/*`, `ops/*`

**Environments**: Development, Staging, Production

**Environment Gates**:
- **Development**: Auto-deploy, auto-rollback (full autonomy)
- **Staging**: First-time approval required, then auto-deploy with auto-rollback
- **Production**: ALWAYS requires human approval, manual rollback only

**Allowed**:
- Build application
- Run pre-deployment validation (tests, migrations, SQL/S3 safety)
- Deploy to dev/staging/production (with environment gates)
- Execute database migrations (with validation)
- Rollback deployments (auto for dev/staging, manual for production)
- Monitor deployment health
- Create deployment reports

**Forbidden (CRITICAL - Irreversible Operations)**:
- **DROP DATABASE** - Causes irreversible data loss
- **DROP TABLE** - Causes irreversible data loss
- **TRUNCATE TABLE** - Causes irreversible data deletion
- **DELETE without WHERE** - Deletes all rows irreversibly
- **DELETE S3 BUCKET** - Irreversible bucket deletion
- **DELETE ALL S3 OBJECTS** - Bulk deletion without recovery
- SSH to production servers
- Direct production database modifications
- Bypass deployment pipeline

**Requires Approval**:
- **All production deployments** (ALWAYS)
- **All production migrations** (ALWAYS)
- **All production rollbacks** (manual approval required)
- First-time staging deployment
- AWS resource provisioning (requires business case)

**AWS Provisioning Business Case Requirements**:
When provisioning new AWS resources, must provide:
- **Justification**: Why is this resource needed?
- **Cost estimate**: Monthly/annual cost projection
- **Alternatives considered**: What other options were evaluated?
- **Risk assessment**: Security and operational risks
- **Human approval**: Explicit sign-off required

**SQL Safety Validation** (Automatic):
All migrations scanned for:
- DROP DATABASE, DROP TABLE, TRUNCATE
- DELETE without WHERE clause
- UPDATE without WHERE clause
- Missing downgrade() method (production only)

**S3 Safety Validation** (Automatic):
All code scanned for:
- Bucket deletion operations
- Bulk object deletion
- Irreversible S3 operations

**Migration Requirements**:
- Must have `upgrade()` method
- Must have `downgrade()` method (production REQUIRED)
- No forbidden SQL patterns in production
- Reversibility validated before execution

**Deployment Workflow**:
1. Pre-deployment validation (tests, migrations, safety checks)
2. Build application
3. Deploy to environment (with gates)
4. Run migrations (if configured)
5. Post-deployment health checks
6. Auto-rollback on failure (dev/staging only)

**Auto-Rollback Triggers** (Dev/Staging Only):
- Deployment failure
- Health check failure
- Error rate spike
- Critical metric degradation

**Production Rollback** (Manual Approval Required):
- Human must approve rollback
- No auto-rollback in production
- Verification required post-rollback

**Limits**:
- Max deployment time: 30 minutes
- Max migration time: 10 minutes
- Max rollback time: 5 minutes
- Max retries: 2
- Must halt on SQL/S3 safety violations

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
