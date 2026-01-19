# Phase C Integration Guide for autonomous_loop.py

**Purpose**: This guide shows how to integrate Phase C components (Task Complexity Analyzer, Parallel Execution Controller, CITO Delegation) with the existing autonomous_loop.py.

---

## Integration Overview

Phase C adds intelligent task routing and parallel execution to the autonomous loop. The integration is designed to be backward-compatible - the system can run with Phase C disabled.

### New Command-Line Parameters

```python
# Add to autonomous_loop.py argument parser (around line 280)
parser.add_argument(
    "--delegation-enabled",
    action="store_true",
    default=False,
    help="Enable CITO delegation and parallel execution"
)
parser.add_argument(
    "--max-parallel-workers",
    type=int,
    default=2,
    help="Maximum number of parallel workers (default: 2)"
)
parser.add_argument(
    "--sync-on-startup",
    action="store_true",
    default=False,
    help="Sync work queues from target repos on startup"
)
```

### Component Initialization

```python
# Add after line 307 (after loading work queue)
if args.delegation_enabled:
    from orchestration.task_analyzer import TaskAnalyzer
    from orchestration.parallel_controller import ParallelController
    from agents.coordinator.cito import CITOInterface
    from orchestration.performance_tracker import AgentPerformanceTracker

    # Initialize components
    cito = CITOInterface()
    task_analyzer = TaskAnalyzer()
    parallel_controller = ParallelController(
        max_workers=args.max_parallel_workers,
        project_dir=actual_project_dir,
        cito_interface=cito
    )
    performance_tracker = AgentPerformanceTracker()

    print(f"✅ Phase C enabled: {args.max_parallel_workers} workers, CITO delegation active")
```

### Work Queue Sync on Startup

```python
# Add after component initialization
if args.sync_on_startup:
    from orchestration.queue_sync_manager import QueueSyncManager

    sync_manager = QueueSyncManager(Path(__file__).parent)
    print("🔄 Syncing work queues from target repos...")

    results = sync_manager.sync_all_repos()
    for result in results:
        if result["status"] == "success":
            print(f"   ✅ {result['repo']}: {result['stats']['total']} tasks")
```

### Task Routing and Parallel Execution

Replace the existing task selection logic (around line 397) with:

```python
def execute_tasks_with_delegation(
    work_queue,
    task_analyzer,
    parallel_controller,
    cito,
    performance_tracker,
    max_parallel_workers,
    app_context
):
    """Execute tasks using Phase C delegation system"""

    # Get pending tasks
    pending_tasks = [t for t in work_queue.features if t.status == "pending"]

    if not pending_tasks:
        return {"completed": 0, "escalated": 0, "failed": 0}

    results = {"completed": 0, "escalated": 0, "failed": 0}

    # Analyze tasks and group by team
    task_assignments = []
    for task in pending_tasks[:max_parallel_workers * 2]:  # Process 2x workers worth
        complexity = task_analyzer.analyze_complexity(task)

        task_assignments.append({
            "task": task,
            "complexity": complexity,
            "team": complexity.recommended_team,
            "agent": complexity.recommended_agent
        })

    # Separate tasks by team
    simple_tasks = [a for a in task_assignments if a["team"] == "qa"]
    dev_tasks = [a for a in task_assignments if a["team"] == "dev"]
    cito_tasks = [a for a in task_assignments if a["team"] == "cito"]

    # Execute simple tasks first (QA team) - can run in parallel
    if simple_tasks and max_parallel_workers > 1:
        futures = {}
        for i, assignment in enumerate(simple_tasks[:max_parallel_workers]):
            worker_id = f"worker-{i}"
            task = assignment["task"]
            agent_type = assignment["agent"]

            future = parallel_controller.spawn_subagent(
                task, worker_id, agent_type, app_context
            )
            futures[worker_id] = future

        # Wait for workers
        worker_results = parallel_controller.wait_for_workers(futures, timeout=300)

        # Process results
        for worker_id, worker_task in worker_results.items():
            if worker_task.status == "completed":
                results["completed"] += 1
                work_queue.update_task_status(worker_task.task_id, "completed")
            elif worker_task.status == "escalated":
                # Handle escalation
                decision = cito.handle_subagent_escalation(
                    worker_id,
                    worker_task.task,
                    worker_task.escalation.get("reason", "Unknown"),
                    worker_task.result
                )

                if decision.action == "escalate_to_human":
                    results["escalated"] += 1
                    work_queue.update_task_status(worker_task.task_id, "blocked")
                    print(f"⬆️  Task {worker_task.task_id} escalated to human: {decision.escalation_file}")
                elif decision.action == "approve":
                    results["completed"] += 1
                    work_queue.update_task_status(worker_task.task_id, "completed")
            else:
                results["failed"] += 1
                work_queue.update_task_status(worker_task.task_id, "blocked")

            # Track performance
            if worker_task.result:
                performance_tracker.record_task_completion(
                    agent_id=worker_task.agent_type,
                    task=worker_task.task,
                    result=worker_task.result,
                    started_at=datetime.fromisoformat(worker_task.started_at),
                    completed_at=datetime.fromisoformat(worker_task.completed_at) if worker_task.completed_at else None,
                    escalated=worker_task.status == "escalated",
                    escalation_reason=worker_task.escalation.get("reason") if worker_task.escalation else None,
                    worker_id=worker_task.subagent_id
                )

    # Save work queue
    work_queue.save()

    return results
```

### Main Loop Integration

```python
# Replace existing task execution loop (around line 640)
if args.delegation_enabled:
    # Use Phase C delegation system
    iteration_results = execute_tasks_with_delegation(
        work_queue=work_queue,
        task_analyzer=task_analyzer,
        parallel_controller=parallel_controller,
        cito=cito,
        performance_tracker=performance_tracker,
        max_parallel_workers=args.max_parallel_workers,
        app_context=app_context
    )

    print(f"\n📊 Iteration Summary:")
    print(f"   Completed: {iteration_results['completed']}")
    print(f"   Escalated: {iteration_results['escalated']}")
    print(f"   Failed: {iteration_results['failed']}")
else:
    # Use existing sequential execution
    # ... (existing code remains unchanged)
    pass
```

---

## Testing the Integration

### 1. Test with Single Worker (No Parallel)

```bash
python autonomous_loop.py \
  --project karematch \
  --delegation-enabled \
  --max-parallel-workers 1 \
  --max-iterations 10
```

### 2. Test with Parallel Workers

```bash
python autonomous_loop.py \
  --project karematch \
  --delegation-enabled \
  --max-parallel-workers 2 \
  --sync-on-startup \
  --max-iterations 20
```

### 3. Test CITO Escalations

```bash
# After running autonomous loop with escalations:
python orchestration/cito_resolver.py list
python orchestration/cito_resolver.py resolve TASK-001 --action modify --iterations 100
```

### 4. Check Performance Metrics

```bash
python orchestration/performance_tracker.py stats
python orchestration/performance_tracker.py report --days 7
python orchestration/performance_tracker.py escalations --days 7
```

---

## Rollback Plan

If Phase C integration causes issues:

1. **Disable Phase C**: Run without `--delegation-enabled` flag
2. **Remove Parameters**: Comment out Phase C parameters in parser
3. **Fall Back to Sequential**: Existing autonomous loop continues to work

Phase C is designed to be **opt-in** - the system works without it.

---

## Performance Considerations

### Resource Usage

- **Memory**: +20-40 MB per worker (isolated state)
- **CPU**: Minimal overhead (<5% per worker spawn)
- **Disk**: ~100 KB per escalation file

### Recommended Settings

| Scenario | Workers | Rationale |
|----------|---------|-----------|
| Development/Testing | 1 | Easier debugging |
| Production (small queue) | 2 | Good balance |
| Production (large queue) | 2-3 | Avoid thread pool exhaustion |
| CI/CD Pipeline | 1 | Deterministic execution |

### Monitoring

```bash
# Watch performance in real-time
watch -n 5 'python orchestration/performance_tracker.py stats'

# Check escalation rate
python orchestration/performance_tracker.py escalations --days 1

# Monitor pending escalations
python orchestration/cito_resolver.py list
```

---

## Troubleshooting

### Workers Not Starting

**Symptom**: No workers spawn, tasks remain pending

**Fix**: Check that delegation is enabled and max_parallel_workers > 0

```bash
python autonomous_loop.py --delegation-enabled --max-parallel-workers 2 ...
```

### Escalations Not Resolving

**Symptom**: Tasks stuck in escalated state

**Fix**: Manually resolve escalations

```bash
python orchestration/cito_resolver.py list
python orchestration/cito_resolver.py resolve TASK-XXX --action approve
```

### Performance Tracker Not Recording

**Symptom**: No data in agent_performance.jsonl

**Fix**: Ensure governance/metrics/ directory exists

```bash
mkdir -p governance/metrics
touch governance/metrics/agent_performance.jsonl
```

---

## Next Steps

1. **Enable Phase C**: Start with `--delegation-enabled --max-parallel-workers 1`
2. **Monitor**: Watch for escalations and performance metrics
3. **Tune**: Adjust worker count based on queue size
4. **Scale**: Increase to 2-3 workers as confidence grows

---

**Integration Status**: Ready for testing (autonomous_loop.py modifications required)
**Backward Compatibility**: ✅ Fully compatible (opt-in via flag)
**Risk Level**: LOW (fallback to sequential execution available)
