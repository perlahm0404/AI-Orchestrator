---
doc-id: "g-guide-pm-reports"
title: "PM Status Reports Guide"
created: "2026-01-10"
updated: "2026-01-11"
author: "Claude AI"
status: "active"

compliance:
  soc2:
    controls: ["CC7.3", "CC8.1"]
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.12.1.1"]
    classification: "internal"
    review-frequency: "quarterly"

project: "ai-orchestrator"
domain: "pm-reporting"
relates-to: ["ADR-015"]

version: "1.0"
---

# PM Status Reports

**Version**: v6.1
**Purpose**: Weekly + on-demand status reports for product management oversight

---

## Report Format

Each report is generated in **3 formats**:

| Format | Filename | Purpose |
|--------|----------|---------|
| **Markdown** | `{project}-{date}.md` | Human-readable with emojis and formatting |
| **Grid** | `{project}-{date}-grid.txt` | Plain ASCII tables (parseable, no emojis) |
| **JSON** | `{project}-{date}.json` | Machine-readable for programmatic access |

---

## Report Contents

### 1. Task Summary
- Total tasks (pending, in-progress, complete, blocked)
- Percentage breakdown

### 2. ADR Rollup
- Tasks grouped by ADR (Architecture Decision Record)
- Progress tracking per ADR
- Evidence coverage per ADR

### 3. Evidence Coverage
- % of ADRs with evidence
- Gap to 80% target

### 4. Meta-Agent Verdicts
- CMO (GTM tasks)
- Governance (risk assessment) - coming soon
- COO (resource management) - coming soon

### 5. Blockers
- Top blockers requiring attention
- Linked to ADRs

---

## Generating Reports

### On-Demand

```bash
# Generate report (console output only)
aibrain pm report --project credentialmate

# Generate and save in all 3 formats
aibrain pm report --project credentialmate --save
```

### Weekly Automation

**Coming Soon**: Automatic Friday morning reports via cron job

```bash
# Add to crontab (future)
0 9 * * 5 cd /Users/tmac/1_REPOS/AI_Orchestrator && .venv/bin/aibrain pm report --project credentialmate --save
```

---

## Report Locations

```
work/reports/
├── credentialmate-2026-01-10.md         # Markdown
├── credentialmate-2026-01-10-grid.txt   # Grid (parseable)
├── credentialmate-2026-01-10.json       # JSON
├── credentialmate-2026-01-17.md         # Next week...
└── ...
```

---

## Reading Reports

### Markdown (Human)
```bash
cat work/reports/credentialmate-2026-01-10.md
```

### Grid (Parse)
```bash
cat work/reports/credentialmate-2026-01-10-grid.txt | grep "ADR-006"
```

### JSON (Programmatic)
```bash
cat work/reports/credentialmate-2026-01-10.json | jq '.adrs[] | select(.progress_pct < 50)'
```

---

## Integration

Reports read from existing systems:
- **Task Queues**: `tasks/queues-active/*.json`, `tasks/queues-feature/*.json`
- **ADR Index**: `AI-Team-Plans/ADR-INDEX.md`
- **Evidence**: `evidence/EVIDENCE-*.md`

---

## Next Steps (Phase 2)

1. **App Feature Mapping**: Link tasks to app features/functions
2. **Friday Automation**: Auto-generate reports every Friday 9am
3. **Queryability**: Drill-down, filtering, search capabilities
4. **Cross-Agent Integration**: Pull from Governance/COO when they deploy

---

**Generated**: 2026-01-10
**Phase**: Phase 1 - FIRST REPORT COMPLETE ✅
