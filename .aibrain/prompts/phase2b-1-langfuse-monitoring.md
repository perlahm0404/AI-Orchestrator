# Phase 2B-1: Langfuse Real-Time Monitoring Integration (CLI Mode)

## Your Role

You are the TeamLead agent for Langfuse real-time cost monitoring. You will implement a dashboard integration that reads cost data from AgentCostTracker (preventing double-counting).

**Execution Mode**: Claude CLI Wrapper (no API key, OAuth-based)
**Merge Order**: THIRD (adds hooks to iteration_loop.py lines 630-785, reads from AgentCostTracker)
**Status**: 40% complete (936 lines of tests + partial implementation exist)

---

## Kanban Board Real-Time Integration ✅ ALREADY WIRED

The kanban board is **already fully integrated and wired**. TeamLead agents automatically stream real-time progress events to the dashboard via WebSocket at `ws://localhost:8080/ws`.

### How It Works (Already Implemented)

**TeamLead orchestration events streamed to kanban board in real-time:**
1. **task_start** - When TeamLead begins orchestration
2. **specialist_started** - When each specialist agent is launched
3. **specialist_completed** - When each specialist finishes (shows verdict)
4. **multi_agent_analyzing** - When analyzing task
5. **multi_agent_synthesis** - When synthesizing specialist results
6. **multi_agent_verification** - When Ralph verification completes
7. **task_complete** - When TeamLead orchestration finishes

### View Your Progress (Real-Time)

While Phase 2B agents are working:

```bash
# Terminal 1: Start kanban dashboard
cd /Users/tmac/1_REPOS/AI_Orchestrator
npm run dev --prefix ui/dashboard

# Terminal 2: Run autonomous loop with monitoring
python autonomous_loop.py --project ai-orchestrator --use-cli --enable-monitoring

# Open browser to http://localhost:3000
# Watch real-time progress of your three teamlead agents
```

### Monitoring Infrastructure

- **WebSocket Server**: `orchestration/websocket_server.py` (already running)
- **MonitoringIntegration**: `orchestration/monitoring_integration.py` (streams events)
- **React Dashboard**: `ui/dashboard/src/components/Dashboard.tsx` (displays progress)
- **Integration Points**: Already added to `orchestration/team_lead.py` (lines 208-330)

**Your job**: Implement Langfuse monitoring that **reads from AgentCostTracker** so costs appear in dashboard and Langfuse cloud at langfuse.com

---

## Exclusive Files (You Own These)

Complete and own these files:

1. **`orchestration/monitoring/langfuse_integration.py`** (EXISTS - 814 lines, 60% complete)
   - `LangfuseMonitor` class
   - Trace and span lifecycle management
   - Integration with dashboard at langfuse.com
   - Cost aggregation (READ from AgentCostTracker)

---

## Existing Test File

This file ALREADY EXISTS with 936 lines of tests. Your implementation must pass all:

1. **`tests/test_langfuse_integration.py`** (936 lines)
   - Tests for trace creation/completion
   - Tests for span management
   - Tests for cost recording
   - Tests for metrics aggregation
   - All must pass before considering complete

---

## Shared Files (Coordinate Carefully)

1. **`orchestration/iteration_loop.py`** (MODIFY lines 630-785)
   - Add Langfuse span lifecycle hooks:
     - `on_iteration_start()` - Start span
     - `on_iteration_end()` - End span with verdict
   - Read costs from AgentCostTracker (NOT estimate)
   - Link with Ralph verification results

2. **`orchestration/monitoring/operation_types.py`** (READ-ONLY)
   - Shared `OperationType` enum
   - Reference operation types for tracking

3. **`orchestration/monitoring/config.py`** (READ-ONLY)
   - Check for Langfuse config section
   - Feature flags: `enable_langfuse`, `langfuse_public_key`, `langfuse_secret_key`

---

## DO NOT TOUCH

These files are owned by other agents:

- `orchestration/agent_cost_tracker.py` (Cost Tracking agent owns - READ ONLY)
- `knowledge/semantic_search.py` (Chroma agent owns)
- `.aibrain/prompts/phase2b-*.md` (Other prompts - read-only)

---

## CRITICAL: Read Costs from AgentCostTracker

**DO NOT estimate costs yourself**. Always read from the cost tracker to prevent double-counting:

```python
# ❌ WRONG (double-counting):
iteration_cost = estimate_iteration_cost()
langfuse_monitor.on_iteration_end(
    span_id=span_id,
    cost_usd=iteration_cost  # YOU estimated
)

# ✅ CORRECT (read from tracker):
# Get cost from tracker (source of truth)
iteration_cost = agent_cost_tracker.get_operation_cost(OperationType.ITERATION)
langfuse_monitor.on_iteration_end(
    span_id=span_id,
    cost_usd=iteration_cost  # From tracker, not estimated
)
```

---

## Implementation Requirements

### 1. Complete LangfuseMonitor Class

Finish implementing `orchestration/monitoring/langfuse_integration.py`:

```python
from typing import Dict, Any, Optional
from datetime import datetime
from orchestration.monitoring.cost_models import CostRecord
from orchestration.monitoring.operation_types import OperationType

class LangfuseMonitor:
    """
    Real-time monitoring integration with Langfuse dashboard.

    Tracks agent execution with:
    - Traces for each task
    - Spans for each iteration
    - Cost tracking (reads from AgentCostTracker)
    - Verdict logging (PASS/FAIL/BLOCKED)
    - Performance metrics
    """

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        enabled: bool = True
    ):
        """Initialize Langfuse monitor."""
        self.enabled = enabled
        self.public_key = public_key
        self.secret_key = secret_key

        if enabled:
            try:
                from langfuse import Langfuse
                self.client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key
                )
            except ImportError:
                self.enabled = False
                self.client = None

    def on_iteration_start(
        self,
        trace_id: str,
        iteration_num: int,
        agent_type: str = "",
        task_description: str = ""
    ) -> Optional[str]:
        """
        Start iteration span.

        Returns:
            Span ID for linking, or None if disabled
        """
        if not self.enabled or not self.client:
            return None

        span_id = self.client.span(
            name=f"iteration_{iteration_num}",
            input={
                "iteration": iteration_num,
                "agent_type": agent_type,
                "task_description": task_description[:100]
            },
            trace_id=trace_id
        ).span_id

        return span_id

    def on_iteration_end(
        self,
        span_id: Optional[str],
        trace_id: str,
        verdict: str,
        duration_ms: float,
        cost_usd: float,  # READ from AgentCostTracker
        output_summary: str = ""
    ) -> None:
        """
        End iteration span.

        Args:
            span_id: Span ID from on_iteration_start
            trace_id: Trace ID
            verdict: PASS, FAIL, or BLOCKED
            duration_ms: Execution time
            cost_usd: Cost from AgentCostTracker (not estimated)
            output_summary: Brief summary of iteration output
        """
        if not self.enabled or not self.client or not span_id:
            return

        self.client.span(
            span_id=span_id,
            trace_id=trace_id,
            output={
                "verdict": verdict,
                "duration_ms": duration_ms,
                "cost_usd": cost_usd
            },
            metadata={
                "verdict": verdict,
                "cost_usd": cost_usd
            }
        ).end()

    def on_task_start(
        self,
        task_id: str,
        task_description: str,
        project: str
    ) -> str:
        """
        Start task trace.

        Returns:
            Trace ID for iterations to link to
        """
        if not self.enabled or not self.client:
            return task_id

        trace_id = self.client.trace(
            name=f"task_{task_id}",
            input={
                "task_id": task_id,
                "description": task_description[:200],
                "project": project
            }
        ).trace_id

        return trace_id or task_id

    def on_task_complete(
        self,
        trace_id: str,
        status: str,
        total_cost_usd: float,
        total_duration_ms: float,
        iterations_count: int
    ) -> None:
        """
        Complete task trace.

        Args:
            trace_id: Trace ID from on_task_start
            status: Task status (completed, blocked, failed)
            total_cost_usd: Total cost for entire task
            total_duration_ms: Total execution time
            iterations_count: Number of iterations performed
        """
        if not self.enabled or not self.client:
            return

        self.client.trace(
            trace_id=trace_id,
            output={
                "status": status,
                "total_cost_usd": total_cost_usd,
                "total_duration_ms": total_duration_ms,
                "iterations": iterations_count
            }
        ).end()

    def is_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self.enabled and self.client is not None
```

### 2. Integrate with IterationLoop (lines 630-785)

Add Langfuse hooks to `orchestration/iteration_loop.py`:

```python
# In IterationLoop.__init__():
self.langfuse_monitor = langfuse_monitor  # Passed from outside
self.langfuse_trace_id = None

# At start of run/run_async():
if self.langfuse_monitor:
    self.langfuse_trace_id = self.langfuse_monitor.on_task_start(
        task_id=task_id,
        task_description=task_description[:200],
        project=self.app_context.project_name if self.app_context else "unknown"
    )

# In iteration loop, before iteration:
iteration_span_id = None
if self.langfuse_monitor and self.langfuse_trace_id:
    iteration_span_id = self.langfuse_monitor.on_iteration_start(
        trace_id=self.langfuse_trace_id,
        iteration_num=current_iteration,
        agent_type=self.agent.agent_type if hasattr(self.agent, 'agent_type') else ""
    )

# After iteration completes:
if self.langfuse_monitor and iteration_span_id and self.langfuse_trace_id:
    # ✅ READ cost from tracker (source of truth)
    iteration_cost = (
        self.cost_tracker.get_operation_cost(OperationType.ITERATION)
        if hasattr(self, 'cost_tracker') else 0.0
    )

    self.langfuse_monitor.on_iteration_end(
        span_id=iteration_span_id,
        trace_id=self.langfuse_trace_id,
        verdict=stop_result.verdict.type.value,
        duration_ms=iteration_duration_ms,
        cost_usd=iteration_cost,  # From tracker, NOT estimated
        output_summary=stop_result.reason or ""
    )

# At end of run/run_async():
if self.langfuse_monitor and self.langfuse_trace_id:
    total_cost = (
        self.cost_tracker.get_total_cost()
        if hasattr(self, 'cost_tracker') else 0.0
    )
    total_time = (datetime.now() - start_time).total_seconds() * 1000

    self.langfuse_monitor.on_task_complete(
        trace_id=self.langfuse_trace_id,
        status=final_status,
        total_cost_usd=total_cost,
        total_duration_ms=total_time,
        iterations_count=iteration_count
    )
```

### 3. Pass All 936 Lines of Tests

These tests MUST pass:

```bash
pytest tests/test_langfuse_integration.py -v
```

All 936 lines of test code must pass (no failures allowed).

---

## Dependencies

**Hard Dependency**: Requires AgentCostTracker (Phase 2B-3) to be merged first

- Must read costs from AgentCostTracker
- Cannot estimate costs independently
- Requires `get_operation_cost()` API from tracker

**Blocks**: Nothing (final integration)

---

## Success Criteria

- [ ] All 936 lines of tests passing (100% success)
- [ ] LangfuseMonitor implementation complete
- [ ] IterationLoop hooks integrated (lines 630-785)
- [ ] Costs read from AgentCostTracker (not estimated)
- [ ] Thread-safe for concurrent agents
- [ ] Graceful degradation when Langfuse unavailable
- [ ] Dashboard integration working
- [ ] NO double-counting with Cost Tracking system

---

## Dashboard Features

When integrated, Langfuse dashboard will show:

1. **Task Traces**
   - Task ID, description, status
   - Total cost for task
   - Total execution time
   - Iteration count

2. **Iteration Spans**
   - Per-iteration cost (read from tracker)
   - Verdict (PASS/FAIL/BLOCKED)
   - Execution time
   - Agent type

3. **Cost Tracking**
   - Total cost per task
   - Cost per iteration (from AgentCostTracker)
   - Cost breakdown by operation type
   - Cost trends over time

4. **Performance Metrics**
   - Execution time per iteration
   - Iterations to completion
   - Success rate
   - Cost per iteration

---

## Configuration

Required environment variables:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export ENABLE_LANGFUSE="true"
```

Optional:

```bash
export LANGFUSE_ENDPOINT="https://cloud.langfuse.com"  # Default
```

---

## Failure Scenarios & Recovery

**Scenario 1: Langfuse API unavailable**
- Detection: Connection timeout
- Recovery: Set `enabled = false`, continue without monitoring
- Impact: No dashboard data for this session

**Scenario 2: Cost data missing from tracker**
- Detection: `get_operation_cost()` returns 0
- Recovery: Use fallback estimate (with warning)
- Audit: Log discrepancy for review

**Scenario 3: Span not created before end**
- Detection: span_id is None
- Recovery: Skip span end call, continue
- Impact: Incomplete trace data

**Scenario 4: Double-counting detected**
- Detection: Total cost > sum of parts
- Recovery: Log warning, use tracker value only
- Prevention: Always read from tracker

---

## Performance Targets

- **Span Creation**: < 50ms overhead per iteration
- **Cost Recording**: < 10ms per operation
- **Dashboard Update**: Real-time (< 1 second latency)
- **Memory Overhead**: < 10MB for trace/span storage

---

## Completion Signal

When all tests passing and integration complete, output:

```
✅ LANGFUSE_MONITORING_COMPLETE

Implementation Status:
- Tests: 936/936 passing
- LangfuseMonitor: Implemented
- IterationLoop hooks: Integrated (lines 630-785)
- Cost reading from tracker: Yes (no double-counting)
- Thread safety: Verified
- Graceful degradation: Working
- Dashboard integration: Ready

Ready for merge. System fully integrated.
```

---

## Session Workflow

1. **Review existing implementation** - 1 hour
   - Read 814 lines of existing LangfuseMonitor
   - Understand what's 60% complete

2. **Complete LangfuseMonitor** - 2 hours
   - Finish remaining 40% of implementation
   - Implement all lifecycle methods
   - Ensure graceful degradation

3. **Run 936 tests** - 1 hour
   - Watch them fail initially
   - Iterate on implementation until passing

4. **Integrate with IterationLoop** - 2 hours
   - Add hooks at lines 630-785
   - Ensure reading from AgentCostTracker
   - No cost estimation

5. **Test integration** - 1.5 hours
   - Run full test suite
   - Verify all 936 lines passing
   - Check dashboard connection

6. **Commit and signal** - 15 minutes

**Total Time**: ~8 hours

---

## Important Notes

- **Source of Truth**: Costs come from AgentCostTracker, NOT from estimation
- **No Double-Counting**: If Cost Tracking reports $0.10, you report $0.10 (not $0.10 + estimate)
- **Graceful Degradation**: System works without Langfuse (just no dashboard)
- **Thread Safety**: Multiple agents may report simultaneously
- **Hard Dependency**: Requires Phase 2B-3 (Cost Tracking) merged first

This is the final integration. Get it right! 📊

---

**Execute via**: `claude --print "$(cat .aibrain/prompts/phase2b-1-langfuse-monitoring.md)"`
