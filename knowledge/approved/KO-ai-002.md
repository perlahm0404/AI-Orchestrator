---
{
  "id": "KO-ai-002",
  "project": "ai-orchestrator",
  "title": "Council Decision: AI Agent Team Setup (2026 Best Practices vs AI-Agency-Agents)",
  "what_was_learned": "Council debate on 'Which approach should we adopt for AI agent team setup: 2026 Best Practices (claude-mem + TeammateTool) or AI-Agency-Agents Orchestration Repo (custom orchestration + Ralph)?' reached a CONDITIONAL recommendation with 46.8% confidence.\n\nVote breakdown:\n  - SUPPORT: 2 agents (Integration 75%, Cost 80%)\n  - OPPOSE: 1 agent (Security 80%)\n  - NEUTRAL: 2 agents (Alternatives 85%, Performance 70%)\n\nKey findings:\n  - Cost: Approach A has significantly lower total cost of ownership (1-3 days setup vs 1-2 weeks)\n  - Integration: Approach A offers lower integration complexity (native Claude Code features vs custom layer)\n  - Security: Approach B provides superior compliance and audit trails (HIPAA/SOC2)\n  - Memory sustainability: A=7/10 (3-5 session retention), B=9.5/10 (infinite retention), Hybrid=9/10\n  - Recommendation: Context-dependent choice - A for new projects, B for enterprise, Hybrid for most teams",
  "why_it_matters": "This council decision provides evidence-based guidance for choosing AI agent team architecture. The CONDITIONAL recommendation (not ADOPT or REJECT) indicates that both approaches have merit depending on context.\n\nMemory sustainability emerged as a critical differentiator: Approach A's claude-mem plugin retains only 3-5 sessions (70% recovery), while Approach B's work_queue.json provides infinite retention (95% recovery).\n\nThe hybrid approach balances both: start with A for speed, add B's work_queue for long-term memory, achieving 90-95% recovery.\n\nDebate cost: $1.95 (under $2.00 budget)",
  "prevention_rule": "Before making decisions about AI agent team setup (claude-mem vs work_queue, session-level vs system-of-record memory), consult this council decision.\n\nKey decision criteria:\n  1. Project timeline: <3 months → A, 3-12 months → Hybrid, 1+ years → B\n  2. Compliance needs: HIPAA/SOC2 required → B (audit trails essential)\n  3. Memory requirements: 70% recovery OK → A, 95% recovery needed → B or Hybrid\n  4. Team size: Solo → A, <5 → Hybrid, >10 → B\n  5. Repository structure: Single repo → A, Multi-repo enterprise → B\n\nAvoid: Starting with A if compliance/audit trails are required (memory gaps unacceptable)",
  "tags": [
    "council",
    "conditional",
    "debate",
    "architecture",
    "memory-sustainability",
    "ai-agent-team",
    "claude-mem",
    "work-queue",
    "2026-best-practices",
    "orchestration",
    "hybrid-approach"
  ],
  "status": "approved",
  "created_at": "2026-02-05T20:57:18.025345",
  "approved_at": "2026-02-06T03:26:30.000000",
  "detection_pattern": "ai.agent.team|claude.mem|work.queue|orchestration.repo|memory.sustainability",
  "file_patterns": [
    ".claude/CLAUDE.md",
    "orchestration/queue/work_queue*.json",
    "sessions/*/active/*council-debate*.md",
    "sessions/*/active/*memory-sustainability*.md"
  ]
}
---

# Council Decision: AI Agent Team Setup (2026 Best Practices vs AI-Agency-Agents)

## What Was Learned

Council debate on 'Which approach should we adopt for AI agent team setup: 2026 Best Practices (claude-mem + TeammateTool) or AI-Agency-Agents Orchestration Repo (custom orchestration + Ralph)?' reached a **CONDITIONAL recommendation** with 46.8% confidence.

### Vote Breakdown
- **SUPPORT (Approach A)**: 2 agents
  - Integration Analyst (75% confidence): Lower complexity, 1-3 days setup
  - Cost Analyst (80% confidence): Lower TCO, zero custom infrastructure
- **OPPOSE (Approach A)**: 1 agent
  - Security Analyst (80% confidence): B has superior compliance, audit trails
- **NEUTRAL**: 2 agents
  - Alternatives Analyst (85% confidence): Hybrid approach recommended
  - Performance Analyst (70% confidence): Context-dependent performance

### Key Findings

**Approach A (2026 Best Practices)**:
- Setup: 1-3 days
- Memory: claude-mem plugin (auto-capture, 3-5 session retention)
- Recovery: 70% after compression/restart
- Best for: New projects, small teams, non-regulated environments

**Approach B (AI-Agency-Agents Orchestration Repo)**:
- Setup: 1-2 weeks
- Memory: work_queue.json (system-of-record, infinite retention)
- Recovery: 95% after compression/restart
- Best for: Enterprise, HIPAA/SOC2, multi-repo, long-term projects

**Hybrid (Recommended for Most)**:
- Phase 1: Start with A (fast iteration)
- Phase 2: Add work_queue.json (long-term memory)
- Phase 3: Add Ralph verifier (quality gates)
- Recovery: 90-95%

### Critical Discovery: Memory Sustainability

Memory sustainability emerged as the **major differentiator**:

| Approach | Retention | Recovery | Score |
|----------|-----------|----------|-------|
| A (2026 Best Practices) | 3-5 sessions | 70% | 7/10 |
| B (AI-Agency-Agents) | Infinite | 95% | 9.5/10 |
| Hybrid | Infinite | 90-95% | 9/10 |
| B→A (Reverse) | Infinite | 95% | 9.5/10 |

**The Pruning Problem**: claude-mem keeps only last 3-5 sessions, older context is **permanently lost**.

**The work_queue Advantage**: Permanent system-of-record, never pruned, task-level granularity.

## Why It Matters

This council decision provides **evidence-based guidance** for choosing AI agent team architecture based on:
1. Project timeline and maturity
2. Compliance requirements (HIPAA, SOC2, audit trails)
3. Memory sustainability needs (70% vs 95% recovery)
4. Team size and repository structure
5. Development workflow (interactive vs autonomous)

The **CONDITIONAL recommendation** (not ADOPT or REJECT) indicates that both approaches have merit depending on context. The hybrid approach emerged as the optimal path for most teams.

### Real-World Impact

**AI Orchestrator (this repo)** uses Approach B architecture:
- STATE.md + work_queue.json + Knowledge Objects + Ralph
- 95%+ context recovery proven over 6+ months
- We learned the hard way that session-level memory (like A) isn't enough for complex systems

**CredentialMate (HIPAA)** should migrate to Approach B:
- Current: Hybrid-lite (8/10 sustainability)
- Target: Full B (9.5/10 sustainability)
- Reason: Compliance requires complete audit trails

Debate cost: $1.95 (under $2.00 budget)

## Prevention Rule

**Before making decisions about AI agent team setup**, consult this council decision.

### Decision Criteria Matrix

| Context | Recommended Approach | Rationale |
|---------|---------------------|-----------|
| **New project (<3 months)** | **A** (2026 Best Practices) | Fast setup, 70% recovery sufficient for early stage |
| **Growing project (3-12 months)** | **Hybrid** | Need long-term memory but retain dev velocity |
| **Mature project (1+ years)** | **B** or **Hybrid** | Institutional memory critical |
| **HIPAA/SOC2 required** | **B** | Audit trails non-negotiable |
| **Multi-repo enterprise** | **B** | Formal orchestration required |
| **Solo developer** | **A** | Low overhead, fast iteration |
| **Small team (<5)** | **Hybrid** | Balance convenience + permanence |
| **Large team (>10)** | **B** | System-of-record for coordination |

### Migration Paths

**A→B (Progressive Enhancement)**:
```
Month 1-3:   Approach A (70% recovery)
Month 4-6:   + work_queue.json (85% recovery)
Month 7-12:  + Ralph verifier (90% recovery)
Year 2+:     Full B if needed (95% recovery)
```

**B→A (Foundation First - Recommended for Enterprise)**:
```
Week 1-2:    Approach B core (95% recovery immediately)
Month 2-3:   + Evals/telemetry (95% recovery)
Month 4+:    + claude-mem (optional convenience, still 95% recovery)
```

### Anti-Patterns to Avoid

1. **❌ Starting with A if compliance required**: Memory gaps create audit trail holes
2. **❌ Never migrating from A to B**: Stuck at 70% recovery (technical debt)
3. **❌ Trusting 3-5 session retention for long-term projects**: Institutional memory degrades
4. **❌ Over-engineering with B for prototypes**: Wasted effort if project abandoned

### When to Reconsult

- Starting a new AI agent project
- Evaluating claude-mem plugin adoption
- Choosing between session-level vs system-of-record memory
- Planning multi-repo agent coordination
- Preparing for HIPAA/SOC2 audit
- Migrating from manual STATE.md to formal work queue
- Experiencing memory loss after session compression

## Tags

council, conditional, debate, architecture, memory-sustainability, ai-agent-team, claude-mem, work-queue, 2026-best-practices, orchestration, hybrid-approach

## Detection Pattern

```regex
ai.agent.team|claude.mem|work.queue|orchestration.repo|memory.sustainability
```

## File Patterns

- `.claude/CLAUDE.md` (agent team configuration)
- `orchestration/queue/work_queue*.json` (system-of-record)
- `sessions/*/active/*council-debate*.md` (debate documentation)
- `sessions/*/active/*memory-sustainability*.md` (memory analysis)

---

**Status**: approved
**Project**: ai-orchestrator
**Created**: 2026-02-05T20:57:18.025345
**Approved**: 2026-02-06T03:26:30.000000
**Council ID**: COUNCIL-20260206-025717
**Debate Cost**: $1.95
**Confidence**: 46.8%
**Recommendation**: CONDITIONAL (context-dependent)

---

## Related Documents

- Council Debate Summary: `sessions/ai-orchestrator/active/20260205-council-debate-implementation-summary.md`
- Memory Sustainability Analysis: `sessions/ai-orchestrator/active/20260206-memory-sustainability-comparison-2026-vs-v2.md`
- Reverse Hybrid (B→A): `sessions/ai-orchestrator/active/20260206-reverse-hybrid-analysis-B-then-A.md`
- Debate Manifest: `.aibrain/councils/COUNCIL-20260206-025717/manifest.jsonl`
- Memory Strategy Guide: `docs/17-governance/memory-sustainability-strategy.md`
