# Agent Activation Guide

## Current Status

Based on the oversight report, all agents are currently **inactive** (F grade, 0 tasks executed):

| Agent | Status | Tasks | Recommendation |
|-------|--------|-------|----------------|
| BugFix | Inactive | 0 | Ready to activate |
| CodeQuality | Inactive | 0 | Ready to activate |
| FeatureBuilder | Inactive | 0 | Ready to activate |
| TestWriter | Inactive | 0 | Ready to activate |
| **CMEDataValidator** | Created | 0 | Phase 3 - Ready |

**Current Autonomy**: 37% (target: >90%)

---

## What "Agent Activation" Means

Agent activation = Running the autonomous loop so agents execute tasks:

1. **Work Queue Populated** → Tasks available for agents
2. **Autonomous Loop Running** → Agents process tasks iteratively
3. **Agents Executing** → Tasks completed, autonomy increases
4. **Oversight Monitoring** → Performance metrics tracked

---

## Activation Process

### Step 1: Populate Work Queue

Generate tasks for agents to work on:

```bash
# Option A: Bug Discovery (automated)
aibrain discover-bugs --project karematch
aibrain discover-bugs --project credentialmate

# Option B: Manual Task Creation
# Edit tasks/work_queue_<project>.json directly
```

**Expected Output**:
- Lint errors → CodeQuality agent
- Type errors → BugFix agent
- Test failures → TestWriter agent
- Feature requests → FeatureBuilder agent

### Step 2: Start Autonomous Loop

Run the Wiggum-integrated autonomous system:

```bash
# KareMatch (L2 autonomy - higher)
python autonomous_loop.py --project karematch --max-iterations 100

# CredentialMate (L1 autonomy - stricter, HIPAA)
python autonomous_loop.py --project credentialmate --max-iterations 50
```

**What Happens**:
1. Loop pulls next pending task from work queue
2. Creates appropriate agent (BugFix, CodeQuality, etc.)
3. Agent iterates with Wiggum control (15-50 retries)
4. Ralph verifies every iteration (PASS/FAIL/BLOCKED)
5. On BLOCKED: Asks human (Revert/Override/Abort)
6. On COMPLETED: Commits to git, moves to next task
7. Repeat until queue empty or max iterations reached

### Step 3: Monitor Execution

Track agent performance in real-time:

```bash
# Watch progress file
tail -f /path/to/project/claude-progress.txt

# Check work queue status
jq '.summary' tasks/work_queue_<project>.json

# View session logs
ls -ltr sessions/*.md | tail -5
```

### Step 4: Review Results

After autonomous execution completes:

```bash
# Generate oversight report
aibrain oversight report --period daily

# Check agent performance
aibrain oversight report --period weekly
```

**Expected Improvements**:
- Autonomy: 37% → 85-95%
- Tasks/session: 22.5 → 30-50
- Agent grades: F → A/B/C
- Bottlenecks identified and addressed

---

## Current Blockers

### Why Agents Are Inactive (37% Autonomy)

1. **No Pending Tasks**: All queues empty or completed
   - CredentialMate: 0 pending, 8 complete
   - KareMatch: No work queue yet

2. **Bug Discovery Not Run**: Queues not populated
   - Need to scan codebases for tasks

3. **Autonomous Loop Not Running**: No active execution
   - Loop not started yet

---

## Activation Commands (Ready to Run)

### Quick Start - KareMatch

```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# 1. Discover bugs (populate queue)
/Users/tmac/1_REPOS/AI_Orchestrator/.venv/bin/python -m cli discover-bugs --project karematch

# 2. Review discovered tasks
jq '.summary' tasks/work_queue_karematch.json
jq '.features[] | select(.status == "pending") | {id, description, priority}' tasks/work_queue_karematch.json

# 3. Start autonomous execution
python autonomous_loop.py --project karematch --max-iterations 50

# 4. Monitor (in separate terminal)
watch -n 5 'jq ".summary" tasks/work_queue_karematch.json'
```

### Quick Start - CredentialMate

```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# 1. Discover bugs
/Users/tmac/1_REPOS/AI_Orchestrator/.venv/bin/python -m cli discover-bugs --project credentialmate

# 2. Review tasks
jq '.summary' tasks/work_queue_credentialmate.json

# 3. Start autonomous execution (L1 = stricter)
python autonomous_loop.py --project credentialmate --max-iterations 30

# 4. Monitor progress
tail -f /Users/tmac/1_REPOS/credentialmate/claude-progress.txt
```

---

## Agent-Specific Activation

### BugFix Agent

**Triggers**: Lint errors, import errors, small fixes

**Config**: 15 iterations max, BUGFIX_COMPLETE promise

**Activation**: Populate queue with lint/type errors

```bash
# Discover bugs that trigger BugFix
aibrain discover-bugs --project karematch --sources lint,typecheck
```

### CodeQuality Agent

**Triggers**: Code smells, dead code, refactoring

**Config**: 20 iterations max, CODEQUALITY_COMPLETE promise

**Activation**: Manual tasks or quality analysis

```json
{
  "id": "QUALITY-001",
  "description": "Remove unused imports in components/",
  "agent": "codequality",
  "max_iterations": 20
}
```

### FeatureBuilder Agent

**Triggers**: New features, enhancements

**Config**: 50 iterations max, FEATURE_COMPLETE promise

**Activation**: Feature requests from work queue

```bash
# Use feature work queue
cp tasks/work_queue_credentialmate_features_converted.json tasks/work_queue_credentialmate.json
```

### TestWriter Agent

**Triggers**: Test failures, missing coverage

**Config**: 15 iterations max, TESTS_COMPLETE promise

**Activation**: Discover test failures

```bash
aibrain discover-bugs --project karematch --sources test
```

### CMEDataValidator Agent

**Triggers**: Schema changes, business rule updates, manual invocation

**Config**: 10 iterations max (deterministic), L1 autonomy

**Activation**: Manual CLI or CI/CD integration

```bash
# Direct invocation (not via autonomous loop)
python -m agents.domain.cme_data_validator /Users/tmac/1_REPOS/credentialmate

# Add to CI/CD (pre-deployment)
# .github/workflows/deploy.yml:
#   - name: CME Validation
#     run: python -m agents.domain.cme_data_validator /app/credentialmate
```

---

## Safety Controls

### Kill Switch

Emergency stop if needed:

```bash
# Stop all operations
aibrain emergency-stop

# Resume
aibrain resume
```

### Circuit Breaker

Automatic limits prevent runaway execution:
- Max cost per task: $0.20
- Max iterations: 15-50 (agent-specific)
- Max runtime: 30 minutes per task

### Human Approval Points

Agents will ask for approval on:
- BLOCKED verdicts (guardrail violations)
- Schema changes (migrations)
- New dependencies
- Production deployments

---

## Expected Timeline

### First Activation (KareMatch)

- **Bug Discovery**: 2-5 minutes
- **Queue Population**: 10-30 tasks discovered
- **Autonomous Execution**: 30-90 minutes
- **Autonomy Improvement**: 37% → 80%+

### Steady State (After Activation)

- **Weekly bug discovery**: Automated (cron)
- **Continuous execution**: Agents process queue daily
- **Oversight reports**: Daily/weekly/quarterly
- **Autonomy target**: 90%+ sustained

---

## Next Steps

1. ✅ **Phase 1-3 Complete**: Bloat eliminated, oversight built, CME validator created
2. 🔄 **Phase 4: Activation** (Current)
   - Run bug discovery for KareMatch
   - Start autonomous loop
   - Monitor agent execution
3. 📊 **Phase 5: Optimization**
   - Review weekly oversight reports
   - Consolidate agents based on data
   - Fine-tune iteration budgets
   - Expand to more projects

---

## Files Generated During Activation

```
/Users/tmac/1_REPOS/AI_Orchestrator/
├── tasks/
│   └── work_queue_karematch.json          # Populated queue
├── sessions/
│   └── 2026-01-11-autonomous-session.md   # Session handoff
├── reports/
│   ├── oversight-daily-2026-01-11.md      # Before activation
│   └── oversight-daily-2026-01-12.md      # After activation
└── .aibrain/
    └── agent-loop.local.md                # State persistence

/Users/tmac/1_REPOS/karematch/
└── claude-progress.txt                     # Real-time progress
```

---

## Success Criteria

**Activation Successful When**:
- ✅ Work queue has pending tasks
- ✅ Autonomous loop running
- ✅ Agents executing tasks (grade improves from F)
- ✅ Autonomy increases (37% → 80%+)
- ✅ Tasks completing without human intervention
- ✅ Ralph PASS rates >85%
- ✅ Oversight reports show agent activity

**Current Status**: ⏸️ **Ready to Activate** (queues empty, loop not started)

---

**To activate now, run**:

```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator
/Users/tmac/1_REPOS/AI_Orchestrator/.venv/bin/python -m cli discover-bugs --project karematch
python autonomous_loop.py --project karematch --max-iterations 50
```
