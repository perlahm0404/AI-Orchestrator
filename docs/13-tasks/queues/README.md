# Task Queue Directory

This directory contains work queues for autonomous agents.

## Structure

- **queues-active/** - Current active queues (3 files)
  - `cm-queue-active.json` - CredentialMate main queue
  - `km-queue-active.json` - KareMatch main queue
  - `g-queue-system.json` - System-wide queue

- **queues-feature/** - Feature-specific queues
  - `cm-queue-adr006.json` - ADR-006 specific tasks
  - `km-queue-features.json` - KareMatch feature queue
  - `g-queue-database-governance.json` - Database governance tasks

- **queues-archived/** - Compressed backups by month
  - `2026-01/` - January 2026 backups

## Usage

Autonomous agents read from `queues-active/` by default:

```python
# autonomous_loop.py reads from:
queue_path = f"tasks/queues-active/{project}-queue-active.json"
```

### Running Autonomous Loop

```bash
# CredentialMate tasks
python autonomous_loop.py --project credentialmate --max-iterations 100

# KareMatch tasks
python autonomous_loop.py --project karematch --max-iterations 100

# System-wide tasks
python autonomous_loop.py --project system --max-iterations 100
```

## Backup Policy

- **Daily backups**: Keep last 3 (timestamped: YYYYMMDD-HHMMSS)
- **Weekly backups**: Compress after 7 days (gzip)
- **Monthly backups**: Keep 90 days, then delete
- **Exception**: Mark preserve=true for backups requiring indefinite retention

### Manual Backup

```bash
# Create timestamped backup
cp tasks/queues-active/cm-queue-active.json \
   tasks/queues-archived/2026-01/cm-queue-backup-$(date +%Y%m%d-%H%M%S).json

# Compress old backups
find tasks/queues-archived -name "*.json" -mtime +7 -exec gzip {} \;
```

## Queue File Format

```json
{
  "project": "credentialmate",
  "features": [
    {
      "id": "TASK-ADR006-001",
      "description": "Implement CME gap calculation",
      "file": "backend/services/cme_service.py",
      "status": "pending",
      "agent_type": "FeatureBuilder",
      "completion_promise": "FEATURE_COMPLETE",
      "max_iterations": 50
    }
  ]
}
```

## Task States

| Status | Description |
|--------|-------------|
| `pending` | Not started |
| `in_progress` | Currently being executed by an agent |
| `blocked` | Waiting on external dependency |
| `completed` | Successfully completed (Ralph PASS) |
| `failed` | Failed after max iterations or guardrail violation |

## Current Active Queues

### CredentialMate (cm-queue-active.json)
- **Size**: 70KB
- **Tasks**: ~50 features
- **Last updated**: 2026-01-10 20:54
- **Primary agent**: FeatureBuilder

### KareMatch (km-queue-active.json)
- **Size**: 388KB
- **Tasks**: ~300+ tasks
- **Last updated**: 2026-01-09 22:07
- **Primary agent**: BugFix, TestWriter

### System (g-queue-system.json)
- **Size**: 18KB
- **Tasks**: ~10 system tasks
- **Last updated**: 2026-01-10 10:06
- **Primary agent**: CodeQuality

## Archived Backups

### 2026-01 Archive
```bash
$ ls -lh tasks/queues-archived/2026-01/
48K  work_queue_credentialmate.backup.20260107-233908.json.gz
```

**Compression Stats**: 913KB → 48KB (95% reduction)

## Related Documents

- **ADR-010**: Documentation Organization & Archival Strategy
- **DECISIONS.md**: Work queue consolidation decision
- **autonomous_loop.py**: Queue consumer (orchestration layer)
- **work/README.md**: Active work directory (higher-level planning)

## Queue Management

### Adding Tasks

```bash
# Edit active queue
vim tasks/queues-active/cm-queue-active.json

# Validate JSON
python -m json.tool tasks/queues-active/cm-queue-active.json
```

### Moving Completed Tasks

When all tasks in a feature queue are completed:

```bash
# Archive completed feature queue
mv tasks/queues-feature/cm-queue-adr006.json \
   tasks/queues-archived/2026-01/cm-queue-adr006-completed.json
```

## Migration History

**2026-01-10**: Reorganized from flat structure (9+ unclear files) to hierarchical (3 active, 3 feature, clear archival)

**Before**:
- work_queue.json, work_queue_credentialmate.json, work_queue_credentialmate_features.json...
- 913KB backup at root level
- No clear "current" queue

**After**:
- queues-active/{project}-queue-active.json (clear ownership)
- Compressed backups (95% size reduction)
- Feature-specific queues isolated
