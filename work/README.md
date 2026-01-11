---
doc-id: "g-guide-work-directory"
title: "Active Work Directory Guide"
created: "2026-01-10"
updated: "2026-01-10"
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
domain: "governance"
relates-to: ["ADR-010", "ADR-011"]

version: "1.0"
---

# Active Work Directory

This directory contains all actively-in-progress plans, ADRs, and tasks.

## Structure

- **plans-active/** - Active implementation plans
- **adrs-active/** - Architecture Decision Records (drafts + recent approvals)
- **tickets-open/** - Open tickets (future use)
- **tasks-wip/** - Work in progress task breakdowns (future use)

## Naming Convention

Files use: `{scope}-{type}-{identifier}-{description}-{status}.md`

**Components**:
- **Scope**: `g` (general), `cm` (credentialmate), `km` (karematch)
- **Type**: `ADR`, `plan`, `task`, `ticket`
- **Identifier**: Number (001-999) or descriptive slug
- **Description**: Kebab-case, 2-5 words
- **Status**: `-DRAFT`, `-WIP`, `-BLOCKED` (or no suffix if approved/active)

**Examples**:
- `cm-ADR-007-duplicate-handling-data-DRAFT.md` - Draft ADR for CredentialMate
- `km-plan-production-completion.md` - Active plan for KareMatch
- `g-task-001-refactor-agents.md` - General task

## Current Active Work

### Plans (3)
```bash
$ ls work/plans-active/
cm-lambda-migration.md          # CredentialMate Lambda migration plan
g-aws-cost-analysis.md          # AWS cost analysis
km-feature-status.md            # KareMatch feature status
```

### ADRs (5)
```bash
$ ls work/adrs-active/
cm-ADR-006-cme-gap-calculation.md         # CME gap calculation standardization
cm-ADR-007-duplicate-handling-data.md     # Duplicate handling data architecture
cm-ADR-008-duplicate-handling-service.md  # Duplicate handling service architecture
cm-ADR-009-duplicate-handling-ux.md       # Duplicate handling user experience
g-ADR-003-lambda-cost-controls.md         # Lambda cost controls & guardrails
```

## Discovery Commands

Find active work:

```bash
# List all active plans
ls work/plans-active/

# List CredentialMate ADRs only
ls work/adrs-active/cm-*

# Find all draft documents
find work -name "*-DRAFT.md"

# Find work in progress
find work -name "*-WIP.md"

# Find blocked items
find work -name "*-BLOCKED.md"

# Search by keyword
grep -r "keyword" work/

# Count active items
find work -name "*.md" -type f | wc -l
```

## Workflow

### Adding New Work

1. **Create file** with proper naming convention
2. **Add SOC2/ISO frontmatter** (see template below)
3. **Add to appropriate subdirectory**
4. **Update CATALOG.md** if significant

### Moving to Archive

When work is completed:

1. **Move to archive**:
   ```bash
   mv work/plans-active/cm-plan-xyz.md archive/YYYY-MM/plans-completed/
   ```
2. **Update frontmatter** with archived status
3. **Update CATALOG.md** and registries
4. **Update related documents** (remove from todos, update references)

## SOC2/ISO Frontmatter Template

All documents in work/ MUST include compliance metadata:

```yaml
---
doc-id: "{scope}-{type}-{identifier}"
title: "Descriptive Title"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
author: "Claude AI / tmac"
status: "draft|active|approved"

compliance:
  soc2:
    controls: ["CC8.1"]  # Change Management
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.14.2.2"]  # System Change Control
    classification: "internal"
    review-frequency: "quarterly"

project: "credentialmate|karematch|ai-orchestrator"
domain: "qa|dev|operator|governance"
relates-to: ["ADR-001", "TASK-123"]

version: "1.0"
---
```

## Related Documents

- **ADR-010**: Documentation Organization & Archival Strategy
- **CATALOG.md**: Master navigation hub
- **archive/README.md**: Archived work directory (contrast with active)
- **catalog/adr-registry.md**: Global ADR registry
- **catalog/plan-registry.md**: Plan registry

## Quick Stats

```bash
# Current active work count
$ find work -name "*.md" -type f | wc -l
8

# By project
$ ls work/adrs-active/cm-* | wc -l    # CredentialMate: 4
$ ls work/adrs-active/g-* | wc -l     # General: 1
$ ls work/plans-active/km-* | wc -l   # KareMatch: 1
```
