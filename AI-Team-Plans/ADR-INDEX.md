# ADR Index - Global Registry

**Last Updated**: 2026-01-10T14:50:00Z
**Total ADRs**: 3
**Numbering**: Global sequential (across all projects)

---

## ADR Registry

| ADR | Title | Project | Status | Date | Advisor |
|-----|-------|---------|--------|------|---------|
| ADR-001 | [Provider Report Generation](../adapters/credentialmate/plans/decisions/ADR-001-provider-report-generation.md) | CredentialMate | approved | 2026-01-10 | app-advisor |
| ADR-002 | [CME Topic Hierarchy](../adapters/credentialmate/plans/decisions/ADR-002-cme-topic-hierarchy.md) | CredentialMate | approved | 2026-01-10 | data-advisor |
| ADR-003 | [Lambda Cost Controls](decisions/ADR-003-lambda-cost-controls.md) | AI_Orchestrator | approved | 2026-01-10 | app-advisor |

---

## By Project

### AI_Orchestrator (Core)
| ADR | Title | Status |
|-----|-------|--------|
| ADR-003 | Lambda Cost Controls & Agentic Guardrails | approved |

### CredentialMate
| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Provider Dashboard At-Risk/Urgent Report Generation | approved |
| ADR-002 | CME Topic Hierarchy for Cross-State Aggregation | approved |

### KareMatch
(No ADRs yet)

---

## By Tag

| Tag | ADRs |
|-----|------|
| infrastructure | ADR-003 |
| lambda | ADR-003 |
| cost-control | ADR-003 |
| agentic | ADR-003 |
| guardrails | ADR-003 |
| cme-compliance | ADR-002 |
| data-model | ADR-002 |
| topic-hierarchy | ADR-002 |
| provider-dashboard | ADR-001 |
| reporting | ADR-001 |

---

## By Domain

| Domain | ADRs |
|--------|------|
| infrastructure | ADR-003 |
| cost-management | ADR-003 |
| agentic-systems | ADR-003 |
| backend | ADR-001, ADR-002 |
| data | ADR-002 |
| rules-engine | ADR-002 |

---

## Next ADR Number

**ADR-004** (use this for the next decision)

---

## Numbering Convention

- **Global sequential**: All ADRs share one sequence regardless of project
- **Format**: `ADR-XXX` where XXX is zero-padded 3-digit number
- **Tasks**: `TASK-{ADR#}-{SEQ}` (e.g., TASK-003-001)

## ADR Locations

```
AI_Orchestrator/
├── AI-Team-Plans/
│   ├── ADR-INDEX.md          ← This file (global registry)
│   └── decisions/
│       └── ADR-003-*.md      ← Core orchestrator ADRs
└── adapters/
    └── credentialmate/
        └── plans/decisions/
            ├── ADR-001-*.md  ← CredentialMate ADRs
            └── ADR-002-*.md
```
