# Dual-Repo Stateless Memory Strategy (AI_Orchestrator + CredentialMate)

**Date**: 2026-02-07
**Scope**: Cross-repo implementation roadmap
**Status**: Strategic Planning
**Target**: Enable autonomous operation across both repositories

---

## Executive Summary

This document outlines how to implement the stateless memory architecture **across both repositories** with:
- **Shared foundations** (Session State, Work Queue, Decision Trees)
- **Repository-specific optimizations** (AI_Orchestrator orchestration, CredentialMate operations)
- **Cross-repo coordination** (unified memory, shared KO system, team separation)

---

## Current State Analysis

### AI_Orchestrator (Execution Engine)

**What it is**: Central orchestration, governance, and agent management system

**Current memory systems**:
- ✅ STATE.md (current build state)
- ✅ sessions/*/active/*.md (session handoffs)
- ✅ knowledge/approved/*.md (KO system, 457x speedup)
- ✅ Wiggum iteration control
- ✅ Ralph verification
- ✅ Council Pattern debates
- ✅ Autonomous loop with work queues

**What's missing**:
- ❌ Fine-grained session checkpointing (iteration-level)
- ❌ Semantic search in KO system
- ❌ Agent Teams coordination
- ❌ Event sourcing (decision immutability)
- ❌ Multi-repo state synchronization

### CredentialMate (Target Application)

**What it is**: Production application executing agent-driven tasks

**Current memory systems**:
- ✅ task work queues (tasks/work_queue_credentialmate.json)
- ✅ Database state (PostgreSQL)
- ✅ Lambda deployments (stateless functions)
- ✅ Session files (from Phase 1 implementation)

**What's missing**:
- ❌ Iteration-level checkpointing (not yet integrated)
- ❌ Cross-session learning (KO integration)
- ❌ Cost tracking per agent
- ❌ Semantic memory retrieval
- ❌ Multi-project awareness

---

## Unified Implementation Strategy

### Layer 1: Session State (Phase 1) ✅ DONE

**Implementation Status**: COMPLETE in both repos

**AI_Orchestrator**:
- ✅ `orchestration/session_state.py` created
- ⏳ Integration with IterationLoop (pending)
- ⏳ Integration with autonomous_loop.py (pending)

**CredentialMate**:
- ✅ `orchestration/session_state.py` copied/linked
- ⏳ Integration with feature builders (pending)
- ⏳ Auto-checkpointing on task completion (pending)

**Shared approach**:
```
.aibrain/session-{task_id}-{checkpoint}.md
├─ JSON frontmatter (structured)
├─ Markdown body (human-readable)
└─ Auto-saves after iteration
```

---

### Layer 2: Work Queue Persistence (Phase 2) ⏳ READY

**Purpose**: Persistent task tracking with checkpoint history

**Affects both**:
- AI_Orchestrator: Orchestrates work across multiple teams/projects
- CredentialMate: Tracks tasks for async execution

**Unified Schema**:
```sql
CREATE TABLE work_items (
  id TEXT PRIMARY KEY,
  task_id TEXT,
  project TEXT,  -- "credentialmate" or "karematch"
  orchestrator_id TEXT,  -- Points to AI_Orchestrator task
  status TEXT,
  session_ref TEXT,
  retry_count INTEGER,
  error_log TEXT,
  metadata JSON
);

CREATE TABLE checkpoints (
  task_id TEXT,
  iteration_count INTEGER,
  verdict TEXT,
  timestamp TIMESTAMP,
  session_ref TEXT,
  project TEXT
);
```

**Implementation**:
- **AI_Orchestrator**: Central SQLite database (source of truth)
- **CredentialMate**: JSON sync with local SQLite (read-only copy)
- **Sync mechanism**: Periodic sync via shared API

---

### Layer 3: Knowledge Objects (Phase 4) - ENHANCED

**Current state**:
- AI_Orchestrator: KO system exists (457x caching)
- CredentialMate: Uses KO system but not creating new KOs

**Enhancement Phase 2**:
```
Add Semantic Search (Chroma)
├─ Hybrid: Tag-based (existing) + Semantic (new)
├─ Expected improvement: 20-30% better discovery
└─ Both repos benefit immediately
```

**Enhancement Phase 3**:
```
Add Session References to KOs
├─ Track which sessions created each KO
├─ Measure KO effectiveness
├─ Cross-repo learning (AI_Orchestrator learns from CredentialMate findings)
└─ Institutional memory survives
```

**Implementation**:
```json
{
  "id": "KO-cm-001",
  "title": "JWT token validation patterns",
  "source_sessions": [
    {"repo": "credentialmate", "session_id": "SESSION-20260207-001"},
    {"repo": "ai-orchestrator", "session_id": "SESSION-20260205-003"}
  ],
  "projects": ["credentialmate", "karematch"],
  "consultation_count": 45,
  "effectiveness": 0.87
}
```

---

### Layer 4: Decision Trees (Phase 3) - NEW

**Purpose**: Immutable audit trail of critical decisions

**Both repos**:
```
.aibrain/decisions/{task_id}.jsonl
├─ APPROACH decisions (why we chose X over Y)
├─ GUARDRAIL_OVERRIDE decisions (governance escalations)
├─ ESTIMATION_ADJUSTMENT decisions (budget changes)
└─ Replay capability for understanding
```

**Example**:
```jsonl
{"timestamp":"2026-02-07T10:00:00Z","task_id":"TASK-123","repo":"credentialmate","decision":"APPROACH","value":"jwt_tokens","confidence":0.9}
{"timestamp":"2026-02-07T10:15:00Z","task_id":"TASK-123","repo":"credentialmate","decision":"GUARDRAIL_OVERRIDE","value":"allow_external_api","severity":"medium","approver":"human"}
```

**Cross-repo benefit**:
- AI_Orchestrator: Governance decisions across teams
- CredentialMate: Audit trail for compliance/HIPAA

---

## Detailed Implementation Plan

### Phase 1: Session State (DONE) ✅

#### AI_Orchestrator
- [x] SessionState class implemented
- [x] 23 tests passing
- [ ] Integration with IterationLoop (1-2 days)
- [ ] Integration with autonomous_loop.py (1-2 days)
- [ ] Testing with real orchestration tasks (2-3 days)

#### CredentialMate
- [x] SessionState imported (shared code)
- [ ] Integrate with feature builders (1-2 days)
- [ ] Auto-checkpoint on task completion (1 day)
- [ ] Testing with real CredentialMate tasks (1-2 days)

**Timeline**: 1 week total

---

### Phase 2: Work Queue Persistence (READY) ⏳

#### Design (3 days)
- [ ] Define unified schema (supports both repos)
- [ ] Plan sync mechanism
- [ ] Design ACID constraints

#### Implementation (7 days)
- [ ] Create `db/models.py` (SQLAlchemy)
- [ ] Create `db/work_queue.py` (manager class)
- [ ] Implement checkpoint logic
- [ ] Create sync API

#### Integration (5 days)
- [ ] Integrate with AI_Orchestrator autonomous_loop.py
- [ ] Integrate with CredentialMate task runner
- [ ] Sync mechanism (git-friendly JSON + SQLite hybrid)

#### Testing (3 days)
- [ ] 20+ integration tests
- [ ] Cross-repo coordination tests
- [ ] Sync mechanism tests

**Timeline**: 2-3 weeks total

---

### Phase 3: Decision Trees (READY) ⏳

#### Both Repos (2 weeks)
- [ ] Decision logging in agents
- [ ] JSONL append-only storage
- [ ] Replay capability
- [ ] Governance integration
- [ ] HIPAA compliance instrumentation

**Location**:
```
.aibrain/decisions/
├─ {task_id}.jsonl  (per-task audit)
├─ governance/      (policy decisions)
└─ guardrails/      (safety overrides)
```

---

### Phase 4: KO Enhancements (READY) ⏳

#### Semantic Search (1-2 weeks)
- [ ] Chroma integration
- [ ] Hybrid tag + semantic search
- [ ] Caching layer
- [ ] Both repos benefit

#### Session References (1 week)
- [ ] Add session_ref to KO metadata
- [ ] Track effectiveness per session
- [ ] Cross-repo learning

#### Effectiveness Tracking (3 days)
- [ ] Measure consultation → success rate
- [ ] Auto-ranking of KOs
- [ ] Feedback loop

---

### Phase 5: Integration Testing (READY) ⏳

#### Full System Tests (2 weeks)
- [ ] Session resumption across contexts
- [ ] Work queue coordination
- [ ] Multi-team execution (QA/Dev/Ops)
- [ ] Cross-repo learning
- [ ] Cost tracking and optimization
- [ ] HIPAA compliance validation

---

## Cross-Repo Coordination Model

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 AI_Orchestrator (Central)               │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Autonomous Loop (orchestrates all work)         │  │
│  │ ├─ Work Queue (SQLite - source of truth)        │  │
│  │ ├─ Session State (checkpoint coordination)      │  │
│  │ ├─ Knowledge Objects (shared institutional)     │  │
│  │ ├─ Decision Trees (governance audit)            │  │
│  │ └─ Team Coordination (QA/Dev/Ops)               │  │
│  └─────────────────────────────────────────────────┘  │
│                     ↕ (API)                            │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Governance Layer                                │  │
│  │ ├─ Ralph Verification                           │  │
│  │ ├─ Guardrails Enforcement                       │  │
│  │ └─ Autonomy Contracts (L0.5/L1/L2)              │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
          ↕                           ↕
┌──────────────────────────┐  ┌──────────────────────────┐
│  CredentialMate          │  │  KareMatch               │
│  (Target App 1)          │  │  (Target App 2)          │
│                          │  │                          │
│  ┌────────────────────┐  │  │  ┌────────────────────┐  │
│  │ Feature Builders   │  │  │  │ QA Agents          │  │
│  │ (Dev Team agents)  │  │  │  │ (QA Team agents)   │  │
│  └────────────────────┘  │  │  └────────────────────┘  │
│  ├─ Session State       │  │  ├─ Session State       │  │
│  ├─ Work Queue (sync)   │  │  ├─ Work Queue (sync)   │  │
│  └─ Task Execution      │  │  └─ Bug Discovery       │  │
└──────────────────────────┘  └──────────────────────────┘
```

### Data Flow

```
Task in CredentialMate
  ↓
AI_Orchestrator receives via API
  ↓
Creates work item in central SQLite
  ↓
Routes to appropriate team (Dev/Ops/QA)
  ↓
Team agent starts work
  ↓
Each iteration:
  - SessionState.save() → .aibrain/session-{id}.md
  - WorkQueue.checkpoint() → SQLite
  - Decision logged → .aibrain/decisions/{id}.jsonl
  ↓
AI_Orchestrator syncs state to CredentialMate (via API)
  ↓
On completion:
  - KO created from multi-iteration learning
  - Effectiveness tracked
  - Cross-repo learning available

Next task benefits from previous learnings!
```

---

## Shared Infrastructure

### Files (Shared Between Repos)

```
orchestration/session_state.py      ← Shared (identical in both)
orchestration/decision_log.py        ← Shared
knowledge/approved/*.md             ← Shared (central KO store)
knowledge/service.py                ← Shared
.aibrain/decisions/*.jsonl          ← Shared
governance/contracts/*.yaml         ← Shared (autonomy rules)
```

**Synchronization Strategy**:
- Symbolic links OR
- Git submodule OR
- Shared Python package (most maintainable)

### Recommended: Shared Python Package

```
ai-orchestrator-core/
├─ __init__.py
├─ session_state.py          (Phase 1)
├─ work_queue.py             (Phase 2)
├─ decision_log.py           (Phase 3)
├─ knowledge_service.py      (Phase 4)
└─ requirements.txt

# Both repos import:
from aio_core import SessionState, WorkQueue, DecisionLog
```

**Benefits**:
- ✅ Single source of truth
- ✅ Versioned in pip
- ✅ Easy to update both repos
- ✅ Clear dependency management

---

## Repository-Specific Customizations

### AI_Orchestrator Only

```python
# Orchestration features
├─ autonomous_loop.py         (multi-team coordination)
├─ team_router.py            (route to QA/Dev/Ops)
├─ council_pattern.py        (debate system)
├─ ralph/checker.py          (verification)
└─ governance/contracts/     (autonomy levels)

# No target repo execution - pure orchestration
```

### CredentialMate Only

```python
# Application-specific features
├─ models/                   (domain models)
├─ api/                      (REST endpoints)
├─ database/                 (PostgreSQL)
├─ lambda_handlers/          (AWS Lambda)
└─ tasks/                    (task definitions)

# Receives work from AI_Orchestrator
# Executes via agents from orchestrator
```

---

## Budget & Timeline

### Phase 1: Session State (1 week)
- **AI_Orchestrator**: 5 days integration + testing
- **CredentialMate**: 2 days integration + testing
- **Total**: 1 week
- **Status**: ✅ Ready to start

### Phase 2: Work Queue (2-3 weeks)
- **Design**: 3 days (unified schema)
- **Implementation**: 7 days (SQLite + sync)
- **Integration**: 5 days (both repos)
- **Testing**: 3 days
- **Total**: 2-3 weeks

### Phase 3: Decision Trees (2 weeks)
- **Both repos**: 2 weeks (shared implementation)

### Phase 4: KO Enhancements (2-3 weeks)
- **Semantic search**: 1-2 weeks (both benefit)
- **Session references**: 1 week
- **Effectiveness tracking**: 3 days

### Phase 5: Testing (2 weeks)
- **Integration**: 2 weeks

**Grand Total**: 8-10 weeks for full implementation

---

## Success Criteria

### Phase 1 (Session State)
- [ ] Both repos can checkpoint and resume
- [ ] 23/23 tests passing in both contexts
- [ ] IterationLoop integration complete
- [ ] Real task testing successful

### Phase 2 (Work Queue)
- [ ] Unified schema implemented
- [ ] Cross-repo coordination working
- [ ] Sync mechanism tested
- [ ] No data loss on failures

### Phase 3 (Decision Trees)
- [ ] All governance decisions logged
- [ ] HIPAA audit trail complete
- [ ] Replay capability working
- [ ] 100% compliance achieved

### Phase 4 (KO Enhancements)
- [ ] Semantic search 20-30% improvement
- [ ] Cross-repo learning enabled
- [ ] Effectiveness tracking accurate
- [ ] Auto-ranking working

### Phase 5 (Integration)
- [ ] Full end-to-end tests passing
- [ ] Cost tracking accurate
- [ ] Multi-team execution smooth
- [ ] Performance targets met

---

## Risk Mitigation

### Shared Code Changes
**Risk**: Breaking both repos if shared code changes
**Mitigation**:
- Version shared package semantically
- Pin versions in both repos
- Test both before releasing update
- Rollback plan if issues

### Cross-Repo Coordination
**Risk**: State desync between repos
**Mitigation**:
- Checksums on all state files
- Sync verification (compare counts, hashes)
- Conflict resolution strategy
- Regular audit runs

### HIPAA Compliance
**Risk**: Decision logs expose sensitive data
**Mitigation**:
- Audit logs don't contain PII
- Encryption at rest
- Access control per team
- Regular compliance validation

---

## Next Steps

### Immediate (This Week)
1. [ ] Review this strategy with both teams
2. [ ] Decide on shared infrastructure approach (Python package vs symlink vs submodule)
3. [ ] Clarify cross-repo API boundaries
4. [ ] Start Phase 1 integration in both repos

### Short Term (Weeks 1-2)
1. [ ] Complete Phase 1 integration (IterationLoop + CredentialMate task runner)
2. [ ] Test with real tasks in both repos
3. [ ] Begin Phase 2 design (unified work queue schema)

### Medium Term (Weeks 3-8)
1. [ ] Implement Phases 2-4
2. [ ] Test cross-repo coordination
3. [ ] Measure improvements (speed, cost, learning)
4. [ ] Optimize based on data

---

## Summary

This strategy enables:

✅ **AI_Orchestrator**: Central orchestration with unified memory
✅ **CredentialMate**: Autonomous task execution with learning
✅ **Shared**: Session state, work queue, KO system, decision audit
✅ **Coordinated**: Tasks flow from CredentialMate → AI_Orchestrator → execution
✅ **Intelligent**: Cross-repo learning improves both systems
✅ **Compliant**: HIPAA audit trails, governance enforcement
✅ **Measurable**: Cost tracking, effectiveness metrics, performance data

**Timeline**: 8-10 weeks from Phase 1 integration to full system ready
**Budget**: 3-4 engineers, estimated 400-500 hours total
**ROI**: Unlimited task complexity, true autonomous operation, 80% token savings, institutional learning

---

**Document Status**: Ready for review and approval
**Next Action**: Schedule implementation kickoff meeting
**Questions**: See cross-repo coordination model diagram for clarification

