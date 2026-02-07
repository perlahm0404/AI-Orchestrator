# Stateless Memory Architecture - Quick Reference

**TL;DR**: Make agents work without relying on conversation context by externalizing ALL memory to files and databases.

---

## The Problem

**Current state**: Agent memory lives in context window
```
Context Window (4K-8K tokens)
├─ Task description
├─ Previous conversation
├─ Work-in-progress state
└─ Error logs
        ↓
      [Context exhausted?]
      [Agent loses memory!]
```

**After stateless**: Memory is always external
```
Agent (stateless)  →  Session File (.md)
Agent (stateless)  →  Work Queue (SQLite)
Agent (stateless)  →  Knowledge Objects
Agent (stateless)  →  Decision Trees (.jsonl)
Agent (stateless)  →  Error Logs
```

---

## Four Memory Stores

### 1. Session State Files (`.aibrain/session-{task_id}.md`)

**What**: Markdown files with task progress

**When to use**: Track current phase, iteration count, recent decisions

**Example**:
```markdown
---
{
  "task_id": "TASK-123",
  "iteration_count": 5,
  "phase": "feature_build",
  "status": "in_progress"
}
---

## Progress
- ✅ Phase 1: [done]
- 🔄 Phase 2: [working on]
- ⏳ Phase 3: [not started]

## Latest Output
[Summary of what agent just did]

## Next Steps
1. [Do this]
2. [Then this]
3. [Finally this]
```

**Benefits**:
- Human readable (git-friendly)
- Fast to read/write
- Can split if too large

---

### 2. Work Queue (SQLite + JSON)

**What**: Persistent task tracking

**When to use**: Find next task, track retries, checkpoint progress

**Schema**:
```sql
CREATE TABLE work_items (
  id TEXT PRIMARY KEY,
  task_id TEXT,
  status TEXT,  -- pending, in_progress, blocked, completed
  retry_count INTEGER,
  session_ref TEXT,  -- Points to SESSION-{id}
  error_log TEXT
);

CREATE TABLE checkpoints (
  task_id TEXT,
  iteration_count INTEGER,
  verdict TEXT,  -- PASS, BLOCKED, RETRY
  timestamp TIMESTAMP
);
```

**Query Examples**:
```python
# Get next task
task = queue.get_next_pending()

# Resume interrupted task
session = queue.load_session(task.session_ref)

# Checkpoint after iteration
queue.checkpoint(task_id, iteration_count=5, verdict="BLOCKED")

# Mark complete
queue.mark_complete(task_id)
```

**Benefits**:
- Powerful queries (find blocked tasks, retry stats)
- Transaction safety
- Full audit trail

---

### 3. Knowledge Objects (Existing System)

**What**: Institutional memory that survives sessions

**When to use**: Pre-execution (learn from past), post-execution (capture new learning)

**How it works**:
```
Before task:
  relevant_kos = find_relevant(tags_from_task_description)
  agent.context += format_kos(relevant_kos)

After task (if ≥2 iterations):
  create_draft_ko(
    title="What we learned",
    tags=["typescript", "auth"],
    learning="How to fix this pattern"
  )
```

**Benefits**:
- Survives across repos/sessions
- 457x speedup with caching
- Auto-approval for high-confidence learnings

---

### 4. Decision Trees (JSONL Logs)

**What**: Append-only log of critical decisions

**When to use**: Audit trail, understanding why we chose approach A over B

**Example**:
```jsonl
{"timestamp": "2026-02-07T10:00:00Z", "decision": "APPROACH", "value": "incremental_refactor", "reasoning": "...", "confidence": 0.87}
{"timestamp": "2026-02-07T10:15:00Z", "decision": "GUARDRAIL_OVERRIDE", "value": true, "requires_approval": true}
```

**Benefits**:
- Immutable record
- Easy to replay
- Supports human audit

---

## Execution Flow (Context-Independent)

```
┌─────────────────────────────────────────────────────────┐
│ Context 1: Agent Starts                                 │
│ 1. Load session file (.aibrain/session-{task_id}.md)   │
│ 2. Load work queue entry (SQLite)                       │
│ 3. Load relevant KOs (knowledge/approved/)              │
│ 4. Load decision tree (if exists)                       │
│ 5. Reconstruct minimal context (~500 tokens)            │
│ 6. Agent does work (iterations 1-5)                     │
│ 7. Checkpoint after iteration 5 (save state)            │
└──────────────────────┬──────────────────────────────────┘
                       │ [Context exhausted]
                       ↓
┌─────────────────────────────────────────────────────────┐
│ Context 2: Agent Resumes                                │
│ 1. Load session file (now has iteration 5 state)        │
│ 2. Continue from iteration 6-10                         │
│ 3. Checkpoint again                                     │
└──────────────────────┬──────────────────────────────────┘
                       │ [Still blocked]
                       ↓
┌─────────────────────────────────────────────────────────┐
│ Context 3: Human Decision + Continue                    │
│ 1. Load session + decision queue entry                  │
│ 2. Apply human decision                                 │
│ 3. Continue work (iterations 11-15)                     │
│ 4. Task complete → mark done in queue                   │
└─────────────────────────────────────────────────────────┘
```

**Key insight**: Each context can be fresh. Agent reconstructs state from external stores.

---

## Context Window Budget

**Before** (context-dependent):
- Task desc: 500 tokens
- Conversation history: 2,000 tokens
- Error logs: 1,000 tokens
- Code: 500 tokens
- **Total**: 4,000 tokens (75% of 5.5K limit)

**After** (stateless):
- Task desc: 300 tokens
- Current phase + next steps: 200 tokens
- Top 1-2 KOs: 100 tokens
- **Total**: 600 tokens (11% of budget)

**Savings**: ~3,400 tokens per context (80% reduction)

---

## Implementation Checklist

### Week 1: Session State Files
- [ ] Create `orchestration/session_state.py`
- [ ] Add save/load methods
- [ ] Integrate with `IterationLoop.run()`
- [ ] Integrate with `autonomous_loop.py`
- [ ] Test save/load/resume

### Week 2: Work Queue Persistence
- [ ] Create `db/models.py` (SQLAlchemy)
- [ ] Create `db/work_queue.py` (manager)
- [ ] Create migrations (Alembic)
- [ ] Integrate with `autonomous_loop.py:get_next_task()`
- [ ] Sync with `tasks/work_queue_{project}.json`

### Week 3: Decision Logging
- [ ] Create `orchestration/decision_log.py`
- [ ] Add decision logging in agent code
- [ ] Add guardrail decision logging
- [ ] Create replay capability

### Week 4: KO Enhancements
- [ ] Add session references to KO metadata
- [ ] Track consultation metrics
- [ ] Enhanced effectiveness tracking

### Week 5: Testing
- [ ] 20+ unit tests
- [ ] 20+ integration tests
- [ ] Scenario: task spanning 5+ contexts
- [ ] Scenario: context reset recovery

---

## Code Examples

### Save Session State

```python
# orchestration/session_state.py

from datetime import datetime
import yaml
import json

class SessionState:
    def __init__(self, task_id: str, project: str):
        self.task_id = task_id
        self.project = project
        self.file_path = f".aibrain/session-{task_id}.md"

    def save(self, data: dict):
        frontmatter = json.dumps({
            "task_id": self.task_id,
            "project": self.project,
            "updated_at": datetime.now().isoformat(),
            **data
        }, indent=2)

        content = f"""---
{frontmatter}
---

{data.get('markdown_content', '')}
"""
        with open(self.file_path, 'w') as f:
            f.write(content)

    @classmethod
    def load(cls, task_id: str):
        file_path = f".aibrain/session-{task_id}.md"
        with open(file_path, 'r') as f:
            content = f.read()

        # Parse frontmatter
        parts = content.split('---')
        frontmatter = json.loads(parts[1].strip())
        markdown = parts[2].strip() if len(parts) > 2 else ""

        return {**frontmatter, "markdown_content": markdown}
```

### Checkpoint in IterationLoop

```python
# orchestration/iteration_loop.py

class IterationLoop:
    def run(self, task_id, task_description):
        # Load session state
        session = SessionState.load(task_id)
        iteration_count = session.get('iteration_count', 0)

        while iteration_count < self.max_iterations:
            # Do work
            result = self.agent.execute(task_description)
            iteration_count += 1

            # Checkpoint
            session.save({
                "iteration_count": iteration_count,
                "last_output": summarize(result),
                "verdict": result.verdict,
                "markdown_content": self._format_session_markdown(session, result)
            })

            # Check completion
            if result.verdict == "PASS":
                break
            elif result.verdict == "BLOCKED":
                break  # Wait for human decision
```

### Resume in Autonomous Loop

```python
# autonomous_loop.py

class AutonomousLoop:
    def run(self):
        while True:
            # Get next task
            queue = WorkQueue(self.project)
            task = queue.get_next_ready()

            if not task:
                break  # Nothing to do

            # Load previous session (if resuming)
            if task.session_ref:
                session = SessionState.load(task.task_id)
                iteration_count = session['iteration_count']
            else:
                iteration_count = 0

            # Run iteration
            result = self.iteration_loop.run(
                task.task_id,
                task.description,
                starting_iteration=iteration_count
            )

            # Update queue
            queue.checkpoint(
                task_id=task.task_id,
                iteration_count=result.iteration_count,
                verdict=result.verdict
            )
```

---

## Testing Strategy

### Test: Basic Save/Load
```python
def test_session_save_load():
    session = SessionState("TASK-123", "credentialmate")
    session.save({
        "iteration_count": 5,
        "phase": "feature_build",
        "markdown_content": "## Progress\n✅ Done"
    })

    loaded = SessionState.load("TASK-123")
    assert loaded['iteration_count'] == 5
    assert loaded['phase'] == "feature_build"
```

### Test: Context Reset Recovery
```python
async def test_resume_after_context_reset():
    # Start task
    task_id = await autonomous_loop.run_one_iteration()

    # Simulate context reset
    del autonomous_loop  # Kill the agent

    # Resume
    new_loop = AutonomousLoop()
    result = await new_loop.run_one_iteration()

    # Should resume from checkpoint
    assert result.task_id == task_id
    assert result.iteration_count > 0  # Continued from saved state
```

### Test: Long-Running Task
```python
async def test_task_spanning_multiple_contexts():
    # Mock context window limit
    for context_num in range(5):
        # Each context does 5 iterations
        for i in range(5):
            await autonomous_loop.do_iteration()

        # Simulate context exhaustion
        context_window_full = True

        # Checkpoint and move to next context
        await autonomous_loop.checkpoint()

    # Task should complete across 5+ contexts
    task = queue.get_task(task_id)
    assert task.status == "completed"
    assert task.iteration_count >= 25
```

---

## Monitoring & Observability

### Metrics to Track

```python
# Monitor stateless memory system health

class MemoryMetrics:
    # Session state
    session_save_time_ms: float  # Should be <100ms
    session_load_time_ms: float  # Should be <50ms
    session_file_size_kb: float  # Should be <50KB

    # Work queue
    checkpoint_latency_ms: float  # Should be <500ms
    query_latency_ms: float  # Should be <100ms

    # KO system
    ko_consultation_count: int  # How often consulted
    ko_effectiveness: float  # 0-1, success rate

    # Decisions
    decision_log_writes: int  # Checkpoint efficiency
    decision_replay_time_ms: float  # Recovery speed
```

### Example Dashboard Entry

```
SESSION STATE METRICS
├─ Active sessions: 23
├─ Avg checkpoint size: 18 KB
├─ Avg save latency: 45ms ✅
├─ Longest session: 156 iterations (TASK-42)
└─ Split sessions (>50KB): 3

WORK QUEUE METRICS
├─ Pending: 12
├─ In progress: 3
├─ Blocked: 5
├─ Query latency (95th): 78ms ✅
└─ Transaction conflicts: 0

RESUMPTION STATS
├─ Interruptions: 23
├─ Successful resumes: 23 (100%) ✅
├─ State mismatches: 0
└─ Avg resume startup: 1m 23s
```

---

## Common Patterns

### Pattern 1: Task Continuation
```python
# Check if task is resuming
if task.session_ref:
    session = load_session(task.session_ref)
    context = {
        "iteration_count": session['iteration_count'],
        "last_decision": session['last_decision'],
        "next_steps": session['next_steps']
    }
else:
    context = {"iteration_count": 0}
```

### Pattern 2: Blocked Task Handling
```python
# Wait for human decision
if task.status == "blocked":
    human_decision = queue.get_human_decision(task.id)
    if human_decision:
        # Update decision tree
        log_decision("USER_APPROVED", human_decision)
        # Unblock task
        queue.mark_ready(task.id)
```

### Pattern 3: Learning from Multi-Iteration Fix
```python
# After task complete
if iteration_count >= 2:
    # Extract learning
    ko = create_draft_ko(
        title="What we learned",
        tags=extract_tags(task.description),
        content=summarize_learning(iteration_history)
    )
    # Next agent benefits
```

---

## Troubleshooting

### Session file too large (>100KB)
**Solution**: Implement splitting logic
```python
if session_size > 50 * 1024:  # 50KB
    split_into_parts(session, part_size=50*1024)
```

### Startup too slow (>5 min)
**Solution**: Load lazily, cache more aggressively
```python
# Only load full state if resuming
if task.status == "in_progress":
    load_full_session()
else:
    load_summary_only()
```

### State mismatch after recovery
**Solution**: Add checksums to session
```python
session.save({
    "checksum": hashlib.md5(json.dumps(data).encode()).hexdigest(),
    ...
})

# On load, verify
if actual_checksum != expected_checksum:
    raise StateIntegrityError("Session file corrupted")
```

---

## Next Steps

1. **Review**: Get feedback on this architecture
2. **Design**: Session file format details
3. **Implement**: Phase 1 (session state files)
4. **Test**: Integration tests for resume scenarios
5. **Deploy**: Enable stateless mode in CredentialMate

---

**Created**: 2026-02-07
**Status**: Design Phase
**Estimated Effort**: 5 weeks (phase 1-5)
**Expected Benefit**: 95%+ context independence + unlimited task complexity

