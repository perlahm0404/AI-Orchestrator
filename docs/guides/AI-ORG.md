# AI Organization & Governance

**Version**: v5.2 - Production Ready
**Last Updated**: 2026-01-11
**Purpose**: Complete agent hierarchy, roles, autonomy levels, and governance contracts

---

## Quick Reference

| Team/Agent | Type | Autonomy | Purpose |
|------------|------|----------|---------|
| **QA Team** | Execution | L2 (higher) | Code quality on stable branches |
| **Dev Team** | Execution | L1 (stricter) | Feature development in isolation |
| **Operator Team** | Execution | L0.5 (strictest) | Safe deployments & migrations |
| **App Advisor** | Advisory | Auto-approve at 85% | Architecture & API guidance |
| **UI/UX Advisor** | Advisory | Auto-approve at 85% | Component & UX guidance |
| **Data Advisor** | Advisory | Auto-approve at 85% | Schema & data modeling |
| **Coordinator** | Orchestrator | L2.5 | ADR → Tasks → Execution |
| **Product Manager** | Meta-Coordinator | Governance | Evidence-based prioritization |
| **CMO Agent** | Meta-Coordinator | Governance | GTM messaging alignment |

---

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

---

## Execution Teams

### QA Team (L2 Autonomy)

**Agents**: BugFix, CodeQuality, TestFixer

**Branches**: `main`, `fix/*`

**Mission**: Maintain code quality on stable code

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

**Iteration Budgets**:
- BugFix: 15 iterations
- CodeQuality: 20 iterations
- TestFixer: 15 iterations

---

### Dev Team (L1 Autonomy)

**Agents**: FeatureBuilder, TestWriter

**Branches**: `feature/*` ONLY

**Mission**: Build new features in isolation

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

**Iteration Budgets**:
- FeatureBuilder: 50 iterations
- TestWriter: 15 iterations

---

### Operator Team (L0.5 Autonomy - Strictest)

**Agents**: Deployment, Migration, Rollback

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

## Branch Ownership

| Branch Pattern | Owner | Ralph Timing |
|----------------|-------|--------------|
| `main` | Protected | Always |
| `fix/*` | QA Team | Every commit |
| `feature/*` | Dev Team | PR only |
| `deploy/*` | Operator Team | Pre-deployment |
| `migration/*` | Operator Team | Pre-deployment |

---

## Advisory & Governance Layer

### Advisor Agents (Tier 1)

Advisors are domain experts that provide recommendations and auto-approve tactical decisions when confident.

| Advisor | Domain | Invocation | File |
|---------|--------|------------|------|
| **App Advisor** | Architecture, APIs, patterns | `/app-advisor` or `@app-advisor` | `agents/advisor/app_advisor.py` |
| **UI/UX Advisor** | Components, accessibility, UX | `/uiux-advisor` or `@uiux-advisor` | `agents/advisor/uiux_advisor.py` |
| **Data Advisor** | Schema, migrations, data modeling | `/data-advisor` or `@data-advisor` | `agents/advisor/data_advisor.py` |

#### How Advisors Work

1. **Analyze** the question and codebase context
2. **Check** alignment with existing ADRs (Architecture Decision Records)
3. **Calculate confidence** score (0-100%) based on:
   - Pattern match (30%): How well question matches known patterns
   - ADR alignment (30%): Alignment with existing decisions
   - Historical success (25%): Past success rate for similar decisions
   - Domain certainty (15%): Certainty question is in advisor's domain
4. **Decide autonomy**:
   - **Auto-approve** if confidence ≥ 85% AND tactical domain AND no ADR conflicts
   - **Escalate** if confidence < 85% OR strategic domain OR ADR conflict
5. **Create ADR** for approved decisions

#### Autonomy Thresholds

**Auto-Approve When**:
- Confidence ≥ 85%
- Decision is tactical (component structure, utility functions, code formatting)
- No ADR conflicts
- Files touched ≤ 5

**Escalate When**:
- Confidence < 85%
- Strategic domain (migrations, API versioning, security, external integrations)
- Conflicts with existing ADR
- Files touched > 5

#### Strategic vs Tactical Domains

**Strategic Domains** (Always require human approval):
- `database_migrations` - Schema changes, data migrations
- `api_versioning` - Breaking API changes, versioning strategy
- `authentication_flow` - Auth/session changes
- `external_integrations` - Third-party API integrations
- `security_policies` - Security architecture changes
- `hipaa_compliance` - HIPAA-related decisions (CredentialMate)

**Tactical Domains** (Can auto-approve when confident):
- `component_structure` - UI component organization
- `utility_functions` - Helper functions, utilities
- `test_organization` - Test file structure
- `code_formatting` - Linting, formatting rules
- `internal_refactoring` - Internal code cleanup
- `documentation` - Docs, comments

#### Usage Examples

```bash
# App Advisor - Architecture questions
@app-advisor How should we structure the API for multi-tenancy?
@app-advisor What's the best caching strategy for this feature?
@app-advisor Should we use REST or GraphQL for the new service?

# UI/UX Advisor - User experience questions
@uiux-advisor How should we display the provider dashboard?
@uiux-advisor What's the best flow for certification upload?
@uiux-advisor Should we use a modal or inline form for editing?

# Data Advisor - Schema and data questions
@data-advisor How should we model certifications and expiration tracking?
@data-advisor What's the best way to handle provider credentials?
@data-advisor Should we use soft deletes or hard deletes?
```

#### Advisor Output

Advisors produce:
- **ADR document** in `AI-Team-Plans/decisions/ADR-XXX.md` (if decision approved)
- **Recommendation** with confidence score and rationale
- **Aligned ADRs** - Existing ADRs that support this decision
- **Conflicting ADRs** - Existing ADRs that conflict (triggers escalation)
- **Decision tags** - Domain tags for categorization

---

### Coordinator Agent (Tier 2)

The Coordinator is the **central orchestration agent** that manages the flow from ADR approval through task execution.

| Agent | Role | File |
|-------|------|------|
| **Coordinator** | Orchestrates ADRs → Tasks → Execution | `agents/coordinator/coordinator.py` |

**Purpose**: Autonomous task orchestration and lifecycle management.

**Responsibilities**:
- Parse approved ADRs and break into executable tasks
- Manage work queue (`work_queue.json`)
- Assign tasks to appropriate Builders (BugFix, FeatureBuilder, etc.)
- Track task status transitions (PENDING → IN_PROGRESS → COMPLETED/BLOCKED)
- Auto-update PROJECT_HQ.md dashboard
- Create session handoffs
- Trigger Advisors on 5+ file escalation
- Register tasks discovered by Advisors (ADR-003)
- Close out ADRs when all tasks complete

**Key Methods**:
```python
from agents.coordinator import Coordinator, CoordinatorConfig

coordinator = Coordinator(CoordinatorConfig(project_root=Path(".")))

# Handle ADR approval (breaks into tasks)
tasks = coordinator.on_adr_approved(Path("AI-Team-Plans/decisions/ADR-001.md"))

# Handle task completion (assigns next task)
next_task = coordinator.on_task_completed("TASK-001-001", {"iterations": 5})

# Handle task blocked (add to blockers, continue others)
coordinator.on_task_blocked("TASK-001-002", "RALPH_BLOCKED", "Test failure")

# Close out completed ADR
result = coordinator.on_adr_closed(Path("AI-Team-Plans/decisions/ADR-001.md"))

# Create session handoff
handoff_path = coordinator.on_session_end()
```

**Tier 2 Position** in AI Team hierarchy:
```
Tier 1: Advisors (user-invoked, recommend) → Create ADRs
    ↓
Tier 2: Coordinator (autonomous, orchestrate) → Break ADRs into tasks
    ↓
Tier 3: Builders (autonomous, execute code) → Complete tasks
```

**Sub-Managers**:
- `TaskManager` - Task lifecycle management (PENDING → IN_PROGRESS → COMPLETED)
- `ProjectHQManager` - PROJECT_HQ.md dashboard updates
- `HandoffGenerator` - Session handoff creation

**Autonomy Level**: L2.5 (high autonomy for orchestration, cannot write code or make architectural decisions)

**Completion Signal**: Tasks are tracked in `work_queue.json` and status in `PROJECT_HQ.md`

---

### Meta-Coordinator Agents (Governance)

Meta-coordinators provide governance oversight and evidence-based prioritization.

| Coordinator | Role | Invocation | File |
|-------------|------|------------|------|
| **Product Manager** | Discovery & prioritization | `ProductManagerAgent.execute()` | `agents/coordinator/product_manager.py` |
| **CMO Agent** | GTM strategy & messaging | `CMOAgent.execute()` | `agents/coordinator/cmo_agent.py` |

#### Product Manager Agent

**Purpose**: Ensure features are evidence-backed and roadmap-aligned.

**Workflow**:
1. Check if task requires PM validation (features/enhancements with user impact)
2. Search Evidence Repository for related evidence items
3. Check roadmap alignment (PROJECT_HQ.md)
4. Validate outcome metrics defined
5. **Decision**: APPROVED / BLOCKED / MODIFIED

**Auto-Approve When**:
- Task type is `bugfix` or `refactor` without user impact
- Task has supporting evidence AND roadmap-aligned AND has outcome metrics

**Block When**:
- Feature lacks supporting evidence from users
- Feature not aligned with current roadmap
- Missing outcome metrics (may MODIFY to add template)

**Usage**:
```python
from agents.coordinator.product_manager import ProductManagerAgent

pm = ProductManagerAgent(app_adapter)
result = pm.execute(
    task_id="TASK-CME-045",
    task_description="Add CME tracking dashboard",
    task_data={"type": "feature", "affects_user_experience": True}
)
# Returns: PMValidation(decision="APPROVED"|"BLOCKED"|"MODIFIED", ...)
```

**Output**:
- `PMValidation` dataclass with:
  - `decision`: "APPROVED" | "BLOCKED" | "MODIFIED"
  - `reason`: Explanation for decision
  - `evidence_count`: Number of related evidence items found
  - `roadmap_aligned`: Boolean - aligns with roadmap?
  - `has_outcome_metrics`: Boolean - metrics defined?
  - `modified_description`: Updated description (if MODIFIED)
  - `recommendations`: List of next steps

**Completion Signal**: `<promise>PM_REVIEW_COMPLETE</promise>`

**Iteration Budget**: 5 iterations

---

#### CMO Agent

**Purpose**: Ensure GTM work is messaging-aligned and demand-validated.

**Workflow**:
1. Check if task is GTM-related (landing pages, messaging, onboarding, activation)
2. Check messaging alignment with messaging matrix
3. Validate demand evidence (for fake-door tests)
4. **Decision**: APPROVED / PROPOSE_ALTERNATIVE

**Auto-Approve When**:
- Task is NOT GTM-related (product/engineering work)
- GTM task with aligned messaging
- Fake-door test with honest "coming soon" language

**Propose Alternative When**:
- Messaging doesn't match current positioning matrix
- Fake-door test lacks honest "coming soon" messaging

**Usage**:
```python
from agents.coordinator.cmo_agent import CMOAgent

cmo = CMOAgent(app_adapter)
result = cmo.execute(
    task_id="TASK-LANDING-001",
    task_description="Create landing page for multi-state license tracking",
    task_data={"is_gtm_related": True}
)
# Returns: CMOReview(decision="APPROVED"|"PROPOSE_ALTERNATIVE", ...)
```

**Output**:
- `CMOReview` dataclass with:
  - `decision`: "APPROVED" | "PROPOSE_ALTERNATIVE"
  - `reason`: Explanation for decision
  - `messaging_aligned`: Boolean - matches messaging matrix?
  - `has_demand_evidence`: Boolean - demand validated?
  - `proposed_alternative`: Alternative approach (if proposing change)
  - `recommendations`: List of next steps

**Completion Signal**: `<promise>CMO_REVIEW_COMPLETE</promise>`

**Iteration Budget**: 5 iterations

---

## Iteration Budgets

| Agent | Max Iterations | Purpose |
|-------|---------------|---------|
| BugFix | 15 | Bug fixes |
| CodeQuality | 20 | Code quality improvements |
| TestFixer | 15 | Test fixes |
| FeatureBuilder | 50 | Feature development |
| TestWriter | 15 | Test writing |
| App Advisor | 5 | Architecture analysis |
| UI/UX Advisor | 5 | UX analysis |
| Data Advisor | 5 | Schema analysis |
| Coordinator | N/A | Event-driven (no iterations) |
| Product Manager | 5 | Evidence gathering |
| CMO Agent | 5 | Messaging review |

**Note**: The Coordinator is event-driven and responds to events (ADR approved, task completed, etc.) rather than iterating on tasks.

---

## Autonomy Contracts

| Contract | Team/Agent | File |
|----------|------------|------|
| QA Team | BugFix, CodeQuality, TestFixer | `governance/contracts/qa-team.yaml` |
| Dev Team | FeatureBuilder, TestWriter | `governance/contracts/dev-team.yaml` |
| Operator Team | Deployment, Migration, Rollback | `governance/contracts/operator-team.yaml` |
| Advisors | App, UI/UX, Data | `governance/contracts/advisor.yaml` |
| Coordinator | Central orchestrator | `agents/coordinator/` (see README) |
| Product Manager | PM meta-coordinator | `governance/contracts/product-manager-simple.yaml` |
| CMO Agent | CMO meta-coordinator | `governance/contracts/cmo-agent-simple.yaml` |

---

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

## Target Applications

| App | Autonomy Level | Stack |
|-----|---------------|-------|
| **KareMatch** | L2 (higher autonomy) | Node/TS monorepo, Vitest, Playwright |
| **CredentialMate** | L1 (HIPAA, stricter) | FastAPI + Next.js + PostgreSQL |

---

## Key Invariants

1. **Sessions are stateless** - Agents reconstruct context from external artifacts
2. **Memory is externalized** - Database, files, tests (not in-memory state)
3. **Agents act within contracts** - Explicit YAML policy, enforced by hooks
4. **Teams stay in their lanes** - QA on main/fix/*, Dev on feature/*, Operator on deploy/*
5. **Humans approve promotion** - Agents execute, humans decide what ships
6. **TDD is primary memory** - Tests encode behavior; if not tested, doesn't exist
7. **Ralph is the law** - PASS/FAIL/BLOCKED verdicts are canonical
8. **Agents iterate until done** - Stop hook enables self-correction loops
9. **Advisors escalate strategic decisions** - Humans make architecture choices
10. **Coordinator orchestrates, doesn't code** - Task breakdown only, no implementation

---

## Related Documentation

- [CLAUDE.md](./CLAUDE.md) - Entry point for AI agents
- [CLI-REFERENCE.md](./CLI-REFERENCE.md) - All command documentation
- [SYSTEMS.md](./SYSTEMS.md) - Core systems (Wiggum, Ralph, KO)
- [STATE.md](./STATE.md) - Current implementation status
- [CATALOG.md](./CATALOG.md) - Master documentation index
