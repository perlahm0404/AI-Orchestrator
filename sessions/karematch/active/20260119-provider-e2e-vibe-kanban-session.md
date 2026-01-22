# KareMatch Provider E2E - Vibe Kanban Execution Session

**Created**: 2026-01-19
**Objective**: OBJ-KM-002 - Provider E2E Experience (Onboarding to Bookable)
**Priority**: P0 - BLOCKS MARKETPLACE LAUNCH
**Tracking**: Vibe Kanban Board
**Status**: ACTIVE

---

## 🎯 COPY THIS PROMPT TO NEW SESSION

```
CONTEXT: I'm implementing the KareMatch provider end-to-end experience using the
new Vibe Kanban board tracking system. This is a P0 objective that unblocks
marketplace launch.

PROJECT LOCATION: /Users/tmac/1_REPOS/karematch

OBJECTIVE: OBJ-KM-002 - Complete provider journey from signup through being
bookable by patients. This is tracked in the Vibe Kanban system.

VIBE KANBAN TRACKING:
- Objective: /Users/tmac/1_REPOS/karematch/vibe-kanban/objectives/OBJ-KM-002.yaml
- ADRs: /Users/tmac/1_REPOS/karematch/vibe-kanban/adrs/ADR-KM-002-*.yaml
- Unified Board: /Users/tmac/1_REPOS/AI_Orchestrator/mission-control/vibe-kanban/unified-board.md
- Work Queue: /Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_karematch_provider_onboarding.json

VIEW CURRENT STATUS:
cat /Users/tmac/1_REPOS/AI_Orchestrator/mission-control/vibe-kanban/unified-board.md

ARCHITECTURAL DECISIONS (Read these first):
1. ADR-KM-002-001: Remix Migration Strategy
   - Incremental migration: legacy → Remix
   - Tasks: PROVIDER-001 (signup), PROVIDER-002 (onboarding)

2. ADR-KM-002-002: Credentialing Wizard Completion
   - Complete steps 5-10 in Remix
   - Tasks: PROVIDER-003 through PROVIDER-008

3. ADR-KM-002-003: Profile Publication Workflow (CRITICAL!)
   - Missing logic that makes approved providers searchable
   - Tasks: PROVIDER-010, PROVIDER-012, PROVIDER-013, PROVIDER-014, PROVIDER-015

4. ADR-KM-002-004: Patient Booking Integration
   - Complete the loop: availability → search → book
   - Tasks: PROVIDER-009, PROVIDER-017, PROVIDER-018, PROVIDER-016

DETAILED PLAN (Optional reference):
/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-ORCHESTRATOR/14-Karematch-Plans/07-PROVIDER-ONBOARDING-PLAN.md

YOUR MISSION:
Implement the provider e2e journey following the ADRs. As you work:

1. BEFORE STARTING: Read the ADRs to understand architectural decisions
2. AS YOU WORK: Update task descriptions in work queue with ADR references
3. WHEN YOU COMPLETE TASKS: Update the vibe kanban board
4. TRACK PROGRESS: Objective completion % auto-calculates from linked tasks

START WITH: PROVIDER-001 (Therapist Signup Migration to Remix)
- Read ADR-KM-002-001 for migration strategy
- Check current state in karematch repo
- Implement following Remix patterns (loaders, actions, forms)
- Test thoroughly
- Commit with ADR reference in commit message

HOW TO UPDATE VIBE KANBAN BOARD:
cd /Users/tmac/1_REPOS/AI_Orchestrator

# After completing tasks, regenerate unified board
/Users/tmac/1_REPOS/AI_Orchestrator/.venv/bin/python mission-control/tools/aggregate_kanban.py

# View updated status
cat mission-control/vibe-kanban/unified-board.md

SUCCESS CRITERIA:
- [ ] All 18 tasks complete (see work queue)
- [ ] All 4 ADRs implemented
- [ ] OBJ-KM-002 completion_pct = 100%
- [ ] E2E test passes (PROVIDER-016)
- [ ] Patients can book appointments with approved providers

AUTONOMOUS MAINTENANCE:
As you work, the vibe kanban board is maintained by:
1. You update task status in work_queue_karematch_provider_onboarding.json
2. Aggregate script reads tasks + links to ADRs
3. ADRs linked to objectives
4. Completion % calculated automatically
5. Unified board regenerates with current status

QUESTIONS TO ASK:
- Should I start with PROVIDER-001 immediately or audit current state first?
- Do you want me to work sequentially or parallelize where possible?
- Should I update the vibe kanban board after each task or at milestones?
```

---

## 📋 Vibe Kanban Autonomous Maintenance

### How It Works

**1. Objective → ADR → Task Hierarchy**
```
OBJ-KM-002 (Provider E2E Experience)
  │
  ├─ ADR-KM-002-001 (Remix Migration)
  │    ├─ PROVIDER-001 (Signup)
  │    └─ PROVIDER-002 (Onboarding)
  │
  ├─ ADR-KM-002-002 (Credentialing)
  │    ├─ PROVIDER-003 (Step 5)
  │    ├─ PROVIDER-004 (Step 6)
  │    ├─ PROVIDER-005 (Step 7)
  │    ├─ PROVIDER-006 (Step 8)
  │    ├─ PROVIDER-007 (Step 9)
  │    └─ PROVIDER-008 (Step 10)
  │
  ├─ ADR-KM-002-003 (Profile Publication) 🔴 CRITICAL
  │    ├─ PROVIDER-010 (Admin approval)
  │    ├─ PROVIDER-012 (Publication logic)
  │    ├─ PROVIDER-013 (Search filter)
  │    ├─ PROVIDER-014 (Dashboard)
  │    └─ PROVIDER-015 (Email notification)
  │
  └─ ADR-KM-002-004 (Patient Booking)
       ├─ PROVIDER-009 (Availability)
       ├─ PROVIDER-017 (Profile view)
       ├─ PROVIDER-018 (Booking flow)
       └─ PROVIDER-016 (E2E test)
```

**2. Linking Tasks to ADRs**

Tasks in `work_queue_karematch_provider_onboarding.json` reference ADRs:
```json
{
  "id": "PROVIDER-001",
  "title": "Migrate therapist signup to Remix",
  "description": "Following ADR-KM-002-001 migration strategy...",
  "adr_references": ["ADR-KM-002-001"],
  "status": "pending"
}
```

**3. Progress Calculation**

Objective completion % auto-calculates:
```
completion_pct = (completed_tasks_linked_to_obj_adrs / total_tasks_linked) * 100
```

Example:
- 18 total tasks linked via ADRs
- 5 tasks completed
- completion_pct = (5/18) * 100 = 27.8%

**4. Board Update Workflow**

```bash
# Agent completes PROVIDER-001
# Updates work queue JSON: status = "completed"

# Agent regenerates board
cd /Users/tmac/1_REPOS/AI_Orchestrator
.venv/bin/python mission-control/tools/aggregate_kanban.py

# Board now shows:
# OBJ-KM-002 | karematch | Provider E2E... | active | ██░░░░░░░░ 5.6% | 1/18
```

**5. Autonomous Agent Workflow**

When running autonomous loop:
```bash
python autonomous_loop.py --project karematch --max-iterations 100
```

Agent automatically:
1. Reads next pending task from work queue
2. Reads linked ADR for architectural guidance
3. Implements following ADR decisions
4. Commits with ADR reference
5. Updates task status to "completed"
6. Regenerates vibe kanban board
7. Moves to next task

---

## 🎨 ADR-Driven Development

### Why ADRs Matter

**Traditional Approach** (before vibe kanban):
- Task: "Migrate signup to Remix"
- Developer: "How? What patterns? Why Remix?"
- **CONTEXT MISSING**: Developer guesses or asks repeatedly

**ADR-Driven Approach** (with vibe kanban):
- Task: "Migrate signup to Remix (ADR-KM-002-001)"
- Developer reads ADR: "Use loaders for SSR, actions for forms, incremental migration"
- **CONTEXT EMBEDDED**: Architectural decision provides guidance
- Consistency: All migrations follow same pattern

### ADR Template for Future Objectives

```yaml
id: ADR-{OBJ-ID}-{SEQ}
objective_id: OBJ-KM-002
title: "Short decision title"
context: |
  Why this decision is needed.
  What's the current state.
  What problem are we solving.
decision: |
  The architectural decision made.
  Step-by-step approach.
  Patterns to follow.
consequences:
  - "✅ Benefit 1"
  - "✅ Benefit 2"
  - "❌ Trade-off 1"
  - "⚠️ Risk to manage"
status: accepted | proposed | superseded
tasks:
  - TASK-001  # Links to work queue
  - TASK-002
target_repos:
  - karematch
estimated_complexity: low | medium | high
```

---

## 📊 Tracking Progress

### View Unified Board
```bash
cat /Users/tmac/1_REPOS/AI_Orchestrator/mission-control/vibe-kanban/unified-board.md
```

### View Specific Objective
```bash
cat /Users/tmac/1_REPOS/karematch/vibe-kanban/objectives/OBJ-KM-002.yaml
```

### View ADRs
```bash
ls /Users/tmac/1_REPOS/karematch/vibe-kanban/adrs/
cat /Users/tmac/1_REPOS/karematch/vibe-kanban/adrs/ADR-KM-002-003-profile-publication-workflow.yaml
```

### Check Work Queue
```bash
cat /Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_karematch_provider_onboarding.json | jq '.summary'
```

---

## 🔄 Session Continuity

### If Session Interrupted

1. **Resume with context**:
   - Read unified board to see current completion %
   - Check work queue to see which task was in progress
   - Read ADR for that task to recall architectural decision

2. **No state loss**:
   - All progress tracked in files (objectives, ADRs, work queue)
   - Board regenerates from files
   - ADRs provide consistent guidance across sessions

3. **Handoff to new agent/session**:
   ```
   Current status: OBJ-KM-002 at 27.8% (5/18 tasks complete)
   Last task completed: PROVIDER-002 (Onboarding wizard)
   Next task: PROVIDER-003 (Credentialing step 5)
   ADR to follow: ADR-KM-002-002 (Credentialing completion)
   ```

---

## 🚀 Launch Readiness

### Exit Criteria

OBJ-KM-002 is complete when:
- [x] completion_pct = 100%
- [x] All 4 ADRs implemented
- [x] E2E test passes (PROVIDER-016)
- [x] Manual verification:
  - [ ] Provider can complete full onboarding
  - [ ] Admin can approve providers
  - [ ] Approved providers visible in patient search
  - [ ] Patients can book appointments

### What This Unlocks

After OBJ-KM-002 completion:
- ✅ Marketplace has supply (therapists)
- ✅ Patients can search and book
- ✅ MVP launch ready
- ✅ Can onboard real providers for beta testing

---

**Document Owner**: AI Orchestrator
**Objective**: OBJ-KM-002
**ADRs**: 4 architectural decisions
**Tasks**: 18 implementation tasks
**Status**: READY FOR EXECUTION
