# Architecture Overview

High-level system design for AI Orchestrator.

## System Philosophy

AI Orchestrator is built on three core principles:

1. **Governed Autonomy** - Agents operate autonomously within explicit boundaries
2. **Evidence-Based Execution** - No task marked done without proof (tests pass, Ralph verifies)
3. **Stateless Sessions** - All memory externalized (database, files, Knowledge Objects)

## Multi-Agent Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        AI Orchestrator                               │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │                  Execution Teams                        │        │
│  │                                                         │        │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │        │
│  │  │  QA Team     │  │  Dev Team    │  │ Operator Team│  │        │
│  │  │  (L2)        │  │  (L1)        │  │  (L0.5)      │  │        │
│  │  │              │  │              │  │              │  │        │
│  │  │ - BugFix     │  │ - Feature    │  │ - Deployment │  │        │
│  │  │ - CodeQual.  │  │ - TestWriter │  │ - Migration  │  │        │
│  │  │ - TestFixer  │  │              │  │ - Rollback   │  │        │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │        │
│  │         │                 │                 │           │        │
│  │         ▼                 ▼                 ▼           │        │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │        │
│  │  │ main, fix/*  │  │  feature/*   │  │  deploy/*    │  │        │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │              Advisory & Governance Layer                │        │
│  │                                                         │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │        │
│  │  │   App    │  │  UI/UX   │  │   Data   │  Advisors   │        │
│  │  │ Advisor  │  │ Advisor  │  │ Advisor  │  (Tier 1)   │        │
│  │  └──────────┘  └──────────┘  └──────────┘             │        │
│  │                       ↓                                 │        │
│  │                 ┌─────────────┐                         │        │
│  │                 │ Coordinator │  Orchestrator (Tier 2)  │        │
│  │                 └─────────────┘                         │        │
│  │                       ↓                                 │        │
│  │  ┌──────────┐  ┌──────────┐                            │        │
│  │  │    PM    │  │   CMO    │  Meta-Coordinators         │        │
│  │  │  Agent   │  │  Agent   │  (Governance)              │        │
│  │  └──────────┘  └──────────┘                            │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
│                          ▼                                           │
│                   Ralph + Wiggum                                     │
│              (Verification + Iteration)                              │
└──────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Execution Teams

**QA Team (L2 Autonomy - Higher)**
- **Agents**: BugFix, CodeQuality, TestFixer
- **Branches**: `main`, `fix/*`
- **Purpose**: Maintain code quality on stable code
- **Ralph Timing**: Every commit
- **Can**: Fix bugs, run tests, auto-fix lint/type issues
- **Cannot**: Create new files, change behavior, bypass Ralph

**Dev Team (L1 Autonomy - Stricter)**
- **Agents**: FeatureBuilder, TestWriter
- **Branches**: `feature/*` only
- **Purpose**: Build new features in isolation
- **Ralph Timing**: PR only
- **Can**: Create files, write tests, build features
- **Cannot**: Push to main/fix/*, modify migrations without approval

**Operator Team (L0.5 Autonomy - Strictest)**
- **Agents**: Deployment, Migration, Rollback
- **Branches**: `deploy/*`, `migration/*`
- **Purpose**: Deploy applications and migrations safely
- **Environment Gates**: Dev (auto), Staging (first-time approval), Production (ALWAYS approval)
- **Can**: Build, deploy, run migrations, health checks
- **Cannot**: DROP DATABASE, TRUNCATE, bulk delete S3, bypass pipeline

### 2. Advisory & Governance Layer

**Tier 1: Advisors (User-Invoked)**
- **App Advisor** - Architecture, APIs, patterns
- **UI/UX Advisor** - Components, accessibility, UX
- **Data Advisor** - Schema, migrations, data modeling
- **Output**: ADRs (Architecture Decision Records)
- **Auto-Approve**: Confidence ≥ 85% AND tactical domain AND no ADR conflicts

**Tier 2: Coordinator (Event-Driven)**
- **Purpose**: ADR → Task orchestration
- **Responsibilities**: Parse ADRs, create tasks, manage work queue, track status
- **Output**: Tasks in `work_queue.json`, updates to `PROJECT_HQ.md`

**Tier 3: Meta-Coordinators (Governance)**
- **Product Manager** - Evidence-based prioritization
- **CMO Agent** - GTM strategy & messaging alignment
- **Decision**: APPROVED / BLOCKED / MODIFIED

### 3. Verification & Iteration

**Ralph (Verification Engine)**
- **Purpose**: Quality gates on every change
- **Verdicts**: PASS / FAIL / BLOCKED
- **Runs**: Lint, type check, tests, guardrails
- **Location**: `ralph/engine.py`

**Wiggum (Iteration Control)**
- **Purpose**: Self-correction loops
- **Detects**: Completion signals (`<promise>COMPLETE</promise>`)
- **Manages**: Retry budgets (15-50 per task)
- **Prevents**: Infinite loops
- **Location**: `orchestration/iteration_loop.py`

### 4. Knowledge Objects

**Purpose**: Persistent learning system

**Structure**:
- `knowledge/approved/` - Vetted learnings (agents query at runtime)
- `knowledge/drafts/` - Pending approval
- `knowledge/service.py` - Query interface

**Auto-Approval**: Ralph PASS + iterations 2-10 + project thresholds

**Cache**: In-memory cache (457x speedup: 0.44ms → 0.001ms)

## Data Flow

### Bug Discovery → Fix → Verify Flow

```
1. Bug Discovery
   ├─ ESLint scan
   ├─ TypeScript check
   ├─ Vitest run
   └─ Guardrails scan
        ↓
2. Task Queue (data/bugs_to_fix.json)
   ├─ Group by file
   ├─ Prioritize (P0 > P1 > P2)
   └─ Infer agent type
        ↓
3. Agent Execution
   ├─ BugFixAgent loads task
   ├─ Consult Knowledge Objects
   ├─ Fix code
   └─ Run tests
        ↓
4. Ralph Verification
   ├─ Run lint/type/test/guardrails
   ├─ Return PASS / FAIL / BLOCKED
   └─ Log verdict (logs/verdicts/)
        ↓
5. Wiggum Iteration Control
   ├─ PASS → commit, continue
   ├─ FAIL → retry (max iterations)
   └─ BLOCKED → ask human (R/O/A)
        ↓
6. Completion
   ├─ Mark task COMPLETED
   ├─ Update state
   └─ Create session handoff
```

### ADR → Task Execution Flow

```
1. User invokes Advisor
   @app-advisor How should we structure multi-tenancy?
        ↓
2. Advisor analyzes
   ├─ Check existing ADRs
   ├─ Calculate confidence (85%+?)
   ├─ Determine domain (strategic vs tactical)
   └─ Decision: Auto-approve or Escalate
        ↓
3. ADR Created
   AI-Team-Plans/decisions/ADR-XXX.md
        ↓
4. Coordinator parses ADR
   ├─ Break into tasks
   ├─ Add to work_queue.json
   └─ Update PROJECT_HQ.md
        ↓
5. Task assigned to Builder
   ├─ FeatureBuilder → feature/*
   ├─ BugFixAgent → fix/*
   └─ Deployment → deploy/*
        ↓
6. Builder executes
   [Same as Bug Discovery flow from step 3]
```

## Branch Strategy

| Branch | Owner | Ralph | Can Push | Can Merge |
|--------|-------|-------|----------|-----------|
| `main` | Protected | Always | No one | PR only |
| `fix/*` | QA Team | Every commit | Agents | PR → main |
| `feature/*` | Dev Team | PR only | Agents | PR → main |
| `deploy/*` | Operators | Validation | Agents | Auto-deploy |

## Autonomy Levels

| Level | Team | Description |
|-------|------|-------------|
| **L2** | QA Team | Higher autonomy - fix bugs, auto-approve small changes |
| **L1** | Dev Team | Stricter - build features but require approval for migrations/APIs |
| **L0.5** | Operators | Strictest - production always requires human approval |

## External Dependencies

### Obsidian Vault (Knowledge Documentation)
- **Path**: `/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/`
- **Contains**: Detailed docs, sessions, plans, ADRs
- **Access**: Via `agents.core.context.get_vault_path()`
- **Sync**: iCloud (Mac ↔ iOS)

### Target Applications
- **KareMatch**: `/Users/tmac/1_REPOS/karematch` (L2)
- **CredentialMate**: `/Users/tmac/1_REPOS/credentialmate` (L1)

## For More Details

- **Agent Details**: See [AGENTS.md](AGENTS.md)
- **Governance Details**: See [GOVERNANCE.md](GOVERNANCE.md)
- **Vault Access**: See [VAULT-REFERENCE.md](VAULT-REFERENCE.md)
- **Complete Docs**: See vault or [CLAUDE.md](../CLAUDE.md)
