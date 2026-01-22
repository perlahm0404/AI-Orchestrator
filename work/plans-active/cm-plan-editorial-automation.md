---
title: Editorial Automation System Implementation Plan
scope: cm
type: plan
status: active
created: 2026-01-21
author: Claude
compliance:
  soc2:
    controls:
      - CC6.1
      - CC7.2
  iso27001:
    controls:
      - A.8.1
      - A.14.2
---

# Editorial Automation System - Implementation Plan

## Executive Summary

Build an autonomous editorial agent system that creates SEO/AEO-optimized blog posts for CredentialMate by:
- Researching state board updates via browser automation
- Analyzing competitor content for SEO gaps
- Generating content drafts following proven patterns
- Validating against keyword strategy and factual accuracy (Ralph-style)
- Publishing through human-approved workflow

**Autonomy Level**: L1.5 (between Dev L1 and QA L2)
**Workflow**: Draft → Ralph Check (factual accuracy) → Human Review → Publish
**Location**: /Users/tmac/1_REPOS/AI_Orchestrator/blog/credentialmate/

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    EditorialAgent                               │
│  - Research (browser automation: state boards + competitors)    │
│  - Generate (Claude CLI: content with citations)                │
│  - Validate (ContentValidator: SEO + factual accuracy)          │
│  - Publish (approval gate → production)                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ Browser          │    │ Content          │
│ Automation       │    │ Validator        │
│ (Playwright)     │    │ (Ralph pattern)  │
│                  │    │                  │
│ - State boards   │    │ - SEO checks     │
│ - Competitors    │    │ - Citations      │
│ - SERP analysis  │    │ - Readability    │
└──────────────────┘    └──────────────────┘
```

**Key Design Decisions**:
1. Reuse existing patterns: Inherit from BaseAgent, use AgentConfig, register in factory
2. Browser automation: Extend existing TypeScript/Node.js system with new adapters
3. Content validation: Mirror Ralph's PASS/FAIL/BLOCKED verdict system
4. Multi-stage workflow: Draft → Validation → Review → Publish (similar to Dev Team PR flow)

---

## Critical Files to Implement

### Phase 1: Agent Core (Python)

1. `/Users/tmac/1_REPOS/AI_Orchestrator/agents/editorial/editorial_agent.py` (NEW)
   - Inherit from BaseAgent (execute, checkpoint, halt methods)
   - Initialize with BrowserAutomationClient for research
   - Workflow: research → generate → validate → save draft
   - Completion signal: `<promise>EDITORIAL_COMPLETE</promise>`
   - Iteration budget: 20 (medium-high complexity)

2. `/Users/tmac/1_REPOS/AI_Orchestrator/agents/editorial/__init__.py` (NEW)
   - Export EditorialAgent for factory registration

3. `/Users/tmac/1_REPOS/AI_Orchestrator/agents/factory.py` (MODIFY)
   - Add "editorial" to COMPLETION_PROMISES dict
   - Add "editorial" to ITERATION_BUDGETS dict (20)
   - Add case for "editorial" in create_agent() switch
   - Add "EDITORIAL" and "CONTENT" prefixes to infer_agent_type()

4. `/Users/tmac/1_REPOS/AI_Orchestrator/governance/contracts/editorial.yaml` (NEW)
   - Autonomy level: L1.5
   - Allowed: read/write to .drafts/, browser automation, Ralph validation
   - Forbidden: publish directly, modify published content
   - Requires approval: publish_to_production
   - Limits: max_iterations=20, max_word_count=3000, min_seo_score=50

### Phase 2: Content Validation (Ralph Pattern)

5. `/Users/tmac/1_REPOS/AI_Orchestrator/ralph/checkers/content_checker.py` (NEW)
   - ContentValidator class following existing Ralph checker pattern
   - Checks: markdown syntax, metadata, SEO, links, spelling, citations
   - Return Verdict with PASS/FAIL/BLOCKED semantics
   - SEO scoring: 0-100 based on keyword density, placement, LSI coverage

6. `/Users/tmac/1_REPOS/AI_Orchestrator/ralph/checkers/citation_verifier.py` (NEW)
   - CitationVerifier class using BrowserAutomationClient
   - Verify citations via browser automation (CFR, USC, state statutes)
   - Confidence scoring: 0.0-1.0 based on match quality
   - Return verification results with source URLs

### Phase 3: Browser Automation Extensions (TypeScript)

7. `/Users/tmac/1_REPOS/AI_Orchestrator/packages/browser-automation/src/adapters/regulatory-boards.ts` (NEW)
   - RegulatoryBoardAdapter extending BasePortalAdapter
   - Methods: extractRegulatoryUpdates(), extractDisciplinaryActions()
   - LLM-powered extraction using existing data-extractor.ts
   - Returns structured RegulatoryUpdate[] with confidence scores

8. `/Users/tmac/1_REPOS/AI_Orchestrator/packages/browser-automation/src/adapters/competitor-blogs.ts` (NEW)
   - CompetitorBlogAdapter extending BasePortalAdapter
   - Methods: extractBlogPost(), analyzeSEOMetadata(), extractSiteMap()
   - Returns BlogPost with headings, keywords, SEO metadata
   - Readability extraction using Mozilla Readability algorithm

9. `/Users/tmac/1_REPOS/AI_Orchestrator/packages/browser-automation/src/seo/keyword-validator.ts` (NEW)
   - KeywordValidator class loading keyword-strategy.yaml
   - Methods: validateContent(), checkKeywordDensity(), validatePlacement()
   - Returns ValidationReport with issues, suggestions, SEO score

10. `/Users/tmac/1_REPOS/AI_Orchestrator/packages/browser-automation/src/cli.ts` (MODIFY)
    - Add commands: scrape-regulatory-updates, analyze-competitors, validate-keywords
    - Add cases to executeCommand() switch statement

11. `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/browser_automation/client.py` (MODIFY)
    - Add methods: scrape_regulatory_updates(), analyze_competitors(), validate_keywords()
    - Python wrappers calling TypeScript CLI via subprocess

### Phase 4: Workflow & Approval

12. `/Users/tmac/1_REPOS/AI_Orchestrator/orchestration/content_pipeline.py` (NEW)
    - ContentPipeline class managing multi-stage workflow
    - Stages: draft → validation → review → publish
    - Integration with stop_hook for approval gates
    - Handles stage transitions and rejection flow

13. `/Users/tmac/1_REPOS/AI_Orchestrator/orchestration/content_approval.py` (NEW)
    - Approval gate display (validation summary, preview, SEO score)
    - Prompt: [A]pprove / [R]eject / [M]odify
    - Log decisions to .aibrain/content-approvals.jsonl
    - Return ApprovalDecision dataclass

### Phase 5: Configuration & Data

14. `/Users/tmac/1_REPOS/AI_Orchestrator/knowledge/seo/keyword-strategy.yaml` (NEW)
    - Master keyword strategy for CredentialMate
    - Primary/secondary/long-tail keywords with target density
    - LSI terms, placement rules, content guidelines

15. `/Users/tmac/1_REPOS/AI_Orchestrator/blog/credentialmate/` directory structure (NEW)
    ```
    blog/credentialmate/
    ├── drafts/              # Agent writes here
    ├── published/           # Production content (read-only for agent)
    ├── strategy/
    │   └── keywords.yaml    # SEO strategy (symlink to knowledge/seo/)
    └── templates/           # Content templates
    ```

16. `/Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_credentialmate_editorial.json` (NEW)
    - Work queue for editorial tasks
    - Task format: EDITORIAL-{CATEGORY}-{TOPIC}-{SEQUENCE}
    - Fields: editorial_spec with keywords, research_sources, target_audience

---

## Implementation Steps

### Step 1: Agent Foundation
1. Create agents/editorial/ directory
2. Implement editorial_agent.py inheriting from BaseAgent
3. Add factory registration in agents/factory.py
4. Create governance contract governance/contracts/editorial.yaml
5. Test agent instantiation

### Step 2: Content Validation
1. Create ralph/checkers/content_checker.py
2. Implement ContentValidator with 8 checks (markdown, SEO, links, etc.)
3. Create ralph/checkers/citation_verifier.py
4. Test validation

### Step 3: Browser Automation - TypeScript
1. Create packages/browser-automation/src/adapters/regulatory-boards.ts
2. Create packages/browser-automation/src/adapters/competitor-blogs.ts
3. Create packages/browser-automation/src/seo/keyword-validator.ts
4. Add CLI commands in src/cli.ts
5. Build TypeScript
6. Test CLI

### Step 4: Browser Automation - Python Client
1. Add methods to adapters/browser_automation/client.py
2. Test Python→TypeScript bridge

### Step 5: Workflow Pipeline
1. Create orchestration/content_pipeline.py
2. Create orchestration/content_approval.py
3. Integrate with existing IterationLoop and stop_hook
4. Test workflow

### Step 6: Configuration & Data Setup
1. Create knowledge/seo/keyword-strategy.yaml
2. Create blog/credentialmate/ directory structure
3. Create sample editorial task in work queue
4. Test task parsing

### Step 7: End-to-End Integration
1. Add editorial task to work queue
2. Run autonomous loop
3. Verify workflow: Draft created → Validation runs → Approval prompt → Publish on approval
4. Check outputs

---

## Verification Strategy

### Unit Tests
- tests/agents/test_editorial_agent.py - Agent initialization, task parsing
- tests/ralph/test_content_checker.py - Validation checks return correct verdicts
- tests/browser_automation/test_regulatory_adapter.py - Scraping returns structured data

### Integration Tests
- tests/integration/test_editorial_workflow.py - Full pipeline: research → generate → validate → approve
- tests/integration/test_browser_automation_editorial.py - Python↔TypeScript communication

### Success Criteria
- ✅ Agent completes research phase without errors
- ✅ Draft content has ≥50 SEO score
- ✅ All citations verified with confidence ≥0.7
- ✅ Approval gate shows validation summary
- ✅ Published content copied to production directory
- ✅ Audit log records approval decision

---

## Risks & Mitigations

### Risk 1: Browser Scraping Blocked by Anti-Bot
**Mitigation**: Rate limiting, rotating user agents, fallback to API providers, caching

### Risk 2: SEO Strategy Changes
**Mitigation**: Strategy in YAML file, validator loads at runtime, version control

### Risk 3: Citation Verification Failures
**Mitigation**: Confidence scoring, allow low-confidence with human review, manual verification fallback

### Risk 4: Approval Bottleneck
**Mitigation**: Auto-approve if SEO ≥80 and citations verified, draft queue for batch review
