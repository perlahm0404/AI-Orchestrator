# CLI Command Reference

**Version**: v5.2
**Last Updated**: 2026-01-11
**Purpose**: Complete reference for all `aibrain` CLI commands and advisor invocations

---

## Quick Command Index

| Category | Commands |
|----------|----------|
| **Status** | `status`, `status TASK-ID` |
| **Approvals** | `approve`, `reject` |
| **Knowledge Objects** | `ko list`, `ko show`, `ko search`, `ko pending`, `ko approve`, `ko metrics` |
| **ADR Management** | `adr list`, `adr show`, `adr create` |
| **Evidence** | `evidence capture`, `evidence list`, `evidence link` |
| **Bug Discovery** | `discover-bugs` |
| **Oversight** | `oversight pm`, `oversight adr` |
| **Advisors** | `/app-advisor`, `/uiux-advisor`, `/data-advisor` |
| **Emergency** | `emergency-stop`, `pause`, `resume` |

---

## Status Commands

### `aibrain status`

Get overall system status.

```bash
aibrain status
```

**Output**:
- Current AI_BRAIN_MODE (OFF/SAFE/NORMAL/PAUSED)
- Active tasks count
- Blocked tasks count
- Pending approvals
- Recent Ralph verdicts

**Example**:
```
AI Brain Status
===============
Mode: NORMAL
Active Tasks: 2
Blocked: 1
Pending Approvals: 0
Recent Verdicts: 3 PASS, 1 FAIL, 0 BLOCKED
```

---

### `aibrain status TASK-ID`

Get status for a specific task.

```bash
aibrain status TASK-123
```

**Output**:
- Task ID, description, status
- Agent assigned
- Iterations used
- Ralph verdict
- Files modified
- Test status
- Blockers (if any)

**Example**:
```
Task: TASK-123
Description: Fix authentication timeout bug
Status: IN_PROGRESS
Agent: bugfix
Iterations: 5/15
Ralph: PASS
Files: src/auth/session.ts (modified)
Tests: 3/3 passing
```

---

## Approval Commands

### `aibrain approve TASK-ID`

Approve a completed task and merge the PR.

```bash
aibrain approve TASK-123
```

**What It Does**:
1. Verifies task is COMPLETED
2. Checks Ralph verdict is PASS
3. Merges PR to target branch
4. Updates work queue status
5. Triggers next task assignment

**Requires**:
- Task status = COMPLETED
- Ralph verdict = PASS
- All tests passing

---

### `aibrain reject TASK-ID "reason"`

Reject a task and close the PR.

```bash
aibrain reject TASK-123 "Approach doesn't align with architecture"
```

**What It Does**:
1. Marks task as CANCELLED
2. Closes associated PR
3. Adds rejection reason to task metadata
4. Optionally creates new task with alternative approach

**Use When**:
- Approach is incorrect
- Requirements changed
- Task no longer needed

---

## Knowledge Object Commands

### `aibrain ko list`

List all approved Knowledge Objects.

```bash
aibrain ko list
```

**Output**:
- KO ID
- Title
- Tags
- Effectiveness score
- Consultation count
- Last updated

**Example**:
```
ID          Title                              Tags                Score  Consults
KO-001      TypeScript Strict Mode Migration   typescript, strict  0.85   12
KO-002      Vitest Test Organization           testing, vitest     0.92   8
KO-003      API Error Handling Pattern         api, errors         0.78   15
```

---

### `aibrain ko show KO-ID`

Show full details for a Knowledge Object.

```bash
aibrain ko show KO-001
```

**Output**:
- Full KO content (problem, solution, context)
- Effectiveness metrics
- Tags and aliases
- Consultation history
- Success rate

---

### `aibrain ko search --tags TAG1,TAG2`

Search Knowledge Objects by tags (OR semantics).

```bash
aibrain ko search --tags typescript,strict-mode
```

**Note**: Uses OR semantics - returns KOs with ANY matching tag.

**Options**:
- `--tags`: Comma-separated tags
- `--limit N`: Max results (default: 10)

**Example**:
```bash
# Find KOs about TypeScript OR strict mode
aibrain ko search --tags typescript,strict-mode

# Find KOs about testing
aibrain ko search --tags testing
```

---

### `aibrain ko pending`

List draft Knowledge Objects awaiting approval.

```bash
aibrain ko pending
```

**Output**:
- Draft KO ID
- Title
- Created by (agent)
- Created at
- Reason for creation

---

### `aibrain ko approve KO-ID`

Approve a draft Knowledge Object.

```bash
aibrain ko approve KO-DRAFT-001
```

**What It Does**:
1. Moves from `knowledge/drafts/` to `knowledge/approved/`
2. Assigns permanent KO ID (KO-XXX)
3. Indexes tags
4. Initializes effectiveness metrics

**Auto-Approval**: Drafts are auto-approved if:
- Ralph verdict = PASS
- Iterations = 2-10 (configurable)
- Auto-approval enabled in config

---

### `aibrain ko reject KO-ID "reason"`

Reject a draft Knowledge Object.

```bash
aibrain ko reject KO-DRAFT-001 "Too specific, not reusable"
```

**What It Does**:
1. Deletes draft from `knowledge/drafts/`
2. Logs rejection reason
3. Notifies agent (if in session)

---

### `aibrain ko metrics [KO-ID]`

View effectiveness metrics for Knowledge Objects.

```bash
# All KOs
aibrain ko metrics

# Specific KO
aibrain ko metrics KO-001
```

**Output**:
- Consultation count
- Success rate (when consulted)
- Average impact score
- Tags with highest correlation
- Recent consultations

**Example**:
```
KO-001: TypeScript Strict Mode Migration
========================================
Consultations: 12
Success Rate: 83% (10/12)
Average Impact: 0.85
Top Tags: typescript (12), strict-mode (8), migration (5)
Recent: 2026-01-10 (PASS), 2026-01-09 (PASS), 2026-01-08 (FAIL)
```

---

## ADR Management Commands

### `aibrain adr list`

List all Architecture Decision Records.

```bash
aibrain adr list
```

**Output**:
- ADR number
- Title
- Status (draft, approved, complete)
- Advisor
- Tags
- File path

---

### `aibrain adr show ADR-XXX`

Show full ADR details.

```bash
aibrain adr show ADR-003
```

**Output**:
- Full ADR content
- Status and metadata
- Related tasks
- Implementation progress

---

### `aibrain adr create`

Create a new ADR interactively.

```bash
aibrain adr create
```

**Interactive Prompts**:
1. Title
2. Context
3. Decision
4. Consequences
5. Advisor (app/uiux/data)
6. Tags

**Output**: Creates `AI-Team-Plans/decisions/ADR-XXX.md`

---

## Evidence Management Commands

### `aibrain evidence capture`

Capture user evidence interactively.

```bash
aibrain evidence capture
```

**Interactive Prompts**:
1. Evidence type (feature-request, objection, feedback, pilot-signup)
2. Source (pilot-user, sales-call, support-ticket)
3. Priority (P0/P1/P2)
4. Summary
5. User quote
6. Related tasks (optional)

**Output**: Creates `evidence/EVIDENCE-XXX.md`

---

### `aibrain evidence list`

List all evidence items.

```bash
aibrain evidence list
```

**Output**:
- Evidence ID
- Priority
- Type
- Source
- Summary
- Created at

**Filters**:
- `--priority P0` - Only P0 evidence
- `--type feature-request` - Specific type
- `--source pilot-user` - Specific source

---

### `aibrain evidence link EVIDENCE-XXX TASK-YYY`

Link evidence to a task.

```bash
aibrain evidence link EVIDENCE-045 TASK-CME-001
```

**What It Does**:
1. Updates evidence file with task reference
2. Updates task file with evidence reference
3. Validates link (evidence + task both exist)

**Use When**:
- Implementing feature based on evidence
- PM validation requires evidence link

---

## Bug Discovery Commands

### `aibrain discover-bugs --project PROJECT`

Scan codebase for bugs and generate tasks.

```bash
aibrain discover-bugs --project karematch
```

**What It Scans**:
- ESLint errors (unused imports, console.log, security issues)
- TypeScript errors (type errors, missing annotations)
- Vitest failures (test failures)
- Guardrails (@ts-ignore, eslint-disable, .only(), .skip())

**Options**:
- `--project NAME` - Project to scan (karematch, credentialmate)
- `--sources lint,typecheck,test,guardrails` - Specific sources
- `--dry-run` - Preview only, don't create tasks

**First Run**: Creates baseline fingerprint snapshot.

**Subsequent Runs**: Detects NEW regressions only.

**Output**:
- Task summary (P0, P1, P2)
- NEW regressions flagged
- Tasks added to work queue

**Example**:
```
📋 Task Summary:
  🆕 [P0] TEST-LOGIN-001: Fix 2 test error(s) (NEW REGRESSION)
  🆕 [P0] TYPE-SESSION-002: Fix 1 typecheck error(s) (NEW REGRESSION)
     [P1] LINT-MATCHING-003: Fix 3 lint error(s) (baseline)
     [P2] GUARD-CONFIG-007: Fix 2 guardrails error(s) (baseline)

Tasks added to: tasks/work_queue_karematch.json
```

---

## Oversight Report Commands

### `aibrain oversight pm`

Generate Product Manager status report.

```bash
aibrain oversight pm
```

**What It Reports**:
- Feature validation status (evidence-backed vs. not)
- Roadmap alignment check
- Outcome metrics defined
- Blocked features awaiting PM review
- Evidence repository status

**Output**: Markdown report in `.meta/oversight/pm-status-YYYY-MM-DD.md`

---

### `aibrain oversight adr`

Generate ADR status report.

```bash
aibrain oversight adr
```

**What It Reports**:
- ADRs by status (draft, approved, complete)
- ADRs by advisor (app, uiux, data)
- Implementation progress per ADR
- Blocked ADRs
- Recent ADR activity

**Output**: Markdown report in `.meta/oversight/adr-status-YYYY-MM-DD.md`

---

## Advisor Invocations (Claude Code Skills)

Advisors are invoked via Claude Code skills (not `aibrain` CLI).

### `/app-advisor <question>`

Consult the App Advisor for architecture & API guidance.

```bash
/app-advisor How should we structure the API for multi-tenancy?
/app-advisor What's the best caching strategy for this feature?
/app-advisor Should we use REST or GraphQL for the new service?
```

**Specializes In**:
- System architecture
- API design and versioning
- Design patterns
- Code organization
- Performance and scalability

**Auto-Approves** (85% confidence):
- Tactical decisions (code organization, internal patterns)
- No ADR conflicts
- Files touched ≤ 5

**Escalates**:
- Strategic decisions (API versioning, breaking changes)
- ADR conflicts
- Files touched > 5

**Output**: ADR in `AI-Team-Plans/decisions/` (if approved)

---

### `/uiux-advisor <question>`

Consult the UI/UX Advisor for component & UX guidance.

```bash
/uiux-advisor How should we display the provider dashboard?
/uiux-advisor What's the best flow for certification upload?
/uiux-advisor Should we use a modal or inline form for editing?
```

**Specializes In**:
- Component architecture
- Accessibility (a11y)
- User experience patterns
- Design system consistency
- Frontend performance

**Auto-Approves** (85% confidence):
- Tactical decisions (component naming, layout)
- No ADR conflicts
- Files touched ≤ 5

**Escalates**:
- Strategic decisions (new user flows, breaking UX changes)
- ADR conflicts
- Files touched > 5

**Output**: ADR in `AI-Team-Plans/decisions/` (if approved)

---

### `/data-advisor <question>`

Consult the Data Advisor for schema & data modeling guidance.

```bash
/data-advisor How should we model certifications and expiration tracking?
/data-advisor What's the best way to handle provider credentials?
/data-advisor Should we use soft deletes or hard deletes?
```

**Specializes In**:
- Schema design
- Migrations
- Data quality
- Query optimization
- Storage architecture

**Auto-Approves** (85% confidence):
- Tactical decisions (column naming)
- No ADR conflicts
- Files touched ≤ 5

**Escalates**:
- Strategic decisions (schema changes, migrations)
- ADR conflicts
- Files touched > 5

**Output**: ADR in `AI-Team-Plans/decisions/` (if approved)

**HIPAA Extension** (CredentialMate):
- Always flags PHI columns
- Recommends encryption for sensitive data
- Includes audit logging in schema designs
- Validates against HIPAA requirements

---

## Autonomous Loop

### `python autonomous_loop.py --project PROJECT --max-iterations N`

Start autonomous task execution loop.

```bash
python autonomous_loop.py --project karematch --max-iterations 100
```

**What Happens**:
1. Loads `work_queue.json` from tasks/
2. For each pending task:
   - Run IterationLoop with Wiggum control (15-50 retries)
   - On BLOCKED, ask human for R/O/A decision
   - On COMPLETED, commit to git and continue
3. Continues until queue empty or max iterations reached

**Options**:
- `--project NAME` - Target project (karematch, credentialmate)
- `--max-iterations N` - Max iterations before pause
- `--resume` - Resume from `.aibrain/agent-loop.local.md`

**Session Resume**:
If interrupted (Ctrl+C, crash), simply run the same command again:

```bash
# Automatically resumes from .aibrain/agent-loop.local.md
python autonomous_loop.py --project karematch --max-iterations 100
```

**Human Interaction Points**:

**BLOCKED Verdict** (Guardrail Violation):
```
🚫 GUARDRAIL VIOLATION DETECTED
============================================================
Pattern: --no-verify detected (bypassing Ralph verification)
File: src/auth/session.ts
============================================================
OPTIONS:
  [R] Revert changes and exit
  [O] Override guardrail and continue
  [A] Abort session immediately
============================================================
Your choice [R/O/A]:
```

**That's it!** No other human interaction required. Agent auto-handles lint/type/test failures.

---

## Emergency Control Commands

### `aibrain emergency-stop`

Immediately halt all autonomous agents.

```bash
aibrain emergency-stop
```

**What It Does**:
1. Sets `AI_BRAIN_MODE=OFF` in `.env`
2. Stops all running autonomous loops
3. Prevents new agent sessions from starting
4. Preserves current state for resume

**Use When**:
- Agents are misbehaving
- Critical production issue
- Need to manually intervene

**To Resume**: `aibrain resume`

---

### `aibrain pause`

Pause autonomous agents (allow completion of current task).

```bash
aibrain pause
```

**What It Does**:
1. Sets `AI_BRAIN_MODE=PAUSED` in `.env`
2. Allows current task to complete
3. Prevents starting new tasks
4. Preserves state for resume

**Use When**:
- Need to review agent work
- Temporary pause for investigation
- Want clean checkpoint

**To Resume**: `aibrain resume`

---

### `aibrain resume`

Resume autonomous agents from paused/stopped state.

```bash
aibrain resume
```

**What It Does**:
1. Sets `AI_BRAIN_MODE=NORMAL` in `.env`
2. Resumes from last checkpoint
3. Continues work queue execution

**Requires**:
- Previous session was paused or stopped cleanly
- State file exists (`.aibrain/agent-loop.local.md`)

---

## Command Completion & Aliases

### Bash Completion

```bash
# Add to ~/.bashrc or ~/.zshrc
eval "$(aibrain --completion)"
```

### Common Aliases

```bash
# Suggested aliases
alias ab='aibrain'
alias abs='aibrain status'
alias abko='aibrain ko'
alias abadr='aibrain adr'
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Task not found |
| 4 | Permission denied |
| 5 | Ralph BLOCKED |
| 6 | Kill-switch active (MODE=OFF) |
| 7 | System paused (MODE=PAUSED) |

---

## Configuration

CLI reads configuration from:

1. `.env` - Environment variables (AI_BRAIN_MODE, etc.)
2. `governance/contracts/*.yaml` - Autonomy contracts
3. `adapters/{project}/config.yaml` - Project-specific config

---

## Related Documentation

- [AI-ORG.md](./AI-ORG.md) - Agent organization & governance
- [SYSTEMS.md](./SYSTEMS.md) - Core systems (Wiggum, Ralph, KO)
- [CLAUDE.md](./CLAUDE.md) - Entry point for AI agents
- [STATE.md](./STATE.md) - Current implementation status
