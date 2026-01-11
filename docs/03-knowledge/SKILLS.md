# AI Orchestrator Skills Catalog

Skills are **reusable, deterministic functions** that agents invoke to accomplish tasks. Unlike agents (which iterate autonomously), skills are stateless utilities that provide immediate results.

**When to use a skill vs. an agent**: See the decision matrix in the strategic review plan.

---

## Verification & Quality

### ralph_verify
**Module**: `ralph/engine.py`
**Purpose**: Quality gate verification (PASS/FAIL/BLOCKED verdicts)
**Usage**: Called by all agents on every iteration
**Performance**: ~2-5 seconds per verification
**Cached**: No (intentionally fresh on each run)

**Example**:
```python
from ralph.engine import verify
verdict = verify(
    project="credentialmate",
    branch="fix/TASK-123",
    enforce_golden_paths=True
)
# Returns: Verdict.PASS | Verdict.FAIL | Verdict.BLOCKED
```

### guardrail_check
**Module**: `ralph/guardrails.py`
**Purpose**: Pattern detection (@ts-ignore, .skip(), eslint-disable, etc.)
**Usage**: Part of Ralph verification pipeline
**Patterns**: 8 anti-patterns detected (see ralph/guardrail_patterns.yaml)

---

## Knowledge Management

### ko_search
**Module**: `knowledge/repository.py`
**Purpose**: Query approved Knowledge Objects by tags or full-text search
**Performance**: 0.001ms (457x speedup with in-memory cache)
**Usage**: Agents consult before attempting complex tasks

**Example**:
```python
from knowledge.repository import search_knowledge_objects
kos = search_knowledge_objects(
    tags=["typescript", "strict-mode"],  # OR semantics
    project="karematch"
)
# Returns: List[KnowledgeObject]
```

**Tag Aliases**:
- `ts` → `typescript`
- `js` → `javascript`
- `py` → `python`

### ko_approve
**Module**: `knowledge/approval.py`
**Purpose**: Promote draft Knowledge Objects to approved status
**Auto-Approval**: Enabled when Ralph=PASS + iterations=2-10
**Impact**: 70% of KOs auto-approved (high-confidence only)

### evidence_search
**Module**: `evidence/repository.py`
**Purpose**: Find user feedback, bug reports, feature requests
**Usage**: ProductManager agent uses for evidence-driven prioritization
**Status**: ⚠️ Currently a stub - needs implementation

**Example**:
```python
from evidence.repository import search_evidence
evidence = search_evidence(
    query="authentication timeout",
    evidence_types=["user_feedback", "bug_report", "feature_request"]
)
# Returns: List[Evidence]
```

---

## Discovery & Analysis

### bug_scan
**Module**: `discovery/scanner.py`
**Purpose**: Auto-discover bugs from 4 sources (ESLint, TypeScript, Vitest, Guardrails)
**Turborepo Support**: Auto-detects turbo.json, uses direct tool invocation
**Baseline Tracking**: First run creates fingerprint, subsequent runs detect regressions
**Output**: Prioritized work queue tasks (P0, P1, P2)

**Example**:
```bash
# First run: Create baseline
python discovery/scanner.py --project karematch

# Subsequent runs: Detect new bugs
python discovery/scanner.py --project karematch --sources lint,typecheck
```

**Impact-Based Priority**:
- P0: Blocks users (test failures, critical type errors)
- P1: Degrades UX (warnings, lint issues)
- P2: Tech debt (guardrail violations, code smells)

### baseline_track
**Module**: `discovery/baseline.py`
**Purpose**: Regression detection via SHA-256 fingerprinting
**Storage**: `discovery/baselines/{project}.json`
**Algorithm**: Hash(file + line + message) for each issue

---

## Git & Version Control

### git_conflict_resolution
**Status**: ⚠️ Currently manual, **candidate for promotion to agent**
**Usage Count**: 47 invocations (high-value automation opportunity)
**Why promote?**: High frequency (>5 uses/week), repeatable pattern, autonomous potential

**Current Usage**:
- Manually resolve merge conflicts during PR integration
- Pattern: Detect conflict markers, analyze intent, propose resolution

**Proposed Agent**:
- **GitConflictAgent** (L1 autonomy, 10 iterations)
- Auto-resolve simple conflicts (formatting, import order)
- Escalate complex conflicts (logic changes) to human

### branch_guard
**Module**: `governance/branch_restrictions.py`
**Purpose**: Enforce branch naming conventions and access control
**Rules**:
- QA Team: `main`, `fix/*`, `hotfix/*` only
- Dev Team: `feature/*` only
- Operator Team: `deploy/*`, `migration/*`, `ops/*`

---

## Cost & Resource Management

### cost_estimate
**Module**: `governance/resource_tracker.py`
**Purpose**: Estimate LLM API cost before execution
**Tracks**: Iteration budgets, cost per task, budget exhaustion rate

**Example**:
```python
from governance.resource_tracker import estimate_task_cost
cost_usd = estimate_task_cost(
    agent_type="BugFix",
    estimated_iterations=5,
    context_size_tokens=8000
)
# Returns: float (USD)
```

### circuit_breaker
**Module**: `orchestration/circuit_breaker.py`
**Purpose**: Auto-halt after repeated failures (prevent runaway loops)
**Triggers**: 3 consecutive BLOCKED verdicts, cost threshold exceeded

---

## Session Management

### session_handoff
**Module**: `orchestration/reflection.py`
**Purpose**: Generate session handoff for continuity across sessions
**Auto-Generated**: At end of autonomous loop iterations
**Format**: Markdown with: accomplished, not done, blockers, Ralph verdict, files modified, next steps

### state_persist
**Module**: `orchestration/state_file.py`
**Purpose**: Session state persistence for resume capability
**Storage**: `.aibrain/agent-loop.local.md`
**Usage**: Autonomous loop auto-resumes from last state on interruption

---

## Future Skills (Pending Implementation)

### dependency_update
**Proposed**: Auto-update npm/pip packages with test verification
**Rationale**: High value for security debt reduction
**Promotion Criteria**: If usage grows >5 invocations/week

### hipaa_audit
**Proposed**: Scan codebase for HIPAA violations
**Target**: CredentialMate repository
**Checks**: PHI in logs, unencrypted data, missing audit trails

### cme_validate
**Proposed**: CME calculation validation (CredentialMate-specific)
**Rationale**: Prevent bugs like 5 critical CME issues discovered manually
**Status**: Will become **CME Data Validator Agent** (Phase 3)

---

## Agent vs. Skill Decision Matrix

**Add Agent When (ALL must be true)**:
1. High frequency (>5 uses/week)
2. Self-verifiable (can detect completion)
3. Repeatable pattern (similar tasks)
4. Autonomous potential (low human supervision)
5. Iteration needed (self-correction loops)

**Add Skill When (ANY can be true)**:
1. Reusable utility (2+ callers)
2. Deterministic function
3. Low frequency (<5 uses/week)
4. Context-dependent (needs human judgment)
5. Quick execution (<30 seconds)

**Sunset Agent When (ANY triggers review)**:
1. Low utilization (<10% of tasks)
2. Redundant capability (overlap >60% with another agent)
3. Governance overhead > value added
4. No iteration needed (convert to skill)
5. Declining performance (completion rate <50%)

---

## Skill Promotion Candidates

Based on usage analysis, the following skills are candidates for promotion to agents:

| Skill | Usage/Week | Status | Recommendation |
|-------|-----------|--------|----------------|
| **git_conflict_resolution** | 47 uses | ⭐ High | Promote to Agent |
| dependency_update | 2 uses | Low | Keep as skill |
| evidence_search | 0 uses (stub) | Not implemented | Implement as skill first |

---

## Last Updated

**Date**: 2026-01-10
**Review Cycle**: Quarterly (next: 2026-04-10)
**Maintained By**: AI Orchestrator strategic oversight system
