# ADR Registry

**Last Updated**: 2026-01-10
**Purpose**: Central index of all Architecture Decision Records across all repositories
**Quick Link**: See [AI-Team-Plans/ADR-INDEX.md](../AI-Team-Plans/ADR-INDEX.md) for detailed global registry

---

## Quick Stats

- **Total ADRs**: 5
- **Approved**: 4
- **Draft**: 1
- **Projects**: 2 (AI_Orchestrator, CredentialMate)

---

## By Repository

### AI_Orchestrator

| ADR | Title | Status | Path |
|-----|-------|--------|------|
| ADR-003 | Lambda Cost Controls | ✅ complete | [AI-Team-Plans/decisions/ADR-003-lambda-cost-controls.md](../AI-Team-Plans/decisions/ADR-003-lambda-cost-controls.md) |
| ADR-004 | Resource Protection / Cost Guardian | ✅ complete | _(inline in ADR-INDEX)_ |

### CredentialMate

| ADR | Title | Status | Path |
|-----|-------|--------|------|
| ADR-001 | Provider Report Generation | approved | [adapters/credentialmate/plans/decisions/ADR-001-provider-report-generation.md](../adapters/credentialmate/plans/decisions/ADR-001-provider-report-generation.md) |
| ADR-002 | CME Topic Hierarchy | approved | [adapters/credentialmate/plans/decisions/ADR-002-cme-topic-hierarchy.md](../adapters/credentialmate/plans/decisions/ADR-002-cme-topic-hierarchy.md) |
| ADR-005 | Business Logic Consolidation | 📋 draft | [adapters/credentialmate/plans/decisions/ADR-005-business-logic-consolidation.md](../adapters/credentialmate/plans/decisions/ADR-005-business-logic-consolidation.md) |

### KareMatch

No ADRs yet.

---

## By Domain

| Domain | ADRs |
|--------|------|
| **Infrastructure** | ADR-003, ADR-004 |
| **Cost Management** | ADR-003, ADR-004 |
| **Agentic Systems** | ADR-003, ADR-004 |
| **Backend** | ADR-001, ADR-002, ADR-005 |
| **Data Modeling** | ADR-002 |
| **Architecture** | ADR-005 |
| **HIPAA Compliance** | ADR-001, ADR-005 |

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

**ADR-006** (use this for the next decision)

---

## Related Resources

- [ADR-INDEX.md](../AI-Team-Plans/ADR-INDEX.md) - Global registry with tag and domain indexes
- [DECISIONS.md](../DECISIONS.md) - Build decisions for AI Orchestrator core
- [CATALOG.md](../CATALOG.md) - Master index of all documentation
