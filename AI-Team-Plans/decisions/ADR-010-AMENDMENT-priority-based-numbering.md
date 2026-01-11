# ADR-010 Amendment: Priority-Based Numbering for AI_Orchestrator

**Status**: approved
**Date**: 2026-01-10
**Approved by**: tmac
**Approval date**: 2026-01-10
**Author**: Claude AI + tmac
**Project**: AI_Orchestrator
**Domain**: governance, documentation
**Amends**: ADR-010 (Documentation Organization & Archival Strategy)

---

## Context

### Original ADR-010 Approach

ADR-010 proposed a **flat structure with work/ and archive/** directories:
- `work/plans-active/`, `work/adrs-active/`, `work/tickets-open/`
- Rationale: "User preference for descriptive filenames over nested folders"

### CredentialMate Learning

During CredentialMate ADR-011 implementation, **user explicitly preferred numbered directories**:
> "i like the numbered directories, we may want to number all the folders inside the /docs/folders"
> "i like the numbered directories to be prioritized--active work reserved for 01-10; active references 10-19 (runbook, etc); next priorities 20-29, etc"

**CredentialMate Results** (100% success):
- 19 numbered directories with semantic priority (01-10 daily, 10-19 weekly, 20-29 monthly, 90-99 meta)
- 42% directory reduction (38 → 19)
- Zero duplicates, 100% clarity
- Self-documenting structure ("check 01-10 first")

### Key Distinction

- ❌ **Arbitrary sequential numbering** (01, 02, 03... with no meaning) = Anti-pattern
- ✅ **Priority-based numbering** (01-10=daily, 10-19=weekly, 20-29=monthly) = Best practice

---

## Decision

**Amend ADR-010 Section 1** from "Flat Structure with Descriptive Filenames" to **"Priority-Based Numbered Directory Structure"**.

### Proposed AI_Orchestrator Structure

```
ai-orchestrator/docs/

01-10: Active Work (Daily Use)
├── 01-quick-start/              ⭐ Onboarding, getting started
├── 02-governance/               ⭐ Contracts, compliance, team policies
├── 03-knowledge/                ⭐ Knowledge Objects (approved/)
└── 04-operations-daily/         ⭐ Day-to-day operations, deployments

10-19: Active References (Weekly Use - Plans, ADRs, Tasks, Architecture)
├── 10-architecture/             📚 System design, agent architecture
├── 11-plans/                    📚 Strategic plans, PRDs, roadmaps
├── 12-decisions/                📚 ADRs (Architecture Decision Records)
├── 13-tasks/                    📚 Task system, tickets, work queues
├── 14-orchestration/            📚 Wiggum, Ralph, iteration control
├── 15-agents/                   📚 Agent implementation guides
├── 16-testing/                  📚 Test documentation, baselines
└── 17-troubleshooting/          📚 Debug guides, issue resolution

20-29: Specialized (Monthly Use)
├── 20-analysis/                 🔬 Cost analysis, token analysis
├── 21-integration/              🔬 Claude Code, external tools
└── 22-reports/                  🔬 Generated reports, metrics

30-39: Project-Specific (Occasional Use)
├── 30-karematch/                🎯 KareMatch adapter documentation
└── 31-credentialmate/           🎯 CredentialMate adapter documentation

90-99: Meta/Admin (Rare Use)
├── 90-archive-index/            📦 Pointer to archive/ location
└── 99-deprecated/               📦 Deprecation notices, sunset guides
```

### Root Level (Core Documentation Only)

**Keep at root** (target: 10-15 files):
- `CLAUDE.md` - Main instructions for agents
- `CATALOG.md` - Master navigation hub
- `STATE.md` - Current implementation status
- `DECISIONS.md` - Build-time decisions
- `USER-PREFERENCES.md` - tmac's working preferences
- `QUICKSTART.md` - Getting started
- `ROADMAP.md` - Strategic roadmap
- `SYSTEM-CONFIGURATION.md` - Configuration guide
- `README.md` - Project overview

**Archive** (everything else):
- All session files → `archive/YYYY-MM/sessions-completed/`
- Completed implementation reports → `archive/YYYY-MM/superseded-docs/`
- Historical analysis → `archive/YYYY-MM/reports-completed/`

---

## Implementation Plan

### Phase 1: Archive Historical Content (30 min)

**Archive to `archive/2026-01/`**:
- 30+ session files from root/docs/
- Completed implementation reports (*-COMPLETE.md)
- Historical analysis (TOKEN_COST_ANALYSIS.md, COST_COMPARISON_QUICK_REFERENCE.md)

**Expected**: Reduce root from 35 → ~12 files, docs/ from 30+ → organized structure

### Phase 2: Create Priority-Based Structure (30 min)

**Create directories**:
```bash
docs/01-quick-start/
docs/02-governance/
docs/03-knowledge/
docs/04-operations-daily/
docs/10-architecture/
docs/12-orchestration/
docs/13-agents/
docs/14-testing/
docs/20-decisions/
docs/21-planning/
docs/22-analysis/
docs/23-integration/
docs/30-karematch/
docs/31-credentialmate/
docs/90-archive-index/
docs/99-deprecated/
```

**Move existing content**:
- `governance/` → `docs/02-governance/`
- `knowledge/` → `docs/03-knowledge/`
- `AI-Team-Plans/decisions/` → `docs/12-decisions/`
- `docs/guides/` → `docs/01-quick-start/`
- `docs/architecture/` → `docs/10-architecture/`
- `docs/planning/` → `docs/11-plans/`
- `docs/reports/` → `docs/22-reports/`
- `tasks/` → `docs/13-tasks/`

### Phase 3: Consolidate Scattered Content (30 min)

**Knowledge Objects** → `docs/03-knowledge/`:
- `knowledge/approved/` → `docs/03-knowledge/approved/`
- `knowledge/drafts/` → `docs/03-knowledge/drafts/`
- `knowledge/config/` → `docs/03-knowledge/config/`

**Governance** → `docs/02-governance/`:
- `governance/contracts/` → `docs/02-governance/contracts/`
- `governance/guardrails/` → `docs/02-governance/guardrails/`

**ADRs** → `docs/12-decisions/`:
- `AI-Team-Plans/decisions/*.md` → `docs/12-decisions/`
- `adapters/*/plans/decisions/*.md` → Keep in adapters (project-specific)

**Plans** → `docs/11-plans/`:
- `docs/planning/*.md` → `docs/11-plans/`
- `AI-Team-Plans/*.md` → `docs/11-plans/` (strategic plans, PRDs)

**Tasks** → `docs/13-tasks/`:
- `tasks/*.json` → `docs/13-tasks/queues/`
- Task management documentation → `docs/13-tasks/`

### Phase 4: Update References (30 min)

**Update CLAUDE.md**:
```markdown
**Read first:** `docs/03-knowledge/` for Knowledge Objects.

## Authority Hierarchy
1. **User/Owner** - Ultimate authority
2. **ADRs** (`docs/12-decisions/`) - Architecture decisions
3. **Knowledge Base** (`docs/03-knowledge/approved/`) - Proven solutions
4. **Governance Contracts** (`docs/02-governance/contracts/`) - Team policies

## Active Work References
- **Plans/PRDs**: `docs/11-plans/`
- **Tasks/Queues**: `docs/13-tasks/queues/`
- **Architecture**: `docs/10-architecture/`
```

**Update CATALOG.md**:
```markdown
## Priority-Based Navigation

### 01-10: Daily Use (Check First)
- `docs/01-quick-start/` - Getting started guides
- `docs/02-governance/` - Contracts, guardrails
- `docs/03-knowledge/` - Knowledge Objects
- `docs/04-operations-daily/` - Deployments, operations

### 10-19: Weekly Reference (Plans, ADRs, Tasks, Architecture)
- `docs/10-architecture/` - System design
- `docs/11-plans/` - Strategic plans, PRDs, roadmaps
- `docs/12-decisions/` - ADRs (Architecture Decision Records)
- `docs/13-tasks/` - Task system, work queues
- `docs/14-orchestration/` - Wiggum, Ralph
- `docs/15-agents/` - Agent guides
- `docs/16-testing/` - Test docs, baselines
- `docs/17-troubleshooting/` - Debug guides
...
```

### Phase 5: Create Archive Index (15 min)

**`docs/90-archive-index/README.md`**:
```markdown
# Archive Location

**Archive Path**: `/Users/tmac/1_REPOS/AI_Orchestrator/archive/YYYY-MM/`

## What's Archived
- **Sessions older than 30 days**: `archive/YYYY-MM/sessions-completed/`
- **Superseded documentation**: `archive/YYYY-MM/superseded-docs/`
- **Historical reports**: `archive/YYYY-MM/reports-completed/`

## Retention Policy
- **Sessions**: 7-year retention (SOC2 CC8.1)
- **Reports**: 7-year retention (audit trail)
- **Superseded Docs**: 1-year retention (unless referenced)
```

### Phase 6: Deprecation Notices (15 min)

**`docs/99-deprecated/`**:
- `FLAT-STRUCTURE-DEPRECATED.md` - Notice for old work/ approach
- `SCATTERED-ADR-DEPRECATED.md` - Notice for AI-Team-Plans/decisions/ location

**90-day sunset period** (expires 2026-04-10)

---

## Comparison: Flat vs Priority-Based

### ADR-010 Original (Flat Structure)

```
work/
├── plans-active/
├── adrs-active/
├── tickets-open/
└── tasks-wip/

archive/
└── YYYY-MM/
```

**Pros**: Simple, descriptive filenames
**Cons**: No visual priority, no semantic grouping, doesn't match user preference

### ADR-010 Amended (Priority-Based)

```
docs/
├── 01-quick-start/       ⭐ Daily
├── 02-governance/        ⭐ Daily
├── 03-knowledge/         ⭐ Daily
├── 10-architecture/      📚 Weekly
├── 12-orchestration/     📚 Weekly
├── 20-decisions/         🔬 Monthly
├── 21-planning/          🔬 Monthly
├── 90-archive-index/     📦 Rare
└── 99-deprecated/        📦 Rare
```

**Pros**: Visual priority, self-documenting, matches user preference, proven in CredentialMate
**Cons**: Requires learning numbering scheme (but very intuitive)

---

## Benefits of Priority-Based Numbering

### 1. Visual Priority Surfacing

The number communicates usage frequency at a glance:
- `02-governance/` = "Daily governance (Priority 02)"
- `20-decisions/` = "Monthly ADRs (Priority 20)"
- `90-archive-index/` = "Rare meta (Priority 90)"

### 2. Cognitive Load Reduction

**Mental Model**: "Need something? Check 01-10 first, then 10-19, rarely go past 20"

Agents know where to look without memorizing arbitrary paths.

### 3. Self-Documenting

No need for external documentation:
- `03-knowledge/` clearly signals "this is daily-use knowledge (Priority 03)"
- `22-analysis/` clearly signals "this is monthly-use analysis (Priority 22)"

### 4. Prevents Sprawl

Forces intentional decision: "Is this 01-10 important (daily) or 20-29 niche (monthly)?"

Prevents docs/ from ballooning with low-priority content.

### 5. Proven Success

CredentialMate achieved:
- 42% directory reduction
- 100% priority-based compliance
- Zero duplicates
- Universal clarity on location

---

## Migration Impact

### Files Affected

| Category | Count | Action |
|----------|-------|--------|
| Root markdown files | ~35 | Archive 23, keep 12 |
| docs/ files | ~30 | Reorganize into priority structure |
| governance/ files | ~50 | Move to docs/02-governance/ |
| knowledge/ files | ~40 | Move to docs/03-knowledge/ |
| AI-Team-Plans/ (plans) | ~10 | Move to docs/11-plans/ |
| docs/planning/ | ~13 | Move to docs/11-plans/ |
| AI-Team-Plans/decisions/ | ~15 | Move to docs/12-decisions/ |
| tasks/ | ~15 | Move to docs/13-tasks/ |

**Total**: ~183 files reorganized

### Path Updates Required

**CLAUDE.md**: 5-10 path references
**CATALOG.md**: Complete navigation rewrite
**STATE.md**: 2-3 path references
**DECISIONS.md**: 1-2 path references
**Agent code**: `agents/*/` may have hardcoded paths

### Estimated Effort

| Phase | Time | Complexity |
|-------|------|------------|
| Phase 1: Archive | 30 min | Low |
| Phase 2: Structure | 30 min | Medium |
| Phase 3: Consolidate | 30 min | Medium |
| Phase 4: References | 30 min | Medium |
| Phase 5: Archive Index | 15 min | Low |
| Phase 6: Deprecation | 15 min | Low |
| **Total** | **2.5 hours** | **Medium** |

---

## Success Metrics

| Metric | Target | Validation |
|--------|--------|------------|
| Root files | ≤12 | `ls *.md \| wc -l` |
| Priority-based structure | 100% | All docs/ dirs numbered |
| Governance consolidated | 1 location | `docs/02-governance/` only |
| Knowledge consolidated | 1 location | `docs/03-knowledge/` only |
| Plans consolidated | 1 location | `docs/11-plans/` only |
| ADRs consolidated | 1 location | `docs/12-decisions/` only |
| Tasks consolidated | 1 location | `docs/13-tasks/` only |
| Archive organization | Month-based | `archive/YYYY-MM/` structure |

---

## Approval

**Status**: approved
**Approved by**: tmac
**Approval date**: 2026-01-10
**Implementation**: In progress (Phases 1-6 executing)

---

## Tags

`documentation`, `priority-based-numbering`, `governance`, `organization`, `archival`, `agent-discoverability`, `repository-structure`, `adr-amendment`
