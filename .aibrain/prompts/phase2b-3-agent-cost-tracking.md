# Phase 2B-3: Agent Cost Tracking System (CLI Mode)

## Your Role

You are the TeamLead agent for per-agent cost tracking. You will implement a cost tracking system that becomes the **SOURCE OF TRUTH** for all costs. Langfuse will read from YOUR tracker (preventing double-counting).

**Execution Mode**: Claude CLI Wrapper (no API key, OAuth-based)
**Merge Order**: SECOND (adds hooks to iteration_loop.py lines 957-1097)
**Status**: 45% complete (1,057 lines of tests exist, no implementation)

---

## Kanban Board Real-Time Integration ✅ ALREADY WIRED

Your work progress will **automatically stream to the kanban board** via WebSocket in real-time. As your cost tracker records operations, the events flow to the dashboard.

### Monitor Your Cost Tracking Progress

While implementing the cost tracking system:

```bash
# Terminal: Dashboard
npm run dev --prefix ui/dashboard

# Browser: http://localhost:3000
# Watch your specialist agent in kanban showing:
# - Implementation checkpoint every test/code/verify cycle
# - Cost operation recording (iteration, MCP tool, verification)
# - Final verdict when all 1,057 tests pass
```

### What Gets Streamed

As you work:
- **specialist_started** - Implementation begins
- **iteration_N** - Each TDD cycle (test, code, verify)
- **specialist_completed** - With final verdict (all tests pass)

The cost tracker will automatically record operations as other agents (IterationLoop) use it, and Langfuse will read from your tracker for the dashboard cost visualization.

---

## Exclusive Files (You Own These)

Create and own these files entirely:

1. **`orchestration/agent_cost_tracker.py`** (NEW - 200-300 lines)
   - `AgentCostTracker` class
   - `CostRecord` dataclass (defined in shared module)
   - Per-operation cost tracking
   - Multi-agent cost aggregation

---

## Existing Test Files

These files ALREADY EXIST with 1,057 lines of passing tests. Your implementation must pass all:

1. **`tests/test_agent_cost_tracking.py`** (726 lines)
   - 20+ test methods covering core tracker functionality
   - Tests for cost recording, aggregation, summaries

2. **`tests/test_specialist_cost_tracking.py`** (331 lines)
   - Tests for specialist-specific cost tracking
   - Multi-specialist aggregation tests

---

## Shared Files (Coordinate Carefully)

1. **`orchestration/iteration_loop.py`** (MODIFY lines 957-1097)
   - Add AgentCostTracker initialization
   - Record costs after each operation:
     - Iteration complete
     - MCP tool invocation
     - Ralph verification
   - Save cost summary to SessionState

2. **`orchestration/monitoring/operation_types.py`** (READ-ONLY)
   - Shared `OperationType` enum
   - Values: AGENT_EXECUTION, ITERATION, MCP_TOOL_CALL, etc.

3. **`orchestration/monitoring/cost_models.py`** (READ-ONLY)
   - Shared `CostRecord` dataclass
   - timestamp, cost_usd, operation_type, agent_type, project, etc.

4. **`orchestration/monitoring/config.py`** (READ-ONLY)
   - Check for cost tracking config section
   - Feature flag: `enable_cost_tracking`

---

## DO NOT TOUCH

These files are owned by other agents:

- `orchestration/monitoring/langfuse_integration.py` (Langfuse agent owns)
- `knowledge/semantic_search.py` (Chroma agent owns)
- `.aibrain/prompts/phase2b-*.md` (Other prompts - read-only)

---

## CRITICAL: Source of Truth Pattern

**You are the SOURCE OF TRUTH for costs**. Langfuse will read FROM YOUR TRACKER.

This prevents double-counting:

```python
# ❌ WRONG (double-counting):
cost = estimate_iteration_cost()
agent_cost_tracker.record_cost(cost)
langfuse_monitor.record_cost(cost)  # Double!

# ✅ CORRECT (single source):
agent_cost_tracker.record_cost(cost)  # You record once
cost = agent_cost_tracker.get_operation_cost(OperationType.ITERATION)
langfuse_monitor.record_cost(trace_id, cost)  # Langfuse reads from you
```

---

## Implementation Requirements

### 1. Implement AgentCostTracker

Create `orchestration/agent_cost_tracker.py`:

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from orchestration.monitoring.operation_types import OperationType
from orchestration.monitoring.cost_models import CostRecord

class AgentCostTracker:
    """
    Source of truth for agent costs.

    Tracks all operations and costs for a single agent execution.
    Langfuse reads from this tracker (no independent cost estimation).
    """

    def __init__(
        self,
        agent_type: str,
        project: str,
        session_id: str
    ):
        """
        Initialize cost tracker.

        Args:
            agent_type: Type of agent (e.g., "bugfix", "featurebuilder")
            project: Project name (e.g., "credentialmate")
            session_id: Unique session identifier
        """
        self.agent_type = agent_type
        self.project = project
        self.session_id = session_id
        self._cost_records: List[CostRecord] = []
        self._total_cost: float = 0.0

    def record_operation_cost(
        self,
        operation_type: OperationType,
        cost_usd: float,
        duration_ms: float = 0.0,
        metadata: Optional[Dict] = None
    ) -> None:
        """Record cost for an operation."""
        record = CostRecord(
            trace_id=self.session_id,
            operation_type=operation_type.value,
            cost_usd=cost_usd,
            agent_type=self.agent_type,
            project=self.project,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        self._cost_records.append(record)
        self._total_cost += cost_usd

    def get_total_cost(self) -> float:
        """Get total cost for all operations."""
        return self._total_cost

    def get_operation_cost(self, operation_type: OperationType) -> float:
        """Get total cost for specific operation type (for Langfuse to read)."""
        return sum(
            r.cost_usd for r in self._cost_records
            if r.operation_type == operation_type.value
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get complete cost summary for SessionState."""
        return {
            "agent_type": self.agent_type,
            "project": self.project,
            "session_id": self.session_id,
            "total_cost_usd": self._total_cost,
            "by_operation": self._cost_breakdown(),
            "record_count": len(self._cost_records),
            "records": [r.to_dict() for r in self._cost_records]
        }

    def _cost_breakdown(self) -> Dict[str, float]:
        """Get cost breakdown by operation type."""
        breakdown = {}
        for record in self._cost_records:
            op = record.operation_type
            breakdown[op] = breakdown.get(op, 0.0) + record.cost_usd
        return breakdown

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return self.get_summary()
```

### 2. Integrate with IterationLoop (lines 957-1097)

In `orchestration/iteration_loop.py`, add cost tracking hooks:

```python
# In IterationLoop.__init__():
from orchestration.agent_cost_tracker import AgentCostTracker
from orchestration.monitoring.operation_types import OperationType

self.cost_tracker = AgentCostTracker(
    agent_type=agent.agent_type if hasattr(agent, 'agent_type') else "unknown",
    project=self.app_context.project_name if self.app_context else "unknown",
    session_id=task_id
)

# After each iteration completes:
self.cost_tracker.record_operation_cost(
    operation_type=OperationType.ITERATION,
    cost_usd=estimated_cost,  # Use provided estimate
    duration_ms=iteration_duration_ms,
    metadata={
        "iteration": current_iteration,
        "status": verdict.type.value
    }
)

# Save to SessionState:
if self.session:
    session_data = self.session.get_latest()
    session_data["cost_tracking"] = self.cost_tracker.get_summary()
    self.session.save(session_data)
```

### 3. Pass All Existing Tests

These 1,057 lines of tests MUST pass:

1. `tests/test_agent_cost_tracking.py` (726 lines)
   - Test cost recording
   - Test aggregation
   - Test cost summaries
   - Test per-operation costs

2. `tests/test_specialist_cost_tracking.py` (331 lines)
   - Test specialist-specific tracking
   - Test multi-specialist aggregation
   - Test cost efficiency metrics

Run tests:
```bash
pytest tests/test_agent_cost_tracking.py tests/test_specialist_cost_tracking.py -v
```

All 1,057 lines must pass (no failures allowed).

---

## Dependencies

**None (independent implementation)**

- Does NOT depend on Chroma
- Does NOT depend on Langfuse
- Provides data that Langfuse will consume

**Blocks**: Langfuse (2B-1) - Langfuse must read from your tracker

---

## Success Criteria

- [ ] All 1,057 lines of tests passing (100% success)
- [ ] AgentCostTracker implemented and working
- [ ] IterationLoop integration complete (lines 957-1097)
- [ ] Cost data saved to SessionState
- [ ] Multi-agent cost aggregation working
- [ ] Langfuse-ready API (get_operation_cost method)
- [ ] No cost estimation (only recording actual costs)

---

## Cost Model

Typical costs per operation:

```
ITERATION: $0.001-0.01 per iteration (varies by agent)
  - BugFix: ~$0.003 per iteration
  - FeatureBuilder: ~$0.005 per iteration
  - TestWriter: ~$0.002 per iteration

MCP_TOOL_CALL: $0.0001-0.001 per operation
  - Ralph verification: $0.001
  - Git operation: $0.0005
  - Database query: $0.0001
  - Deployment: $0.01

RALPH_VERIFICATION: $0.001 per verification
```

---

## Failure Scenarios & Recovery

**Scenario 1: Cost tracker initialization fails**
- Detection: Catch exception during AgentCostTracker init
- Recovery: Create tracker with defaults
- Fallback: Disable cost tracking if initialization fails

**Scenario 2: SessionState save fails**
- Detection: Try/catch on session.save()
- Recovery: Log error, continue without saving
- Impact: Cost data lost for this session (acceptable)

**Scenario 3: Operation cost not recorded**
- Detection: Compare recorded vs expected operations
- Recovery: Backfill costs from MCP metrics
- Audit: Log discrepancies for later review

---

## Environment Variables

No special env vars needed. Check existing:

```python
ENABLE_COST_TRACKING = os.environ.get("ENABLE_COST_TRACKING", "true").lower() == "true"
```

---

## Completion Signal

When all tests passing and integration complete, output:

```
✅ AGENT_COST_TRACKING_COMPLETE

Implementation Status:
- Tests: 1,057/1,057 passing (726 + 331 lines)
- AgentCostTracker: Implemented
- IterationLoop hooks: Integrated (lines 957-1097)
- SessionState integration: Complete
- Multi-agent aggregation: Functional
- Langfuse-ready: Yes

Ready for merge. Langfuse can read from this tracker.
```

---

## Session Workflow

1. **Read existing tests** - 1 hour
   - Understand what you need to implement
   - 726 lines + 331 lines of test expectations

2. **Create AgentCostTracker** - 2 hours
   - Implement core class
   - All methods must match test expectations

3. **Run tests** - 30 minutes
   - Watch them fail initially
   - Iterate on implementation

4. **Integrate with IterationLoop** - 2 hours
   - Add cost tracker initialization
   - Add recording hooks after operations
   - Add SessionState saving

5. **Test integration** - 1 hour
   - Run full test suite
   - Verify all 1,057 lines passing

6. **Commit and signal** - 15 minutes

**Total Time**: ~7 hours

---

## Important Notes

- **Single Source of Truth**: This is it. Don't estimate, don't double-count.
- **Test-Driven**: Run tests frequently. All 1,057 lines must pass.
- **Integration Hooks**: Lines 957-1097 in iteration_loop.py are reserved for this.
- **Langfuse Dependency**: Langfuse agent (2B-1) depends on this. They read from your tracker.
- **No API Keys**: Everything local, no external services needed.

You are the foundation. Get this right! 🎯

---

**Execute via**: `claude --print "$(cat .aibrain/prompts/phase2b-3-agent-cost-tracking.md)"`
