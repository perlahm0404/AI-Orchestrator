# AI Team Specification v3

**Date**: 2026-01-09
**Version**: 3.0
**Status**: Design Complete - Ready for Implementation
**Supersedes**: 00-OVERVIEW.md through 07-HIERARCHICAL-ORCHESTRATION-V2.md

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Agent Specifications](#3-agent-specifications)
4. [AI-Team-Plans Folder Structure](#4-ai-team-plans-folder-structure)
5. [Request Routing & Agent Invocation](#5-request-routing--agent-invocation)
6. [Advisor Decision Flow](#6-advisor-decision-flow)
7. [Coordinator Orchestration](#7-coordinator-orchestration)
8. [Event Logging & Observability](#8-event-logging--observability)
9. [Phase-Based Retrospectives](#9-phase-based-retrospectives)
10. [Governance & Contracts](#10-governance--contracts)
11. [Recovery & Error Handling](#11-recovery--error-handling)
12. [Implementation Plan](#12-implementation-plan)
13. [Success Metrics](#13-success-metrics)
14. [Appendices](#14-appendices)

---

## 1. Executive Summary

### 1.1 The Problem

Manual orchestration overhead consumes project time:
- Human acting as Program Manager, Project Manager, Technical Architect
- Manual triggering of plan mode, roadmap creation, status tracking
- No single source of truth for project state
- Context-switching between strategic decisions and execution

### 1.2 The Solution

A three-tier hierarchical AI team with autonomous orchestration:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TIER 1: ADVISORS (User-Invoked, Conditional Autonomy)                      │
│                                                                             │
│  Human invokes: @data-advisor, @app-advisor, @uiux-advisor                  │
│  Advisors can auto-decide when: ADR-aligned + confident + tactical          │
│  Advisors escalate when: ADR conflict, strategic domain, 5+ files           │
│  Output: ADRs, PROJECT_HQ updates                                           │
└────────────────────────────────────────────┬────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  TIER 2: COORDINATOR (Autonomous Orchestration)                             │
│                                                                             │
│  Auto-triggered by: ADR approval, task completion, phase completion         │
│  Manages: Task breakdown, work queue, Builder assignment, status tracking   │
│  Can invoke: Advisors (on 5+ file escalation), Builders (task assignment)   │
│  Output: work_queue.json, PROJECT_HQ updates, session handoffs              │
└────────────────────────────────────────────┬────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  TIER 3: BUILDERS (Autonomous Execution)                                    │
│                                                                             │
│  Auto-assigned by: Coordinator based on task type                           │
│  Includes: FeatureBuilder, BugFixer, TestWriter, CodeQuality                │
│  Verified by: Ralph (PASS/FAIL/BLOCKED)                                     │
│  Controlled by: Wiggum (iteration budgets: 15-50)                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Key Decisions (v3)

| Decision | v1/v2 | v3 (Final) |
|----------|-------|------------|
| **Request Routing** | Unspecified | User explicitly invokes `@advisor-name` |
| **Advisor Autonomy** | v1: Always wait / v2: Conditional | Conditional (can auto-decide when ADR-aligned) |
| **Confidence Scoring** | Unspecified | Pattern matching + historical success |
| **ADR Alignment** | Unspecified | Explicit tagging in ADR files |
| **Phase Detection** | Unspecified | Explicit completion triggers in specs |
| **Event Retention** | Unspecified | 7 days current, 30 days archive, then permanent |
| **Agent Lifecycle** | Assumed ephemeral | Explicitly ephemeral (Claude invocations) |

---

## 2. System Architecture

### 2.1 Three-Tier Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TIER 1: ADVISORS                                  │
│                    (User-Invoked + Conditional Autonomy)                    │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │  Data Advisor   │  │   App Advisor   │  │  UI/UX Advisor  │            │
│   │                 │  │                 │  │                 │            │
│   │ Schema, DB,     │  │ Architecture,   │  │ Interfaces,     │            │
│   │ Migrations,     │  │ APIs, Tech      │  │ Flows,          │            │
│   │ Data Integrity  │  │ Stack, Security │  │ Components      │            │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│            │                    │                    │                      │
│            └────────────────────┼────────────────────┘                      │
│                                 │                                           │
│                    ┌────────────▼────────────┐                              │
│                    │   ADRs + PROJECT_HQ     │                              │
│                    │   (Decision Artifacts)  │                              │
│                    └────────────┬────────────┘                              │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                          TIER 2: COORDINATOR                                │
│                       (Autonomous Orchestration)                            │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                         Coordinator Agent                            │  │
│   │                                                                      │  │
│   │  • Reads approved ADRs → Breaks into tasks                           │  │
│   │  • Manages work_queue.json → Assigns to Builders                     │  │
│   │  • Auto-updates PROJECT_HQ.md on every change                        │  │
│   │  • Creates session handoffs automatically                            │  │
│   │  • Triggers Advisors on 5+ file escalation                           │  │
│   │  • Detects phase completion → Triggers retrospectives                │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                 │                                           │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                           TIER 3: BUILDERS                                  │
│                        (Autonomous Execution)                               │
│                                                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   │FeatureBuilder│  │   BugFixer   │  │  TestWriter  │  │ CodeQuality  │   │
│   │              │  │              │  │              │  │              │   │
│   │ feature/*    │  │ main, fix/*  │  │ feature/*    │  │ main, fix/*  │   │
│   │ L1 autonomy  │  │ L2 autonomy  │  │ L1 autonomy  │  │ L2 autonomy  │   │
│   │ 50 iters     │  │ 15 iters     │  │ 15 iters     │  │ 20 iters     │   │
│   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                             │
│                    ┌────────────────────────────────────┐                   │
│                    │        Ralph Verification          │                   │
│                    │  (PASS / FAIL / BLOCKED verdicts)  │                   │
│                    └────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent Capabilities Matrix

| Agent | Mode | Autonomy | Can Write Code | Can Make Decisions | Ralph Required |
|-------|------|----------|----------------|-------------------|----------------|
| Data Advisor | User-invoked + Conditional | L3 | No | Yes (if ADR-aligned) | No |
| App Advisor | User-invoked + Conditional | L3 | No | Yes (if ADR-aligned) | No |
| UI/UX Advisor | User-invoked + Conditional | L3 | No | Yes (if ADR-aligned) | No |
| Coordinator | Autonomous | L2.5 | No | Yes (orchestration) | No |
| FeatureBuilder | Autonomous | L1 | Yes | No | At PR |
| BugFixer | Autonomous | L2 | Yes | No | Every commit |
| TestWriter | Autonomous | L1 | Yes | No | At PR |
| CodeQuality | Autonomous | L2 | Yes | No | Every commit |

### 2.3 Agent Lifecycle Model

**All agents are ephemeral** - invoked per task, not persistent processes.

```yaml
agent_lifecycle: ephemeral
# Agents are Claude Code invocations
# All state externalized to files in AI-Team-Plans/
# Session handoffs bridge invocations
# No in-memory state persists between sessions
```

**Implications**:
- Agents read canonical files on every invocation
- No "memory" of previous sessions except what's in files
- Anti-hallucination through grounding (files are source of truth)
- Session handoffs capture context for next invocation

---

## 3. Agent Specifications

### 3.1 Data Advisor

```yaml
name: data-advisor
mode: user_invoked_conditional
domain: data architecture, schema design, storage
autonomy_level: L3

invocation:
  explicit: "@data-advisor"
  keywords: [schema, table, column, database, migration, data model, storage]

capabilities:
  - Schema design and review
  - Migration strategy
  - Data quality rules
  - Performance optimization (queries, indexes)
  - Storage architecture (SQL vs NoSQL)

can_auto_decide_when:
  - Existing ADR covers the case (tagged alignment)
  - Confidence >= 85%
  - Decision is tactical (naming, organization)
  - Files touched <= 5

must_escalate_when:
  - Conflicts with existing ADR
  - Touches strategic domain (security, compliance, cost)
  - Files touched > 5
  - Confidence < 85%

output_artifacts:
  - decisions/ADR-XXX-data-*.md (after any decision)
  - PROJECT_HQ.md roadmap update

hipaa_extension: # CredentialMate only
  - Always flag PHI columns
  - Recommend encryption for sensitive data
  - Include audit logging in schema
```

### 3.2 App Advisor

```yaml
name: app-advisor
mode: user_invoked_conditional
domain: application architecture, APIs, tech stack
autonomy_level: L3

invocation:
  explicit: "@app-advisor"
  keywords: [architecture, API, service, integration, endpoint, stack, pattern]

capabilities:
  - System architecture decisions
  - Technology stack selection
  - API design and contracts
  - Integration patterns
  - Security architecture

can_auto_decide_when:
  - Existing ADR covers the case
  - Confidence >= 85%
  - Decision is tactical
  - Files touched <= 5

must_escalate_when:
  - Conflicts with existing ADR
  - Touches strategic domain
  - Files touched > 5
  - Confidence < 85%

output_artifacts:
  - decisions/ADR-XXX-app-*.md
  - PROJECT_HQ.md roadmap update
```

### 3.3 UI/UX Advisor

```yaml
name: uiux-advisor
mode: user_invoked_conditional
domain: user experience, interfaces, flows
autonomy_level: L3

invocation:
  explicit: "@uiux-advisor"
  keywords: [UI, UX, interface, screen, page, component, flow, user]

capabilities:
  - User flow design
  - Component architecture
  - Data display patterns
  - Accessibility compliance
  - Responsive design

can_auto_decide_when:
  - Existing ADR covers the case
  - Confidence >= 85%
  - Decision is tactical
  - Files touched <= 5

must_escalate_when:
  - Conflicts with existing ADR
  - Touches strategic domain
  - Files touched > 5
  - Confidence < 85%

output_artifacts:
  - decisions/ADR-XXX-ux-*.md
  - PROJECT_HQ.md roadmap update
```

### 3.4 Coordinator

```yaml
name: coordinator
mode: autonomous
domain: project orchestration
autonomy_level: L2.5

triggers:
  - adr_approved: Break into tasks, add to queue
  - task_completed: Check deps, assign next
  - task_blocked: Add to blockers, continue others
  - session_end: Create handoff
  - scope_escalation: Trigger Advisor (5+ files)
  - phase_complete: Generate retrospective

auto_behaviors:
  - update_project_hq_on_every_change: true
  - log_all_events: true
  - create_handoff_on_session_end: true
  - respect_task_dependencies: true
  - trigger_retrospective_on_phase: true

allowed_actions:
  - read_adr, read_codebase, read_project_hq
  - create_task, update_task_status, assign_task
  - update_project_hq, update_work_queue
  - create_handoff, create_retrospective
  - log_event, trigger_advisor, notify_builder

forbidden_actions:
  - write_code
  - modify_application_files
  - make_architectural_decisions (Advisors' job)
  - modify_adr (ADRs are immutable)
  - bypass_dependencies
  - skip_logging

limits:
  max_iterations: 100
  max_concurrent_tasks: 3
  max_queue_size: 50
  max_tasks_per_adr: 20
```

### 3.5 Builders (Existing)

Builders are existing agents from AI_Orchestrator, unchanged:

| Builder | Contract | Iterations | Branch | Ralph Timing |
|---------|----------|------------|--------|--------------|
| FeatureBuilder | dev-team.yaml | 50 | feature/* | At PR |
| BugFixer | qa-team.yaml | 15 | main, fix/* | Every commit |
| TestWriter | dev-team.yaml | 15 | feature/* | At PR |
| CodeQuality | qa-team.yaml | 20 | main, fix/* | Every commit |

---

## 4. AI-Team-Plans Folder Structure

### 4.1 Location

Each target repository contains its own `AI-Team-Plans/` folder:

```
credentialmate/AI-Team-Plans/    # CredentialMate instance
karematch/AI-Team-Plans/         # KareMatch instance
```

### 4.2 Complete Structure

```
AI-Team-Plans/
│
├── PROJECT_HQ.md                    # Single source of truth (living)
│
├── specs/                           # Human-authored specifications
│   ├── epic-rules-engine.md         # Epic-level specs
│   ├── story-user-auth.md           # Story-level specs
│   └── task-api-endpoint.md         # Task-level specs
│
├── decisions/                       # Architecture Decision Records (immutable)
│   ├── ADR-001-rules-engine-approach.md
│   ├── ADR-002-data-model-design.md
│   └── index.md                     # ADR index with tags
│
├── tasks/                           # Work queues (Coordinator-managed)
│   └── work_queue.json
│
├── sessions/                        # Session handoffs
│   ├── latest.md                    # Symlink to most recent
│   ├── 2026-01-09-001.md
│   └── archive/                     # Old sessions (30+ days)
│
├── events/                          # Observability (event stream)
│   ├── current/                     # Last 7 days (detailed)
│   │   ├── 2026-01-09-001-advisor-triggered.md
│   │   └── 2026-01-09-002-coordinator-assigned.md
│   ├── metrics.json                 # Aggregated counts (all-time)
│   └── archive/                     # 30 days, then permanent archive
│
└── retrospectives/                  # Phase learnings (permanent)
    ├── PROJ-001-phase-1.md
    ├── PROJ-001-phase-2.md
    └── patterns.json                # Aggregated learnings
```

### 4.3 File Lifecycle & Retention

| File Type | Lifecycle | Git Strategy | Retention |
|-----------|-----------|--------------|-----------|
| `PROJECT_HQ.md` | Living (auto-updated) | Always commit | Permanent |
| `specs/*.md` | Living (human-edited) | Always commit | Permanent |
| `decisions/ADR-*.md` | Immutable once approved | Always commit | Permanent |
| `decisions/index.md` | Living (auto-updated) | Always commit | Permanent |
| `tasks/work_queue.json` | Living (Coordinator) | Always commit | Permanent |
| `sessions/*.md` | Archivable | Commit | 30 days active, then archive |
| `events/current/*.md` | Ephemeral | Optional commit | 7 days, then archive |
| `events/metrics.json` | Rolling | Always commit | Daily rollup, permanent |
| `events/archive/` | Compressed | Commit monthly | 30 days, then permanent |
| `retrospectives/*.md` | Permanent | Always commit | Permanent |
| `retrospectives/patterns.json` | Living | Always commit | Permanent |

### 4.4 Bootstrap Requirements

Before automation can begin, these artifacts must exist:

```
Bootstrap Checklist:
- [ ] AI-Team-Plans/ folder created
- [ ] PROJECT_HQ.md (from template, can be empty sections)
- [ ] decisions/ folder (can be empty)
- [ ] decisions/index.md (empty index)
- [ ] tasks/work_queue.json (empty array: {"project": "name", "tasks": []})
- [ ] events/ folder structure
- [ ] events/metrics.json (zeroed counters)
- [ ] retrospectives/ folder (can be empty)
- [ ] retrospectives/patterns.json (empty: {"patterns": [], "thresholds": {}})
```

### 4.5 Anti-Hallucination Strategy

**Problem**: Agents can "remember" things incorrectly or make up prior decisions.

**Solution**: All agent memory is externalized. Agents MUST read canonical sources.

```python
# CORRECT: Agent reads from source of truth
def advisor_make_decision(context):
    # 1. Read existing ADRs (not from "memory")
    adrs = read_all_adrs("AI-Team-Plans/decisions/")

    # 2. Read PROJECT_HQ for current state
    project_hq = read_file("AI-Team-Plans/PROJECT_HQ.md")

    # 3. Read specs for requirements
    spec = read_file(f"AI-Team-Plans/specs/{context.spec_file}")

    # 4. Make decision based on EXTERNAL sources
    decision = analyze(adrs, project_hq, spec, context)

    # 5. Document decision (creates external record)
    write_adr(decision)

    return decision
```

**Grounding Rules**:
1. **Specs are canonical** - If not in `specs/`, requirement doesn't exist
2. **ADRs are immutable** - Once approved, decisions cannot change
3. **PROJECT_HQ is current state** - Always read before acting
4. **Events are evidence** - What happened is logged, not remembered
5. **Agents don't trust themselves** - Always verify against files

---

## 5. Request Routing & Agent Invocation

### 5.1 How Users Invoke Advisors

**Method**: User explicitly invokes advisor by name.

```
User: "@data-advisor how should we structure the rules engine data?"
→ Data Advisor activates

User: "@app-advisor what's the best API pattern for this feature?"
→ App Advisor activates

User: "@uiux-advisor how should users interact with the dashboard?"
→ UI/UX Advisor activates
```

**Rationale**: Explicit invocation prevents ambiguity about which advisor should handle a request. User knows their domain best.

### 5.2 How Coordinator Gets Triggered

Coordinator is **auto-triggered** by events, not user invocation:

| Trigger Event | Coordinator Action |
|---------------|-------------------|
| ADR approved (status: approved) | Break ADR into tasks, add to queue |
| Task completed (Ralph PASS) | Check deps, assign next task |
| Task blocked (Ralph BLOCKED) | Add to PROJECT_HQ blockers |
| Session ending | Create handoff document |
| 5+ file scope detected | Invoke appropriate Advisor |
| Phase tasks complete | Generate retrospective |

### 5.3 How Builders Get Assigned

Coordinator assigns Builders based on task type:

```python
def coordinator_assign_task(task):
    """Assign task to appropriate Builder based on type."""

    BUILDER_MAP = {
        "feature": "FeatureBuilder",
        "bugfix": "BugFixer",
        "test": "TestWriter",
        "quality": "CodeQuality",
        "migration": "manual"  # Humans do migrations
    }

    builder_type = BUILDER_MAP.get(task.type, "FeatureBuilder")

    if builder_type == "manual":
        # Add to blockers, human must handle
        add_to_blockers(task, "Requires manual intervention")
        return

    # Assign to Builder
    task.agent = builder_type
    task.status = "in_progress"

    # Notify Builder (triggers execution)
    notify_builder(builder_type, task)
```

### 5.4 Debug Work Queue: Discovery Agent

**Question from user**: Which agent scans the repo and creates a debug work queue for debugger agent?

**Answer**: The **Bug Discovery System** (existing in AI_Orchestrator) scans the repo:

```
Discovery System
├── parsers/
│   ├── eslint_parser.py      # Lint errors
│   ├── typescript_parser.py  # Type errors
│   ├── vitest_parser.py      # Test failures
│   └── guardrails_parser.py  # @ts-ignore, .skip(), etc.
├── scanner.py                # Orchestrates all parsers
├── baseline.py               # Tracks known vs new issues
└── task_generator.py         # Creates work queue tasks
```

**Invocation**:
```bash
# CLI command to scan and generate debug tasks
aibrain discover-bugs --project credentialmate
```

**Output**: Adds tasks to `tasks/work_queue.json`:
```json
{
  "id": "BUG-001",
  "type": "bugfix",
  "agent": "BugFixer",
  "description": "Fix 2 type errors in src/auth/session.ts",
  "priority": "P0",
  "source": "discovery",
  "status": "pending"
}
```

### 5.5 When Each Agent Type Is Invoked

| Agent | Invoked By | Trigger |
|-------|------------|---------|
| **Data Advisor** | User | `@data-advisor` or Coordinator (5+ file escalation in data domain) |
| **App Advisor** | User | `@app-advisor` or Coordinator (5+ file escalation in app domain) |
| **UI/UX Advisor** | User | `@uiux-advisor` or Coordinator (5+ file escalation in UI domain) |
| **Coordinator** | System | ADR approval, task completion, session end, phase complete |
| **FeatureBuilder** | Coordinator | Task type = feature |
| **BugFixer** | Coordinator | Task type = bugfix (from discovery or ADR) |
| **TestWriter** | Coordinator | Task type = test |
| **CodeQuality** | Coordinator | Task type = quality |

### 5.6 QA Agents Invocation

QA agents (BugFixer, CodeQuality) are invoked in two scenarios:

**Scenario 1: Discovery-driven** (proactive)
```
1. Run: aibrain discover-bugs --project X
2. Discovery scans for lint, type, test, guardrail issues
3. Creates tasks in work_queue.json with type=bugfix or type=quality
4. Coordinator assigns tasks to BugFixer or CodeQuality
5. Agents execute autonomously
```

**Scenario 2: ADR-driven** (reactive)
```
1. Advisor creates ADR with quality improvement items
2. Coordinator breaks ADR into tasks
3. Quality-related tasks assigned to CodeQuality
4. Bug-related tasks assigned to BugFixer
```

---

## 6. Advisor Decision Flow

### 6.1 Conditional Autonomy Model

Advisors can decide autonomously when conditions are met:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ADVISOR DECISION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  1. Check for ADR conflicts   │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │   CONFLICT    │               │  NO CONFLICT  │
            └───────┬───────┘               └───────┬───────┘
                    │                               │
                    ▼                               ▼
            ┌───────────────┐       ┌───────────────────────────┐
            │   ESCALATE    │       │ 2. Check strategic domain │
            │   to human    │       └─────────────┬─────────────┘
            └───────────────┘                     │
                                    ┌─────────────┴─────────────┐
                                    │                           │
                                    ▼                           ▼
                            ┌───────────────┐           ┌───────────────┐
                            │   STRATEGIC   │           │  NOT STRATEGIC│
                            └───────┬───────┘           └───────┬───────┘
                                    │                           │
                                    ▼                           ▼
                            ┌───────────────┐       ┌───────────────────────┐
                            │   ESCALATE    │       │ 3. Check file count   │
                            │   to human    │       └─────────────┬─────────┘
                            └───────────────┘                     │
                                                    ┌─────────────┴─────────┐
                                                    │                       │
                                                    ▼                       ▼
                                            ┌───────────────┐       ┌───────────────┐
                                            │    >5 FILES   │       │   ≤5 FILES    │
                                            └───────┬───────┘       └───────┬───────┘
                                                    │                       │
                                                    ▼                       ▼
                                            ┌───────────────┐       ┌───────────────────┐
                                            │   ESCALATE    │       │ 4. Check ADR      │
                                            │   to human    │       │    alignment &    │
                                            └───────────────┘       │    confidence     │
                                                                    └─────────┬─────────┘
                                                                              │
                                                            ┌─────────────────┼─────────────────┐
                                                            │                 │                 │
                                                            ▼                 ▼                 ▼
                                                    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
                                                    │ ADR ALIGNED   │ │ TACTICAL      │ │ UNCERTAIN     │
                                                    │ conf >= 85%   │ │ conf >= 85%   │ │ conf < 85%    │
                                                    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
                                                            │                 │                 │
                                                            ▼                 ▼                 ▼
                                                    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
                                                    │ AUTO-PROCEED  │ │ AUTO-PROCEED  │ │   ESCALATE    │
                                                    │ Log + ADR     │ │ Log + ADR     │ │   to human    │
                                                    └───────────────┘ └───────────────┘ └───────────────┘
```

### 6.2 Strategic vs Tactical Domains

**Strategic Domains (Always escalate to human)**:
- `security` - Auth, encryption, access control
- `external_dependency` - New npm/pip packages, third-party APIs
- `data_schema` - Database migrations, model changes
- `infrastructure` - Docker, cloud resources, CI/CD
- `compliance` - HIPAA, GDPR, legal requirements
- `cost` - Paid services, resource scaling

**Tactical Domains (Can auto-decide if confident)**:
- `naming_convention` - Variable/function names
- `code_organization` - File structure within module
- `error_message_wording` - User-facing text
- `test_structure` - How tests are organized
- `logging_format` - Log message format

**Decision Tree**:
```
Is it STRATEGIC?
├── Affects external users directly? → YES
├── Changes data schema? → YES
├── Adds external dependency? → YES
├── Touches security/auth? → YES
├── Cost implications > $0? → YES
├── Affects compliance (HIPAA/etc)? → YES
└── None of above? → TACTICAL
```

### 6.3 Confidence Scoring

Confidence is calculated using pattern matching and historical success:

```python
def calculate_confidence(context: AdvisorContext) -> float:
    """
    Calculate confidence score for autonomous decision.
    Uses pattern matching + historical success rate.
    """
    score = 0.0

    # 1. ADR alignment (40% weight)
    if has_matching_adr(context):
        alignment = check_adr_alignment(context)
        if alignment.tags_match:
            score += 0.40
        elif alignment.domain_match:
            score += 0.25

    # 2. Historical success (30% weight)
    similar_decisions = find_similar_decisions(context)
    if similar_decisions:
        success_rate = calculate_success_rate(similar_decisions)
        score += 0.30 * success_rate

    # 3. Scope boundedness (20% weight)
    if context.estimated_files <= 3:
        score += 0.20
    elif context.estimated_files <= 5:
        score += 0.10

    # 4. Requirement clarity (10% weight)
    if not has_ambiguous_requirements(context):
        score += 0.10

    return min(score, 1.0)
```

### 6.4 ADR Alignment Checking

ADR alignment uses explicit tagging:

**ADR File Format (with tags)**:
```markdown
# ADR-023: Certification Tracking Data Model

**Date**: 2026-01-09
**Status**: approved
**Advisor**: data-advisor
**Deciders**: tmac

## Tags
```yaml
tags: [certification, tracking, database, schema]
applies_to:
  - "src/models/certification*"
  - "src/api/certification*"
  - "alembic/versions/*certification*"
domains: [data_schema]
```

## Context
[...]
```

**Alignment Check**:
```python
def check_adr_alignment(context: AdvisorContext) -> AlignmentResult:
    """
    Check if proposed decision aligns with existing ADR.
    Uses explicit tag matching.
    """
    relevant_adrs = []

    for adr in load_all_adrs():
        # Check tag overlap
        tag_overlap = set(context.tags) & set(adr.tags)

        # Check path matching
        path_match = any(
            fnmatch(context.primary_file, pattern)
            for pattern in adr.applies_to
        )

        # Check domain matching
        domain_match = context.domain in adr.domains

        if tag_overlap or path_match or domain_match:
            relevant_adrs.append(AlignmentResult(
                adr=adr,
                tags_match=len(tag_overlap) >= 2,
                path_match=path_match,
                domain_match=domain_match
            ))

    if not relevant_adrs:
        return AlignmentResult(aligned=False, reason="NO_RELEVANT_ADR")

    # Check for conflicts
    best_match = max(relevant_adrs, key=lambda r: r.score)

    if conflicts_with(context.proposed_decision, best_match.adr):
        return AlignmentResult(aligned=False, reason="ADR_CONFLICT", adr=best_match.adr)

    return AlignmentResult(aligned=True, adr=best_match.adr)
```

### 6.5 ADR Index File

Maintain an index for fast lookups:

```markdown
# ADR Index

**Last Updated**: 2026-01-09T18:00:00Z
**Total ADRs**: 25

## By Tag

| Tag | ADRs |
|-----|------|
| authentication | ADR-001, ADR-015 |
| certification | ADR-023 |
| database | ADR-002, ADR-012, ADR-023 |
| schema | ADR-002, ADR-012, ADR-023 |

## By Domain

| Domain | ADRs |
|--------|------|
| data_schema | ADR-002, ADR-012, ADR-023 |
| security | ADR-001, ADR-015 |
| api | ADR-003, ADR-018 |

## By File Path

| Pattern | ADRs |
|---------|------|
| src/models/* | ADR-002, ADR-012, ADR-023 |
| src/auth/* | ADR-001, ADR-015 |
| src/api/* | ADR-003, ADR-018 |
```

---

## 7. Coordinator Orchestration

### 7.1 Task Breakdown from ADR

When an ADR is approved, Coordinator breaks it into tasks:

```python
def coordinator_break_into_tasks(adr: ADR) -> List[Task]:
    """Break approved ADR into executable tasks."""

    tasks = []
    impl_notes = adr.implementation_notes

    # Parse implementation notes for task types
    if impl_notes.has_schema_changes:
        tasks.append(Task(
            type="migration",
            agent="manual",  # Humans do migrations
            priority="P0",
            description="Create database migration",
            dependencies=[]
        ))

    if impl_notes.has_api_changes:
        tasks.append(Task(
            type="feature",
            agent="FeatureBuilder",
            priority="P1",
            description=impl_notes.api_description,
            dependencies=["migration"] if impl_notes.has_schema_changes else []
        ))

    if impl_notes.has_ui_changes:
        tasks.append(Task(
            type="feature",
            agent="FeatureBuilder",
            priority="P2",
            description=impl_notes.ui_description,
            dependencies=["api"] if impl_notes.has_api_changes else []
        ))

    # Always add test task
    tasks.append(Task(
        type="test",
        agent="TestWriter",
        priority="P3",
        description=f"Write tests for {adr.title}",
        dependencies=[t.id for t in tasks if t.agent != "manual"]
    ))

    # Assign IDs
    for i, task in enumerate(tasks):
        task.id = f"TASK-{adr.number}-{i+1:03d}"
        task.adr = adr.id

    return tasks
```

### 7.2 Work Queue Format

```json
{
  "project": "credentialmate",
  "last_updated": "2026-01-09T15:30:00Z",
  "tasks": [
    {
      "id": "TASK-023-001",
      "adr": "ADR-023",
      "title": "Create migration for certification_completions",
      "type": "migration",
      "agent": "manual",
      "status": "pending",
      "priority": "P0",
      "dependencies": [],
      "estimated_files": 1
    },
    {
      "id": "TASK-023-002",
      "adr": "ADR-023",
      "title": "Implement certification completion API",
      "type": "feature",
      "agent": "FeatureBuilder",
      "status": "pending",
      "priority": "P1",
      "dependencies": ["TASK-023-001"],
      "estimated_files": 3
    }
  ]
}
```

### 7.3 Phase Detection

Phases are defined in specs with explicit completion triggers:

```yaml
# In specs/epic-rules-engine.md

phases:
  - id: 1
    name: "Foundation"
    description: "Core data models and database schema"
    tasks:
      - "Create database migrations"
      - "Implement base models"
      - "Set up API structure"
    completion_triggers:
      all_of:
        - "All tasks with tag 'foundation' completed"
        - "Ralph PASS on all foundation code"
        - "No P0 blockers in phase 1"
    on_complete:
      - generate_retrospective
      - notify_human
      - unlock_phase_2

  - id: 2
    name: "Business Logic"
    description: "Rules engine implementation"
    depends_on: [1]
    completion_triggers:
      all_of:
        - "All tasks with tag 'business-logic' completed"
        - "Test coverage >= 80%"
        - "Performance benchmarks pass"
```

**Phase Detection Logic**:
```python
def coordinator_check_phase_complete(phase: Phase) -> bool:
    """Check if phase completion triggers are met."""

    for trigger in phase.completion_triggers.all_of:
        if not evaluate_trigger(trigger):
            return False

    return True

def evaluate_trigger(trigger: str) -> bool:
    """Evaluate a single completion trigger."""

    if trigger.startswith("All tasks with tag"):
        tag = extract_tag(trigger)
        tasks = get_tasks_by_tag(tag)
        return all(t.status == "completed" for t in tasks)

    if trigger.startswith("Ralph PASS"):
        scope = extract_scope(trigger)
        return check_ralph_pass(scope)

    if trigger.startswith("No P0 blockers"):
        phase_id = extract_phase(trigger)
        blockers = get_blockers(phase_id)
        return not any(b.priority == "P0" for b in blockers)

    if trigger.startswith("Test coverage"):
        threshold = extract_percentage(trigger)
        return get_coverage() >= threshold

    return False
```

### 7.4 5+ File Escalation

When Builder detects scope exceeds 5 files:

```python
def coordinator_handle_scope_escalation(task: Task, builder_analysis: Dict):
    """Handle 5+ file scope escalation."""

    # 1. Log event
    log_event("SCOPE_ESCALATION", {
        "task_id": task.id,
        "estimated_files": builder_analysis["files_to_touch"],
        "threshold": 5
    })

    # 2. Determine appropriate Advisor
    advisor_type = infer_advisor_type(task)
    advisor = get_advisor(advisor_type)

    # 3. Request Advisor analysis
    response = advisor.consult(AdvisorRequest(
        requester="coordinator",
        task=task,
        question="Should this task be broken into smaller pieces?"
    ))

    # 4. Handle response
    if response.recommendation == "SPLIT_TASK":
        # Replace task with subtasks
        remove_task(task.id)
        for new_task in response.suggested_tasks:
            add_task(new_task)
        return EscalationResult(action="SPLIT", new_tasks=response.suggested_tasks)

    elif response.recommendation == "PROCEED":
        # Advisor approved large scope
        return EscalationResult(action="PROCEED", guidance=response.guidance)

    else:
        # Needs human decision
        return EscalationResult(action="ESCALATE_HUMAN", options=response.options)
```

---

## 8. Event Logging & Observability

### 8.1 Event Types

| Event Type | Detailed Log | Counted | Description |
|------------|--------------|---------|-------------|
| `ADVISOR_TRIGGERED` | Yes | Yes | Advisor activated by user |
| `ADVISOR_AUTO_DECIDED` | Yes | Yes | Advisor decided autonomously |
| `ADVISOR_ESCALATED` | Yes | Yes | Advisor escalated to human |
| `COORDINATOR_TASK_CREATED` | Yes | Yes | New task from ADR |
| `COORDINATOR_TASK_ASSIGNED` | No | Yes | Task assigned to Builder |
| `BUILDER_ITERATION` | No | Yes | Builder iteration (many) |
| `BUILDER_COMPLETED` | Yes | Yes | Builder finished task |
| `BUILDER_BLOCKED` | Yes | Yes | Builder hit BLOCKED |
| `RALPH_PASS` | No | Yes | Ralph PASS verdict |
| `RALPH_FAIL` | No | Yes | Ralph FAIL verdict |
| `RALPH_BLOCKED` | Yes | Yes | Ralph BLOCKED verdict |
| `SCOPE_ESCALATION` | Yes | Yes | 5+ files trigger |
| `PHASE_COMPLETE` | Yes | Yes | Phase milestone |
| `RETROSPECTIVE_CREATED` | Yes | Yes | Retro generated |

### 8.2 Detailed Event Format

```markdown
# EVENT-2026-01-09-001

**Timestamp**: 2026-01-09T14:23:45Z
**Type**: ADVISOR_AUTO_DECIDED
**Agent**: Data Advisor
**Session**: session-2026-01-09-001

## Trigger
Coordinator requested consultation for task TASK-023-002

## Context
- **Task**: TASK-023-002 - Implement user profile API
- **Domain**: data
- **Files analyzed**: 3
- **Existing ADRs checked**: ADR-020, ADR-021, ADR-023

## Decision Made
- **Action**: AUTO_PROCEED
- **Reason**: Decision aligns with ADR-023 (tag match: database, schema)
- **Confidence**: 92%

## Impact
- Task unblocked
- No human intervention required

## Escalation
- **Escalated**: No
- **Reason**: Confidence above threshold, ADR-aligned
```

### 8.3 Metrics JSON

```json
{
  "project": "credentialmate",
  "period": "2026-01-09",
  "generated_at": "2026-01-09T23:59:59Z",

  "totals": {
    "events_total": 147,
    "events_logged_detail": 12,
    "events_counted_only": 135
  },

  "by_agent": {
    "advisor_data": {
      "triggers": 3,
      "auto_decisions": 2,
      "escalations": 1,
      "avg_confidence": 0.89
    },
    "coordinator": {
      "tasks_created": 8,
      "tasks_assigned": 12,
      "handoffs_created": 1
    },
    "builder_feature": {
      "iterations": 48,
      "completions": 4,
      "blocks": 1
    }
  },

  "ralph_verdicts": {
    "pass": 18,
    "fail": 7,
    "blocked": 2
  },

  "escalations": {
    "to_human": 3,
    "scope_triggers": 1,
    "adr_conflicts": 0
  }
}
```

---

## 9. Phase-Based Retrospectives

### 9.1 Trigger

Retrospectives are auto-generated when phase completion triggers are met:

```python
def coordinator_on_phase_complete(phase: Phase):
    """Auto-generate retrospective when phase completes."""

    # 1. Gather metrics
    metrics = gather_phase_metrics(phase)
    events = get_phase_events(phase)
    tasks = get_phase_tasks(phase)

    # 2. Analyze patterns
    patterns = identify_patterns(tasks, events, metrics)

    # 3. Generate retrospective
    retro = generate_retrospective(phase, metrics, patterns)

    # 4. Update patterns.json
    update_patterns_json(patterns)

    # 5. Log event
    log_event("RETROSPECTIVE_CREATED", {
        "phase": phase.id,
        "tasks_completed": metrics.tasks_completed,
        "patterns_identified": len(patterns)
    })

    # 6. Notify human
    notify_human(f"Phase {phase.id} complete. Retrospective generated.")
```

### 9.2 Retrospective Template

```markdown
# Retrospective: PROJ-001 Phase 1 - Foundation

**Phase**: 1 - Foundation
**Project**: credentialmate
**Duration**: 2026-01-06 to 2026-01-09
**Generated**: 2026-01-09T18:30:00Z
**Generated By**: Coordinator (auto)

---

## Summary

| Metric | Value |
|--------|-------|
| Tasks Completed | 8 |
| Tasks Blocked | 1 |
| Total Iterations | 47 |
| Avg Iterations/Task | 5.9 |
| Human Interventions | 2 |
| Auto Decisions | 6 |

---

## What Worked Well

- Advisor auto-decisions reduced human interrupts by 75%
- ADR grounding prevented 2 potential conflicts
- Scope escalation triggered correctly when needed

---

## What Didn't Work

- Confidence threshold too high (escalated at 84%, threshold 85%)
- Task TASK-023-003 took 15 iterations (expected 5-8)

---

## Barriers Encountered

| Barrier | Task | Resolution |
|---------|------|------------|
| Ralph BLOCKED | TASK-023-005 | Pre-existing, human override |

---

## Proposed Changes

| Change | Category | Priority |
|--------|----------|----------|
| Lower confidence threshold to 80% | Governance | P1 |

---

## Patterns Identified

### Pattern: "Spec Ambiguity → Iteration Bloat"
Tasks with unclear specs averaged 12 iterations vs 5 for clear specs.

---

## Phase 2 Recommendations

1. Review specs before starting
2. Monitor iteration counts early
```

### 9.3 Patterns Aggregation

```json
{
  "project": "credentialmate",
  "last_updated": "2026-01-09T18:30:00Z",

  "patterns": [
    {
      "id": "PAT-001",
      "name": "Spec Ambiguity → Iteration Bloat",
      "type": "anti-pattern",
      "discovered_in": "PROJ-001-phase-1",
      "occurrences": 3,
      "detection_rule": "task.iterations > (avg_iterations * 2)",
      "prevention": "Require Advisor spec review",
      "status": "active"
    }
  ],

  "thresholds": {
    "confidence_threshold": 0.85,
    "iteration_warning": 10,
    "file_scope_trigger": 5
  }
}
```

---

## 10. Governance & Contracts

### 10.1 Advisor Contract

```yaml
# governance/contracts/advisor.yaml

name: advisor
version: "3.0"
mode: user_invoked_conditional
autonomy_level: L3

applies_to:
  - data-advisor
  - app-advisor
  - uiux-advisor

# ═══════════════════════════════════════════════════════════════
# DECISION AUTONOMY
# ═══════════════════════════════════════════════════════════════

autonomous_decision_rules:
  can_auto_decide_when:
    all_of:
      - adr_aligned: true
      - confidence_threshold: 0.85
      - max_files_touched: 5
    any_of:
      - domain_type: tactical

  must_escalate_when:
    any_of:
      - adr_conflict: true
      - domain_type: strategic
      - files_touched_exceeds: 5
      - confidence_below: 0.85

strategic_domains:
  - security
  - external_dependency
  - data_schema
  - infrastructure
  - compliance
  - cost

tactical_domains:
  - naming_convention
  - code_organization
  - error_message_wording
  - test_structure
  - logging_format

# ═══════════════════════════════════════════════════════════════
# ALLOWED/FORBIDDEN ACTIONS
# ═══════════════════════════════════════════════════════════════

allowed_actions:
  - read_file
  - read_codebase
  - search_codebase
  - analyze_schema
  - analyze_architecture
  - analyze_components
  - create_adr
  - update_adr_draft
  - update_project_hq
  - update_adr_index
  - log_event
  - consult_knowledge_objects

forbidden_actions:
  - write_code
  - modify_application_files
  - run_commands
  - execute_tests
  - deploy
  - modify_infrastructure
  - bypass_escalation_rules

# ═══════════════════════════════════════════════════════════════
# BEHAVIORS
# ═══════════════════════════════════════════════════════════════

behaviors:
  # Option presentation (when escalating)
  must_present_options: true
  min_options: 2
  max_options: 4
  must_explain_tradeoffs: true
  plain_language_required: true

  # Decision documentation (always)
  must_document_decision: true
  adr_required_for_all_decisions: true
  log_all_decisions: true

limits:
  max_iterations: 5
  max_analysis_time_seconds: 300
  max_files_to_analyze: 50

on_violation: halt
```

### 10.2 Coordinator Contract

```yaml
# governance/contracts/coordinator.yaml

name: coordinator
version: "3.0"
mode: autonomous
autonomy_level: L2.5

# ═══════════════════════════════════════════════════════════════
# TRIGGERS
# ═══════════════════════════════════════════════════════════════

triggers:
  - event: adr_approved
    action: break_into_tasks

  - event: task_completed
    action: check_dependencies_assign_next

  - event: task_blocked
    action: add_to_blockers_continue_others

  - event: session_end
    action: create_handoff

  - event: scope_escalation
    action: trigger_advisor_consultation

  - event: phase_complete
    action: generate_retrospective

# ═══════════════════════════════════════════════════════════════
# ALLOWED/FORBIDDEN ACTIONS
# ═══════════════════════════════════════════════════════════════

allowed_actions:
  - read_adr
  - read_codebase
  - read_project_hq
  - create_task
  - update_task_status
  - assign_task
  - update_project_hq
  - update_work_queue
  - update_adr_index
  - create_handoff
  - create_retrospective
  - log_event
  - trigger_advisor
  - notify_builder

forbidden_actions:
  - write_code
  - modify_application_files
  - make_architectural_decisions
  - modify_adr
  - bypass_dependencies
  - skip_logging

limits:
  max_iterations: 100
  max_concurrent_tasks: 3
  max_queue_size: 50
  max_tasks_per_adr: 20

auto_behaviors:
  update_project_hq_on_change: true
  log_all_events: true
  create_handoff_on_session_end: true
  respect_task_dependencies: true
  trigger_retrospective_on_phase: true

on_violation: halt
```

### 10.3 Golden Paths (Protected Files)

```yaml
# governance/unified/golden-paths.yaml

version: "3.0"

protection_levels:
  BLOCK_AND_ASK:
    description: "Cannot modify without explicit human approval"
    files:
      - "CLAUDE.md"
      - ".claude/instructions.md"
      - "governance/**/*.yaml"
      - "AI-Team-Plans/PROJECT_HQ.md"  # Coordinator can update specific sections
      - "AI-Team-Plans/decisions/ADR-*.md"  # Immutable once approved

  VALIDATE_FIRST:
    description: "Must pass validation before modification"
    files:
      - "**/migrations/**"
      - "**/alembic/versions/**"
      - "package.json"
      - "requirements.txt"

  WARN_AND_LOG:
    description: "Allow but log modification"
    files:
      - "Dockerfile*"
      - "docker-compose*.yml"
      - ".env*"

  SECURITY_REVIEW:
    description: "Requires security check"
    files:
      - "**/auth/**"
      - "**/encryption/**"

# Project-specific extensions
project_extensions:
  credentialmate:
    BLOCK_AND_ASK:
      - "ralph/hipaa_*.py"
    SECURITY_REVIEW:
      - "**/models/patient*.py"

  karematch:
    BLOCK_AND_ASK:
      - ".claude/golden-paths.json"
```

### 10.4 Guardrails

```yaml
# governance/unified/guardrails.yaml

version: "3.0"

forbidden_patterns:
  typescript:
    - pattern: "@ts-ignore"
      message: "Fix the type error instead of ignoring"
    - pattern: "@ts-nocheck"
      message: "Type checking must remain enabled"

  eslint:
    - pattern: "eslint-disable"
      message: "Fix the lint error instead of disabling"

  testing:
    - pattern: ".skip("
      message: "Do not skip tests"
    - pattern: ".only("
      message: "Do not focus tests"

  git:
    - pattern: "--no-verify"
      message: "Never bypass pre-commit hooks"

behavioral_rules:
  advisors:
    - rule: "no_implementation"
      message: "Advisors cannot implement, only advise"
    - rule: "must_document"
      message: "All decisions must have ADR"

  coordinator:
    - rule: "no_code_changes"
      message: "Coordinator orchestrates, doesn't code"
    - rule: "must_update_project_hq"
      message: "Every action must update PROJECT_HQ"

hipaa_rules:
  enabled_for: [credentialmate]
  patterns:
    - pattern: "patient"
      context: "hardcoded string"
      message: "No hardcoded PHI"
```

---

## 11. Recovery & Error Handling

### 11.1 Recovery Protocols

```yaml
recovery_protocols:
  project_hq_corrupted:
    detection: "Parse error or missing required sections"
    steps:
      - Attempt auto-repair from git history
      - If fails, rebuild from events log
      - If fails, create fresh from template
      - Alert human if unrecoverable

  work_queue_corrupted:
    detection: "JSON parse error or invalid schema"
    steps:
      - Rebuild from completed tasks in git
      - Mark in-progress tasks as pending
      - Resume from clean state
      - Log recovery event

  adr_index_stale:
    detection: "Index missing recent ADRs"
    steps:
      - Scan decisions/ folder
      - Regenerate index from ADR files
      - Log rebuild event

  event_log_gap:
    detection: "Missing sequence numbers"
    steps:
      - Note gap in metrics.json
      - Continue logging from current point
      - Do not fabricate missing events

  session_interrupted:
    detection: "No handoff for previous session"
    steps:
      - Read work_queue.json for current state
      - Read PROJECT_HQ.md for context
      - Resume from last known state
      - Note gap in session history
```

### 11.2 Graceful Degradation

```yaml
degradation_modes:
  advisor_unavailable:
    fallback: "Escalate to human"
    message: "Advisor consultation failed. Please provide guidance."

  coordinator_overloaded:
    threshold: "Queue > 50 tasks"
    fallback: "Pause new ADR processing"
    message: "Task queue full. Complete existing tasks first."

  builder_repeated_failure:
    threshold: "3 consecutive BLOCKED"
    fallback: "Pause task, add to blockers"
    message: "Multiple failures. Human review required."

  ralph_unavailable:
    fallback: "Block all commits"
    message: "Verification unavailable. Cannot proceed."
```

---

## 12. Implementation Plan

### 12.1 Phase Summary

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| 1 | Foundation | AI-Team-Plans structure, PROJECT_HQ template, event logging skeleton |
| 2 | Coordinator | Coordinator agent, task breakdown, work queue, auto-status |
| 3 | Advisors | All 3 Advisors, ADR automation, conditional autonomy |
| 4 | Integration | End-to-end testing, 5+ file escalation, phase retrospectives |
| 5 | Deployment | Deploy to CredentialMate, then KareMatch |
| 6 | Polish | Documentation, edge cases, threshold tuning |

### 12.2 Phase 1: Foundation

**Tasks**:
1. Create `AI-Team-Plans/` folder structure in AI_Orchestrator
2. Create PROJECT_HQ.md template
3. Create ADR template with tags
4. Create decisions/index.md template
5. Create event logging skeleton (EventLogger class)
6. Create metrics.json schema
7. Create bootstrap script

**Validation**:
- [ ] Folder structure matches spec
- [ ] Templates render correctly
- [ ] Event logging captures test events

### 12.3 Phase 2: Coordinator

**Tasks**:
1. Create BaseCoordinator class
2. Implement ADR parsing and task breakdown
3. Implement work_queue.json management
4. Implement PROJECT_HQ auto-updates
5. Implement session handoff generation
6. Implement phase detection logic

**Validation**:
- [ ] Coordinator breaks ADR into correct tasks
- [ ] Tasks assigned to correct Builder type
- [ ] PROJECT_HQ updates automatically
- [ ] Handoffs generated on session end

### 12.4 Phase 3: Advisors

**Tasks**:
1. Create BaseAdvisor class
2. Implement Data Advisor
3. Implement App Advisor
4. Implement UI/UX Advisor
5. Implement confidence scoring
6. Implement ADR alignment checking
7. Implement ADR index auto-update

**Validation**:
- [ ] Advisors respond to explicit invocation
- [ ] Auto-decide when ADR-aligned + confident
- [ ] Escalate when required
- [ ] ADRs created with proper tags

### 12.5 Phase 4: Integration

**Tasks**:
1. Implement 5+ file scope escalation
2. Connect Coordinator → Advisor escalation
3. Implement phase completion triggers
4. Implement retrospective generation
5. End-to-end workflow testing

**Validation**:
- [ ] Full workflow runs without manual intervention
- [ ] 5+ file escalation triggers Advisor
- [ ] Retrospectives auto-generate at phase end

### 12.6 Phase 5: Deployment

**Tasks**:
1. Deploy to CredentialMate
2. Add HIPAA extensions
3. Deploy to KareMatch
4. Add healthcare extensions
5. Cross-repo validation

**Validation**:
- [ ] Works in CredentialMate
- [ ] HIPAA guardrails enforced
- [ ] Works in KareMatch
- [ ] No governance conflicts

### 12.7 Phase 6: Polish

**Tasks**:
1. Documentation
2. Edge case handling
3. Threshold tuning based on usage
4. User feedback integration

---

## 13. Success Metrics

### 13.1 Quantitative Targets

| Metric | Current | Target |
|--------|---------|--------|
| Human interventions per session | ~10 | ≤3 |
| Advisor auto-decision rate | N/A | ≥70% |
| Task iteration efficiency | ~15 avg | ≤8 avg |
| Event coverage | 0% | 100% |
| Retrospective auto-generation | 0% | 100% |

### 13.2 Qualitative Targets

| Metric | Target |
|--------|--------|
| Decision traceability | 100% traceable to ADR + event |
| Hallucination incidents | 0 |
| Governance compliance | 100% violations caught |

---

## 14. Appendices

### 14.1 Glossary

| Term | Definition |
|------|------------|
| **ADR** | Architecture Decision Record - immutable document capturing a decision |
| **Advisor** | L3 agent that analyzes and recommends (user-invoked) |
| **Builder** | L1/L2 agent that writes code (Coordinator-assigned) |
| **Coordinator** | L2.5 agent that orchestrates tasks and status |
| **Grounding** | Linking agent decisions to verifiable external sources |
| **Phase** | Logical grouping of tasks with completion triggers |
| **PROJECT_HQ** | Single source of truth for project status |
| **Ralph** | Verification engine (PASS/FAIL/BLOCKED) |
| **Retrospective** | Post-phase analysis generated automatically |
| **Wiggum** | Iteration control (15-50 retries per agent type) |

### 14.2 File References

**Core Governance**:
- `governance/contracts/advisor.yaml`
- `governance/contracts/coordinator.yaml`
- `governance/unified/golden-paths.yaml`
- `governance/unified/guardrails.yaml`

**AI-Team-Plans Templates**:
- `AI-Team-Plans/PROJECT_HQ.md`
- `AI-Team-Plans/decisions/ADR-TEMPLATE.md`
- `AI-Team-Plans/decisions/index.md`
- `AI-Team-Plans/tasks/work_queue.json`
- `AI-Team-Plans/events/metrics.json`
- `AI-Team-Plans/retrospectives/patterns.json`

### 14.3 Superseded Documents

This v3 specification supersedes:
- `00-OVERVIEW.md`
- `01-CURRENT-STATE.md`
- `02-ARCHITECTURE.md`
- `03-ADVISOR-AGENTS.md`
- `04-COORDINATOR-AGENT.md`
- `05-GOVERNANCE-OVERHAUL.md`
- `06-IMPLEMENTATION-PLAN.md`
- `07-HIERARCHICAL-ORCHESTRATION-V2.md`
- `PROJECT-HQ-TEMPLATE.md`

These files remain for historical reference but `AI-TEAM-SPEC-V3.md` is the authoritative source.

---

**Document Version**: 3.0
**Last Updated**: 2026-01-09
**Next Review**: After Phase 1 implementation
