---
pin-to-desktop: true
protect-from-cleanup: true
desktop-priority: 1
tags: [catalog, index, pinned]
---

# AI Orchestrator Documentation Catalog

**Last Updated**: 2026-01-10
**Purpose**: Master index and quick navigation hub for all documentation

> **Quick Start**: New to the codebase? Read [CLAUDE.md](./CLAUDE.md), then [STATE.md](./STATE.md), then the latest [session handoff](./sessions/latest.md).

---

## 🚀 Quick Links

| Category | Document | Purpose |
|----------|----------|---------|
| **Start Here** | [CLAUDE.md](./CLAUDE.md) | Project instructions, agent memory protocol |
| **Current State** | [STATE.md](./STATE.md) | What's done, what's next, blockers |
| **Build Decisions** | [DECISIONS.md](./DECISIONS.md) | Implementation choices with rationale |
| **User Preferences** | [USER-PREFERENCES.md](./USER-PREFERENCES.md) | tmac's working preferences |
| **Roadmap** | [ROADMAP.md](./ROADMAP.md) | Future features and backlog |

---

## 📚 Registries (Deep Indexes)

| Registry | Contents | Quick Stats |
|----------|----------|-------------|
| [ADR Registry](./catalog/adr-registry.md) | Architecture Decision Records | 5 ADRs (4 approved, 1 draft) |
| [Session Registry](./catalog/session-registry.md) | Session handoffs across all repos | 60+ sessions |
| [Plan Registry](./catalog/plan-registry.md) | Implementation plans and blueprints | 30+ plans |
| [Knowledge Registry](./catalog/knowledge-registry.md) | Knowledge Objects (KOs) and KB articles | 9+ artifacts |
| [Repo Registry](./catalog/repo-registry.md) | Repository metadata and relationships | 3 repos |

---

## 🗂️ Repository Map

```
AI_Orchestrator/                    ← You are here
├── CATALOG.md                      ← This file (master index)
├── CLAUDE.md                       ← Project instructions
├── STATE.md                        ← Current implementation status
├── DECISIONS.md                    ← Build decisions
├── ROADMAP.md                      ← Future features
├── USER-PREFERENCES.md             ← tmac's preferences
│
├── work/                           ← 🆕 ACTIVE WORK HUB
│   ├── README.md                   ← Active work navigation
│   ├── plans-active/               ← Active implementation plans
│   ├── adrs-active/                ← Active ADRs (single lookup)
│   ├── tickets-open/               ← Open tickets
│   └── tasks-wip/                  ← Work in progress
│
├── archive/                        ← 🆕 HISTORICAL ARCHIVE
│   ├── README.md                   ← Archive navigation
│   └── YYYY-MM/                    ← Month-based archival
│       ├── sessions-completed/
│       ├── superseded-docs/
│       └── work-queues-large-backups/
│
├── tasks/                          ← 🔄 REORGANIZED TASK QUEUES
│   ├── README.md                   ← Queue structure guide
│   ├── queues-active/              ← Current active queues
│   ├── queues-feature/             ← Feature-specific queues
│   └── queues-archived/            ← Compressed backups
│
├── catalog/                        ← Deep indexes (registries)
│   ├── adr-registry.md
│   ├── session-registry.md
│   ├── plan-registry.md
│   ├── knowledge-registry.md
│   └── repo-registry.md
│
├── AI-Team-Plans/                  ← ADRs, decisions, templates
│   ├── ADR-INDEX.md                ← Global ADR registry
│   └── decisions/                  ← Core orchestrator ADRs
│
├── sessions/                       ← Session handoffs
│   └── latest.md                   ← Most recent session
│
├── docs/                           ← 🔄 CATEGORIZED DOCUMENTATION
│   ├── INDEX.md                    ← Docs navigation
│   ├── architecture/               ← Architecture docs
│   ├── guides/                     ← How-to guides
│   ├── status/                     ← Status reports
│   ├── workflow/                   ← Workflow guides
│   ├── project-specs/              ← Project specifications
│   └── plans/                      ← Detailed plans
│
├── knowledge/                      ← Knowledge Objects (KOs)
│   └── README.md                   ← KO system guide
│
├── agents/                         ← Agent implementations
├── ralph/                          ← Verification engine
├── governance/                     ← Autonomy contracts
│   ├── contracts/
│   └── guardrails/
│
├── orchestration/                  ← Session lifecycle
├── discovery/                      ← Bug discovery system
├── adapters/                       ← Project configs
│   ├── credentialmate/
│   └── karematch/
│
└── tests/                          ← Test suites
```

---

## 📋 Common Tasks

### Session Startup

**CRITICAL**: Sessions are stateless. Read these files on every session start:

1. [STATE.md](./STATE.md) → What's the current state?
2. [DECISIONS.md](./DECISIONS.md) → What decisions were already made?
3. [sessions/latest.md](./sessions/latest.md) → What happened last session?
4. [USER-PREFERENCES.md](./USER-PREFERENCES.md) → How does tmac like to work?

### Find Documentation

| Looking for... | Go to... |
|----------------|----------|
| **Active work** | [work/](./work/) (plans, ADRs, tasks in progress) |
| **Active ADRs** | [work/adrs-active/](./work/adrs-active/) (single lookup location) |
| **Active plans** | [work/plans-active/](./work/plans-active/) |
| **Current work queues** | [tasks/queues-active/](./tasks/queues-active/) |
| Architecture decision | [ADR Registry](./catalog/adr-registry.md) or [work/adrs-active/](./work/adrs-active/) |
| Previous session notes | [Session Registry](./catalog/session-registry.md) or [sessions/](./sessions/) |
| Implementation plan | [Plan Registry](./catalog/plan-registry.md) or [work/plans-active/](./work/plans-active/) |
| Knowledge Object | [Knowledge Registry](./catalog/knowledge-registry.md) or `aibrain ko search` |
| Repo metadata | [Repo Registry](./catalog/repo-registry.md) |
| **Archived/historical** | [archive/](./archive/) (completed work, superseded docs) |

### Run Autonomous Loop

```bash
# CredentialMate (L1 autonomy)
python autonomous_loop.py --project credentialmate --max-iterations 100

# KareMatch (L2 autonomy)
python autonomous_loop.py --project karematch --max-iterations 100
```

### Search Documentation

```bash
# Search active work (plans, ADRs, tasks)
grep -r "keyword" work/

# Search active ADRs only
grep -r "keyword" work/adrs-active/

# Search active plans only
grep -r "keyword" work/plans-active/

# Search sessions
grep -r "keyword" sessions/

# Search all documentation
grep -r "keyword" docs/

# Search archived work
grep -r "keyword" archive/

# Search Knowledge Objects
aibrain ko search --tags "keyword"

# Find active work queues
ls tasks/queues-active/

# Search all ADRs (active + source locations)
grep -r "keyword" work/adrs-active/ AI-Team-Plans/decisions/ adapters/*/plans/decisions/
```

---

## 🎯 System Status (Quick View)

### Version

**AI Orchestrator v5.2** - Production Ready

### Autonomy Metrics

- **Autonomy**: 89% (up from 60%)
- **Tasks/Session**: 30-50 (up from 10-15)
- **KO Query Speed**: 457x faster (caching)

### Recent Milestones

- ✅ v5.1 - Wiggum iteration control + autonomous loop integration
- ✅ v5.2 - Automated bug discovery with turborepo support
- ✅ v5.3 - Knowledge Object enhancements (cache, metrics, CLI)

### Active Projects

| Project | Autonomy | Status |
|---------|----------|--------|
| [CredentialMate](./catalog/repo-registry.md#credentialmate) | L1 (HIPAA) | 🔄 Active Development |
| [KareMatch](./catalog/repo-registry.md#karematch) | L2 (Higher) | 🚀 Pre-Production |

---

## 🔍 By Topic

### Governance & Safety

- [Autonomy Contracts](./governance/contracts/)
  - [QA Team Contract](./governance/contracts/qa-team.yaml)
  - [Dev Team Contract](./governance/contracts/dev-team.yaml)
- [Guardrails](./ralph/guardrails/)
- [Kill Switch](./CLAUDE.md#emergency-controls)

### Agent System

- [Agent Implementations](./agents/)
- [Iteration Control (Wiggum)](./CLAUDE.md#wiggum-system)
- [Verification Engine (Ralph)](./ralph/)
- [Session Lifecycle](./orchestration/)

### Knowledge Management

- [Knowledge Objects System](./knowledge/README.md)
- [KO CLI Commands](./CLAUDE.md#cli-commands)
- [Auto-Approval](./knowledge/README.md#auto-approval)
- [Tag Index](./knowledge/README.md#tag-matching-semantics)

### Bug Discovery

- [Automated Bug Discovery](./CLAUDE.md#automated-bug-discovery-system)
- [Scanner Implementation](./discovery/)
- [Baseline Tracking](./discovery/baseline.py)

### Testing

- [Test Suites](./tests/)
- [E2E Testing](./adapters/credentialmate/plans/tasks/) _(CredentialMate)_
- [Playwright Config](../../karematch/playwright.config.ts) _(KareMatch)_

---

## 🛠️ CLI Reference

### AI Brain Commands

```bash
# Status
aibrain status                    # Overall system status
aibrain status TASK-123           # Specific task status

# Approvals
aibrain approve TASK-123          # Approve fix, merge PR
aibrain reject TASK-123 "reason"  # Reject fix, close PR

# Knowledge Objects
aibrain ko list                   # List all approved KOs
aibrain ko show KO-ID             # Show full KO details
aibrain ko search --tags X,Y      # Search by tags
aibrain ko pending                # List pending KOs
aibrain ko approve KO-ID          # Approve KO
aibrain ko metrics [KO-ID]        # View metrics

# Bug Discovery
aibrain discover-bugs --project X # Scan for bugs

# Emergency Controls
aibrain emergency-stop            # AI_BRAIN_MODE=OFF
aibrain pause                     # AI_BRAIN_MODE=PAUSED
aibrain resume                    # AI_BRAIN_MODE=NORMAL
```

---

## 📖 External Documentation

### Target Apps

- **CredentialMate**: `/Users/tmac/1_REPOS/credentialmate/docs/`
- **KareMatch**: `/Users/tmac/1_REPOS/karematch/docs/`

### Research Vault

- **AI_Brain Vault**: `/Users/tmac/Vaults/AI_Brain/` (30+ analyzed repos)

### Obsidian Integration

- **Docs Hub**: `/Users/tmac/Workspace/docs-hub/` (planned symlink)

---

## 🔗 Key Relationships

```
CATALOG.md (this file)
    │
    ├─→ CLAUDE.md (project instructions)
    ├─→ STATE.md (current state)
    ├─→ DECISIONS.md (build decisions)
    ├─→ USER-PREFERENCES.md (tmac's preferences)
    ├─→ ROADMAP.md (future features)
    │
    ├─→ catalog/ (deep indexes)
    │   ├─→ adr-registry.md
    │   ├─→ session-registry.md
    │   ├─→ plan-registry.md
    │   ├─→ knowledge-registry.md
    │   └─→ repo-registry.md
    │
    ├─→ AI-Team-Plans/ADR-INDEX.md (global ADR registry)
    ├─→ knowledge/README.md (KO system)
    └─→ sessions/latest.md (recent session)
```

---

## 💡 Tips

### For AI Agents

- **Always** read CATALOG.md first to understand structure
- **Always** read STATE.md to understand current status
- **Always** read USER-PREFERENCES.md to understand working style
- **Never** assume prior knowledge - session state is externalized

### For Humans (tmac)

- Bookmark this file in Obsidian
- Use registries for deep dives into specific areas
- Check STATE.md for "what's next"
- Review sessions/latest.md before starting work

---

## 📝 Document Conventions

### Status Indicators

| Icon | Meaning |
|------|---------|
| ✅ | Complete / Approved |
| 🔄 | Active / In Progress |
| 📋 | Planned / Pending |
| 🔍 | Investigation / Research |
| 🚫 | Blocked / Rejected |
| 🗄️ | Archived / Superseded |

### File Naming (ADR-010 Standard)

**New Convention**: `{scope}-{type}-{identifier}-{description}-{status}.ext`

- **Scope**: `g` (general), `cm` (credentialmate), `km` (karematch)
- **Type**: `ADR`, `plan`, `queue`, `session`, `task`
- **Status**: `-DRAFT`, `-WIP`, `-BLOCKED` (optional)

**Examples**:
- **Sessions**: `YYYY-MM-DD-description.md` (unchanged)
- **Plans**: `cm-plan-lambda-migration.md`, `km-feature-status.md`
- **ADRs**: `cm-ADR-006-cme-gap-calculation.md`, `g-ADR-003-lambda-cost-controls.md`
- **Work Queues**: `cm-queue-active.json`, `km-queue-features.json`
- **KOs**: `KO-{project}-NNN.md` (unchanged)

---

## 🆘 Help

**Need help?**
- Read [CLAUDE.md](./CLAUDE.md) for system overview
- Check [STATE.md](./STATE.md) for current blockers
- Review [sessions/latest.md](./sessions/latest.md) for recent context
- Search registries for related decisions/sessions

**Feedback**: Report issues at https://github.com/anthropics/claude-code/issues

---

**Last Updated**: 2026-01-10 | **Version**: 1.0 | **Maintainer**: tmac
