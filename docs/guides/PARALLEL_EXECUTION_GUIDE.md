# Parallel Execution Guide - Provider E2E
**Created**: 2026-01-19
**Strategy**: Option A - Maximum Parallelization

## 🎯 Three Parallel Tracks

### Track 1: Credentialing UI (Primary Queue)
**Status**: PROVIDER-005 in progress
**Queue**: `tasks/work_queue_karematch_provider_onboarding.json`
**Tasks**: PROVIDER-005 → 006 → 007 → 008
**Estimated Time**: 8-10 hours remaining

### Track 2: Backend Critical Path (NEW - Start NOW)
**Status**: Ready to launch
**Queue**: `tasks/work_queue_karematch_backend.json`
**Tasks**: PROVIDER-010 → 012 → 013 → 014 → 015
**Estimated Time**: 12 hours
**🔥 HIGH VALUE**: Unblocks profile publication workflow

### Track 3: Patient-Facing (After Track 2 completes 013)
**Status**: Queued for later
**Tasks**: PROVIDER-009, 017, 018, 016
**Trigger**: After PROVIDER-013 completes

---

## 🚀 Launch Commands

### Terminal 1: Monitor Current Work (Already Running)
If not already running, start:
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator
python autonomous_loop.py --project karematch --max-iterations 50
```

### Terminal 2: Launch Backend Critical Path (START NOW) ⭐
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# Launch autonomous loop on backend queue (uses features queue slot)
.venv/bin/python autonomous_loop.py \
  --project karematch \
  --queue features \
  --max-iterations 30 \
  --non-interactive

# What this does:
# - Processes tasks/work_queue_karematch_features.json (now contains backend tasks)
# - Runs PROVIDER-010 → 012 → 013 → 014 → 015
# - Non-interactive mode auto-handles any blocks
```

### Terminal 3: Reserved for Patient-Facing Work
Wait for PROVIDER-013 to complete, then:
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# Create patient-facing queue (to be done later)
# python autonomous_loop.py --project karematch --task-id PROVIDER-009
```

---

## 📊 Progress Monitoring

### Check Overall Status
```bash
# View unified kanban board
cat mission-control/vibe-kanban/unified-board.md

# Check both work queues
jq '.summary' tasks/work_queue_karematch_provider_onboarding.json
jq '.summary' tasks/work_queue_karematch_backend.json
```

### Monitor Individual Tracks
```bash
# Track 1: Credentialing UI
tail -f tasks/work_queue_karematch_provider_onboarding.json

# Track 2: Backend critical path
tail -f tasks/work_queue_karematch_backend.json

# Ralph verification logs
tail -f /Users/tmac/1_REPOS/karematch/.aibrain/ralph-verification.log
```

---

## ⚙️ Key Design Decisions

### Why PROVIDER-010 Can Run in Parallel
**Original Dependency**: PROVIDER-008 (frontend submission UI)
**Rationale for Removal**:
- PROVIDER-010 is a backend API endpoint (`PATCH /api/admin/therapists/:id/approve`)
- PROVIDER-008 is frontend UI for credential submission
- These are **technically independent** - API doesn't need UI to be built
- Parallel development is standard practice for full-stack teams
- Integration tested at the end via E2E tests (PROVIDER-016)

### Dependency Chain Preserved
```
PROVIDER-010 (Admin approval API)
    ↓
PROVIDER-012 (Event handler: publication)
    ↓
PROVIDER-013 (Search filter: approved only)
    ↓
PROVIDER-014 (Dashboard status badge)
    ↓
PROVIDER-015 (Email notification)
```

---

## 🎉 Expected Outcomes

### By End of Parallel Execution
- ✅ All credentialing UI steps complete (005-008)
- ✅ Backend publication workflow complete (010, 012, 013)
- ✅ Dashboard + email features complete (014, 015)
- ✅ Ready for patient-facing work (009, 017, 018)
- ✅ ~20 hours of work done in ~12 hours (60% time savings)

### Integration Point
After both tracks complete:
1. Run E2E test (PROVIDER-016) to validate full flow
2. Manual verification: signup → onboard → credential → approve → searchable
3. Complete remaining tasks (009, 017, 018)
4. Final E2E test again

---

## 🚨 Risk Mitigation

### If Tracks Conflict
- Ralph verification will catch integration issues
- Git branch strategy: both write to same branch, conflicts resolved during commit
- Autonomous loop auto-retries on Ralph FAIL

### If Backend Completes First
- Track 2 completes, idle waits
- Track 1 continues
- No blockers - backend endpoints ready for frontend integration

### If UI Completes First
- Track 1 completes, moves to next tasks
- Track 2 continues independently
- Can immediately start PROVIDER-009 (availability wizard)

---

## 📝 Session Continuity

If interrupted, resume with:
```bash
# Both loops will auto-resume from last checkpoint
python autonomous_loop.py --project karematch --max-iterations 50
python autonomous_loop.py --project karematch --work-queue tasks/work_queue_karematch_backend.json --max-iterations 30
```

State is externalized in:
- Work queue JSON files (task status)
- `.aibrain/agent-loop.local.md` (iteration state)
- Git commits (completed work)

---

**Ready to Launch**: Terminal 2 command is ready to execute NOW
