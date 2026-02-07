# Multi-Agent Orchestration Operator Guide

**Version**: 1.0
**Date**: 2026-02-07
**Audience**: Operations, DevOps, and Platform Engineering teams

---

## Table of Contents

1. [Overview](#overview)
2. [How Multi-Agent Orchestration Works](#how-multi-agent-orchestration-works)
3. [Key Components](#key-components)
4. [Monitoring & Observability](#monitoring--observability)
5. [Common Issues & Troubleshooting](#common-issues--troubleshooting)
6. [Cost Monitoring](#cost-monitoring)
7. [Rollback Procedures](#rollback-procedures)
8. [Performance Tuning](#performance-tuning)
9. [FAQ](#faq)

---

## Overview

AI Orchestrator's multi-agent system enables **parallel specialist execution** for complex tasks, improving quality and reducing execution time compared to single-agent approaches.

### Key Benefits

- **Higher Quality**: 15-40% improvement in code quality (tests passing, bugs fixed)
- **Better Coverage**: Multiple specialists tackle different aspects in parallel
- **Cost Efficient**: ROI positive for tasks worth ≥$50 or HIGH complexity
- **Resumable**: Full session state persistence across context resets

### When It's Active

Multi-agent orchestration activates automatically for:
- Tasks worth ≥ $50 USD
- HIGH or CRITICAL complexity
- HIPAA-related work
- Deployments and migrations
- Cross-repository changes

---

## How Multi-Agent Orchestration Works

### Single-Agent (Traditional)

```
Task → IterationLoop → Agent → Iterations → Result
       (15-50 iterations)
```

**Cost**: $0.10-$0.30 per task
**Time**: 5-15 minutes for complex tasks
**Risk**: Single point of failure

### Multi-Agent (New)

```
                    ┌→ Specialist 1 (BugFix)
Task → TeamLead ────┼→ Specialist 2 (TestWriter)  [PARALLEL]
       (Analysis)   └→ Specialist 3 (CodeQuality)
                          ↓
                    (Synthesis)
                          ↓
                        Result
```

**Cost**: $0.15-$0.60 per task (higher cost, higher quality)
**Time**: 3-10 minutes (parallel execution)
**Risk**: Distributed across specialists, graceful degradation

### Execution Flow

1. **TaskRouter Decision** (Instant)
   - Analyzes task value, complexity, type
   - Decides: Multi-agent vs single-agent
   - Logs decision with reasoning

2. **TeamLead Analysis** (Async)
   - If multi-agent: TeamLead analyzes task
   - Breaks into subtasks
   - Selects appropriate specialists
   - Launches specialists in parallel (asyncio.gather)

3. **Specialist Execution** (Parallel)
   - Each specialist works independently
   - Enforces iteration budget (bugfix: 15, featurebuilder: 50, etc.)
   - SessionState tracks progress
   - Ralph verification per specialist

4. **Synthesis** (Post-Parallel)
   - TeamLead synthesizes specialist results
   - Resolves conflicts/overlaps
   - Produces final deliverable
   - Verification check

5. **Completion**
   - Result committed to git
   - Metrics logged (cost, time, quality)
   - SessionState archived

### Data Flow

```
Autonomous Loop
    ↓
Task from work_queue.json
    ↓
TaskRouter (should_use_multi_agent?)
    ├─ YES → TeamLead Orchestrator
    │         ├─ SpecialistAgent (BugFix)
    │         ├─ SpecialistAgent (TestWriter)
    │         └─ SpecialistAgent (CodeQuality)
    │
    └─ NO → IterationLoop (single agent)
             └─ Agent (BugFix/FeatureBuilder/etc)
    ↓
SessionState (save state)
    ↓
Git Commit
    ↓
Metrics Logged
```

---

## Key Components

### 1. TaskRouter (`orchestration/task_router.py`)

**Responsibility**: Decides whether to use multi-agent or single-agent for each task.

**Routing Rules** (in priority order):
1. **Explicit Override**: `agent_type_override` or `use_multi_agent` flag (final decision)
2. **Task Type**: HIPAA, deployment, cross-repo → multi-agent
3. **Complexity**: HIGH or CRITICAL → multi-agent
4. **Value**: ≥ $50 → multi-agent
5. **Default**: Single-agent (cost-efficient)

**Configuration**:
```python
VALUE_THRESHOLD_USD = 50.0  # Adjust to change value threshold
QUALITY_IMPROVEMENTS = {    # Adjust quality estimates
    ComplexityCategory.LOW: 0.05,
    ComplexityCategory.MEDIUM: 0.15,
    ...
}
AGENT_COSTS = {            # Adjust per-agent costs
    AgentType.BUGFIX: 0.067,
    ...
}
```

### 2. TeamLead (`orchestration/team_lead.py`)

**Responsibility**: Orchestrates multiple specialists for complex tasks.

**Process**:
1. Analyzes task description
2. Determines which specialists needed
3. Creates subtasks for each specialist
4. Launches all specialists in parallel (asyncio.gather)
5. Monitors progress via SessionState
6. Synthesizes results
7. Verifies final output

**Iteration Budget**: 10 iterations (task analysis + coordination)

### 3. SpecialistAgent (`orchestration/specialist_agent.py`)

**Responsibility**: Wraps individual agents with iteration budget enforcement.

**Per-Specialist Budgets**:
- **BugFix**: 15 iterations
- **FeatureBuilder**: 50 iterations
- **TestWriter**: 15 iterations
- **CodeQuality**: 20 iterations
- **Advisor**: 10 iterations
- **Deployment**: 20 iterations
- **Migration**: 50 iterations

**Timeout**: 10 minutes per specialist (configurable)

### 4. SessionState (`orchestration/session_state.py`)

**Responsibility**: Persists state for resumption across context resets.

**Multi-Agent Methods**:
- `record_team_lead_analysis(analysis)` - Log TeamLead's analysis
- `record_specialist_launch(specialist_type, subtask_id)` - Log specialist start
- `record_specialist_iteration(specialist_type, iteration, output)` - Log each iteration
- `record_specialist_completion(specialist_type, status, verdict, cost)` - Log completion
- `get_specialist_status(specialist_type)` - Query specialist state
- `get_all_specialists_status()` - Query all specialists
- `all_specialists_complete()` - Check if all done

**Data Location**: `.aibrain/.multi-agent-{task_id}.json`

### 5. WorkQueueTask (`orchestration/work_queue_schema.py`)

**New Multi-Agent Fields**:
- `complexity_category`: LOW/MEDIUM/HIGH/CRITICAL
- `estimated_value_usd`: Budget impact (0.0-5000.0)
- `preferred_agents`: List of recommended specialists
- `use_multi_agent`: Explicit flag (True/False/None)
- `agent_type_override`: Force single agent type

---

## Monitoring & Observability

### Key Metrics to Track

#### Task-Level Metrics

| Metric | Target | Alert If |
|--------|--------|----------|
| Multi-agent usage rate | 30-40% | < 10% or > 60% |
| Quality improvement | 15-30% | < 5% |
| Cost per task | $0.15-0.40 | > $0.50 |
| Time to completion | 3-10 min | > 15 min |
| Success rate | ≥ 95% | < 90% |

#### Specialist-Level Metrics

| Metric | Target | Alert If |
|--------|--------|----------|
| Avg iterations per specialist | 8-15 | > 30 (infinite loop) |
| Avg token usage per specialist | 20K-40K | > 100K (wasteful) |
| Avg cost per specialist | $0.05-0.15 | > $0.25 |
| Timeout rate | 0-2% | > 5% |

### How to Monitor

#### Option 1: Langfuse (Recommended)

```python
from langfuse import Langfuse
from orchestration.session_state import SessionState

langfuse = Langfuse(public_key="...", secret_key="...")

session = SessionState(task_id, project="ai-orchestrator")
specialists = session.get_all_specialists_status()

for specialist_type, data in specialists.items():
    langfuse.trace(
        name=f"specialist_{specialist_type}",
        input={"task_id": task_id, "specialist": specialist_type},
        output=data,
        metadata={
            "cost_usd": data.get("cost", 0),
            "iterations": data.get("iterations", 0),
            "verdict": data.get("verdict", "UNKNOWN"),
        }
    )
```

#### Option 2: CloudWatch (AWS)

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='AIOrchestrator',
    MetricData=[
        {
            'MetricName': 'MultiAgentUsageRate',
            'Value': multi_agent_count / total_tasks,
            'Unit': 'Percent'
        },
        {
            'MetricName': 'SpecialistCost',
            'Value': specialist_cost_usd,
            'Unit': 'None',
            'Dimensions': [
                {'Name': 'SpecialistType', 'Value': specialist_type}
            ]
        }
    ]
)
```

#### Option 3: StdOut/Logs

```bash
# Watch for multi-agent launches
tail -f logs/*.log | grep "USE_MULTI_AGENT"

# Track costs
grep "cost_usd" logs/*.log | awk '{sum += $NF} END {print "Total: $" sum}'

# Monitor specialist timeouts
grep "TIMEOUT\|timeout" logs/*.log
```

### Health Checks

**Daily Dashboard Should Show**:
- ✅ Multi-agent usage: 30-40% of tasks
- ✅ Quality improvement: 15-30% vs single-agent
- ✅ Cost overhead: <30% vs single-agent
- ✅ Success rate: ≥95%
- ✅ No timeouts: <2% of specialists

---

## Common Issues & Troubleshooting

### Issue 1: Multi-Agent Using Too Much Cost

**Symptom**: Cost per task > $0.50, ROI negative

**Root Cause**:
- VALUE_THRESHOLD_USD too low (routing too many tasks)
- Specialist budgets too high (specialists iterating too long)
- Inefficient task breakdown (overlapping work)

**Fix**:
```python
# In task_router.py
VALUE_THRESHOLD_USD = 75.0  # Raise threshold (was 50.0)

# In specialist_agent.py
ITERATION_BUDGETS = {
    AgentType.BUGFIX: 12,  # Reduce from 15
    AgentType.FEATUREBUILDER: 40,  # Reduce from 50
}
```

### Issue 2: Multi-Agent Not Launching (Staying Single-Agent)

**Symptom**: High-value tasks still use single-agent

**Possible Causes**:
1. TaskRouter not imported in autonomous_loop.py
2. `is_multi_agent_available()` returning False
3. Feature flag disabled

**Diagnosis**:
```bash
# Check logs for routing decisions
grep "RoutingDecision" logs/*.log

# Verify TaskRouter is called
grep "TaskRouter.should_use_multi_agent" logs/*.log

# Check feature flag
cat tasks/work_queue_*.json | grep '"use_multi_agent"'
```

**Fix**:
```python
# In autonomous_loop.py
from orchestration.task_router import TaskRouter

task = load_task(task_id)
analysis = TaskRouter.should_use_multi_agent(task)

if analysis.decision == RoutingDecision.USE_MULTI_AGENT:
    result = await team_lead.orchestrate(task_id, task.description)
else:
    result = await iteration_loop.run(task_id)
```

### Issue 3: Specialist Timeouts (10+ seconds stuck)

**Symptom**: "Specialist X timed out after 600 seconds"

**Root Cause**:
- Specialist hitting external API (slow response)
- Infinite loop in agent logic
- Thread/process deadlock

**Fix**:
```python
# In specialist_agent.py
TIMEOUT_SECONDS = 900  # Increase from 600 to 15 minutes

# Or: Add timeout per iteration
timeout_per_iteration = TIMEOUT_SECONDS / budget
# If time > timeout_per_iteration, force completion

# Or: Reduce budget to prevent infinite loops
ITERATION_BUDGETS[AgentType.BUGFIX] = 10  # Force completion sooner
```

### Issue 4: SessionState File Not Saving/Loading

**Symptom**: Context reset loses multi-agent state

**Root Cause**:
- Session directory doesn't exist (`.aibrain/`)
- File permissions issue
- JSON serialization error

**Fix**:
```bash
# Check directory exists
ls -la .aibrain/

# Check file permissions
chmod 755 .aibrain/
chmod 644 .aibrain/.multi-agent-*.json

# Verify JSON is valid
python -m json.tool .aibrain/.multi-agent-TASK-001-1.json
```

### Issue 5: Quality Not Improving with Multi-Agent

**Symptom**: Ralph verdict same for multi-agent vs single-agent

**Root Cause**:
- Specialists not selected appropriately
- Task too simple (doesn't benefit from parallelism)
- TeamLead not synthesizing results correctly

**Fix**:
```python
# Review specialist selection in task_router.py
# For each task type, verify right specialists selected:

if task.type == "feature":
    # Should include TestWriter for coverage
    if AgentType.TESTWRITER not in recommended_specialists:
        recommended_specialists.append(AgentType.TESTWRITER)

# Review TeamLead synthesis logic
# Ensure no specialist output is ignored
```

---

## Cost Monitoring

### Daily Cost Tracking

```python
from orchestration.session_state import SessionState
from pathlib import Path

def daily_cost_report():
    """Generate daily multi-agent cost report."""

    session_dir = Path(".aibrain")
    multi_agent_files = session_dir.glob(".multi-agent-*.json")

    total_cost = 0.0
    multi_agent_cost = 0.0
    single_agent_cost = 0.0
    specialist_breakdown = {}

    for session_file in multi_agent_files:
        session = SessionState.load(session_file.stem.replace(".multi-agent-", ""))

        if session.get_all_specialists_status():
            # Multi-agent task
            for specialist_type, data in session.get_all_specialists_status().items():
                cost = data.get("cost", 0.0)
                multi_agent_cost += cost

                if specialist_type not in specialist_breakdown:
                    specialist_breakdown[specialist_type] = 0.0
                specialist_breakdown[specialist_type] += cost
        else:
            # Single-agent task
            single_agent_cost += 0.135  # Estimate

    total_cost = multi_agent_cost + single_agent_cost

    print(f"Daily Cost Report:")
    print(f"  Total: ${total_cost:.2f}")
    print(f"  Multi-agent: ${multi_agent_cost:.2f} ({multi_agent_cost/total_cost*100:.1f}%)")
    print(f"  Single-agent: ${single_agent_cost:.2f} ({single_agent_cost/total_cost*100:.1f}%)")
    print(f"\nBreakdown by Specialist:")
    for specialist, cost in specialist_breakdown.items():
        print(f"  {specialist}: ${cost:.2f}")
```

### Cost Thresholds

| Threshold | Action |
|-----------|--------|
| Daily cost > $100 | Alert operations team |
| Avg cost per task > $0.50 | Review TaskRouter thresholds |
| Any specialist > $0.30 | Review specialist budget |
| Quality improvement < 10% | Consider disabling multi-agent |

---

## Rollback Procedures

### Scenario 1: Multi-Agent System Broken

**Steps**:

1. **Immediate**: Disable multi-agent routing
   ```python
   # In task_router.py
   @staticmethod
   def should_use_multi_agent(task) -> RoutingAnalysis:
       # OVERRIDE: Force single-agent during outage
       return RoutingAnalysis(
           task_id=task.id,
           decision=RoutingDecision.USE_SINGLE_AGENT,
           reason="SYSTEM MAINTENANCE: Multi-agent disabled",
           ...
       )
   ```

2. **Notify**: Alert users that multi-agent is offline

3. **Diagnose**: Identify root cause
   - Check TaskRouter logs
   - Check SessionState file creation
   - Check TeamLead orchestration logs

4. **Fix**: Deploy patch or hotfix

5. **Verify**: Test with sample task before re-enabling

6. **Re-enable**: Gradually re-enable (10% → 25% → 50% → 100%)

### Scenario 2: Specific Specialist Broken

**Steps**:

1. **Identify**: Which specialist has issues?
   - Review logs: `grep "specialist_type.*TIMEOUT\|ERROR"`
   - Check success rate per specialist

2. **Disable**: Remove from routing
   ```python
   # In task_router.py
   @staticmethod
   def _select_specialists(task):
       specialists = [...]

       # HOTFIX: Exclude broken specialist
       if AgentType.FEATUREBUILDER in specialists:
           specialists.remove(AgentType.FEATUREBUILDER)  # Broken

       return specialists
   ```

3. **Fix**: Deploy specialist fix

4. **Re-enable**: Add back to routing

### Scenario 3: Increased Costs

**Steps**:

1. **Investigate**: Which tasks cost too much?
   ```bash
   grep "cost_usd.*[0-9]\{2\}[.][0-9][0-9]" logs/*.log
   ```

2. **Identify**: Specialist budgets too high?
   - Compare against daily cost report
   - Check if specific task type is expensive

3. **Adjust**: Reduce VALUE_THRESHOLD_USD
   ```python
   # Reduce from $50 → $75 (fewer tasks use multi-agent)
   VALUE_THRESHOLD_USD = 75.0
   ```

4. **Monitor**: Ensure quality doesn't degrade

---

## Performance Tuning

### Parallel Execution Optimization

```python
# In team_lead.py
async def _launch_specialists(self, specialists_with_subtasks):
    """Launch specialists with optional parallel limits."""

    # Option 1: Unlimited parallel (current)
    results = await asyncio.gather(
        *specialist_tasks,
        return_exceptions=True
    )

    # Option 2: Limited parallel (reduce resource contention)
    semaphore = asyncio.Semaphore(3)  # Max 3 parallel

    async def limited_task(task):
        async with semaphore:
            return await task

    results = await asyncio.gather(
        *[limited_task(t) for t in specialist_tasks],
        return_exceptions=True
    )
```

### SessionState Optimization

```python
# In session_state.py
def _save_multi_agent_data(self):
    """Save with optional compression."""

    # Option 1: Save as-is (current)
    with open(self._multi_agent_file, "w") as f:
        json.dump(multi_agent_data, f)

    # Option 2: Compress if large (> 100KB)
    import gzip
    if len(json.dumps(multi_agent_data)) > 100000:
        with gzip.open(self._multi_agent_file + ".gz", "wt") as f:
            json.dump(multi_agent_data, f)
```

### Cost Estimation Tuning

```python
# Calibrate AGENT_COSTS based on actual data
def calibrate_agent_costs():
    """Adjust cost estimates based on real execution."""

    # Collect actual costs from past 30 days
    actual_costs = {
        AgentType.BUGFIX: 0.062,  # Was 0.067
        AgentType.FEATUREBUILDER: 0.210,  # Was 0.220
    }

    # Update TaskRouter with actual costs
    TaskRouter.AGENT_COSTS = actual_costs
```

---

## FAQ

### Q: Will multi-agent break my existing workflows?

**A**: No. Multi-agent is additive and non-breaking:
- Existing single-agent workflows continue unchanged
- TaskRouter is opt-in (initially routes only high-value tasks)
- Feature flag allows gradual rollout
- Rollback is instant (disable in TaskRouter)

### Q: What if a specialist fails (timeout/error)?

**A**: Graceful degradation:
- TeamLead catches exceptions from specialists (return_exceptions=True)
- Failed specialist results marked as "blocked" or "timeout"
- Other specialists continue working
- TeamLead synthesizes partial results
- Final output may be lower quality but still usable
- Task can be retried with single-agent as fallback

### Q: How much does multi-agent cost extra?

**A**: ROI positive for:
- Tasks worth ≥ $50 (extra 20-40% cost, but 15-30% quality gain)
- HIGH/CRITICAL complexity (quality gain > cost increase)

**Example**: $200 task
- Single-agent: $0.13
- Multi-agent: $0.35 (+$0.22, +170%)
- Quality improvement: 30% (worth ~$60 in value)
- ROI: 270% ($60 value / $0.22 cost)

### Q: Can I adjust thresholds?

**A**: Yes, all thresholds are tunable in TaskRouter:
- VALUE_THRESHOLD_USD (default: $50)
- QUALITY_IMPROVEMENTS (default: 5-40% by complexity)
- AGENT_COSTS (default: per-specialist estimates)
- Specialist iteration budgets (in specialist_agent.py)

Adjust based on your team's actual metrics.

### Q: How do I know if multi-agent is working?

**A**: Check these metrics daily:
- Multi-agent usage rate: 30-40% of tasks
- Quality improvement: Ralph pass rate 15-30% higher
- Cost overhead: <30% vs single-agent equivalent
- Success rate: ≥95%

### Q: What if multi-agent is slower than single-agent?

**A**: Common reasons:
- TeamLead analysis takes 1-2 minutes (overhead)
- Networking latency between specialists
- Specialist selection inefficient

**Solution**:
- Optimize TeamLead.analyze() prompt
- Reduce networking round-trips
- Refine specialist selection in _select_specialists()

### Q: How do I debug a failed multi-agent task?

**A**: Use SessionState files:
```bash
# Check if multi-agent was used
grep "USE_MULTI_AGENT" .aibrain/session-*.md

# View specialist status
python -c "
from orchestration.session_state import SessionState
s = SessionState.load('TASK-001-1')
import json
print(json.dumps(s.get_all_specialists_status(), indent=2))
"

# Check iteration history
grep "iteration_history" .aibrain/.multi-agent-*.json | jq .
```

---

## Support

For issues:
1. Check this guide's troubleshooting section
2. Review logs in appropriate workspace
3. Contact AI Orchestrator team
4. Reference IMPLEMENTATION-PROGRESS.md for current status

---

**Document Status**: Complete and ready for production operations
**Last Updated**: 2026-02-07
**Version**: 1.0
