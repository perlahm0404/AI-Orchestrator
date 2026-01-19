# Documentation Architecture Strategy

**Session**: 2026-01-18 14:30
**Topic**: Multi-Repo Documentation Consolidation Analysis
**Status**: Active - Strategic Planning

---

## Current State Analysis

### Three Documentation Repositories

We currently have THREE distinct documentation systems:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. KNOWLEDGE VAULT (Obsidian, iCloud)                         │
│     - Strategic/historical context                              │
│     - ADRs (12 total)                                           │
│     - Cross-repo planning                                       │
│     - Offline/iCloud synced                                     │
│     - Path: ~/Library/.../Knowledge_Vault/AI-Engineering/...    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  2. MISSIONCONTROL REPO (Git, Constitutional Layer)             │
│     - Governance (objectives, policies, skills, protocols)      │
│     - RIS (central incident log)                                │
│     - Global KB                                                 │
│     - Cross-repo session tracking                               │
│     - Path: /Users/tmac/1_REPOS/MissionControl/                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  3. AI_ORCHESTRATOR REPO (Git, Execution HQ)                    │
│     - Vibe Kanban execution state                               │
│     - Knowledge Objects (runtime memory)                        │
│     - Agent implementations                                     │
│     - Session files (local)                                     │
│     - STATE.md (runtime state)                                  │
│     - Path: /Users/tmac/1_REPOS/AI_Orchestrator/                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  4. APP REPOS (Git, Business Units)                             │
│     - karematch/docs/ (well-organized, 11 categories)           │
│     - credentialmate/docs/ (assuming similar)                   │
│     - Local planning, PRDs, technical specs                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Overlap Analysis

### Current Redundancies

| Content Type | Knowledge Vault | MissionControl | AI_Orchestrator | App Repos |
|--------------|----------------|----------------|-----------------|-----------|
| **ADRs** | ✅ (12 total) | ✅ (ris/decisions/) | ❌ | ❌ |
| **Session Logs** | ✅ (07-SESSIONS/) | ✅ (sessions/) | ✅ (sessions/) | ✅ (karematch/docs/sessions/) |
| **Planning Docs** | ✅ (06-PLANS/) | ✅ (meta/planning/) | ✅ (.claude/plans/) | ✅ (karematch/docs/08-planning/) |
| **Governance** | ✅ (03-GOVERNANCE/) | ✅ (governance/) | ✅ (governance/contracts/) | ✅ (karematch/docs/07-governance/) |
| **Knowledge Objects** | ✅ (08-KO/) | ❌ | ✅ (knowledge/) | ❌ |
| **RIS/Incidents** | ❌ | ✅ (ris/resolutions/) | ❌ | ✅ (karematch/docs/06-ris/) |

**KEY INSIGHT**: We have 4-way duplication for sessions, planning, and governance!

---

## The Core Question

**Where should karematch planning documents live?**

Current reality:
- Karematch has `docs/08-planning/` with active plans, PRDs, trackers
- MissionControl has `meta/planning/` for harmonization
- AI_Orchestrator has `.claude/plans/` for Claude Code UI plans
- Knowledge Vault has `06-PLANS/` for strategic context

**The confusion**: When starting a new karematch feature, where do you document it?

---

## Consolidation Options

### Option 1: Keep Current 3-Tier Model (RECOMMENDED)

**Principle**: Each layer owns specific content types

```
KNOWLEDGE VAULT (Strategic/Historical)
├─ ADRs (architectural decisions)
├─ Historical session archives (>30 days old)
├─ Cross-project learnings
└─ Strategic planning (v7 redesign, etc.)

MISSIONCONTROL (Constitutional/Governance)
├─ Governance definitions (policies, skills, protocols)
├─ Objectives (inputs to Vibe Kanban)
├─ RIS central log (all repos)
└─ Cross-repo session tracking (active)

AI_ORCHESTRATOR (Execution/Runtime)
├─ .claude/plans/ (Claude Code UI only)
├─ sessions/cross-repo/ (active coordination)
├─ STATE.md (current runtime state)
├─ Knowledge Objects (runtime memory)
└─ Vibe Kanban (execution board)

APP REPOS (Domain/Operational)
├─ docs/08-planning/active/ (current work)
├─ docs/08-planning/prd/ (product specs)
├─ docs/06-ris/ (local incidents)
├─ docs/sessions/active/ (domain sessions)
└─ Local governance constraints
```

**Rules**:
1. **New karematch features** → Start in `karematch/docs/08-planning/active/`
2. **Cross-repo features** → Start in `AI_Orchestrator/sessions/cross-repo/active/`
3. **ADRs** → Knowledge Vault (single source of truth)
4. **RIS** → MissionControl (central log), app repos link to it
5. **Sessions** → Active in app repos, archive to Knowledge Vault after 30 days
6. **Governance** → Define in MissionControl, reference from app repos

**Pros**:
- Clear boundaries (strategic vs operational)
- Git-tracked execution state
- Obsidian for research/history
- Each repo is self-contained
- Minimal migration required

**Cons**:
- Still 3 systems to maintain
- Potential for drift
- Need clear rules enforcement

---

### Option 2: Consolidate to Git (2-Tier)

**Eliminate Knowledge Vault, consolidate to MissionControl + app repos**

```
MISSIONCONTROL (Strategic + Constitutional)
├─ adr/ (move from Vault)
├─ governance/
├─ ris/
├─ planning/ (strategic, cross-repo)
└─ archive/ (historical sessions)

APP REPOS (Operational)
├─ docs/planning/ (domain-specific)
├─ docs/sessions/
└─ docs/ris/ (symlinks to MissionControl?)
```

**Pros**:
- Everything version-controlled
- No iCloud sync issues
- Easier for agents to access
- Single git-based workflow

**Cons**:
- Lose Obsidian graph view
- Lose iCloud backup/sync
- ADRs mixed with operational docs
- Large migration effort

---

### Option 3: Consolidate to Obsidian (Vault-Centric)

**All strategic docs in Vault, only runtime state in Git**

```
KNOWLEDGE VAULT (All Documentation)
├─ 01-ADRs/
├─ 02-Governance/
├─ 03-Planning/
├─ 04-Sessions/
├─ 05-RIS/
└─ 06-Repos/
    ├─ karematch/
    ├─ credentialmate/
    └─ ai-orchestrator/

GIT REPOS (Runtime Only)
├─ STATE.md
├─ work_queue.json
├─ Knowledge Objects cache
└─ Code implementation
```

**Pros**:
- Single documentation source
- Best for research/exploration
- Graph view across all content

**Cons**:
- Agents harder to access (iCloud path)
- No version control on docs
- Offline/sync issues
- Breaks "docs live with code" principle

---

## Recommendation: Hybrid Clarity (Option 1 Enhanced)

**Keep 3-tier, but add clear routing rules:**

### Content Type Routing Table

| I want to... | Location | Why |
|--------------|----------|-----|
| Plan a new karematch feature | `karematch/docs/08-planning/active/` | Domain-specific, lives with code |
| Track cross-repo coordination | `AI_Orchestrator/sessions/cross-repo/active/` | Execution coordination |
| Document architectural decision | Knowledge Vault ADR | Strategic, permanent |
| Create governance policy | `MissionControl/governance/policies/` | Constitutional |
| Log incident resolution | `MissionControl/ris/resolutions/` | Central audit trail |
| Write session notes | App repo `sessions/active/` first | Move to Vault after 30 days |
| Create Claude Code plan | `AI_Orchestrator/.claude/plans/` | UI-specific |
| Define new objective | `MissionControl/governance/objectives/` | Inputs to Vibe Kanban |

### Automation Rules

1. **Auto-archive sessions** after 30 days (app repos → Knowledge Vault)
2. **Symlink RIS** from app repos to MissionControl (single source of truth)
3. **MissionControl CLAUDE.md** references in all app repos
4. **Knowledge Vault sync** to git weekly (backup ADRs)

---

## Specific Answer: KareMatch Planning

### Current Structure
```
karematch/docs/08-planning/
├─ README.md
├─ active/           (30 files - current work)
├─ completed/        (16 files - done)
├─ prd/              (7 files - product specs)
└─ trackers/         (7 files - progress tracking)
```

### Recommendation: KEEP IT

**Why?**
1. **Domain-specific** - Planning lives with the code it describes
2. **Developer-centric** - Engineers expect `docs/` in repos
3. **Self-contained** - Repo can be understood in isolation
4. **Git-tracked** - Versioned with implementation
5. **CI-accessible** - Agents can read during execution

**Changes to Make**:
1. Add `planning/templates/` with standard templates
2. Add `planning/index.md` linking to MissionControl objectives
3. Reference MissionControl governance in PRD template
4. Auto-archive completed/ to Knowledge Vault quarterly

---

## Migration Plan (If Choosing Option 1)

### Phase 1: Establish Boundaries (1 session)
1. Document content routing table (this file)
2. Update CLAUDE.md in all repos with routing rules
3. Create templates with proper headers/links

### Phase 2: Clean Overlaps (2-3 sessions)
1. Move strategic sessions from app repos → Knowledge Vault
2. Create RIS symlinks from app repos → MissionControl
3. Consolidate governance docs to MissionControl
4. Update all cross-references

### Phase 3: Automate (1 session)
1. Add hook to auto-archive old sessions
2. Add hook to validate governance references
3. Add CLI command: `aibrain docs route <topic>` (tells you where to put it)

### Phase 4: Test & Refine (1 session)
1. Run through full feature lifecycle
2. Document any confusion points
3. Update routing table as needed

---

## Next Steps

1. **Decide**: Option 1 (3-tier) vs Option 2 (git-only) vs Option 3 (vault-centric)
2. **Document**: Update this file with decision rationale
3. **Execute**: Run migration plan if needed
4. **Validate**: Test with next karematch feature

---

## Questions for Human

1. **Primary workflow**: Do you prefer Obsidian graph view or git-based workflow?
2. **Collaboration**: Will others need access to strategic docs? (Git easier to share)
3. **Backup priority**: How critical is iCloud backup vs git history?
4. **Agent access**: Do agents need ADRs during execution? (Easier in git)
5. **Migration tolerance**: How much effort is acceptable for cleanup?

