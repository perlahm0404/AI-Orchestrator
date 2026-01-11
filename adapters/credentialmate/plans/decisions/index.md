# Architecture Decision Records: CredentialMate

This directory contains Architecture Decision Records (ADRs) for the CredentialMate project, managed through the AI_Orchestrator global ADR system.

---

## Index

| ID | Title | Status | Date | Advisor |
|----|-------|--------|------|---------|
| ADR-001 | Provider Dashboard At-Risk/Urgent Report Generation | approved | 2026-01-09 | app-advisor |
| ADR-002 | CME Topic Hierarchy | approved | 2026-01-09 | data-advisor |
| ADR-005 | Business Logic Consolidation | approved | 2026-01-10 | app-advisor |
| ADR-006 | CME Gap Calculation Standardization | approved | 2026-01-10 | app-advisor |
| ADR-007 | Duplicate Handling Data Architecture | draft | 2026-01-10 | data-advisor |
| ADR-008 | Duplicate Handling Service Architecture | draft | 2026-01-10 | app-advisor |
| ADR-009 | Duplicate Handling User Experience | draft | 2026-01-10 | uiux-advisor |
| ADR-011 | Documentation Organization & Archival Strategy | approved | 2026-01-10 | app-advisor |

---

## ADR Numbering

**Note**: ADR-003 and ADR-004 were skipped in this sequence.

---

## Status Definitions

- **draft**: Awaiting approval from tmac
- **approved**: Approved for implementation
- **implemented**: Implementation complete
- **deprecated**: No longer applies
- **superseded**: Replaced by another ADR

---

## How to Use

1. ADRs are created by strategic advisors (data-advisor, app-advisor, uiux-advisor)
2. All ADRs are stored in AI_Orchestrator repo at `/adapters/credentialmate/plans/decisions/`
3. Coordinator agents break ADRs into implementation tasks
4. After tmac approval, status changes from `draft` to `approved`
5. After implementation, status changes to `implemented`

---

## Related Documentation

- **Implementation Plans**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/*.md`
- **Task Queues**: `/Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_credentialmate_features.json`
- **Architecture Overview**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/ARCHITECTURE_OVERVIEW.md`

---

<!--
SYSTEM SECTION - DO NOT EDIT
-->

```yaml
_system:
  version: "1.0"
  project: "credentialmate"
  orchestrator_path: "/Users/tmac/1_REPOS/AI_Orchestrator"
  adr_count: 8
  last_updated: "2026-01-10T23:00:00Z"
```
