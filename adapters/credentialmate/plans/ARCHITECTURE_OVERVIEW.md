# Architecture Overview: Where State Lives & Work Happens

## 🏗️ Two-Repo Architecture

The AI Orchestrator system uses a **dual-repository pattern**:

```
┌─────────────────────────────────────────────────────────────────┐
│  AI Orchestrator Repo                                           │
│  /Users/tmac/1_REPOS/AI_Orchestrator                            │
│                                                                  │
│  📋 ORCHESTRATION & GOVERNANCE (read-only to target repos)      │
│  ├── autonomous_loop.py          # Runs agents                  │
│  ├── agents/                     # Agent implementations        │
│  ├── ralph/                      # Verification engine          │
│  ├── governance/                 # Contracts, guardrails        │
│  ├── knowledge/                  # Knowledge Objects            │
│  └── adapters/                                                  │
│      └── credentialmate/                                        │
│          ├── config.yaml         # Points to target repo ─┐    │
│          └── plans/              # PROJECT-SPECIFIC STATE  │    │
│              ├── decisions/      # ADRs                    │    │
│              ├── tasks/          # Work queues             │    │
│              └── IMPLEMENTATION_PLAN_ADR001.md             │    │
└────────────────────────────────────────────────────────────┼────┘
                                                             │
                                    project_path: /Users/tmac/1_REPOS/credentialmate
                                                             │
┌────────────────────────────────────────────────────────────▼────┐
│  CredentialMate Repo (Target)                                   │
│  /Users/tmac/1_REPOS/credentialmate                                     │
│                                                                  │
│  💻 ACTUAL CODE & EXECUTION (where agents write code)           │
│  ├── apps/backend-api/           # Code changes happen here    │
│  ├── apps/frontend-web/                                         │
│  ├── apps/worker-tasks/                                         │
│  ├── tests/                      # Tests run here              │
│  ├── .git/                       # Git operations here         │
│  └── claude-progress.txt         # Session state (local)       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 State Maintained in TWO Places

### 1. **AI Orchestrator Repo** (Orchestration State)

**Location**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/`

**What lives here**:
- ✅ **ADRs** (Architecture Decision Records) - decisions/ADR-001-*.md
- ✅ **Work Queues** - tasks/work_queue_adr001.json
- ✅ **Implementation Plans** - IMPLEMENTATION_PLAN_ADR001.md
- ✅ **Project Config** - config.yaml (points to target repo)
- ✅ **Knowledge Objects** - Approved patterns, best practices
- ✅ **Governance Contracts** - What agents can/cannot do

**Why here**:
- Centralized governance across multiple target projects
- Version controlled separately from application code
- Agents can consult KOs/ADRs without cluttering app repo
- Easy to share governance patterns across projects

---

### 2. **Target Repo** (Execution State)

**Location**: `/Users/tmac/1_REPOS/credentialmate/`

**What lives here**:
- ✅ **Application Code** - All source files (.py, .ts, .tsx)
- ✅ **Git Branches** - feature/*, fix/*, main
- ✅ **Git Commits** - Changes made by agents
- ✅ **Test Results** - Pytest output, coverage reports
- ✅ **Session State** - claude-progress.txt (local, not committed)
- ✅ **Ralph Verification** - Runs in this directory

**Why here**:
- Actual code changes must happen in the app repo
- Git history belongs with the application
- Tests run against the actual codebase
- Developers work here (not in orchestrator repo)

---

## 🔄 How They Connect

### Adapter Configuration

**File**: `adapters/credentialmate/config.yaml`

```yaml
project:
  name: credentialmate
  path: /Users/tmac/1_REPOS/credentialmate  # ← Bridges the two repos
  language: python

commands:
  lint: "ruff check apps/backend-api ..."
  test: "pytest tests/ -v"
  # All commands run in /Users/tmac/1_REPOS/credentialmate

paths:
  source:
    - "apps/backend-api/"
    - "apps/worker-tasks/"
  # All paths relative to /Users/tmac/1_REPOS/credentialmate
```

**The adapter is the bridge**:
1. Orchestration logic reads config.yaml
2. Gets `project_path = /Users/tmac/1_REPOS/credentialmate`
3. All git/test/ralph commands execute in that directory
4. But ADRs/work queues stay in orchestrator repo

---

## 🚀 Autonomous Loop Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. START: autonomous_loop.py runs from orchestrator repo    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ 2. LOAD: Work queue from adapters/credentialmate/plans/    │
│    tasks/work_queue_adr001.json                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ 3. EXECUTE: For each task:                                  │
│    a. cd /Users/tmac/1_REPOS/credentialmate  (via adapter config)   │
│    b. Agent writes code in that directory                   │
│    c. Ralph runs tests in that directory                    │
│    d. Git commit happens in that directory                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ 4. UPDATE: Update work queue status back in orchestrator   │
│    adapters/credentialmate/plans/tasks/work_queue_adr001.json│
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ 5. REPEAT: Next task (loop back to step 3)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Example: TASK-ADR001-006 Execution

**Task**: Create report generation API routes

**What happens**:

1. **Orchestrator repo** reads task from `work_queue_adr001.json`:
   ```json
   {
     "id": "TASK-ADR001-006",
     "title": "Create report generation API routes",
     "files": ["apps/backend-api/app/api/v1/reports/routes.py"]
   }
   ```

2. **Adapter config** provides target directory:
   ```yaml
   project:
     path: /Users/tmac/1_REPOS/credentialmate
   ```

3. **Agent executes** in target repo:
   ```bash
   # These commands run in /Users/tmac/1_REPOS/credentialmate/
   cd /Users/tmac/1_REPOS/credentialmate
   git checkout -b feature/ADR001-TASK-006
   # Agent writes code to apps/backend-api/app/api/v1/reports/routes.py
   pytest tests/api/test_reports.py
   git add -A
   git commit -m "feat: Add report generation API routes (TASK-006)"
   ```

4. **Ralph verification** runs in target repo:
   ```bash
   # In /Users/tmac/1_REPOS/credentialmate/
   ruff check apps/backend-api/
   mypy apps/backend-api/
   pytest tests/ -v
   ```

5. **Work queue updated** in orchestrator repo:
   ```json
   {
     "id": "TASK-ADR001-006",
     "status": "completed",  # ← Updated
     "completed_at": "2026-01-09T12:34:56Z"
   }
   ```

---

## 🔍 Why This Separation?

### Benefits

| Aspect | Orchestrator Repo | Target Repo |
|--------|-------------------|-------------|
| **Purpose** | Governance, planning, memory | Execution, code, tests |
| **Changes** | ADRs, work queues, KOs | Application code, features |
| **Versioning** | Governance evolution | Application releases |
| **Audience** | AI agents, orchestration | Developers, users |
| **Lifecycle** | Long-lived (years) | Per-project |

### Multi-Project Support

The orchestrator can manage **multiple target projects**:

```
/Users/tmac/1_REPOS/AI_Orchestrator/
├── adapters/
│   ├── karematch/
│   │   ├── config.yaml     # → /Users/tmac/karematch
│   │   └── plans/
│   └── credentialmate/
│       ├── config.yaml     # → /Users/tmac/1_REPOS/credentialmate
│       └── plans/
```

Each adapter has its own:
- ADRs (project-specific decisions)
- Work queues (project-specific tasks)
- Config (points to different target repo)

But they **share**:
- Governance contracts (same QA/Dev team rules)
- Knowledge Objects (cross-project patterns)
- Ralph engine (same verification logic)
- Wiggum control (same iteration patterns)

---

## 🎯 Key Takeaway

**Orchestrator repo** = The brain (governance, planning, memory)
**Target repo** = The hands (code, execution, git)

**Connection** = Adapter config.yaml bridges them

**Work happens**: In target repo (/Users/tmac/1_REPOS/credentialmate)
**State lives**: In BOTH (orchestration state in orchestrator, execution state in target)

---

## 📋 Quick Reference

| Question | Answer |
|----------|--------|
| Where is ADR-001? | `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/decisions/` |
| Where is work_queue_adr001.json? | `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/tasks/` |
| Where do agents write code? | `/Users/tmac/1_REPOS/credentialmate/apps/backend-api/` |
| Where are git commits? | `/Users/tmac/1_REPOS/credentialmate/.git/` |
| Where do tests run? | `/Users/tmac/1_REPOS/credentialmate/` (via pytest) |
| Where is Ralph executed? | `/Users/tmac/1_REPOS/credentialmate/` (via adapter context) |
| Where is the autonomous loop? | `/Users/tmac/1_REPOS/AI_Orchestrator/autonomous_loop.py` |
| Where is session state? | `/Users/tmac/1_REPOS/credentialmate/claude-progress.txt` (local file) |

---

**Last Updated**: 2026-01-09
**Status**: Dual-repo architecture, fully operational
