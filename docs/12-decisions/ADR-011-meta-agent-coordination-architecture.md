# ADR-011: Meta-Agent Coordination Architecture (PM/CMO/Governance)

**Date**: 2026-01-10
**Status**: approved
**Advisor**: None (human-designed architecture)
**Deciders**: tmac

---

## Tags

```yaml
tags: [architecture, meta-agents, governance, product-management, growth, v6.0]
applies_to:
  - "agents/coordinator/**/*.py"
  - "tasks/work_queue.py"
  - "autonomous_loop.py"
  - "governance/contracts/*-agent.yaml"
domains: [orchestration, governance, product, marketing]
```

---

## Context

**Problem**: AI Orchestrator (v5.7) achieved 89% autonomy but lacked strategic oversight for three critical dimensions:

1. **Product Direction**: No evidence-driven prioritization or continuous discovery
   - Agents built whatever was in the queue without validating user need
   - No roadmap alignment checks
   - Missing outcome metrics for features

2. **Growth Engine**: No systematic demand capture or messaging validation
   - Marketing tasks had no growth strategy coordination
   - Fake-door tests lacked ethical oversight ("coming soon" messaging)
   - No pipeline tracking (lead → demo → pilot → paid)

3. **Risk & Compliance**: Limited governance beyond Ralph verification
   - HIPAA compliance checks were reactive (post-build)
   - No pre-task risk assessment for PHI, auth, billing, infra
   - Missing human-in-the-loop gates for high-risk changes

**User Context**:
- Solo founder (tmac) building CredentialMate (healthcare credentialing SaaS)
- Operating principle: **User value > safety/compliance > quality > cost**
- Need meta-coordination to ensure agents serve business goals, not just execute tasks
- HIPAA compliance is non-negotiable (PHI protection critical)

**Constraint**: Meta-agents must be **proposal-based** (no direct code modification), with human approval gates for structural changes.

---

## Decision

**Implement 3 meta-coordinator agents (L3.5 autonomy) with conditional gates**:

1. **Governance Agent**: HIPAA compliance, LLM security, human-in-the-loop for high-risk tasks
2. **Product Manager Agent**: Continuous discovery, evidence-driven prioritization, roadmap alignment
3. **CMO Agent**: Growth engine (demand capture, messaging, fake-door validation)

**Key Architecture Principles**:
- **Conditional gates** (not sequential waterfall): Agents fire only when needed
- **Proposal-based pattern**: Meta-agents validate/recommend, humans approve structural changes
- **Human-in-the-loop**: High-risk decisions require explicit approval
- **Evidence-driven**: PM requires evidence linkage for features
- **Ethical marketing**: CMO enforces honest "coming soon" messaging for fake-door tests

---

## Options Considered

### Option A: Sequential Meta-Agent Gates (Waterfall)

**Approach**: Every task passes through CMO → PM → CFO → Governance in order

**Tradeoffs**:
- Pro: Simple linear flow, easy to understand
- Pro: Every task gets full review
- Con: **High latency** - 4 sequential API calls add 1-2 seconds per task
- Con: **Wasted cycles** - Refactors don't need CMO/PM review (80% of tasks)
- Con: **Coordination overhead** - Agents wait on each other even when irrelevant

**Best for**: High-stakes environments where every task requires full review (not our case)

### Option B: Conditional Meta-Agent Gates (Selected)

**Approach**: Gates fire only when task characteristics trigger them
- Governance: **ALWAYS** (risk assessment for all tasks)
- PM: **ONLY IF** `task.type == "feature"` OR `task.affects_user_experience`
- CMO: **ONLY IF** `task.is_gtm_related`

**Tradeoffs**:
- Pro: **Low latency** - Most tasks run 1-2 gates (not 4)
- Pro: **Efficient** - Refactors/bugfixes skip PM/CMO (70-80% of tasks)
- Pro: **Flexible** - Easy to add/remove gates without changing all tasks
- Con: Requires task metadata flags (`affects_user_experience`, `is_gtm_related`)
- Con: More complex routing logic

**Best for**: Our use case (CredentialMate solo founder, high autonomy goal)

### Option C: Post-Hoc Review Only

**Approach**: No pre-task gates, only post-completion review by meta-agents

**Tradeoffs**:
- Pro: Zero pre-task latency
- Pro: Agents don't get blocked upfront
- Con: **Wasted work** - Agent builds feature, then PM blocks it (hours wasted)
- Con: **Risk exposure** - High-risk code gets written before Governance sees it
- Con: **Late feedback** - Can't course-correct before work starts

**Best for**: Exploratory prototyping where work is cheap to discard (not our case)

---

## Rationale

**Why Conditional Gates (Option B)**:

1. **CredentialMate-specific needs**:
   - HIPAA compliance is non-negotiable → Governance must always run
   - Growth engine critical at early stage → CMO needed for GTM tasks
   - Evidence-driven development → PM validates features have user demand

2. **Autonomy efficiency**:
   - 70-80% of tasks are bugfixes/refactors (skip PM/CMO)
   - Only 20-30% are features (trigger PM)
   - Only 5-10% are GTM (trigger CMO)
   - Result: Most tasks run 1 gate (Governance), not 4

3. **Solo founder constraints**:
   - tmac can't review every task manually (defeats autonomy goal)
   - Meta-agents provide oversight without bottlenecking
   - Human-in-the-loop only for HIGH/CRITICAL risk (not all tasks)

4. **Clear separation of concerns**:
   - PM: "What should we build next, for whom, and how will we measure value?"
   - CMO: "How do the right customers find us, trust us, try us, and buy—reliably?"
   - Governance: "What must never happen, what must be auditable, and what requires human approval?"

**Why NOT sequential (Option A)**:
- Adding 1-2 seconds per task × 50 tasks/session = 50-100 seconds wasted
- 70% of tasks don't need PM/CMO review (refactors, bugfixes)
- Coordination overhead compounds with more meta-agents (future: COO, CFO)

**Why NOT post-hoc (Option C)**:
- Governance can't block PHI violations after code is written
- PM can't prevent off-roadmap features before agent wastes 50 iterations
- CMO can't fix dishonest messaging after landing page is built

---

## Implementation Notes

### Schema Changes

**Task dataclass** (`tasks/work_queue.py`):
```python
# Meta-agent fields (v6.0)
pm_validated: Optional[bool] = None          # True if PM approved
pm_feedback: Optional[str] = None            # PM feedback (reason)
pm_outcome_metrics: Optional[str] = None     # Outcome metrics added by PM
cmo_reviewed: Optional[bool] = None          # True if CMO approved
cmo_priority: Optional[int] = None           # 0-10 user value priority
cmo_experiment_id: Optional[str] = None      # Related experiment ID
governance_risk_level: Optional[str] = None  # LOW/MEDIUM/HIGH/CRITICAL
governance_approved: Optional[bool] = None   # True if approved
affects_user_experience: bool = False        # Triggers PM review
is_gtm_related: bool = False                 # Triggers CMO review
touches_phi_code: bool = False               # Governance flag
evidence_refs: Optional[list[str]] = None    # Links to evidence
```

### Agent Implementations

**Created 3 new meta-agents**:
1. `agents/coordinator/governance_agent.py` (288 lines)
   - Risk assessment logic (PHI, auth, billing, infra, state expansion)
   - PHI detection (regex-based, can upgrade to ML later)
   - HIPAA eval integration (placeholder for future)
   - Recommendations engine

2. `agents/coordinator/product_manager.py` (391 lines)
   - Evidence matching (keyword-based heuristic)
   - Roadmap alignment checks (PROJECT_HQ.md)
   - Outcome metrics template injection
   - Auto-approves refactors/bugfixes (low PM value)

3. `agents/coordinator/cmo_agent.py` (288 lines)
   - GTM keyword detection (15 keywords)
   - Messaging alignment (checks messaging_matrix.md)
   - Fake-door validation (requires "coming soon" language)
   - Demand evidence checks (waitlist, pilot, LOI)

**Contracts created**:
- `governance/contracts/governance-agent.yaml` (L3.5, max_iterations=3)
- `governance/contracts/product-manager.yaml` (L3.5, max_iterations=5)
- `governance/contracts/cmo-agent.yaml` (L3.5, max_iterations=5)

### Integration Changes

**autonomous_loop.py** (lines 490-601):
```python
# GATE 1: Governance (ALWAYS)
governance_result = governance_agent.execute(task.id, task.description, task_data)
if governance_result.decision == "BLOCKED": → mark_blocked()
if governance_result.decision == "REQUIRES_APPROVAL": → prompt human

# GATE 2: PM (CONDITIONAL - if feature OR affects_user_experience)
if should_pm_validate:
    pm_result = pm_agent.execute(...)
    if pm_result.decision == "BLOCKED": → mark_blocked()
    if pm_result.decision == "MODIFIED": → inject outcome metrics

# GATE 3: CMO (CONDITIONAL - if is_gtm_related)
if should_cmo_review:
    cmo_result = cmo_agent.execute(...)
    if cmo_result.decision == "PROPOSE_ALTERNATIVE": → warn user
```

### Supporting Systems

**Evidence Repository** (`evidence/`):
- Template: `EVIDENCE_TEMPLATE.md`
- CLI commands: `aibrain evidence capture/list/link/show`
- Example: `evidence/examples/EVIDENCE-001-ca-np-cme-tracking.md`
- Integration: PM checks `evidence_refs` field on tasks

**Factory updates** (`agents/factory.py`):
- Added 3 new agent types to `COMPLETION_PROMISES` and `ITERATION_BUDGETS`
- Added imports and `create_agent()` branches for meta-agents

### Estimated Scope

- **Files modified**: 6 core files
  - `tasks/work_queue.py` (12 new fields)
  - `autonomous_loop.py` (~110 lines added)
  - `agents/factory.py` (3 agent types added)
  - 3 new agent implementations (~1000 lines total)
  - 3 new contracts
- **Complexity**: High (meta-agent architecture is new pattern)
- **Dependencies**:
  - Evidence Repository (for PM agent)
  - Messaging matrix file (for CMO agent, optional)
  - PROJECT_HQ.md roadmap (for PM agent, optional)

---

## Consequences

### Enables

1. **Evidence-driven development**
   - PM blocks features without user evidence (3+ similar evidence items)
   - Forces continuous discovery (weekly user touchpoints)
   - Links tasks → evidence → ADRs → KOs (full traceability)

2. **Ethical growth engine**
   - CMO enforces honest "coming soon" messaging for fake-door tests
   - Messaging alignment with positioning matrix (4 personas × 3 value props)
   - Pipeline metrics tracking (lead → demo → pilot → paid)

3. **Proactive HIPAA compliance**
   - Governance assesses risk BEFORE code is written
   - Human-in-the-loop for HIGH/CRITICAL risk tasks (PHI, auth, billing, infra)
   - PHI detection in task descriptions (prevents accidental logging)

4. **Higher autonomy**
   - 89% → 94-97% estimated (conditional gates reduce human interrupts)
   - Auto-approves 70% of tasks (refactors, bugfixes skip PM/CMO)
   - Only escalates HIGH/CRITICAL risk to human

5. **Strategic alignment**
   - Agents build what users need (PM validates)
   - Growth tasks follow positioning (CMO validates)
   - Risk-appropriate governance (not over/under-controlled)

6. **Solo founder leverage**
   - tmac doesn't review every task (meta-agents do)
   - Human approval only for structural/high-risk decisions
   - Full audit trail in work queue (all gate decisions logged)

### Constrains

1. **Task metadata required**
   - Must set `affects_user_experience`, `is_gtm_related`, `touches_phi_code` flags
   - Without flags, gates don't fire (tasks slip through)
   - Manual queue creation burden (can automate later)

2. **Evidence Repository dependency**
   - PM requires evidence for features
   - If no evidence exists, features get blocked
   - Forces up-front discovery work (good constraint, but slows initial velocity)

3. **Messaging matrix dependency**
   - CMO checks `messaging_matrix.md` for alignment
   - If file missing, defaults to aligned (permissive fallback)
   - Requires maintaining external docs

4. **Human-in-the-loop latency**
   - HIGH/CRITICAL risk tasks pause for human approval
   - Non-interactive mode auto-approves (reduces autonomy safety)
   - Solo founder must be available for approvals (or enable auto-approve)

5. **Meta-agent iteration cost**
   - Each gate adds 1-3 iterations (API calls)
   - Governance: ~3 iterations max
   - PM: ~5 iterations max
   - CMO: ~5 iterations max
   - Total: ~13 iterations worst-case (all 3 gates fire)

6. **Simple heuristics (not ML)**
   - Evidence matching: keyword overlap (can miss semantic matches)
   - PHI detection: regex patterns (can miss obfuscated PHI)
   - Roadmap alignment: keyword matching (can miss intent)
   - Can upgrade to ML later, but starts simple

---

## Related ADRs

- **ADR-010**: Documentation organization archival strategy (session handoffs, STATE.md)
- **ADR-003**: Lambda cost controls (circuit breaker for API limits)
- **ADR-004**: Resource tracking (iteration budgets, cost estimation)
- **ADR-005**: Business logic consolidation (CredentialMate backend)

**Future ADRs**:
- ADR-012: Eval Suite architecture (gold datasets for HIPAA, license extraction, deadline calculation)
- ADR-013: Tracing system (observability for meta-agent decisions)
- ADR-014: COO/CFO agents (operations optimization, cost management)

---

<!--
SYSTEM SECTION - DO NOT EDIT
-->

```yaml
_system:
  created_by: "tmac"
  created_at: "2026-01-10T22:00:00Z"
  approved_at: "2026-01-10T22:00:00Z"
  approved_by: "tmac"
  confidence: 0.95
  auto_decided: false
  escalation_reason: "Strategic architecture change requiring human design"
  version: "v6.0"
  autonomy_impact: "+5-8% (89% → 94-97%)"
  implementation_status: "complete"
  files_modified:
    - "tasks/work_queue.py"
    - "autonomous_loop.py"
    - "agents/factory.py"
    - "agents/coordinator/governance_agent.py"
    - "agents/coordinator/product_manager.py"
    - "agents/coordinator/cmo_agent.py"
    - "agents/coordinator/__init__.py"
    - "governance/contracts/governance-agent.yaml"
    - "governance/contracts/product-manager.yaml"
    - "governance/contracts/cmo-agent.yaml"
    - "evidence/EVIDENCE_TEMPLATE.md"
    - "evidence/README.md"
    - "evidence/index.md"
    - "cli/commands/evidence.py"
  lines_added: ~1500
  test_coverage: "pending"
```
