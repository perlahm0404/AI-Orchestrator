# AI Orchestrator v9.0 - Stateless Memory Architecture Diagram

## System Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                    CREDENTIALMATE AUTONOMOUS SYSTEM                    │
│                         (Context-Independent)                          │
└────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────┐
                    │   AGENT (Stateless)     │
                    │                         │
                    │ • Zero internal memory  │
                    │ • Reconstructs on init  │
                    │ • Executes iteration    │
                    │ • Checkpoints progress  │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
                 ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │   SESSION    │ │  WORK QUEUE  │ │   KNOWLEDGE  │
        │   STATE      │ │  (SQLite)    │ │   OBJECTS    │
        │ (Markdown)   │ │              │ │  (KO System) │
        └──────────────┘ └──────────────┘ └──────────────┘
                │               │               │
                ▼               ▼               ▼
        .aibrain/       tasks/           knowledge/
        session-        work_queue       approved/
        {id}.md         {proj}.db        KO-*.md


    ┌──────────────────────────────────────────────────────────┐
    │         Execution Loop: No Context Window Limits          │
    └──────────────────────────────────────────────────────────┘

    Context 1 (0-3,847 tokens)     Context 2 (0-3,847 tokens)
    ┌──────────────────────┐       ┌──────────────────────┐
    │ 1. Load session      │       │ 1. Load session      │
    │ 2. Iterations 1-5    │       │ 2. Iterations 6-10   │
    │ 3. Checkpoint (500b) │──────→│ 3. Checkpoint (500b) │
    │ [Context exhausted]  │       │ [Task complete]      │
    └──────────────────────┘       └──────────────────────┘
            │                              │
            ▼                              ▼
    Save: session-{id}.md         Update: work_queue.db
    Create KO draft               Create KO final
    Log decision tree             Mark task complete
```

---

## Data Flow: Task Execution Across Contexts

```
TASK: "Build user authentication module"
├─ ID: TASK-123
├─ Project: credentialmate
├─ Status: pending
└─ Max iterations: 50


CONTEXT 1 (Iteration 1-5)
│
├─ [STARTUP]
│  ├─ Load: work_queue[TASK-123]
│  ├─ Load: session-TASK-123.md (if exists)
│  ├─ Load: KOs matching ["auth", "jwt", "oauth"]
│  ├─ Reconstruct context (~600 tokens)
│  └─ Status: "Resuming iteration 0" or "Starting new"
│
├─ [ITERATIONS 1-5]
│  ├─ Iter 1: Agent designs architecture (PASS)
│  ├─ Iter 2: Agent implements tokens (PASS)
│  ├─ Iter 3: Agent tests tokens (FAIL) → retry
│  ├─ Iter 4: Agent fixes token bug (PASS)
│  └─ Iter 5: Agent adds OAuth2 (FAIL) → blocked
│
├─ [CHECKPOINT after iteration 5]
│  ├─ Save: .aibrain/session-TASK-123.md
│  │         ├─ iteration_count: 5
│  │         ├─ phase: "auth_implementation"
│  │         ├─ status: "blocked"
│  │         ├─ last_output: "OAuth2 requires external service"
│  │         └─ next_steps: ["Resolve OAuth blocker", "Add tests"]
│  │
│  ├─ Update: work_queue.db
│  │         ├─ TASK-123.iteration_count = 5
│  │         ├─ TASK-123.status = "blocked"
│  │         ├─ TASK-123.session_ref = "SESSION-xxx"
│  │         └─ checkpoint[5] = (verdict:"BLOCKED", timestamp, ...)
│  │
│  ├─ Log: .aibrain/decisions/TASK-123.jsonl
│  │       + {"decision": "APPROACH", "value": "jwt_tokens"}
│  │       + {"decision": "BLOCKER", "value": "oauth_external"}
│  │
│  └─ Create: knowledge/drafts/KO-cm-123.md
│             "JWT token implementation pattern"
│
└─ [CONTEXT EXHAUSTED - PAUSE]


HUMAN DECISION (Outside context)
│
├─ Reads: .aibrain/session-TASK-123.md
├─ Understands: OAuth blocker
├─ Decides: "Use internal OAuth2 mock for now"
└─ Updates: work_queue.db
           └─ decision = "USE_OAUTH_MOCK"


CONTEXT 2 (Iteration 6-12)
│
├─ [STARTUP]
│  ├─ Load: work_queue[TASK-123]
│  │        → iteration_count: 5, status: "blocked"
│  ├─ Load: session-TASK-123.md
│  │        → last_output: "OAuth2 requires external service"
│  │        → next_steps: ["Resolve OAuth blocker", "Add tests"]
│  ├─ Load: decision from work_queue
│  │        → "USE_OAUTH_MOCK"
│  ├─ Load: Top 1-2 KOs about OAuth
│  ├─ Reconstruct context (~600 tokens)
│  └─ Status: "Resuming iteration 6 after human decision"
│
├─ [ITERATIONS 6-12]
│  ├─ Iter 6: Agent applies human decision (PASS)
│  ├─ Iter 7: Agent adds OAuth mock (PASS)
│  ├─ Iter 8: Agent writes integration tests (PASS)
│  ├─ Iter 9: Agent fixes test failures (PASS)
│  ├─ Iter 10: Agent updates documentation (PASS)
│  ├─ Iter 11: Agent security review (PASS)
│  └─ Iter 12: Agent final integration test (PASS) → COMPLETE
│
├─ [FINAL CHECKPOINT after iteration 12]
│  ├─ Save: .aibrain/session-TASK-123.md (final version)
│  ├─ Update: work_queue.db
│  │         └─ status = "completed"
│  ├─ Archive: Move session to .aibrain/sessions/archive/
│  ├─ Create: knowledge/approved/KO-cm-123.md
│  │          "Complete auth implementation with JWT + OAuth mock"
│  └─ Update: metrics
│            ├─ total_iterations: 12
│            ├─ contexts_used: 2
│            ├─ tokens_saved: 3,400 × 2 = 6,800
│            └─ effectiveness: (12 iter / 50 max) = 24% of budget
│
└─ [COMPLETE]


RESULT: Task completed in 2 contexts, 12 iterations
        - Full audit trail in work_queue.db
        - Session files show exact progress
        - Knowledge Objects preserve learning
        - Decision tree shows how we got here
```

---

## Memory Storage Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL MEMORY LAYER (Persistent)             │
│                   (Survives context resets)                 │
└─────────────────────────────────────────────────────────────┘

1. SESSION STATE FILES
   ────────────────────
   Location: .aibrain/session-{task_id}.md
   Format:   Markdown with JSON frontmatter
   Update:   After every iteration
   Size:     ~5-20 KB per task (split if > 50KB)
   Reads:    Fast (< 50ms)

   Example:
   ---
   {
     "id": "SESSION-2026-02-07-001",
     "task_id": "TASK-123",
     "iteration_count": 5,
     "phase": "auth_implementation",
     "status": "blocked",
     "next_steps": ["resolve_oauth", "add_tests"]
   }
   ---
   ## Progress
   - ✅ Design auth architecture
   - ✅ Implement JWT tokens
   - 🔄 Test OAuth flow (blocked)


2. WORK QUEUE
   ───────────
   Location: tasks/work_queue_credentialmate.db (SQLite)
   Fallback: tasks/work_queue_credentialmate.json (git-friendly)

   Tables:
   ┌─────────────────┐     ┌───────────────────┐
   │ work_items      │     │ checkpoints       │
   ├─────────────────┤     ├───────────────────┤
   │ id              │     │ task_id           │
   │ task_id         │     │ iteration_count   │
   │ status ◄────────┼─────│ verdict (PASS/... │
   │ session_ref     │     │ timestamp         │
   │ retry_count     │     │ recoverable       │
   │ error_log       │     └───────────────────┘
   └─────────────────┘

   Queries (< 100ms):
   - Get next pending: SELECT * FROM work_items WHERE status='pending'
   - Get blocked tasks: SELECT * FROM work_items WHERE status='blocked'
   - Get task history: SELECT * FROM checkpoints WHERE task_id=?
   - Get retry count: SELECT retry_count FROM work_items WHERE id=?


3. KNOWLEDGE OBJECTS
   ──────────────────
   Location: knowledge/approved/*.md, knowledge/drafts/*.md
   Format:   Markdown with JSON frontmatter + content

   Pre-execution Consultation:
   ┌──────────────────────────────┐
   │ Task: "Fix auth bug"         │
   │ Tags: ["auth", "bug", "jwt"] │
   └────────────┬─────────────────┘
                │
                ├─→ KO-cm-001: "JWT token validation patterns"
                ├─→ KO-cm-005: "Common OAuth2 mistakes"
                └─→ KO-cm-012: "HIPAA auth compliance"
                    [Loaded into context before agent starts]

   Post-execution Learning:
   ┌──────────────────────────────┐
   │ Task completed after 6 iters │
   └────────────┬─────────────────┘
                │
                └─→ Auto-create draft KO
                    └─→ "How to fix token validation"
                    └─→ Source: SESSION-xxx
                    └─→ Tags: ["auth", "jwt", "validation"]


4. DECISION TREES
   ───────────────
   Location: .aibrain/decisions/{task_id}.jsonl
   Format:   JSONL (one decision per line, append-only)

   Example entries:
   {"timestamp":"2026-02-07T10:00:00Z","decision":"APPROACH","value":"jwt_tokens","confidence":0.9}
   {"timestamp":"2026-02-07T10:15:00Z","decision":"BLOCKER","value":"oauth_external","severity":"high"}
   {"timestamp":"2026-02-07T10:30:00Z","decision":"HUMAN_OVERRIDE","value":"use_oauth_mock"}

   Use cases:
   - Replay: Understand how decisions evolved
   - Audit: Full trail of critical choices
   - Learning: Why we chose X over Y
```

---

## Performance Characteristics

```
Operation                  Target    Status   Notes
─────────────────────────────────────────────────────────────
Session save               < 100ms   Design   After each iteration
Session load               < 50ms    Design   Only session + decision
Work queue query           < 100ms   Design   Cached, indexed
KO consultation            < 200ms   Design   Top 1-3 KOs only
Full startup               < 2 min   Design   Reconstruct context
Checkpoint latency         < 200ms   Design   Per iteration overhead
─────────────────────────────────────────────────────────────

Token Usage Comparison:
─────────────────────────────────────────────────────────────
Scenario              Before    After    Savings
─────────────────────────────────────────────────────────────
Single iteration      4,000t    600t     3,400 (85%)
5-iteration task      20,000t   3,000t   17,000 (85%)
10-iteration task     40,000t   6,000t   34,000 (85%)
─────────────────────────────────────────────────────────────

Why such large savings?
- Before: Must load full conversation history + all code
- After: Load only summary + current phase + top KOs
```

---

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│              SYSTEM INTEGRATION LAYER                       │
└─────────────────────────────────────────────────────────────┘

ITERATION LOOP (orchestration/iteration_loop.py)
│
├─ Pre-execution:
│  ├─ Load session state (if resuming)
│  ├─ Consult knowledge objects
│  └─ Initialize agent context
│
├─ Mid-iteration:
│  └─ Agent executes work
│
└─ Post-iteration:
   ├─ Save session state → .aibrain/session-{id}.md
   ├─ Update work queue → SQLite checkpoint
   ├─ Log decision → .aibrain/decisions/{id}.jsonl
   └─ Create draft KO (if ≥2 iterations)


AUTONOMOUS LOOP (autonomous_loop.py)
│
├─ Get next task → work_queue.db
├─ Resume if possible → Load session
├─ Run iteration loop
├─ Update status → work_queue.db
└─ Continue to next task


RALPH VERIFICATION (ralph/verification.py)
│
├─ Verify result
├─ Log verdict → work_queue checkpoint
├─ Create KO (if PASS + multi-iteration)
└─ Update task status


KNOWLEDGE SERVICE (knowledge/service.py)
│
├─ Pre-execution: find_relevant(tags)
├─ Post-execution: create_draft_ko(task, history)
└─ Auto-approve (if PASS + 2-10 iterations)
```

---

## Deployment Architecture

```
CURRENT (Context-Dependent)           FUTURE (Context-Independent, v9.0)
────────────────────────────────      ──────────────────────────────────

Agent    │ Context Window              Agent    │ Minimal Context
 (4-8k)  │ ├─ Task desc                         │ ├─ Task desc (100t)
         │ ├─ History (2k)                      │ ├─ Phase (50t)
         │ ├─ Errors (1k)                       │ ├─ Next steps (100t)
         │ ├─ Code (1k)                         │ ├─ Top KOs (250t)
         │ └─ State (500t)                      │ └─ Decision (50t)
         │ TOTAL: 4,600t                        │ TOTAL: 550t
         │                                      │
         ▼                                      ▼
    [Context exhausted]                   [Plenty of room]
    [Memory lost]                         [Can continue]

    [Continue? Need new session]           [Continue naturally]
                                          [Save → External]
                                          [Resume → Reconstruct]
```

---

## Success Metrics

```
Metric                          Target      How Measured
────────────────────────────────────────────────────────────────
Context Independence            95%+        Tasks complete in <2 contexts
Token Savings                   80%+        tokens_before / tokens_after
Resume Success Rate             99%+        Successful resumes / total resumes
State Accuracy                  100%        Reconstructed == actual
Startup Time                    < 2 min     Time to start iteration
Query Performance               < 100ms     work_queue queries
Scalability                     1000s tasks 50+ tasks concurrent
────────────────────────────────────────────────────────────────
```

---

## Implementation Timeline

```
Phase 1: Session State        Week 1 (40h)  ✅ ESSENTIAL
├─ Save/load logic
├─ Markdown file format
├─ IterationLoop integration
└─ Basic tests (20+)

Phase 2: Work Queue           Week 2 (30h)  ✅ ESSENTIAL
├─ SQLite schema
├─ Checkpoint logic
├─ AutonomousLoop integration
└─ Query tests (15+)

Phase 3: Decision Trees       Week 3 (20h)  Optional (audit trail)
├─ JSONL logging
├─ Replay capability
└─ Tests (10+)

Phase 4: KO Enhancements      Week 4 (15h)  Optional (learning)
├─ Session references
├─ Effectiveness tracking
└─ Tests (5+)

Phase 5: Testing & Validation Week 5 (25h)  ✅ CRITICAL
├─ Integration tests (20+)
├─ Scenario tests (10+)
├─ Long-running task tests
└─ Performance benchmarks
```

---

## Risk Mitigation

```
Risk                    Impact  Probability  Mitigation
───────────────────────────────────────────────────────────────
State desync            High    Low          Checksums + validation
Large session files     Med     Med          Auto-split at 50KB
Query performance       Low     Low          Indexes + caching
Complexity              Med     Med          Clear separation, docs
────────────────────────────────────────────────────────────────
```

---

## Architecture Comparison

```
v6.0: Context-Dependent        v9.0: Context-Independent (Stateless)
──────────────────────         ──────────────────────────────────────

Memory:   In context           Memory:   External (files + DB)
State:    Lost on reset        State:    Always reconstructed
Token use: 4,000/context       Token use: 600/context (80% saving)
Tasks:    Limited by context   Tasks:    Unlimited contexts
Learning: Lost                 Learning: Captured in KOs
Audit:    Implicit             Audit:    Explicit (decision trees)
Resume:   Manual               Resume:   Automatic
────────────────────────────  ──────────────────────────────────────

v9.0 enables unlimited task complexity + true autonomous operation
```

---

## File References

**Design Documents**:
- [`sessions/credentialmate/active/20260207-stateless-memory-architecture.md`](../sessions/credentialmate/active/20260207-stateless-memory-architecture.md) - Full architecture
- [`docs/stateless-memory-quick-reference.md`](./stateless-memory-quick-reference.md) - Quick guide + examples
- [`docs/phase-1-session-state-implementation.md`](./phase-1-session-state-implementation.md) - Phase 1 spec

**Implementation**:
- `orchestration/session_state.py` (to be created)
- `db/work_queue.py` (to be created)
- `orchestration/decision_log.py` (to be created)

**Integration Points**:
- `orchestration/iteration_loop.py` (modify)
- `autonomous_loop.py` (modify)
- `knowledge/service.py` (enhance)

---

**Created**: 2026-02-07
**Version**: v9.0 Architecture
**Status**: Design Phase
**Next**: Review → Clarify Questions → Implement Phase 1

