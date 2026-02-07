---
title: "Phase 2B: Launch Guide - Three Teamlead Agents Starting Now"
date: 2026-02-07
time: "23:55 UTC"
status: launching
---

# Phase 2B: Launch Guide 🚀

**Status**: ✅ **LAUNCHING NOW - THREE TEAMLEAD AGENTS**
**Project**: ai-orchestrator
**Timeline**: 7-10 days expected
**Real-Time Monitoring**: http://localhost:3000

---

## Quick Start (2 Minutes)

### Terminal 1: Start Dashboard
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator
npm run dev --prefix ui/dashboard
```
**Wait for**: "ready - started server on 0.0.0.0:3000"

### Terminal 2: Launch Agents
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator
python autonomous_loop.py \
  --project ai-orchestrator \
  --use-cli \
  --enable-monitoring \
  --max-iterations 50
```

### Browser
Open: `http://localhost:3000`

**You should see**: Three specialist agents appearing on kanban board in real-time.

---

## What to Expect

### Agents Starting (Next 1-2 minutes)

The autonomous loop will:
1. ✅ Load work queue for ai-orchestrator project
2. ✅ Initialize TeamLead orchestrator
3. ✅ Stream `task_start` event to dashboard
4. ✅ Analyze task requirements
5. ✅ Launch three specialists in parallel

### Three Specialists Launching

**Phase 2B-2: Chroma Semantic Search**
- Role: Implement ChromaKnowledgeStore
- Tests: 20+ (write first - TDD)
- Expected: 2-3 days
- Event: `specialist_started` → Kanban shows "Chroma: in_progress"

**Phase 2B-3: Agent Cost Tracking**
- Role: Implement AgentCostTracker (source of truth)
- Tests: 1,057 existing
- Expected: 2-3 days after Chroma
- Event: `specialist_started` → Kanban shows "Cost: in_progress"

**Phase 2B-1: Langfuse Monitoring**
- Role: Implement LangfuseMonitor (reads from Cost Tracker)
- Tests: 936 existing
- Expected: 2-3 days after Cost
- Event: `specialist_started` → Kanban shows "Langfuse: in_progress"

### Real-Time Progress (Continuous)

As agents work:
- ✅ Kanban board updates every iteration
- ✅ Status changes: in_progress → completed
- ✅ Iteration counts increment
- ✅ Duration tracked in real-time
- ✅ Verdicts appear: PASS / FAIL / BLOCKED

### Expected Completion Timeline

```
Day 1-3:   Chroma (2B-2)    [0% → COMPLETE]
Day 3-6:   Cost (2B-3)      [45% → COMPLETE]
Day 6-10:  Langfuse (2B-1)  [40% → COMPLETE]

Each agent: 2-3 days
Sequential merge required
Total: 7-10 days
```

---

## Kanban Board Display

### What You'll See

**Initial State** (T=0):
```
┌─────────────────────────────────────────┐
│  Task: Phase 2B Infrastructure Tests    │
│  Status: Starting                       │
│  ├─ Chroma:   [waiting]                │
│  ├─ Cost:     [waiting]                │
│  └─ Langfuse: [waiting]                │
└─────────────────────────────────────────┘
```

**Agents Launching** (T=1-2 min):
```
┌─────────────────────────────────────────┐
│  Chroma Semantic Search                 │
│  Status: in_progress                    │
│  Iterations: 0/20+  Duration: 2s        │
│  ├─ Test 1: PASS                       │
│  └─ Test 2: [running]                  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Agent Cost Tracking                    │
│  Status: in_progress                    │
│  Iterations: 0/1057  Duration: 1s       │
│  ├─ Test 1: PASS                       │
│  └─ Test 2: [running]                  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Langfuse Monitoring                    │
│  Status: in_progress                    │
│  Iterations: 0/936  Duration: 0s        │
│  └─ [waiting for Cost Tracker]          │
└─────────────────────────────────────────┘
```

**Agents Completing** (Day 3+):
```
┌─────────────────────────────────────────┐
│  Chroma Semantic Search                 │
│  Status: COMPLETE ✅                    │
│  Iterations: 24/20+  Duration: 47h 23m  │
│  Verdict: PASS ✅                       │
│  ├─ All tests passing                  │
│  └─ Ready to merge                     │
└─────────────────────────────────────────┘
```

---

## Monitoring Events (Real-Time)

All events stream to dashboard via WebSocket:

### Timeline of Events

```
T0:00     [task_start] Team Lead begins orchestration
T0:05     [multi_agent_analyzing] Analyzing task requirements
T0:15     [specialist_started] Chroma launching
T0:16     [specialist_started] Cost Tracking launching
T0:17     [specialist_started] Langfuse launching
T1:00+    [iteration N] Each agent iterates (TDD cycles)
Day 3:    [specialist_completed] Chroma PASS ✅
Day 6:    [specialist_completed] Cost PASS ✅
Day 10:   [specialist_completed] Langfuse PASS ✅
Day 10:   [multi_agent_synthesis] Merging results
Day 10:   [multi_agent_verification] Ralph verification
Day 10:   [task_complete] All agents done - Final verdict: PASS
```

---

## Agent Details

### Phase 2B-2: Chroma Semantic Search

**Objective**: Implement vector-based semantic search for Knowledge Objects

**Implementation**:
- File: `knowledge/semantic_search.py` (NEW)
- Tests: `tests/test_semantic_search.py` (20+ tests, write first)
- Integration: `knowledge/service.py` (enhance find_relevant())

**Key Components**:
- `ChromaKnowledgeStore` class with Chroma vector DB
- Hybrid search: semantic + tag-based
- Local embeddings (all-MiniLM-L6-v2)
- Performance target: < 100ms per query

**Success**: All 20+ tests passing, semantic search working, +20-30% KO discovery improvement

---

### Phase 2B-3: Agent Cost Tracking

**Objective**: Implement cost tracking system as source of truth

**Implementation**:
- File: `orchestration/agent_cost_tracker.py` (NEW)
- Tests: `tests/test_agent_cost_tracking.py` (726 lines, exist)
- Tests: `tests/test_specialist_cost_tracking.py` (331 lines, exist)
- Integration: `orchestration/iteration_loop.py` (lines 957-1097)

**Key Components**:
- `AgentCostTracker` class
- Per-operation cost recording
- Multi-agent aggregation
- SessionState integration

**Critical**: Source of truth for costs - Langfuse reads FROM this tracker (prevents double-counting)

**Success**: All 1,057 tests passing, cost tracking operational, no double-counting

---

### Phase 2B-1: Langfuse Monitoring

**Objective**: Implement real-time monitoring dashboard with Langfuse

**Implementation**:
- File: `orchestration/monitoring/langfuse_integration.py` (complete 60% → 100%)
- Tests: `tests/test_langfuse_integration.py` (936 lines, exist)
- Integration: `orchestration/iteration_loop.py` (lines 630-785)

**Key Components**:
- `LangfuseMonitor` class
- Trace and span lifecycle
- Cost aggregation (reads from AgentCostTracker)
- Dashboard integration

**Critical**: NEVER estimate costs - always read from AgentCostTracker

**Success**: All 936 tests passing, dashboard showing metrics, Langfuse cloud integration

---

## Progress Tracking

### How to Monitor

**Dashboard**: http://localhost:3000
- Real-time kanban board
- Status updates every iteration
- Verdicts update as tests pass

**Console Output**:
```bash
# Terminal 2 shows:
[INFO] TaskRouter: Multi-agent routing to TeamLead
[INFO] TeamLead: Starting orchestration for Task-1
[INFO] TeamLead: Launching 3 specialists in parallel
[INFO] Specialist[1]: Starting Chroma implementation
[INFO] Specialist[2]: Starting Cost Tracking implementation
[INFO] Specialist[3]: Starting Langfuse implementation
[INFO] Specialist[1]: Iteration 1 - Test: PASS, Code: generated
... (continuous updates)
[INFO] Specialist[1]: COMPLETE - Chroma PASS ✅
```

**Session Files**:
```bash
# Check progress
ls -la .aibrain/session-*.md
cat .aibrain/session-TASK-*.md | head -50
```

### What to Watch For

✅ **Good Signs**:
- Agents appear on dashboard within 30 seconds
- Status updates every 30-60 seconds
- Verdicts change from in_progress → completed
- Iteration counts increment
- Tests pass (green badges)

❌ **Problem Signs**:
- Agents don't appear after 1 minute
- Dashboard shows 500 errors
- WebSocket connection closes
- No status updates for > 5 minutes
- Tests fail repeatedly without progress

---

## Troubleshooting

### Issue: Agents Don't Appear on Kanban

**Check**:
1. Dashboard running? `http://localhost:3000` (should load)
2. Browser console errors? (open DevTools: F12)
3. WebSocket connected? (look for "ws://localhost:8080/ws" in logs)

**Fix**:
```bash
# Restart dashboard
npm run dev --prefix ui/dashboard

# Check WebSocket server
curl -v http://localhost:8080/health
```

### Issue: Agents Stuck in "in_progress"

**Check**:
1. Terminal 2 console output (look for errors)
2. Test failures (Red badges on dashboard)
3. Iteration stuck (duration not increasing)

**Fix**:
```bash
# Check for specific errors
grep ERROR .aibrain/session-TASK-*.md

# Re-run with verbose output
python autonomous_loop.py --project ai-orchestrator --use-cli --enable-monitoring --verbose
```

### Issue: WebSocket Connection Error

**Check**:
1. Is WebSocket server running? (should be in background)
2. Port 8080 available? `lsof -i :8080`
3. Firewall blocking?

**Fix**:
```bash
# Kill any process on 8080
lsof -i :8080 | grep -v PID | awk '{print $2}' | xargs kill -9

# Restart dashboard (includes WebSocket server)
npm run dev --prefix ui/dashboard
```

---

## Success Criteria

### Phase 2B Complete When:

✅ **Chroma (2B-2)**:
- [ ] All 20+ tests passing
- [ ] ChromaKnowledgeStore fully functional
- [ ] Semantic search integrated
- [ ] +20-30% KO discovery improvement
- [ ] Performance < 100ms
- [ ] Dashboard shows COMPLETE with PASS

✅ **Cost Tracking (2B-3)**:
- [ ] All 1,057 tests passing
- [ ] AgentCostTracker is source of truth
- [ ] Costs tracked per operation
- [ ] SessionState saves cost data
- [ ] Multi-agent aggregation working
- [ ] Dashboard shows COMPLETE with PASS

✅ **Langfuse (2B-1)**:
- [ ] All 936 tests passing
- [ ] LangfuseMonitor fully implemented
- [ ] Reads costs from AgentCostTracker
- [ ] Dashboard shows metrics
- [ ] Langfuse cloud integration
- [ ] Dashboard shows COMPLETE with PASS

### Overall Success:
- [ ] All three agents: COMPLETE ✅
- [ ] All tests passing: 2,093+ tests ✅
- [ ] No merge conflicts: Sequential merge successful ✅
- [ ] No double-counting: Cost architecture verified ✅
- [ ] Dashboard metrics: All visible and accurate ✅

---

## Timeline Tracking

Use this to track Phase 2B progress:

```
START: 2026-02-07 23:55 UTC
├─ Chroma starts: [waiting for start]
├─ Cost starts: [waiting for Chroma finish]
└─ Langfuse starts: [waiting for Cost finish]

EXPECTED DATES:
├─ Chroma complete: 2026-02-10 (day 3)
├─ Cost complete: 2026-02-13 (day 6)
└─ Langfuse complete: 2026-02-17 (day 10)

FINAL: 2026-02-17 [all agents COMPLETE]
```

---

## Key Commands

### Launch Phase 2B
```bash
python autonomous_loop.py --project ai-orchestrator --use-cli --enable-monitoring --max-iterations 50
```

### View Dashboard
```bash
http://localhost:3000
```

### Check Progress
```bash
# View latest session
cat .aibrain/session-TASK-*.md | tail -20

# Watch real-time logs
tail -f .aibrain/session-TASK-*.md

# Count passing tests
grep "PASS\|FAIL" .aibrain/session-TASK-*.md | wc -l
```

### If Agents Get Stuck
```bash
# Check last error
grep -i "error\|exception" .aibrain/session-TASK-*.md | tail -5

# View full session
cat .aibrain/session-TASK-*.md

# Restart
Ctrl+C to stop
python autonomous_loop.py --project ai-orchestrator --use-cli --enable-monitoring
```

---

## Next Steps After Phase 2B

Once all three agents complete (Day 10):

1. **Verify Integration**:
   - All tests passing ✅
   - No merge conflicts ✅
   - No double-counting ✅

2. **Phase 3 Begins**:
   - Integrate Phase 2B into IterationLoop
   - Test with real CredentialMate workflows
   - Set up production monitoring

3. **Deployment**:
   - Merge to main
   - Deploy to production
   - Monitor real usage

---

## Status

**🚀 PHASE 2B LAUNCHING NOW**

Dashboard: http://localhost:3000
Command: python autonomous_loop.py --project ai-orchestrator --use-cli --enable-monitoring
Timeline: 7-10 days
Agents: 3 (Chroma, Cost, Langfuse)
Tests: 2,093+ to pass

**WATCH THE KANBAN BOARD FOR REAL-TIME PROGRESS!**

