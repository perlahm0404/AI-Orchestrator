# Human-in-the-Loop Project Plan

**Date**: 2026-01-05
**Status**: Draft
**Source**: Derived from [v4 Planning.md](./v4%20Planning.md)

---

## Design Principles

These principles are non-negotiable:

1. **Sessions are stateless** - Agent sessions do not persist memory
2. **Memory is externalized** - All state lives in artifacts (files, database, tests)
3. **Agents act within contracts** - Explicit boundaries, enforced by governance
4. **Humans approve promotion** - Agents execute, humans decide what ships
5. **TDD is primary memory** - Tests encode behavior; if it's not tested, it doesn't exist
6. **Knowledge Objects on resolution only** - No speculative knowledge creation

---

## Standalone Repository Requirement

### Why AI Brain Must Be Standalone

AI Brain is **not** a library embedded in application repos. It is a standalone system that:

1. **Manages multiple projects** - Single brain, multiple targets
2. **Owns governance** - Contracts, hooks, and rules live in one place
3. **Owns institutional memory** - Knowledge Objects are cross-project
4. **Survives project changes** - App refactors don't break governance
5. **Has its own release cycle** - Governance updates independent of app releases

### Repository Structure

```
ai-brain/                          # STANDALONE REPO
├─ agents/
│  ├─ base.py                      # Shared agent protocol
│  ├─ bugfix.py                    # BugFix agent
│  ├─ codequality.py               # CodeQuality agent
│  └─ refactor.py                  # Refactor agent (Phase 2)
├─ prompts/
│  ├─ bugfix.md                    # System prompt
│  ├─ codequality.md
│  └─ refactor.md
├─ governance/
│  ├─ contracts/
│  │  ├─ bugfix.yaml               # Autonomy contract
│  │  ├─ codequality.yaml
│  │  └─ refactor.yaml
│  ├─ guardrails/
│  │  ├─ bash_security.py          # Command allowlist
│  │  ├─ no_new_features.py        # Scope creep detection
│  │  └─ governance_rules.py       # Per-task-type rules
│  └─ kill_switch/
│     └─ mode.py                   # OFF/SAFE/NORMAL/PAUSED
├─ orchestration/
│  ├─ session.py                   # Session lifecycle
│  ├─ checkpoint.py                # Resume capability
│  └─ circuit_breaker.py           # Failure handling
├─ knowledge/
│  ├─ approved/                    # Markdown mirrors (synced from DB)
│  ├─ drafts/
│  └─ service.py                   # CRUD, matching, consultation
├─ audit/
│  ├─ logger.py                    # Action logging with causality
│  └─ queries.py                   # Causality chain queries
├─ adapters/
│  ├─ base.py                      # Adapter interface
│  ├─ karematch/
│  │  ├─ config.yaml               # Project-specific settings
│  │  └─ ralph.py                  # Invokes KareMatch's Ralph
│  └─ credentialmate/
│     ├─ config.yaml
│     └─ ralph.py                  # Invokes CredentialMate's Ralph
├─ db/
│  └─ migrations/
│     ├─ 001_initial_schema.sql
│     ├─ 002_audit_causality.sql
│     └─ 003_knowledge_objects.sql
├─ cli/
│  ├─ __main__.py
│  └─ commands/
│     ├─ status.py                 # aibrain status
│     ├─ approve.py                # aibrain approve TASK-123
│     ├─ reject.py
│     └─ emergency_stop.py
├─ tests/
│  ├─ governance/
│  │  └─ test_negative_capabilities.py
│  ├─ agents/
│  └─ integration/
└─ docs/
```

### What AI Brain Owns vs Application Repos

| AI Brain Owns | Application Repos Own |
|---------------|----------------------|
| Governance engine | Ralph verification harness |
| Autonomy contracts | Source code |
| Knowledge Objects | Tests |
| Audit schema | Application database |
| Agent orchestration | CI/CD pipeline |
| CLI interface | Deployment |

### Integration Model

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI BRAIN REPO                             │
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │   Agents    │    │ Governance  │    │  Knowledge  │        │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘        │
│          │                  │                  │                │
│          └──────────────────┼──────────────────┘                │
│                             │                                   │
│                    ┌────────┴────────┐                          │
│                    │    Adapters     │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
┌───────────────────┐ ┌───────────────────┐ ┌──────────────┐
│   KAREMATCH REPO  │ │ CREDENTIALMATE    │ │ FUTURE REPO  │
│                   │ │      REPO         │ │              │
│ ┌───────────────┐ │ │ ┌───────────────┐ │ │              │
│ │ tools/ralph/  │ │ │ │ tools/ralph/  │ │ │              │
│ └───────────────┘ │ │ └───────────────┘ │ │              │
│ ┌───────────────┐ │ │ ┌───────────────┐ │ │              │
│ │    src/       │ │ │ │    src/       │ │ │              │
│ └───────────────┘ │ │ └───────────────┘ │ │              │
│ ┌───────────────┐ │ │ ┌───────────────┐ │ │              │
│ │   tests/      │ │ │ │   tests/      │ │ │              │
│ └───────────────┘ │ │ └───────────────┘ │ │              │
└───────────────────┘ └───────────────────┘ └──────────────┘
```

**Key**: AI Brain invokes Ralph in target repos via adapters. It does not own Ralph.

---

## Phase-by-Phase Operational Plan

### Artifact Legend

| Artifact | Purpose | Location |
|----------|---------|----------|
| `audit_log` | What happened (episodic) | Postgres |
| `REVIEW.md` | Human review packet | Target repo (PR) |
| `Knowledge Object` | What must not be forgotten | ai-brain/knowledge/ + Postgres |
| `STATUS.md` | Current task status | ai-brain state |
| `checkpoint.json` | Session resume state | ai-brain/state/ |

---

## Phase -1: Trust Calibration Sprint

**Duration**: 1 week
**Mode**: Manual execution, no AI agents

### What Happens

Human operator manually executes the BugFix workflow to validate:
- The workflow produces good evidence
- Guardrails block forbidden actions
- Thresholds are calibrated correctly

### Autonomous Agent Activities

**None.** This phase is entirely manual.

### Human Visibility Points

| Checkpoint | What Human Sees |
|------------|-----------------|
| Bug selection | Human selects 3 trivial + 1 medium bug |
| Reproduction test | Human writes test, verifies it fails |
| Fix application | Human applies fix, verifies test passes |
| Ralph verification | Human runs Ralph, sees pass/fail |
| Evidence review | Human reviews evidence package |
| Guardrail test | Human attempts forbidden action, sees block |

### Human Decision Points

| Decision | Options |
|----------|---------|
| Bug selection | Select from TODO list |
| Fix approval | Self-approve (manual workflow) |
| Threshold tuning | Adjust max_lines, max_files, etc. |
| Go/No-Go | Proceed to Phase 0 or halt |

### Artifacts Produced

| Artifact | Contents |
|----------|----------|
| `CALIBRATION-REPORT.md` | Results of all calibration tasks |
| `THRESHOLD-DECISIONS.md` | Threshold values with rationale |
| `evidence/{bug-id}/` | Evidence packages for each fix |

### Session Survival

No AI sessions in Phase -1. Human creates artifacts directly.

---

## Phase 0: Governance Foundation

**Duration**: 2 weeks
**Mode**: Implementation, no AI agents on production code

### What Happens

Build and test the governance infrastructure:
- Autonomy contracts
- Kill-switch and safe mode
- Enhanced audit schema
- Negative capability tests

### Autonomous Agent Activities

**None on production code.** Test agents may run against mock projects.

### Human Visibility Points

| Checkpoint | What Human Sees |
|------------|-----------------|
| Contract creation | YAML files in `governance/contracts/` |
| Hook implementation | Python files in `governance/guardrails/` |
| Schema deployment | Migration files applied to Postgres |
| Test execution | Negative capability test results |

### Human Decision Points

| Decision | Options |
|----------|---------|
| Contract review | Approve/modify autonomy contracts |
| Threshold finalization | Lock in max_lines, max_files, etc. |
| Test coverage | Determine if safety tests are sufficient |
| Phase 0 exit | Proceed to Phase 1 or extend |

### Artifacts Produced

| Artifact | Contents |
|----------|----------|
| `governance/contracts/*.yaml` | Finalized autonomy contracts |
| `tests/governance/test_negative_capabilities.py` | Safety tests |
| `db/migrations/*.sql` | Applied schema changes |
| `PHASE-0-COMPLETION.md` | Exit checklist |

### Session Survival

No production AI sessions. Implementation sessions use standard git workflow.

---

## Phase 1: BugFix + CodeQuality Agents

**Duration**: 4-6 weeks
**Mode**: Autonomous agents on real code

### What Happens

AI agents autonomously fix bugs and improve code quality on KareMatch (L2) and CredentialMate (L1).

### Autonomous Agent Activities

#### BugFix Agent (Autonomous)

```
1. READ issue from database
2. CONSULT Knowledge Objects for related patterns
3. FIND or WRITE reproduction test (must fail)
4. ANALYZE root cause
5. APPLY minimal fix
6. RUN Ralph verification
7. CAPTURE evidence (before/after commits, test outputs)
8. GENERATE REVIEW.md
9. MARK issue as pending_review
10. HALT and wait for human approval
```

**The agent does NOT**:
- Push to main
- Deploy
- Modify database schema
- Exceed 100 lines added / 5 files changed

#### CodeQuality Agent (Autonomous)

```
1. ESTABLISH baseline (test count, lint errors, type errors)
2. SCAN for safe auto-fix issues
3. PROCESS in batches (max 20)
4. VALIDATE test count unchanged after each batch
5. ROLLBACK if tests fail
6. GENERATE batch REVIEW.md
7. MARK batch as pending_review
8. HALT and wait for human approval
```

### Human Visibility Points

| Checkpoint | What Human Sees | Location |
|------------|-----------------|----------|
| Session start | `audit_log` entry with session_id | Postgres / CLI |
| Issue assigned | `audit_log` entry: action=assigned | Postgres / CLI |
| Knowledge consulted | `audit_log` entry: action=consulted | Postgres / CLI |
| Fix attempted | `audit_log` entries for each action | Postgres / CLI |
| Ralph run | Ralph logs + summary | Target repo |
| Review ready | `REVIEW.md` in PR | Target repo |
| Knowledge draft | Draft KO in `knowledge/drafts/` | ai-brain repo |

**CLI visibility**:
```bash
aibrain status                    # Overall system status
aibrain status TASK-123           # Specific task status
aibrain log TASK-123              # Audit log for task
aibrain log --session abc-123     # Audit log for session
```

### Human Decision Points

| Decision | When | Options | Artifacts |
|----------|------|---------|-----------|
| **Approve fix** | After REVIEW.md generated | Approve / Request changes / Reject | REVIEW.md |
| **Approve KO** | After fix merged | Approve / Edit / Skip | Knowledge Object draft |
| **Emergency stop** | Any time | OFF / SAFE / PAUSED | None required |
| **Resume session** | After pause/failure | Resume / Restart / Abandon | checkpoint.json |

**CLI commands**:
```bash
aibrain approve TASK-123          # Approve fix, merge PR
aibrain reject TASK-123 "reason"  # Reject fix, close PR
aibrain request-changes TASK-123  # Request modifications

aibrain ko approve KO-km-001      # Approve Knowledge Object
aibrain ko edit KO-km-001         # Edit before approving
aibrain ko skip KO-km-001         # Skip KO creation

aibrain emergency-stop            # AI_BRAIN_MODE=OFF
aibrain pause                     # AI_BRAIN_MODE=PAUSED
aibrain resume                    # AI_BRAIN_MODE=NORMAL
```

### Artifacts Produced

| Artifact | When Created | Contents |
|----------|--------------|----------|
| `audit_log` entries | Every action | Who, what, when, why, causality |
| `REVIEW.md` | Fix complete | Summary, root cause, changes, evidence |
| `checkpoint.json` | Periodically | Session state for resume |
| `Knowledge Object (draft)` | On RESOLVED_FULL | Extracted insight |
| `Knowledge Object (approved)` | After human approval | Permanent memory |

### Session Survival

Agents are stateless. Sessions survive compaction and restart via:

1. **Checkpoint files** - Saved at milestones
2. **Database state** - Issue status, evidence
3. **Git state** - Branch, commits
4. **Audit log** - Complete history

**Restart protocol**:
```python
def resume_session(session_id: str):
    # 1. Load checkpoint
    checkpoint = load_checkpoint(session_id)

    # 2. Reconstruct context from external state
    issue = db.get_issue(checkpoint.issue_id)
    git_state = git.status(checkpoint.branch)
    audit = db.get_audit_log(session_id)

    # 3. Determine next action
    if checkpoint.phase == "fix_applied":
        return run_ralph_verification(issue)
    elif checkpoint.phase == "ralph_passed":
        return generate_review_md(issue)
    # ... etc
```

---

## Operational Runbook

### Daily Operations

**Morning check**:
```bash
aibrain status                    # Any blocked tasks? Any failures?
aibrain log --since yesterday     # What happened overnight?
```

**Review queue**:
```bash
aibrain pending                   # List tasks awaiting approval
# For each pending task:
cat /path/to/pr/REVIEW.md         # Read review packet
aibrain approve TASK-123          # Or reject/request-changes
```

**Knowledge queue**:
```bash
aibrain ko pending                # List KOs awaiting approval
# For each pending KO:
cat ai-brain/knowledge/drafts/KO-km-001.md
aibrain ko approve KO-km-001      # Or edit/skip
```

### Incident Response

**Something feels wrong**:
```bash
aibrain pause                     # Stop new work, preserve state
aibrain status                    # What's happening?
aibrain log --session <latest>    # What did it do?
```

**Confirmed problem**:
```bash
aibrain emergency-stop            # Full stop, no actions
# Investigate in audit_log
# Fix issue
aibrain resume                    # When ready
```

**Rollback a fix**:
```bash
git revert <commit>               # In target repo
aibrain reject TASK-123 "Rolled back due to X"
```

### Weekly Review

```bash
aibrain metrics --week            # Bugs fixed, quality issues, time
aibrain ko list --approved        # New institutional knowledge
aibrain audit --high-risk         # Any high-risk actions taken?
```

---

## Artifact Templates

### REVIEW.md Template

See [v4 Planning.md → Human Review UX](./v4%20Planning.md#human-review-ux)

### Knowledge Object Template

See [KNOWLEDGE-OBJECTS-v1.md](./KNOWLEDGE-OBJECTS-v1.md)

### Checkpoint Schema

```json
{
  "session_id": "abc-123-def-456",
  "issue_id": 123,
  "project": "karematch",
  "branch": "fix/TASK-123-null-check",
  "phase": "fix_applied",
  "started_at": "2026-01-05T14:00:00Z",
  "last_checkpoint_at": "2026-01-05T14:32:00Z",
  "actions_completed": [
    "reproduction_test_written",
    "reproduction_verified_failing",
    "fix_applied"
  ],
  "next_action": "run_ralph_verification",
  "evidence": {
    "before_commit": "abc123",
    "after_commit": "def456",
    "reproduction_test_path": "tests/auth.test.ts:89"
  }
}
```

---

## Summary: When Does Human Pay Attention?

| Scenario | Human Action | Urgency |
|----------|--------------|---------|
| Task pending review | Review REVIEW.md, approve/reject | Daily |
| Knowledge Object pending | Review draft, approve/edit/skip | Daily |
| Agent blocked | Investigate, resolve blocker | Same day |
| Circuit breaker triggered | Investigate repeated failure | Same day |
| High-risk action logged | Review audit_log | Weekly review |
| Emergency (something wrong) | `aibrain pause` or `emergency-stop` | Immediate |

---

## References

- [v4 Planning.md](./v4%20Planning.md) - Complete implementation plan
- [KNOWLEDGE-OBJECTS-v1.md](./KNOWLEDGE-OBJECTS-v1.md) - Knowledge Object specification
- [PRD-AI-Brain-v1.md](v4-PRD-AI-Brain-v1.md) - Product requirements