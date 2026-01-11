# Governance & Autonomy Contracts

Summary of governance rules and autonomy contracts for AI agents.

## Governance Hierarchy

```
Kill-Switch (global: OFF/SAFE/NORMAL/PAUSED)
    │
    ▼
Team Contract (qa-team.yaml / dev-team.yaml / operator-team.yaml)
    │
    ▼
Branch Restrictions (main/fix/* vs feature/* vs deploy/*)
    │
    ▼
Ralph Verification (per-change: PASS/FAIL/BLOCKED)
    │
    ▼
Human Approval (per-merge or per-deployment)
```

## Autonomy Levels

| Level | Teams | Description | Examples |
|-------|-------|-------------|----------|
| **L2** | QA Team | Higher autonomy - can auto-commit to fix/* branches | BugFix, CodeQuality, TestFixer |
| **L1** | Dev Team | Stricter - can only commit to feature/*, PR required | FeatureBuilder, TestWriter |
| **L0.5** | Operators | Strictest - production always requires approval | Deployment, Migration, Rollback |

## QA Team Contract (L2)

**File**: `governance/contracts/qa-team.yaml` (or individual: `bugfix.yaml`, `codequality.yaml`)

**Branches**: `main`, `fix/*`

### Allowed Actions
- ✅ Read files
- ✅ Write to existing files (no new files)
- ✅ Run tests
- ✅ Run Ralph (every commit)
- ✅ Create fix branches
- ✅ Commit changes
- ✅ Auto-fix lint/type issues

### Forbidden Actions
- ❌ Create new files (features)
- ❌ Modify migrations
- ❌ Modify CI config
- ❌ Push to main directly
- ❌ Deploy anything
- ❌ Change behavior (test count must stay same)
- ❌ **Use `--no-verify` flag** (NEVER bypass Ralph)

### Limits
- Max 100 lines added
- Max 5 files changed
- Must halt on Ralph BLOCKED

### Ralph Timing
**Every commit** - No exceptions

---

## Dev Team Contract (L1)

**File**: `governance/contracts/dev-team.yaml`

**Branches**: `feature/*` ONLY

### Allowed Actions
- ✅ Read files
- ✅ Write files
- ✅ Create new files
- ✅ Run tests
- ✅ Run Ralph (PR only)
- ✅ Create feature branches
- ✅ Build new functionality
- ✅ Write new tests

### Forbidden Actions
- ❌ Push to main or fix/* branches
- ❌ Modify migrations (requires approval)
- ❌ Modify CI config
- ❌ Deploy anything
- ❌ Delete existing tests
- ❌ **Use `--no-verify` flag**

### Requires Approval
- New dependencies
- New API endpoints
- Schema changes
- External API integrations

### Limits
- Max 500 lines added
- Max 20 files changed
- Must halt on `approval_required`

### Ralph Timing
**PR only** - Not on every commit, only when creating PR

---

## Operator Team Contract (L0.5)

**File**: `governance/contracts/operator-team.yaml`

**Branches**: `deploy/*`, `migration/*`, `ops/*`

### Environment Gates

| Environment | Auto-Deploy? | Auto-Rollback? | Approval Required? |
|-------------|-------------|----------------|-------------------|
| **Development** | ✅ Yes | ✅ Yes | ❌ No (full autonomy) |
| **Staging** | ✅ Yes (after first approval) | ✅ Yes | ✅ First time only |
| **Production** | ❌ No | ❌ No (manual only) | ✅ ALWAYS |

### Allowed Actions
- ✅ Build application
- ✅ Run pre-deployment validation (tests, migrations, SQL/S3 safety)
- ✅ Deploy to dev/staging/production (with environment gates)
- ✅ Execute database migrations (with validation)
- ✅ Rollback deployments (auto for dev/staging, manual for production)
- ✅ Monitor deployment health
- ✅ Create deployment reports

### Forbidden Actions (CRITICAL - Irreversible)
- ❌ **DROP DATABASE** - Irreversible data loss
- ❌ **DROP TABLE** - Irreversible data loss
- ❌ **TRUNCATE TABLE** - Irreversible data deletion
- ❌ **DELETE without WHERE** - Deletes all rows irreversibly
- ❌ **DELETE S3 BUCKET** - Irreversible bucket deletion
- ❌ **DELETE ALL S3 OBJECTS** - Bulk deletion without recovery
- ❌ SSH to production servers
- ❌ Direct production database modifications
- ❌ Bypass deployment pipeline

### Requires Approval
- **All production deployments** (ALWAYS)
- **All production migrations** (ALWAYS)
- **All production rollbacks** (manual approval required)
- First-time staging deployment
- AWS resource provisioning (requires business case)

### Migration Requirements
- Must have `upgrade()` method
- Must have `downgrade()` method (production REQUIRED)
- No forbidden SQL patterns in production
- Reversibility validated before execution

### SQL Safety Validation (Automatic)
All migrations scanned for:
- DROP DATABASE, DROP TABLE, TRUNCATE
- DELETE without WHERE clause
- UPDATE without WHERE clause
- Missing downgrade() method (production only)

### S3 Safety Validation (Automatic)
All code scanned for:
- Bucket deletion operations
- Bulk object deletion
- Irreversible S3 operations

### Auto-Rollback Triggers (Dev/Staging Only)
- Deployment failure
- Health check failure
- Error rate spike
- Critical metric degradation

---

## Ralph Verification

**Purpose**: Quality gates on every change (QA Team) or PR (Dev Team)

**File**: `ralph/engine.py`

### Verdict Types

| Verdict | Meaning | Agent Action |
|---------|---------|--------------|
| **PASS** ✅ | All checks passed | Commit and continue |
| **FAIL** ❌ | Pre-existing issues OR new issues agent can fix | Agent retries (up to max iterations) |
| **BLOCKED** 🚫 | Guardrail violation (e.g., `--no-verify`) | Human decision required (R/O/A) |

### Checks Performed
1. **Lint**: ESLint (JavaScript/TypeScript)
2. **Type**: TypeScript compiler
3. **Tests**: Vitest, Playwright
4. **Guardrails**:
   - No `@ts-ignore`
   - No `eslint-disable`
   - No `.only()` in tests
   - No `.skip()` in tests
   - No `--no-verify` flag usage

### Human Decision on BLOCKED

When Ralph returns BLOCKED:
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

**Note**: Agents NEVER bypass Ralph. `--no-verify` is FORBIDDEN in all contracts.

---

## Wiggum Iteration Control

**Purpose**: Manage self-correction loops

**File**: `orchestration/iteration_loop.py`

### Iteration Budgets

| Agent Type | Max Iterations |
|------------|---------------|
| BugFixAgent | 15 |
| CodeQualityAgent | 20 |
| FeatureBuilder | 50 |
| TestWriter | 15 |
| TestFixer | 15 |

### Stop Hook Logic

```
Agent completes iteration → Stop Hook evaluates:
  ├─→ Completion signal detected? → ALLOW (exit)
  ├─→ Iteration budget exhausted? → ASK_HUMAN
  ├─→ Ralph PASS? → ALLOW (exit)
  ├─→ Ralph BLOCKED? → ASK_HUMAN (R/O/A prompt)
  ├─→ Ralph FAIL (pre-existing)? → ALLOW (safe to merge)
  └─→ Ralph FAIL (regression)? → BLOCK (continue iteration)
```

### Completion Signals

Agents signal task completion with `<promise>` tags:

| Task Type | Completion Signal |
|-----------|-------------------|
| Bugfix | `<promise>BUGFIX_COMPLETE</promise>` |
| Code quality | `<promise>CODEQUALITY_COMPLETE</promise>` |
| Feature | `<promise>FEATURE_COMPLETE</promise>` |
| Tests | `<promise>TESTS_COMPLETE</promise>` |
| Refactor | `<promise>REFACTOR_COMPLETE</promise>` |

**Requirements**: REQUIRED for all agents, exact string matching (case-sensitive).

---

## Branch Strategy

| Branch Pattern | Owner | Ralph Timing | Can Push | Can Merge |
|----------------|-------|--------------|----------|-----------|
| `main` | Protected | Always | No one | PR only (human approval) |
| `fix/*` | QA Team | Every commit | Agents | PR → main (human approval) |
| `feature/*` | Dev Team | PR only | Agents | PR → main (human approval) |
| `deploy/*` | Operators | Validation | Agents | Auto-deploy (with environment gates) |

---

## Kill Switch

**Purpose**: Emergency stop for all agents

**File**: `governance/kill_switch/mode.py`

### Modes

| Mode | Description | Agents Can Execute? |
|------|-------------|-------------------|
| **OFF** | Emergency stop | ❌ No |
| **SAFE** | Read-only mode | ❌ No writes |
| **NORMAL** | Full operation | ✅ Yes |
| **PAUSED** | Temporary pause | ❌ No |

### Commands

```bash
aibrain emergency-stop    # Set to OFF
aibrain pause             # Set to PAUSED
aibrain resume            # Set to NORMAL
```

---

## Key Invariants

1. **Sessions are stateless** - Agents reconstruct context from external artifacts
2. **Memory is externalized** - Database, files, tests (not in-memory state)
3. **Agents act within contracts** - Explicit YAML policy, enforced by hooks
4. **Teams stay in their lanes** - QA on main/fix/*, Dev on feature/*, Operators on deploy/*
5. **Humans approve promotion** - Agents execute, humans decide what ships
6. **TDD is primary memory** - Tests encode behavior; if not tested, doesn't exist
7. **Ralph is the law** - PASS/FAIL/BLOCKED verdicts are canonical
8. **Agents iterate until done** - Stop hook enables self-correction loops

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

## For More Details

- **Agent Details**: See [AGENTS.md](AGENTS.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Complete Contracts**: See `governance/contracts/*.yaml`
- **Ralph Implementation**: See `ralph/engine.py`
- **Wiggum Implementation**: See `orchestration/iteration_loop.py`
