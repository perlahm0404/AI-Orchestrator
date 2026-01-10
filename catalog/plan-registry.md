# Plan Registry

**Last Updated**: 2026-01-10
**Purpose**: Central index of all implementation plans and project blueprints across all repositories

---

## Quick Stats

- **AI_Orchestrator**: 10+ active plans
- **KareMatch**: 20+ archived plans
- **CredentialMate**: Limited (most work via ADRs)

---

## AI_Orchestrator Plans

### Active Plans

| Title | Path | Status |
|-------|------|--------|
| KareMatch Production Completion Plan | [plans/karematch-production-completion-plan.md](../plans/karematch-production-completion-plan.md) | 🔄 Active |
| CME Systemic Fix Plan | [plans/CME-SYSTEMIC-FIX-PLAN.md](../plans/CME-SYSTEMIC-FIX-PLAN.md) | 🔄 Active |
| CredentialMate Internalization Plan | [docs/plans/credentialmate-internalization-plan.md](../docs/plans/credentialmate-internalization-plan.md) | 📋 Planned |
| TN CME DEA Rules Update Plan | [docs/plans/tn-cme-dea-rules-update-plan.md](../docs/plans/tn-cme-dea-rules-update-plan.md) | ✅ Complete |
| Database Governance v2 Implementation | [docs/plans/database-governance-v2-implementation.md](../docs/plans/database-governance-v2-implementation.md) | 📋 Planned |
| Nextera Provider Import Plan | [docs/plans/nextera-provider-import-plan.md](../docs/plans/nextera-provider-import-plan.md) | 📋 Planned |
| CredentialMate Branch Cleanup Investigation | [docs/plans/credentialmate-branch-cleanup-investigation.md](../docs/plans/credentialmate-branch-cleanup-investigation.md) | 🔍 Investigation |

### .claude Plans (System Implementation)

| Title | Path | Status |
|-------|------|--------|
| Claude CLI Integration Execution Plan | [.claude/plans/claude-cli-integration-execution-plan.md](../.claude/plans/claude-cli-integration-execution-plan.md) | ✅ Complete |
| Autonomous Agent Improvements | [.claude/plans/autonomous-agent-improvements.md](../.claude/plans/autonomous-agent-improvements.md) | ✅ Complete |
| Autonomous Implementation Plan | [.claude/plans/autonomous-implementation-plan.md](../.claude/plans/autonomous-implementation-plan.md) | ✅ Complete |

### CredentialMate Adapter Plans

| Title | Path | Status |
|-------|------|--------|
| Architecture Overview | [adapters/credentialmate/plans/ARCHITECTURE_OVERVIEW.md](../adapters/credentialmate/plans/ARCHITECTURE_OVERVIEW.md) | 📖 Reference |
| Implementation Plan ADR-001 | [adapters/credentialmate/plans/IMPLEMENTATION_PLAN_ADR001.md](../adapters/credentialmate/plans/IMPLEMENTATION_PLAN_ADR001.md) | 🔄 Active |
| Tech Debt 001: Ad Hoc Logic Divergence Remediation | [adapters/credentialmate/plans/TECH-DEBT-001-adhoc-logic-divergence-remediation.md](../adapters/credentialmate/plans/TECH-DEBT-001-adhoc-logic-divergence-remediation.md) | 🔄 Active |

---

## KareMatch Plans

### Active Plans

| Title | Path | Status |
|-------|------|--------|
| Manual Hook Trigger Implementation | [../../karematch/.claude/plans/manual-hook-trigger-implementation.md](../../karematch/.claude/plans/manual-hook-trigger-implementation.md) | 📋 Planned |

### Archived/Superseded Plans

Located in `karematch/docs/archive/plans/superseded/` (20+ plans from Dec 2025):

**Infrastructure & Deployment**:
- Autonomous Playwright Implementation (plan-20251222-001)
- Dev Env Health Fix (plan-20251222-002)
- Drizzle ORM Version Fix Project (plan-20251222-003)

**Code Quality**:
- QA Observability Validation Results (plan-20251222-012)
- Phase 1 Completion (plan-20251222-007)
- Phase Completion Assessment (plan-20251222-010)

**Refactoring**:
- Therapist Search Permanent Fix (plan-20251226-015)
- Therapist UI Refactor Quick Start (plan-20251226-016)
- Refactoring Project (plan-20251226-014)
- Phase 3 Trend Analysis Recommendation (plan-20251226-012)

**Documentation**:
- README Handoff (plan-20251225-014)
- Phase 3 Detailed File Mapping (plan-20251226-010)
- Phase 3 Root Files Case by Case Review (plan-20251226-011)

**Integration**:
- Ollama Integration Strategy (plan-20251222-006)
- Next.js Migration Blueprint (plan-20251223-001)

---

## CredentialMate Plans

Most CredentialMate planning happens via ADRs (see [adr-registry.md](./adr-registry.md)).

Limited standalone plans in the CredentialMate repo itself.

---

## Plan Categories

### By Type

| Type | Count | Examples |
|------|-------|----------|
| **System Implementation** | 3 | Claude CLI, Autonomous Agent |
| **Feature Plans** | 4 | ADR-001 Implementation, CME Systemic Fix |
| **Tech Debt** | 2 | Ad Hoc Logic Divergence, Branch Cleanup |
| **Infrastructure** | 3 | Database Governance, Nextera Import |
| **Refactoring** | 5+ | Therapist Search, UI Refactor |
| **Investigation** | 1 | Branch Cleanup Investigation |

### By Status

| Status | Meaning | Count |
|--------|---------|-------|
| ✅ Complete | Fully implemented | 6+ |
| 🔄 Active | Currently in progress | 4 |
| 📋 Planned | Ready to start | 4 |
| 🔍 Investigation | Research phase | 1 |
| 🗄️ Superseded | Archived (completed or obsolete) | 20+ |

---

## Plan Template

Located at: `templates/AI-Team-Plans/PLAN-TEMPLATE.md` (if exists)

**Standard sections**:
- Context / Background
- Goals & Success Criteria
- Implementation Steps
- Files to Modify
- Testing Strategy
- Rollback Plan
- Related ADRs

---

## Search Tips

**Find active plans**:
```bash
find . -name "*plan*.md" -not -path "*/archive/*" | grep -v superseded
```

**Search by keyword**:
```bash
grep -r "keyword" plans/ docs/plans/ adapters/*/plans/
```

**List by date (most recent first)**:
```bash
ls -lt plans/*.md docs/plans/*.md
```

---

## Related Resources

- [adr-registry.md](./adr-registry.md) - Architecture decisions
- [session-registry.md](./session-registry.md) - Session handoffs
- [CATALOG.md](../CATALOG.md) - Master documentation index
- [STATE.md](../STATE.md) - Current implementation status
