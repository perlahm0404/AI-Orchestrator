# ADR Registry

**Last Updated**: 2026-01-10
**Purpose**: Central index of all Architecture Decision Records across all repositories
**Quick Link**: See [AI-Team-Plans/ADR-INDEX.md](../AI-Team-Plans/ADR-INDEX.md) for detailed global registry

**🆕 Active ADRs Location**: [work/adrs-active/](../work/adrs-active/) - Single lookup location for all active ADRs

---

## Quick Stats

- **Total ADRs**: 11
- **Approved**: 7
- **Draft**: 4
- **Projects**: 2 (AI_Orchestrator, CredentialMate)

---

## By Repository

### AI_Orchestrator

| ADR | Title | Status | Path |
|-----|-------|--------|------|
| ADR-003 | Lambda Cost Controls | ✅ complete | [work/adrs-active/g-ADR-003-lambda-cost-controls.md](../work/adrs-active/g-ADR-003-lambda-cost-controls.md) |
| ADR-004 | Resource Protection / Cost Guardian | ✅ complete | _(inline in ADR-INDEX)_ |
| ADR-010 | Documentation Organization & Archival Strategy | ✅ approved | [AI-Team-Plans/decisions/ADR-010-documentation-organization-archival-strategy.md](../AI-Team-Plans/decisions/ADR-010-documentation-organization-archival-strategy.md) |
| ADR-011 | Documentation Validation & Governance System | ✅ approved | [work/adrs-active/g-ADR-011-documentation-validation-governance.md](../work/adrs-active/g-ADR-011-documentation-validation-governance.md) |

### CredentialMate

| ADR | Title | Status | Path |
|-----|-------|--------|------|
| ADR-001 | Provider Report Generation | approved | [adapters/credentialmate/plans/decisions/ADR-001-provider-report-generation.md](../adapters/credentialmate/plans/decisions/ADR-001-provider-report-generation.md) |
| ADR-002 | CME Topic Hierarchy | approved | [adapters/credentialmate/plans/decisions/ADR-002-cme-topic-hierarchy.md](../adapters/credentialmate/plans/decisions/ADR-002-cme-topic-hierarchy.md) |
| ADR-005 | Business Logic Consolidation | ✅ approved | [adapters/credentialmate/plans/decisions/ADR-005-business-logic-consolidation.md](../adapters/credentialmate/plans/decisions/ADR-005-business-logic-consolidation.md) |
| ADR-006 | CME Gap Calculation Standardization | ✅ approved | [work/adrs-active/cm-ADR-006-cme-gap-calculation.md](../work/adrs-active/cm-ADR-006-cme-gap-calculation.md) |
| ADR-007 | Duplicate Handling Data Architecture | 📋 draft | [work/adrs-active/cm-ADR-007-duplicate-handling-data.md](../work/adrs-active/cm-ADR-007-duplicate-handling-data.md) |
| ADR-008 | Duplicate Handling Service Architecture | 📋 draft | [work/adrs-active/cm-ADR-008-duplicate-handling-service.md](../work/adrs-active/cm-ADR-008-duplicate-handling-service.md) |
| ADR-009 | Duplicate Handling User Experience | 📋 draft | [work/adrs-active/cm-ADR-009-duplicate-handling-ux.md](../work/adrs-active/cm-ADR-009-duplicate-handling-ux.md) |

### KareMatch

No ADRs yet.

---

## By Domain

| Domain | ADRs |
|--------|------|
| **Infrastructure** | ADR-003, ADR-004 |
| **Cost Management** | ADR-003, ADR-004 |
| **Agentic Systems** | ADR-003, ADR-004 |
| **Backend** | ADR-001, ADR-002, ADR-005, ADR-006, ADR-007, ADR-008 |
| **Data Modeling** | ADR-002, ADR-007 |
| **Architecture** | ADR-005, ADR-007, ADR-008 |
| **HIPAA Compliance** | ADR-001, ADR-005, ADR-006 |
| **User Experience** | ADR-009 |
| **Governance** | ADR-010 |
| **Documentation** | ADR-010 |

---

## External ADRs (in project repos)

### CredentialMate Repo

- [ADR-001 (copy)](../../credentialmate/AI-Team-Plans/decisions/ADR-001-provider-report-generation.md)
- [ADR Template](../../credentialmate/docs/15-kb/templates/adr.md)

---

## Templates

- [ADR Template](../templates/AI-Team-Plans/decisions/ADR-TEMPLATE.md) - Use this for new ADRs

---

## Next ADR Number

**ADR-011** (use this for the next decision)

---

## Related Resources

- [ADR-INDEX.md](../AI-Team-Plans/ADR-INDEX.md) - Global registry with tag and domain indexes
- [DECISIONS.md](../DECISIONS.md) - Build decisions for AI Orchestrator core
- [CATALOG.md](../CATALOG.md) - Master index of all documentation
