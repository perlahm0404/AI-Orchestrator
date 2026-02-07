---
title: Phase 1 Integration - Implementation Plan
date: 2026-02-07
status: in_progress
phase: 1-integration
---

# Phase 1 Integration: Connect to Production

**Duration**: 1 week (40 hours)
**Team**: 2 engineers
**Goal**: Connect TaskRouter and SessionState to autonomous_loop.py for production multi-agent routing

---

## Overview

Phase 1 foundation is complete (70/70 tests passing). Now we integrate the multi-agent system into the production autonomous loop so it actually routes real tasks.

### Current State
- ✅ TaskRouter ready (32/32 tests passing)
- ✅ SessionState multi-agent ready (12/12 tests passing)
- ✅ WorkQueue schema ready (26/26 tests passing)
- ⏳ NOT integrated with autonomous_loop.py yet

### After Integration
- ✅ TaskRouter makes routing decisions in autonomous_loop
- ✅ SessionState persists multi-agent state
- ✅ Real tasks routed to multi-agent or single-agent
- ✅ Full state resumption on context reset

---

## Integration Tasks

### Task 1: IterationLoop SessionState Integration (2 days)

**Goal**: Make IterationLoop save/load SessionState for resumption

**Current State**:
```python
# orchestration/iteration_loop.py
async def run(self, task_id: str) -> Dict[str, Any]:
    # Runs agent iterations until done
    # No SessionState integration
    # State lost on context reset
```

**Target State**:
```python
# orchestration/iteration_loop.py
async def run(self, task_id: str, resume: bool = False) -> Dict[str, Any]:
    # Load existing SessionState if resuming
    if resume:
        session = SessionState.load(task_id)
        iteration_count = session.iteration_count
        # Resume from saved state
    else:
        session = SessionState(task_id)

    # Run iterations
    for iteration in range(iteration_count, MAX_ITERATIONS):
        # Run agent iteration
        result = await agent.run_iteration(iteration)

        # Save state after each iteration
        session.update(
            iteration_count=iteration + 1,
            status="in_progress",
            output=result
        )
        session.save()

    # Archive on completion
    session.archive()
    return session.load()
```

**Implementation Steps**:
1. [ ] Review current IterationLoop.run() signature and implementation
2. [ ] Add SessionState import and initialization
3. [ ] Add resume parameter to run()
4. [ ] Load existing SessionState if resume=True
5. [ ] Save SessionState after each iteration
6. [ ] Archive SessionState on completion
7. [ ] Handle SessionState errors gracefully
8. [ ] Add integration tests
9. [ ] Verify backward compatibility

**Files to Modify**:
- `orchestration/iteration_loop.py` (~30 lines added)

**Tests to Add**:
- `test_iteration_loop_sessionstate_save_load.py` (15 tests)

**Success Criteria**:
- [ ] IterationLoop saves SessionState after each iteration
- [ ] Context reset doesn't lose progress
- [ ] Resumption restores all state
- [ ] All existing tests still pass
- [ ] New integration tests pass

---

### Task 2: Autonomous Loop TaskRouter Integration (2-3 days)

**Goal**: Use TaskRouter to make multi-agent vs single-agent routing decisions

**Current State**:
```python
# autonomous_loop.py
async def run(self, project: str, max_iterations: int = 100):
    while work_queue:
        task = work_queue.pop()
        # Always use single-agent IterationLoop
        result = await self.iteration_loop.run(task.id)
        # Commit and continue
```

**Target State**:
```python
# autonomous_loop.py
from orchestration.task_router import TaskRouter, RoutingDecision

async def run(self, project: str, max_iterations: int = 100, use_multi_agent: bool = True):
    while work_queue:
        task = work_queue.pop()

        # Make routing decision
        if use_multi_agent:
            analysis = TaskRouter.should_use_multi_agent(task)
        else:
            analysis = TaskRouter.fallback_to_single_agent(task)

        # Route accordingly
        if analysis.decision == RoutingDecision.USE_MULTI_AGENT:
            # Launch TeamLead orchestrator
            result = await self.team_lead.orchestrate(
                task_id=task.id,
                task_description=task.description,
                resume=True  # SessionState resumption
            )
        else:
            # Use single-agent IterationLoop
            result = await self.iteration_loop.run(
                task_id=task.id,
                resume=True  # SessionState resumption
            )

        # Log routing decision
        logger.info(
            f"Task {task.id}: {analysis.decision}",
            extra={"analysis": analysis.to_dict()}
        )

        # Commit result
        if result["status"] == "completed":
            await self._commit_and_continue(task, result)
```

**Implementation Steps**:
1. [ ] Review current autonomous_loop.py structure
2. [ ] Import TaskRouter and RoutingDecision
3. [ ] Add use_multi_agent parameter to run()
4. [ ] Implement routing decision logic
5. [ ] Add multi-agent vs single-agent branching
6. [ ] Add resume=True to both paths
7. [ ] Log routing decisions for monitoring
8. [ ] Handle multi-agent failures with fallback
9. [ ] Add feature flag for gradual rollout
10. [ ] Add integration tests
11. [ ] Verify backward compatibility

**Files to Modify**:
- `autonomous_loop.py` (~50 lines added)

**New Files**:
- `orchestration/autonomous_loop_config.py` (feature flag config, ~20 lines)

**Tests to Add**:
- `test_autonomous_loop_taskrouter_integration.py` (12 tests)

**Success Criteria**:
- [ ] TaskRouter makes routing decisions in autonomous_loop
- [ ] Multi-agent tasks routed to TeamLead
- [ ] Single-agent tasks routed to IterationLoop
- [ ] Routing decisions logged for monitoring
- [ ] Fallback to single-agent on multi-agent failure
- [ ] Feature flag allows gradual rollout
- [ ] All existing tests still pass
- [ ] New integration tests pass

---

### Task 3: Fallback & Error Handling (1-2 days)

**Goal**: Handle failures gracefully, fall back to single-agent if needed

**Scenarios**:
1. Multi-agent initiated, TeamLead analysis fails
2. Multi-agent initiated, specialist times out
3. Multi-agent initiated, synthesis fails
4. SessionState save fails
5. Context reset during multi-agent execution

**Implementation**:
```python
# In autonomous_loop.py
try:
    if analysis.decision == RoutingDecision.USE_MULTI_AGENT:
        result = await self.team_lead.orchestrate(...)
except Exception as e:
    logger.warning(
        f"Multi-agent failed for {task.id}, falling back to single-agent",
        exc_info=e
    )
    # Fallback to single-agent
    analysis = TaskRouter.fallback_to_single_agent(task)
    result = await self.iteration_loop.run(task.id, resume=True)
```

**Files to Modify**:
- `autonomous_loop.py` (~20 lines)
- `orchestration/team_lead.py` (error handling review)

**Tests to Add**:
- `test_autonomous_loop_fallback_behavior.py` (8 tests)

**Success Criteria**:
- [ ] Multi-agent failures caught and logged
- [ ] Fallback to single-agent automatic
- [ ] Task eventually completes (multi or single)
- [ ] SessionState survives failures
- [ ] Monitoring captures fallbacks

---

### Task 4: Real Workflow Testing (2-3 days)

**Goal**: Test multi-agent routing with real tasks from work queue

**Test Scenarios**:
1. Simple bug fix (should be single-agent)
2. High-value feature (should be multi-agent)
3. HIPAA credential task (should be multi-agent)
4. Deployment task (should be multi-agent)
5. Cross-repo refactor (should be multi-agent)
6. Context reset during multi-agent execution (should resume)

**Test Setup**:
```python
# tests/test_phase1_integration_e2e.py

async def test_simple_bug_routed_to_single_agent():
    """Simple bugs should use single-agent."""
    task = WorkQueueTaskMultiAgent(
        id="TEST-BUG-001",
        description="Fix typo in README",
        complexity_category=ComplexityCategory.LOW,
        estimated_value_usd=10.0,
    )

    loop = AutonomousLoop(project="test")
    result = await loop.run_single_task(task)

    assert result["routing_decision"] == RoutingDecision.USE_SINGLE_AGENT
    assert result["status"] == "completed"

async def test_high_value_feature_routed_to_multi_agent():
    """High-value features should use multi-agent."""
    task = WorkQueueTaskMultiAgent(
        id="TEST-FEATURE-001",
        description="Implement new payment processing",
        complexity_category=ComplexityCategory.HIGH,
        estimated_value_usd=500.0,
    )

    loop = AutonomousLoop(project="test")
    result = await loop.run_single_task(task)

    assert result["routing_decision"] == RoutingDecision.USE_MULTI_AGENT
    assert result["status"] == "completed"

async def test_context_reset_resumes_multi_agent():
    """Multi-agent execution should resume across context resets."""
    task = WorkQueueTaskMultiAgent(
        id="TEST-RESUME-001",
        description="Complex feature with HIPAA compliance",
        complexity_category=ComplexityCategory.HIGH,
        estimated_value_usd=250.0,
    )

    # Start multi-agent execution
    loop = AutonomousLoop(project="test")

    # Simulate context reset after 2 iterations
    result1 = await loop.run_single_task(task, max_iterations=2)
    assert result1["status"] == "in_progress"

    # Resume from saved state
    result2 = await loop.run_single_task(task, resume=True, max_iterations=10)
    assert result2["status"] == "completed"
    assert result2["total_iterations"] == 8  # Resumed from iteration 2
```

**Files to Create**:
- `tests/test_phase1_integration_e2e.py` (200 lines, 8 tests)

**Success Criteria**:
- [ ] Simple tasks routed correctly
- [ ] High-value tasks routed correctly
- [ ] HIPAA tasks routed correctly
- [ ] Deployment tasks routed correctly
- [ ] Cross-repo tasks routed correctly
- [ ] Context reset doesn't lose progress
- [ ] All 8 tests passing
- [ ] Metrics logged correctly

---

## Integration Checklist

### Pre-Integration (Today)
- [x] Phase 1 foundation complete (70/70 tests)
- [x] TaskRouter ready (32/32 tests)
- [x] SessionState multi-agent ready (12/12 tests)
- [x] Work queue schema ready (26/26 tests)
- [ ] Integration plan reviewed
- [ ] Team assigned
- [ ] Testing infrastructure ready

### IterationLoop Integration
- [ ] SessionState import added
- [ ] resume parameter added
- [ ] Load existing SessionState if resume=True
- [ ] Save SessionState after each iteration
- [ ] Archive on completion
- [ ] Error handling implemented
- [ ] Backward compatibility verified
- [ ] Integration tests written
- [ ] All tests passing

### Autonomous Loop Integration
- [ ] TaskRouter import added
- [ ] use_multi_agent parameter added
- [ ] Routing decision logic implemented
- [ ] Multi-agent branching added
- [ ] Single-agent branching added
- [ ] Feature flag implemented
- [ ] Error handling and fallback implemented
- [ ] Monitoring/logging added
- [ ] Integration tests written
- [ ] All tests passing

### Fallback & Error Handling
- [ ] Multi-agent failure catching implemented
- [ ] Fallback to single-agent automatic
- [ ] SessionState error handling
- [ ] Context reset handling
- [ ] Error tests written
- [ ] All tests passing

### Real Workflow Testing
- [ ] Test suite created (8 tests)
- [ ] Simple tasks tested
- [ ] High-value tasks tested
- [ ] HIPAA tasks tested
- [ ] Deployment tasks tested
- [ ] Cross-repo tasks tested
- [ ] Context reset tested
- [ ] Metrics verification
- [ ] All tests passing

### Final Verification
- [ ] Phase 1 tests still passing (70/70)
- [ ] IterationLoop tests passing
- [ ] Autonomous loop tests passing
- [ ] Integration tests passing (8/8)
- [ ] No breaking changes
- [ ] Backward compatible
- [ ] Documentation updated
- [ ] Ready for Phase 2

---

## Risk Mitigation

### Risk 1: SessionState integration breaks existing code
**Mitigation**:
- Add SessionState as optional parameter
- Keep existing non-SessionState path working
- Run all existing tests after integration
- Gradual rollout with feature flag

### Risk 2: Multi-agent routing decision wrong
**Mitigation**:
- Log all routing decisions
- Monitor real tasks manually
- Adjust VALUE_THRESHOLD_USD if needed
- Quick rollback via feature flag

### Risk 3: Context reset during multi-agent loses state
**Mitigation**:
- SessionState saves after each iteration
- Comprehensive resumption tests
- Session file validation on load
- Error handling for corrupted files

### Risk 4: Multi-agent slower than single-agent
**Mitigation**:
- Monitor execution time per task
- Compare multi-agent vs single-agent timing
- Optimize TeamLead analysis prompt
- Fall back to single-agent if too slow

---

## Success Metrics

### Code Quality
- [x] Phase 1 tests: 70/70 passing
- [ ] IterationLoop integration tests: 15/15 passing
- [ ] Autonomous loop integration tests: 12/12 passing
- [ ] Error handling tests: 8/8 passing
- [ ] E2E workflow tests: 8/8 passing
- **Total Target**: 113/113 tests passing

### Functionality
- [ ] TaskRouter making decisions
- [ ] Multi-agent tasks routed correctly
- [ ] Single-agent tasks routed correctly
- [ ] SessionState persisting across context resets
- [ ] Fallback working on failures

### Monitoring
- [ ] Routing decisions logged
- [ ] Multi-agent vs single-agent ratio tracked
- [ ] Task success rate monitored
- [ ] Cost tracked per task
- [ ] Errors logged with context

### Production Readiness
- [ ] Feature flag working
- [ ] Gradual rollout possible (10% → 25% → 50% → 100%)
- [ ] Quick rollback available
- [ ] Operator guide updated
- [ ] Team trained

---

## Timeline

**Day 1**: IterationLoop SessionState integration
- [ ] Review iteration_loop.py (1 hr)
- [ ] Implement SessionState integration (3 hrs)
- [ ] Write tests (2 hrs)
- [ ] Verify backward compatibility (1 hr)

**Day 2**: Autonomous loop TaskRouter integration
- [ ] Review autonomous_loop.py (1 hr)
- [ ] Implement TaskRouter integration (3 hrs)
- [ ] Add feature flag (1 hr)
- [ ] Write tests (2 hrs)

**Day 3**: Error handling and fallback
- [ ] Implement fallback logic (2 hrs)
- [ ] Error handling tests (1 hr)
- [ ] Manual testing (2 hrs)

**Day 4-5**: Real workflow testing
- [ ] Set up test scenarios (2 hrs)
- [ ] Run tests (4 hrs)
- [ ] Fix issues (2 hrs)
- [ ] Documentation (2 hrs)

---

## Documentation Updates

**Files to Create**:
- `.aibrain/PHASE-1-INTEGRATION-PLAN.md` (this file)
- `.aibrain/PHASE-1-INTEGRATION-COMPLETE.md` (after completion)
- `docs/INTEGRATION-GUIDE.md` (how to integrate with existing systems)

**Files to Update**:
- `docs/multi-agent-operator-guide.md` (add operational integration section)
- `.aibrain/IMPLEMENTATION-PROGRESS.md` (update status)
- `STATE.md` (update current state)

---

## Rollout Strategy

### Phase 1: Internal Testing (Day 1-5)
- 100% multi-agent enabled in test environment
- Test with sample work queue tasks
- Verify routing, execution, SessionState

### Phase 2: Staged Rollout (Week 2)
- 10% multi-agent enabled (only high-confidence routes)
- Monitor carefully
- Adjust thresholds if needed

### Phase 3: Increased Adoption (Week 3)
- 25% multi-agent enabled
- More confident in routing decisions
- Monitor quality metrics

### Phase 4: Full Rollout (Week 4)
- 100% multi-agent enabled
- All high-value/complex tasks routed
- Production ready

---

## Go/No-Go Criteria

**Go Criteria** (Must Have):
- [ ] 113/113 tests passing
- [ ] No breaking changes to existing code
- [ ] Feature flag working
- [ ] SessionState persisting correctly
- [ ] Monitoring capturing metrics
- [ ] Documentation complete
- [ ] Team trained

**No-Go Criteria** (Would Rollback):
- Multiple test failures
- SessionState data corruption
- Context reset losing state
- Multi-agent much slower than single-agent
- Routing decisions clearly wrong

---

## Next Steps After Integration

**Phase 1 Complete**: All 8 steps + integration done ✅

**Phase 2 Ready to Start** (parallel):
- MCP Wrapping (Ralph, Git, DB, Deploy servers)
- Quick Wins (Langfuse monitoring, Chroma search)

**Phase 3 (after Phase 2)**:
- Production integration with autonomous loop
- Cost tracking and monitoring

**Phase 4 (after Phase 3)**:
- Real workflow validation (20-30 tasks)
- Quality/speed/cost metrics

---

## Contact & Questions

**Architecture**: See PHASE-1-THROUGH-5-ROADMAP.md
**Implementation**: See IMPLEMENTATION-PROGRESS.md
**Operations**: See docs/multi-agent-operator-guide.md
**Code**: Phase 1 files in orchestration/ and tests/

---

**Document Status**: Integration plan ready
**Start Date**: 2026-02-07 (after Phase 1 completion)
**Target Completion**: 2026-02-14
**Status**: 📋 READY TO PROCEED
