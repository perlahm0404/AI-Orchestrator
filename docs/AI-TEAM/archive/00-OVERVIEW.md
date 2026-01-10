# AI Team Architecture: Executive Overview

**Date**: 2026-01-09
**Author**: Claude Opus 4.5
**Status**: Design Phase

---

## The Problem

You're currently acting as the Program Manager, Project Manager, and Technical Architect yourself:
- Manually telling agents to go into plan mode
- Manually directing creation of technical roadmaps
- Manually tracking project status across sessions
- Context-switching between strategic decisions and execution oversight
- No single source of truth for project state

**This doesn't scale.**

---

## The Solution: Two-Phase AI Team

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: DIALOGUE (Human + Advisors)                                       │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  You ←→ Data Advisor    "How should we structure this data?"                │
│  You ←→ App Advisor     "What's the best technical approach?"               │
│  You ←→ UI/UX Advisor   "How should users interact with this?"              │
│                                                                             │
│  OUTPUT: Decision Documents (ADRs) written automatically                    │
│          PROJECT_HQ.md updated automatically                                │
│          Technical roadmap created automatically                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          "Approved. Build it."
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: AUTONOMOUS EXECUTION (Coordinator + Builders)                     │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  Coordinator Agent:                                                         │
│    - Breaks decisions into tasks (automatically)                            │
│    - Assigns to Builder agents (automatically)                              │
│    - Updates PROJECT_HQ.md status (automatically)                           │
│    - Creates session handoffs (automatically)                               │
│                                                                             │
│  Builder Agents:                                                            │
│    - Feature Builder, Bug Fixer, Test Writer (existing)                     │
│    - Execute tasks autonomously                                             │
│    - Report completion to Coordinator                                       │
│                                                                             │
│  YOU: Only intervene on BLOCKED verdicts                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

### 1. Advisors DIALOGUE, They Don't Decide Autonomously

```
WRONG:  "I've designed your database schema and implemented it."
RIGHT:  "Here are 3 schema approaches with tradeoffs. Which fits your needs?"
```

Advisors present options, explain tradeoffs, and wait for your decision. Once you decide, they document it and hand off to execution.

### 2. Coordinators AUTOMATE Artifact Creation

You should never have to say:
- "Create a project plan"
- "Update the status"
- "Write a technical roadmap"

The Coordinator does this automatically as part of its core behavior.

### 3. Single Source of Truth: PROJECT_HQ.md

One file per project that tracks everything:
- Current focus
- Task status
- Recent decisions
- Blockers needing your attention
- Roadmap

Agents update it. You read it.

### 4. Governance Unified Across Repos

| Repo | Current State | After Overhaul |
|------|---------------|----------------|
| AI_Orchestrator | Contract-based agents | + Advisor mode, + Coordinator |
| CredentialMate | HIPAA contracts | Synced from AI_Orchestrator + HIPAA extensions |
| KareMatch | Skill-based | Adopts unified governance, keeps domain skills |

---

## The Agent Roster

### Tier 1: Advisors (Dialogue Mode)

| Agent | Domain | Key Question |
|-------|--------|--------------|
| **Data Advisor** | Schema, pipelines, quality | "How should we store and manage this data?" |
| **App Advisor** | Architecture, APIs, tech stack | "What's the best technical approach?" |
| **UI/UX Advisor** | Interfaces, flows, accessibility | "How should users interact with this?" |

**Mode**: Interactive dialogue. Present options. Wait for decisions. Auto-document.

### Tier 2: Coordinator (Autonomous Mode)

| Agent | Role | Key Behaviors |
|-------|------|---------------|
| **Coordinator** | Project orchestration | Break decisions into tasks, assign to builders, track status, create artifacts |

**Mode**: Autonomous. Runs without prompting once decisions are made.

### Tier 3: Builders (Autonomous Mode)

| Agent | Role | Inherited From |
|-------|------|----------------|
| **Feature Builder** | Build new features | Existing (AI_Orchestrator) |
| **Bug Fixer** | Fix issues | Existing (AI_Orchestrator) |
| **Test Writer** | Write tests | Existing (AI_Orchestrator) |
| **Code Quality** | Refactoring, lint fixes | Existing (AI_Orchestrator) |

**Mode**: Autonomous. Execute within contracts. Ralph-verified.

---

## What Changes

### For You (The Human)

| Before | After |
|--------|-------|
| "Go into plan mode" | Just describe what you want |
| "Create a technical roadmap" | Advisor creates it automatically |
| "Update the project status" | Coordinator updates it automatically |
| Track status mentally | Read PROJECT_HQ.md |
| Direct every artifact | Artifacts created as byproduct of workflow |

### For the System

| Before | After |
|--------|-------|
| Agents wait for instructions | Advisors ask clarifying questions proactively |
| Artifacts created on request | Artifacts created automatically |
| Status scattered across files | Single PROJECT_HQ.md |
| Three different governance models | Unified governance with project extensions |

---

## Document Index

| Document | Purpose |
|----------|---------|
| [01-CURRENT-STATE.md](./01-CURRENT-STATE.md) | Analysis of all 3 repos, conflicts identified |
| [02-ARCHITECTURE.md](./02-ARCHITECTURE.md) | Detailed agent architecture design |
| [03-ADVISOR-AGENTS.md](./03-ADVISOR-AGENTS.md) | Data/App/UI Advisor specifications |
| [04-COORDINATOR-AGENT.md](./04-COORDINATOR-AGENT.md) | Coordinator agent specification |
| [05-GOVERNANCE-OVERHAUL.md](./05-GOVERNANCE-OVERHAUL.md) | Unified governance across repos |
| [06-IMPLEMENTATION-PLAN.md](./06-IMPLEMENTATION-PLAN.md) | Build phases and order |
| [PROJECT-HQ-TEMPLATE.md](./PROJECT-HQ-TEMPLATE.md) | Template for project tracking |

---

## Success Criteria

After implementation:

1. **You describe a feature** → Advisor dialogue begins automatically
2. **You approve a decision** → ADR written, roadmap updated, tasks created automatically
3. **You say "build it"** → Autonomous execution begins, you only see BLOCKED prompts
4. **You want status** → Read PROJECT_HQ.md (always current)
5. **Session ends** → Handoff created automatically, next session resumes seamlessly

**Target**: 90% reduction in manual orchestration overhead.


![[Pasted image 20260109181628.png]]