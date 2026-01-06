# AI Orchestrator - Build Decisions Log

**Purpose**: Track decisions made during implementation (not planning decisions - those are in v4-DECISION-v4-recommendations.md)

---

## How to Use This File

When making implementation decisions during the build:

1. Add entry with date, context, decision, rationale
2. Reference this file in future sessions to avoid re-litigating
3. If a decision needs revisiting, mark it as SUPERSEDED with link to new decision

---

## Decisions

### D-016: Critical Fix for Autonomous Loop Verification (2026-01-06)

**Context**:
- Deployed autonomous_loop.py to production with work queue discovery + fast verification
- System ran on 9 tasks, claimed 6/9 completed successfully
- Investigation revealed **0/9 actually completed** - all were false positives
- Critical bugs found: skips verification when no files changed, signature mismatch, unconditional completion

**Evidence of Failure**:
1. **Git commits**: Only `claude-progress.txt` modified, claimed target files unchanged
2. **Test files**: Work queue references non-existent test files, yet tasks marked "passing"
3. **Test failures**: 16 admin-actions tests still failing, no improvement despite "fixes"
4. **File detection**: Fragile pattern matching missed all file changes

**Root Causes Identified**:
1. **Bug #1**: Lines 259-261 - Sets `verification_passed = True` without checks when no files changed
2. **Bug #2**: Lines 204-207 - Calls `fast_verify(app_context=...)` but parameter doesn't exist
3. **Bug #3**: Line 264 - Unconditional `queue.mark_complete()` regardless of verification result
4. **Bug #4**: work_queue.py line 87 - Always sets `passes = True` without evidence
5. **Bug #5**: Missing fast_verify integration in BugFixAgent and CodeQualityAgent

**Options Considered**:

1. **Rollback and disable autonomous loop**
   - Pros: Prevents further false positives
   - Cons: Loses all autonomous capabilities, back to manual operation

2. **Patch only critical bugs (Phases 1-2)**
   - Pros: Quick fix (1 hour), stops false positives
   - Cons: Lacks validation and audit trail, fragile file detection remains

3. **Comprehensive 5-phase fix** ✅ CHOSEN
   - Pros: Addresses all root causes, adds validation and audit trail, robust
   - Cons: 10.5 hours total effort (but only 2 hours for P0 fixes)

**Decision**: Implement comprehensive 5-phase fix immediately

**Rationale**:
1. **Trust recovery**: System credibility damaged by false completions - need robust solution
2. **Evidence-based**: Must store verification verdicts to prevent future false positives
3. **File detection**: Git fallback provides reliable alternative to pattern matching
4. **Agent integration**: Fast verification must be part of agent execution, not optional
5. **Incremental deployment**: Can implement P0 fixes (Phases 1-3) in 2 hours, defer P1 enhancements

**5-Phase Fix Plan**:
- **Phase 1** (30 min, P0): Fix signature mismatch, enforce verification, store verdicts
- **Phase 2** (45 min, P0): Add fast_verify to BugFixAgent and CodeQualityAgent
- **Phase 3** (30 min, P0): Work queue validation (pre-execution file checks)
- **Phase 4** (20 min, P1): Enhanced audit trail (verification details in queue)
- **Phase 5** (30 min, P1): Self-healing auto-fix for lint/type errors

**Success Criteria**:
- False positives: 7/9 (78%) → 0/9 (0%)
- Verification enforcement: Optional → Required
- Audit trail: None → Full verdict + details
- File detection: Pattern-only → Pattern + git fallback

**Implementation Order**:
1. Phase 1 first (30 min) - Stops the bleeding
2. Test on 2 tasks to verify proper blocking
3. Phases 2-3 (2 hours) - Critical fixes complete
4. Phases 4-5 optional but recommended

**Document**: [docs/planning/AUTONOMOUS-LOOP-VERIFICATION-FIX.md](docs/planning/AUTONOMOUS-LOOP-VERIFICATION-FIX.md)

**Status**: 🔴 BLOCKING - Must implement before any further autonomous work

**Impact**: All 9 tasks in work_queue.json must be reset to "pending" after fix deployed

---

### D-015: Integrate Wiggum into Autonomous Loop (2026-01-06)

**Status**: ⚠️ **SUPERSEDED by D-016** - Must fix verification bugs before integration

**Context**:
- autonomous_loop.py provides work queue discovery and multi-task execution (60% autonomy)
- Wiggum IterationLoop provides iteration control and self-correction (fully implemented, tested)
- Both systems working independently but not integrated
- Goal: Achieve long-running, fully autonomous operation (85% autonomy target)

**Options Considered**:

1. **Keep systems separate** (status quo)
   - Pros: No integration risk, both work independently
   - Cons: Limited autonomy (60%), hard-coded 3 retries, no completion signals, weak session persistence

2. **Replace autonomous_loop with Wiggum CLI**
   - Pros: Use proven Wiggum system
   - Cons: Loses work queue discovery, manual task input required, not truly autonomous

3. **Integrate Wiggum into autonomous_loop.py** ✅ CHOSEN
   - Pros: Best of both worlds - work queue + iteration control, 85% autonomy, minimal integration surface
   - Cons: ~6 hours implementation effort, testing required

**Decision**: Integrate Wiggum IterationLoop into autonomous_loop.py

**Rationale**:
1. **Complementary strengths**: autonomous_loop handles multi-task orchestration, Wiggum handles per-task iteration
2. **Proven components**: Both systems fully implemented and tested independently
3. **Low risk**: Clean integration surface (replace 150 lines in autonomous_loop.py)
4. **High impact**: 60% → 85% autonomy improvement
5. **Key capabilities unlocked**:
   - Agent-specific retry budgets (15-50 vs hard-coded 3)
   - Completion signal detection (`<promise>` tags)
   - Human override on BLOCKED verdicts (R/O/A prompts)
   - Automatic session resume from state files
   - Full iteration audit trail

**Implementation Plan**: [docs/planning/wiggum-autonomous-integration-plan.md](docs/planning/wiggum-autonomous-integration-plan.md)

**Success Metrics**:
- Autonomy: 60% → 85%
- Retries per task: 3 → 15-50 (agent-specific)
- Tasks per session: 10-15 → 30-50
- Session resume: Manual → Automatic

**Status**: 📋 Plan complete, ready for implementation

---

### 2026-01-05: Memory Infrastructure Approach

**Context**: Need external artifacts for agent memory before building the repo.

**Decision**: Create three-tier memory system:
1. `STATE.md` - Current build state, what's done/in-progress/blocked
2. `DECISIONS.md` - This file, build-time decisions
3. `sessions/` - Per-session handoff notes for continuity

**Rationale**:
- Matches the "externalized memory" principle from v4 design
- Simple markdown files work with Obsidian
- Can be upgraded to database later without changing pattern

**Status**: ACTIVE

---

### 2026-01-05: Directory Structure Timing

**Context**: Should we create empty directories now or during Phase 0?

**Decision**: Scaffold NOW (user confirmed)

**Rationale**: Provides structure for agents to understand where things go, enables parallel work.

**Status**: ACTIVE

---

### 2026-01-05: Target Repository Locations

**Context**: Need to know where target apps live for Phase -1 calibration and adapter config.

**Decision**: Confirmed locations:
- KareMatch: `/Users/tmac/karematch`
- CredentialMate: `/Users/tmac/credentialmate`

**Status**: ACTIVE

---

---

### 2026-01-05: Autonomous Operation Configuration

**Context**: User requested long autonomous sessions without approval prompts for routine operations.

**Decision**: Created `.claude/settings.json` with permissive allow-list for git, file operations, and Python tools. Restructured `.claude` from file to directory.

**Configuration**:
- Allow: git, npm, pytest, python, pip, file operations (Edit/Write/Read/Glob/Grep)
- Deny: secrets, rm -rf, sudo, curl/wget
- Mode: `acceptEdits` with sandboxing **disabled** (updated after initial setup)

**Rationale**:
- This is a meta-project about autonomous AI - should eat its own dogfood
- Session continuity requires autonomous commits to STATE.md and sessions/
- Security maintained via deny-list and sandboxing

**Status**: ACTIVE

---

### 2026-01-06: Dual-Team Architecture (v5)

**Context**: KareMatch has significant incomplete features (matching algorithm, admin dashboard, credentialing APIs) AND needs QA work (72 test failures, 10 verified bugs). Running both on `main` would cause conflicts.

**Decision**: Implement Dual-Team Architecture:
- **QA Team**: Works on `main` and `fix/*` branches, maintains existing code quality
- **Dev Team**: Works on `feature/*` branches only, builds new features in isolation
- Weekly integration points after Ralph verification

**Alternatives Considered**:
- Option A: Single team alternating between QA and features (rejected: context switching overhead)
- Option B: Features wait until QA complete (rejected: blocks product progress)
- Option C: Dual teams with branch isolation (selected)

**Rationale**:
1. **No conflicts**: Teams work on separate branches
2. **Parallel progress**: QA improves while features ship
3. **Clear ownership**: Each team knows their scope

**Status**: ACTIVE (v5.0 planned, contracts created)

---

### 2026-01-06: Wiggum Integration (v5.1) [SUPERSEDED - See Rename Decision Below]

**Context**: Discovered anthropics/claude-code has a "Ralph-Wiggum" plugin for iterative self-referential development loops using stop hooks. Their Ralph serves a different purpose than our Ralph verification engine. Need to decide if/how to integrate these patterns.

**Decision**: Integrate Wiggum iteration patterns as ADDITIVE features to our Ralph verification system:
1. **Completion Signals**: `<promise>TEXT</promise>` tags for explicit task completion (REQUIRED for all agents)
2. **Iteration Budgets**: Liberal limits per agent type (BugFix: 15, CodeQuality: 20, Feature: 50)
3. **Stop Hook System**: Block agent exit until Ralph verification passes, enable self-correction loops
4. **Human Override**: Interactive prompts on BLOCKED verdicts (Revert/Override/Abort)

**Alternatives Considered**:
- Option A: Ignore their patterns, keep our Ralph as-is (rejected: misses iteration value)
- Option B: Replace our Ralph with theirs (rejected: they solve different problems)
- Option C: Integrate both - use our Ralph for verification, their patterns for iteration (selected)

**Key Sub-Decisions**:

**Decision 1 - Iteration Budget Defaults**:
- Selected: Liberal limits (BugFix: 15, CodeQuality: 20, Feature: 50, TestWriter: 15)
- Rationale: Higher limits allow agents to explore solutions and self-correct without artificial constraints
- Alternative rejected: Conservative limits (5-10) would hit limits on complex tasks

**Decision 2 - BLOCKED Verdict Behavior**:
- Selected: Ask human for approval/override with interactive prompt (R/O/A)
- Rationale: Gives humans flexibility to override false positives while maintaining safety
- Alternative rejected: Auto-revert (too rigid), give agent one retry (delays human decision)

**Decision 3 - Completion Promise Requirement**:
- Selected: REQUIRED for all agents (no optional promises)
- Rationale: Clear exit criteria prevents ambiguity, forces explicit definition of "done"
- Alternative rejected: Optional promises would lead to ambiguous completion states

**Decision 4 - Human Approval Interface**:
- Selected: Interactive terminal prompt using `input()` - synchronous, blocking
- Rationale: Simple, immediate feedback appropriate for governed sessions
- Alternative rejected: CLI commands (too async), webhook (too complex for v1)

**Implementation Plan**: 5 phases over 3 weeks
- Week 1: Completion signals + iteration budgets
- Week 2: Stop hook system with human approval
- Week 3: State files + CLI commands

**Rationale**:
1. **Complementary systems**: Our Ralph verifies quality, their patterns enable iteration
2. **Agent autonomy**: Agents can self-correct on FAIL verdicts, iterate until PASS
3. **Safety maintained**: Ralph runs on every iteration, BLOCKED escalates to human
4. **Evidence-based**: Full iteration history tracked with verdicts
5. **Minimal risk**: Additive only, no changes to core Ralph verification engine

**Status**: SUPERSEDED by Wiggum Rename Decision (2026-01-06) - Implementation complete, renamed from "Ralph-Wiggum" to "Wiggum"

**References**:
- Implementation Plan: `/.claude/plans/jaunty-humming-hartmanis.md`
- Ralph Comparison: `/RALPH-COMPARISON.md`
- Session Handoff: `sessions/2026-01-06-ralph-wiggum-integration.md`
4. **Safe integration**: Ralph gates all merges to main
5. **Different autonomy levels**: QA (L2, higher) vs Dev (L1, stricter) matches risk profiles

**Implementation**:
- Created `governance/contracts/qa-team.yaml`
- Created `governance/contracts/dev-team.yaml`
- Created `docs/planning/v5-Planning.md`
- Updated CLAUDE.md with team documentation

**Status**: ACTIVE

---

### 2026-01-06: Dev Team Autonomy Level (L1 vs L2)

**Context**: Dev Team creates new code. QA Team modifies existing code. Which needs more oversight?

**Decision**: Dev Team gets L1 (stricter), QA Team gets L2 (higher autonomy)

**Rationale**:
- New code has more unknowns and higher risk
- QA changes are safer (behavior preservation required)
- Dev Team changes require approval for deps, APIs, schema
- QA Team can auto-fix lint/type issues without approval

**Status**: ACTIVE

---

### 2026-01-06: Governance Improvements (@require_harness, baseline, safe_to_merge)

**Context**: Agent built governance tools but bypassed them using native Claude Code tools, revealing a meta-problem where governance could be circumvented.

**Decision**: Implement three P0 governance improvements:
1. **@require_harness decorator**: Functions cannot run outside GovernedSession context (prevents accidental bypass)
2. **Baseline Recording**: Capture pre-existing failures to distinguish from regressions
3. **safe_to_merge field**: Clear boolean signal in Verdict (replaces ambiguous states)

**Rationale**:
- Without @require_harness, code could run outside governance (accidental bypass)
- Without baseline, can't tell "repo was already broken" from "this fix broke something"
- Without safe_to_merge flag, unclear if verdict means "safe" or "proceed with caution"

**Implementation**:
- `governance/require_harness.py`: Decorator with env var + thread-local checks
- `ralph/baseline.py`: BaselineRecorder to capture pre-existing state
- `ralph/engine.py`: Added safe_to_merge boolean + summary() method
- `tests/governance/test_require_harness.py`: 12 new tests (49 total passing)

**Status**: ACTIVE

---

### 2026-01-06: Automated Session Reflection System

**Context**: Sessions were ending without structured handoffs. Next session had to reconstruct context from git diffs and STATE.md updates. Manual handoff creation was inconsistent and skipped during fast iteration.

**Decision**: Build automated session reflection system that generates structured handoff documents at end of every agent execution.

**Alternatives Considered**:
- Option A: Manual handoffs only (rejected: too easy to skip)
- Option B: Git commit messages as handoffs (rejected: insufficient structure)
- Option C: Automated SessionReflection system (selected)

**Rationale**:
1. **Consistency**: Every session gets a handoff, no exceptions
2. **Structure**: Standardized format (accomplished, blockers, Ralph verdict, etc.)
3. **Continuity**: Next session reads sessions/latest.md for full context
4. **Evidence**: Handoff includes Ralph verdict, test status, risk assessment
5. **Integration**: Hooks into existing agent framework without breaking changes

**Implementation Details**:
- **Format**: Markdown (human-readable, git-friendly)
- **Naming**: SessionTestSummary (not TestSummary - avoids pytest confusion)
- **Symlink**: sessions/latest.md always points to most recent
- **Ralph Integration**: verify_handoff.py checks completeness
- **Auto-generation**: run_agent.py creates handoffs automatically

**Components**:
- `orchestration/reflection.py`: Core system (445 lines)
- `agents/base.py`: Added finalize_session() method
- `run_agent.py`: Integrated handoff generation
- `ralph/verify_handoff.py`: Handoff verification (220 lines)
- `tests/orchestration/test_reflection.py`: 14 tests, all passing

**Status**: ACTIVE

---

### 2026-01-06: Autonomous Implementation Architecture (v5.1)

**Context**: AI Orchestrator requires manual CLI invocation (`run_agent.py`), has no self-correction loops, and is "too slow and not truly autonomous." Analysis revealed most infrastructure already exists (Ralph, iteration loops, stop hooks, contracts), but needs wiring together with proven patterns from Anthropic's autonomous-coding quickstart.

**Decision**: Implement 5-phase plan to make system fully autonomous using Claude Agent SDK:

**Phase 1**: Wire Claude Agent SDK into `autonomous_loop.py` (2 days)
- Replace manual CLI invocation with autonomous work-pulling
- Map contract actions to Claude tools
- Integrate fast verification and git commits
- Simplify work queue format

**Phase 2**: Fast verification loop (1 day)
- Wire `fast_verify.py` into iteration loop (30-second feedback vs 5-minute Ralph)
- Two-tier strategy: fast during iteration, full Ralph on PR
- Update pre-commit hook to use fast verify

**Phase 3**: Self-correction module (2 days)
- Create `agents/self_correct.py` for failure analysis
- Auto-fix lint errors (`npm run lint:fix`)
- Claude analyzes/fixes type and test errors
- Bounded retries (3-5 iterations max)

**Phase 4**: Progress persistence (1 day)
- Enhance `claude-progress.txt` (Anthropic pattern)
- State file resume logic (read `.aibrain/agent-loop.local.md`)
- Session startup protocol (read state, verify, resume)
- Git commits after each task

**Phase 5**: Simplified governance (1 day)
- Simplify `@require_harness` to env var only (141 → 20 LOC)
- Delete file watcher (297 LOC - use git hooks instead)
- Optional: Remove complex orchestration (985 LOC total savings)

**Alternatives Considered**:

**Option A: Claude Code CLI** (original plan)
- Pros: Already authenticated via claude.ai
- Cons: Subprocess overhead, less control, no session management
- Status: Rejected

**Option B: Claude Agent SDK** (selected)
- Pros: Better control, session management, hooks/permissions built-in, no subprocess
- Cons: Requires API setup
- Status: Selected - better for long-running autonomous agents

**Option C: Keep manual invocation, just add self-correction**
- Pros: Smaller change
- Cons: Still requires human to start each task
- Status: Rejected - doesn't solve autonomy problem

**Rationale**:
1. **Leverage existing work**: 90% of infrastructure already built, just need wiring (~330 new LOC)
2. **Proven patterns**: Adopting Anthropic's validated autonomous-coding approach
3. **Command center validated**: Centralized orchestrator is correct architecture per Claude Agent SDK docs
4. **Fast feedback**: 30-second verification enables iteration (vs 5-minute Ralph)
5. **Self-correction**: Agents fix lint/type/test errors automatically
6. **Simplification**: Remove ceremony (985 LOC) while keeping safety (contracts, kill-switch, stop hooks)

**Success Metrics**:
| Metric | Current | Target |
|--------|---------|--------|
| Time to start | Manual CLI | Automatic |
| Verification | 5 minutes | 30 seconds |
| Self-correction | 0 retries | 3-5 retries |
| Session continuity | Manual | Automatic |
| Code complexity | ~1,753 LOC | ~768 LOC |
| Autonomy | 0% (manual) | 80% (human approves PRs) |

**Key Sub-Decisions Pending**:

**Decision 1 - Claude Agent SDK vs CLI**:
- Recommendation: SDK (better control, session management)
- User approval: PENDING

**Decision 2 - Delete Complex Orchestration**:
- Files: `governed_session.py`, `parallel_agents.py`, `watcher.py` (985 LOC)
- Options: Delete (aggressive), Keep as "advanced mode", Decide later
- User approval: PENDING

**Decision 3 - Work Queue Format**:
- Current: `tasks_to_run.json` with full prompts
- Target: Simple `work_queue.json` (Anthropic pattern)
- User approval: PENDING

**Decision 4 - Governance Simplification Level**:
- Aggressive: Save 985 LOC (delete watcher, orchestration, simplify harness)
- Conservative: Save 121 LOC (simplify harness only)
- User approval: PENDING

**Implementation**:
- Created `docs/planning/autonomous-implementation-plan.md` (comprehensive 5-phase spec)
- Updated STATE.md with plan summary
- Timeline: 2 weeks (5 phases + 3 days testing)

**Status**: PLANNED (awaiting user approval of 4 key decisions)

**References**:
- [Implementation Plan](docs/planning/autonomous-implementation-plan.md)
- [Anthropic Autonomous Coding](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)
- [Claude Agent SDK Docs](https://platform.claude.com/docs/agent-sdk)

---

### 2026-01-06: Wiggum Rename - Separating Iteration from Verification

**Context**: Two systems both using "Ralph" in their names caused confusion:
- Ralph Verification Engine (`ralph/engine.py`) - Code quality verification (PASS/FAIL/BLOCKED)
- Ralph-Wiggum Pattern (`orchestration/iteration_loop.py`) - Iteration control with stop hooks

Users and agents were mixing up which "Ralph" was being referenced.

**Decision**: Rename the iteration control system from "Ralph-Wiggum" to "Wiggum" for clear separation of concerns.

**Changes Made**:
1. **CLI Command**: `aibrain ralph-loop` → `aibrain wiggum`
2. **Files Renamed**:
   - `cli/commands/ralph_loop.py` → `cli/commands/wiggum.py`
   - `tests/integration/test_ralph_loop.py` → `tests/integration/test_wiggum.py`
3. **Session IDs**: `ralph-20260106-111414` → `wiggum-20260106-111414`
4. **Documentation**: Updated CLAUDE.md, STATE.md, all code comments and docstrings
5. **Bonus Implementation**: Integrated Claude CLI wrapper into BugFixAgent.execute() for real AI-powered fixes

**Alternatives Considered**:
- Option A: Keep "Ralph-Wiggum" name (rejected: continued confusion)
- Option B: Rename to "Loop" (rejected: too generic)
- Option C: Rename to "Wiggum" (selected: clear, distinctive, honors source)

**Clear Architecture After Rename**:

| System | Purpose | Location |
|--------|---------|----------|
| **Ralph** | Verification (PASS/FAIL/BLOCKED verdicts) | `ralph/engine.py`, `ralph/fast_verify.py` |
| **Wiggum** | Iteration control (manages loops, calls Ralph) | `orchestration/iteration_loop.py` |

**Rationale**:
1. **Eliminates confusion**: "Ralph" = verification, "Wiggum" = iteration control
2. **Clear separation of concerns**: Two distinct systems with different purposes
3. **Easier onboarding**: New developers immediately understand the distinction
4. **Better documentation**: Can reference each system unambiguously
5. **Honors origin**: "Wiggum" still references anthropics/claude-code's Ralph-Wiggum plugin

**Testing**:
- ✅ 56/56 Wiggum-related tests passing
- ✅ CLI command operational: `python3 -m cli wiggum --help`
- ✅ Claude CLI integration verified (actively working on real bugs)

**Breaking Change**: CLI command name changed
- Users must update: `aibrain ralph-loop` → `aibrain wiggum`
- Internal APIs unchanged (backward compatible)

**Status**: ACTIVE (implementation complete, all tests passing)

**References**:
- [Rename Summary](docs/WIGGUM-RENAME-SUMMARY.md)
- [RALPH-COMPARISON.md](RALPH-COMPARISON.md)
- Original decision superseded: See "Wiggum Integration (v5.1)" above

---

## Template for New Decisions

```markdown
### YYYY-MM-DD: Decision Title

**Context**: What situation prompted this decision?

**Decision**: What was decided?

**Alternatives Considered**:
- Option A: ...
- Option B: ...

**Rationale**: Why this choice?

**Status**: ACTIVE | SUPERSEDED by [link] | PENDING
```