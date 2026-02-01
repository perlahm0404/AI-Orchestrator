---
title: Repository Assessment Rubric - Agent Swarm Ecosystem
scope: cross-repo
type: assessment
status: complete
created: 2026-01-31
author: Claude
compliance:
  soc2:
    controls:
      - CC6.1
  iso27001:
    controls:
      - A.8.1
---

# Repository Assessment Rubric: Agent Swarm Ecosystem

**Date**: 2026-01-31
**Purpose**: Evaluate 9 repositories for keep/consolidate/archive decisions
**Author**: AI Orchestrator Assessment

---

## Table of Contents

1. [Assessment Rubric Matrix](#1-assessment-rubric-matrix)
2. [Individual Repository Scores](#2-individual-repository-scores)
3. [Overlap Analysis](#3-overlap-analysis)
4. [Consolidation Recommendations](#4-consolidation-recommendations)
5. [Usage Guide](#5-usage-guide)
6. [Strengths & Weaknesses](#6-strengths--weaknesses)

---

## 1. Assessment Rubric Matrix

### Scoring Dimensions

| Dimension | Weight | 1 (Poor) | 3 (Adequate) | 5 (Excellent) |
|-----------|--------|----------|--------------|---------------|
| **Strategic Value** | 25% | Nice-to-have, no clear goal alignment | Supports goals indirectly | Core to personal/professional mission |
| **Uniqueness** | 20% | Duplicates existing capabilities | Partially unique features | Irreplaceable, one-of-a-kind |
| **Maturity** | 15% | Prototype, broken, undocumented | Functional but rough edges | Production-ready, stable, documented |
| **Active Use** | 15% | Unused for 6+ months | Occasional use (monthly) | Daily/weekly active use |
| **Maintenance Burden** | 10% | High cost, frequent breakage | Moderate upkeep needed | Self-maintaining, stable deps |
| **Integration Potential** | 10% | Standalone, no connections | Can integrate with 1-2 repos | Hub connecting multiple repos |
| **Learning Value** | 5% | No educational benefit | Some reference patterns | Rich learning resource |

### Scoring Formula

```
Final Score = Σ(Dimension Score × Weight)
```

### Decision Thresholds

| Score Range | Decision | Action |
|-------------|----------|--------|
| **4.0 - 5.0** | **KEEP** | Active maintenance, priority investment |
| **3.0 - 3.9** | **MONITOR** | Keep but evaluate quarterly |
| **2.0 - 2.9** | **CONSOLIDATE** | Merge into another repo or simplify |
| **1.0 - 1.9** | **ARCHIVE** | Read-only, no active development |

---

## 2. Individual Repository Scores

### Summary Table

| Repository | Strategic | Unique | Mature | Active | Maint | Integrate | Learn | **Weighted** | **Decision** |
|------------|-----------|--------|--------|--------|-------|-----------|-------|--------------|--------------|
| AI_Orchestrator | 5 | 5 | 4 | 5 | 3 | 5 | 4 | **4.55** | KEEP |
| clawdbot | 5 | 5 | 5 | 5 | 3 | 4 | 3 | **4.55** | KEEP |
| ResearchAgent | 5 | 4 | 4 | 4 | 4 | 4 | 4 | **4.30** | KEEP |
| MissionControl | 4 | 5 | 4 | 4 | 5 | 5 | 3 | **4.30** | KEEP |
| craft-agents-oss | 4 | 4 | 4 | 4 | 3 | 4 | 4 | **3.90** | MONITOR |
| agent-browser | 3 | 4 | 5 | 3 | 5 | 3 | 3 | **3.55** | MONITOR |
| BlogPublisher | 4 | 3 | 3 | 3 | 3 | 4 | 3 | **3.40** | MONITOR |
| notebooklm-cli | 3 | 4 | 3 | 2 | 3 | 3 | 4 | **3.05** | MONITOR |
| awesome-llm-apps | 2 | 2 | 4 | 2 | 5 | 1 | 5 | **2.55** | CONSOLIDATE |

### Detailed Scoring Rationale

---

#### AI_Orchestrator (Score: 4.55) ⭐ KEEP

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Strategic Value | 5 | Core autonomous agent system, enables all other work |
| Uniqueness | 5 | Only repo with Ralph verification, Wiggum control, governance contracts |
| Maturity | 4 | v6.0 production, 91% autonomy, but still evolving |
| Active Use | 5 | Daily use, primary development environment |
| Maintenance Burden | 3 | Moderate - complex system requires ongoing attention |
| Integration Potential | 5 | Hub connecting MissionControl, target apps, all agents |
| Learning Value | 4 | Rich patterns for autonomous systems |

**Role**: Execution engine for the entire agent swarm

---

#### clawdbot (Score: 4.55) ⭐ KEEP

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Strategic Value | 5 | Primary human-AI interface, multi-channel access |
| Uniqueness | 5 | Only multi-platform messaging gateway (WhatsApp, Telegram, Slack, etc.) |
| Maturity | 5 | 100+ releases, production-grade, extensive features |
| Active Use | 5 | Daily messaging interface |
| Maintenance Burden | 3 | Multi-platform means multiple integration points |
| Integration Potential | 4 | Connects to agent-browser, can invoke other agents |
| Learning Value | 3 | Good TypeScript/messaging patterns |

**Role**: Human-facing messaging gateway to AI capabilities

---

#### ResearchAgent (Score: 4.30) ⭐ KEEP

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Strategic Value | 5 | Personal knowledge platform, content generation |
| Uniqueness | 4 | Unique RAG + SEO combo, but overlaps with some LLM patterns |
| Maturity | 4 | v1.0 released, stable, documented |
| Active Use | 4 | Regular use for research and content |
| Maintenance Burden | 4 | Clean architecture, manageable deps |
| Integration Potential | 4 | Pairs with BlogPublisher, uses MCP |
| Learning Value | 4 | Good RAG/vector patterns |

**Role**: Knowledge synthesis and content generation engine

---

#### MissionControl (Score: 4.30) ⭐ KEEP

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Strategic Value | 4 | Constitutional layer, but value tied to AI_Orchestrator |
| Uniqueness | 5 | Only governance/policy repository, SSOT |
| Maturity | 4 | Framework complete, ongoing policy evolution |
| Active Use | 4 | Referenced by AI_Orchestrator sessions |
| Maintenance Burden | 5 | Just YAML/Markdown, minimal breakage risk |
| Integration Potential | 5 | Designed to govern all repos |
| Learning Value | 3 | Good governance patterns |

**Role**: Constitutional authority and policy definitions

---

#### craft-agents-oss (Score: 3.90) ⚠️ MONITOR

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Strategic Value | 4 | Desktop agent IDE, valuable for document work |
| Uniqueness | 4 | Unique multi-session Electron UI |
| Maturity | 4 | v0.2.29, stable, regular releases |
| Active Use | 4 | Used for document-centric agent work |
| Maintenance Burden | 3 | Electron apps require dependency vigilance |
| Integration Potential | 4 | MCP integration, can connect to services |
| Learning Value | 4 | Good Electron + React patterns |

**Watch**: Evaluate overlap with Claude desktop apps as they evolve

---

#### agent-browser (Score: 3.55) ⚠️ MONITOR

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Strategic Value | 3 | Useful utility but not core to mission |
| Uniqueness | 4 | Solid browser automation, though alternatives exist |
| Maturity | 5 | v0.6.0, Vercel Labs quality, well-documented |
| Active Use | 3 | Occasional use, not daily driver |
| Maintenance Burden | 5 | Upstream maintained by Vercel |
| Integration Potential | 3 | Can be used by clawdbot/agents |
| Learning Value | 3 | Good Playwright patterns |

**Watch**: May be replaceable by built-in MCP browser tools

---

#### BlogPublisher (Score: 3.40) ⚠️ MONITOR

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Strategic Value | 4 | Content distribution is valuable |
| Uniqueness | 3 | Multi-platform publishing, but common pattern |
| Maturity | 3 | v1.0 alpha, functional but rough |
| Active Use | 3 | Occasional use for blog posts |
| Maintenance Burden | 3 | API integrations require upkeep |
| Integration Potential | 4 | Designed to pair with ResearchAgent |
| Learning Value | 3 | FastAPI patterns |

**Watch**: Consider merging into ResearchAgent as publishing module

---

#### notebooklm-cli (Score: 3.05) ⚠️ MONITOR

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Strategic Value | 3 | Useful for NotebookLM access |
| Uniqueness | 4 | Only CLI for NotebookLM (unofficial) |
| Maturity | 3 | v0.1.12 beta, uses undocumented APIs |
| Active Use | 2 | Infrequent use |
| Maintenance Burden | 3 | Risk of API changes breaking it |
| Integration Potential | 3 | Can feed ResearchAgent |
| Learning Value | 4 | Interesting reverse-engineering patterns |

**Watch**: May become obsolete if Google releases official API

---

#### awesome-llm-apps (Score: 2.55) 🔄 CONSOLIDATE

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Strategic Value | 2 | Reference only, not active development |
| Uniqueness | 2 | Third-party repo, not custom work |
| Maturity | 4 | Well-maintained by community |
| Active Use | 2 | Rarely consulted |
| Maintenance Burden | 5 | Just a fork, no maintenance needed |
| Integration Potential | 1 | No integration, standalone reference |
| Learning Value | 5 | Rich educational resource |

**Action**: Archive or delete local fork; reference upstream directly

---

## 3. Overlap Analysis

### Functional Overlap Matrix

| Repos | Overlap Area | Severity | Resolution |
|-------|--------------|----------|------------|
| AI_Orchestrator ↔ MissionControl | Governance | **Low** | Complementary: Execution vs Constitution |
| BlogPublisher ↔ ResearchAgent | Content Pipeline | **Medium** | Keep paired OR merge BlogPublisher into ResearchAgent |
| clawdbot ↔ craft-agents-oss | Agent UI | **Low** | Different channels: messaging vs desktop |
| agent-browser ↔ clawdbot | Browser Control | **Low** | agent-browser is utility, clawdbot is gateway |
| ResearchAgent ↔ notebooklm-cli | Knowledge Tools | **Low** | Different sources: RAG vs NotebookLM |

### Integration Dependency Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MissionControl                               │
│                    (Constitutional Authority)                        │
│                              │                                       │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     AI_Orchestrator                          │   │
│  │                  (Execution Engine)                          │   │
│  │                         │                                    │   │
│  │     ┌───────────────────┼───────────────────┐                │   │
│  │     ▼                   ▼                   ▼                │   │
│  │ ┌─────────┐      ┌─────────────┐     ┌───────────┐          │   │
│  │ │clawdbot │      │craft-agents │     │ResearchAgt│          │   │
│  │ │(Gateway)│      │  (Desktop)  │     │   (RAG)   │          │   │
│  │ └────┬────┘      └─────────────┘     └─────┬─────┘          │   │
│  │      │                                     │                 │   │
│  │      ▼                                     ▼                 │   │
│  │ ┌──────────────┐                   ┌─────────────┐          │   │
│  │ │agent-browser │                   │BlogPublisher│          │   │
│  │ │  (Utility)   │                   │ (Publish)   │          │   │
│  │ └──────────────┘                   └─────────────┘          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Standalone/Reference:                                               │
│  ┌────────────────┐  ┌─────────────────┐                            │
│  │ notebooklm-cli │  │ awesome-llm-apps│                            │
│  │   (Utility)    │  │   (Reference)   │                            │
│  └────────────────┘  └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Consolidation Recommendations

### Immediate Actions

| Action | Repository | Rationale |
|--------|------------|-----------|
| ✅ **KEEP** | AI_Orchestrator | Core execution engine, irreplaceable |
| ✅ **KEEP** | clawdbot | Primary messaging gateway, high maturity |
| ✅ **KEEP** | ResearchAgent | Unique RAG platform, active use |
| ✅ **KEEP** | MissionControl | Governance layer, lightweight |

### Monitor & Evaluate (Quarterly)

| Action | Repository | Trigger for Change |
|--------|------------|-------------------|
| ⚠️ **MONITOR** | craft-agents-oss | If Claude desktop improves, may become redundant |
| ⚠️ **MONITOR** | agent-browser | If MCP browser tools mature, may archive |
| ⚠️ **MONITOR** | BlogPublisher | Consider merging into ResearchAgent |
| ⚠️ **MONITOR** | notebooklm-cli | If Google releases official API, archive |

### Archive/Consolidate

| Action | Repository | Recommendation |
|--------|------------|----------------|
| 🔄 **ARCHIVE** | awesome-llm-apps | Delete local fork, bookmark upstream URL |

### Potential Future Mergers

| Merge Candidate | Into | When |
|-----------------|------|------|
| BlogPublisher | ResearchAgent | When content pipeline is proven stable |
| notebooklm-cli | ResearchAgent | If used primarily for feeding RAG |

---

## 5. Usage Guide

### Decision Tree: Which Repo Do I Need?

```
Start
  │
  ├─► Need to run autonomous agents?
  │     └─► AI_Orchestrator
  │
  ├─► Need governance/policy definitions?
  │     └─► MissionControl
  │
  ├─► Need to chat with AI via messaging apps?
  │     └─► clawdbot (WhatsApp, Telegram, Slack, etc.)
  │
  ├─► Need to do document-focused agent work?
  │     └─► craft-agents-oss (desktop app)
  │
  ├─► Need to research/synthesize knowledge?
  │     └─► ResearchAgent (RAG + web search)
  │
  ├─► Need to publish content to platforms?
  │     └─► BlogPublisher (LinkedIn, Twitter, Substack)
  │
  ├─► Need programmatic browser control?
  │     └─► agent-browser (CLI)
  │
  ├─► Need NotebookLM features via CLI?
  │     └─► notebooklm-cli (unofficial)
  │
  └─► Need LLM code examples/tutorials?
        └─► awesome-llm-apps (upstream GitHub)
```

### Common Workflows

| Workflow | Repos Involved | Flow |
|----------|----------------|------|
| **Autonomous Bug Fixing** | AI_Orchestrator + MissionControl | Orchestrator executes, MissionControl governs |
| **Research to Blog** | ResearchAgent → BlogPublisher | Research generates, Publisher distributes |
| **Multi-Channel AI Chat** | clawdbot + agent-browser | clawdbot receives, agent-browser browses |
| **Document Analysis** | craft-agents-oss + ResearchAgent | Desktop UI ingests, ResearchAgent indexes |

---

## 6. Strengths & Weaknesses

### AI_Orchestrator

| Strengths | Weaknesses |
|-----------|------------|
| ✅ Core autonomous execution engine | ⚠️ Complex architecture, learning curve |
| ✅ Ralph verification, governance contracts | ⚠️ Tightly coupled to Python ecosystem |
| ✅ 91% autonomy achieved | ⚠️ Documentation scattered across files |
| ✅ Cross-repo memory continuity | |

### clawdbot

| Strengths | Weaknesses |
|-----------|------------|
| ✅ Multi-platform (WhatsApp, Telegram, Slack, etc.) | ⚠️ Many integrations = many failure points |
| ✅ Production-grade, 100+ releases | ⚠️ Node.js 22 requirement |
| ✅ Skills platform, voice wake, canvas UI | ⚠️ Platform-specific quirks |
| ✅ Remote gateway support | |

### ResearchAgent

| Strengths | Weaknesses |
|-----------|------------|
| ✅ Zero LLM cost (uses Claude.ai) | ⚠️ Depends on Claude.ai availability |
| ✅ RAG + SEO/AEO content generation | ⚠️ Setup complexity (PostgreSQL + pgvector) |
| ✅ MCP integration | ⚠️ Single-user focused |
| ✅ Perplexity + NotebookLM style outputs | |

### MissionControl

| Strengths | Weaknesses |
|-----------|------------|
| ✅ Single Source of Truth (SSOT) | ⚠️ Value dependent on AI_Orchestrator |
| ✅ Minimal maintenance (YAML/Markdown) | ⚠️ Governance without enforcement is just docs |
| ✅ Clear policy structure | ⚠️ Can drift from actual implementation |

### craft-agents-oss

| Strengths | Weaknesses |
|-----------|------------|
| ✅ Multi-session desktop IDE | ⚠️ Electron overhead |
| ✅ MCP integration (32+ tools) | ⚠️ May overlap with Claude desktop |
| ✅ Document-centric workflow | ⚠️ OSS sync from internal repo |

### agent-browser

| Strengths | Weaknesses |
|-----------|------------|
| ✅ Vercel Labs quality, well-maintained | ⚠️ Not core to mission |
| ✅ Serverless-ready, streaming | ⚠️ Alternatives emerging (MCP browser) |
| ✅ Semantic locators, snapshot refs | |

### BlogPublisher

| Strengths | Weaknesses |
|-----------|------------|
| ✅ Multi-platform publishing | ⚠️ Alpha maturity |
| ✅ Pairs with ResearchAgent | ⚠️ API maintenance burden |
| ✅ MCP integration | ⚠️ Could be a module, not a repo |

### notebooklm-cli

| Strengths | Weaknesses |
|-----------|------------|
| ✅ Unique NotebookLM access | ⚠️ Unofficial, uses undocumented APIs |
| ✅ Rich feature set (podcasts, quizzes, etc.) | ⚠️ Risk of Google breaking it |
| ✅ Good reverse-engineering example | ⚠️ Low active use |

### awesome-llm-apps

| Strengths | Weaknesses |
|-----------|------------|
| ✅ Rich educational resource | ⚠️ Third-party, not custom work |
| ✅ 50+ projects, many frameworks | ⚠️ No integration potential |
| ✅ Zero maintenance (upstream) | ⚠️ Local fork unnecessary |

---

## Appendix: Repository Quick Reference

| Repository | Path | Version | Primary Language |
|------------|------|---------|------------------|
| AI_Orchestrator | `/Users/tmac/1_REPOS/AI_Orchestrator` | v6.0 | Python |
| clawdbot | `/Users/tmac/1_REPOS/clawdbot` | 2026.1.24-3 | TypeScript |
| ResearchAgent | `/Users/tmac/1_REPOS/ResearchAgent` | v1.0 | Python |
| MissionControl | `/Users/tmac/1_REPOS/MissionControl` | - | YAML/Markdown |
| craft-agents-oss | `/Users/tmac/1_REPOS/craft-agents-oss` | v0.2.29 | TypeScript |
| agent-browser | `/Users/tmac/1_REPOS/agent-browser` | v0.6.0 | TypeScript/Rust |
| BlogPublisher | `/Users/tmac/1_REPOS/BlogPublisher` | v1.0-alpha | Python |
| notebooklm-cli | `/Users/tmac/1_REPOS/notebooklm-cli` | v0.1.12 | Python |
| awesome-llm-apps | `/Users/tmac/1_REPOS/awesome-llm-apps` | - | Mixed |

---

*Generated by AI_Orchestrator Assessment System*
