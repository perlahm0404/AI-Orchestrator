# AI Orchestrator (AI Brain v5)

## What This Is

AI Orchestrator is an autonomous multi-agent system for governed code quality improvement, feature development, AND safe deployments. It deploys **three specialized teams** of AI agents:

| Team | Mission | Autonomy |
|------|---------|----------|
| **QA Team** | Maintain code quality on stable code | L2 (higher) |
| **Dev Team** | Build new features in isolation | L1 (stricter) |
| **Operator Team** | Deploy applications and migrations safely | L0.5 (strictest) |

### Core Principles

- **Evidence-based completion** - No task marked done without proof (tests pass, Ralph verifies)
- **Human-in-the-loop approval** - Agents execute, humans approve what ships
- **Institutional memory** - Knowledge Objects capture learning that survives sessions
- **Explicit governance** - Autonomy contracts define what agents can/cannot do
- **Team isolation** - QA and Dev work on separate branches, merge at defined points

## Repository Location

```
/Users/tmac/1_REPOS/AI_Orchestrator   # This repo (execution engine: agents, ralph, orchestration)
/Users/tmac/1_REPOS/karematch         # Target app (L2 autonomy)
/Users/tmac/1_REPOS/credentialmate    # Target app (L1 autonomy, HIPAA)
```

## Knowledge Vault Location

**Vault Path**: `/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/`

**When to Consult**: Historical context, strategic planning, governance documentation, cross-project learnings

**How to Access**:
```python
from agents.core.context import get_vault_path, detect_context
vault_path = get_vault_path(detect_context())
```

**When NOT to Use**: Runtime execution, current state (use STATE.md), governance contracts (use `governance/contracts/*.yaml`)

## Current Status

**Version**: v9.1 - Parking Lot System (Idea Capture + Deferred Work)

**Implemented Systems**:
- ✅ v5.1 - Wiggum iteration control + autonomous loop integration
- ✅ v5.2 - Automated bug discovery with turborepo support
- ✅ v5.3 - Knowledge Object enhancements (cache, metrics, CLI)
- ✅ v6.0 - Cross-repo memory continuity + 9-step startup protocol
- ✅ v9.1 - Icebox system for quick idea capture + work queue "parked" status

**Key Metrics**:
- Autonomy: 91% (up from 60%)
- Tasks per session: 30-50 (target: 100+ with v6.0 optimizations)
- KO query speed: 457x faster (caching)
- Retry budget: 15-50 per task (agent-specific)

### Key Documents

| Document | Purpose |
|----------|---------|
| [docs/03-knowledge/README.md](./docs/03-knowledge/README.md) | Complete KO system documentation |
| [STATE.md](./STATE.md) | Current implementation status |
| [CATALOG.md](./CATALOG.md) | Documentation index |
| [docs/CROSS-REPO-SKILLS.md](./docs/CROSS-REPO-SKILLS.md) | Target repo skills and infrastructure access |

### Target Repository Skills & Tools

**CRITICAL**: Target repos (credentialmate, karematch) have their own `.claude/skills/` and `tools/` directories.

**Before building custom solutions, check target repo first:**
- `.claude/skills/` - Pre-built skills (credentialmate has 48!)
- `tools/` - CLI utilities for infrastructure access
- `docs/INFRASTRUCTURE.md` - Infrastructure documentation

**Example - CredentialMate Database Access**:
```bash
# ✅ Use this (existing tool)
python tools/rds-query "SELECT * FROM licenses"

# ❌ Don't build this (waste of time)
# - Custom Lambda function
# - Direct psql (VPC blocked)
# - RDS Data API script
```

**See**: [docs/CROSS-REPO-SKILLS.md](./docs/CROSS-REPO-SKILLS.md) for complete reference

### Autonomy Contracts

**See**: `governance/contracts/` for complete team permissions

| Contract | Team | File |
|----------|------|------|
| QA Team | BugFix, CodeQuality, TestFixer | `governance/contracts/qa-team.yaml` |
| Dev Team | FeatureBuilder, TestWriter | `governance/contracts/dev-team.yaml` |
| Operator Team | Deployment, Migration, Rollback | `governance/contracts/operator-team.yaml` |

---

## Agent Memory Protocol

**CRITICAL**: Sessions are stateless. All memory is externalized. The 9-step startup protocol loads context automatically.

### Memory Files

| File | Purpose | When to Update |
|------|---------|----------------|
| [CATALOG.md](./CATALOG.md) | Master documentation index | When adding new doc categories |
| [STATE.md](./STATE.md) | Current build state, what's done/blocked/next | Every significant change |
| [sessions/latest.md](./sessions/latest.md) | Most recent session handoff (if present) | End of every session |

### Automatic Checkpoint System

**IMPORTANT**: A hook runs after every Write/Edit operation and tracks tool call count.

**When you see the CHECKPOINT REMINDER banner:**
1. **STOP** current work
2. **UPDATE** STATE.md or relevant session file
3. **RESET** counter: `echo 0 > .claude/hooks/.checkpoint_counter`
4. **CONTINUE** work

**Why this matters:** If session crashes, only work since last checkpoint is lost.

### Session Documentation Protocol

When conducting research or multi-step exploration:

1. **Create session file EARLY** (not at the end):
   ```
   sessions/{repo}/active/{YYYYMMDD-HHMM}-{topic}.md
   ```
   - Repo options: `karematch`, `credentialmate`, `ai-orchestrator`, `cross-repo`
   - Use the template at `sessions/templates/session-template.md`

2. **Write findings AS YOU GO**:
   - Don't print walls of research text to terminal
   - Write directly to the session file
   - Update as you discover new information

3. **At session end**: Session file should already be complete
   - If resuming later: leave in `active/`
   - If complete: move to `archive/` (or auto-archive after 30 days)

---

## Autonomous System

### Running the Autonomous Loop

```bash
# Start autonomous loop
python autonomous_loop.py --project karematch --max-iterations 100

# What happens:
# 1. Loads tasks/work_queue_{project}.json
# 2. For each pending task:
#    a. Run IterationLoop with Wiggum control (15-50 retries)
#    b. On BLOCKED, ask human for R/O/A decision (unless --non-interactive)
#    c. On COMPLETED, commit to git and continue
# 3. Continues until queue empty or max iterations reached
```

**Note**: Human interaction can still be required (governance gates, advisor escalations, guardrail decisions).
Use `--non-interactive` to auto-revert guardrail violations and auto-approve required prompts.

### Session Resume

If interrupted (Ctrl+C, crash):

```bash
# Simply run the same command again - automatically resumes
python autonomous_loop.py --project karematch --max-iterations 100
```

System reads `.aibrain/agent-loop.local.md` state file and resumes from last iteration.

---

## Core Concepts

### Dual-Team Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Orchestrator                            │
│                                                                 │
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │    QA Team       │           │    Dev Team      │           │
│  │  (L2 autonomy)   │           │  (L1 autonomy)   │           │
│  │                  │           │                  │           │
│  │  - BugFix        │           │  - FeatureBuilder│           │
│  │  - CodeQuality   │           │  - TestWriter    │           │
│  │  - TestFixer     │           │                  │           │
│  └────────┬─────────┘           └────────┬─────────┘           │
│           │                              │                      │
│           ▼                              ▼                      │
│    ┌─────────────┐               ┌─────────────┐               │
│    │ main, fix/* │◄──────────────│  feature/*  │               │
│    │  branches   │  PR + Ralph   │  branches   │               │
│    └─────────────┘   PASS        └─────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Branch Ownership

| Branch Pattern | Owner | Ralph Timing |
|----------------|-------|--------------|
| `main` | Protected | Always |
| `fix/*` | QA Team | Every commit |
| `feature/*` | Dev Team | PR only |

### Governance Hierarchy

```
Kill-Switch (global: OFF/SAFE/NORMAL/PAUSED)
    │
    ▼
Team Contract (qa-team.yaml / dev-team.yaml)
    │
    ▼
Branch Restrictions (main/fix/* vs feature/*)
    │
    ▼
Ralph Verification (per-change: PASS/FAIL/BLOCKED)
    │
    ▼
Human Approval (per-merge)
```

### Target Applications

| App | Autonomy Level | Stack |
|-----|---------------|-------|
| **KareMatch** | L2 (higher autonomy) | Node/TS monorepo, Vitest, Playwright |
| **CredentialMate** | L1 (HIPAA, stricter) | FastAPI + Next.js + PostgreSQL |

### Deployment Quick Reference

**CredentialMate Frontend (SST):**
```bash
cd /Users/tmac/1_REPOS/credentialmate/apps/frontend-web
npx sst deploy --stage prod  # ALWAYS use 'prod' for production
```

**Key Infrastructure IDs (CredentialMate):**
| Resource | ID |
|----------|-----|
| CloudFront | `E3C4D2B3O2P8FS` |
| Route53 Zone | `Z00320409BFWAM57MKQD` |
| Domain | `credentialmate.com` |

**Full details:** `/Users/tmac/1_REPOS/credentialmate/docs/INFRASTRUCTURE.md`

### Key Invariants

1. **Sessions are stateless** - Agents reconstruct context from external artifacts
2. **Memory is externalized** - Database, files, tests (not in-memory state)
3. **Agents act within contracts** - Explicit YAML policy, enforced by hooks
4. **Teams stay in their lanes** - QA on main/fix/*, Dev on feature/*
5. **Humans approve promotion** - Agents execute, humans decide what ships
6. **TDD is primary memory** - Tests encode behavior; if not tested, doesn't exist
7. **Ralph is the law** - PASS/FAIL/BLOCKED verdicts are canonical
8. **Agents iterate until done** - Stop hook enables self-correction loops

---

## Wiggum System

**Status**: ✅ Production Ready

**Purpose**: Iteration control for agents, enabling them to iteratively improve work until Ralph verification passes or a completion signal is detected.

**Documentation**: See `docs/14-orchestration/wiggum.md` for complete details

### Core Components

1. **Completion Signals**: Agents signal task completion with `<promise>` tags
   ```python
   "All tests passing, bug fixed. <promise>COMPLETE</promise>"
   ```

2. **Iteration Budgets**: BugFix (15), CodeQuality (20), FeatureBuilder (50), TestWriter (15)

3. **Stop Hook System**: Blocks agent exit, decides whether to continue iterating based on Ralph verdict

**Auto-Detection**: System auto-detects task type and applies appropriate completion signal (80% reduction in manual signal specification)

---

## Knowledge Object System

**Status**: ✅ Production Ready

**Purpose**: Institutional memory that survives sessions, captures learning from agent work

**Documentation**: See `knowledge/README.md` for complete details

### Key Features

- **In-Memory Caching**: 457x speedup for repeated queries
- **Tag Index**: O(1) hash lookups
- **Effectiveness Metrics**: Tracks consultations, success rates
- **Auto-Approval**: 70% of KOs auto-approved (high-confidence only)

### Quick Reference

```bash
aibrain ko list                   # List all approved KOs
aibrain ko search --tags X,Y      # Search by tags (OR semantics)
aibrain ko pending                # List drafts awaiting approval
```

---

## Automated Bug Discovery

**Status**: ✅ Production Ready

**Purpose**: Scans codebases for bugs across 4 sources (ESLint, TypeScript, Vitest, Guardrails) and generates prioritized work queue tasks

**Documentation**: See `docs/16-testing/bug-discovery.md` for complete details

### Key Features

- **Baseline Tracking**: Detects new regressions vs. pre-existing issues
- **Impact-Based Priority**: P0 (blocks users), P1 (degrades UX), P2 (tech debt)
- **File Grouping**: Groups bugs in same file (reduces task count 50-70%)
- **Turborepo Support**: Auto-detects and handles monorepo structure

```bash
aibrain discover-bugs --project karematch  # Scan and generate tasks
```

---

## Icebox System (Parking Lot)

**Status**: ✅ Production Ready

**Purpose**: Quick idea capture without disrupting current work. Two-tier system for managing deferred tasks and features.

**Storage**: `.aibrain/icebox/` (markdown files with YAML frontmatter)

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   ICEBOX    │ ──► │   PARKED    │ ──► │   PENDING   │
│  (raw idea) │     │   (task)    │     │   (task)    │
└─────────────┘     └─────────────┘     └─────────────┘
   Human/Agent        Human review       Autonomous
   quick capture      + prioritization   loop picks up
```

### CLI Commands

```bash
# Capture a new idea
aibrain icebox add --title "Add semantic search" --project ai-orchestrator

# List ideas (filter by project/status)
aibrain icebox list --project credentialmate --status raw

# Show idea details
aibrain icebox show IDEA-20260207-1430-001

# Promote to work queue
aibrain icebox promote IDEA-xxx --status pending   # Ready for autonomous work
aibrain icebox promote IDEA-xxx --status parked    # Needs more refinement

# Find stale ideas
aibrain icebox stale --days 30

# Archive an idea
aibrain icebox archive IDEA-xxx --reason "Superseded by FEAT-123"

# Bulk cleanup old ideas
aibrain icebox cleanup --older-than 90
```

### Key Features

- **SHA256 Deduplication**: Prevents duplicate ideas via fingerprinting
- **Structured Metadata**: Title, priority (0-3), effort (XS-XL), category, tags
- **Cross-Repo Support**: CredentialMate symlinks to shared icebox
- **Work Queue Integration**: Extended `TaskStatus` with "parked" status
- **Auto-Archive**: Ideas >90 days without review auto-archive

### Decision Rights

| Role | Can Capture | Can Promote | Can Archive |
|------|------------|-------------|-------------|
| Human (CLI) | Yes | Yes | Yes |
| AI Agent | Yes | No | No |
| Advisor | Yes | Suggest only | No |

---

## MCP Servers (Model Context Protocol)

**Status**: ✅ Production Ready

**Configuration**: `.mcp.json` (project root)

**Purpose**: Extend Claude's capabilities with specialized tools for memory, git, filesystem, and reasoning.

### Available Servers

| Server | Tools | Use Case |
|--------|-------|----------|
| **memory** | `create_entities`, `search_nodes`, `read_graph` | Knowledge graph for cross-session institutional memory |
| **sequential-thinking** | `sequential_thinking` | Structured problem-solving with revision/branching |
| **git** | `git_status`, `git_diff`, `git_log`, `git_commit` | Repository operations and verification |
| **filesystem** | `read_file`, `write_file`, `list_directory` | Cross-repo file access (AI_Orchestrator, karematch, credentialmate) |
| **fetch** | `fetch` | Web content fetching and conversion |
| **time** | `get_current_time`, `convert_timezone` | Time operations and timezone handling |
| **orchestrator** | `list_tasks`, `update_task_status`, `verify_changes`, `search_knowledge_objects` | Work queue, Ralph verification, KO queries |

### Memory MCP Integration

The Memory MCP provides a knowledge graph for institutional learning:

**Storage**: `.aibrain/memory/knowledge-graph.jsonl`

**Use Cases**:
- Store entity relationships (e.g., "BugFix agent" → "works_on" → "karematch")
- Track observations about projects, patterns, and decisions
- Query learned patterns across sessions

**Example Operations**:
```
# Create entities
memory.create_entities([
  {"name": "React 19", "entityType": "technology", "observations": ["Supports server components"]}
])

# Search knowledge graph
memory.search_nodes("react patterns")

# Read entire graph
memory.read_graph()
```

### Sequential Thinking for Wiggum Integration

The Sequential Thinking MCP enhances the Wiggum iteration system:

**Use Cases**:
- Break complex bugs into reasoning steps
- Track hypothesis evolution during debugging
- Branch reasoning when exploring multiple solutions

**Parameters**:
- `thought`: Current reasoning step
- `thoughtNumber`: Step in sequence
- `totalThoughts`: Estimated total (can adjust dynamically)
- `isRevision`: True if revising earlier thought
- `branchId`: For parallel reasoning paths

### Orchestrator MCP (Custom)

The Orchestrator MCP exposes AI Orchestrator functionality:

**Tools**:
- `list_tasks` - List work queue tasks by project/status
- `get_task` - Get task details by ID
- `update_task_status` - Update task status (pending, in_progress, completed, blocked, parked)
- `verify_changes` - Run Ralph verification on files
- `search_knowledge_objects` - Search KOs by query/tags
- `get_session_state` - Get STATE.md content
- `get_autonomy_contract` - Get team autonomy contract

**Example**:
```
# List pending tasks for karematch
orchestrator.list_tasks(project="karematch", status="pending")

# Update task status
orchestrator.update_task_status(project="karematch", task_id="T-001", status="in_progress")

# Verify files
orchestrator.verify_changes(project="karematch", files=["src/auth.ts"])
```

### Verification

```bash
claude mcp list  # Show all connected servers
```

---

## Team Permissions

**See governance contracts for complete details**: `governance/contracts/*.yaml`

Quick summary:
- **QA Team**: Fix bugs on main/fix/* branches, Ralph verification every commit, max 100 lines/5 files
- **Dev Team**: Build features on feature/* branches, Ralph verification on PR only, max 500 lines/20 files
- **Operator Team**: Deploy to dev/staging/prod with environment-specific gates, production requires human approval

---

## CRITICAL: Git Commit Rules

**NEVER use `--no-verify` or `-n` flags when committing.**

The pre-commit hook runs Ralph verification. Bypassing it:
1. Violates governance policy
2. Will be caught by CI anyway (wasted effort)
3. May result in session termination

If a commit is blocked by Ralph:
1. **Fix the issue** - don't bypass
2. If tests fail, fix the code
3. If guardrails trigger, remove the violation
4. If lint fails, run the linter fix

```bash
# CORRECT
git commit -m "Fix bug"

# FORBIDDEN - NEVER DO THIS
git commit --no-verify -m "Fix bug"
git commit -n -m "Fix bug"
```
