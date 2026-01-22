# Mission Control Tools

Automated tools for managing work queues, kanban boards, and cross-repo coordination.

## Tools Overview

### 1. **audit_work_queue_status.py** - Status Sync Auditor (NEW!)

Automatically syncs work queue task status by scanning actual files in target repos.

**What it does:**
- Scans target repos for files specified in work queue tasks
- Checks if files exist and have substantive content (>50 lines)
- Updates task status based on file state:
  - `completed` - File exists with >50 lines of code
  - `in_progress` - File exists but <50 lines (stub)
  - `pending` - File doesn't exist
- Updates metadata: `completed_at`, `files_actually_changed`, `verification_verdict`

**Usage:**
```bash
# Audit all repos (preview changes)
python mission-control/tools/audit_work_queue_status.py --dry-run

# Audit and update karematch only
python mission-control/tools/audit_work_queue_status.py --repo karematch

# Audit all repos and apply updates
python mission-control/tools/audit_work_queue_status.py

# Show detailed output
python mission-control/tools/audit_work_queue_status.py --verbose
```

**Example Output:**
```
🔍 Work Queue Status Auditor
   Mode: LIVE (will update files)
   Repos: karematch

📊 Audit Report: karematch
   Tasks audited: 17
   Tasks need update: 2

   Task Details:
   • PROVIDER-006: pending → completed (exists: ✅, substantive: ✅)
   • PROVIDER-007: pending → in_progress (exists: ✅, substantive: ❌)

✅ Updated 2 tasks in /path/to/work-queues/karematch.json
```

**When to use:**
- After autonomous agents complete work
- When manual implementations are done
- To verify board accuracy
- Before generating reports

---

### 2. **sync_work_queues.py** - Work Queue Sync Tool

Syncs work queue files FROM target repos TO mission-control.

**What it does:**
- Copies work queue JSON files from target repos (e.g., `karematch/tasks/work_queue_karematch.json`)
- Places them in `mission-control/work-queues/` for centralized tracking
- Tracks checksums to detect changes

**Usage:**
```bash
# Sync all repos
python mission-control/tools/sync_work_queues.py --all

# Sync specific project
python mission-control/tools/sync_work_queues.py --project karematch
```

**When to use:**
- After creating new work queues in target repos
- After manual edits to work queues
- Before running kanban aggregation

---

### 3. **aggregate_kanban.py** - Kanban Board Generator

Aggregates objectives, ADRs, and tasks into unified kanban board.

**What it does:**
- Reads objectives from `{repo}/vibe-kanban/objectives/*.yaml`
- Reads ADRs from `{repo}/vibe-kanban/adrs/*.yaml`
- Reads tasks from `mission-control/work-queues/{repo}.json`
- Links tasks → ADRs → objectives
- Calculates completion percentages
- Generates unified board (JSON + Markdown)

**Usage:**
```bash
# Generate unified board
python mission-control/tools/aggregate_kanban.py
```

**Output:**
- `mission-control/vibe-kanban/unified-board.json` - Machine-readable
- `mission-control/vibe-kanban/unified-board.md` - Human-readable

**When to use:**
- After updating work queues
- After completing tasks
- Before reviewing project status
- When generating reports

---

## Typical Workflows

### Workflow 1: After Autonomous Agent Session

**Problem:** Agents completed work but board shows 0% progress

**Solution:**
```bash
# Step 1: Audit actual file state
python mission-control/tools/audit_work_queue_status.py --repo karematch

# Step 2: Regenerate board
python mission-control/tools/aggregate_kanban.py

# Step 3: View updated board
cat mission-control/vibe-kanban/unified-board.md
```

---

### Workflow 2: Starting New Objective

**Steps:**
```bash
# 1. Create objective YAML in target repo
vim /path/to/karematch/vibe-kanban/objectives/OBJ-KM-003.yaml

# 2. Create ADRs for objective
vim /path/to/karematch/vibe-kanban/adrs/ADR-KM-003-001.yaml

# 3. Create work queue in target repo
vim /path/to/karematch/tasks/work_queue_karematch_feature_x.json

# 4. Sync to mission control
python mission-control/tools/sync_work_queues.py --project karematch

# 5. Generate board
python mission-control/tools/aggregate_kanban.py

# 6. Start autonomous loop
python autonomous_loop.py --project karematch --max-iterations 100
```

---

### Workflow 3: Manual Status Update

**When:** You manually implemented features outside autonomous loop

**Steps:**
```bash
# Option A: Let auditor detect changes
python mission-control/tools/audit_work_queue_status.py --repo karematch

# Option B: Manual edit
vim mission-control/work-queues/karematch.json
# Change task status to "completed"

# Then regenerate board
python mission-control/tools/aggregate_kanban.py
```

---

## File Locations

### AI_Orchestrator (Execution Engine)
```
/Users/tmac/1_REPOS/AI_Orchestrator/
├── mission-control/
│   ├── work-queues/           ← Synced work queues (centralized)
│   │   ├── karematch.json
│   │   └── credentialmate.json
│   ├── vibe-kanban/
│   │   ├── unified-board.json ← Aggregated board data
│   │   └── unified-board.md   ← Human-readable board
│   └── tools/
│       ├── audit_work_queue_status.py  ← NEW: Status auditor
│       ├── sync_work_queues.py         ← Queue sync
│       └── aggregate_kanban.py         ← Board generator
└── tasks/                     ← Legacy work queues (deprecated)
    └── work_queue_*.json
```

### Target Repos (KareMatch, CredentialMate)
```
/Users/tmac/1_REPOS/karematch/
├── vibe-kanban/
│   ├── objectives/
│   │   └── OBJ-KM-002.yaml    ← Objective definitions
│   └── adrs/
│       ├── ADR-KM-002-001.yaml ← Architecture decisions
│       └── ADR-KM-002-002.yaml
├── tasks/
│   └── work_queue_karematch.json ← Source work queue
└── [actual code files]         ← Implementations
```

---

## Troubleshooting

### Issue: Board shows 0% but work is done

**Cause:** Work queue not synced with actual file state

**Fix:**
```bash
# Run status auditor
python mission-control/tools/audit_work_queue_status.py --repo karematch

# Regenerate board
python mission-control/tools/aggregate_kanban.py
```

---

### Issue: Tasks marked complete but files don't exist

**Cause:** Manual status update without implementation

**Fix:**
```bash
# Audit will detect and revert
python mission-control/tools/audit_work_queue_status.py --repo karematch

# Tasks will be set back to "pending"
```

---

### Issue: Work queue changes not reflected in board

**Cause:** Need to regenerate board after edits

**Fix:**
```bash
python mission-control/tools/aggregate_kanban.py
```

---

## Best Practices

### 1. **Run Auditor After Each Session**
```bash
# After autonomous loop or manual work
python mission-control/tools/audit_work_queue_status.py --repo karematch
python mission-control/tools/aggregate_kanban.py
```

### 2. **Use Dry-Run First**
```bash
# Preview changes before applying
python mission-control/tools/audit_work_queue_status.py --dry-run
```

### 3. **Keep Work Queues in Target Repos**
- Work queues live in `{repo}/tasks/work_queue_*.json`
- Use `sync_work_queues.py` to copy to mission-control
- Don't edit mission-control copies directly (they get overwritten)

### 4. **Commit Board Updates**
```bash
# After regenerating board
git add mission-control/vibe-kanban/unified-board.*
git commit -m "chore: update kanban board - 4/17 tasks complete"
```

---

## Future Enhancements

Potential improvements for these tools:

1. **Real-time File Watching**
   - Auto-detect file changes and update status immediately
   - Use `watchdog` library

2. **Git Integration**
   - Detect task completion from commit messages
   - Extract task IDs from commits (e.g., "feat: PROVIDER-001 - ...")

3. **Test Coverage Analysis**
   - Check if test files exist for completed features
   - Mark tasks as `needs_tests` if missing

4. **ADR Compliance Check**
   - Verify implementations follow ADR patterns
   - Flag deviations from architectural decisions

5. **Slack/Discord Notifications**
   - Post updates when tasks complete
   - Alert when objectives reach milestones (25%, 50%, 75%, 100%)

---

**Last Updated:** 2026-01-19
**Maintainer:** AI Orchestrator Team
