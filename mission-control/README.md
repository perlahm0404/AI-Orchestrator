# Mission Control - Centralized Multi-Repo Observability

**Version**: 1.0 (Phase A)
**Created**: 2026-01-18
**Purpose**: Centralized visibility and coordination for AI Orchestrator across karematch, credentialmate, and ai-orchestrator repos

---

## Directory Structure

```
mission-control/
├── README.md                  # This file - navigation hub
├── DASHBOARD.md               # Human-readable status overview (auto-generated)
├── work-queues/               # Aggregated work from all repos
│   ├── aggregate-view.json    # Combined queue stats
│   ├── karematch.json         # Mirror of karematch queue
│   ├── credentialmate.json    # Mirror of credentialmate queue
│   └── sync-metadata.json     # Last sync times, checksums
├── vibe-kanban/               # Cross-repo kanban
│   ├── unified-board.md       # Human-readable combined board
│   └── unified-board.json     # Machine-readable state
├── metrics/                   # Performance tracking
│   ├── agent-performance.json # Per-agent metrics
│   ├── repo-performance.json  # Per-repo aggregates
│   └── autonomy-trends.json   # Autonomy % over time
├── issues/                    # Centralized issue tracking
│   ├── issues-log.md          # Human-readable tracker
│   └── issues-log.json        # Machine-readable database
└── tools/                     # Mission control utilities
    ├── sync_work_queues.py    # Sync queues from all repos
    ├── aggregate_kanban.py    # Combine kanban boards
    ├── collect_metrics.py     # Gather performance metrics
    └── generate_dashboard.py  # Create DASHBOARD.md
```

---

## Quick Start

### Sync Work Queues
```bash
# Sync all repos
python mission-control/tools/sync_work_queues.py --all

# Sync specific repo
python mission-control/tools/sync_work_queues.py --project karematch

# View aggregate stats
cat mission-control/work-queues/aggregate-view.json
```

### Generate Dashboard
```bash
# Generate human-readable overview
python mission-control/tools/generate_dashboard.py

# View dashboard
cat mission-control/DASHBOARD.md
```

### View Unified Kanban
```bash
# Aggregate all objectives/ADRs/tasks
python mission-control/tools/aggregate_kanban.py

# View unified board
cat mission-control/vibe-kanban/unified-board.md
```

---

## Protocols

### Work Queue Sync Protocol

**Purpose**: Maintain read-only mirrors of work queues from target repos

**Source of Truth**: Target repos (`karematch/tasks/work_queue_karematch.json`, etc.)

**Sync Strategy**:
1. **Read-only**: Mission Control never writes back to source queues
2. **Checksum validation**: MD5 hash to detect changes
3. **Timestamp tracking**: Last sync time recorded in `sync-metadata.json`
4. **Automatic**: File watcher monitors source files for changes
5. **Manual**: `sync_work_queues.py` can be run on-demand

**Sync Frequency**:
- Auto (file watcher): Instant (on source file change)
- Manual: On-demand via CLI
- Fallback (cron): Every 15 minutes (if file watcher unavailable)

**Data Integrity**:
- Checksums compared before/after sync
- Sync failures logged to `mission-control/issues/issues-log.json`
- Stale data flagged if >1 hour since last successful sync

---

### Kanban Aggregation Logic

**Purpose**: Combine objectives, ADRs, and tasks from all repos into unified board

**Data Sources**:
1. **Objectives**: `vibe-kanban/objectives/*.yaml` (each repo)
2. **ADRs**: `docs/decisions/ADR-*.md` (karematch, credentialmate) | `decisions/ADR-*.md` (ai-orchestrator)
3. **Tasks**: Work queue data (from sync)

**Linking Logic**:
- Objectives → ADRs (via ADR tags or explicit links in objectives)
- ADRs → Tasks (via task descriptions matching ADR numbers)

**Completion Tracking**:
- Objective completion % = (completed tasks / total tasks) * 100
- Only counts tasks explicitly linked to objective via ADRs

**Output Format**:
- `unified-board.json`: Machine-readable with full metadata
- `unified-board.md`: Human-readable Markdown table

---

### Metrics Collection Schedule

**Purpose**: Track agent/repo performance over time

**Collection Frequency**: Hourly snapshots

**Data Sources**:
1. `agents/coordinator/metrics.py` → AIHRDashboard
2. `governance/metrics/agent_performance.jsonl` → Per-task records
3. `knowledge/metrics.json` → KO effectiveness

**Metrics Tracked**:

**Per-Agent**:
- Success rate (% tasks completed without escalation)
- Average iterations per task
- Escalation rate (% tasks escalated to human)
- Total tasks completed

**Per-Repo**:
- Autonomy % (tasks completed without human intervention)
- Human intervention rate
- Tasks pending/in_progress/completed/blocked
- Avg task completion time

**Trends**:
- Autonomy % over time (7-day, 30-day)
- Success rate trends by agent type
- Escalation frequency patterns

**Storage**:
- Hourly snapshots appended to JSON files
- Retention: 90 days (auto-purge older data)

---

### Issue Tracking Workflow

**Purpose**: Centralize issues across all repos

**Auto-Detection**:
- Tasks blocked >3 days → Auto-create issue
- Ralph BLOCKED verdicts → Flag for review
- Agent escalations → Log as issue
- Governance violations → Critical issue

**Issue Lifecycle**:
1. **Created**: Auto-detected or manually created
2. **Triaged**: CITO or human assigns priority (P0/P1/P2)
3. **Assigned**: Routed to appropriate team/agent
4. **In Progress**: Agent working on resolution
5. **Resolved**: Issue fixed, verification pending
6. **Closed**: Verified resolved, archived

**Priority Levels**:
- **P0 (Critical)**: Blocks users, production down
- **P1 (High)**: Degrades UX, blocks development
- **P2 (Medium)**: Tech debt, optimization

**Fields**:
- ID (ISS-YYYY-NNN format)
- Title
- Description
- Priority (P0/P1/P2)
- Status (created/triaged/assigned/in_progress/resolved/closed)
- Created/Updated timestamps
- Assigned to (team/agent)
- Related tasks (task IDs)
- Resolution notes

---

## CLI Integration

### Planned Commands (via `aibrain` CLI)

```bash
# Work Queue Sync
aibrain queue sync --all              # Sync all repos
aibrain queue sync --project karematch  # Sync one repo
aibrain queue status                  # Show aggregate-view.json

# Kanban
aibrain kanban refresh                # Re-aggregate all boards
aibrain kanban show                   # Display unified-board.md

# Dashboard
aibrain mission dashboard             # Generate & show DASHBOARD.md
aibrain mission refresh               # Refresh all data

# Issues
aibrain issues list                   # Show all open issues
aibrain issues create                 # Create new issue (interactive)
aibrain issues resolve ISS-2026-001   # Mark resolved
```

---

## File Formats

### aggregate-view.json
```json
{
  "last_sync": "2026-01-18T18:30:00Z",
  "repos": {
    "karematch": {
      "total": 253,
      "pending": 251,
      "in_progress": 0,
      "blocked": 0,
      "completed": 2,
      "last_updated": "2026-01-18T18:30:00Z"
    },
    "credentialmate": { ... },
    "ai-orchestrator": { ... }
  },
  "summary": {
    "total_tasks": 300,
    "pending": 280,
    "in_progress": 5,
    "blocked": 3,
    "completed": 12
  },
  "alerts": [
    {
      "type": "long_blocked",
      "task_id": "TASK-123",
      "blocked_since": "2026-01-15T10:00:00Z",
      "duration_hours": 72
    }
  ]
}
```

### sync-metadata.json
```json
{
  "karematch": {
    "source_path": "/Users/tmac/1_REPOS/karematch/tasks/work_queue_karematch.json",
    "last_sync": "2026-01-18T18:30:00Z",
    "checksum": "abc123def456",
    "status": "success"
  },
  "credentialmate": { ... }
}
```

---

## Integration Points

### With Tmux Monitors
- Repo monitors read from mission-control mirrors (optional)
- Dashboards can pull from mission-control metrics
- No circular dependencies (monitors work standalone)

### With Autonomous Loop
- Autonomous loop reads source queues (not mirrors)
- Mission control observes, never modifies
- Sync runs in background, no blocking

### With CITO Delegation (Phase C)
- CITO reads aggregate-view.json for task routing
- Issues escalated to CITO logged in issues/
- Delegation decisions tracked in metrics/

---

## Maintenance

### Data Retention
- Work queue mirrors: 7 days (rolling)
- Metrics snapshots: 90 days
- Issues (closed): 180 days
- Kanban snapshots: 30 days

### Cleanup
```bash
# Auto-cleanup runs daily via cron
python mission-control/tools/cleanup.py

# Manual cleanup
python mission-control/tools/cleanup.py --force
```

### Backup
- Mission control data backed up to `.aibrain/backups/mission-control/` daily
- Retention: 14 days

---

## Troubleshooting

### Work queue sync not updating
1. Check file watcher: `ps aux | grep watchdog`
2. Check last sync time: `cat mission-control/work-queues/sync-metadata.json`
3. Manual sync: `python mission-control/tools/sync_work_queues.py --project <name>`

### Dashboard shows stale data
1. Check last refresh: `head -10 mission-control/DASHBOARD.md`
2. Force refresh: `python mission-control/tools/generate_dashboard.py --force`

### Metrics not collecting
1. Check cron job: `crontab -l | grep collect_metrics`
2. Manual collection: `python mission-control/tools/collect_metrics.py`
3. Check logs: `tail -100 mission-control/metrics/.collection.log`

---

## References

- [Mission Control Implementation Plan](../sessions/2026-01-18-mission-control-plan.md)
- [Phase B Test Results](../sessions/2026-01-18-phase-b-test-results.md)
- [AI Orchestrator CLAUDE.md](../CLAUDE.md)

---

**Last Updated**: 2026-01-18
**Maintained By**: AI Orchestrator Team
