# AI Orchestrator v6.0 - Meta-Coordination & C-Suite AI Architecture

**Version**: v6.0
**Created**: 2026-01-10
**Status**: Planning Complete - Pending Approval
**Impact**: +5-8% autonomy (89% → 94-97%)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture (v5.7)](#current-architecture-v57)
3. [Proposed Architecture (v6.0)](#proposed-architecture-v60)
4. [Integration with Existing Systems](#integration-with-existing-systems)
5. [New Agent Specifications](#new-agent-specifications)
6. [Decision Flow Examples](#decision-flow-examples)
7. [Code-Level Integration](#code-level-integration)
8. [Implementation Timeline](#implementation-timeline)
9. [Risk Assessment](#risk-assessment)

---

## Executive Summary

### The Problem

Current AI Orchestrator (v5.7) achieves 89% autonomy but lacks:
1. **Strategic oversight** - No one validates features align with roadmap
2. **Cost management** - No automated budget enforcement
3. **Team evolution** - Creating new agents is manual, time-consuming
4. **Product alignment** - Features may not match consumer demands

### The Solution

Add two layers of meta-coordination:

**Layer 1: Meta-Coordinators (L3.5)**
- **Governance Agent**: Analyzes team composition, drafts new agents → PR approval
- **Product Manager Agent**: Validates tasks vs roadmap (pre + post gates)

**Layer 2: C-Suite AI (L4)**
- **COO**: Operations optimization, resource allocation across projects
- **CFO**: Cost management, budget enforcement
- **CMO**: Marketing strategy, user value prioritization (CredentialMate focus)

**Key Design Principle**: Meta-agents **propose**, humans **approve**. No direct code modification.

### Expected Impact

- **Governance**: +2% autonomy (auto-drafts 4 agents/year)
- **PM**: +1% autonomy (blocks misaligned features early)
- **CFO**: +1% autonomy (auto-enforces budget)
- **COO**: +1-4% autonomy (optimizes resource allocation)

**Total: 89% → 94-97% autonomy**

---

## Current Architecture (v5.7)

### Agent Teams Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN ADVISORS (L3)                         │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│  │    Data    │    │    App     │    │   UI/UX    │            │
│  │  Advisor   │    │  Advisor   │    │  Advisor   │            │
│  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘            │
│        │                  │                  │                   │
│        └──────────────────┼──────────────────┘                   │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │ (Consult & recommend)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EXECUTION AGENTS (L0.5 - L2)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ QA Team  │  │ Dev Team │  │  Admin   │  │ Operator │        │
│  │   L2     │  │   L1     │  │   L1.5   │  │  L0.5    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                 │
│  QA: BugFixAgent, CodeQualityAgent, TestFixerAgent             │
│  Dev: FeatureBuilderAgent, TestWriterAgent                     │
│  Admin: ADRCreatorAgent                                        │
│  Operator: DeploymentAgent                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Current Autonomous Loop Flow

**File**: `autonomous_loop.py` (lines 223-665)

```
1. Load work queue (work_queue_{project}.json)
   ↓
2. Get next pending task
   ↓
3. Resource checks (kill-switch, circuit-breaker)
   ↓
4. PRE-TASK ADVISOR ANALYSIS (lines 451-486):
   ├─→ Pattern detection (TaskAnalyzer)
   │   - Database keywords → DataAdvisor
   │   - API keywords → AppAdvisor
   │   - UI keywords → UIUXAdvisor
   ├─→ Advisor consultation
   │   - Confidence scoring (4 components, weighted)
   │   - ADR alignment checking
   │   - Conflict detection
   ├─→ Decision classification
   │   - Strategic: Requires human approval
   │   - Tactical: Auto-proceed if confidence ≥85%
   └─→ Escalation if needed
   ↓
5. Create agent (factory.create_agent)
   ↓
6. Run IterationLoop with Wiggum
   - Max 15-50 iterations (depends on agent type)
   - Ralph verification each iteration
   - Self-correction on FAIL verdicts
   ↓
7. Ralph verification (final)
   - PASS → continue
   - BLOCKED → R/O/A prompt to human
   ↓
8. Git commit (if PASS)
   ↓
9. Check should_create_adr()
   - 5 criteria (strategic domain, multi-iteration, conflict, escalation, high impact)
   - Register ADR creation task if triggered
   ↓
10. Continue to next task
```

### Current Decision Points

| Gate | Who Decides | Auto-Approve Threshold |
|------|-------------|----------------------|
| Strategic vs Tactical | Domain Advisors | Confidence ≥85% + no conflicts |
| Ralph Verification | Ralph Engine | PASS verdict required |
| ADR Creation | Advisor + Criteria | 5 automatic triggers |
| Production Deploy | Human | ALWAYS requires approval |

### What Works Well

✅ Domain expertise (Data, App, UI/UX advisors)
✅ Self-correction (Wiggum iteration control)
✅ Quality gates (Ralph verification)
✅ Institutional memory (ADR automation)

### What's Missing

❌ **Product alignment validation** - No check against roadmap
❌ **Cost management** - No automated budget enforcement
❌ **Resource optimization** - No cross-project balancing
❌ **Team evolution** - Manual agent creation process
❌ **User value prioritization** - No marketing perspective

---

## Proposed Architecture (v6.0)

### New Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                      C-SUITE AI (L4)                            │
│                   System-Level Orchestration                     │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│  │    COO     │    │    CFO     │    │    CMO     │            │
│  │ Operations │    │  Finance   │    │ Marketing  │            │
│  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘            │
│        │                  │                  │                   │
│        └──────────────────┼──────────────────┘                   │
└───────────────────────────┼──────────────────────────────────────┘
                            │ (Strategic decisions)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   META-COORDINATORS (L3.5)                      │
│                      Hybrid Pattern                              │
│  ┌──────────────────────┐       ┌──────────────────────┐       │
│  │  Governance Agent    │       │  Product Manager     │       │
│  │  Team Composition    │       │  Consumer Alignment  │       │
│  └──────────┬───────────┘       └──────────┬───────────┘       │
│             │                               │                    │
└─────────────┼───────────────────────────────┼────────────────────┘
              │ (Propose & validate)          │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN ADVISORS (L3)                         │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│  │    Data    │    │    App     │    │   UI/UX    │            │
│  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘            │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │ (Consult & recommend)              │
          ▼                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EXECUTION AGENTS (L0.5 - L2)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ QA Team  │  │ Dev Team │  │  Admin   │  │ Operator │        │
│  │   L2     │  │   L1     │  │   L1.5   │  │  L0.5    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Autonomy Levels Explained

| Level | Role | Decision Authority | Example Decision |
|-------|------|-------------------|-----------------|
| **L4** | C-Suite | System-wide strategy, cross-project resource allocation | COO: "Pause all P2 tasks, focus on P0 bugs" |
| **L3.5** | Meta-Coordinators | Propose structural changes, validate alignment | Governance: "Draft DatabaseSpecialistAgent contract → PR" |
| **L3** | Domain Advisors | Recommend solutions, create ADRs | DataAdvisor: "Use JSONB column for metadata storage" |
| **L2** | QA Team | Auto-fix quality issues on stable code | BugFixAgent: "Fix lint errors automatically" |
| **L1** | Dev Team | Build features (PR approval required) | FeatureBuilder: "Implement OAuth endpoint" |
| **L0.5** | Operator Team | Deploy (production always requires approval) | Deployment: "Deploy to staging (auto), production (approval)" |

---

## Integration with Existing Systems

### Key Principle: **Zero Breaking Changes**

The meta-agent system is **additive**. Existing agents run **exactly as before** if gates pass.

### What Changes

| File | Type | Change |
|------|------|--------|
| `autonomous_loop.py` | MODIFIED | Add 4 new gates (lines 451-500) |
| `tasks/work_queue.py` | MODIFIED | Add 9 fields to Task dataclass |
| `agents/factory.py` | MODIFIED | Add 5 new agent types |
| `agents/coordinator/` | NEW | 2 new agents (Governance, PM) |
| `agents/csuite/` | NEW | 3 new agents (COO, CFO, CMO) |
| `governance/contracts/` | NEW | 5 new contracts (.yaml files) |
| `orchestration/meta_integration.py` | NEW | Meta-coordinator routing |
| `cli/commands/governance.py` | NEW | CLI commands |
| `cli/commands/pm.py` | NEW | CLI commands |
| `cli/commands/coo.py` | NEW | CLI commands |
| `cli/commands/cfo.py` | NEW | CLI commands |
| `cli/commands/cmo.py` | NEW | CLI commands |

### What DOESN'T Change

✅ All existing agent implementations (bugfix.py, featurebuilder.py, etc.)
✅ All existing contracts (qa-team.yaml, dev-team.yaml, etc.)
✅ Iteration loop (Wiggum system)
✅ Ralph verification
✅ Git workflows
✅ ADR automation (v5.8)
✅ Knowledge Object system

### New Autonomous Loop Flow (v6.0)

```
1. Load work queue (SAME)
   ↓
2. Get next pending task (SAME)
   ↓
3. Resource checks (SAME)
   ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. META-COORDINATION GATES (NEW - Sequential)               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 4a. CMO Review (if user-facing)                             │
│     IF task.affects_user_experience OR task.type="feature": │
│     ├─→ CMOAgent.review_feature()                           │
│     ├─→ Decision: Approve / Deprioritize / Block            │
│     └─→ Update task.cmo_priority (0-10 scale)               │
│                                                              │
│ 4b. PM Validation (if feature)                              │
│     IF task.type == "feature":                              │
│     ├─→ ProductManagerAgent.validate_task()                 │
│     ├─→ Read PROJECT_HQ.md roadmap                          │
│     ├─→ Decision: Approve / Block / Modify description      │
│     └─→ Update task.pm_validated, task.pm_feedback          │
│                                                              │
│ 4c. CFO Spend Approval (if expensive)                       │
│     IF task.estimated_cost_usd > $10:                       │
│     ├─→ CFOAgent.approve_spend()                            │
│     ├─→ Check daily/monthly budget                          │
│     ├─→ Decision: Approve / Block / Escalate                │
│     └─→ Update task.cfo_approved                            │
│                                                              │
│ 4d. Domain Advisors (EXISTING - NO CHANGES)                 │
│     ├─→ advisor_integration.pre_task_analysis()             │
│     ├─→ Pattern detection → route to advisors               │
│     ├─→ Confidence scoring                                  │
│     ├─→ Strategic vs tactical classification                │
│     └─→ Escalation if needed                                │
│                                                              │
│ 4e. COO Resource Check (always)                             │
│     ├─→ COOAgent.check_resources()                          │
│     ├─→ Verify iteration budget available                   │
│     ├─→ Check resource_tracker limits                       │
│     ├─→ Decision: Approve / Pause / Block                   │
│     └─→ Update task.coo_resource_allocated                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
   ↓
5. Create agent (SAME - factory pattern)
   ↓
6. Run IterationLoop with Wiggum (SAME)
   ↓
7. Ralph verification (SAME)
   ↓
8. Git commit (SAME)
   ↓
9. Check should_create_adr() (SAME)
   ↓
10. Continue to next task
```

### Decision Gate Order (Critical)

Gates execute **sequentially** in this exact order:

1. **CMO** (user value) → Can deprioritize
2. **PM** (roadmap) → Can block/modify
3. **CFO** (budget) → Can block
4. **Advisors** (domain expertise) → Can escalate
5. **COO** (resources) → Can pause/block

**Why this order?**
- Financial constraints (CFO) trump product alignment (PM)
- Product alignment (PM) trumps user value ranking (CMO)
- Resource limits (COO) are last check before execution
- Domain advisors sit in middle (technical expertise)

---

## New Agent Specifications

### 1. Governance Agent (L3.5)

**Purpose**: Analyze team composition, detect capability gaps, draft new agents

**File**: `agents/coordinator/governance_agent.py`

**Contract**: `governance/contracts/governance-agent.yaml`

#### Capabilities

✅ **Allowed**:
- Read agent performance metrics
- Analyze work queue statistics
- Analyze escalation patterns
- Draft agent contracts (YAML)
- Create agent implementation (Python)
- Update factory.py
- Create PR for human review
- Consult Knowledge Objects

❌ **Forbidden**:
- Deploy new agents without approval
- Modify governance rules without PR
- Bypass human review
- Modify existing agent code directly

#### Workflow

```
Trigger: Weekly cron OR manual "aibrain governance analyze"
    ↓
1. ANALYSIS PHASE:
   ├─→ Read work_queue_*.json (all projects)
   ├─→ Read advisor_consultations.json (confidence scores)
   ├─→ Read resource_tracker.usage (agent utilization)
   └─→ Read git history (commit patterns by agent)
    ↓
2. DETECT PATTERNS:
   ├─→ High escalation rate (>70%) for specific task type?
   ├─→ Low advisor confidence (<75%) in domain?
   ├─→ Agent hitting iteration limits frequently?
   └─→ New technology/pattern not covered?
    ↓
3. RECOMMENDATION:
   ├─→ Generate gap analysis report
   ├─→ Recommend new agent type
   ├─→ Estimate impact (reduce escalations by X%)
   └─→ Draft autonomy level (L0.5 - L2)
    ↓
4. DRAFT AGENT:
   ├─→ Create governance/contracts/{agent-name}.yaml
   │   - Autonomy level
   │   - Allowed/forbidden actions
   │   - Iteration budget
   │   - Completion promise
   ├─→ Create agents/{team}/{agent-name}.py
   │   - Extend BaseAgent
   │   - Implement execute(), checkpoint(), halt()
   │   - Add completion signal
   └─→ Update agents/factory.py
       - Add to COMPLETION_PROMISES
       - Add to ITERATION_BUDGETS
       - Add to create_agent() switch
    ↓
5. CREATE PR:
   ├─→ Title: "Add {AgentName} for {purpose}"
   ├─→ Description: Gap analysis + impact estimate
   ├─→ Files changed: contract + implementation + factory
   └─→ Assign to human reviewer
    ↓
6. HUMAN REVIEW:
   ├─→ Validate gap analysis
   ├─→ Review autonomy level
   ├─→ Test agent in isolation
   └─→ Approve or request changes
    ↓
7. MERGE:
   └─→ Agent becomes available in factory
```

#### Example: Creating DatabaseSpecialistAgent

**Trigger**: Governance Agent detects 81% escalation rate for database tasks

**Analysis**:
```json
{
  "gap_detected": true,
  "task_type": "database_migration",
  "escalation_rate": 0.81,
  "total_tasks": 43,
  "escalated": 35,
  "reason": "DataAdvisor is generic, not specialized for migrations",
  "recommendation": "Create DatabaseSpecialistAgent with L1 autonomy"
}
```

**Drafted Contract** (`governance/contracts/database-specialist.yaml`):
```yaml
agent: database-specialist
version: "1.0"
team: dev-team
autonomy_level: L1

description: "Specialized agent for database schema migrations"

allowed_actions:
  - read_schema
  - write_migration_file
  - run_alembic_command
  - consult_data_advisor
  - create_test_migration

forbidden_actions:
  - drop_table
  - truncate_table
  - modify_production_db_directly
  - bypass_migration_validation

requires_approval:
  - production_migrations
  - breaking_schema_changes
  - data_migrations_with_transforms

limits:
  max_iterations: 25
  max_tables_per_migration: 5
  max_migration_file_lines: 200

completion_promise: "MIGRATION_COMPLETE"

halt_conditions:
  - ralph_blocked
  - unsafe_sql_detected
  - production_deployment_without_approval
```

**PR Created**: "Add DatabaseSpecialistAgent for schema migrations"

**Human Reviews**: Approves

**Result**: Future database tasks route to DatabaseSpecialistAgent automatically

---

### 2. Product Manager Agent (L3.5)

**Purpose**: Validate tasks align with consumer demands and roadmap

**File**: `agents/coordinator/product_manager.py`

**Contract**: `governance/contracts/product-manager.yaml`

#### Capabilities

✅ **Allowed**:
- Block/approve/modify tasks
- Read roadmap (PROJECT_HQ.md)
- Read user stories
- Update task descriptions
- Consult UIUXAdvisor
- Create follow-up tasks
- Update task priorities

❌ **Forbidden**:
- Modify code directly
- Deploy features
- Change roadmap without approval
- Bypass roadmap validation

#### Workflow

**Pre-Task Validation**:
```
Trigger: Before any task with type="feature"
    ↓
1. READ CONTEXT:
   ├─→ Load PROJECT_HQ.md (roadmap section)
   ├─→ Load user stories / requirements
   └─→ Check task.description
    ↓
2. VALIDATE ALIGNMENT:
   ├─→ Is feature on roadmap? (exact match or semantic similarity)
   ├─→ Does it match user stories?
   ├─→ Is it the right priority? (Q1 vs Q2 vs Q3)
   └─→ Consult UIUXAdvisor for UX concerns
    ↓
3. DECISION:
   ├─→ APPROVED: Feature aligns, proceed
   ├─→ BLOCKED: Not on roadmap, mark task blocked
   └─→ MODIFIED: Suggest alternative approach
    ↓
4. UPDATE TASK:
   ├─→ task.pm_validated = True/False
   ├─→ task.pm_feedback = "Reason..."
   └─→ Continue or block
```

**Post-Completion Review**:
```
Trigger: After agent completes, before PR merge
    ↓
1. REVIEW IMPLEMENTATION:
   ├─→ Read PR diff
   ├─→ Verify implementation matches specs
   ├─→ Check UX aligns with user stories
   └─→ Validate no scope creep
    ↓
2. DECISION:
   ├─→ APPROVED: Merge PR
   ├─→ REQUEST_CHANGES: Create follow-up tasks
   └─→ REJECTED: Revert changes
```

#### Example: Blocking Off-Roadmap Feature

**Task**: "Add dark mode support"

**PM Validation**:
```python
pm_result = ProductManagerAgent.validate_task(
    task_id="FEAT-UI-055",
    description="Add dark mode support",
    roadmap=get_project_roadmap("credentialmate")
)

# Result:
{
    "status": "blocked",
    "reason": "Dark mode not on Q1 2026 roadmap. Q1 priorities: CME tracking, credential renewal automation, report generation. Dark mode is Q3 2026.",
    "recommendation": "Defer to Q3 or escalate if user demand spike detected."
}

# Action:
queue.mark_blocked("FEAT-UI-055", "PM: Not on Q1 roadmap, defer to Q3")
```

---

### 3. COO - Chief Operating Officer (L4)

**Purpose**: Operations optimization across all projects

**File**: `agents/csuite/coo_agent.py`

**Contract**: `governance/contracts/coo.yaml`

#### Capabilities

✅ **Allowed**:
- Adjust iteration budgets (±50%)
- Pause low-priority tasks (P2)
- Rebalance work queues across projects
- Modify resource limits (within bounds)
- Create optimization reports

❌ **Forbidden**:
- Modify governance contracts
- Pause P0 tasks without approval
- Change agent behavior
- Deploy code

#### Workflow

```
Trigger: Daily analysis OR resource limit exceeded
    ↓
1. COLLECT METRICS:
   ├─→ resource_tracker.get_summary()
   │   - Daily API calls: 8543 / 10000
   │   - Monthly API calls: 245623 / 100000
   │   - Estimated cost: $42.35 / $50.00
   ├─→ Agent utilization rates
   │   - BugFixAgent: 15/15 iterations (100% usage)
   │   - FeatureBuilder: 23/50 iterations (46% usage)
   ├─→ Success rates per agent
   │   - BugFixAgent: 60% success in 15 iters
   │   - CodeQualityAgent: 85% success in 20 iters
   └─→ Work queue distribution
       - KareMatch: 34 pending tasks (80%)
       - CredentialMate: 9 pending tasks (20%)
    ↓
2. ANALYZE PATTERNS:
   ├─→ Is iteration budget optimal?
   │   - BugFixAgent hitting 15 limit frequently → increase to 20
   ├─→ Is work balanced across projects?
   │   - KareMatch 80% vs CredentialMate 20% → rebalance
   ├─→ Are we near resource limits?
   │   - Daily budget 85% used → pause P2 tasks
   └─→ Are there bottlenecks?
       - 10 tasks blocked on same dependency → escalate
    ↓
3. OPTIMIZATION DECISIONS:
   ├─→ Adjust iteration budgets
   │   - BugFixAgent: 15 → 20 (60% success → need more retries)
   ├─→ Pause low-priority tasks
   │   - Pause all P2 tasks until tomorrow (budget near limit)
   ├─→ Rebalance queues
   │   - Move 10 tasks from KareMatch → CredentialMate
   └─→ Recommend limits increase
       - Daily API limit 10000 → 12000 (submit for approval)
    ↓
4. EXECUTE (within autonomy):
   ├─→ Low-risk: Auto-execute
   │   - Adjust budgets ±50%
   │   - Pause P2 tasks
   └─→ High-risk: Submit PR for approval
       - Pausing P0 tasks
       - Increasing limits >50%
```

#### Example: Budget Optimization

**Scenario**: BugFixAgent frequently exhausts 15-iteration budget

**COO Analysis**:
```python
coo_result = COOAgent.optimize_operations()

# Detected pattern:
{
    "agent": "BugFixAgent",
    "current_budget": 15,
    "utilization": 1.0,  # 100% (hitting limit)
    "success_rate": 0.60,  # Only 60% succeed within 15 iterations
    "average_iterations_on_success": 12.3,
    "recommendation": "Increase budget to 20 iterations",
    "impact_estimate": "+15% success rate (60% → 75%)"
}

# Action:
agents/factory.py:
  ITERATION_BUDGETS = {
      "bugfix": 20,  # Was 15, increased by COO
  }

# Log event:
.aibrain/coo_decisions.json:
{
    "timestamp": "2026-01-10T14:30:00Z",
    "decision": "increase_iteration_budget",
    "agent": "BugFixAgent",
    "from": 15,
    "to": 20,
    "reason": "Success rate 60%, avg 12.3 iters on success",
    "approval": "auto"  # Within ±50% authority
}
```

---

### 4. CFO - Chief Financial Officer (L4)

**Purpose**: Cost management and budget enforcement

**File**: `agents/csuite/cfo_agent.py`

**Contract**: `governance/contracts/cfo.yaml`

#### Capabilities

✅ **Allowed**:
- Block tasks over $10/task
- Approve small spend (<$50 auto)
- Track Lambda costs (2.6M invocations/month)
- Create cost reports
- Forecast monthly costs

❌ **Forbidden**:
- Approve AWS spend >$500/month without human
- Modify budget without approval
- Change pricing policies

#### Budget Policies

**File**: `governance/cost_policies.yaml`
```yaml
budgets:
  daily: 50.00        # USD
  monthly: 1500.00    # USD
  per_task_max: 10.00 # USD

thresholds:
  auto_approve: 50.00     # Tasks <$50 auto-approved
  human_approval: 500.00  # AWS spend >$500 requires approval
  block: 1000.00          # Hard block at $1000/month

cost_tracking:
  lambda_invocations:
    current: 2600000      # 2.6M/month
    limit: 3000000        # 3M/month
    cost_per_million: 0.20  # $0.20 per 1M invocations

  api_calls:
    current: 245623       # Current month
    limit: 1000000        # 1M/month
    cost_per_call: 0.002  # $0.002 per call (Claude API)
```

#### Workflow

```
Trigger: Before task execution (if task.estimated_cost_usd exists)
    ↓
1. CHECK CURRENT USAGE:
   ├─→ Daily spend: $42.35 / $50.00 (85%)
   ├─→ Monthly spend: $1234.56 / $1500.00 (82%)
   └─→ Task cost: $25.00
    ↓
2. FORECAST IMPACT:
   ├─→ New daily total: $67.35 (over limit!)
   ├─→ New monthly total: $1259.56 (within limit)
   └─→ Projected month-end: $1486.20 (95% of limit)
    ↓
3. DECISION TREE:
   ├─→ Cost < $10? → APPROVE (auto)
   ├─→ Cost $10-$50 AND within budget? → APPROVE (logged)
   ├─→ Cost $50-$500 AND within budget? → ESCALATE (human approval)
   ├─→ Cost >$500? → BLOCK (requires approval)
   └─→ Would exceed daily limit? → BLOCK (wait until tomorrow)
    ↓
4. TAKE ACTION:
   ├─→ APPROVED: Continue to next gate
   ├─→ BLOCKED: Mark task blocked, notify human
   └─→ ESCALATED: Pause task, await human decision
```

#### Example: Blocking Expensive Task

**Task**: "Deploy ML model for CME recommendations"
**Estimated Cost**: $75/month (Lambda + DynamoDB + API Gateway)

**CFO Check**:
```python
cfo_result = CFOAgent.approve_spend(
    operation="deploy_ml_model",
    estimated_cost=75.00,
    project="credentialmate"
)

# Result:
{
    "approved": False,
    "reason": "Cost $75 exceeds auto-approve threshold ($50). Monthly budget at 82% ($1234/$1500). Requires human approval.",
    "recommendation": "Optimize model to reduce costs or defer to next month when budget resets.",
    "manual_override": "aibrain cfo approve-spend 75 'ML model for CME recommendations'"
}

# Action:
queue.mark_blocked("FEAT-ML-089", "CFO: Exceeds auto-approve threshold, requires manual approval")

# Human notified:
print("""
🚫 CFO BLOCKED TASK: FEAT-ML-089

Reason: Estimated cost $75/month exceeds auto-approve threshold ($50)
Budget status: $1234 / $1500 used (82%)

Options:
1. Approve manually:
   aibrain cfo approve-spend 75 "ML model critical for Q1 launch"

2. Optimize costs:
   - Use smaller Lambda functions
   - Reduce DynamoDB capacity
   - Cache API responses

3. Defer to next month (budget resets)
""")
```

---

### 5. CMO - Chief Marketing Officer (L4)

**Purpose**: Marketing strategy, user value prioritization (CredentialMate)

**File**: `agents/csuite/cmo_agent.py`

**Contract**: `governance/contracts/cmo.yaml`

#### Capabilities

✅ **Allowed**:
- Prioritize features by user value (0-10 scale)
- Create marketing tasks (tutorials, onboarding)
- Recommend UX improvements
- Analyze user feedback
- Update positioning docs

❌ **Forbidden**:
- Deploy marketing campaigns
- Modify code
- Change pricing
- Approve product roadmap changes

#### Workflow

```
Trigger: Task with affects_user_experience=True OR type="feature"
    ↓
1. ANALYZE USER VALUE:
   ├─→ Read user feedback logs
   │   - Mentions of this feature: 47 requests (high)
   │   - User pain points addressed: "Login takes too long"
   ├─→ Check feature usage metrics (if existing feature)
   │   - Current engagement: 23% of users
   │   - Target engagement: 60%
   ├─→ Consult UIUXAdvisor
   │   - UX impact: "Improves onboarding flow"
   └─→ Market positioning
       - Competitive advantage: "Competitors don't offer this"
    ↓
2. PRIORITIZE:
   ├─→ User retention impact: High (reduces churn by 15%)
   ├─→ Acquisition impact: Medium (not a main selling point)
   ├─→ Engagement impact: High (daily active feature)
   └─→ Brand impact: Medium (nice-to-have)
    ↓
3. ASSIGN PRIORITY (0-10):
   ├─→ 9-10: Critical user value (must-have)
   ├─→ 7-8: High user value (should-have)
   ├─→ 5-6: Medium user value (nice-to-have)
   ├─→ 3-4: Low user value (can defer)
   └─→ 0-2: Minimal user value (deprioritize)
    ↓
4. CREATE MARKETING TASKS (if approved):
   ├─→ "Write tutorial: How to use [feature]"
   ├─→ "Create onboarding video for NPs"
   ├─→ "Add feature announcement to newsletter"
   └─→ "Update positioning doc with new capability"
    ↓
5. DECISION:
   ├─→ APPROVED: High priority (7+), proceed
   ├─→ DEPRIORITIZED: Low priority (3-6), continue but lower queue position
   └─→ BLOCKED: No user value (0-2), recommend alternative
```

#### Example: Prioritizing Features

**Scenario**: Two features, limited resources

**Feature A**: "CME tracking dashboard"
- User feedback: 89 requests in last 30 days
- Pain point: "Manual CME tracking is time-consuming"
- Retention impact: High (reduces churn by 20%)
- **CMO Priority**: 10/10 (critical)

**Feature B**: "Dark mode"
- User feedback: 12 requests in last 30 days
- Pain point: "Bright mode strains eyes"
- Retention impact: Low (aesthetic preference)
- **CMO Priority**: 4/10 (nice-to-have)

**CMO Decision**:
```python
# Feature A:
cmo_result_a = CMOAgent.review_feature("FEAT-CME-042")
# Priority: 10, Status: Approved
# Marketing tasks created:
# - "Write CME dashboard tutorial"
# - "Create onboarding video"
# - "Add to Q1 newsletter"

# Feature B:
cmo_result_b = CMOAgent.review_feature("FEAT-UI-055")
# Priority: 4, Status: Deprioritized
# Recommendation: "Defer to Q3, focus on retention features first"
```

**Result**: CME tracking prioritized, dark mode deferred.

---

## Decision Flow Examples

### Example 1: Feature Task - Full Lifecycle

**Task**: "Add OAuth support for Google/Microsoft login"

```
┌─────────────────────────────────────────────────────────────┐
│ TASK CREATED                                                │
└─────────────────────────────────────────────────────────────┘
{
  "id": "FEAT-AUTH-042",
  "description": "Add OAuth support for Google/Microsoft login",
  "type": "feature",
  "affects_user_experience": true,
  "estimated_cost_usd": 25.00,
  "file": "apps/backend-api/auth/oauth.py"
}

┌─────────────────────────────────────────────────────────────┐
│ GATE 1: CMO REVIEW                                          │
└─────────────────────────────────────────────────────────────┘
CMOAgent.review_feature("FEAT-AUTH-042"):
  - User feedback: 47 requests for OAuth in last 30 days
  - Retention impact: High (reduces onboarding friction)
  - Competitive analysis: All competitors offer OAuth
  - UX Advisor: "OAuth improves onboarding by 40%"

✅ DECISION: APPROVED
   Priority: 9/10 (high user demand)
   Marketing tasks created:
   - "Tutorial: OAuth login setup"
   - "Announcement: New login options"

┌─────────────────────────────────────────────────────────────┐
│ GATE 2: PM VALIDATION                                       │
└─────────────────────────────────────────────────────────────┘
ProductManagerAgent.validate_task("FEAT-AUTH-042"):
  - Read PROJECT_HQ.md roadmap
  - Found: "✅ OAuth integration (Q1 2026 priority #2)"
  - User stories: "As a user, I want to login with Google"

✅ DECISION: APPROVED
   Feedback: "Aligns with Q1 roadmap, proceed"

┌─────────────────────────────────────────────────────────────┐
│ GATE 3: CFO SPEND APPROVAL                                  │
└─────────────────────────────────────────────────────────────┘
CFOAgent.approve_spend(25.00):
  - Daily budget: $12 / $50 (24% used, 76% remaining)
  - Monthly budget: $423 / $1500 (28% used)
  - Cost: $25 < $50 threshold

✅ DECISION: APPROVED (auto)
   Logged: "Task FEAT-AUTH-042: $25 approved (within threshold)"

┌─────────────────────────────────────────────────────────────┐
│ GATE 4: DOMAIN ADVISORS (Existing)                         │
└─────────────────────────────────────────────────────────────┘
advisor_integration.pre_task_analysis():
  - Pattern: "oauth", "auth" → AppAdvisor
  - Domain: "authentication" (STRATEGIC)
  - Confidence: 88% (high)
  - Recommendation: "Use Authlib library, configure providers"
  - ADRs: Aligned with ADR-002 (Auth Strategy)
  - Conflicts: None

⚠️  ESCALATED: Strategic authentication decision
    User prompt: "Continue? [y/N]"
    User: y

✅ DECISION: APPROVED (human override)

┌─────────────────────────────────────────────────────────────┐
│ GATE 5: COO RESOURCE CHECK                                  │
└─────────────────────────────────────────────────────────────┘
COOAgent.check_resources():
  - Current iterations: 423 / 500 daily limit (85%)
  - Task budget: 50 iterations (FeatureBuilder)
  - Projected: 473 (under 500 limit)

✅ DECISION: APPROVED
   Resource allocated: 50 iterations

┌─────────────────────────────────────────────────────────────┐
│ AGENT EXECUTION (Existing - No Changes)                    │
└─────────────────────────────────────────────────────────────┘
FeatureBuilderAgent.execute():
  - Branch: feature/oauth-integration
  - Implement: Authlib providers (Google, Microsoft)
  - Tests: OAuth flow tests
  - Iteration 1: Implement providers → Ralph FAIL (missing tests)
  - Iteration 2: Add tests → Ralph FAIL (type errors)
  - Iteration 3: Fix types → Ralph PASS ✅

RESULT: COMPLETED (3 iterations, under 50 budget)

┌─────────────────────────────────────────────────────────────┐
│ POST-EXECUTION                                              │
└─────────────────────────────────────────────────────────────┘
- Git commit: feature/oauth-integration
- PR created: "Add OAuth support for Google/Microsoft"
- should_create_adr(): YES (strategic auth decision)
- ADR task: ADMIN-ADR007-OAUTH-INTEGRATION

┌─────────────────────────────────────────────────────────────┐
│ PM POST-COMPLETION REVIEW                                   │
└─────────────────────────────────────────────────────────────┘
ProductManagerAgent.review_completion("FEAT-AUTH-042"):
  - Implementation matches specs: YES
  - UX aligns with user stories: YES
  - No scope creep: YES
  - Follow-up tasks: None needed

✅ DECISION: APPROVED FOR MERGE
   PR status: Ready for human final review
```

**Summary**: Task passed all 5 gates, executed successfully, triggered ADR creation, ready for merge.

---

### Example 2: Task Blocked by PM (Off-Roadmap)

**Task**: "Add dark mode support"

```
┌─────────────────────────────────────────────────────────────┐
│ TASK CREATED                                                │
└─────────────────────────────────────────────────────────────┘
{
  "id": "FEAT-UI-055",
  "description": "Add dark mode support",
  "type": "feature",
  "affects_user_experience": true,
  "estimated_cost_usd": 15.00
}

┌─────────────────────────────────────────────────────────────┐
│ GATE 1: CMO REVIEW                                          │
└─────────────────────────────────────────────────────────────┘
CMOAgent.review_feature("FEAT-UI-055"):
  - User feedback: 12 requests in last 30 days (low)
  - Retention impact: Low (aesthetic preference)
  - Competitive analysis: Nice-to-have, not differentiator

✅ DECISION: APPROVED (but deprioritized)
   Priority: 4/10 (nice-to-have, not critical)

┌─────────────────────────────────────────────────────────────┐
│ GATE 2: PM VALIDATION                                       │
└─────────────────────────────────────────────────────────────┘
ProductManagerAgent.validate_task("FEAT-UI-055"):
  - Read PROJECT_HQ.md roadmap
  - Q1 2026: CME tracking, credential renewal, report generation
  - Q2 2026: Mobile app, notifications
  - Q3 2026: ✅ Dark mode, accessibility improvements

❌ DECISION: BLOCKED
   Reason: "Not on Q1 roadmap. Dark mode scheduled for Q3 2026."
   Recommendation: "Defer to Q3 or escalate if user demand spike"

TASK MARKED BLOCKED:
  queue.mark_blocked("FEAT-UI-055", "PM: Not on Q1 roadmap, defer to Q3")

GATES 3-5: SKIPPED (task already blocked)
```

**Summary**: PM blocked task early (gate 2), no wasted execution effort.

---

### Example 3: Task Blocked by CFO (Budget Exceeded)

**Task**: "Deploy ML model for CME recommendations"

```
┌─────────────────────────────────────────────────────────────┐
│ TASK CREATED                                                │
└─────────────────────────────────────────────────────────────┘
{
  "id": "FEAT-ML-089",
  "description": "Deploy ML model for CME recommendations",
  "type": "feature",
  "estimated_cost_usd": 75.00,  # Lambda + DynamoDB
  "affects_user_experience": true
}

┌─────────────────────────────────────────────────────────────┐
│ GATE 1: CMO REVIEW                                          │
└─────────────────────────────────────────────────────────────┘
CMOAgent.review_feature("FEAT-ML-089"):
  - User value: High (personalized recommendations)
  - Retention impact: Very high (increases engagement by 30%)

✅ DECISION: APPROVED
   Priority: 9/10

┌─────────────────────────────────────────────────────────────┐
│ GATE 2: PM VALIDATION                                       │
└─────────────────────────────────────────────────────────────┘
ProductManagerAgent.validate_task("FEAT-ML-089"):
  - Roadmap: Q1 priority #1 (ML recommendations)

✅ DECISION: APPROVED

┌─────────────────────────────────────────────────────────────┐
│ GATE 3: CFO SPEND APPROVAL                                  │
└─────────────────────────────────────────────────────────────┘
CFOAgent.approve_spend(75.00):
  - Daily budget: $45 / $50 (90% used)
  - Monthly budget: $1234 / $1500 (82% used)
  - Cost: $75 > $50 threshold (requires approval)
  - Forecast: $1309 / $1500 (87% if approved)

❌ DECISION: BLOCKED
   Reason: "Cost $75 exceeds auto-approve threshold ($50)"
   Escalation: "Requires human approval"

TASK MARKED BLOCKED:
  queue.mark_blocked("FEAT-ML-089", "CFO: Exceeds auto-approve threshold")

HUMAN NOTIFIED:
  """
  CFO blocked FEAT-ML-089: $75/month cost

  Budget status: $1234 / $1500 (82%)

  Override: aibrain cfo approve-spend 75 "ML model critical for Q1"
  """

GATES 4-5: SKIPPED (task blocked)
```

**Summary**: CFO blocked expensive task, human can override if critical.

---

### Example 4: Governance Agent Creates New Agent

**Trigger**: Weekly governance analysis

```
┌─────────────────────────────────────────────────────────────┐
│ GOVERNANCE ANALYSIS TRIGGERED                               │
└─────────────────────────────────────────────────────────────┘
Command: aibrain governance analyze

GovernanceAgent.analyze_system():

1. READ METRICS:
   ├─→ Work queues: 43 DB tasks in last month
   ├─→ Escalations: 35 escalated (81% rate!)
   ├─→ DataAdvisor confidence: Avg 72% (below 85%)
   └─→ Reason: "Strategic domain (data_schema)"

2. DETECT GAP:
   Gap: Database migration tasks
   Pattern: High escalation (81%), low confidence (72%)
   Root cause: DataAdvisor too generic, not specialized

3. RECOMMENDATION:
   Create: DatabaseSpecialistAgent
   Autonomy: L1 (Dev Team)
   Impact: Reduce escalations 81% → <20%

4. DRAFT CONTRACT:
   File: governance/contracts/database-specialist.yaml
   ---
   agent: database-specialist
   autonomy_level: L1
   allowed_actions:
     - read_schema
     - write_migration_file
     - run_alembic_command
   forbidden_actions:
     - drop_table
     - truncate_table
   requires_approval:
     - production_migrations
   max_iterations: 25
   completion_promise: "MIGRATION_COMPLETE"

5. DRAFT IMPLEMENTATION:
   File: agents/dev/database_specialist.py
   ---
   class DatabaseSpecialistAgent(BaseAgent):
       def execute(self, task_id):
           # Read schema
           # Generate migration
           # Write alembic file
           # Test migration
           return {"status": "completed", "output": "...<promise>MIGRATION_COMPLETE</promise>"}

6. UPDATE FACTORY:
   File: agents/factory.py
   ---
   + "database_migration": "MIGRATION_COMPLETE",
   + "database_migration": 25,
   + elif task_type == "database_migration":
         return DatabaseSpecialistAgent(adapter, config)

7. CREATE PR:
   Title: "Add DatabaseSpecialistAgent for schema migrations"
   Description:
     Analysis: 81% of DB tasks escalate to human
     Root cause: DataAdvisor is generic
     Solution: Specialized agent (L1 autonomy)
     Impact: Reduce escalations 81% → <20%
   Files:
     - governance/contracts/database-specialist.yaml (NEW)
     - agents/dev/database_specialist.py (NEW)
     - agents/factory.py (MODIFIED)
   Reviewer: @tmac

┌─────────────────────────────────────────────────────────────┐
│ HUMAN REVIEW                                                │
└─────────────────────────────────────────────────────────────┘
@tmac reviews PR:
  ✓ Gap analysis valid (81% escalation is real)
  ✓ Autonomy level appropriate (L1 for migrations)
  ✓ Contract well-defined
  ✓ Test agent in isolation → works

DECISION: APPROVED

┌─────────────────────────────────────────────────────────────┐
│ DEPLOYMENT                                                  │
└─────────────────────────────────────────────────────────────┘
PR merged → DatabaseSpecialistAgent available in factory

NEXT DB TASK:
  Task: "Add index to users table"
  Type: "database_migration"

  autonomous_loop.py:
    agent = factory.create_agent("database_migration")
    → DatabaseSpecialistAgent

  Result: No escalation! (confidence 92%)
```

**Summary**: Governance detected gap, drafted agent, human approved, future tasks route automatically.

---

## Code-Level Integration

### File: `autonomous_loop.py` (Lines 451-550)

```python
# ============================================================================
# META-COORDINATION GATES (v6.0 - NEW)
# Lines 451-500: Add before advisor analysis
# ============================================================================

print(f"🔍 Running meta-coordination gates for task {task.id}...")

# Gate 1: CMO Review (if user-facing)
if task.affects_user_experience or task.type == "feature":
    from agents.csuite.cmo_agent import CMOAgent

    print(f"  Gate 1/5: CMO Review...")
    cmo = CMOAgent.get_instance(app_context)
    cmo_result = cmo.review_feature(
        task_id=task.id,
        description=task.description,
        context={"user_stories": getattr(task, 'user_stories', [])}
    )

    if cmo_result.status == "blocked":
        print(f"  ❌ CMO BLOCKED: {cmo_result.reason}")
        queue.mark_blocked(task.id, f"CMO: {cmo_result.reason}")
        queue.save(queue_path)
        continue  # Skip to next task

    task.cmo_priority = cmo_result.priority
    print(f"  ✅ CMO Approved (Priority: {task.cmo_priority}/10)")

# Gate 2: PM Validation (if feature)
if task.type == "feature":
    from agents.coordinator.product_manager import ProductManagerAgent

    print(f"  Gate 2/5: PM Validation...")
    pm = ProductManagerAgent.get_instance(app_context)

    # Load roadmap
    roadmap_path = actual_project_dir / "PROJECT_HQ.md"
    roadmap = roadmap_path.read_text() if roadmap_path.exists() else ""

    pm_result = pm.validate_task(
        task_id=task.id,
        description=task.description,
        roadmap=roadmap
    )

    if pm_result.status == "blocked":
        print(f"  ❌ PM BLOCKED: {pm_result.reason}")
        queue.mark_blocked(task.id, f"PM: {pm_result.reason}")
        queue.save(queue_path)
        continue

    elif pm_result.status == "modified":
        print(f"  📝 PM Modified: {pm_result.feedback}")
        task.description = pm_result.updated_description
        task.pm_feedback = pm_result.feedback

    task.pm_validated = True
    print(f"  ✅ PM Approved")

# Gate 3: CFO Spend Approval (if expensive)
if hasattr(task, 'estimated_cost_usd') and task.estimated_cost_usd and task.estimated_cost_usd > 10.0:
    from agents.csuite.cfo_agent import CFOAgent

    print(f"  Gate 3/5: CFO Spend Approval (${task.estimated_cost_usd:.2f})...")
    cfo = CFOAgent.get_instance(app_context)
    cfo_result = cfo.approve_spend(
        operation=f"task_{task.id}",
        estimated_cost=task.estimated_cost_usd,
        project=project_name
    )

    if not cfo_result.approved:
        print(f"  ❌ CFO BLOCKED: {cfo_result.reason}")
        print(f"  💡 Override: aibrain cfo approve-spend {task.estimated_cost_usd} 'reason'")
        queue.mark_blocked(task.id, f"CFO: {cfo_result.reason}")
        queue.save(queue_path)
        continue

    task.cfo_approved = True
    print(f"  ✅ CFO Approved (${task.estimated_cost_usd:.2f})")

# ============================================================================
# EXISTING WORKFLOW (v5.7 - NO CHANGES)
# Lines 451-486: Domain advisor analysis
# ============================================================================

print(f"  Gate 4/5: Domain Advisors...")

# EXISTING: Pre-task advisor analysis
advisor_result = advisor_integration.pre_task_analysis(
    task_id=task.id,
    description=task.description,
    file_path=task.file,
)

# EXISTING: Strategic escalation
if advisor_result["escalations"]:
    if advisor_result["analysis"]["priority"] == "required":
        if not non_interactive:
            print(f"  ⚠️  Strategic domain detected: {advisor_result['analysis']['domain_tags']}")
            response = input("Continue anyway? [y/N]: ")
            if response.lower() != 'y':
                queue.mark_blocked(task.id, "Escalated for human review")
                continue

print(f"  ✅ Advisors Approved")

# ============================================================================
# META-COORDINATION GATES (v6.0 - NEW)
# Gate 5: COO Resource Check
# ============================================================================

print(f"  Gate 5/5: COO Resource Check...")

from agents.csuite.coo_agent import COOAgent

coo = COOAgent.get_instance(app_context)
coo_result = coo.check_resources(
    task_id=task.id,
    estimated_iterations=task.max_iterations,
    current_usage=resource_tracker.get_summary()
)

if not coo_result.approved:
    print(f"  ❌ COO BLOCKED: {coo_result.reason}")
    queue.mark_blocked(task.id, f"COO: {coo_result.reason}")
    queue.save(queue_path)
    continue

task.coo_resource_allocated = True
print(f"  ✅ COO Approved (Resource allocated)")

print(f"✅ All gates passed! Proceeding to agent execution...")

# ============================================================================
# AGENT EXECUTION (EXISTING - NO CHANGES)
# Lines 500+: Create agent, run iteration loop, etc.
# ============================================================================

# EXISTING: Create agent from factory
agent = factory.create_agent(
    task_type=task.type,
    project_name=project_name,
    completion_promise=task.completion_promise,
    max_iterations=task.max_iterations
)

# EXISTING: Run iteration loop
result = IterationLoop(agent, app_context).run(
    task_id=task.id,
    task_description=task.description,
    max_iterations=task.max_iterations,
    resume=False
)

# ... rest continues unchanged
```

---

### File: `tasks/work_queue.py` (New Fields)

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class Task:
    # =========================================================================
    # EXISTING FIELDS (v5.7 - NO CHANGES)
    # =========================================================================
    id: str
    description: str
    file: str
    status: TaskStatus
    tests: List[str] = field(default_factory=list)
    type: str = "bugfix"
    branch: Optional[str] = None
    completion_promise: Optional[str] = None
    max_iterations: Optional[int] = None
    verification_verdict: Optional[str] = None
    source: Optional[str] = None
    discovered_by: Optional[str] = None
    fingerprint: Optional[str] = None
    priority: int = 1  # 0=P0, 1=P1, 2=P2

    # ADR automation (v5.8)
    adr_context: Optional[Dict[str, Any]] = None
    creates_adr: Optional[str] = None

    # =========================================================================
    # NEW FIELDS (v6.0) - Meta-Coordinator Tracking
    # =========================================================================

    # PM (Product Manager) fields
    pm_validated: Optional[bool] = None           # PM approval status
    pm_feedback: Optional[str] = None             # PM recommendations

    # CMO (Chief Marketing Officer) fields
    cmo_priority: Optional[int] = None            # Priority score (0-10)

    # CFO (Chief Financial Officer) fields
    cfo_approved: Optional[bool] = None           # Spend approval
    estimated_cost_usd: Optional[float] = None    # Triggers CFO review

    # COO (Chief Operating Officer) fields
    coo_resource_allocated: Optional[bool] = None # Resource check

    # Context fields (trigger meta-coordinators)
    affects_user_experience: bool = False         # Triggers CMO review
    business_value: Optional[str] = None          # "high" | "medium" | "low"

    # Governance tracking
    governance_reviewed: Optional[bool] = None
    governance_recommendations: Optional[List[str]] = field(default_factory=list)
```

---

### File: `agents/factory.py` (New Agent Types)

```python
# ============================================================================
# COMPLETION PROMISES (v6.0 - ADD NEW)
# ============================================================================
COMPLETION_PROMISES = {
    # EXISTING
    "bugfix": "BUGFIX_COMPLETE",
    "codequality": "CODEQUALITY_COMPLETE",
    "feature": "FEATURE_COMPLETE",
    "test": "TESTS_COMPLETE",
    "admin": "ADR_CREATE_COMPLETE",

    # NEW (v6.0)
    "governance": "GOVERNANCE_ANALYSIS_COMPLETE",
    "product_management": "PM_REVIEW_COMPLETE",
    "coo": "OPERATIONS_OPTIMIZED",
    "cfo": "BUDGET_REVIEWED",
    "cmo": "MARKETING_REVIEWED",
}

# ============================================================================
# ITERATION BUDGETS (v6.0 - ADD NEW)
# ============================================================================
ITERATION_BUDGETS = {
    # EXISTING
    "bugfix": 15,
    "codequality": 20,
    "feature": 50,
    "test": 15,
    "admin": 3,

    # NEW (v6.0)
    "governance": 10,       # Analysis is lightweight
    "product_management": 5, # Quick review
    "coo": 5,               # Operational decisions
    "cfo": 3,               # Budget checks
    "cmo": 5,               # Marketing review
}

# ============================================================================
# CREATE AGENT (v6.0 - ADD NEW CASES)
# ============================================================================
def create_agent(
    task_type: str,
    project_name: str,
    completion_promise: Optional[str] = None,
    max_iterations: Optional[int] = None
):
    """Create agent instance with proper Wiggum configuration."""

    adapter = get_adapter(project_name)

    config = AgentConfig(
        project_name=project_name,
        agent_name=task_type,
        expected_completion_signal=completion_promise or COMPLETION_PROMISES.get(task_type, "COMPLETE"),
        max_iterations=max_iterations or ITERATION_BUDGETS.get(task_type, 10)
    )

    # =========================================================================
    # EXISTING AGENTS (v5.7 - NO CHANGES)
    # =========================================================================
    if task_type == "bugfix":
        return BugFixAgent(adapter, config)
    elif task_type == "codequality":
        return CodeQualityAgent(adapter, config)
    elif task_type == "feature":
        return FeatureBuilderAgent(adapter, config)
    elif task_type == "test":
        return TestWriterAgent(adapter, config)
    elif task_type == "admin":
        return ADRCreatorAgent(adapter, config)

    # =========================================================================
    # NEW AGENTS (v6.0) - Meta-Coordinators
    # =========================================================================
    elif task_type == "governance":
        from agents.coordinator.governance_agent import GovernanceAgent
        return GovernanceAgent(adapter, config)

    elif task_type == "product_management":
        from agents.coordinator.product_manager import ProductManagerAgent
        return ProductManagerAgent(adapter, config)

    # =========================================================================
    # NEW AGENTS (v6.0) - C-Suite
    # =========================================================================
    elif task_type == "coo":
        from agents.csuite.coo_agent import COOAgent
        return COOAgent(adapter, config)

    elif task_type == "cfo":
        from agents.csuite.cfo_agent import CFOAgent
        return CFOAgent(adapter, config)

    elif task_type == "cmo":
        from agents.csuite.cmo_agent import CMOAgent
        return CMOAgent(adapter, config)

    else:
        raise ValueError(
            f"Unknown agent type: {task_type}. "
            f"Valid types: {', '.join(COMPLETION_PROMISES.keys())}"
        )
```

---

## Implementation Timeline

### Phase 1: Foundation (Week 1)

**Goal**: Create base infrastructure

**Tasks**:
- [ ] Create `agents/coordinator/base_coordinator.py`
- [ ] Create `agents/csuite/base_csuite.py`
- [ ] Extend Task dataclass in `tasks/work_queue.py`
- [ ] Create `orchestration/meta_integration.py`
- [ ] Create `orchestration/csuite_integration.py`
- [ ] Write 5 YAML contracts
- [ ] Write `governance/cost_policies.yaml`

**Deliverables**: Base classes, extended dataclass, contracts

---

### Phase 2: Meta-Coordinators (Week 2)

**Goal**: Implement Governance and PM agents

**Tasks**:
- [ ] Implement `agents/coordinator/governance_agent.py`
  - `analyze_system()`
  - `draft_agent_contract()`
  - `create_pr()`
- [ ] Implement `agents/coordinator/product_manager.py`
  - `validate_task()`
  - `review_completion()`
- [ ] Add gates to `autonomous_loop.py` (lines 451-486)
- [ ] Test meta-coordinator decision flow

**Deliverables**: Working Governance + PM agents with gates

---

### Phase 3: C-Suite (Week 3)

**Goal**: Implement COO, CFO, CMO

**Tasks**:
- [ ] Implement `agents/csuite/coo_agent.py`
- [ ] Implement `agents/csuite/cfo_agent.py`
- [ ] Implement `agents/csuite/cmo_agent.py`
- [ ] Add gates to `autonomous_loop.py`
- [ ] Update `agents/factory.py`

**Deliverables**: Working C-suite with full gate integration

---

### Phase 4: CLI & Testing (Week 4)

**Goal**: User interface and validation

**Tasks**:
- [ ] Create `cli/commands/governance.py`
- [ ] Create `cli/commands/pm.py`
- [ ] Create `cli/commands/coo.py`
- [ ] Create `cli/commands/cfo.py`
- [ ] Create `cli/commands/cmo.py`
- [ ] Integration tests (end-to-end)
- [ ] Performance benchmarking

**Deliverables**: CLI commands, test suite

---

### Phase 5: Documentation (Week 5)

**Goal**: Knowledge transfer

**Tasks**:
- [ ] Update `CATALOG.md`
- [ ] Update `STATE.md`
- [ ] Update `DECISIONS.md`
- [ ] Update `CLAUDE.md`
- [ ] Create `docs/meta-agents.md`
- [ ] Create `docs/csuite.md`
- [ ] Create `docs/governance-workflow.md`

**Deliverables**: Complete documentation

---

## Risk Assessment

### Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Meta-agents make bad decisions** | HIGH | All structural changes require PR approval |
| **Budget overrun** | MEDIUM | Human approval required >$500/month |
| **PM blocks critical tasks** | MEDIUM | P0 tasks can bypass PM validation |
| **Governance spam PRs** | LOW | Max 3 PRs/week limit enforced |
| **Decision conflicts** | MEDIUM | Clear hierarchy (CFO > PM > CMO > COO) |
| **Performance degradation** | LOW | Gates add <100ms latency |
| **Existing agents broken** | CRITICAL | Zero changes to existing agent code |

### Safeguards

1. **Proposal-based design**
   - Meta-agents cannot modify code directly
   - All changes go through PR approval
   - Human has final say

2. **Audit trail**
   - All decisions logged to `.aibrain/meta_decisions.json`
   - Daily summary reports
   - Weekly human review

3. **Human gates**
   - New agents: ALWAYS requires approval
   - Budgets >$500: ALWAYS requires approval
   - Governance rules: ALWAYS requires approval

4. **Emergency override**
   - Kill-switch (AI_BRAIN_MODE=OFF)
   - Can disable individual meta-agents
   - Can revert to v5.7 behavior

---

## Appendix: File Locations

### New Files (Create)

```
agents/
├── coordinator/
│   ├── __init__.py
│   ├── base_coordinator.py
│   ├── governance_agent.py
│   └── product_manager.py
├── csuite/
│   ├── __init__.py
│   ├── base_csuite.py
│   ├── coo_agent.py
│   ├── cfo_agent.py
│   └── cmo_agent.py

governance/
├── contracts/
│   ├── governance-agent.yaml
│   ├── product-manager.yaml
│   ├── coo.yaml
│   ├── cfo.yaml
│   └── cmo.yaml
└── cost_policies.yaml

orchestration/
├── meta_integration.py
├── csuite_integration.py
└── decision_flow.py

cli/commands/
├── governance.py
├── pm.py
├── coo.py
├── cfo.py
└── cmo.py

.aibrain/
├── meta_decisions.json
├── coo_optimizations.json
├── cfo_budget_tracking.json
└── cmo_priorities.json
```

### Modified Files

```
agents/factory.py            # Add 5 new agent types
autonomous_loop.py           # Add 4 new gates (lines 451-500)
tasks/work_queue.py          # Add 9 fields to Task dataclass
```

---

**Ready for implementation? Approve this architecture to begin Phase 1.**
