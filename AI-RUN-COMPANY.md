# AI-Run Company: The 3 Meta-Agents Framework

**Version**: 2.0
**Date**: 2026-01-10
**Context**: CredentialMate (healthcare licensing + CME compliance automation)
**Current State**: 89% autonomy, 5 agent teams, v5.7 production-ready
**Proposed**: v6.0 with 3 meta-agents (PM, CMO, Governance)

---

## Executive Summary

After extensive research and discussion, here's the operating model for CredentialMate's AI-run company:

**The 3 meta-agents are non-negotiable:**
- **Product Manager Agent**: Ensures we build the right things (continuous discovery, evidence-driven prioritization)
- **Chief Marketing Officer Agent**: Ensures the right people find us, trust us, and buy (growth engine, demand capture, messaging)
- **Governance Agent**: Ensures we never violate compliance, always maintain auditability, and gate high-risk actions (HIPAA, LLM security, human approval gates)

**Operating principle:**
User value > safety/compliance > quality > cost
*(Cost is a guardrail, not a gate)*

**Why these 3 work together:**
- **PM + CMO drive velocity + learning**: PM discovers what to build, CMO discovers how to reach users and prove value
- **Governance constrains the action space**: Prevents HIPAA violations, ensures audit trails, gates high-risk changes
- **They don't compete**: PM owns product scope, CMO owns GTM, Governance owns compliance/risk

**Timeline:** 8 weeks to implement all 3 + operating loops (realistic for solo founder)

**Prerequisites:** Evidence Repository, Eval Suite, Tracing (meta-agents can't function without these)

---

## The 3 Meta-Agents That Move the Company Forward

### 1. Product Manager Agent (Discovery & Prioritization)

**Mission:**
Run continuous discovery to ensure we build what users need, prioritize by evidence and outcome metrics, and prevent wasted effort on off-roadmap work.

**Why it's non-negotiable:**
A startup that builds without discovery risks the most common failure mode: a product that solves the wrong problem. PM ensures we stay aligned with user needs through weekly touchpoints and evidence-based decisions.

**Inputs (what it reads):**
- Evidence Repository (`evidence/*.md`) - user feedback, bug reports, feature requests, edge cases
- Roadmap document (`PROJECT_HQ.md`) - Q1 focus areas (5 bullets, not exhaustive)
- Work queue (`tasks/work_queue_credentialmate.json`) - pending tasks
- User interview notes (stored in Evidence Repository)
- Product usage metrics (activation, retention, time-to-value)
- ADR registry - past decisions and rationale

**Outputs (hard requirements):**
- **Pre-task validation**: APPROVED / BLOCKED / MODIFIED decision for each task
  - If BLOCKED: reason + alternative recommendation
  - If MODIFIED: updated task description with acceptance criteria
- **Weekly discovery summary**: 3-5 evidence items captured, patterns identified, recommended experiments
- **Outcome metrics dashboard**: feature → activation/retention impact
- **Quarterly roadmap updates**: "Q1 Focus" doc (5 bullets)

**Decision rights:**
- **Can block:** Tasks that don't align with roadmap OR lack evidence of user need OR have no outcome metrics defined
- **Can modify:** Task descriptions to add acceptance criteria, outcome metrics, or evidence links
- **Cannot do:** Override Governance constraints, change compliance posture, decide GTM strategy

**Cadence:**
- **Event-driven:** Pre-task validation (fires before agent execution)
- **Weekly ritual:** Discovery synthesis (Fridays, 30 min) - review evidence, identify patterns, propose experiments
- **Quarterly:** Roadmap review + update

**Success metrics:**
1. **Evidence coverage**: 80%+ of tasks link to ≥1 evidence item
2. **Discovery cadence**: 5+ evidence items captured per week
3. **Roadmap alignment**: 0 off-roadmap features shipped
4. **Outcome clarity**: 100% of features have defined success metrics
5. **Waste reduction**: <10% of completed tasks have zero user adoption
6. **Human escalations**: <10 per week (low interrupt rate)

**Failure modes + mitigations:**
- **Bottleneck risk**: PM blocks everything, slows velocity
  - *Mitigation*: PM only fires on user-facing changes, refactors auto-approved
  - *Mitigation*: 24-hour approval SLA, auto-approve after timeout
- **False positives**: PM blocks valuable work due to lack of evidence
  - *Mitigation*: Human override available (`aibrain pm override TASK-ID "reason"`)
  - *Mitigation*: PM recommends how to gather evidence, doesn't just block
- **Roadmap staleness**: Roadmap doesn't reflect reality
  - *Mitigation*: Quarterly review ritual, triggered by 3+ evidence items contradicting roadmap
- **PM/CMO overlap**: Both trying to prioritize features
  - *Mitigation*: PM owns product scope, CMO proposes but doesn't decide

---

### 2. Chief Marketing Officer Agent (Growth Engine)

**Mission:**
Build and run the growth system that turns provider demand into a reliable pipeline, activation, and revenue—while continuously improving positioning and messaging.

**Why it's non-negotiable early:**
A startup isn't just "build"; it's *make something people want and reach those people*. If you only build, you risk the most common failure mode: a product that's valuable but invisible. Early-stage CMO is not brand spend or broad segmentation—it's a repeatable growth loop: attract the right prospects, activate them, convert to paying users, turn them into referrals/case studies that attract the next cohort.

**"Fake it before you make it" (ethical demand testing):**
Use lightweight market tests to validate demand before building:
- **Landing pages**: "Join waitlist for [feature]" to gauge interest
- **Webinars**: "How to avoid license renewal mistakes" to attract prospects
- **Pricing tests**: "Would you pay $X/month for automated CME tracking?" (honest survey)
- **Fake doors**: "This feature is coming soon" (with honest messaging, not deception)
- **LOI collection**: "Sign this Letter of Intent if interested" to validate enterprise deals

This isn't deceptive—it's validating demand before committing engineering resources. Reduces build risk, accelerates learning.

**Why growth now doesn't contradict PMF:**
Early growth work = recruiting users manually, learning objections, accelerating PMF feedback loops. You can't find product-market fit without users. CMO recruiting pilots + capturing objections FEEDS PM's discovery work. They're complementary, not competitive.

**Non-goals (to prevent overlap with PM):**
- ❌ Does NOT own feature prioritization or product scope decisions
- ❌ Does NOT "score" product work or veto roadmap items
- ❌ Does NOT decide compliance posture (Governance does)

**Primary responsibilities (what PM should not be doing):**
- **Messaging & positioning**: Segment-specific messaging matrix (MD/DO/NP/PA; multi-state vs single-state; enterprise vs individual)
- **Channel experiments**: Run weekly experiment backlog (email, webinars, partnerships, outbound, referral asks, SEO pillars)
- **Demand capture**: Landing pages, waitlists, demos, LOIs, conversion scripts
- **Activation + onboarding improvements (GTM side)**: Reduce friction from "interested" → "activated"
- **Proof-building assets**: Case studies, ROI calculator, security/trust one-pager, "what happens if you miss renewal" story library (CredentialMate-specific credibility)

**Inputs (what it reads):**
- CRM/pipeline + deal notes, demo recordings, objections
- Website analytics, email metrics
- Evidence Repository (customer interviews + support tickets) - but uses it for *messaging*, not roadmap
- Product usage metrics (activation/retention) at a coarse level
- Competitor positioning (scraped from websites)
- State licensing board websites (for credibility stories)

**Outputs (hard requirements):**
- **Messaging matrix** (monthly update): 4 segments × 3 value props × 2 objection handles
- **Weekly experiment plan + results**: What ran, what we learned, what changed
- **Pipeline dashboard**: Counts + stage conversion (lead → demo → pilot → paid)
- **Content/calendar + distribution plan**: Webinars, blog posts, case studies, email sequences
- **"Fake-door / demand test" results**: When testing new offers/pricing

**Decision rights:**
- **Can ship**: GTM experiments, messaging changes (within brand/compliance guardrails)
- **Can propose**: Product changes (e.g., "activation is blocked by X, suggest we fix Y")
- **Cannot do**: Override PM roadmap decisions, override Governance constraints, deploy product code

**Cadence:**
- **Weekly experiment loop**: Monday plan, Friday review
- **Monthly messaging update**: Refresh positioning based on objections/wins
- **Quarterly growth review**: Pipeline health, channel performance, activation funnel

**Success metrics (early-stage, low-signal-friendly):**
1. **Qualified lead volume**: Week-over-week growth
2. **Demo → pilot conversion rate**: Target 30%+
3. **Pilot → paid conversion rate**: Target 50%+
4. **Time-to-first-value (activation)**: Target <7 days
5. **Referral / intro rate from early users**: Target 20%+ (even if small numbers)
6. **Channel experiment velocity**: 1+ new experiment per week

*(Optional: Structure using AARRR framework - Acquisition, Activation, Retention, Referral, Revenue)*

**Failure modes + mitigations:**
- **PM/CMO overlap**: Both analyzing evidence, confusing boundaries
  - *Mitigation*: PM uses evidence for "what to build," CMO uses evidence for "how to message"
  - *Mitigation*: Weekly sync (15 min) - PM shares roadmap updates, CMO shares objection patterns
- **Vanity metrics**: CMO optimizes for traffic, not revenue
  - *Mitigation*: Metrics tied to pipeline (leads → demos → paid), not just visitors
- **Channel sprawl**: CMO runs 10 experiments, none at depth
  - *Mitigation*: Max 2 active channels at a time, double-down on what works
- **Activation theater**: Landing pages promise features that don't exist
  - *Mitigation*: Governance enforces "coming soon" language, no false claims
  - *Mitigation*: CMO must link fake-door tests to PM backlog (if demand proven → PM prioritizes build)

---

### 3. Governance Agent (Compliance + Risk)

**Mission:**
Ensure CredentialMate never violates HIPAA, maintains complete auditability, gates high-risk actions, and enforces human-in-the-loop for critical decisions.

**Why it's non-negotiable:**
HIPAA violations are existential for a healthcare product. The January 2025 HIPAA Security Rule NPRM (proposed rule) tightens cybersecurity requirements. 78% of CIOs cite compliance as the primary implementation barrier for AI systems. Governance is not optional—it's survival.

**Scope (early-stage focus):**
1. **HIPAA Compliance** (existential): PHI protection, encryption, audit trails
2. **LLM Security** (high risk): Adversarial prompts, prompt injection, data leakage
3. **Human-in-the-Loop Gates** (regulatory): Production deploys, auth changes, billing, state expansion

**Deferred until scale:**
- Organizational policy (creating new agents, capability gaps) - wait until 10+ agents

**Inputs (what it reads):**
- Code changes (via git diff)
- Task descriptions (`work_queue_credentialmate.json`)
- Agent traces (`.aibrain/traces/*.json`)
- HIPAA eval results (CI)
- Risk register (`governance/risk_register.yaml`)
- Guardrail violations (Ralph BLOCKED verdicts)

**Outputs (hard requirements):**
- **Pre-task risk assessment**: LOW / MEDIUM / HIGH / CRITICAL
  - If HIGH or CRITICAL: human approval required before execution
- **HIPAA eval results**: PASS / FAIL for every PR (CI integration)
- **Audit trail validation**: 100% of PHI access logged (who, when, what, why)
- **Risk register updates**: New failure modes identified, mitigations proposed
- **Human approval requests**: Clear, actionable (what's the risk, what are options, what do you recommend)

**Decision rights:**
- **Can block**: Tasks that touch PHI-handling code, auth, billing, infra, state expansion (until human approves)
- **Can enforce**: Logging constraints (no PHI in logs/traces/errors), encryption standards, audit trail requirements
- **Cannot do**: Decide product scope (PM), decide GTM strategy (CMO), override human approval

**Cadence:**
- **Event-driven**: Pre-task risk assessment (fires before high-risk actions)
- **Always-on**: Logging constraint enforcement (passive monitoring)
- **Weekly ritual**: Risk register review (Fridays, 15 min) - new failure modes, mitigation status
- **Monthly**: HIPAA compliance report (eval pass rates, audit trail coverage, PHI detection accuracy)

**Success metrics:**
1. **HIPAA eval pass rate**: 100% (critical evals must always pass)
2. **PHI detection accuracy**: 100% (no PHI in logs/traces/errors)
3. **Audit trail coverage**: 100% (all PHI access logged)
4. **Human approval latency**: <24 hours (don't block work unnecessarily)
5. **Risk register coverage**: 100% of critical contexts have failure modes mapped
6. **False positive rate**: <5% (don't cry wolf on low-risk changes)

**Failure modes + mitigations:**
- **Over-blocking**: Governance blocks low-risk changes, slows velocity
  - *Mitigation*: Risk scoring model (only HIGH/CRITICAL require approval)
  - *Mitigation*: Human override available with justification
- **PHI leakage**: Agent logs patient name in trace despite detection
  - *Mitigation*: Multi-layer defense (regex + ML-based PHI detection + eval suite + manual audits)
  - *Mitigation*: Fail-safe: if PHI detected in logs → immediate alert + purge
- **Audit gap**: Not all PHI access logged (compliance violation)
  - *Mitigation*: Daily audit trail validation, alerts on gaps
  - *Mitigation*: Quarterly external audit (manual spot-check)
- **Security drift**: LLM vulnerabilities not monitored
  - *Mitigation*: Monthly OWASP LLM Top 10 review, update threat model

**NIST AI RMF Framework (Govern/Map/Measure/Manage):**
- **Govern**: Policies (HIPAA, human-in-loop), roles (solo founder = approver), contracts (agent permissions)
- **Map**: Contexts (CME tracking, license renewal, notifications), failure modes (incorrect CME hours, missed deadlines, PHI exposure)
- **Measure**: Metrics (HIPAA eval pass rate, PHI detection accuracy, audit coverage)
- **Manage**: Mitigations (eval suites, multi-layer PHI detection, human approval gates), response (incident playbook, rollback, postmortems)

**OWASP LLM Top 10 Coverage:**
1. Prompt Injection → Governance detects adversarial inputs in traces
2. Insecure Output Handling → HIPAA evals check for PHI in outputs
3. Training Data Poisoning → N/A (using hosted LLMs)
4. Model Denial of Service → CFO agent cost guardrails (if added)
5. Supply Chain Vulnerabilities → Governance tracks LLM provider SLAs
6. Sensitive Information Disclosure → PHI detection, audit trails
7. Insecure Plugin Design → Agent tool calls logged in traces
8. Excessive Agency → Human-in-loop gates for critical actions
9. Overreliance → PM ensures outcome metrics, not blind trust
10. Model Theft → N/A (using hosted LLMs)

---

## One-Line Separation (Preventing Overlap)

**PM**: "What should we build next, for whom, and how will we measure value?"
*(Continuous discovery cadence: weekly user touchpoints, evidence-driven decisions)*

**CMO**: "How do the right customers find us, trust us, try us, and buy—reliably?"
*(Growth loop: attract → activate → convert → refer)*

**Governance**: "What must never happen, what must be auditable, and what requires human approval?"
*(NIST AI RMF: Govern/Map/Measure/Manage)*

---

## Agent Interaction Workflow (Human-in-the-Loop)

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CREDENTIALMATE AI ORG                        │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   HUMAN (Solo Founder)                       │  │
│  │  - Approves high-risk actions                                │  │
│  │  - Reviews weekly rituals (PM/CMO/Gov summaries)             │  │
│  │  - Overrides agent decisions when needed                     │  │
│  └────────┬─────────────────────────────────┬──────────────────┘  │
│           │                                 │                      │
│           ▼                                 ▼                      │
│  ┌─────────────────┐              ┌──────────────────┐            │
│  │  META-AGENTS    │              │ OPERATING LOOPS  │            │
│  │  (Coordinate)   │◄────────────►│ (Data Sources)   │            │
│  └─────────────────┘              └──────────────────┘            │
│           │                                 │                      │
│           │  ┌──────────────────────────────┤                      │
│           │  │                              │                      │
│           ▼  ▼                              ▼                      │
│  ┌─────────────────┐              ┌──────────────────┐            │
│  │ PM Agent        │              │ Evidence Repo    │            │
│  │ CMO Agent       │              │ Eval Suite       │            │
│  │ Governance Agent│              │ Tracing System   │            │
│  └────────┬────────┘              └──────────────────┘            │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              EXECUTION AGENTS (Do Work)                     │  │
│  │  - BugFixAgent, CodeQualityAgent, FeatureBuilderAgent      │  │
│  │  - TestWriterAgent, DeploymentAgent                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Detailed Task Flow (Conditional Gates)

```
NEW TASK CREATED
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│ 1. GOVERNANCE RISK ASSESSMENT (always runs)                      │
│    - Read task description                                       │
│    - Classify risk: LOW / MEDIUM / HIGH / CRITICAL               │
│    - Check: Does it touch PHI code, auth, billing, infra?        │
├───────────────────────────────────────────────────────────────────┤
│ IF CRITICAL: BLOCK → Human approval required                     │
│ IF HIGH: WARN → Log risk, continue but flag for review           │
│ IF MEDIUM/LOW: ALLOW → Continue                                  │
└───────────┬───────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│ 2. PM VALIDATION (conditional: only if user-facing or feature)   │
│    - IF task.type == "feature" OR task.affects_user_experience:  │
│      ├─ Read Evidence Repository                                 │
│      ├─ Check roadmap alignment (PROJECT_HQ.md)                  │
│      ├─ Validate outcome metrics defined                         │
│      └─ Decision: APPROVED / BLOCKED / MODIFIED                  │
│    - ELSE: Skip PM validation (auto-approve refactors/bugfixes)  │
├───────────────────────────────────────────────────────────────────┤
│ IF BLOCKED: Mark task blocked, notify human                      │
│ IF MODIFIED: Update task description, continue                   │
│ IF APPROVED: Continue                                            │
└───────────┬───────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│ 3. CMO REVIEW (conditional: only if GTM-related)                 │
│    - IF task involves messaging, landing pages, onboarding:      │
│      ├─ Check messaging matrix alignment                         │
│      ├─ Validate demand evidence (fake-door results)             │
│      └─ Decision: APPROVED / PROPOSE_ALTERNATIVE                 │
│    - ELSE: Skip CMO review                                       │
├───────────────────────────────────────────────────────────────────┤
│ IF PROPOSE_ALTERNATIVE: Add to CMO experiment backlog            │
│ IF APPROVED: Continue                                            │
└───────────┬───────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│ 4. COST GUARDRAIL CHECK (threshold-based)                        │
│    - IF task.estimated_cost_usd > $10:                           │
│      └─ Log warning, continue (cost is guardrail, not gate)      │
│    - IF task.estimated_cost_usd > $50:                           │
│      └─ Escalate to human, recommend approval/rejection          │
│    - ELSE: Skip cost check                                       │
└───────────┬───────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│ 5. EXECUTION AGENT RUNS TASK                                     │
│    - IterationLoop with Wiggum control (15-50 retries)           │
│    - Agent performs work (read, write, edit files)               │
│    - Generate trace (tools called, files changed, tests run)     │
│    - Run tests                                                   │
│    - Ralph verification (PASS/FAIL/BLOCKED)                      │
└───────────┬───────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│ 6. POST-COMPLETION CHECKS                                        │
│    ├─ Governance: Validate no PHI in logs/traces                 │
│    ├─ PM: Verify implementation matches acceptance criteria      │
│    └─ Ralph: PASS/FAIL/BLOCKED verdict                           │
├───────────────────────────────────────────────────────────────────┤
│ IF Ralph BLOCKED: Human decision (R/O/A)                         │
│ IF Ralph FAIL (regression): Agent iterates (Wiggum loop)         │
│ IF Ralph PASS: Continue to merge                                 │
└───────────┬───────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│ 7. HUMAN APPROVAL (for merge to main)                            │
│    - Review PR                                                   │
│    - Check trace (what changed, why)                             │
│    - Check eval results (HIPAA passed?)                          │
│    - Approve or Reject                                           │
└───────────┬───────────────────────────────────────────────────────┘
            │
            ▼
         MERGED
```

### Weekly Ritual Flow (Human Reviews)

```
FRIDAY RITUALS (90 minutes total)
│
├─ 30 min: PM Discovery Synthesis
│   ├─ Review Evidence Repository (new items this week)
│   ├─ Identify patterns (3+ items same theme → potential feature)
│   ├─ Update roadmap if needed
│   └─ Output: Weekly discovery summary
│
├─ 30 min: CMO Growth Review
│   ├─ Review experiment results (what worked, what didn't)
│   ├─ Update messaging matrix based on objections
│   ├─ Plan next week's experiments
│   └─ Output: Weekly experiment plan
│
└─ 30 min: Governance Risk Review
    ├─ Review risk register (new failure modes?)
    ├─ Check HIPAA eval trends (any declining pass rates?)
    ├─ Validate audit trails (any gaps?)
    └─ Output: Weekly compliance report
```

### Meta-Agent Communication (How They Coordinate)

```
┌────────────────────────────────────────────────────────────────┐
│                     SHARED DATA SOURCES                        │
│  (Meta-agents read, don't write to each other)                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────┐      ┌──────────────────┐              │
│  │ Evidence Repo    │◄─────┤ PM reads for     │              │
│  │                  │      │ product insights │              │
│  │ (user feedback)  │      └──────────────────┘              │
│  └────────┬─────────┘                                         │
│           │                                                   │
│           └──────────────────┐                                │
│                              ▼                                │
│                    ┌──────────────────┐                       │
│                    │ CMO reads for    │                       │
│                    │ messaging/GTM    │                       │
│                    └──────────────────┘                       │
│                                                                │
│  ┌──────────────────┐      ┌──────────────────┐              │
│  │ Work Queue       │◄─────┤ PM validates     │              │
│  │                  │      │ tasks            │              │
│  │ (tasks)          │      └──────────────────┘              │
│  └────────┬─────────┘                                         │
│           │                                                   │
│           └──────────────────┐                                │
│                              ▼                                │
│                    ┌──────────────────┐                       │
│                    │ Governance gates │                       │
│                    │ high-risk tasks  │                       │
│                    └──────────────────┘                       │
│                                                                │
│  ┌──────────────────┐      ┌──────────────────┐              │
│  │ Traces           │◄─────┤ Governance reads │              │
│  │                  │      │ for PHI leakage  │              │
│  │ (agent logs)     │      └──────────────────┘              │
│  └────────┬─────────┘                                         │
│           │                                                   │
│           └──────────────────┐                                │
│                              ▼                                │
│                    ┌──────────────────┐                       │
│                    │ PM reads for     │                       │
│                    │ outcome metrics  │                       │
│                    └──────────────────┘                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘

NO DIRECT COMMUNICATION (prevents coordination overhead)
- PM doesn't call CMO
- CMO doesn't call Governance
- Each reads shared data sources
- Weekly sync ritual (15 min) for human to resolve conflicts
```

---

## Operating Loops (Prerequisites for Meta-Agents)

Meta-agents can't function without these data sources. Build these first.

### 1. Evidence Repository (Continuous Discovery)

**Purpose**: Structured capture of user feedback, bug reports, feature requests, edge cases, state variations.

**Minimal folder structure:**
```
evidence/
├── README.md                    # Purpose, capture workflow, types, tags
├── EVIDENCE_TEMPLATE.md         # Copy this for new entries
├── index.md                     # Master table of all evidence
├── EVIDENCE-001-ca-np-cme.md    # Example: CA NP CME issue
├── EVIDENCE-002-tx-pa-renewal.md
└── ...
```

**Required template fields:**
```yaml
---
id: EVIDENCE-{NUMBER}
date: YYYY-MM-DD
type: [bug-report|feature-request|user-question|edge-case|state-variation]
source: [pilot-user|support-ticket|state-website|manual-testing]
project: credentialmate
tags: [cme, licensing, {state}, {specialty}]
priority: [p0-blocks-user|p1-degrades-trust|p2-improvement]
linked_tasks: []
linked_adrs: []
status: [captured|analyzed|implemented|validated]
---

## Evidence Summary
Brief description (1-2 sentences)

## Context
- User persona: [NP|PA|Physician]
- State: [CA|TX|NY|...]
- Specialty: [Family Medicine|Emergency|...]
- Current behavior: What happens now
- Expected behavior: What should happen

## Raw Data
- Screenshots / PDFs / links
- User quote (if applicable)
- Relevant state regulation text

## Impact Assessment
- How many users affected?
- Urgency: [immediate|this quarter|backlog]
- Business value: [high-retention|nice-to-have|table-stakes]

## Linked Items
- Tasks: TASK-XXX
- ADRs: ADR-XXX

## Resolution (if implemented)
- Date resolved:
- Implementation:
- Validation:
```

**CLI commands needed:**
```bash
aibrain evidence capture <type> <source>   # Interactive capture
aibrain evidence list --state CA --priority p0
aibrain evidence link EVIDENCE-001 TASK-CME-045
```

---

### 2. Eval Suite (Domain-Specific Correctness)

**Purpose**: Validate agent accuracy on CredentialMate-specific domains (license extraction, CME rules, deadlines).

**Minimal folder structure:**
```
evals/
├── README.md                        # Purpose, categories, running evals
├── manifest.yaml                    # Eval registry (8 categories)
├── gold/
│   ├── license_requirements.json    # Gold dataset: CA/TX/NY/FL/PA
│   ├── cme_rules.json               # Gold dataset: CME hours per state
│   ├── deadlines.json               # Gold dataset: renewal calculations
│   ├── notifications.json           # Gold dataset: notification correctness
│   ├── state_edge_cases.json        # Gold dataset: compact states, reciprocity
│   ├── specialty_rules.json         # Gold dataset: NP vs PA vs MD
│   ├── regression_cases.json        # Gold dataset: previously fixed bugs
│   └── hipaa_cases.json             # Gold dataset: no PHI in logs/outputs
├── test_license_extraction.py
├── test_cme_rules.py
├── test_deadline_calculation.py
├── test_notifications.py
├── test_state_variations.py
├── test_specialty_rules.py
├── test_regression.py
└── test_hipaa_compliance.py
```

**8 eval categories:**
1. **License Extraction** (100% accuracy required)
2. **CME Rules** (95% accuracy, some ambiguity acceptable)
3. **Deadline Calculation** (100% accuracy, wrong date = user misses renewal)
4. **Notification Correctness** (100% accuracy, wrong notification = trust loss)
5. **State Variations** (90% accuracy, learning edge cases over time)
6. **Specialty Rules** (95% accuracy, NP vs PA vs MD differences)
7. **Regression Prevention** (100% accuracy, regressions are unacceptable)
8. **HIPAA Compliance** (100% accuracy, no PHI in logs/traces/errors)

**CI integration:**
```yaml
# .github/workflows/evals.yml
name: Evals
on: [pull_request, push]
jobs:
  run-evals:
    steps:
      - name: Run critical evals
        run: pytest evals/ -m "eval and critical"
      - name: Fail on regression
        run: python scripts/check_eval_results.py
```

---

### 3. Tracing System (End-to-End Observability)

**Purpose**: Capture full agent execution path (tools called, files changed, tests run, verdict) for debugging and audit.

**Minimal folder structure:**
```
.aibrain/
├── traces/
│   ├── trace-abc123.json
│   ├── trace-def456.json
│   └── ...
└── meta_decisions.json    # Meta-agent decisions log
```

**Trace schema (JSON):**
```json
{
  "trace_id": "trace-abc123",
  "task_id": "TASK-CME-045",
  "goal": "Fix CME hour calculation for CA NPs",
  "project": "credentialmate",
  "agent_type": "bugfix",
  "started_at": "2026-01-10T14:30:00Z",
  "completed_at": "2026-01-10T14:45:00Z",
  "duration_seconds": 900,
  "iterations": 3,
  "status": "completed",

  "tools_called": [
    {"tool": "Read", "file": "src/cme_calculator.py", "success": true, "duration_ms": 123},
    {"tool": "Edit", "file": "src/cme_calculator.py", "success": true, "duration_ms": 456}
  ],

  "files_changed": [
    {"file": "src/cme_calculator.py", "operation": "edit", "lines_added": 5, "lines_removed": 2}
  ],

  "test_results": [
    {"test": "test_ca_np_cme_hours", "status": "passed", "duration_ms": 234}
  ],

  "ralph_verdict": "PASS",
  "completion_signal": "BUGFIX_COMPLETE",

  "evidence_refs": ["EVIDENCE-001"],
  "linked_adrs": ["ADR-006"]
}
```

**CLI commands needed:**
```bash
aibrain trace show trace-abc123
aibrain trace list --task TASK-CME-045
aibrain trace analyze trace-abc123    # Show diff between passing/failing
```

---

### 4. Incident Response + Postmortems

**Purpose**: Learn from failures, prevent recurrence.

**Minimal folder structure:**
```
incidents/
├── README.md                  # Incident lifecycle, severity levels
├── INCIDENT_TEMPLATE.md       # Copy for new incidents
├── INC-001-phi-in-logs.md     # Example: PHI leaked to logs
└── ...
```

**Incident lifecycle:**
1. **Detection**: Automated (HIPAA eval fail, trace shows PHI) or manual (user reports bug)
2. **Containment**: Kill-switch if needed, rollback if deployed
3. **Analysis**: Root cause (what failed, why)
4. **Recovery**: Fix + deploy
5. **Postmortem**: What happened, why, how to prevent (add to eval suite, update risk register)

**Severity levels:**
- **P0**: HIPAA violation, data loss, service down
- **P1**: User-blocking bug, security vulnerability
- **P2**: Degraded UX, non-critical bug
- **P3**: Nice-to-fix, low impact

---

### 5. Decision Journal + Assumption Ledger

**Purpose**: Anti-thrashing, capture why decisions were made and assumptions that underpin them.

**Minimal folder structure:**
```
decisions/
├── README.md                   # Decision log format
├── DECISION_TEMPLATE.md        # Copy for new decisions
├── DEC-001-choose-fastapi.md   # Example: Why FastAPI over Flask
└── ...

assumptions/
├── README.md                   # Assumption ledger format
├── ASSUMPTION_TEMPLATE.md      # Copy for new assumptions
├── ASM-001-user-growth-rate.md # Example: "We assume 10% MoM growth"
└── ...
```

**Decision log format:**
```yaml
---
id: DEC-{NUMBER}
date: YYYY-MM-DD
decision: "What we decided"
context: "Why we were deciding this"
options_considered:
  - option: "Option A"
    pros: ["Pro 1", "Pro 2"]
    cons: ["Con 1", "Con 2"]
  - option: "Option B"
    pros: ["Pro 1"]
    cons: ["Con 1"]
evidence: ["EVIDENCE-001", "ADR-006"]
counter_evidence: ["What argued against this"]
revisit_date: YYYY-MM-DD (or "when X happens")
status: [active|superseded|validated]
---

## Decision
We chose [option] because [rationale].

## Revisit Triggers
- If user growth exceeds 100/month → revisit scalability
- If cost exceeds $10K/month → revisit architecture
```

**Assumption ledger format:**
```yaml
---
id: ASM-{NUMBER}
date: YYYY-MM-DD
assumption: "What we're assuming is true"
risk: "What happens if we're wrong"
test: "How we'll validate this"
owner: solo-founder
due_date: YYYY-MM-DD
status: [untested|testing|validated|invalidated]
---

## Assumption
We assume [assumption].

## Test Plan
- Week 1: [test step 1]
- Week 2: [test step 2]
- Success criteria: [what proves this true]
```

---

## HIPAA Compliance Reality (NPRM Context)

### January 2025 HIPAA Security Rule NPRM (Proposed Rule)

**Status**: PROPOSED rule (Notice of Proposed Rulemaking), not yet final law.
**Source**: [HHS HIPAA Security Rule NPRM Fact Sheet](https://www.hhs.gov/hipaa/for-professionals/security/hipaa-security-rule-nprm/factsheet/index.html) | [Federal Register Entry](https://www.federalregister.gov/documents/2025/01/06/2024-30983/hipaa-security-rule-to-strengthen-the-cybersecurity-of-electronic-protected-health-information)

**Key changes proposed:**
- Remove distinction between "required" and "addressable" safeguards
- Strengthen risk analysis and risk management requirements
- Enhance encryption requirements
- Require multifactor authentication (MFA)
- Stricter access controls and monitoring

**Timeline**: Public comment period → final rule (likely 6-12 months) → compliance deadline (likely 12-24 months after final rule).

**What this means for CredentialMate:**
- Start building HIPAA controls now (even though rule isn't final)
- Proposed requirements are directional—final rule will be similar
- Early compliance = competitive advantage (most orgs unprepared)

### PHI Protection Requirements

**What is PHI (Protected Health Information)?**
- Names, license numbers, dates of birth, addresses, SSN, medical record numbers, email addresses (when linked to health info)

**CredentialMate-specific PHI:**
- Provider names, NPI numbers, license numbers, license renewal dates
- CME course completion dates (if linked to provider identity)
- State licensing board correspondence

**What you MUST do:**
1. **No PHI in logs/traces/errors** (automatic PHI detection + sanitization)
2. **Encryption at rest and in transit** (database, S3, API calls, agent-to-agent communication)
3. **Audit trails** (who accessed what PHI, when, why)
4. **Access controls** (role-based, principle of least privilege)
5. **Business Associate Agreements (BAAs)** with LLM providers (OpenAI, Anthropic)

**What you CANNOT do:**
- Log raw API responses that contain provider names/license numbers
- Store PHI in plaintext
- Share PHI with third parties without BAA
- Skip audit logging for PHI access

---

## Implementation Plan (8 Weeks, Realistic for Solo Founder)

### Month 1-2: Foundation + Meta-Agents (8 weeks)

**Week 1: Evidence Repository + PM Agent Foundation**
- Day 1-2: Create `evidence/` directory, templates, CLI commands
- Day 3-4: Implement PM Agent contract (`governance/contracts/product-manager.yaml`)
- Day 5: Implement PM Agent skeleton (`agents/coordinator/product_manager.py`)

**Week 2: Eval Suite (Critical Categories)**
- Day 1: Create `evals/` directory, manifest.yaml
- Day 2: License extraction eval + gold dataset (5 cases: CA, TX, NY, FL, PA)
- Day 3: Deadline calculation eval + gold dataset (10 cases)
- Day 4: HIPAA compliance eval + gold dataset (PHI detection test cases)
- Day 5: CI integration (.github/workflows/evals.yml)

**Week 3: Governance Agent (Compliance + Risk)**
- Day 1-2: Implement Governance Agent contract (`governance/contracts/governance-agent.yaml`)
- Day 3-4: Implement Governance Agent (`agents/coordinator/governance_agent.py`)
  - Risk assessment logic (LOW/MEDIUM/HIGH/CRITICAL)
  - HIPAA eval integration
  - PHI detection (regex + ML-based)
- Day 5: Risk register creation (`governance/risk_register.yaml`)

**Week 4: PM Agent (Full Implementation)**
- Day 1-2: PM pre-task validation logic
  - Read Evidence Repository
  - Check roadmap alignment
  - Validate outcome metrics
- Day 3: PM decision logic (APPROVED/BLOCKED/MODIFIED)
- Day 4: PM weekly discovery ritual
- Day 5: Integration with `autonomous_loop.py` (PM gate)

**Week 5: CMO Agent (Full Implementation)**
- Day 1-2: Implement CMO Agent contract (`governance/contracts/cmo-agent.yaml`)
- Day 3-4: Implement CMO Agent (`agents/coordinator/cmo_agent.py`)
  - Messaging matrix management
  - Experiment backlog
  - Pipeline tracking
- Day 5: Weekly experiment ritual

**Week 6: Tracing System**
- Day 1-2: Trace schema (`observability/trace_schema.py`)
- Day 3: Tracer integration into BaseAgent (`agents/base.py`)
- Day 4: CLI commands (`aibrain trace show/list/analyze`)
- Day 5: Trace-based debugging features

**Week 7: Eval Suite Expansion**
- Day 1: CME rules eval + gold dataset
- Day 2: Notification correctness eval + gold dataset
- Day 3: State variations eval + gold dataset
- Day 4: Specialty rules eval + gold dataset
- Day 5: Regression eval setup

**Week 8: Integration + Testing**
- Day 1-2: Integrate all 3 meta-agents into `autonomous_loop.py`
- Day 3: Test PM/CMO/Governance coordination
- Day 4: Fix conflicts/overlaps
- Day 5: Documentation updates

---

### Month 3: Validation (4 weeks)

**Week 9-10: Run All 3 Meta-Agents**
- PM validates 20+ tasks
- CMO runs 4+ experiments
- Governance gates 10+ high-risk actions

**Week 11: Measure Impact**
- Did PM reduce off-roadmap work? (Target: 0 off-roadmap features)
- Did CMO improve pipeline? (Target: 10+ qualified leads/week)
- Did Governance prevent HIPAA violations? (Target: 100% eval pass rate)

**Week 12: Tune + Expand**
- Fix PM/CMO overlaps (if any)
- Tune risk scoring (reduce false positives)
- Expand eval suite based on evidence captured

---

### Month 4+: Scale (Optional)

**Add CFO Agent if cost becomes issue:**
- Block tasks >$10 without approval
- Track Lambda costs (2.6M invocations/month)
- Monthly budget enforcement

**Add COO Agent if resource allocation becomes bottleneck:**
- Adjust iteration budgets (±50%)
- Pause low-priority tasks when over budget
- Rebalance work queues across projects

**Expand Governance to Organizational Policy:**
- Capability gap detection
- New agent drafting (YAML + Python + PR)
- Team composition analysis

---

## Factory Updates (Agent Routing)

**File**: `agents/factory.py`

```python
COMPLETION_PROMISES = {
    # Existing
    "bugfix": "BUGFIX_COMPLETE",
    "codequality": "CODEQUALITY_COMPLETE",
    "feature": "FEATURE_COMPLETE",
    "test": "TESTS_COMPLETE",
    "admin": "ADR_CREATE_COMPLETE",

    # NEW (v6.0)
    "product_management": "PM_REVIEW_COMPLETE",
    "cmo": "CMO_REVIEW_COMPLETE",
    "governance": "GOVERNANCE_ASSESSMENT_COMPLETE",
}

ITERATION_BUDGETS = {
    # Existing
    "bugfix": 15,
    "codequality": 20,
    "feature": 50,
    "test": 15,
    "admin": 3,

    # NEW (v6.0)
    "product_management": 5,   # PM validation is quick
    "cmo": 5,                  # CMO review is quick
    "governance": 3,           # Risk assessment is quick
}

def create_agent(task_type: str, project_name: str, ...):
    # ... existing agents ...

    # NEW AGENTS (v6.0)
    elif task_type == "product_management":
        from agents.coordinator.product_manager import ProductManagerAgent
        return ProductManagerAgent(adapter, config)
    elif task_type == "cmo":
        from agents.coordinator.cmo_agent import CMOAgent
        return CMOAgent(adapter, config)
    elif task_type == "governance":
        from agents.coordinator.governance_agent import GovernanceAgent
        return GovernanceAgent(adapter, config)
```

---

## Work Queue Extensions (Task Dataclass)

**File**: `tasks/work_queue.py`

```python
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Task:
    # =========================================================================
    # EXISTING FIELDS (v5.7)
    # =========================================================================
    id: str
    description: str
    file: str
    status: TaskStatus
    tests: List[str] = field(default_factory=list)
    type: str = "bugfix"
    # ... other existing fields ...

    # =========================================================================
    # NEW FIELDS (v6.0) - Meta-Coordinator Tracking
    # =========================================================================

    # PM (Product Manager) fields
    pm_validated: Optional[bool] = None
    pm_feedback: Optional[str] = None
    pm_outcome_metrics: Optional[Dict[str, str]] = None  # {"activation_rate": "target 80%"}

    # CMO fields
    cmo_reviewed: Optional[bool] = None
    cmo_experiment_id: Optional[str] = None  # Link to experiment backlog
    cmo_messaging_variant: Optional[str] = None  # A/B test variant

    # Governance fields
    governance_risk_level: Optional[str] = None  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    governance_approved: Optional[bool] = None
    governance_approval_reason: Optional[str] = None

    # Context fields (trigger meta-coordinators)
    affects_user_experience: bool = False
    is_gtm_related: bool = False  # Landing pages, messaging, onboarding
    touches_phi_code: bool = False  # PHI-handling paths

    # Evidence linkage
    evidence_refs: List[str] = field(default_factory=list)  # ["EVIDENCE-001", ...]

    # Cost tracking
    estimated_cost_usd: Optional[float] = None
```

---

## Authoritative Sources

### HIPAA Compliance
- [HHS HIPAA Security Rule NPRM Fact Sheet](https://www.hhs.gov/hipaa/for-professionals/security/hipaa-security-rule-nprm/factsheet/index.html)
- [Federal Register: HIPAA Security Rule NPRM](https://www.federalregister.gov/documents/2025/01/06/2024-30983/hipaa-security-rule-to-strengthen-the-cybersecurity-of-electronic-protected-health-information)

### AI Risk Management
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST AI RMF Core Functions](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
- [OpenAI: Practices for Governing Agentic AI Systems](https://openai.com/index/practices-for-governing-agentic-ai-systems/)
- [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

### Continuous Discovery
- [Continuous Discovery: Getting Started](https://www.producttalk.org/getting-started-with-discovery/) (Teresa Torres)

### Multi-Agent Systems (2025 Research)
- [Multi-AI Agents Systems in 2025: Key Insights](https://ioni.ai/post/multi-ai-agents-in-2025-key-insights-examples-and-challenges)
- [Arthur in 2025: Building Trust for Agentic AI](https://www.arthur.ai/blog/2025-recap)
- [How AI and automation are transforming the COO role | McKinsey](https://www.mckinsey.com/capabilities/operations/our-insights/how-ai-is-redefining-the-coos-role)

---

## Next Steps

1. **Review this V2 document** - Is the PM/CMO/Governance separation clear? Any overlaps?
2. **Approve implementation plan** - 8 weeks realistic? Want to adjust scope/timeline?
3. **Build all 3 agents** - Start with Week 1 (Evidence + PM foundation)

**Ready to proceed with implementation when you are.**

---

**Version**: 2.0
**Last Updated**: 2026-01-10
**Status**: Design Complete, Ready for Implementation
