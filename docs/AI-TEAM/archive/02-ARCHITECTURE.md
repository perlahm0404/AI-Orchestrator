# AI Team Architecture: Unified Design

**Date**: 2026-01-09
**Version**: 1.0
**Status**: Design Phase

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI TEAM ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 1: ADVISORS (Dialogue Mode)                                   │   │
│  │  ════════════════════════════════════════════════════════════════   │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Data      │  │    App      │  │   UI/UX     │                 │   │
│  │  │  Advisor    │  │  Advisor    │  │  Advisor    │                 │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │   │
│  │         │                │                │                         │   │
│  │         └────────────────┴────────────────┘                         │   │
│  │                          │                                          │   │
│  │                   Decision Documents                                │   │
│  │                   (ADR-XXX.md auto-created)                         │   │
│  └──────────────────────────┬──────────────────────────────────────────┘   │
│                             │                                               │
│                             ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 2: COORDINATOR (Autonomous Mode)                              │   │
│  │  ════════════════════════════════════════════════════════════════   │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    COORDINATOR                               │   │   │
│  │  │                                                              │   │   │
│  │  │  • Reads Decision Documents                                  │   │   │
│  │  │  • Breaks into Tasks                                         │   │   │
│  │  │  • Assigns to Builders                                       │   │   │
│  │  │  • Updates PROJECT_HQ.md                                     │   │   │
│  │  │  • Creates Session Handoffs                                  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────┬──────────────────────────────────────────┘   │
│                             │                                               │
│                             ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 3: BUILDERS (Autonomous Mode)                                 │   │
│  │  ════════════════════════════════════════════════════════════════   │   │
│  │                                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │ Feature  │  │   Bug    │  │   Test   │  │  Code    │           │   │
│  │  │ Builder  │  │  Fixer   │  │  Writer  │  │ Quality  │           │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │   │
│  │       │             │             │             │                   │   │
│  │       └─────────────┴─────────────┴─────────────┘                   │   │
│  │                          │                                          │   │
│  │                    Ralph Verification                               │   │
│  │                    (PASS/FAIL/BLOCKED)                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ARTIFACTS (Auto-Created & Maintained)                                      │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  PROJECT_HQ.md          Single source of truth for project status          │
│  decisions/ADR-XXX.md   Architecture Decision Records (by Advisors)        │
│  sessions/*.md          Session handoffs (by Coordinator)                   │
│  tasks/work_queue.json  Task queue (by Coordinator)                        │
│  knowledge/             Learning artifacts (by system)                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Modes

### Dialogue Mode (Advisors)

```python
class DialogueMode:
    """
    Interactive mode for strategic decisions.
    Advisor presents options, waits for human decision.
    """

    def workflow(self, user_request):
        # 1. Analyze request
        context = self.gather_context(user_request)

        # 2. Generate options (ALWAYS plural)
        options = self.generate_options(context)  # Min 2, max 4

        # 3. Present with tradeoffs
        self.present_options(options)

        # 4. WAIT for human decision (blocking)
        decision = self.await_decision()

        # 5. Auto-document decision
        adr = self.create_adr(decision)

        # 6. Hand off to Coordinator
        self.notify_coordinator(adr)
```

**Key Behaviors**:
- ALWAYS present options (never single recommendation)
- ALWAYS explain tradeoffs in plain language
- ALWAYS wait for human decision
- ALWAYS auto-create ADR after decision
- NEVER implement without approval

### Autonomous Mode (Coordinator & Builders)

```python
class AutonomousMode:
    """
    Autonomous mode for execution.
    Runs without human intervention unless BLOCKED.
    """

    def workflow(self, task):
        # 1. Execute within contract
        while self.iteration < self.max_iterations:
            result = self.execute_iteration(task)

            # 2. Check completion
            if self.completion_signal_detected(result):
                break

            # 3. Verify with Ralph
            verdict = self.ralph.verify(result)

            # 4. Handle verdict
            if verdict == PASS:
                break
            elif verdict == BLOCKED:
                self.escalate_to_human()  # Only human touch point
                break
            elif verdict == FAIL:
                if verdict.is_regression:
                    continue  # Retry
                else:
                    break  # Pre-existing, safe to merge

            self.iteration += 1

        # 5. Update status (automatic)
        self.update_project_hq()

        # 6. Create handoff (automatic)
        self.create_handoff()
```

**Key Behaviors**:
- Execute within contract limits
- Self-correct on FAIL (regression)
- Escalate only on BLOCKED
- Auto-update PROJECT_HQ.md
- Auto-create session handoffs

---

## Agent Specifications

### Tier 1: Advisors

#### Data Advisor

```yaml
name: data-advisor
mode: dialogue
domain: data architecture

responsibilities:
  - Schema design and review
  - Data modeling decisions
  - Migration strategy
  - Data quality rules
  - Performance optimization
  - Storage architecture

dialogue_triggers:
  - "How should we store..."
  - "What's the best schema for..."
  - "Database design for..."
  - "Data model for..."
  - Any mention of: schema, table, column, migration, database

output_artifacts:
  - decisions/ADR-XXX-data-*.md (auto-created)
  - Updated PROJECT_HQ.md roadmap section

options_template: |
  ## Data Architecture Options

  ### Option A: [Name]
  **Approach**: [Description]
  **Tradeoffs**:
  - Pro: [...]
  - Con: [...]
  **Best for**: [Use case]

  ### Option B: [Name]
  ...

  ### My Recommendation
  Option [X] because [plain language reason].

  **Questions for you**:
  1. [Clarifying question]
  2. [Constraint question]
```

#### App Advisor

```yaml
name: app-advisor
mode: dialogue
domain: application architecture

responsibilities:
  - System architecture decisions
  - Technology stack selection
  - API design and contracts
  - Integration patterns
  - Scalability planning
  - Security architecture

dialogue_triggers:
  - "How should we build..."
  - "What technology for..."
  - "Architecture for..."
  - "API design for..."
  - Any mention of: architecture, API, service, integration, stack

output_artifacts:
  - decisions/ADR-XXX-app-*.md (auto-created)
  - Updated PROJECT_HQ.md roadmap section

options_template: |
  ## Architecture Options

  ### Option A: [Name]
  **Approach**: [Description]
  **Tech Stack**: [Technologies]
  **Tradeoffs**:
  - Pro: [...]
  - Con: [...]

  ### Option B: [Name]
  ...

  ### My Recommendation
  Option [X] because [plain language reason].

  **Questions for you**:
  1. [Clarifying question]
```

#### UI/UX Advisor

```yaml
name: uiux-advisor
mode: dialogue
domain: user experience

responsibilities:
  - Interface design decisions
  - User flow design
  - Component architecture
  - Accessibility compliance
  - Data display patterns
  - Interaction patterns

dialogue_triggers:
  - "How should users..."
  - "What's the best UX for..."
  - "Interface for..."
  - "User flow for..."
  - Any mention of: UI, UX, interface, screen, page, component, flow

output_artifacts:
  - decisions/ADR-XXX-ux-*.md (auto-created)
  - Updated PROJECT_HQ.md roadmap section

options_template: |
  ## UX Options

  ### Option A: [Name]
  **Approach**: [Description]
  **User Flow**: [Steps]
  **Tradeoffs**:
  - Pro: [...]
  - Con: [...]

  ### Option B: [Name]
  ...

  ### My Recommendation
  Option [X] because [plain language reason].

  **Questions for you**:
  1. [Clarifying question]
```

### Tier 2: Coordinator

```yaml
name: coordinator
mode: autonomous
domain: project orchestration

responsibilities:
  - Read approved ADRs
  - Break decisions into tasks
  - Assign tasks to Builders
  - Maintain PROJECT_HQ.md
  - Create session handoffs
  - Track dependencies
  - Manage work queue

triggers:
  - ADR approved (auto-start)
  - "Build it" / "Implement" command
  - Session start (resume work)

auto_behaviors:
  on_adr_approved:
    - Parse ADR for implementation details
    - Generate task breakdown
    - Update work_queue.json
    - Update PROJECT_HQ.md with new tasks
    - Assign first task to appropriate Builder

  on_task_complete:
    - Update task status in PROJECT_HQ.md
    - Assign next task if available
    - Check for blockers
    - Update roadmap progress

  on_session_end:
    - Create session handoff
    - Update PROJECT_HQ.md status
    - Persist work queue state

output_artifacts:
  - PROJECT_HQ.md (continuous updates)
  - tasks/work_queue.json
  - sessions/session-*.md (handoffs)

contract:
  autonomy_level: L2
  max_iterations: 100
  forbidden_actions:
    - make_architectural_decisions  # That's Advisors' job
    - modify_adrs                   # Immutable once approved
    - bypass_ralph
  requires_approval:
    - delete_tasks
    - change_priority
```

### Tier 3: Builders

```yaml
# Inherited from existing AI_Orchestrator agents

builders:
  - name: feature-builder
    mode: autonomous
    contract: dev-team.yaml
    iterations: 50
    triggers:
      - Task type: feature
      - Assigned by Coordinator

  - name: bug-fixer
    mode: autonomous
    contract: qa-team.yaml
    iterations: 15
    triggers:
      - Task type: bugfix
      - Assigned by Coordinator

  - name: test-writer
    mode: autonomous
    contract: dev-team.yaml
    iterations: 15
    triggers:
      - Task type: test
      - Assigned by Coordinator

  - name: code-quality
    mode: autonomous
    contract: qa-team.yaml
    iterations: 20
    triggers:
      - Task type: quality
      - Assigned by Coordinator
```

---

## Information Flow

### Decision Flow (Dialogue → Autonomous)

```
User Request
    │
    ▼
┌─────────────┐
│   Advisor   │ ← Dialogue mode
│  (presents  │
│   options)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Human     │ ← Decision point
│  (chooses)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    ADR      │ ← Auto-created by Advisor
│  (written)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Coordinator │ ← Autonomous mode starts
│  (breaks    │
│   down)     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Builders   │ ← Fully autonomous
│  (execute)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Ralph     │ ← Verification
│  (verify)   │
└──────┬──────┘
       │
       ├─── PASS ───► Done
       │
       ├─── FAIL ───► Retry (if regression)
       │
       └─── BLOCKED ─► Human (only touch point)
```

### Status Flow (Auto-Update)

```
Any Agent Action
       │
       ▼
┌─────────────────────────────────────────┐
│           PROJECT_HQ.md                 │
│                                         │
│  Advisor decides  → Roadmap updated     │
│  Coordinator assigns → Tasks updated    │
│  Builder completes → Status updated     │
│  Session ends → Handoff linked          │
│                                         │
└─────────────────────────────────────────┘
       │
       ▼
   Human reads
   (always current)
```

---

## Artifact Specifications

### PROJECT_HQ.md (Single Source of Truth)

```markdown
# PROJECT_HQ: [Project Name]

**Last Updated**: [Auto-timestamp]
**Updated By**: [Agent name]

## Current Focus
[What's being worked on right now - auto-updated]

## Status Dashboard

| Task | Status | Agent | Updated |
|------|--------|-------|---------|
| [Auto-populated from work queue] |

## Blockers (Need You)
[Only populated when BLOCKED verdict - otherwise empty]

## Recent Decisions
| ADR | Title | Date | Status |
|-----|-------|------|--------|
| [Auto-populated from decisions/] |

## Roadmap
[Auto-updated by Advisors when decisions made]

## Session History
| Session | Date | Accomplishments |
|---------|------|-----------------|
| [Auto-populated from sessions/] |
```

### ADR Template (Auto-Created by Advisors)

```markdown
# ADR-XXX: [Title]

**Date**: [Auto]
**Status**: draft | approved | superseded
**Advisor**: data | app | uiux
**Deciders**: [Human name]

## Context
[What prompted this decision]

## Decision
[What was decided]

## Options Considered
### Option A: [Name]
[Description + tradeoffs]

### Option B: [Name]
[Description + tradeoffs]

## Rationale
[Why this option was chosen - in human's words]

## Implementation Notes
[Technical details for Coordinator/Builders]

## Consequences
- [What this enables]
- [What this constrains]
```

### Session Handoff (Auto-Created)

```markdown
# Session Handoff: [Date]-[Sequence]

**Created By**: Coordinator
**Project**: [Name]

## Accomplished
- [Auto-populated from completed tasks]

## In Progress
- [Auto-populated from active tasks]

## Blocked
- [Auto-populated from BLOCKED verdicts]

## Next Session
- [Auto-populated from work queue]

## Files Changed
| File | Changes | Agent |
|------|---------|-------|
| [Auto-populated] |

## Notes
[Any context for next session]
```

---

## Integration Points

### With Existing Systems

| System | Integration |
|--------|-------------|
| **Ralph** | Builders use for verification (unchanged) |
| **Wiggum** | Builders use for iteration control (unchanged) |
| **Knowledge Objects** | All agents consult pre-execution (unchanged) |
| **Contracts** | Builders follow existing contracts (unchanged) |
| **Golden Paths** | Coordinator respects file protection (new) |
| **RIS** | ADRs replace RIS for decisions (consolidation) |

### Cross-Repo Sync

```
AI_Orchestrator (Source)
├── agents/base/
│   ├── base_advisor.py      (NEW - sync to projects)
│   ├── base_coordinator.py  (NEW - sync to projects)
│   └── base_builder.py      (Existing agents)
│
└── governance/
    ├── contracts/
    │   ├── advisor.yaml     (NEW)
    │   ├── coordinator.yaml (NEW)
    │   └── *.yaml           (Existing)
    └── unified/
        └── governance.yaml  (NEW - merged format)

                    ↓ SYNC

CredentialMate
├── agents/
│   ├── data_advisor.py      (Extends base + HIPAA)
│   ├── coordinator.py       (Extends base + HIPAA)
│   └── *.py                  (Existing)
└── governance/
    └── contracts/            (HIPAA extensions)

KareMatch
├── agents/
│   ├── data_advisor.py      (Extends base + Healthcare)
│   ├── coordinator.py       (Extends base + Healthcare)
│   └── *.py                  (Existing)
└── governance/
    └── contracts/            (Healthcare extensions)
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Manual orchestration commands | ~20/session | 0 |
| Artifact creation prompts | ~10/session | 0 |
| Status tracking files | 3+ scattered | 1 (PROJECT_HQ.md) |
| Decision documentation | Manual | Auto (100%) |
| Session handoffs | Sometimes | Auto (100%) |
| Human intervention points | Many | Only BLOCKED |
