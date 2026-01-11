# Evidence Registry

**Last Updated**: 2026-01-10T23:45:00Z
**Total Evidence Items**: 2

---

## Active Evidence

| ID | Type | Project | Priority | Status | Linked ADRs |
|----|------|---------|----------|--------|-------------|
| [EVIDENCE-001](EVIDENCE-001-ca-np-cme-tracking.md) | bug-report | credentialmate | P0 (blocks user) | captured | ADR-006 |
| [EVIDENCE-002](EVIDENCE-002-cme-gap-calculation-contradictions.md) | bug-report | credentialmate | P1 (degrades UX) | captured | ADR-006 |

---

## By Project

### CredentialMate (2 items)
- **EVIDENCE-001**: CA NP CME tracking (incorrect hours requirement)
- **EVIDENCE-002**: CME gap calculation contradictions (dashboard vs state detail)

### KareMatch (0 items)
(No evidence captured yet)

### AI_Orchestrator (0 items)
(No evidence captured yet)

---

## By Priority

| Priority | Count | Evidence IDs |
|----------|-------|--------------|
| P0 (blocks user) | 1 | EVIDENCE-001 |
| P1 (degrades UX) | 1 | EVIDENCE-002 |

---

## By Type

| Type | Count | Evidence IDs |
|------|-------|--------------|
| bug-report | 2 | EVIDENCE-001, EVIDENCE-002 |
| feature-request | 0 | - |
| user-feedback | 0 | - |

---

## Linked to ADRs

### ADR-006 (CME Gap Calculation Standardization)
- EVIDENCE-001: CA NP CME tracking
- EVIDENCE-002: CME gap calculation contradictions ← **Primary evidence**

---

## Evidence Capture Workflow

1. **Capture**: Create `EVIDENCE-XXX-*.md` with frontmatter
2. **Link**: Add to `linked_tasks` and `linked_adrs` in frontmatter
3. **Register**: Update this index
4. **Reference**: Tasks can reference via `evidence_refs: ["EVIDENCE-XXX"]`

---

## CLI Commands

```bash
# List all evidence
aibrain evidence list

# Capture new evidence
aibrain evidence capture

# Link evidence to task
aibrain evidence link EVIDENCE-001 TASK-123

# Show full evidence details
aibrain evidence show EVIDENCE-001
```

---

**Next Evidence ID**: EVIDENCE-003
