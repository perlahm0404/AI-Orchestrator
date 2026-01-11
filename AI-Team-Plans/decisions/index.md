# Architecture Decision Records: AI_Orchestrator

This directory contains Architecture Decision Records (ADRs) for the AI_Orchestrator project.

---

## Index

| ID | Title | Status | Date | Advisor |
|----|-------|--------|------|---------|
| ADR-010 | Documentation Organization & Archival Strategy | approved | 2026-01-10 | app-advisor |
| ADR-010-AMENDMENT | Priority-Based Numbering System | approved | 2026-01-10 | app-advisor |
| ADR-011 | Meta-Agent Coordination Architecture | approved | 2026-01-10 | app-advisor |
| ADR-013 | AI_Orchestrator Validation Infrastructure - Type Safety Enforcement | approved | 2026-01-10 | app-advisor |

---

## ADR Numbering

**Note**: ADR-012 was allocated to CredentialMate validation infrastructure improvements.

**Numbering Strategy**: Priority-based allocation (see ADR-010-AMENDMENT) ensures critical/blocking ADRs get lower numbers.

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
2. All ADRs are stored in AI_Orchestrator repo at `/AI-Team-Plans/decisions/`
3. Coordinator agents break ADRs into implementation tasks
4. After tmac approval, status changes from `draft` to `approved`
5. After implementation, status changes to `implemented`

---

## Related Documentation

- **Implementation Plans**: `/AI-Team-Plans/plans/*.md`
- **Architecture Overview**: `/CLAUDE.md`
- **State Management**: `/STATE.md`

---

<!--
SYSTEM SECTION - DO NOT EDIT
-->

```yaml
_system:
  version: "1.0"
  project: "ai_orchestrator"
  orchestrator_path: "/Users/tmac/1_REPOS/AI_Orchestrator"
  adr_count: 4
  last_updated: "2026-01-10T23:59:00Z"
```
