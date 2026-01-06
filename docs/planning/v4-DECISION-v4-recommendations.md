# Decision Document: V4 Planning Recommendations

**Date**: 2026-01-05
**Author**: Claude (Opus 4.5)
**Context**: Expert review of V3 plan + evaluation of ChatGPT schema/observability recommendations

---

## Executive Summary

After reviewing:
- V3 Planning document (comprehensive, well-structured)
- 30+ repos in AI_Brain vault (AMADO, CrewAI, OpenHands, SWE-bench, etc.)
- ChatGPT recommendations for schema design and observability

I recommend **selective adoption** of the recommendations. The V3 plan is already solid. We add high-value governance features and defer complexity until we have actual pain points.

---

## Evaluation Framework

Each recommendation was evaluated on:

| Criteria | Weight |
|----------|--------|
| **Immediate necessity** | Does Phase 1 fail without this? |
| **Complexity cost** | How much overhead does it add? |
| **YAGNI risk** | Are we building for imagined scale? |
| **Proven value** | Is this battle-tested in the reference repos? |

---

## Recommendations: ACCEPTED

### 1. Phase -1: Trust Calibration Sprint

**Source**: ChatGPT recommendation #10
**Verdict**: ACCEPTED - Add before Phase 0
**Rationale**:

Most teams skip validation and discover problems late. By fixing 3 trivial bugs, 1 medium bug, and testing 2 forbidden actions manually, we:
- Prove the workflow before automating it
- Identify friction points early
- Calibrate thresholds with real data
- Build confidence before committing resources

**Implementation**: 1 week sprint with defined exit criteria.

---

### 2. Autonomy Contracts (YAML Policy Files)

**Source**: ChatGPT recommendation #1
**Verdict**: ACCEPTED - Add to Phase 0
**Rationale**:

V3 has implicit L1/L2 autonomy levels. Making them machine-readable:
- Turns governance intent into enforceable code
- Prevents silent scope creep as agents evolve
- Makes policy auditable for HIPAA compliance
- Enables different contracts per agent type

**Implementation**: Three YAML files (bugfix.yaml, codequality.yaml, refactor.yaml) with allowed/forbidden actions, constraints, and escalation rules.

---

### 3. Negative Capability Tests

**Source**: ChatGPT recommendation #2
**Verdict**: ACCEPTED - Add to Phase 0
**Rationale**:

You cannot claim safety without testing failure modes. These tests prove:
- Ralph blocks skipped tests, @ts-ignore, eslint-disable
- Bash hook blocks rm -rf /, chmod 777
- Autonomy contracts enforce forbidden actions
- Kill-switch actually stops execution

This is critical for HIPAA narratives and production trust.

**Implementation**: pytest suite that must pass before Phase 0 is complete.

---

### 4. Kill-Switch / Safe Mode

**Source**: ChatGPT recommendation #9
**Verdict**: ACCEPTED - Add to Phase 0
**Rationale**:

Every production system needs a global off switch. When something goes wrong at 2am, you need:
- One command to stop everything
- Read-only mode for investigation
- Graceful pause that preserves state

This is non-negotiable for production readiness.

**Implementation**: Environment variable `AI_BRAIN_MODE` with OFF/SAFE/NORMAL/PAUSED modes.

---

### 5. Human Review UX (REVIEW.md)

**Source**: ChatGPT recommendation #5
**Verdict**: ACCEPTED - Add to Phase 1
**Rationale**:

"Human approval required" is meaningless without good UX. A standardized review packet:
- Makes human-in-the-loop sustainable
- Reduces review time (target: < 5 minutes)
- Ensures consistent information for every fix
- Includes rollback plan and risk assessment

Without this, human fatigue will kill the system.

**Implementation**: Auto-generated REVIEW.md template with summary, root cause, changes, evidence, risks, and rollback plan.

---

### 6. Enhanced Audit Schema (Causality Tracking)

**Source**: ChatGPT schema recommendations (OpenTelemetry, Temporal)
**Verdict**: PARTIALLY ACCEPTED - Simplified version
**Rationale**:

The full trace/span/event schema is over-engineering for 2 target apps. However, causality tracking is valuable for debugging and HIPAA compliance.

**What we add**:
- `parent_event_id` - hierarchical event grouping
- `caused_by_event_id` - causal chains
- `decision_rationale` - why decisions were made
- `risk_level` - action risk classification

**What we skip**:
- Separate traces/spans/events tables
- OpenTelemetry integration
- Temporal workflow infrastructure

**Implementation**: ALTER TABLE audit_log with 4 new columns + indexes.

---

### 7. No-New-Features Guardrail (Simplified)

**Source**: ChatGPT recommendation #7
**Verdict**: ACCEPTED WITH MODIFICATION - Simplified heuristics
**Rationale**:

Bug-fix drift is real. But full AST analysis to detect "new public methods" is complex and prone to false positives.

**Simplified approach**:
- Use line count limits (already in V3: max 100 lines)
- Detect new exports with regex
- Detect new API routes with regex
- Warn but don't block (require manual approval if suspicious)

**Implementation**: Heuristic-based checks in governance/no_new_features.py.

---

## Recommendations: DEFERRED

### 8. Evidence Schema Versioning

**Source**: ChatGPT recommendation #3
**Verdict**: DEFERRED to Phase 3
**Rationale**:

V3 uses `evidence JSONB` which is flexible. Schema versioning matters when you have multiple versions in production and need migrations. For Phase 1 with greenfield data, this is premature.

**When to revisit**: Phase 3, if we need to query historical evidence with different structures.

---

### 9. Drift Detection Between Repos

**Source**: ChatGPT recommendation #4
**Verdict**: DEFERRED to Phase 4
**Rationale**:

Smart for multi-repo governance, but we only have 2 repos. When managing 10+ projects with diverging standards, this becomes essential.

**When to revisit**: Phase 4 (Multi-Project), when we add more target apps.

---

### 10. Agent Performance Telemetry

**Source**: ChatGPT recommendation #6
**Verdict**: DEFERRED to Phase 3
**Rationale**:

V3 already tracks F2P, P2P, completion rates. More granular metrics (avg iterations, time-to-first-green) are useful for optimization but not for proving the system works.

**When to revisit**: Phase 3 (Learning & Optimization).

---

## Recommendations: REJECTED

### 11. Full OpenTelemetry Schema

**Source**: ChatGPT Tier 1 recommendations
**Verdict**: REJECTED
**Rationale**:

OpenTelemetry's trace → span → event hierarchy is the industry standard for distributed systems at scale. But:
- We have 2 target apps, not 200
- Single-agent execution, not distributed services
- The proposed schema adds 5 tables on top of V3's 5
- Extended audit_log gives us causality without the complexity

This is a textbook case of over-engineering. We can always add OpenTelemetry later if we have actual observability pain points.

---

### 12. Temporal Workflow Infrastructure

**Source**: ChatGPT Tier 1 recommendations
**Verdict**: REJECTED
**Rationale**:

Temporal is excellent for orchestrating distributed microservices. But:
- It's a separate infrastructure service to deploy and maintain
- Our workflows are simpler (single agent, linear steps)
- AMADO's checkpoint pattern is sufficient for Phase 1
- Adding Temporal means significant complexity for marginal benefit

"Steal the schema" makes sense conceptually. Actually using Temporal does not.

---

### 13. Cross-Language Abstraction Layer

**Source**: ChatGPT recommendation #8
**Verdict**: REJECTED
**Rationale**:

Theoretically correct but practically expensive:
- Python (pytest, mypy, ruff) and TypeScript (vitest, tsc, eslint) have fundamentally different semantics
- An abstraction layer adds maintenance burden
- Every time a tool updates, you update the abstraction
- V3 already handles this with per-project adapters

Accept the duplication. Maintain simplicity.

---

### 14. LangSmith-Style Run Trees

**Source**: ChatGPT Tier 2 recommendations
**Verdict**: REJECTED
**Rationale**:

LangSmith's schema is designed for their SaaS product. Adapting it:
- Requires significant work
- Creates vendor-like coupling to a schema we don't control
- Our causality tracking in audit_log is simpler and sufficient

---

### 15. Dagster Asset Lineage

**Source**: ChatGPT Tier 1 recommendations
**Verdict**: REJECTED
**Rationale**:

Dagster solves data pipeline lineage problems. Our problem is tracking bug fixes. The conceptual model doesn't transfer cleanly.

---

## Summary: What V4 Adds to V3

| Addition | Phase | Complexity | Value |
|----------|-------|------------|-------|
| Phase -1: Trust Calibration | Before Phase 0 | Low | High |
| Autonomy Contracts (YAML) | Phase 0 | Medium | High |
| Negative Capability Tests | Phase 0 | Medium | High |
| Kill-Switch / Safe Mode | Phase 0 | Low | High |
| Enhanced Audit (causality) | Phase 0 | Low | Medium |
| Human Review UX (REVIEW.md) | Phase 1 | Medium | High |
| No-New-Features Guardrail | Phase 1 | Low | Medium |

**Total new complexity**: Moderate
**Total new value**: High

---

## The Meta-Lesson

ChatGPT's recommendations reflect someone who has studied distributed systems and enterprise architecture. The references are good (OpenTelemetry, Temporal, Dagster). But they're optimizing for a scale we don't have yet.

**The V3 plan is already well-designed for Phase 1.** The highest-value additions are governance and safety features, not observability infrastructure.

Build for the scale you have. Add complexity when you have pain points that justify it.

---

## Decision Log

| # | Recommendation | Decision | Phase | Rationale |
|---|----------------|----------|-------|-----------|
| 1 | Trust Calibration Sprint | ACCEPTED | -1 | Prove before building |
| 2 | Autonomy Contracts | ACCEPTED | 0 | Enforceable governance |
| 3 | Negative Capability Tests | ACCEPTED | 0 | Prove safety works |
| 4 | Kill-Switch | ACCEPTED | 0 | Production necessity |
| 5 | Human Review UX | ACCEPTED | 1 | Sustainable HITL |
| 6 | Enhanced Audit Schema | ACCEPTED | 0 | Simplified causality |
| 7 | No-New-Features Guard | ACCEPTED | 1 | Simplified heuristics |
| 8 | Evidence Versioning | DEFERRED | 3 | YAGNI for Phase 1 |
| 9 | Drift Detection | DEFERRED | 4 | Only 2 repos |
| 10 | Agent Telemetry | DEFERRED | 3 | Optimization, not proof |
| 11 | OpenTelemetry Schema | REJECTED | - | Over-engineering |
| 12 | Temporal Infrastructure | REJECTED | - | Heavyweight |
| 13 | Cross-Language Abstraction | REJECTED | - | Maintenance burden |
| 14 | LangSmith Run Trees | REJECTED | - | SaaS coupling |
| 15 | Dagster Lineage | REJECTED | - | Wrong problem domain |

---

## Approval

- [ ] Review V4 Planning.md
- [ ] Approve additions
- [ ] Approve rejections
- [ ] Proceed to Phase -1

---

*Document generated by Claude (Opus 4.5) based on comprehensive analysis of V3 plan, 30+ reference repos, and ChatGPT recommendations.*