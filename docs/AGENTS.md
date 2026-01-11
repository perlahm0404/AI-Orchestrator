# Agent Types & Usage

Guide to all AI agents in the orchestrator system.

## Execution Agents (Tier 3)

These agents write code and execute tasks.

### BugFix Agent
**Purpose**: Fix bugs in existing code without changing behavior.

**Autonomy**: L2 (Higher)
**Branches**: `main`, `fix/*`
**Max Iterations**: 15
**Completion Signal**: `<promise>BUGFIX_COMPLETE</promise>`

**Can Do**:
- Read/write existing files
- Run tests
- Fix lint/type errors
- Auto-commit to `fix/*` branches

**Cannot Do**:
- Create new files (features)
- Change test count (behavior change)
- Modify migrations
- Use `--no-verify` flag

**When to Use**: Bug reports, test failures, type errors, lint issues

**Example**:
```bash
python run_agent.py --agent bugfix --task-id BUG-001
```

---

### CodeQuality Agent
**Purpose**: Improve code quality without changing behavior.

**Autonomy**: L2 (Higher)
**Branches**: `main`, `fix/*`
**Max Iterations**: 20
**Completion Signal**: `<promise>CODEQUALITY_COMPLETE</promise>`

**Can Do**:
- Refactor for readability
- Remove dead code
- Fix lint violations
- Improve type safety

**Cannot Do**:
- Change behavior
- Add features
- Remove tests

**When to Use**: Code cleanup, refactoring, technical debt

**Example**:
```bash
python run_agent.py --agent codequality --task-id QUALITY-001
```

---

### TestFixer Agent
**Purpose**: Fix broken tests without changing implementation.

**Autonomy**: L2 (Higher)
**Branches**: `main`, `fix/*`
**Max Iterations**: 15
**Completion Signal**: `<promise>TESTS_COMPLETE</promise>`

**Can Do**:
- Fix failing tests
- Update test assertions
- Fix test setup/teardown

**Cannot Do**:
- Change implementation code
- Delete tests
- Skip tests (`.skip()`)

**When to Use**: Test failures after refactoring

---

### FeatureBuilder Agent
**Purpose**: Build new features from ADRs.

**Autonomy**: L1 (Stricter)
**Branches**: `feature/*` only
**Max Iterations**: 50
**Completion Signal**: `<promise>FEATURE_COMPLETE</promise>`

**Can Do**:
- Create new files
- Write new tests
- Implement features
- Update documentation

**Cannot Do**:
- Push to `main` or `fix/*`
- Modify migrations without approval
- Create new dependencies without approval
- Deploy anything

**Requires Approval**:
- New dependencies
- New API endpoints
- Schema changes
- External API integrations

**When to Use**: New features, enhancements

**Example**:
```bash
python run_agent.py --agent featurebuilder --adr ADR-005
```

---

### TestWriter Agent
**Purpose**: Write tests for existing features.

**Autonomy**: L1 (Stricter)
**Branches**: `feature/*`
**Max Iterations**: 15
**Completion Signal**: `<promise>TESTS_COMPLETE</promise>`

**Can Do**:
- Write unit tests
- Write integration tests
- Create test fixtures

**Cannot Do**:
- Modify implementation code
- Change behavior

**When to Use**: Improving test coverage

---

## Advisor Agents (Tier 1)

Advisors provide domain expertise and create ADRs.

### App Advisor
**Purpose**: Architecture, APIs, and application patterns.

**Invocation**: `/app-advisor` or `@app-advisor`
**File**: `agents/advisor/app_advisor.py`
**Max Iterations**: 5

**Auto-Approve When**:
- Confidence ≥ 85%
- Tactical domain (utility functions, internal refactoring)
- No ADR conflicts

**Escalate When**:
- Strategic domain (migrations, API versioning, external integrations)
- ADR conflicts
- Files touched > 5

**Example Questions**:
```
@app-advisor How should we structure the API for multi-tenancy?
@app-advisor What's the best caching strategy for this feature?
@app-advisor Should we use REST or GraphQL?
```

---

### UI/UX Advisor
**Purpose**: Components, accessibility, and user experience.

**Invocation**: `/uiux-advisor` or `@uiux-advisor`
**File**: `agents/advisor/uiux_advisor.py`
**Max Iterations**: 5

**Auto-Approve When**:
- Component structure decisions (tactical)
- Code formatting/organization
- Internal UI refactoring

**Escalate When**:
- Major UX flow changes
- Accessibility requirements changes
- External UI library changes

**Example Questions**:
```
@uiux-advisor How should we display the provider dashboard?
@uiux-advisor What's the best flow for certification upload?
@uiux-advisor Should we use a modal or inline form?
```

---

### Data Advisor
**Purpose**: Schema, migrations, and data modeling.

**Invocation**: `/data-advisor` or `@data-advisor`
**File**: `agents/advisor/data_advisor.py`
**Max Iterations**: 5

**Auto-Approve When**:
- Tactical data queries
- Internal data structures
- Test data setup

**Escalate When**:
- Database migrations (ALWAYS strategic)
- Schema changes
- Data retention policies

**Example Questions**:
```
@data-advisor How should we model certifications and expiration?
@data-advisor What's the best way to handle provider credentials?
@data-advisor Should we use soft deletes or hard deletes?
```

---

## Orchestration Agents (Tier 2)

### Coordinator Agent
**Purpose**: ADR → Task orchestration and execution management.

**File**: `agents/coordinator/coordinator.py`
**Autonomy**: L2.5 (event-driven, no iterations)

**Responsibilities**:
- Parse approved ADRs
- Break into executable tasks
- Manage work queue (`work_queue.json`)
- Assign tasks to Builders
- Track task status (PENDING → IN_PROGRESS → COMPLETED/BLOCKED)
- Update PROJECT_HQ.md dashboard
- Create session handoffs

**Event Handlers**:
```python
coordinator.on_adr_approved(adr_path)     # ADR approved → create tasks
coordinator.on_task_completed(task_id)    # Task done → assign next
coordinator.on_task_blocked(task_id)      # Task blocked → add to blockers
coordinator.on_adr_closed(adr_path)       # All tasks done → close ADR
coordinator.on_session_end()              # Session ending → create handoff
```

**When to Use**: Automatically triggered by ADR events, not manually invoked.

---

## Meta-Coordinator Agents (Governance)

### Product Manager Agent
**Purpose**: Evidence-based prioritization and validation.

**File**: `agents/coordinator/product_manager.py`
**Max Iterations**: 5

**Auto-Approve When**:
- Task type is `bugfix` or `refactor` (no user impact)
- Task has supporting evidence + roadmap-aligned + outcome metrics

**Block When**:
- Feature lacks evidence from users
- Not roadmap-aligned
- Missing outcome metrics

**Decision**: APPROVED / BLOCKED / MODIFIED

**Usage**:
```python
from agents.coordinator.product_manager import ProductManagerAgent

pm = ProductManagerAgent(app_adapter)
result = pm.execute(
    task_id="TASK-CME-045",
    task_description="Add CME tracking dashboard"
)
```

---

### CMO Agent
**Purpose**: GTM strategy and messaging alignment.

**File**: `agents/coordinator/cmo_agent.py`
**Max Iterations**: 5

**Auto-Approve When**:
- NOT GTM-related (product/engineering work)
- GTM work with aligned messaging

**Propose Alternative When**:
- Messaging doesn't match positioning
- Fake-door test lacks honest "coming soon"

**Decision**: APPROVED / PROPOSE_ALTERNATIVE

**Usage**:
```python
from agents.coordinator.cmo_agent import CMOAgent

cmo = CMOAgent(app_adapter)
result = cmo.execute(
    task_id="TASK-LANDING-001",
    task_description="Create landing page for multi-state tracking"
)
```

---

## Operator Agents (Tier 3 - Deployment)

### Deployment Agent
**Purpose**: Deploy applications to dev/staging/production.

**Autonomy**: L0.5 (Strictest)
**Branches**: `deploy/*`

**Environment Gates**:
- **Dev**: Auto-deploy, auto-rollback
- **Staging**: First-time approval, then auto-deploy with auto-rollback
- **Production**: ALWAYS requires human approval, manual rollback only

**Workflow**:
1. Pre-deployment validation (tests, migrations, safety checks)
2. Build application
3. Deploy to environment
4. Run migrations (if configured)
5. Health checks
6. Auto-rollback on failure (dev/staging only)

**SQL Safety** (Automatic):
- Blocks: DROP DATABASE, DROP TABLE, TRUNCATE
- Blocks: DELETE without WHERE, UPDATE without WHERE
- Requires: downgrade() method in production migrations

**S3 Safety** (Automatic):
- Blocks: Bucket deletion
- Blocks: Bulk object deletion

---

### Migration Agent
**Purpose**: Execute database migrations safely.

**Autonomy**: L0.5 (Strictest)

**Requirements**:
- Must have `upgrade()` method
- Must have `downgrade()` method (production REQUIRED)
- No forbidden SQL patterns in production
- Reversibility validated before execution

---

### Rollback Agent
**Purpose**: Rollback failed deployments.

**Autonomy**: L0.5 (Strictest)

**Dev/Staging**: Auto-rollback on failure triggers
**Production**: Manual approval ALWAYS required

**Triggers**:
- Deployment failure
- Health check failure
- Error rate spike
- Critical metric degradation

---

## Agent Selection Guide

| Scenario | Agent | Autonomy |
|----------|-------|----------|
| Bug in existing code | BugFix | L2 (auto-commit) |
| Code cleanup/refactor | CodeQuality | L2 (auto-commit) |
| Test failures | TestFixer | L2 (auto-commit) |
| New feature (with ADR) | FeatureBuilder | L1 (PR only) |
| Missing tests | TestWriter | L1 (PR only) |
| Architecture question | App Advisor | Tier 1 (creates ADR) |
| UX question | UI/UX Advisor | Tier 1 (creates ADR) |
| Schema question | Data Advisor | Tier 1 (creates ADR) |
| Task orchestration | Coordinator | Tier 2 (event-driven) |
| Feature prioritization | PM Agent | Governance |
| GTM validation | CMO Agent | Governance |
| Deploy to dev | Deployment | L0.5 (auto) |
| Deploy to production | Deployment | L0.5 (manual approval) |

## For More Details

- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Governance**: See [GOVERNANCE.md](GOVERNANCE.md)
- **Complete Docs**: See [CLAUDE.md](../CLAUDE.md)
