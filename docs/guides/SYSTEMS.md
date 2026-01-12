# Core Systems Documentation

**Version**: v5.2 - Production Ready
**Last Updated**: 2026-01-11
**Purpose**: Complete reference for Wiggum, Ralph, Knowledge Objects, and Bug Discovery systems

---

## System Overview

| System | Status | Purpose | Impact |
|--------|--------|---------|--------|
| **Wiggum** | ✅ Production | Iteration control & self-correction | 89% autonomy |
| **Ralph** | ✅ Production | Code quality verification (PASS/FAIL/BLOCKED) | Zero regressions |
| **Knowledge Objects** | ✅ Production | Institutional memory across sessions | 457x speedup |
| **Bug Discovery** | ✅ Production | Automated bug scanning & task generation | +2% autonomy |

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

---

### Core Components

#### 1. Completion Signals

Agents signal task completion with `<promise>` tags:

```python
# Agent output when task is complete
"All tests passing, bug fixed. <promise>COMPLETE</promise>"
```

**Requirements**: REQUIRED for all agents, exact string matching (case-sensitive).

**Completion Signal Templates** (Auto-Detection):

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

#### 2. Iteration Budgets

| Agent Type | Max Iterations | Purpose |
|------------|---------------|---------|
| BugFixAgent | 15 | Bug fixes |
| CodeQualityAgent | 20 | Code quality improvements |
| FeatureBuilder | 50 | Feature development |
| TestWriter | 15 | Test writing |
| TestFixer | 15 | Test fixes |

**Budget Exhaustion**:
- Agent stops iterating
- Human prompt: Continue, Abort, or Increase budget?

---

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

**Key Insight**: Pre-existing failures are OK (don't block). New regressions trigger iteration.

---

### Wiggum Configuration

Located in `orchestration/iteration_loop.py`:

```python
from orchestration.iteration_loop import IterationLoop, IterationConfig

config = IterationConfig(
    max_iterations=15,
    expected_completion_signal="BUGFIX_COMPLETE",
    stop_on_ralph_pass=True,
    stop_on_ralph_blocked=True,  # Escalate to human
    allow_preexisting_failures=True,  # Don't block on old failures
)

loop = IterationLoop(config)
result = loop.run(agent, task_description)
```

**Options**:
- `max_iterations`: Max retry count
- `expected_completion_signal`: What `<promise>` tag to detect
- `stop_on_ralph_pass`: Exit when Ralph returns PASS
- `stop_on_ralph_blocked`: Escalate when Ralph returns BLOCKED
- `allow_preexisting_failures`: Don't block on pre-existing test failures

---

### Human Interaction (BLOCKED Verdicts)

When Ralph returns BLOCKED (e.g., guardrail violation):

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

**R (Revert)**: Undo changes, exit loop
**O (Override)**: Continue despite violation (logged)
**A (Abort)**: Terminate session immediately

---

### Wiggum Metrics

**Autonomy Impact**: 89% (up from 60%)
**Tasks per session**: 30-50 (up from 10-15)
**Average iterations per task**: 3-7
**Success rate**: 92% (tasks completed without human intervention)

---

## Ralph Verification System

**Status**: ✅ Production Ready

Ralph is the code quality verification engine that returns PASS/FAIL/BLOCKED verdicts.

### Verification Types

| Check | What It Does | Verdict |
|-------|--------------|---------|
| **Lint** | ESLint, Prettier | FAIL if errors, PASS if clean |
| **Type** | TypeScript type checking | FAIL if errors, PASS if clean |
| **Test** | Vitest, Playwright | FAIL if failures, PASS if all pass |
| **Guardrails** | Detects forbidden patterns | BLOCKED if violation |

---

### Ralph Verdicts

#### PASS

**Meaning**: Code meets all quality gates.

**What Happens**:
- Wiggum allows agent to exit
- Task marked COMPLETED
- PR ready for human approval

**Example**:
```
✅ RALPH VERDICT: PASS
- Lint: clean
- Types: no errors
- Tests: 15/15 passing
- Guardrails: none detected
```

---

#### FAIL

**Meaning**: Code has quality issues but no guardrail violations.

**What Happens**:
- If **new regression**: Wiggum blocks exit, agent iterates to fix
- If **pre-existing failure**: Wiggum allows exit (don't block progress)

**Example**:
```
❌ RALPH VERDICT: FAIL
- Lint: 3 errors (src/auth/session.ts)
- Types: no errors
- Tests: 14/15 passing (1 pre-existing failure)
- Guardrails: none detected

Action: Continue iteration (fix lint errors)
```

---

#### BLOCKED

**Meaning**: Code contains guardrail violations (forbidden patterns).

**What Happens**:
- Wiggum escalates to human (R/O/A prompt)
- Agent cannot proceed without human decision

**Example**:
```
🚫 RALPH VERDICT: BLOCKED
- Guardrail: --no-verify flag detected
- File: src/auth/session.ts
- Reason: Bypassing Ralph verification is forbidden

Action: Human decision required (R/O/A)
```

---

### Guardrail Patterns

Ralph detects these **forbidden patterns**:

| Pattern | Why Forbidden | Team |
|---------|---------------|------|
| `--no-verify` | Bypasses Ralph verification | All |
| `git commit -n` | Bypasses pre-commit hooks | All |
| `@ts-ignore` | Silences type errors | QA, Dev |
| `eslint-disable` | Silences lint errors | QA, Dev |
| `.only()` in tests | Skips other tests | QA, Dev |
| `.skip()` in tests | Disables tests | QA, Dev |
| `DROP DATABASE` | Irreversible data loss | Operator |
| `DROP TABLE` | Irreversible data loss | Operator |
| `TRUNCATE` | Irreversible data deletion | Operator |
| `DELETE` without `WHERE` | Deletes all rows | Operator |

---

### Ralph Configuration

Located in `ralph/config.yaml`:

```yaml
verification:
  lint:
    enabled: true
    command: "npm run lint"
    fail_on_warnings: false

  typecheck:
    enabled: true
    command: "npm run typecheck"

  test:
    enabled: true
    command: "npm run test"
    allow_preexisting_failures: true

  guardrails:
    enabled: true
    patterns:
      - pattern: "--no-verify"
        severity: BLOCKED
        message: "Bypassing Ralph verification is forbidden"
      - pattern: "@ts-ignore"
        severity: BLOCKED
        message: "Type errors must be fixed, not ignored"
```

---

### Ralph CLI

```bash
# Run Ralph verification manually
ralph verify --project karematch

# Run specific checks
ralph verify --checks lint,typecheck

# Baseline mode (record current state)
ralph verify --baseline

# Compare against baseline
ralph verify --compare-baseline
```

---

## Knowledge Object System

**Status**: ✅ Production Ready

Knowledge Objects (KOs) are institutional memory artifacts that capture learning across sessions.

**Comprehensive Documentation**: See [knowledge/README.md](./knowledge/README.md)

---

### Key Features

1. **In-Memory Caching**: 457x speedup for repeated queries (0.44ms → 0.001ms)
2. **Tag Index**: O(1) hash lookups instead of O(n) scans
3. **Effectiveness Metrics**: Tracks consultations, success rates, impact scores
4. **Configurable Auto-Approval**: Project-specific thresholds
5. **Tag Aliases**: Shortcuts like `ts` → `typescript`, `js` → `javascript`

---

### KO Lifecycle

```
┌─────────────────────────────────────────────────────┐
│                   KO Lifecycle                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Agent encounters problem                        │
│  2. Agent solves problem successfully               │
│  3. Agent creates DRAFT KO                          │
│     → Saved to: knowledge/drafts/KO-DRAFT-XXX.md   │
│                                                     │
│  4. Auto-Approval Check:                            │
│     - Ralph verdict = PASS?                         │
│     - Iterations = 2-10?                            │
│     - Auto-approval enabled?                        │
│                                                     │
│     YES → Move to knowledge/approved/KO-XXX.md      │
│     NO  → Wait for human approval                   │
│                                                     │
│  5. KO Consultation (future sessions):              │
│     - Agent queries by tags                         │
│     - System returns matching KOs                   │
│     - Agent applies solution                        │
│     - Success tracked in metrics                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### KO Format

```yaml
---
id: KO-001
title: TypeScript Strict Mode Migration
tags: [typescript, strict-mode, migration]
effectiveness_score: 0.85
consultations: 12
success_rate: 0.83
created_at: 2026-01-10T10:00:00Z
approved_at: 2026-01-10T12:00:00Z
---

## Problem

Enabling TypeScript strict mode in an existing codebase causes hundreds
of type errors across multiple files.

## Solution

Incremental migration strategy:
1. Enable strict mode in tsconfig.json
2. Add `// @ts-expect-error` comments to existing errors
3. Fix one file at a time
4. Remove @ts-expect-error as you go

## Context

- Works best for codebases with <50k LOC
- Requires TypeScript 4.0+
- Team should agree on strict mode benefits first

## Example

```typescript
// Before (implicit any)
function getUser(id) {
  return database.users.find(u => u.id === id);
}

// After (strict mode)
function getUser(id: string): User | undefined {
  return database.users.find(u => u.id === id);
}
```

## Effectiveness Metrics

- Consultations: 12
- Success Rate: 83% (10/12)
- Average Impact: 0.85
- Top Tags: typescript (12), strict-mode (8), migration (5)
```

---

### KO Query Interface

```python
from knowledge.service import KnowledgeService

ko_service = KnowledgeService(Path("knowledge/"))

# Query by tags (OR semantics)
results = ko_service.query_by_tags(["typescript", "strict-mode"])

# Get specific KO
ko = ko_service.get_ko("KO-001")

# Record consultation
ko_service.record_consultation("KO-001", success=True, impact=0.9)

# Get effectiveness metrics
metrics = ko_service.get_effectiveness_metrics("KO-001")
```

---

### Tag Matching Semantics

**IMPORTANT**: Uses **OR semantics** - returns KOs with ANY matching tag (not ALL).

```bash
aibrain ko search --tags "typescript,strict-mode"
# Returns KOs with EITHER typescript OR strict-mode (or both)
```

**Why OR?**
- More results = better chance of finding solution
- Tags are additive (typescript AND strict-mode is too specific)
- Agent can filter results post-query

---

### Auto-Approval

KO system auto-approves drafts when:
- Ralph verdict = PASS
- Iterations = 2-10 (configurable)
- Auto-approval enabled in config

**Impact**: 70% of KOs auto-approved (high-confidence only).

**Configuration** (`knowledge/config.yaml`):

```yaml
auto_approval:
  enabled: true
  min_iterations: 2
  max_iterations: 10
  require_ralph_pass: true

project_overrides:
  credentialmate:
    min_iterations: 5  # HIPAA requires more validation
```

---

### Effectiveness Metrics

Tracked automatically:

| Metric | Description |
|--------|-------------|
| **Consultations** | How many times KO was queried |
| **Success Rate** | % of consultations that led to PASS |
| **Impact Score** | Average Ralph score improvement (0-1) |
| **Tag Correlation** | Which tags appear together most often |

**Dashboard**:

```bash
aibrain ko metrics

# Output:
Top 5 Knowledge Objects by Effectiveness
=========================================
KO-002: Vitest Test Organization          0.92 (8 consults, 88% success)
KO-001: TypeScript Strict Mode Migration  0.85 (12 consults, 83% success)
KO-005: API Error Handling Pattern        0.78 (15 consults, 73% success)
```

---

## Automated Bug Discovery System

**Status**: ✅ Production Ready

**Autonomy Impact**: +2% (87% → 89%)

---

### What It Does

Scans codebases for bugs across 4 sources and generates prioritized work queue tasks:

| Source | What It Detects |
|--------|-----------------|
| **ESLint** | Unused imports, console logs, security issues |
| **TypeScript** | Type errors, missing annotations |
| **Vitest** | Test failures |
| **Guardrails** | @ts-ignore, eslint-disable, .only(), .skip() |

**Turborepo Support**: Auto-detects `turbo.json` and uses direct tool invocation (bypasses argument passing issues).

---

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

---

### Key Features

#### 1. Baseline Tracking

**First Run**: Creates fingerprint snapshot

```json
{
  "baseline_created_at": "2026-01-10T10:00:00Z",
  "fingerprints": {
    "src/auth/session.ts:15": "TYPE: Property 'user' does not exist",
    "src/api/routes.ts:42": "LINT: Unused variable 'config'"
  }
}
```

**Subsequent Runs**: Detect NEW regressions only

```bash
📋 Task Summary:
  🆕 [P0] TEST-LOGIN-001: Fix 2 test error(s) (NEW REGRESSION)
  🆕 [P0] TYPE-SESSION-002: Fix 1 typecheck error(s) (NEW REGRESSION)
     [P1] LINT-MATCHING-003: Fix 3 lint error(s) (baseline)
     [P2] GUARD-CONFIG-007: Fix 2 guardrails error(s) (baseline)
```

**Why?**
- Don't create tasks for pre-existing issues
- Focus on new regressions only
- Avoid overwhelming the work queue

---

#### 2. Impact-Based Priority

| Priority | Criteria | Example |
|----------|----------|---------|
| **P0** | Blocks users or breaks builds | Test failures, build errors |
| **P1** | Degrades UX or performance | Type errors, missing props |
| **P2** | Tech debt, cleanup | Unused imports, console.logs |

---

#### 3. File Grouping

**Problem**: 50 lint errors in same file = 50 tasks (overwhelming)

**Solution**: Group all bugs in same file into 1 task

```bash
# Before grouping (50 tasks):
LINT-SESSION-001: Fix unused import on line 10
LINT-SESSION-002: Fix unused import on line 15
LINT-SESSION-003: Fix unused import on line 20
... (47 more)

# After grouping (1 task):
LINT-SESSION-001: Fix 50 lint error(s) in src/auth/session.ts
```

**Impact**: 50-70% reduction in task count

---

#### 4. Agent Type Inference

Auto-selects appropriate agent based on bug type:

| Bug Source | Agent Type | Example |
|------------|-----------|---------|
| Test failure | TestFixer | Vitest test failing |
| Type error | CodeQuality | TypeScript error |
| Lint error | CodeQuality | ESLint warning |
| Guardrail | BugFix | @ts-ignore detected |

---

### Bug Discovery Configuration

Located in `discovery/config.yaml`:

```yaml
discovery:
  sources:
    lint:
      enabled: true
      command: "npm run lint -- --format json"
      priority_map:
        error: P1
        warning: P2

    typecheck:
      enabled: true
      command: "npm run typecheck"
      priority_map:
        error: P0

    test:
      enabled: true
      command: "npm run test -- --reporter json"
      priority_map:
        failure: P0

    guardrails:
      enabled: true
      patterns:
        - "@ts-ignore": P1
        - "eslint-disable": P2
        - ".only()": P0
        - ".skip()": P1

  baseline:
    enabled: true
    path: ".aibrain/baseline.json"

  grouping:
    enabled: true
    group_by_file: true
    max_group_size: 100
```

---

### Example Output

```bash
$ aibrain discover-bugs --project karematch

🔍 Scanning karematch for bugs...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Scan Results:
  ESLint:     15 errors, 23 warnings
  TypeScript: 3 errors
  Vitest:     2 failures
  Guardrails: 5 violations

📦 Grouping by file: 48 issues → 8 tasks (83% reduction)

📋 Task Summary:
  🆕 [P0] TEST-LOGIN-001: Fix 2 test error(s) (NEW REGRESSION)
      - tests/auth/login.test.ts
  🆕 [P0] TYPE-SESSION-002: Fix 1 typecheck error(s) (NEW REGRESSION)
      - src/auth/session.ts
     [P1] LINT-MATCHING-003: Fix 3 lint error(s) (baseline)
      - src/matching/algorithm.ts
     [P1] GUARD-AUTH-004: Fix 2 guardrails error(s) (baseline)
      - src/auth/middleware.ts
     [P2] LINT-UTILS-005: Fix 8 lint error(s) (baseline)
      - src/utils/helpers.ts

✅ Tasks added to: tasks/work_queue_karematch.json

💡 Next: Run autonomous loop to fix bugs
    python autonomous_loop.py --project karematch
```

---

## Session State Management

**Location**: `orchestration/state_file.py`

Agents maintain state across sessions using markdown files with YAML frontmatter.

---

### State File Format

**Path**: `.aibrain/agent-loop.local.md`

```yaml
---
iteration: 5
max_iterations: 15
completion_promise: "BUGFIX_COMPLETE"
agent_name: "bugfix"
session_id: "session-123"
started_at: "2026-01-11T10:00:00Z"
project_name: "karematch"
task_id: "TASK-001"
---

# Task Description

Fix authentication timeout bug in login.ts that causes users to be
logged out after 5 minutes.

## Context

This is a critical bug affecting all users. The session token expires
too quickly due to incorrect TTL calculation.
```

---

### Session Resume

```python
from orchestration.state_file import read_state_file, write_state_file, LoopState
from pathlib import Path

# Read previous state
state_file = Path(".aibrain/agent-loop.local.md")
state = read_state_file(state_file)

if state:
    print(f"Resuming from iteration {state.iteration}/{state.max_iterations}")
    # Continue from where we left off
else:
    # Fresh start
    state = LoopState(
        iteration=1,
        max_iterations=15,
        completion_promise="BUGFIX_COMPLETE",
        task_description="Fix bug in login.ts",
        agent_name="bugfix",
        session_id="session-123",
        started_at=datetime.now().isoformat()
    )
    write_state_file(state, Path(".aibrain"))
```

---

### Memory Locations

| Memory Type | Location | Format | Purpose |
|-------------|----------|--------|---------|
| **Session State** | `.aibrain/agent-loop.local.md` | Markdown + YAML | Resume autonomous loops |
| **Work Queue** | `tasks/work_queue.json` | JSON | Pending/in-progress/completed tasks |
| **Session Handoffs** | `adapters/{project}/sessions/*.md` | Markdown | End-of-session summaries |
| **Audit Logs** | `.meta/audit/sessions/*.json` | JSON | Session event logs |
| **PROJECT_HQ** | `AI-Team-Plans/PROJECT_HQ.md` | Markdown | Project dashboard |
| **Ralph State** | Git commit metadata | Git | Verification history |
| **Knowledge Objects** | `knowledge/approved/*.md` | Markdown + YAML | Institutional learning |

---

## System Integration

### Wiggum + Ralph

```python
from orchestration.iteration_loop import IterationLoop
from ralph.verifier import RalphVerifier

# Create Wiggum loop with Ralph integration
loop = IterationLoop(config)
ralph = RalphVerifier(project_root)

for iteration in range(1, config.max_iterations + 1):
    # Agent makes changes
    agent.execute(task)

    # Ralph verifies
    verdict = ralph.verify()

    # Wiggum decides
    if verdict == "PASS":
        break  # Success!
    elif verdict == "BLOCKED":
        decision = ask_human_for_decision()  # R/O/A
        if decision == "R":
            revert_changes()
            break
        elif decision == "A":
            abort_session()
    else:  # FAIL
        if is_new_regression(verdict):
            continue  # Iterate
        else:
            break  # Pre-existing, allow exit
```

---

### Knowledge Objects + Wiggum

```python
from knowledge.service import KnowledgeService

ko_service = KnowledgeService(Path("knowledge/"))

# Before agent execution: Query KOs
relevant_kos = ko_service.query_by_tags(["typescript", "strict-mode"])

# Provide to agent as context
agent_context = {"knowledge_objects": relevant_kos}

# After successful execution: Create new KO
if verdict == "PASS" and 2 <= iterations <= 10:
    draft_ko = agent.create_knowledge_object(problem, solution, context)
    ko_service.save_draft(draft_ko)

    # Auto-approve if enabled
    if config.auto_approve:
        ko_service.approve_draft(draft_ko.id)
```

---

### Bug Discovery + Autonomous Loop

```bash
# 1. Discover bugs (creates tasks)
aibrain discover-bugs --project karematch

# 2. Run autonomous loop (executes tasks)
python autonomous_loop.py --project karematch --max-iterations 100

# What happens:
# - Autonomous loop reads work_queue_karematch.json
# - For each P0 task (NEW REGRESSION):
#   - Wiggum runs agent with iteration control
#   - Ralph verifies each iteration
#   - On PASS: commit, move to next task
#   - On BLOCKED: ask human (R/O/A)
```

---

## Performance Metrics

| System | Metric | Value | Impact |
|--------|--------|-------|--------|
| **Wiggum** | Autonomy | 89% | +29% from v4 |
| **Wiggum** | Tasks/session | 30-50 | 3x increase |
| **Ralph** | Zero regressions | 100% | Critical |
| **KO** | Query speed | 457x faster | Cache optimization |
| **KO** | Auto-approval | 70% | Reduced human toil |
| **Bug Discovery** | Task reduction | 50-70% | File grouping |
| **Bug Discovery** | Autonomy | +2% | Baseline tracking |

---

## Related Documentation

- [AI-ORG.md](./AI-ORG.md) - Agent organization & governance
- [CLI-REFERENCE.md](./CLI-REFERENCE.md) - All command documentation
- [CLAUDE.md](./CLAUDE.md) - Entry point for AI agents
- [knowledge/README.md](./knowledge/README.md) - Full KO system docs
- [STATE.md](./STATE.md) - Current implementation status
