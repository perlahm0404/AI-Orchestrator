# AI Team Hierarchical Orchestration v2

**Date**: 2026-01-09
**Author**: Claude Opus 4.5
**Status**: Design Phase
**Version**: 2.0

---

## Executive Summary

This document extends the AI Team architecture with **CrewAI-like hierarchical patterns**, **enhanced observability**, and **autonomous Advisor decision-making**. It synthesizes industry research from LangGraph, CrewAI, AutoGen, and production observability systems to create a governance-aware multi-agent system.

### Key Enhancements in v2

| Feature | v1 (Current Design) | v2 (This Document) |
|---------|---------------------|---------------------|
| **Advisor Decisions** | Always wait for human | Autonomous if aligned with ADR |
| **Escalation Trigger** | Only on BLOCKED | Also on 5+ files touched |
| **Event Logging** | Not specified | Detailed + counts hybrid |
| **Retrospectives** | Session-based | Phase-based (real-time) |
| **Artifact Location** | Scattered | Unified `AI-Team-Plans/` folder |
| **Agent-to-Agent Advice** | Not specified | Advisors serve agents too |

---

## Table of Contents

1. [Industry Research Summary](#1-industry-research-summary)
2. [Hierarchical Agent Architecture](#2-hierarchical-agent-architecture)
3. [AI-Team-Plans Folder Structure](#3-ai-team-plans-folder-structure)
4. [Advisor Autonomous Decision Flow](#4-advisor-autonomous-decision-flow)
5. [Coordinator Orchestration Patterns](#5-coordinator-orchestration-patterns)
6. [Event Logging & Observability](#6-event-logging--observability)
7. [Phase-Based Retrospectives](#7-phase-based-retrospectives)
8. [Auto-Escalation System](#8-auto-escalation-system)
9. [Agent Contracts](#9-agent-contracts)
10. [Implementation Integration](#10-implementation-integration)
11. [Success Metrics](#11-success-metrics)

---

## 1. Industry Research Summary

### 1.1 Sources Analyzed

| Framework/Tool | Key Pattern | Source |
|----------------|-------------|--------|
| **LangGraph** | Graph-based state machine orchestration | [LangChain](https://www.langchain.com/langgraph) |
| **CrewAI** | Manager → Specialist hierarchical delegation | [CrewAI Docs](https://docs.crewai.com/en/concepts/crews) |
| **AutoGen** | Conversation-based multi-agent coordination | [Microsoft AutoGen](https://github.com/microsoft/autogen) |
| **Swarms** | Director → Worker enterprise orchestration | [Swarms GitHub](https://github.com/kyegomez/swarms) |
| **Agent Squad** | Supervisor → Teams with nesting | [AWS Agent Squad](https://github.com/awslabs/agent-squad) |
| **LangSmith** | Agent observability & tracing | [LangSmith](https://www.langchain.com/langsmith/observability) |
| **Langfuse** | Event logging & metrics dashboards | [Langfuse](https://langfuse.com/docs/observability/overview) |
| **OpenTelemetry** | AI agent observability standards | [OpenTelemetry AI](https://opentelemetry.io/blog/2025/ai-agent-observability/) |

### 1.2 Key Industry Patterns Adopted

#### Pattern 1: Hierarchical Delegation (CrewAI)

From [CrewAI Hierarchical Guide](https://activewizards.com/blog/hierarchical-ai-agents-a-guide-to-crewai-delegation):

> "The Manager Agent acts as the orchestrator, responsible for delegating tasks and validating outputs. Meanwhile, Specialist Agents are designed for specific roles."

**Our Mapping**: Coordinator = Manager, Advisors = Strategic Specialists, Builders = Execution Specialists

#### Pattern 2: Event-Driven State (Confluent/AWS)

From [Confluent Event-Driven Multi-Agent](https://www.confluent.io/blog/event-driven-multi-agent-systems/):

> "Every event or command an agent processes is recorded in an immutable log... Acting as a single source of truth, the log ensures all agents operate with the same context."

**Our Mapping**: `AI-Team-Plans/events/` folder with immutable event logs

#### Pattern 3: Confidence-Based Escalation (Industry Standard)

From [Permit.io HITL Guide](https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo):

> "Human intervention is triggered by predefined thresholds... if confidence falls below a certain percentage (e.g., 85%)."

**Our Mapping**: Advisors auto-decide when confident + aligned, escalate when uncertain

#### Pattern 4: Grounding = Anti-Hallucination (RAG)

From [InfoWorld](https://www.infoworld.com/article/3822251/how-to-keep-ai-hallucinations-out-of-your-code.html):

> "RAG, in which the model uses one or more designated 'sources of truth' that contain code either specific to the user or at least vetted by them."

**Our Mapping**: `AI-Team-Plans/` folder IS the grounding source. Agents read specs, ADRs, PROJECT_HQ—not their own "memory."

#### Pattern 5: Observability is Table Stakes (89% Adoption)

From [LangChain State of Agents](https://www.langchain.com/state-of-agent-engineering):

> "89% of organizations have implemented some form of observability for their agents, and 62% have detailed tracing."

**Our Mapping**: Hybrid approach—detailed logs for significant events, JSON counts for everything else.

#### Pattern 6: Continuous Learning Flywheel

From [OpenAI Self-Evolving Agents](https://cookbook.openai.com/examples/partners/self_evolving_agents/autonomous_agent_retraining):

> "A repeatable retraining loop that captures issues, learns from feedback, and promotes improvements back into production."

**Our Mapping**: Phase-based retrospectives with `patterns.json` aggregation.

### 1.3 Why Build on Existing System vs. Adopt Framework

From [Lyzr Comparison](https://www.lyzr.ai/blog/top-open-source-agentic-frameworks/):

> "All three top open source agentic frameworks are exceptional at prototyping, but dangerously incomplete for production... the cost isn't in the code; it's in the security, governance, and deployment layer you have to custom-build."

**Decision**: Our AI Orchestrator already has governance (contracts, Ralph, guardrails), security (kill-switch, golden paths), and deployment (autonomous_loop, session handoffs). Extend rather than replace.

---

## 2. Hierarchical Agent Architecture

### 2.1 Three-Tier Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TIER 1: ADVISORS                                  │
│                         (Dialogue + Conditional Autonomy)                   │
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
│                         (Autonomous Orchestration)                          │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                         Coordinator Agent                            │  │
│   │                                                                      │  │
│   │  • Reads approved ADRs                                               │  │
│   │  • Breaks decisions into tasks                                       │  │
│   │  • Manages work_queue.json                                           │  │
│   │  • Assigns tasks to Builders                                         │  │
│   │  • Auto-updates PROJECT_HQ.md                                        │  │
│   │  • Creates session handoffs                                          │  │
│   │  • Triggers Advisors on 5+ file escalation                           │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                 │                                           │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                           TIER 3: BUILDERS                                  │
│                         (Autonomous Execution)                              │
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
| Data Advisor | Dialogue + Conditional | L3 | ❌ No | ✅ If ADR-aligned | ❌ No |
| App Advisor | Dialogue + Conditional | L3 | ❌ No | ✅ If ADR-aligned | ❌ No |
| UI/UX Advisor | Dialogue + Conditional | L3 | ❌ No | ✅ If ADR-aligned | ❌ No |
| Coordinator | Autonomous | L2.5 | ❌ No | ✅ Orchestration only | ❌ No |
| FeatureBuilder | Autonomous | L1 | ✅ Yes | ❌ No | ✅ At PR |
| BugFixer | Autonomous | L2 | ✅ Yes | ❌ No | ✅ Every commit |
| TestWriter | Autonomous | L1 | ✅ Yes | ❌ No | ✅ At PR |
| CodeQuality | Autonomous | L2 | ✅ Yes | ❌ No | ✅ Every commit |

### 2.3 Information Flow

```
Human describes problem/feature
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ ADVISOR PHASE (Dialogue + Conditional Autonomy)             │
│                                                             │
│  1. Advisor detects domain (data/app/uiux)                  │
│  2. Gathers codebase context                                │
│  3. Checks existing ADRs for prior decisions                │
│  4. Decision point:                                         │
│     ├─→ Aligns with ADR + confident → AUTO-PROCEED         │
│     ├─→ Conflicts with ADR → ESCALATE to human             │
│     ├─→ No ADR + strategic → ESCALATE to human             │
│     └─→ No ADR + tactical → AUTO-DECIDE + draft ADR        │
│  5. Documents decision in ADR                               │
│  6. Updates PROJECT_HQ.md roadmap                           │
│  7. Notifies Coordinator                                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ COORDINATOR PHASE (Autonomous Orchestration)                │
│                                                             │
│  1. Detects new ADR approval                                │
│  2. Parses ADR implementation notes                         │
│  3. Breaks into tasks with dependencies                     │
│  4. Adds to work_queue.json                                 │
│  5. Assigns first ready task to Builder                     │
│  6. Updates PROJECT_HQ.md status                            │
│  7. Logs event to events/                                   │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ BUILDER PHASE (Autonomous Execution)                        │
│                                                             │
│  1. Receives task from Coordinator                          │
│  2. Consults Knowledge Objects                              │
│  3. Executes with Wiggum iteration control (15-50 retries)  │
│  4. Ralph verification (PASS/FAIL/BLOCKED)                  │
│  5. On PASS → Task complete, notify Coordinator             │
│  6. On FAIL (regression) → Retry within budget              │
│  7. On BLOCKED → Escalate to human (R/O/A)                  │
│  8. Coordinator assigns next task                           │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE COMPLETE → RETROSPECTIVE (Auto-triggered)             │
│                                                             │
│  1. Coordinator detects phase milestone                     │
│  2. Generates retrospective document                        │
│  3. Captures: worked well, didn't work, barriers, changes   │
│  4. Updates patterns.json with learnings                    │
│  5. Logs to events/                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. AI-Team-Plans Folder Structure

### 3.1 Location

Each target repository contains its own `AI-Team-Plans/` folder:

```
credentialmate/AI-Team-Plans/    # CredentialMate instance
karematch/AI-Team-Plans/         # KareMatch instance
```

### 3.2 Complete Structure

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
│   └── ADR-003-api-structure.md
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
│   │   ├── 2026-01-09-002-coordinator-assigned.md
│   │   └── 2026-01-09-003-builder-completed.md
│   ├── metrics.json                 # Aggregated counts (all-time)
│   └── archive/                     # Compressed old events
│
└── retrospectives/                  # Phase learnings (permanent)
    ├── PROJ-001-phase-1.md
    ├── PROJ-001-phase-2.md
    └── patterns.json                # Aggregated learnings
```

### 3.3 File Lifecycle Management

| File Type | Lifecycle | Git Strategy | Archive Policy |
|-----------|-----------|--------------|----------------|
| `PROJECT_HQ.md` | Living (auto-updated) | ✅ Always commit | Never archive |
| `specs/*.md` | Living (human-edited) | ✅ Always commit | Never archive |
| `decisions/ADR-*.md` | Immutable once approved | ✅ Always commit | Never archive |
| `tasks/work_queue.json` | Living (Coordinator) | ✅ Always commit | Never archive |
| `sessions/*.md` | Archivable | ✅ Commit | Archive after 30 days |
| `events/current/*.md` | Ephemeral | ⚠️ Optional commit | Archive after 7 days |
| `events/metrics.json` | Rolling | ✅ Always commit | Daily rollup |
| `retrospectives/*.md` | Permanent | ✅ Always commit | Never archive |
| `retrospectives/patterns.json` | Living | ✅ Always commit | Never archive |

### 3.4 Anti-Hallucination Strategy

**Problem**: Agents can "remember" things that didn't happen or misinterpret prior decisions.

**Solution**: All agent memory is externalized to files. Agents MUST read canonical sources.

```python
# CORRECT: Agent reads from source of truth
def advisor_make_decision(context):
    # 1. Read existing ADRs (not from memory)
    adrs = read_all_adrs("AI-Team-Plans/decisions/")

    # 2. Read PROJECT_HQ for current state (not from memory)
    project_hq = read_file("AI-Team-Plans/PROJECT_HQ.md")

    # 3. Read specs for requirements (not from memory)
    spec = read_file(f"AI-Team-Plans/specs/{context.spec_file}")

    # 4. Make decision based on EXTERNAL sources
    decision = analyze(adrs, project_hq, spec, context)

    # 5. Document decision (creates external record)
    write_adr(decision)

    return decision

# WRONG: Agent relies on its own "memory"
def advisor_make_decision_bad(context):
    # BAD: "I remember we decided to use PostgreSQL"
    # This could be hallucinated or from a different project
    return {"database": "postgresql"}  # No external verification
```

**Grounding Rules**:

1. **Specs are canonical** - If it's not in `specs/`, the requirement doesn't exist
2. **ADRs are immutable** - Once approved, decisions cannot change (create new ADR to supersede)
3. **PROJECT_HQ is current state** - Always read before acting
4. **Events are evidence** - What happened is logged, not remembered
5. **Agents don't trust themselves** - Always verify against files

---

## 4. Advisor Autonomous Decision Flow

### 4.1 Key Change from v1

**v1 (Current)**: Advisors ALWAYS wait for human decision

**v2 (New)**: Advisors can decide autonomously when:
- Decision aligns with existing ADRs
- Decision is tactical (not strategic)
- Confidence is above threshold (85%)

### 4.2 Decision Flow Algorithm

```python
def advisor_should_escalate(context: AdvisorContext) -> Tuple[bool, str]:
    """
    Determines if Advisor should escalate to human or decide autonomously.

    Returns:
        (should_escalate: bool, reason: str)
    """

    # ══════════════════════════════════════════════════════════════════
    # PHASE 1: HARD ESCALATION TRIGGERS (Always escalate)
    # ══════════════════════════════════════════════════════════════════

    # 1.1 Check for ADR conflicts
    existing_adr = find_relevant_adr(context.domain, context.topic)
    if existing_adr and conflicts_with(context.proposed_decision, existing_adr):
        return True, "ADR_CONFLICT"

    # 1.2 Check defined strategic domains (always need human)
    STRATEGIC_DOMAINS = [
        "security",           # Auth, encryption, access control
        "external_dependency", # New npm/pip packages, APIs
        "data_schema",        # Database migrations, model changes
        "infrastructure",     # Docker, cloud resources, CI/CD
        "compliance",         # HIPAA, GDPR, legal requirements
        "cost",               # Paid services, resource scaling
    ]
    if context.touches_domain(STRATEGIC_DOMAINS):
        return True, "STRATEGIC_DOMAIN"

    # 1.3 Check file count trigger (5+ files = escalate)
    if context.estimated_files_touched > 5:
        return True, "SCOPE_ESCALATION"

    # ══════════════════════════════════════════════════════════════════
    # PHASE 2: ADR ALIGNMENT CHECK (May proceed autonomously)
    # ══════════════════════════════════════════════════════════════════

    if existing_adr and aligns_with(context.proposed_decision, existing_adr):
        # Decision follows established pattern
        if context.confidence >= 0.85:
            return False, "ADR_ALIGNED"
        else:
            return True, "LOW_CONFIDENCE"

    # ══════════════════════════════════════════════════════════════════
    # PHASE 3: TACTICAL VS STRATEGIC (No existing ADR)
    # ══════════════════════════════════════════════════════════════════

    # Tactical decisions (can auto-decide)
    TACTICAL_PATTERNS = [
        "naming_convention",      # Variable/function names
        "code_organization",      # File structure within module
        "error_message_wording",  # User-facing text
        "test_structure",         # How tests are organized
        "logging_format",         # Log message format
    ]

    if context.decision_type in TACTICAL_PATTERNS:
        if context.confidence >= 0.85:
            return False, "TACTICAL_AUTO_DECIDE"
        else:
            return True, "LOW_CONFIDENCE"

    # ══════════════════════════════════════════════════════════════════
    # PHASE 4: DEFAULT (Escalate if uncertain)
    # ══════════════════════════════════════════════════════════════════

    return True, "UNCERTAIN"
```

### 4.3 Decision Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ADVISOR DECISION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Check for ADR conflicts      │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │   CONFLICT    │               │  NO CONFLICT  │
            │   detected    │               │   or no ADR   │
            └───────┬───────┘               └───────┬───────┘
                    │                               │
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────────────────┐
            │   ESCALATE    │               │ Check strategic domains   │
            │   to human    │               │ (security, schema, etc.)  │
            └───────────────┘               └─────────────┬─────────────┘
                                                          │
                                            ┌─────────────┴─────────────┐
                                            │                           │
                                            ▼                           ▼
                                    ┌───────────────┐           ┌───────────────┐
                                    │   STRATEGIC   │           │  NOT STRATEGIC│
                                    │   domain      │           │               │
                                    └───────┬───────┘           └───────┬───────┘
                                            │                           │
                                            ▼                           ▼
                                    ┌───────────────┐           ┌───────────────────────────┐
                                    │   ESCALATE    │           │ Check file count (>5?)    │
                                    │   to human    │           └─────────────┬─────────────┘
                                    └───────────────┘                         │
                                                                ┌─────────────┴─────────────┐
                                                                │                           │
                                                                ▼                           ▼
                                                        ┌───────────────┐           ┌───────────────┐
                                                        │    >5 FILES   │           │   ≤5 FILES    │
                                                        └───────┬───────┘           └───────┬───────┘
                                                                │                           │
                                                                ▼                           ▼
                                                        ┌───────────────┐           ┌───────────────────────────┐
                                                        │   ESCALATE    │           │ Check ADR alignment       │
                                                        │   to human    │           └─────────────┬─────────────┘
                                                        └───────────────┘                         │
                                                                                    ┌─────────────┴─────────────┐
                                                                                    │                           │
                                                                                    ▼                           ▼
                                                                            ┌───────────────┐           ┌───────────────┐
                                                                            │ ADR ALIGNED   │           │ NO ADR        │
                                                                            │ + conf ≥85%   │           │ + tactical    │
                                                                            └───────┬───────┘           │ + conf ≥85%   │
                                                                                    │                   └───────┬───────┘
                                                                                    ▼                           │
                                                                            ┌───────────────┐                   │
                                                                            │ AUTO-PROCEED  │◄──────────────────┘
                                                                            │ Log decision  │
                                                                            │ Update ADR    │
                                                                            └───────────────┘
```

### 4.4 Advisor-to-Agent Communication

**Key Innovation**: Advisors can serve other agents, not just humans.

When a Builder agent encounters ambiguity during execution:

```python
def builder_handle_ambiguity(context: BuilderContext):
    """
    Builder encounters ambiguity → Can request Advisor help
    """

    # 1. Check for existing ADR that covers this case
    adr = find_relevant_adr(context.domain, context.question)
    if adr:
        # Follow existing decision (no Advisor needed)
        return apply_adr_guidance(adr)

    # 2. No ADR → Request Advisor consultation
    advisor_request = AdvisorRequest(
        requester="builder",
        requester_type="agent",  # Not human
        domain=context.domain,
        question=context.question,
        context=context.to_dict()
    )

    # 3. Advisor processes request
    advisor = get_advisor(context.domain)
    response = advisor.consult(advisor_request)

    # 4. If Advisor can decide autonomously → proceed
    if not response.requires_human:
        # Advisor decided based on existing patterns
        log_event("ADVISOR_AGENT_CONSULTATION", {
            "requester": "builder",
            "advisor": advisor.name,
            "decision": response.decision,
            "confidence": response.confidence,
            "adr_created": response.adr_id
        })
        return response.guidance

    # 5. If Advisor needs human → escalate the whole chain
    else:
        return escalate_to_human(
            original_context=context,
            advisor_analysis=response.analysis,
            options=response.options
        )
```

### 4.5 Advisor Contract (v2)

```yaml
# governance/contracts/advisor.yaml

name: advisor
version: "2.0"
mode: conditional_dialogue    # NEW: Not always dialogue
autonomy_level: L3

# ════════════════════════════════════════════════════════════════════
# DECISION AUTONOMY (New in v2)
# ════════════════════════════════════════════════════════════════════

autonomous_decision_rules:
  # Can decide autonomously when:
  can_auto_decide:
    - adr_aligned: true
    - confidence_threshold: 0.85
    - domain_type: tactical
    - max_files_touched: 5

  # Must escalate to human when:
  must_escalate:
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

# ════════════════════════════════════════════════════════════════════
# ALLOWED/FORBIDDEN ACTIONS
# ════════════════════════════════════════════════════════════════════

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

# ════════════════════════════════════════════════════════════════════
# BEHAVIORS
# ════════════════════════════════════════════════════════════════════

behaviors:
  # Option presentation (when escalating)
  must_present_options: true
  min_options: 2
  max_options: 4
  must_explain_tradeoffs: true

  # Decision documentation (always)
  must_document_decision: true
  adr_required_for_autonomous: true
  log_all_decisions: true

  # Communication
  plain_language_required: true
  no_jargon: true

# ════════════════════════════════════════════════════════════════════
# LIMITS
# ════════════════════════════════════════════════════════════════════

limits:
  max_iterations: 5              # Quick analysis
  max_analysis_time_seconds: 300 # 5 minutes max
  max_files_to_analyze: 50

# ════════════════════════════════════════════════════════════════════
# HALT CONDITIONS
# ════════════════════════════════════════════════════════════════════

halt_conditions:
  - confidence_below_threshold_and_no_escalation
  - adr_conflict_not_resolved
  - strategic_decision_attempted_autonomously

on_violation: halt
```

---

## 5. Coordinator Orchestration Patterns

### 5.1 Coordinator Role

The Coordinator is the **orchestration hub** that:
1. Watches for ADR approvals
2. Breaks decisions into executable tasks
3. Manages the work queue
4. Assigns tasks to appropriate Builders
5. Tracks progress in PROJECT_HQ.md
6. Creates session handoffs
7. **NEW: Triggers Advisors on 5+ file escalation**

### 5.2 Coordinator State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COORDINATOR STATE MACHINE                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │      IDLE        │◄────────────────────────────────────┐
    │                  │                                     │
    │ Waiting for      │                                     │
    │ events           │                                     │
    └────────┬─────────┘                                     │
             │                                               │
             │ Event received                                │
             ▼                                               │
    ┌────────────────────────────────────────────┐          │
    │           EVENT DISPATCHER                  │          │
    └────────────────────────────────────────────┘          │
             │                                               │
    ┌────────┼────────┬────────────┬────────────┐          │
    │        │        │            │            │          │
    ▼        ▼        ▼            ▼            ▼          │
┌───────┐┌───────┐┌───────┐┌──────────┐┌──────────┐       │
│ADR    ││TASK   ││TASK   ││SESSION   ││5+ FILE   │       │
│APPROVED││COMPLETE││BLOCKED││END      ││ESCALATION│       │
└───┬───┘└───┬───┘└───┬───┘└────┬─────┘└────┬─────┘       │
    │        │        │         │           │              │
    ▼        ▼        ▼         ▼           ▼              │
┌───────┐┌───────┐┌───────┐┌──────────┐┌──────────┐       │
│Break  ││Check  ││Add to ││Create    ││Trigger   │       │
│into   ││deps,  ││PROJECT││handoff,  ││Advisor,  │       │
│tasks  ││assign ││_HQ    ││update    ││wait for  │       │
│       ││next   ││blockers││stats    ││decision  │       │
└───┬───┘└───┬───┘└───┬───┘└────┬─────┘└────┬─────┘       │
    │        │        │         │           │              │
    └────────┴────────┴─────────┴───────────┘              │
                      │                                     │
                      ▼                                     │
             ┌────────────────┐                             │
             │ Update         │                             │
             │ PROJECT_HQ.md  │                             │
             │ Log event      │                             │
             └────────┬───────┘                             │
                      │                                     │
                      └─────────────────────────────────────┘
```

### 5.3 Task Breakdown Strategy

```python
def coordinator_break_into_tasks(adr: ADR) -> List[Task]:
    """
    Breaks an approved ADR into executable tasks.
    """

    tasks = []

    # 1. Parse implementation notes from ADR
    impl_notes = adr.implementation_notes

    # 2. Identify task types needed
    if impl_notes.has_schema_changes:
        tasks.append(Task(
            type="migration",
            agent="manual",  # Humans do migrations
            priority="P0",
            description="Create database migration"
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

    # 3. Always add test task
    tasks.append(Task(
        type="test",
        agent="TestWriter",
        priority="P3",
        description=f"Write tests for {adr.title}",
        dependencies=[t.id for t in tasks if t.agent != "manual"]
    ))

    # 4. Assign IDs based on ADR
    for i, task in enumerate(tasks):
        task.id = f"TASK-{adr.number}-{i+1:03d}"
        task.adr = adr.id

    return tasks
```

### 5.4 5+ File Escalation Handler

```python
def coordinator_handle_scope_escalation(
    task: Task,
    builder_analysis: Dict
) -> EscalationResult:
    """
    When a Builder reports 5+ files will be touched,
    Coordinator triggers Advisor intervention.
    """

    # 1. Log the escalation event
    log_event("SCOPE_ESCALATION", {
        "task_id": task.id,
        "estimated_files": builder_analysis.files_to_touch,
        "reason": "Exceeds 5-file threshold"
    })

    # 2. Determine which Advisor to invoke
    advisor_type = infer_advisor_type(task.description)
    advisor = get_advisor(advisor_type)

    # 3. Request Advisor analysis
    analysis_request = AdvisorRequest(
        requester="coordinator",
        requester_type="agent",
        task=task,
        builder_analysis=builder_analysis,
        question="Should this task be broken into smaller pieces?"
    )

    response = advisor.consult(analysis_request)

    # 4. Handle Advisor response
    if response.recommendation == "SPLIT_TASK":
        # Advisor suggests splitting
        new_tasks = response.suggested_tasks

        # Replace original task with subtasks
        remove_task(task.id)
        for new_task in new_tasks:
            add_task(new_task)

        log_event("TASK_SPLIT", {
            "original_task": task.id,
            "new_tasks": [t.id for t in new_tasks],
            "advisor": advisor.name
        })

        return EscalationResult(
            action="SPLIT",
            new_tasks=new_tasks
        )

    elif response.recommendation == "PROCEED":
        # Advisor says it's fine to proceed
        log_event("SCOPE_APPROVED", {
            "task_id": task.id,
            "advisor": advisor.name,
            "rationale": response.rationale
        })

        return EscalationResult(
            action="PROCEED",
            guidance=response.guidance
        )

    else:  # response.requires_human
        # Advisor needs human decision
        return EscalationResult(
            action="ESCALATE_HUMAN",
            advisor_analysis=response.analysis,
            options=response.options
        )
```

### 5.5 Coordinator Contract

```yaml
# governance/contracts/coordinator.yaml

name: coordinator
version: "2.0"
mode: autonomous
autonomy_level: L2.5

# ════════════════════════════════════════════════════════════════════
# TRIGGERS
# ════════════════════════════════════════════════════════════════════

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

# ════════════════════════════════════════════════════════════════════
# ALLOWED/FORBIDDEN ACTIONS
# ════════════════════════════════════════════════════════════════════

allowed_actions:
  - read_adr
  - read_codebase
  - read_project_hq
  - create_task
  - update_task_status
  - assign_task
  - update_project_hq
  - update_work_queue
  - create_handoff
  - create_retrospective
  - log_event
  - trigger_advisor
  - notify_builder

forbidden_actions:
  - write_code
  - modify_application_files
  - make_architectural_decisions  # That's Advisors' job
  - modify_adr                    # ADRs are immutable
  - bypass_dependencies
  - skip_logging

# ════════════════════════════════════════════════════════════════════
# LIMITS
# ════════════════════════════════════════════════════════════════════

limits:
  max_iterations: 100            # High - manages many sub-tasks
  max_concurrent_tasks: 3
  max_queue_size: 50
  max_tasks_per_adr: 20

# ════════════════════════════════════════════════════════════════════
# AUTO-BEHAVIORS
# ════════════════════════════════════════════════════════════════════

auto_behaviors:
  update_project_hq_on_change: true
  log_all_events: true
  create_handoff_on_session_end: true
  respect_task_dependencies: true
  trigger_retrospective_on_phase: true

# ════════════════════════════════════════════════════════════════════
# HALT CONDITIONS
# ════════════════════════════════════════════════════════════════════

halt_conditions:
  - all_tasks_blocked
  - circular_dependency_detected
  - queue_overflow

on_violation: halt
```

---

## 6. Event Logging & Observability

### 6.1 Design Principles

1. **Significant events logged in detail** (markdown files)
2. **All events counted** (JSON metrics)
3. **Events are immutable** (append-only log)
4. **Events enable debugging** (trace agent decisions)
5. **Events survive sessions** (persistent in repo)

### 6.2 Event Types

| Event Type | Logged Detail | Counted | Trigger |
|------------|---------------|---------|---------|
| `ADVISOR_TRIGGERED` | ✅ Full | ✅ | Advisor activated |
| `ADVISOR_AUTO_DECIDED` | ✅ Full | ✅ | Advisor decided autonomously |
| `ADVISOR_ESCALATED` | ✅ Full | ✅ | Advisor escalated to human |
| `COORDINATOR_TASK_CREATED` | ✅ Full | ✅ | New task from ADR |
| `COORDINATOR_TASK_ASSIGNED` | ❌ Count only | ✅ | Task assigned to Builder |
| `BUILDER_ITERATION` | ❌ Count only | ✅ | Builder iteration (many) |
| `BUILDER_COMPLETED` | ✅ Full | ✅ | Builder finished task |
| `BUILDER_BLOCKED` | ✅ Full | ✅ | Builder hit BLOCKED |
| `RALPH_PASS` | ❌ Count only | ✅ | Ralph PASS verdict |
| `RALPH_FAIL` | ❌ Count only | ✅ | Ralph FAIL verdict |
| `RALPH_BLOCKED` | ✅ Full | ✅ | Ralph BLOCKED verdict |
| `SCOPE_ESCALATION` | ✅ Full | ✅ | 5+ files trigger |
| `PHASE_COMPLETE` | ✅ Full | ✅ | Phase milestone |
| `RETROSPECTIVE_CREATED` | ✅ Full | ✅ | Retro generated |

### 6.3 Detailed Event Format

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
- **Domain**: data (schema-related)
- **Files analyzed**: 3
- **Existing ADRs checked**: ADR-020, ADR-021, ADR-023

## Decision Made
- **Action**: AUTO_PROCEED
- **Reason**: Decision aligns with ADR-023 data model
- **Confidence**: 92%

## Impact
- Task unblocked
- No human intervention required
- ADR-023 guidance applied

## Artifacts Created
- Updated PROJECT_HQ.md status section
- No new ADR (existing ADR sufficient)

## Escalation
- **Escalated**: No
- **Reason**: Confidence above threshold, aligned with existing ADR
```

### 6.4 Metrics JSON Format

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
    "advisor_app": {
      "triggers": 2,
      "auto_decisions": 1,
      "escalations": 1,
      "avg_confidence": 0.82
    },
    "coordinator": {
      "tasks_created": 8,
      "tasks_assigned": 12,
      "handoffs_created": 1,
      "retrospectives_created": 0
    },
    "builder_feature": {
      "iterations": 48,
      "completions": 4,
      "blocks": 1
    },
    "builder_bugfix": {
      "iterations": 22,
      "completions": 3,
      "blocks": 0
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
  },

  "phase_progress": {
    "current_phase": 2,
    "tasks_in_phase": 8,
    "tasks_completed": 5,
    "tasks_blocked": 1,
    "tasks_pending": 2
  }
}
```

### 6.5 Event Logging Implementation

```python
# orchestration/event_logger.py

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

@dataclass
class Event:
    type: str
    agent: str
    timestamp: datetime
    context: dict
    decision: dict = None
    impact: dict = None
    escalated: bool = False
    escalation_reason: str = None

class EventLogger:
    def __init__(self, project_root: Path):
        self.events_dir = project_root / "AI-Team-Plans" / "events"
        self.current_dir = self.events_dir / "current"
        self.metrics_file = self.events_dir / "metrics.json"

        # Ensure directories exist
        self.current_dir.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: Event):
        """Log an event - detail file if significant, always count."""

        # 1. Always update metrics (count)
        self._update_metrics(event)

        # 2. Create detailed log if significant
        if self._is_significant(event):
            self._write_detail_log(event)

    def _is_significant(self, event: Event) -> bool:
        """Determine if event warrants detailed logging."""
        SIGNIFICANT_TYPES = [
            "ADVISOR_TRIGGERED",
            "ADVISOR_AUTO_DECIDED",
            "ADVISOR_ESCALATED",
            "COORDINATOR_TASK_CREATED",
            "BUILDER_COMPLETED",
            "BUILDER_BLOCKED",
            "RALPH_BLOCKED",
            "SCOPE_ESCALATION",
            "PHASE_COMPLETE",
            "RETROSPECTIVE_CREATED"
        ]
        return event.type in SIGNIFICANT_TYPES

    def _write_detail_log(self, event: Event):
        """Write detailed markdown event file."""
        date_str = event.timestamp.strftime("%Y-%m-%d")

        # Get next sequence number for today
        existing = list(self.current_dir.glob(f"{date_str}-*.md"))
        seq = len(existing) + 1

        filename = f"{date_str}-{seq:03d}-{event.type.lower()}.md"
        filepath = self.current_dir / filename

        content = self._format_event_markdown(event)
        filepath.write_text(content)

    def _update_metrics(self, event: Event):
        """Update metrics.json with event count."""
        metrics = self._load_metrics()

        # Update totals
        metrics["totals"]["events_total"] += 1
        if self._is_significant(event):
            metrics["totals"]["events_logged_detail"] += 1
        else:
            metrics["totals"]["events_counted_only"] += 1

        # Update by-agent counts
        agent_key = event.agent.lower().replace(" ", "_")
        if agent_key not in metrics["by_agent"]:
            metrics["by_agent"][agent_key] = {}

        event_key = event.type.lower()
        metrics["by_agent"][agent_key][event_key] = \
            metrics["by_agent"][agent_key].get(event_key, 0) + 1

        # Update escalation counts
        if event.escalated:
            metrics["escalations"]["to_human"] += 1

        self._save_metrics(metrics)

    def _format_event_markdown(self, event: Event) -> str:
        """Format event as markdown."""
        return f"""# EVENT-{event.timestamp.strftime("%Y-%m-%d-%H%M%S")}

**Timestamp**: {event.timestamp.isoformat()}Z
**Type**: {event.type}
**Agent**: {event.agent}

## Context
{json.dumps(event.context, indent=2)}

## Decision Made
{json.dumps(event.decision, indent=2) if event.decision else "N/A"}

## Impact
{json.dumps(event.impact, indent=2) if event.impact else "N/A"}

## Escalation
- **Escalated**: {"Yes" if event.escalated else "No"}
- **Reason**: {event.escalation_reason or "N/A"}
"""
```

---

## 7. Phase-Based Retrospectives

### 7.1 Design Principles

1. **Triggered at phase completion** (not arbitrary time intervals)
2. **Generated while fresh** (context is recent)
3. **Captures actionable learnings** (what to change)
4. **Aggregates patterns** (patterns.json for long-term)
5. **Auto-generated by Coordinator** (no manual effort)

### 7.2 Phase Definition

Phases are defined in specs and tracked in PROJECT_HQ.md:

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
    completion_criteria:
      - "All migrations applied"
      - "Models pass validation"
      - "API endpoints responding"

  - id: 2
    name: "Business Logic"
    description: "Rules engine implementation"
    tasks:
      - "Implement rule evaluation"
      - "Add condition matching"
      - "Create action handlers"
    completion_criteria:
      - "Rules evaluate correctly"
      - "All test cases pass"
      - "Performance within bounds"
```

### 7.3 Retrospective Template

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
| Ralph PASS | 12 |
| Ralph FAIL | 4 |
| Ralph BLOCKED | 1 |

---

## What Worked Well

- [ ] **Advisor auto-decisions** reduced human interrupts by 75% (6 auto vs 2 manual)
- [ ] **ADR grounding** prevented 2 potential conflicts (referenced ADR-020, ADR-021)
- [ ] **Event logging** caught Builder loop early at iteration 12 (budget was 50)
- [ ] **Scope escalation** triggered correctly when TASK-023-004 touched 7 files

---

## What Didn't Work

- [ ] **Advisor confidence threshold** too high - escalated unnecessarily when confidence was 84% (threshold 85%)
- [ ] **Task TASK-023-003** took 15 iterations (expected 5-8) due to unclear spec
- [ ] **metrics.json** file growing large - needs daily rollup implementation

---

## Barriers Encountered

| Barrier | Task | Resolution |
|---------|------|------------|
| Ralph BLOCKED on test file | TASK-023-005 | Pre-existing failure, human override (O) |
| Spec ambiguity | TASK-023-003 | Advisor clarification, updated spec |
| Missing dependency | TASK-023-006 | Added after ADR-024 approval |

---

## Proposed Changes

| Change | Category | Priority | Rationale |
|--------|----------|----------|-----------|
| Lower confidence threshold to 80% | Governance | P1 | Reduce unnecessary escalations |
| Add daily metrics archival | Infrastructure | P2 | Prevent file bloat |
| Require task estimate in specs | Process | P2 | Better iteration budgeting |
| Add spec validation step | Process | P3 | Catch ambiguity earlier |

---

## Action Items

| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| Update advisor.yaml confidence_threshold | Governance | Phase 2 start | Pending |
| Implement metrics archival cron | Infrastructure | Phase 2 start | Pending |
| Update spec template with estimates | Human | Before Phase 2 | Pending |

---

## Patterns Identified

### Pattern: "Spec Ambiguity → Iteration Bloat"

**Observation**: Tasks with unclear specs averaged 12 iterations vs 5 for clear specs.

**Detection Rule**: If task iterations > 2x average, check spec clarity.

**Prevention**: Require Advisor review of spec before task creation.

### Pattern: "ADR Alignment → Fast Decisions"

**Observation**: When existing ADR covered the case, decisions were 3x faster.

**Detection Rule**: Track time-to-decision by ADR-alignment status.

**Reinforcement**: Ensure comprehensive ADRs for common patterns.

---

## Phase 2 Recommendations

1. **Review specs before starting** - Have Advisor validate clarity
2. **Monitor iteration counts** - Flag if exceeding 10 early
3. **Lower escalation threshold** - 80% confidence should be sufficient
4. **Archive events daily** - Implement before phase 2 generates more

---

## Linked Artifacts

- **ADRs Created**: ADR-023, ADR-024
- **Events Logged**: 12 detailed, 135 counted
- **Knowledge Objects**: KO-cm-015 (draft)
- **Session Handoffs**: 2026-01-06-001, 2026-01-07-001, 2026-01-08-001, 2026-01-09-001
```

### 7.4 Patterns Aggregation

```json
// retrospectives/patterns.json

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
      "prevention": "Require Advisor spec review before task creation",
      "status": "active"
    },
    {
      "id": "PAT-002",
      "name": "ADR Alignment → Fast Decisions",
      "type": "positive-pattern",
      "discovered_in": "PROJ-001-phase-1",
      "occurrences": 6,
      "detection_rule": "decision.adr_aligned == true",
      "reinforcement": "Create comprehensive ADRs for common patterns",
      "status": "active"
    },
    {
      "id": "PAT-003",
      "name": "5+ File Scope → Needs Splitting",
      "type": "heuristic",
      "discovered_in": "PROJ-001-phase-1",
      "occurrences": 2,
      "detection_rule": "task.estimated_files > 5",
      "action": "Trigger scope escalation to Advisor",
      "status": "active"
    }
  ],

  "thresholds": {
    "confidence_threshold": 0.85,
    "iteration_warning": 10,
    "iteration_budget_default": 20,
    "file_scope_trigger": 5
  },

  "recommendations": [
    {
      "from_phase": "PROJ-001-phase-1",
      "recommendation": "Lower confidence threshold to 80%",
      "status": "pending",
      "priority": "P1"
    }
  ]
}
```

### 7.5 Retrospective Generation Logic

```python
def coordinator_generate_retrospective(phase: Phase) -> Retrospective:
    """
    Auto-generate retrospective when phase completes.
    """

    # 1. Gather metrics for this phase
    metrics = gather_phase_metrics(phase)
    events = get_phase_events(phase)
    tasks = get_phase_tasks(phase)

    # 2. Analyze what worked well
    worked_well = []

    if metrics.auto_decisions > metrics.human_interventions:
        worked_well.append({
            "item": "Advisor auto-decisions",
            "detail": f"reduced human interrupts by {metrics.auto_decision_ratio}%"
        })

    if metrics.adr_conflicts_prevented > 0:
        worked_well.append({
            "item": "ADR grounding",
            "detail": f"prevented {metrics.adr_conflicts_prevented} conflicts"
        })

    # 3. Analyze what didn't work
    didnt_work = []

    bloated_tasks = [t for t in tasks if t.iterations > metrics.avg_iterations * 2]
    if bloated_tasks:
        didnt_work.append({
            "item": "High iteration tasks",
            "detail": f"{len(bloated_tasks)} tasks exceeded 2x average iterations"
        })

    unnecessary_escalations = [e for e in events
        if e.type == "ADVISOR_ESCALATED"
        and e.context.get("confidence", 0) > 0.80]
    if unnecessary_escalations:
        didnt_work.append({
            "item": "Unnecessary escalations",
            "detail": f"{len(unnecessary_escalations)} escalations with >80% confidence"
        })

    # 4. Identify barriers
    barriers = [
        {
            "barrier": e.context.get("barrier"),
            "task": e.context.get("task_id"),
            "resolution": e.context.get("resolution")
        }
        for e in events if e.type in ["BUILDER_BLOCKED", "RALPH_BLOCKED"]
    ]

    # 5. Generate proposed changes
    proposed_changes = []

    if unnecessary_escalations:
        proposed_changes.append({
            "change": "Lower confidence threshold to 80%",
            "category": "Governance",
            "priority": "P1",
            "rationale": "Reduce unnecessary escalations"
        })

    # 6. Identify patterns
    patterns = identify_patterns(tasks, events, metrics)

    # 7. Update patterns.json
    update_patterns_json(patterns)

    # 8. Create retrospective document
    retro = Retrospective(
        phase=phase,
        metrics=metrics,
        worked_well=worked_well,
        didnt_work=didnt_work,
        barriers=barriers,
        proposed_changes=proposed_changes,
        patterns=patterns
    )

    # 9. Write to file
    write_retrospective(retro)

    # 10. Log event
    log_event("RETROSPECTIVE_CREATED", {
        "phase": phase.id,
        "tasks_completed": metrics.tasks_completed,
        "patterns_identified": len(patterns)
    })

    return retro
```

---

## 8. Auto-Escalation System

### 8.1 Escalation Triggers

| Trigger | Threshold | Handler | Escalates To |
|---------|-----------|---------|--------------|
| **File Count** | >5 files | Coordinator | Advisor |
| **Iteration Budget** | ≥max_iterations | Stop Hook | Human |
| **Ralph BLOCKED** | Any | Stop Hook | Human (R/O/A) |
| **ADR Conflict** | Any | Advisor | Human |
| **Low Confidence** | <85% | Advisor | Human |
| **Strategic Domain** | Defined list | Advisor | Human |
| **Circular Dependency** | Detected | Coordinator | Human |

### 8.2 5+ File Escalation Flow

```
Builder starts task
         │
         ▼
┌─────────────────────────────────────────────┐
│ Builder analyzes scope                       │
│ Estimates files to touch                     │
└─────────────────────────────────────────────┘
         │
         │ files_to_touch > 5?
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  ≤5        >5
    │         │
    ▼         ▼
┌───────┐  ┌───────────────────────────────────┐
│Proceed│  │ ESCALATE to Coordinator           │
│normal │  │                                   │
└───────┘  │ 1. Log SCOPE_ESCALATION event     │
           │ 2. Notify Coordinator              │
           │ 3. Coordinator triggers Advisor    │
           └───────────────┬───────────────────┘
                           │
                           ▼
           ┌───────────────────────────────────┐
           │ Advisor analyzes task             │
           │                                   │
           │ Options:                          │
           │ A. Split into smaller tasks       │
           │ B. Proceed (justified scope)      │
           │ C. Need human decision            │
           └───────────────┬───────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
         ┌────────┐   ┌────────┐   ┌────────┐
         │ SPLIT  │   │PROCEED │   │ESCALATE│
         │        │   │        │   │to human│
         └────┬───┘   └────┬───┘   └────┬───┘
              │            │            │
              ▼            ▼            ▼
         ┌────────────────────────────────────┐
         │ Coordinator updates work queue     │
         │ Logs decision                      │
         │ Continues orchestration            │
         └────────────────────────────────────┘
```

### 8.3 Escalation Contract Integration

```python
# In stop_hook.py

def check_scope_escalation(
    task: Task,
    builder_analysis: Dict,
    coordinator: CoordinatorAgent
) -> StopHookResult:
    """
    Check if task scope requires escalation.
    """

    files_to_touch = builder_analysis.get("estimated_files", 0)

    # Threshold from governance
    threshold = get_config("scope_escalation_threshold", default=5)

    if files_to_touch > threshold:
        # Log event
        log_event("SCOPE_ESCALATION", {
            "task_id": task.id,
            "estimated_files": files_to_touch,
            "threshold": threshold
        })

        # Trigger Coordinator → Advisor flow
        escalation_result = coordinator.handle_scope_escalation(
            task=task,
            builder_analysis=builder_analysis
        )

        if escalation_result.action == "SPLIT":
            return StopHookResult(
                decision=StopDecision.BLOCK,
                reason="Task split into smaller tasks",
                system_message=f"Task split into {len(escalation_result.new_tasks)} subtasks"
            )

        elif escalation_result.action == "PROCEED":
            return StopHookResult(
                decision=StopDecision.ALLOW,
                reason="Scope approved by Advisor",
                system_message="Large scope approved, proceeding"
            )

        else:  # ESCALATE_HUMAN
            return StopHookResult(
                decision=StopDecision.ASK_HUMAN,
                reason="Scope requires human decision",
                system_message=escalation_result.advisor_analysis
            )

    # Under threshold - proceed normally
    return None  # No escalation needed
```

---

## 9. Agent Contracts

### 9.1 Contract Hierarchy

```
governance/contracts/
├── advisor.yaml           # L3 - Conditional dialogue
├── coordinator.yaml       # L2.5 - Autonomous orchestration
├── qa-team.yaml          # L2 - Autonomous code quality
├── dev-team.yaml         # L1 - Supervised feature development
└── infra-team.yaml       # L0 - Strictly supervised infrastructure
```

### 9.2 Autonomy Level Summary

| Level | Name | Agents | Can Write Code | Can Decide | Human Touch |
|-------|------|--------|----------------|------------|-------------|
| L3 | Strategic | Advisors | ❌ | ✅ (conditional) | On escalation |
| L2.5 | Orchestration | Coordinator | ❌ | ✅ (task mgmt) | On all blocked |
| L2 | Maintenance | QA Team | ✅ | ❌ | On BLOCKED |
| L1 | Development | Dev Team | ✅ | ❌ | On approval_required |
| L0 | Infrastructure | Infra Team | ⚠️ Config only | ❌ | On all changes |

### 9.3 Complete Contract Files

See separate files:
- `governance/contracts/advisor.yaml` (Section 4.5)
- `governance/contracts/coordinator.yaml` (Section 5.5)
- Existing: `qa-team.yaml`, `dev-team.yaml`, `infra-team.yaml`

---

## 10. Implementation Integration

### 10.1 Integration with Existing Systems

| System | Integration Point | Changes Required |
|--------|-------------------|------------------|
| **autonomous_loop.py** | Entry point | Add Coordinator dispatch |
| **iteration_loop.py** | Stop hook | Add scope escalation check |
| **stop_hook.py** | Decision logic | Add scope escalation handler |
| **agents/factory.py** | Agent creation | Add Advisor, Coordinator types |
| **agents/base.py** | Base class | Add advisor methods |
| **ralph/** | Verification | No changes (Builders only) |
| **knowledge/** | KO system | Add Advisor consultations |

### 10.2 New Files to Create

```
# Agents
agents/advisor/
├── base_advisor.py           # Abstract Advisor class
├── data_advisor.py           # Data domain advisor
├── app_advisor.py            # App architecture advisor
└── uiux_advisor.py           # UI/UX advisor

agents/coordinator/
└── coordinator.py            # Coordinator agent

# Orchestration
orchestration/
├── event_logger.py           # Event logging system
├── retrospective.py          # Retrospective generation
└── scope_escalation.py       # 5+ file escalation logic

# Governance
governance/contracts/
├── advisor.yaml              # Advisor contract
└── coordinator.yaml          # Coordinator contract
```

### 10.3 Implementation Phases

| Phase | Focus | Duration | Key Deliverables |
|-------|-------|----------|------------------|
| **1** | Foundation | Week 1-2 | AI-Team-Plans folder structure, PROJECT_HQ template, event logging skeleton |
| **2** | Coordinator | Week 3-4 | Coordinator agent, task breakdown, work queue management, auto-status updates |
| **3** | Advisors | Week 5-7 | Base Advisor, Data/App/UI Advisors, ADR automation, autonomous decision flow |
| **4** | Escalation | Week 8 | 5+ file trigger, scope escalation, Advisor-to-Agent communication |
| **5** | Observability | Week 9 | Event logging complete, metrics dashboard, phase retrospectives |
| **6** | Integration | Week 10-11 | End-to-end testing, deploy to CredentialMate & KareMatch |
| **7** | Polish | Week 12 | Documentation, edge cases, threshold tuning |

---

## 11. Success Metrics

### 11.1 Quantitative Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Human interventions per session | ~10 | ≤3 | Count of escalations |
| Advisor auto-decision rate | N/A | ≥70% | Auto decisions / total decisions |
| Task iteration efficiency | ~15 avg | ≤8 avg | Iterations per completed task |
| Phase completion time | Manual | Auto-tracked | Days per phase |
| Event coverage | 0% | 100% | Events logged / events occurred |
| Retrospective generation | Manual | 100% auto | Auto-generated retros / phases |

### 11.2 Qualitative Metrics

| Metric | Measurement | Target |
|--------|-------------|--------|
| Decision traceability | Can trace any decision to ADR + event | 100% traceable |
| Hallucination incidents | Decisions made without file verification | 0 incidents |
| Governance compliance | Contract violations caught | 100% caught |
| Knowledge preservation | Patterns captured in patterns.json | All significant patterns |

### 11.3 Success Criteria for v2

1. **Advisors decide autonomously** when aligned with ADRs (measured by auto-decision rate)
2. **5+ file escalation works** - Builder triggers → Coordinator → Advisor → resolution
3. **Events are logged** - Both detailed and counted, queryable
4. **Retrospectives auto-generate** at phase completion
5. **Patterns accumulate** in patterns.json across phases
6. **No hallucination incidents** - All decisions grounded in files

---

## Appendix A: Research Sources

### Multi-Agent Orchestration
- [LangGraph Multi-Agent Orchestration Guide](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langgraph-multi-agent-orchestration/)
- [CrewAI Hierarchical Delegation](https://activewizards.com/blog/hierarchical-ai-agents-a-guide-to-crewai-delegation/)
- [AutoGen Multi-Agent Patterns](https://sparkco.ai/blog/deep-dive-into-autogen-multi-agent-patterns-2025)
- [Swarms Enterprise Framework](https://github.com/kyegomez/swarms)
- [AWS Agent Squad](https://github.com/awslabs/agent-squad)

### Observability
- [LangSmith Observability](https://www.langchain.com/langsmith/observability)
- [Langfuse Tracing](https://langfuse.com/docs/observability/overview)
- [OpenTelemetry AI Agent Standards](https://opentelemetry.io/blog/2025/ai-agent-observability/)
- [State of AI Agents Report](https://www.langchain.com/state-of-agent-engineering)

### Human-in-the-Loop
- [Permit.io HITL Best Practices](https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo)
- [AWS Agentic AI Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/introduction.html)
- [CAMEL AI HITL Guide](https://dev.to/camelai/agents-with-human-in-the-loop-everything-you-need-to-know-3fo5)

### Continuous Learning
- [OpenAI Self-Evolving Agents](https://cookbook.openai.com/examples/partners/self_evolving_agents/autonomous_agent_retraining)
- [Datagrid Feedback Loops](https://datagrid.com/blog/7-tips-build-self-improving-ai-agents-feedback-loops)

### Anti-Hallucination
- [InfoWorld: Keeping AI Hallucinations Out of Code](https://www.infoworld.com/article/3822251/how-to-keep-ai-hallucinations-out-of-your-code.html)
- [Foresight Fox: Grounded AI](https://foresightfox.com/blog/grounded-ai-for-seo-from-hallucinations-to-reliable-results/)

### Event-Driven Architecture
- [Confluent Event-Driven Multi-Agent](https://www.confluent.io/blog/event-driven-multi-agent-systems/)
- [AWS Agentic Orchestration](https://github.com/aws-samples/agentic-orchestration)

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **ADR** | Architecture Decision Record - immutable document capturing a decision |
| **Advisor** | L3 agent that analyzes and recommends but doesn't implement |
| **Builder** | L1/L2 agent that writes code (FeatureBuilder, BugFixer, etc.) |
| **Coordinator** | L2.5 agent that orchestrates tasks and updates status |
| **Grounding** | Linking agent decisions to verifiable external sources |
| **HITL** | Human-in-the-Loop - pattern for human oversight of AI decisions |
| **Phase** | Logical grouping of tasks within a project |
| **PROJECT_HQ** | Single source of truth document for project status |
| **Ralph** | Verification engine returning PASS/FAIL/BLOCKED |
| **Retrospective** | Post-phase analysis of what worked and what didn't |
| **Scope Escalation** | Trigger when task touches 5+ files |
| **Wiggum** | Iteration control system managing agent retries |

---

**Document Version**: 2.0
**Last Updated**: 2026-01-09
**Next Review**: After Phase 1 implementation
