# ADR-010: Documentation Organization & Archival Strategy

**Status**: approved
**Date**: 2026-01-10
**Author**: Claude AI + tmac
**Project**: AI_Orchestrator
**Domain**: governance, documentation
**Advisor**: N/A (human-initiated)

---

## Context

The AI_Orchestrator repository had grown to **211 markdown files** across 90+ directories, with significant organizational challenges:

### Problems Identified

1. **Root Clutter**: 35 files at root level (target: 15-20)
   - Mixture of active plans, completed sessions, superseded docs, and core documentation
   - Difficult for agents to identify canonical documents on session startup

2. **Scattered ADRs**: Architecture Decision Records in 3+ locations
   - `AI-Team-Plans/decisions/`
   - `adapters/credentialmate/plans/decisions/`
   - No single lookup location for active ADRs

3. **Work Queue Chaos**: 9+ work queue files with unclear ownership
   - Multiple "current" candidates (work_queue.json, work_queue_credentialmate_features.json, etc.)
   - Massive 913KB backup file (work_queue_credentialmate.backup.20260107-233908.json)
   - No backup retention policy

4. **Versioned Duplicates**: No clear deprecation strategy
   - AI-RUN-COMPANY.md vs AI-RUN-COMPANY-V2.md
   - ai-orch-credentialmate.md vs ai-orch-credentialmate-v2.md
   - Status unclear (which is current?)

5. **Naming Inconsistencies**: Multiple conventions without standard
   - SCREAMING-KEBAB, lowercase-kebab, underscores, spaces
   - Status hidden in directories vs filenames (knowledge/approved/ vs knowledge/KO-001-approved.md)

6. **Missing Compliance Metadata**: No SOC2/ISO audit trail
   - No frontmatter with compliance controls
   - No retention policies
   - No classification (internal, confidential, public)

### Impact on Agents

- **Discoverability**: Agents must scan 211 files to find active work
- **Session Startup**: Slow context reconstruction from scattered documentation
- **Grep Inefficiency**: 50+ false positives when searching for specific artifacts
- **No Clear Canon**: Ambiguity about which documents are authoritative

---

## Decision

We will implement a **6-phase documentation reorganization** with the following principles:

### 1. Flat Structure with Descriptive Filenames

**Rationale**: User preference for descriptive filenames over nested folders with generic names.

- **Avoid**: `adapters/credentialmate/plans/decisions/index.md` (5 levels deep, generic name)
- **Prefer**: `work/adrs-active/cm-ADR-006-cme-gap-calculation.md` (3 levels, self-documenting)

### 2. Active vs Archived Separation

**New Directory Structure**:
```
work/                           # Active work (plans, ADRs, tasks in progress)
├── plans-active/
├── adrs-active/
├── tickets-open/
└── tasks-wip/

archive/                        # Completed, superseded, historical
└── YYYY-MM/
    ├── sessions-completed/
    ├── superseded-docs/
    └── work-queues-large-backups/
```

### 3. Naming Convention

**Format**: `{scope}-{type}-{identifier}-{description}-{status}.ext`

- **scope**: `g` (general), `cm` (credentialmate), `km` (karematch)
- **type**: `ADR`, `plan`, `queue`, `session`, `task`
- **identifier**: Number (001-999) or date (YYYY-MM-DD)
- **description**: Kebab-case, 2-5 words
- **status**: Optional - `DRAFT`, `WIP`, `BLOCKED`, `active`, `archived`

**Examples**:
- `work/adrs-active/cm-ADR-006-cme-gap-calculation.md`
- `tasks/queues-active/cm-queue-active.json`
- `archive/2026-01/superseded-docs/AI-RUN-COMPANY-v1-superseded.md`

### 4. SOC2/ISO Compliance Metadata

**All documents MUST include YAML frontmatter**:

```yaml
---
doc-id: "{scope}-{type}-{identifier}"
title: "Descriptive Title"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
author: "Claude AI / tmac"
status: "draft|active|approved|archived"

compliance:
  soc2:
    controls: ["CC7.3", "CC8.1"]
    evidence-type: "documentation|configuration|code|test-result|audit-log"
    retention-period: "7-years"
  iso27001:
    controls: ["A.12.1.1", "A.18.1.3"]
    classification: "internal|confidential|public"
    review-frequency: "annual|quarterly|monthly"

project: "credentialmate|karematch|ai-orchestrator"
domain: "qa|dev|operator|governance"
relates-to: ["ADR-001", "TASK-123"]

version: "1.0"
---
```

**Control Mapping**:
- **SOC2**: CC6.1, CC6.6, CC7.2, CC7.3, CC8.1
- **ISO 27001**: A.12.1.1, A.12.4.1, A.14.2.2, A.14.2.9, A.18.1.3

### 5. Work Queue Consolidation

**Clear Ownership**:
- `tasks/queues-active/cm-queue-active.json` - Current CredentialMate queue
- `tasks/queues-active/km-queue-active.json` - Current KareMatch queue
- `tasks/queues-active/g-queue-system.json` - System-wide queue
- `tasks/queues-feature/{project}-queue-{feature}.json` - Feature-specific

**Backup Retention**:
- Keep last 3 daily backups
- Compress backups older than 7 days
- Archive backups older than 30 days
- Delete archived backups older than 90 days (unless marked preserve)

### 6. Version Handling

**V2 becomes current, V1 archived**:
- `AI-RUN-COMPANY-V2.md` → `AI-RUN-COMPANY.md`
- `AI-RUN-COMPANY.md` → `archive/2026-01/superseded-docs/AI-RUN-COMPANY-v1-superseded.md`

---

## Implementation

### Phase 1: Archive Setup (1-2 hours)
- Create archive directory structure
- Move 17 completed/superseded files
- Handle versioned duplicates
- Create archive/README.md

### Phase 2: Work Directory (1 hour)
- Create work/ structure
- Move 3 active plans
- Move 5 active ADRs with renaming
- Create work/README.md

### Phase 3: Work Queue Consolidation (30 min)
- Reorganize 9 work queue files
- Compress 913KB backup → ~50KB
- Delete superseded backups
- Create tasks/README.md

### Phase 4: Naming Standardization (1 hour)
- Move 7+ files to docs/ subdirectories
- Standardize naming (kebab-case)
- Keep only core docs at root

### Phase 5: Registry Updates (30 min)
- Update CATALOG.md
- Update catalog/adr-registry.md
- Update DECISIONS.md
- Verify agent discoverability

### Phase 6: Compliance Metadata (1-2 hours)
- Add SOC2/ISO frontmatter to active plans
- Add compliance metadata to ADRs
- Add audit-log classification to sessions
- Create automation script

---

## Consequences

### Positive

1. **71% reduction in root clutter** (35 → 10 files)
2. **80% faster ADR lookup** (single work/adrs-active/ location)
3. **100% clarity on work queue ownership** (9 unclear → 3 clear active)
4. **95% reduction in backup size** (964KB → ~50KB compressed)
5. **93% faster agent discovery** (scan 10-15 files vs 211)
6. **SOC2/ISO audit trail** (7-year retention, evidence classification)

### Negative

1. **Breaking changes to existing paths**: All documentation references must be updated
2. **Migration effort**: 5-6 hours total implementation time
3. **Learning curve**: Team must learn new naming conventions
4. **Frontmatter overhead**: Extra YAML in every document (mitigated by templates)

### Neutral

1. **Centralized work/**: Easier discovery, but need to update CATALOG.md
2. **Compressed backups**: Saves space, but requires decompression to view
3. **Month-based archival**: Clear organization, but need monthly folder creation

---

## Verification

### Success Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Root Files | 35 | ~10 | 71% reduction |
| Active ADR Lookup | 5+ locations | 1 location | 80% faster |
| Work Queue Clarity | 9+ unclear | 3 clear | 100% clarity |
| Backup Size | 964KB | ~50KB | 95% reduction |
| Agent Discoverability | 211 files | 10-15 files | 93% faster |

### Validation Commands

```bash
# Test agent discoverability
find work/plans-active -name "*.md"          # 3-4 active plans
find work/adrs-active -name "*.md"           # 5-7 active ADRs
find tasks/queues-active -name "*.json"      # 3 active queues

# Verify root cleanup
ls *.md | wc -l                              # ~10 files

# Check compliance metadata
grep -r "^compliance:" work/ | wc -l         # All files have metadata
```

---

## Related Decisions

- **ADR-003**: Lambda Cost Controls (governance patterns)
- **ADR-004**: Resource Protection (task registration)
- **CATALOG.md**: Master navigation hub (updated with new structure)
- **DECISIONS.md**: Build-time decisions (this ADR added)

---

## Tags

`documentation`, `governance`, `organization`, `archival`, `compliance`, `soc2`, `iso27001`, `agent-discoverability`, `naming-convention`, `repository-structure`

---

## Approval

**Approved by**: tmac
**Approval date**: 2026-01-10
**Implementation status**: in-progress (Phase 1 active)
