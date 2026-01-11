# ADR Index - Global Registry

**Last Updated**: 2026-01-11T09:10:00Z
**Total ADRs**: 14
**Numbering**: Global sequential (across all projects)

---

## ADR Registry

| ADR | Title | Project | Status | Date | Advisor |
|-----|-------|---------|--------|------|---------|
| ADR-001 | [Provider Report Generation](../adapters/credentialmate/plans/decisions/ADR-001-provider-report-generation.md) | CredentialMate | approved | 2026-01-10 | app-advisor |
| ADR-002 | [CME Topic Hierarchy](../adapters/credentialmate/plans/decisions/ADR-002-cme-topic-hierarchy.md) | CredentialMate | approved | 2026-01-10 | data-advisor |
| ADR-003 | [Lambda Cost Controls](decisions/ADR-003-lambda-cost-controls.md) | AI_Orchestrator | ✅ complete | 2026-01-10 | app-advisor |
| ADR-004 | Resource Protection / Cost Guardian | AI_Orchestrator | ✅ complete | 2026-01-10 | app-advisor |
| ADR-005 | [Business Logic Consolidation](../adapters/credentialmate/plans/decisions/ADR-005-business-logic-consolidation.md) | CredentialMate | ✅ approved | 2026-01-10 | app-advisor |
| ADR-006 | [CME Gap Calculation Standardization](../adapters/credentialmate/plans/decisions/ADR-006-implementation-prompt.md) | CredentialMate | 🚧 in-progress | 2026-01-10 | app-advisor |
| ADR-007 | Duplicate Handling Data Architecture | CredentialMate | 📝 draft | 2026-01-10 | data-advisor |
| ADR-008 | Duplicate Handling Service Architecture | CredentialMate | 📝 draft | 2026-01-10 | app-advisor |
| ADR-009 | Duplicate Handling User Experience | CredentialMate | 📝 draft | 2026-01-10 | uiux-advisor |
| ADR-010 | [Documentation Organization & Archival Strategy](decisions/ADR-010-documentation-organization-archival-strategy.md) | AI_Orchestrator | ✅ approved | 2026-01-10 | human-initiated |
| ADR-011 | [Meta-Agent Coordination Architecture](decisions/ADR-011-meta-agent-coordination-architecture.md) | AI_Orchestrator | ✅ approved | 2026-01-10 | human-designed |
| ADR-011-CM | [Documentation Organization (CredentialMate)](../adapters/credentialmate/plans/decisions/ADR-011-documentation-organization-archival-strategy.md) | CredentialMate | ✅ approved | 2026-01-10 | app-advisor |
| ADR-012 | [Validation Infrastructure Improvements](../adapters/credentialmate/plans/decisions/ADR-012-validation-infrastructure-improvements.md) | CredentialMate | ✅ approved | 2026-01-10 | app-advisor |
| ADR-013 | [Orchestrator Validation Infrastructure](decisions/ADR-013-orchestrator-validation-infrastructure.md) | AI_Orchestrator | ✅ approved | 2026-01-10 | app-advisor |

---

## By Project

### AI_Orchestrator (Core)
| ADR | Title | Status |
|-----|-------|--------|
| ADR-003 | Lambda Cost Controls & Agentic Guardrails | ✅ complete |
| ADR-004 | Resource Protection / Cost Guardian System | ✅ complete |
| ADR-010 | Documentation Organization & Archival Strategy | ✅ approved |
| ADR-011 | Meta-Agent Coordination Architecture (PM/CMO/Governance) | ✅ approved |
| ADR-013 | Orchestrator Validation Infrastructure - Type Safety | ✅ approved |

### CredentialMate
| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Provider Dashboard At-Risk/Urgent Report Generation | approved |
| ADR-002 | CME Topic Hierarchy for Cross-State Aggregation | approved |
| ADR-005 | Business Logic Consolidation - Backend Service as SSOT | ✅ approved |
| ADR-006 | CME Gap Calculation Standardization | 🚧 in-progress |
| ADR-007 | Duplicate Handling Data Architecture | 📝 draft |
| ADR-008 | Duplicate Handling Service Architecture | 📝 draft |
| ADR-009 | Duplicate Handling User Experience | 📝 draft |
| ADR-011-CM | Documentation Organization (CredentialMate-specific) | ✅ approved |
| ADR-012 | Validation Infrastructure Improvements | ✅ approved |

### KareMatch
(No ADRs yet)

---

## By Tag

| Tag | ADRs |
|-----|------|
| infrastructure | ADR-003 |
| lambda | ADR-003 |
| cost-control | ADR-003, ADR-004 |
| agentic | ADR-003, ADR-004 |
| guardrails | ADR-003, ADR-004 |
| resource-protection | ADR-004 |
| task-registration | ADR-004 |
| orchestration | ADR-004 |
| cme-compliance | ADR-002 |
| data-model | ADR-002 |
| topic-hierarchy | ADR-002 |
| provider-dashboard | ADR-001 |
| reporting | ADR-001 |
| business-logic | ADR-005 |
| technical-debt | ADR-005 |
| api-design | ADR-001, ADR-005 |
| ssot | ADR-005 |
| rules-engine | ADR-002, ADR-005 |
| hipaa-compliance | ADR-001, ADR-005 |

---

## By Domain

| Domain | ADRs |
|--------|------|
| infrastructure | ADR-003, ADR-004 |
| cost-management | ADR-003, ADR-004 |
| agentic-systems | ADR-003, ADR-004 |
| orchestration | ADR-004 |
| backend | ADR-001, ADR-002, ADR-005 |
| data | ADR-002 |
| rules-engine | ADR-002, ADR-005 |
| architecture | ADR-005 |
| governance | ADR-005 |
| data-integrity | ADR-005 |

---

## Next ADR Number

**ADR-014** (use this for the next decision)

**Note**: ADR-011-CM is a project-specific variant of the global ADR-011. Future ADRs should use unique global numbers.

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
            ├── ADR-002-*.md
            └── ADR-005-*.md
```
