# Mission Control Dashboard

**Last Updated**: 2026-01-18 18:47:31
**Version**: AI Orchestrator v6.0

---

## System Health

**Status**: 🔴 CRITICAL

| Metric | Value |
|---|---|
| Total Tasks | 253 |
| Pending | 251 |
| In Progress | 0 |
| Blocked | 0 |
| Completed | 2 |

---

## Repo Status

| Repo | Total | Pending | In Progress | Blocked | Completed | Autonomy |
|---|---|---|---|---|---|---|
| 🔴 karematch | 253 | 251 | 0 | 0 | 2 | 0.8% |
| 🔴 credentialmate | 0 | 0 | 0 | 0 | 0 | 0.0% |

---

## Agent Performance

*No agent metrics available*

## Vibe Kanban Overview

- **Objectives**: 0
- **ADRs**: 1
- **Tasks**: 253


---

## Alerts & Issues

✅ No active alerts

---

## Quick Actions

```bash
# Refresh all data
python mission-control/tools/sync_work_queues.py --all
python mission-control/tools/aggregate_kanban.py
python mission-control/tools/collect_metrics.py
python mission-control/tools/generate_dashboard.py

# View specific data
cat mission-control/work-queues/aggregate-view.json
cat mission-control/vibe-kanban/unified-board.md
cat mission-control/metrics/agent-performance.json
```
