# PRD: AI Brain (v1)

**Date**: 2026-01-05
**Status**: Draft
**Source**: Derived from [v4 Planning.md](./v4%20Planning.md)

---

## 1. Problem Statement

Software teams accumulate technical debt faster than they can address it. Bug backlogs grow, lint errors pile up, and type violations multiply. Human developers context-switch between feature work and maintenance, losing productivity on both.

Current approaches fail because:
- Manual bug fixing is interruptible and slow
- Automated tools fix syntax but miss semantics
- AI assistants lack governance and produce regressions
- Knowledge is lost between sessions and team members

AI Brain solves this by providing **governed, autonomous agents** that fix bugs and improve code quality with:
- Evidence-based completion (no "trust me, it's fixed")
- Human-in-the-loop approval (not human-in-the-loop execution)
- Institutional memory that survives sessions

---

## 2. Goals (What Success Looks Like)

### Phase 1 Success (Primary)
- **First real bug in KareMatch fixed autonomously** with full evidence trail
- **First quality batch completed** with zero behavior changes
- Human review time < 5 minutes per fix
- Zero regressions introduced

### Longer-term Success
- 10+ bugs fixed per week across projects
- 50+ quality issues resolved per week
- Recurring bug patterns detected and prevented
- Human trust in AI fixes increasing (measured by approval rate)

---

## 3. Non-Goals (Explicit Exclusions)

| Excluded | Rationale |
|----------|-----------|
| Feature development | Earn trust with fixes first (Phase 5) |
| Deployment | Human-only action, never automated |
| Database migrations | High-risk, requires human judgment |
| Multi-tenant SaaS | Single-operator system for now |
| Real-time collaboration | Async workflow is sufficient |
| Vector embeddings | Tag-based matching for v1 |
| Cross-language abstraction | Accept Python/TypeScript duplication |

---

## 4. Users / Personas

### 4.1 Human Operator

**Who**: Solo developer or tech lead managing 1-3 codebases

**Needs**:
- Visibility into what AI is doing without constant monitoring
- Clear decision points (approve/reject/defer)
- Artifacts that explain decisions
- Emergency stop capability
- Sustainable review workflow (< 5 min per fix)

**Touchpoints**:
- CLI (`aibrain status`, `aibrain approve TASK-123`)
- REVIEW.md for each fix
- Knowledge Objects for institutional memory
- Obsidian for browsing artifacts

### 4.2 AI Agents (System Users)

**Who**: BugFix, CodeQuality, Refactor agents

**Needs**:
- Clear contracts defining allowed/forbidden actions
- Access to prior Knowledge Objects
- Stateless execution (no session memory)
- External memory via artifacts

**Constraints**:
- Cannot exceed autonomy contract
- Cannot bypass governance hooks
- Must produce evidence for completion
- Must halt on circuit breaker

### 4.3 Auditors / Reviewers

**Who**: Future team members, compliance reviewers, curious humans

**Needs**:
- Complete audit trail (who did what, when, why)
- Causality chains (what caused this action)
- Immutable evidence (cannot be retroactively edited)
- Human-readable artifacts (REVIEW.md, Knowledge Objects)

**Touchpoints**:
- `audit_log` table with causality tracking
- Knowledge Objects with traceability to source issues
- Ralph verification logs

---

## 5. Core Capabilities (High-Level)

### 5.1 Governed Autonomous Execution

Agents work within explicit contracts. They cannot:
- Exceed allowed actions
- Bypass governance hooks
- Mark tasks complete without evidence
- Modify production infrastructure

See: [v4 Planning.md → Autonomy Contracts](./v4%20Planning.md#autonomy-contracts)

### 5.2 Evidence-Based Completion

No task is marked complete without:
- Reproduction test (for bugs)
- Ralph verification (all steps passed)
- Before/after snapshots
- Human approval (for L1/L2 autonomy)

See: [v4 Planning.md → Ralph Wiggum Verification System](./v4%20Planning.md#ralph-wiggum-verification-system)

### 5.3 Human-in-the-Loop Approval

Humans approve **promotion**, not execution:
- Agent executes autonomously within contract
- Agent produces REVIEW.md with evidence
- Human reviews and approves/rejects
- Agent cannot proceed past approval gates without human

See: [v4 Planning.md → Human Review UX](./v4%20Planning.md#human-review-ux)

### 5.4 Institutional Memory

Knowledge survives sessions via:
- Knowledge Objects (semantic memory from resolutions)
- Audit log (episodic memory of actions)
- REVIEW.md (human-readable fix summaries)
- Tests (TDD as primary memory mechanism)

See: [KNOWLEDGE-OBJECTS-v1.md](./KNOWLEDGE-OBJECTS-v1.md)

### 5.5 Safety Controls

- **Kill-switch**: `AI_BRAIN_MODE=OFF` stops all execution
- **Safe mode**: `AI_BRAIN_MODE=SAFE` allows reads and tests only
- **Circuit breaker**: Auto-halt after repeated failures
- **Negative capability tests**: Prove safety systems work

See: [v4 Planning.md → Kill-Switch & Safe Mode](./v4%20Planning.md#kill-switch--safe-mode)

---

## 6. Safety & Governance Principles

### Non-Negotiable Principles

1. **Sessions are stateless** - Agents reconstruct context from external artifacts
2. **Memory is externalized** - No in-memory state survives session boundaries
3. **Agents act within contracts** - Explicit allowed/forbidden/approval-required actions
4. **Humans approve promotion** - Agents execute, humans decide what ships
5. **TDD is primary memory** - Tests encode behavior, not comments or docs
6. **Knowledge Objects on resolution only** - No speculative knowledge creation

### Governance Hierarchy

```
Kill-Switch (global)
    │
    ▼
Autonomy Contract (per-agent)
    │
    ▼
Governance Rules (per-task-type)
    │
    ▼
Ralph Verification (per-change)
    │
    ▼
Human Approval (per-fix)
```

---

## 7. Success Metrics

### Phase -1 Metrics (Trust Calibration)
| Metric | Target |
|--------|--------|
| Trivial bugs fixed manually | 3 |
| Medium bugs fixed manually | 1 |
| Forbidden actions blocked | 2 |
| Evidence quality score | >= 4/5 |

### Phase 0 Metrics (Governance Foundation)
| Metric | Target |
|--------|--------|
| Negative capability tests passing | 100% |
| Kill-switch response time | < 1 second |
| Autonomy contracts enforced | 100% |

### Phase 1 Metrics (Agents Working)
| Metric | Target |
|--------|--------|
| Real bugs fixed | >= 10 |
| Quality issues fixed | >= 50 |
| Regressions introduced | 0 |
| Human review time per fix | < 5 minutes |
| Approval rate | > 80% |

---

## 8. Rollout Phases

### Phase -1: Trust Calibration (1 week)

**Purpose**: Prove the workflow before automating it

**Activities**:
- Fix 3 trivial + 1 medium bug manually
- Test that guardrails block forbidden actions
- Calibrate thresholds
- Go/No-Go decision

**Exit Criteria**: All calibration tasks pass

### Phase 0: Governance Foundation (2 weeks)

**Purpose**: Working governance before any AI runs

**Activities**:
- Implement autonomy contracts
- Implement kill-switch and safe mode
- Deploy enhanced audit schema
- Write and pass negative capability tests

**Exit Criteria**: Safety systems proven to work

### Phase 1: BugFix + CodeQuality Agents (4-6 weeks)

**Purpose**: First autonomous fixes on real code

**Activities**:
- Deploy BugFix agent on KareMatch
- First real bug fixed with full evidence
- Deploy CodeQuality agent
- First quality batch completed

**Exit Criteria**: 10 bugs fixed, 50 quality issues fixed, zero regressions

---

## 9. Explicitly Deferred Work

| Deferred | Phase | Rationale |
|----------|-------|-----------|
| Sentry integration | Phase 2 | Need working agents first |
| GitHub issue intake | Phase 2 | Need working agents first |
| Refactor agent | Phase 2 | Lower priority than fixes |
| Hot patterns / learning | Phase 3 | Optimization, not core |
| Evidence schema versioning | Phase 3 | YAGNI for Phase 1 |
| Multi-project dashboard | Phase 4 | Only 2 projects initially |
| Drift detection | Phase 4 | Only 2 projects initially |
| Feature agent | Phase 5 | Earn trust with fixes first |
| Vector embeddings | Future | Tag matching sufficient |
| Model-graded evals | Future | Pass/fail tests sufficient |

---

## 10. References

- [v4 Planning.md](./v4%20Planning.md) - Complete implementation plan
- [KNOWLEDGE-OBJECTS-v1.md](./KNOWLEDGE-OBJECTS-v1.md) - Knowledge Object specification
- [DECISION-v4-recommendations.md](./DECISION-v4-recommendations.md) - Design decisions