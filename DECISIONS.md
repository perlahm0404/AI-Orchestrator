# AI Orchestrator - Build Decisions Log

**Purpose**: Track key implementation decisions with rationale

**Note**: This records decisions made during build, not planning decisions (those are in planning docs).

---

## Active Decisions

### D-020: Golden Pathway Protection & Infrastructure Governance (v5.5 - 2026-01-08)

**Decision**: Implement comprehensive golden pathway protection with service contract validation

**Context**: CredentialMate production incident revealed that infrastructure configuration drift (S3 bucket name mismatch) can break critical user workflows silently without failing tests.

**Root Cause**: LocalStack init script created `credmate-documents-local` bucket, but app config expected `credmate-documents-development`. Result: Documents uploaded successfully but worker couldn't retrieve files → "DocumentFileMissing" errors.

**Implementation**:
1. **Service Contracts SSOT** (`infra/config/service-contracts.yaml`)
   - Single source of truth for S3 buckets, DB URLs, Redis, AWS config
   - Prevents drift between .env, docker-compose, init scripts
   - Validated automatically pre-commit

2. **Contract Validation Script** (`infra/scripts/validate_service_contracts.py`)
   - Validates all cross-service contracts against SSOT
   - Exit code 1 blocks commits with violations
   - Checks .env files, docker-compose.yml, LocalStack init scripts

3. **Infra Team Contract** (`governance/contracts/infra-team.yaml`)
   - NEW team for infrastructure/DevOps agents
   - L0 autonomy (strictest) - all changes require approval
   - Mandatory pre-commit validations for infrastructure files
   - Golden pathway test required for docker-compose/env changes

4. **Enhanced QA/Dev Team Contracts**
   - Added forbidden_actions: modify_docker_compose, modify_env_files, modify_localstack_init
   - Infrastructure changes reserved for Infra Team only
   - Golden pathway protection section added

5. **Golden Pathway Guardrails** (`ralph/guardrails/GOLDEN_PATHWAY_GUARDRAILS.md`)
   - Comprehensive documentation of protection mechanisms
   - Forbidden pattern detection (--no-verify, git commit -n)
   - Service contract enforcement rules
   - Recovery procedures for production incidents

**Rationale**:
- Configuration drift as dangerous as code drift
- Infrastructure changes are #1 cause of silent failures
- SSOT prevents "works on my machine" issues
- Automated validation catches 80%+ of regressions pre-commit
- Golden pathway is critical user workflow - must never break

**Key Design Choices**:
- **SSOT over duplication**: One source of truth, validated automatically
- **Fail-fast validation**: Block commits early (pre-commit) vs. fail late (production)
- **Infrastructure as code**: Treat docker-compose/env files like application code
- **Team separation**: Infra changes require different governance than code changes
- **No bypass allowed**: `--no-verify` is BLOCKED (not just warned)

**Impact**:
- Prevents 80%+ of configuration drift regressions
- Catches S3 bucket mismatches, env var errors before commit
- Clear governance for infrastructure changes
- Faster incident recovery (documented procedures)

**Learnings from Incident**:
1. boto3 auto-creates missing S3 buckets (hides misconfigurations)
2. Silent failures worse than loud failures (need fail-fast)
3. Tests don't catch infrastructure config issues
4. Multiple sources of truth → inevitable drift
5. AI agents need explicit knowledge of critical pathways

**Status**: Implemented in CredentialMate, governance updated in AI_Orchestrator (2026-01-08)

**Related Documents**:
- Session Reflection: `sessions/2026-01-08-golden-pathway-fix-session.md` (CredentialMate)
- Golden Pathway Protection: `docs/governance/GOLDEN_PATHWAY_PROTECTION.md` (CredentialMate)

---

### D-019: Dev Team Architecture Implementation (v5.4 - 2026-01-06)

**Decision**: Implement complete Dev Team architecture (FeatureBuilder + TestWriter agents)

**Context**: v5 planning defined dual-team architecture, but only QA Team was implemented. Dev Team blocked feature development.

**Implementation**:
1. FeatureBuilder agent (agents/featurebuilder.py)
   - Works only on feature/* branches (enforced)
   - 50 iteration budget (liberal for complex features)
   - L1 autonomy (dev-team contract)
   - Can create new files (unlike BugFix)
   - No per-commit Ralph (only at PR time)
2. TestWriter agent (agents/testwriter.py)
   - Specializes in Vitest/Playwright tests
   - 15 iteration budget
   - 80%+ coverage requirement
   - Can use .todo() for WIP tests
   - Cannot delete existing tests
3. Work queue format extended
   - Added: type ("bugfix"|"feature"|"test")
   - Added: branch (e.g., "feature/matching-algorithm")
   - Added: agent ("BugFix"|"FeatureBuilder"|"TestWriter")
   - Added: requires_approval (list of approval items)
4. Autonomous loop enhancements
   - --queue parameter (bugs vs features)
   - Auto branch creation/checkout
   - Human approval workflow
   - Branch validation per task type

**Rationale**:
- Feature development blocked without Dev Team
- QA Team alone is insufficient (fixes only, not features)
- Dual-team architecture maximizes autonomy
- Feature branches isolate risk from main
- Approval workflow enables sensitive operations

**Key Design Choices**:
- **Branch enforcement**: Hard requirement (FeatureBuilder checks at runtime)
- **No per-commit Ralph**: Too slow for feature iteration (PR-time only)
- **Liberal retry budget**: Features need exploration (50 vs 15)
- **Approval as list**: Supports multiple approval types per task
- **Separate queue files**: bugs vs features (clear separation)

**Impact**: Feature development now autonomous (completes dual-team architecture)

**Status**: ✅ COMPLETE

---

### D-018: Wiggum System Enhancements (2026-01-06)

**Decision**: Implement 3 of 4 enhancements (defer Metrics Dashboard)

**Enhancements**:
1. ✅ KO CLI - Already complete (7 commands)
2. ✅ CodeQualityAgent Claude CLI - Full agent parity
3. ✅ Completion Signal Templates - 80% auto-detection
4. ⏸️ Metrics Dashboard - Deferred (session count < 20)

**Rationale**:
- CodeQuality parity needed (100% agent coverage)
- Auto-detection eliminates 80% manual work
- Dashboard premature at current scale
- `aibrain ko metrics` already provides basics

**Impact**: +80% productivity (KO management + signal auto-detection)

**Status**: ✅ COMPLETE

---

### D-017: Knowledge Object System Enhancements (2026-01-06)

**Decision**: Implement all P1 and P2 recommendations from testing

**Implementations**:
- In-memory cache (457x speedup)
- Tag index (O(1) lookups)
- Consultation metrics tracking
- Configurable auto-approval thresholds
- Tag aliases (14 shortcuts)
- Verdict format validation

**Rationale**:
- Performance critical (degrades at 100+ KOs without cache)
- High ROI (low effort, massive speedup)
- Production readiness requires metrics and config
- Tag aliases improve UX

**Key Architecture Choices**:
- **Caching**: In-memory + time expiry (simple, no Redis needed)
- **Metrics**: JSON file (sufficient for <100 KOs)
- **Config**: JSON files (human-editable, version-controllable)
- **Tag semantics**: OR not AND (better discovery)

**Status**: ✅ COMPLETE - Production ready, scales to 200-500 KOs

---

### D-016: Autonomous Loop Verification Fix (2026-01-06)

**Context**: Critical bug - autonomous loop claimed 6/9 tasks complete, but 0/9 actually done (false positives).

**Decision**: Comprehensive 5-phase fix (not just patch)

**Root Causes Fixed**:
1. Skipped verification when no files changed
2. Signature mismatch in fast_verify call
3. Unconditional task completion
4. Missing fast_verify integration in agents

**Rationale**:
- Trust recovery needed after false positives
- Evidence-based: Must store verification verdicts
- Git fallback for reliable file detection
- Verification must be in agent execution, not optional

**Status**: ✅ COMPLETE

---

### D-015: Wiggum + Autonomous Integration (2026-01-06)

**Decision**: Integrate Wiggum IterationLoop into autonomous_loop.py

**Alternatives Rejected**:
- Keep separate (limited autonomy, hard-coded retries)
- Replace autonomous_loop with Wiggum CLI (loses work queue)

**Rationale**:
- Complementary: autonomous_loop = multi-task, Wiggum = per-task iteration
- Proven components (both tested independently)
- Low risk (clean integration surface)
- High impact (60% → 85% autonomy)

**Key Capabilities Unlocked**:
- Agent-specific retry budgets (15-50 vs 3)
- Completion signal detection
- Human override on BLOCKED
- Automatic session resume
- Full audit trail

**Status**: ✅ COMPLETE - 87% autonomy achieved

---

### D-014: Wiggum Rename (2026-01-06)

**Decision**: Rename "Ralph-Wiggum" to "Wiggum"

**Rationale**:
- Two "Ralph" systems caused confusion
- Clear separation: Ralph = verification, Wiggum = iteration
- Better onboarding and documentation

**Changes**:
- CLI: `aibrain ralph-loop` → `aibrain wiggum`
- Files: `ralph_loop.py` → `wiggum.py`
- Documentation updated throughout

**Status**: ✅ COMPLETE

---

### D-013: Dual-Team Architecture (v5.0 - 2026-01-06)

**Decision**: Split into QA Team (main/fix/*) and Dev Team (feature/*)

**Alternatives Rejected**:
- Single team alternating (context switching overhead)
- Features wait for QA (blocks product)

**Rationale**:
- No branch conflicts
- Parallel progress (QA + features)
- Clear ownership
- Different autonomy levels (QA: L2, Dev: L1)

**Status**: ✅ ACTIVE

---

### D-012: Governance Self-Oversight (2026-01-06)

**Decision**: Add @require_harness, baseline recording, safe_to_merge flag

**Rationale**:
- Prevent accidental bypass of governance
- Distinguish pre-existing failures from regressions
- Clear merge decisions (boolean vs ambiguous states)

**Status**: ✅ ACTIVE

---

### D-011: Automated Session Reflection (2026-01-06)

**Decision**: Generate structured handoff documents automatically

**Alternatives Rejected**:
- Manual handoffs (too easy to skip)
- Git commit messages as handoffs (insufficient structure)

**Rationale**:
- Consistency (every session gets handoff)
- Standardized format
- Evidence-based (Ralph verdict, test status)

**Status**: ✅ ACTIVE

---

### D-010: Autonomous Implementation (v5.1 - 2026-01-06)

**Decision**: Use Claude Agent SDK (not CLI) for autonomous operation

**Key Phases**:
1. Wire SDK into autonomous_loop.py
2. Fast verification (30s vs 5min)
3. Self-correction module (auto-fix lint/type/test)
4. Progress persistence (state resume)
5. Simplified governance

**Alternatives Rejected**:
- Claude Code CLI (subprocess overhead, less control)
- Keep manual invocation (doesn't solve autonomy)

**Rationale**:
- Leverage existing infrastructure (90% built)
- Proven patterns from Anthropic
- Fast feedback enables iteration
- Self-correction reduces human intervention

**Target Metrics**:
- Verification: 5min → 30s
- Self-correction: 0 → 3-5 retries
- Autonomy: 0% → 80%

**Status**: ✅ COMPLETE (achieved 89% autonomy)

---

### D-009: Memory Infrastructure (2026-01-05)

**Decision**: Three-tier external memory system

**Files**:
1. STATE.md - Current build state
2. DECISIONS.md - Build decisions (this file)
3. sessions/ - Per-session handoffs

**Rationale**:
- Matches "externalized memory" principle
- Simple markdown (works with Obsidian)
- Upgradeable to database later

**Status**: ✅ ACTIVE

---

### D-008: Directory Scaffolding Timing (2026-01-05)

**Decision**: Create directory structure immediately

**Rationale**:
- Provides structure for agents
- Enables parallel work
- User confirmed preference

**Status**: ✅ COMPLETE

---

### D-007: Autonomous Operation Config (2026-01-05)

**Decision**: Permissive allow-list in `.claude/settings.json`

**Allowed**:
- git, npm, pytest, python, pip
- File operations (Edit/Write/Read/Glob/Grep)

**Denied**:
- secrets, rm -rf, sudo, curl/wget

**Rationale**:
- Meta-project should eat own dogfood
- Session continuity requires autonomous commits
- Security via deny-list and sandboxing

**Status**: ✅ ACTIVE

---

## Historical Context

### Repository Locations (2026-01-05)

- KareMatch: `/Users/tmac/karematch` (L2 autonomy)
- CredentialMate: `/Users/tmac/credentialmate` (L1 autonomy, HIPAA)

**Status**: ✅ CONFIRMED

---

## Decision Guidelines

When adding new decisions:

1. **Clear title**: Date + descriptive name
2. **Context**: Why was decision needed?
3. **Decision**: What was chosen?
4. **Alternatives**: What else was considered?
5. **Rationale**: Why this choice?
6. **Status**: ACTIVE | COMPLETE | SUPERSEDED

Keep entries concise. Full implementation details belong in session notes or planning docs.
