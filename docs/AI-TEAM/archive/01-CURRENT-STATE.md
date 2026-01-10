# Current State Analysis: Three Repositories

**Date**: 2026-01-09
**Purpose**: Understand existing architecture before designing unified AI Team

---

## Repository Summary

| Repo | Purpose | Agent Model | Governance | Autonomy |
|------|---------|-------------|------------|----------|
| **AI_Orchestrator** | Multi-agent orchestration framework | Contract-based autonomous agents | YAML contracts + Ralph | 89% (L1-L2) |
| **CredentialMate** | HIPAA credential tracking | Synced agents + HIPAA extensions | Contracts + HIPAA guardrails | L1 (strict) |
| **KareMatch** | Healthcare marketplace | Skill-based interactive | Golden paths + RIS system | L0-L4 graduated |

---

## AI_Orchestrator (Framework Source)

**Location**: `/Users/tmac/1_REPOS/AI_Orchestrator`

### Agent Architecture

```
agents/
├── base.py              # BaseAgent abstract class
├── factory.py           # Agent creation factory
├── bugfix.py            # BugFixAgent (L2, 15 iterations)
├── codequality.py       # CodeQualityAgent (L2, 20 iterations)
├── featurebuilder.py    # FeatureBuilderAgent (L1, 50 iterations)
├── testwriter.py        # TestWriterAgent (L1, 15 iterations)
└── self_correct.py      # Self-correction logic
```

**Key Patterns**:
- **Stateless execution**: No persistent memory between sessions
- **External memory**: Git, work queues, Knowledge Objects, session handoffs
- **Completion signals**: `<promise>COMPLETE</promise>` tags
- **Iteration budgets**: 15-50 retries per agent type

### Governance

```
governance/
├── contracts/
│   ├── qa-team.yaml      # BugFix, CodeQuality (L2 - higher autonomy)
│   ├── dev-team.yaml     # FeatureBuilder, TestWriter (L1 - stricter)
│   └── infra-team.yaml   # Infrastructure (L0 - most restrictive)
├── contract.py           # Contract loader & enforcer
├── hooks/stop_hook.py    # Wiggum iteration control
└── kill_switch.py        # Emergency stop modes
```

**Contract Structure**:
```yaml
agent: bugfix
version: "1.0"
autonomy_level: L2
allowed_actions: [read_file, write_file, run_tests]
forbidden_actions: [modify_migrations, push_to_main, deploy]
requires_approval: [merge_pr]
limits:
  max_iterations: 15
  max_lines_added: 100
  max_files_changed: 5
```

### Verification (Ralph-Wiggum)

**Ralph** = Quality gates (PASS/FAIL/BLOCKED)
**Wiggum** = Iteration control (manages loops)

```
Agent completes iteration → Stop Hook evaluates:
  ├─→ Completion signal? → ALLOW (exit)
  ├─→ Budget exhausted? → ASK_HUMAN
  ├─→ Ralph PASS? → ALLOW (exit)
  ├─→ Ralph BLOCKED? → ASK_HUMAN (R/O/A)
  ├─→ Ralph FAIL (pre-existing)? → ALLOW
  └─→ Ralph FAIL (regression)? → BLOCK (retry)
```

### Knowledge Objects

```
knowledge/
├── approved/            # Production KOs
├── drafts/              # Pending review
└── config/              # Cache settings
```

- **In-memory cache**: 457x speedup
- **Auto-approval**: High-confidence KOs approved automatically
- **Tag-based search**: OR semantics

### Strengths (Keep)
- ✅ Mature agent base class
- ✅ Contract-based governance
- ✅ Ralph verification pipeline
- ✅ Wiggum iteration control
- ✅ Knowledge Object learning
- ✅ 89% autonomy achieved

### Gaps (Fix)
- ❌ No dialogue mode for strategic decisions
- ❌ No automatic artifact creation
- ❌ No single status tracking document
- ❌ No Advisor agents
- ❌ No Coordinator for orchestration

---

## CredentialMate (HIPAA Instance)

**Location**: `/Users/tmac/1_REPOS/credentialmate`

### Agent Architecture

Same agents as AI_Orchestrator, synced via mechanism:
- BugFixAgent
- CodeQualityAgent
- FeatureBuilderAgent
- TestWriterAgent

**Key Difference**: LocalAdapter pattern (no cross-repo imports)

```python
# CredentialMate uses inline AppContext
class LocalAdapter:
    def __init__(self, app_ctx):
        self.app_context = app_ctx
    def get_context(self):
        return self.app_context
```

### Sync Mechanism

```
.aibrain/sync-manifest.yaml

SYNCABLE (46 files):
  - agents/*.py (core logic)
  - ralph/*.py (verification)
  - governance/*.py (framework)
  - orchestration/*.py (loops)

PROTECTED (never sync):
  - ralph/hipaa_check.py
  - ralph/hipaa_config.yaml
  - governance/contracts/*.yaml
  - knowledge/ (internalized)

MERGE_STRATEGY:
  - agents/factory.py (preserve LocalAdapter)
  - ralph/cli.py (preserve config imports)
```

### HIPAA-Specific Governance

```
ralph/
├── hipaa_check.py       # PHI detection
├── hipaa_config.yaml    # Sensitive patterns
└── engine.py            # HIPAA integrated

governance/contracts/
├── bugfix.yaml          # + HIPAA constraints
├── qa-team.yaml         # L2 but stricter
└── dev-team.yaml        # L1 (HIPAA-strict)
```

**PHI Detection**:
- Hardcoded patterns: `patient`, `ssn`, `dob`, `medical`
- Sensitive paths: `app/models/`, `app/api/`, `alembic/`
- Verdict: BLOCKED (cannot override)

### Strengths (Keep)
- ✅ Sync mechanism works
- ✅ HIPAA guardrails enforced
- ✅ Standalone operation (no symlinks)
- ✅ LocalAdapter pattern

### Gaps (Fix)
- ❌ Same gaps as AI_Orchestrator
- ❌ HIPAA Advisors don't exist
- ❌ Healthcare-specific artifact templates missing

---

## KareMatch (Healthcare Marketplace)

**Location**: `/Users/tmac/1_REPOS/karematch`

### Agent Architecture

**Fundamentally different**: Skill-based, not contract-based

```
.claude/
├── skills/              # 26+ domain skills
│   ├── rebuild/
│   ├── tdd-enforcer/
│   ├── governance-enforcer/
│   └── ...
├── agents/
│   └── _agent-base.md   # Agent definitions
└── memory/
    ├── hot-patterns.md  # Cached issues
    └── session-bridge.json
```

**Skills vs Agents**:

| Aspect | AI_Orchestrator Agents | KareMatch Skills |
|--------|------------------------|------------------|
| Invocation | Automatic (work queue) | Manual (`/skill-name`) |
| State | Stateless + external memory | Session-scoped |
| Governance | Contract enforcement | Golden paths + RIS |
| Autonomy | High (L1-L2) | Graduated (L0-L4) |
| Artifact creation | Manual | Manual |

### Governance

```
.claude/
├── golden-paths.json    # Protected files
├── agent-guardrails.yml # Safety rules
└── mcp.json             # 26 hooks

docs/
├── 06-ris/              # Resolution & Incident System (43 docs)
└── 07-governance/       # Audit trails
```

**Golden Paths** (5 protection levels):
- BLOCK_AND_ASK: Critical files (CLAUDE.md)
- WARN_AND_LOG: Production files
- VALIDATE_MIGRATION: Schema changes
- SECURITY_REVIEW: Auth/crypto
- BLOCK_MODIFICATION: Frozen references

**Autonomy Levels**:
```
L0: Read-only (explore, search)
L1: Code changes (+ tests)
L2: Schema changes (+ migrations)
L3: Deployment (+ production)
L4: Architecture (+ system design)
```

### Verification (Ralph)

```
tools/ralph/verify.sh    # Shell script harness
```

Same concept, different implementation:
1. Guardrail check (anti-shortcuts)
2. Lint (ESLint)
3. Type check (TypeScript)
4. Tests (Vitest)
5. Coverage (≥80%)

### Strengths (Keep)
- ✅ Skill-based domain specialization
- ✅ Golden paths protection
- ✅ RIS system for decisions
- ✅ Hot patterns cache
- ✅ Graduated autonomy model

### Gaps (Fix)
- ❌ No autonomous agents
- ❌ Skills require manual invocation
- ❌ No unified contract system
- ❌ Artifact creation is manual
- ❌ No Coordinator for orchestration

---

## Conflict Analysis

### Paradigm Conflict

| Aspect | AI_Orchestrator | KareMatch | Resolution |
|--------|-----------------|-----------|------------|
| Agent model | Autonomous | Interactive | **Hybrid**: Advisors (interactive) + Builders (autonomous) |
| Governance | Contracts (YAML) | Golden paths (JSON) | **Unified**: Contracts + Golden paths |
| Memory | Knowledge Objects | Hot patterns | **Merge**: KOs + hot patterns |
| Invocation | Work queue | Manual `/skill` | **Auto-invoke**: Coordinator assigns |

### Governance Conflict

```
AI_Orchestrator:          KareMatch:
governance/               .claude/
├── contracts/            ├── golden-paths.json
│   ├── qa-team.yaml      ├── agent-guardrails.yml
│   └── dev-team.yaml     └── mcp.json
```

**Resolution**: Unified governance folder with:
- `contracts/` for agent autonomy rules
- `golden-paths.yaml` for file protection
- `guardrails.yaml` for safety rules
- Single source, synced to projects

### Artifact Conflict

| Artifact | AI_Orchestrator | KareMatch | Resolution |
|----------|-----------------|-----------|------------|
| Decisions | DECISIONS.md (manual) | RIS docs (manual) | **Auto**: ADR-XXX.md created by Advisors |
| Status | STATE.md (manual) | CONTEXT.md (manual) | **Auto**: PROJECT_HQ.md updated by Coordinator |
| Handoffs | sessions/*.md (auto) | sessions/*.md (manual) | **Auto**: Always auto-generated |

---

## Unified Design Requirements

Based on analysis, the unified system must:

1. **Preserve AI_Orchestrator strengths**:
   - BaseAgent, factory pattern
   - Contract-based governance
   - Ralph-Wiggum verification
   - Knowledge Objects
   - High autonomy for Builders

2. **Preserve KareMatch strengths**:
   - Skill-based domain expertise
   - Golden paths protection
   - RIS decision tracking
   - Hot patterns cache
   - Graduated autonomy for interactive work

3. **Add missing capabilities**:
   - Advisor agents (dialogue mode)
   - Coordinator agent (orchestration)
   - Automatic artifact creation
   - Single PROJECT_HQ.md per project
   - Unified governance format

4. **Resolve conflicts**:
   - Hybrid agent model (dialogue + autonomous)
   - Unified governance (contracts + golden paths)
   - Merged memory (KOs + hot patterns)
   - Auto-invocation (Coordinator assigns work)

---

## File Paths Reference

### AI_Orchestrator
- `/Users/tmac/1_REPOS/AI_Orchestrator/agents/` - Agent implementations
- `/Users/tmac/1_REPOS/AI_Orchestrator/governance/contracts/` - Team contracts
- `/Users/tmac/1_REPOS/AI_Orchestrator/ralph/` - Verification engine
- `/Users/tmac/1_REPOS/AI_Orchestrator/knowledge/` - KO system
- `/Users/tmac/1_REPOS/AI_Orchestrator/orchestration/` - Loop control

### CredentialMate
- `/Users/tmac/1_REPOS/credentialmate/agents/` - Synced agents
- `/Users/tmac/1_REPOS/credentialmate/governance/contracts/` - HIPAA contracts
- `/Users/tmac/1_REPOS/credentialmate/ralph/hipaa_check.py` - PHI detection
- `/Users/tmac/1_REPOS/credentialmate/.aibrain/sync-manifest.yaml` - Sync config

### KareMatch
- `/Users/tmac/1_REPOS/karematch/.claude/skills/` - Domain skills
- `/Users/tmac/1_REPOS/karematch/.claude/golden-paths.json` - Protected files
- `/Users/tmac/1_REPOS/karematch/tools/ralph/` - Verification harness
- `/Users/tmac/1_REPOS/karematch/docs/06-ris/` - Decision records
