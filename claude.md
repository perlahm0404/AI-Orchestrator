# AI Orchestrator (AI Brain v5)

## What This Is

AI Orchestrator is an autonomous multi-agent system for governed code quality improvement, feature development, AND safe deployments.

**Current Status**: v5.2 - Production Ready (89% autonomy achieved)

**Quick Links**:
- **Quick Start**: See [README.md](./README.md) - Get running in 5 minutes
- **Essential Docs**: See [docs/](./docs/) - Architecture, agents, governance, vault reference
- **Agent Organization**: See [AI-ORG.md](./AI-ORG.md) - Complete hierarchy, roles, governance
- **CLI Commands**: See [CLI-REFERENCE.md](./CLI-REFERENCE.md) - All `aibrain` commands
- **Core Systems**: See [SYSTEMS.md](./SYSTEMS.md) - Wiggum, Ralph, Knowledge Objects, Bug Discovery
- **Current State**: See [STATE.md](./STATE.md) - What's done, what's next, blockers
- **User Preferences**: See [USER-PREFERENCES.md](./USER-PREFERENCES.md) - How tmac likes to work
- **Documentation Index**: See [CATALOG.md](./CATALOG.md) - Master navigation

---

## Repository Location

```
/Users/tmac/1_REPOS/AI_Orchestrator   # This repo (execution engine)
/Users/tmac/1_REPOS/karematch         # Target app (L2 autonomy)
/Users/tmac/1_REPOS/credentialmate    # Target app (L1 autonomy, HIPAA)
```

---

## Knowledge Vault Location

**Context**: This is a CODE REPO. Documentation is in the Obsidian vault.

**Vault Path**: `/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/`

**What's in This Repo**:
- Agent execution code (agents/, ralph/, orchestration/, discovery/, cli/)
- Runtime configuration (governance/contracts/, adapters/)
- Work queues and state (tasks/, .aibrain/)
- Knowledge Objects for runtime (knowledge/approved/)
- Tests (tests/)

**What's in the Vault**:
- Architecture documentation
- Session handoffs (historical)
- Strategic planning (DECISIONS.md, ROADMAP.md, etc.)
- Learning & analysis
- Knowledge Objects (reference copies)

### Agent Protocol: When to Consult the Vault

**If you are an AI agent, consult the vault when you need:**

1. **Historical Context**
   - Previous session outcomes → `Sessions/`
   - Past decisions and rationale → `DECISIONS.md`, `Plans/`
   - Architecture evolution → `Architecture/`

2. **Strategic Planning**
   - System roadmap → `ROADMAP.md`
   - Feature plans → `Plans/`
   - Architecture Decision Records → `Decisions/`

3. **Governance & Policy**
   - Team contracts explained → `Governance/`
   - Operational guides → `Operations/`
   - Troubleshooting guides → `Operations/`

4. **Cross-Project Learning**
   - Knowledge Objects (reference) → `Knowledge-Objects/`
   - Best practices → Vault `05-Knowledge-Base/`
   - Other project learnings → Vault `02-KareMatch/`, `03-CredentialMate/`

**How to Access Vault Files (on Mac)**:
```python
# Use the context detection system
from agents.core.context import get_vault_path, detect_context

context = detect_context()
vault_path = get_vault_path(context)
# Returns: /Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/

# Then read files normally
import os
sessions_dir = os.path.join(vault_path, "Sessions")
decisions_file = os.path.join(vault_path, "DECISIONS.md")
```

**When NOT to Use the Vault**:
- Runtime execution (use repo files)
- Governance contracts (use `governance/contracts/*.yaml`)
- Knowledge Object queries (use `knowledge/service.py`)
- Current state (use `STATE.md` in repo)

**Note**: On iOS, vault access requires Working Copy app or manual Obsidian viewing.

---

## Agent Memory Protocol

**CRITICAL**: Sessions are stateless. All memory is externalized. Read these files on every session start.

### Session Startup Checklist

```
1. Read CATALOG.md               → How is documentation organized?
2. Read USER-PREFERENCES.md      → How does tmac like to work?
3. Read STATE.md                 → What's the current state?
4. Read AI-ORG.md (if needed)    → Who does what (agent hierarchy)
5. Read sessions/latest.md (if present) → What happened last session?
6. Proceed with work
7. Before ending: Update STATE.md and create session handoff
```

### Memory Files

| File | Purpose | When to Update |
|------|---------|----------------|
| [CATALOG.md](./CATALOG.md) | Master documentation index | When adding new doc categories |
| [USER-PREFERENCES.md](./USER-PREFERENCES.md) | tmac's working preferences | When patterns change |
| [STATE.md](./STATE.md) | Current build state | Every significant change |
| [AI-ORG.md](./AI-ORG.md) | Agent hierarchy & governance | When org structure changes |
| [CLI-REFERENCE.md](./CLI-REFERENCE.md) | All CLI commands | When commands added |
| [SYSTEMS.md](./SYSTEMS.md) | Core systems docs | When systems change |
| [sessions/latest.md](./sessions/latest.md) | Most recent session (if present) | End of every session |

### Session Handoff Protocol

**Automated**: Not wired for `autonomous_loop.py` today. Use SessionReflection or add a hook if you want automatic handoffs.

**Manual**: For interactive sessions, use the SessionReflection system (see `orchestration/reflection.py`).

**Handoff includes**: What was accomplished, what was NOT done, blockers, Ralph verdict details, files modified, test status, risk assessment, next steps.

See [orchestration/handoff_template.md](./orchestration/handoff_template.md) for full format.

---

## Session State Management

Agents maintain state across sessions for resume capability.

### State File Location

**Path**: `.aibrain/agent-loop.local.md`

**Format**: Markdown with YAML frontmatter

```yaml
---
iteration: 5
max_iterations: 15
completion_promise: "BUGFIX_COMPLETE"
agent_name: "bugfix"
session_id: "session-123"
started_at: "2026-01-11T10:00:00Z"
project_name: "karematch"
task_id: "TASK-001"
---

# Task Description

Fix authentication timeout bug in login.ts...
```

### Memory Locations by Type

| Memory Type | Location | Format | Purpose |
|-------------|----------|--------|---------|
| **Session State** | `.aibrain/agent-loop.local.md` | Markdown + YAML | Resume autonomous loops mid-session |
| **Work Queue** | `tasks/work_queue_{project}.json` / `tasks/work_queue_{project}_features.json` | JSON | Pending/in-progress/completed tasks |
| **Session Handoffs** | `adapters/{project}/sessions/*.md` | Markdown | End-of-session summaries |
| **Audit Logs** | `.meta/audit/sessions/*.json` | JSON | Session event logs |
| **PROJECT_HQ** | `AI-Team-Plans/PROJECT_HQ.md` | Markdown | Project dashboard (current focus, blockers) |
| **Ralph State** | Git commit metadata | Git | Verification history |
| **Knowledge Objects** | `knowledge/approved/*.md` | Markdown + YAML | Institutional learning |

### Session Resume

If interrupted (Ctrl+C, crash), simply run the same command again:

```bash
# Automatically resumes from .aibrain/agent-loop.local.md
python autonomous_loop.py --project karematch --max-iterations 100
```

**Design Principle** (from `orchestration/__init__.py`):
> "Sessions are stateless. All state is externalized to state files, database, and git. An agent can be interrupted at any time and resumed from the last state checkpoint."

---

## Autonomous System Quick Start

### Running the Autonomous Loop

```bash
# Start autonomous loop
python autonomous_loop.py --project karematch --max-iterations 100

# What happens:
# 1. Loads tasks/work_queue_{project}.json (or tasks/work_queue_{project}_features.json)
# 2. For each pending task:
#    a. Run IterationLoop with Wiggum control (15-50 retries)
#    b. On BLOCKED, ask human for R/O/A decision (unless --non-interactive)
#    c. On COMPLETED, commit to git and continue
# 3. Continues until queue empty or max iterations reached
```

**Note**: Human interaction can still be required (governance gates, advisor escalations, guardrail decisions).
Use `--non-interactive` to auto-revert guardrail violations and auto-approve required prompts.

**See [SYSTEMS.md](./SYSTEMS.md)** for complete Wiggum, Ralph, and Knowledge Object documentation.

---

## Key Documents Quick Reference

### Daily Reference (Read These Often)

| Document | When to Read | Lines |
|----------|--------------|-------|
| [CATALOG.md](./CATALOG.md) | Session start (navigation) | 383 |
| [STATE.md](./STATE.md) | Session start (current state) | 785 |
| [USER-PREFERENCES.md](./USER-PREFERENCES.md) | Session start (how tmac works) | 423 |
| [sessions/latest.md](./sessions/latest.md) | Session start (last session) | Varies |

### Reference Docs (Read As Needed)

| Document | When to Read | Lines |
|----------|--------------|-------|
| [AI-ORG.md](./AI-ORG.md) | Need agent hierarchy/governance | ~800 |
| [CLI-REFERENCE.md](./CLI-REFERENCE.md) | Need command syntax | ~600 |
| [SYSTEMS.md](./SYSTEMS.md) | Need system internals | ~1000 |

### Specialized

| Document | Purpose |
|----------|---------|
| [knowledge/README.md](./knowledge/README.md) | Complete KO system docs |
| [governance/contracts/](./governance/contracts/) | Autonomy contracts (YAML) |
| [adapters/{project}/](./adapters/) | Project-specific configs |

---

## Emergency Controls

### Kill-Switch

```bash
aibrain emergency-stop    # AI_BRAIN_MODE=OFF (immediate halt)
aibrain pause             # AI_BRAIN_MODE=PAUSED (graceful pause)
aibrain resume            # AI_BRAIN_MODE=NORMAL (resume)
```

**Current Mode**: Check `.env` file for `AI_BRAIN_MODE`

**Modes**:
- `OFF` - All agents halted immediately
- `SAFE` - Read-only mode (no writes)
- `PAUSED` - Current task completes, then stop
- `NORMAL` - Full autonomy

---

## Core Principles

1. **Sessions are stateless** - Agents reconstruct context from external artifacts
2. **Memory is externalized** - Database, files, tests (not in-memory state)
3. **Agents act within contracts** - Explicit YAML policy, enforced by hooks
4. **Teams stay in their lanes** - QA on main/fix/*, Dev on feature/*, Operator on deploy/*
5. **Humans approve promotion** - Agents execute, humans decide what ships
6. **TDD is primary memory** - Tests encode behavior; if not tested, doesn't exist
7. **Ralph is the law** - PASS/FAIL/BLOCKED verdicts are canonical
8. **Agents iterate until done** - Stop hook enables self-correction loops
9. **Advisors escalate strategic decisions** - Humans make architecture choices
10. **Coordinator orchestrates, doesn't code** - Task breakdown only, no implementation

---

## Key Metrics

- **Autonomy**: 89% (up from 60%)
- **Tasks per session**: 30-50 (up from 10-15)
- **KO query speed**: 457x faster (caching)
- **Retry budget**: 15-50 per task (agent-specific)
- **Zero regressions**: Ralph verification at every commit

---

## Getting Help

- **Quick start**: See [README.md](./README.md) or [docs/QUICKSTART.md](./docs/QUICKSTART.md)
- **Architecture**: See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for high-level design
- **Agents**: See [docs/AGENTS.md](./docs/AGENTS.md) for agent types and usage
- **Governance**: See [docs/GOVERNANCE.md](./docs/GOVERNANCE.md) for autonomy contracts
- **Vault access**: See [docs/VAULT-REFERENCE.md](./docs/VAULT-REFERENCE.md) for detailed docs
- **Navigation**: Start with [CATALOG.md](./CATALOG.md) for complete index
- **Current state**: See [STATE.md](./STATE.md) for implementation status
- **Agent hierarchy**: See [AI-ORG.md](./AI-ORG.md)
- **Commands**: See [CLI-REFERENCE.md](./CLI-REFERENCE.md)
- **Systems**: See [SYSTEMS.md](./SYSTEMS.md)
- **User feedback**: Report issues at https://github.com/anthropics/claude-code/issues

---

## Documentation Structure

```
AI_Orchestrator/
├── README.md               ← GitHub landing page
├── CLAUDE.md               ← YOU ARE HERE (entry point for agents)
├── docs/                   ← Essential reference docs (~100K)
│   ├── QUICKSTART.md       ← Get running in 5 minutes
│   ├── ARCHITECTURE.md     ← High-level system design
│   ├── AGENTS.md           ← Agent types and usage
│   ├── GOVERNANCE.md       ← Autonomy contracts summary
│   └── VAULT-REFERENCE.md  ← How to access detailed docs
├── CATALOG.md              ← Master index
├── STATE.md                ← Current state
├── USER-PREFERENCES.md     ← How tmac works
├── AI-ORG.md               ← Agent hierarchy & governance
├── CLI-REFERENCE.md        ← All CLI commands
├── SYSTEMS.md              ← Core systems (Wiggum, Ralph, KO)
│
├── agents/                 ← Agent implementations
├── ralph/                  ← Verification engine
├── orchestration/          ← Wiggum, iteration control
├── knowledge/              ← Knowledge Objects
├── governance/contracts/   ← Autonomy contracts (YAML)
├── tasks/                  ← Work queues
└── adapters/               ← Project-specific configs

Detailed Docs (3.2M):
└── /Users/tmac/Library/.../Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/
    ├── Architecture/       ← Detailed system design
    ├── Sessions/           ← Historical handoffs
    ├── Plans/              ← Strategic plans
    ├── Decisions/          ← ADRs with full context
    ├── Governance/         ← Complete policy details
    └── Operations/         ← Runbooks, deployment guides
```

---

**Version**: v5.2 - Production Ready
**Autonomy**: 89%
**Last Updated**: 2026-01-11
