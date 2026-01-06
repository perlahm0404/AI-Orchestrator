# Session: 2026-01-06 - Ralph-Wiggum Integration Planning

**Session ID**: 2026-01-06-ralph-wiggum-planning
**Outcome**: Complete implementation plan created and approved
**Status**: Ready for implementation

---

## What Was Accomplished

### 1. Comprehensive Ralph Comparison Analysis
- ✅ Created [RALPH-COMPARISON.md](../RALPH-COMPARISON.md) - detailed analysis of anthropics/claude-code Ralph-Wiggum vs AI-Orchestrator Ralph
- ✅ Identified two completely different systems solving complementary problems:
  - **Our Ralph**: Code quality verification & governance (PASS/FAIL/BLOCKED verdicts)
  - **Their Ralph-Wiggum**: Self-referential iteration loops (stop hooks, persistence)
- ✅ Analyzed 30 open PRs from anthropics/claude-code repository
- ✅ Examined their stop-hook.sh implementation (177 lines bash)
- ✅ Studied their state file format (Markdown + YAML frontmatter)

### 2. Codebase Architecture Exploration
Launched 3 parallel Explore agents to understand:
- ✅ Agent architecture (`agents/base.py`, `agents/bugfix.py`, `agents/codequality.py`)
- ✅ Ralph integration points (`ralph/engine.py`, `governance/require_harness.py`)
- ✅ KareMatch hook infrastructure (26 hooks in `.claude/hooks/`)
- ✅ Session management (`harness/governed_session.py`)
- ✅ Current completion signals and halt mechanisms

### 3. Implementation Plan Created
- ✅ Detailed 5-phase implementation plan in `/Users/tmac/.claude/plans/jaunty-humming-hartmanis.md`
- ✅ All design decisions clarified with user via AskUserQuestion tool:
  - **Iteration budgets**: Liberal (BugFix: 15, CodeQuality: 20, Feature: 50)
  - **BLOCKED behavior**: Ask human for approval/override (R/O/A prompt)
  - **Completion promises**: Required for all agents
  - **Approval interface**: Interactive terminal prompts
- ✅ Plan approved by user - ready to implement

### 4. Implementation Tracking Setup
- ✅ Created 19-task todo list tracking all phases
- ✅ Clear success criteria defined for each phase
- ✅ Risk mitigation strategies documented

---

## What Was NOT Done

- ⏸️ No code implementation yet (planning phase only)
- ⏸️ No contract files modified
- ⏸️ No agent files modified
- ⏸️ No tests written

**Reason**: This session was dedicated to planning and design. User approved moving to implementation in next session.

---

## Implementation Plan Overview

### Phase 1: Completion Signal Protocol (Week 1)
**Files to modify**:
- `agents/base.py` - Add `check_completion_signal()` method
- `agents/bugfix.py` - Integrate completion checking
- `agents/codequality.py` - Integrate completion checking

**Pattern**: `<promise>TEXT</promise>` tags with exact string matching

### Phase 2: Iteration Budget System (Week 1)
**Files to modify**:
- `agents/base.py` - Add iteration tracking (`record_iteration()`, `get_iteration_summary()`)
- `governance/contract.py` - Add `max_iterations` to ContractLimits
- `governance/contracts/bugfix.yaml` - Add `max_iterations: 15`
- `governance/contracts/codequality.yaml` - Add `max_iterations: 20`
- `governance/contracts/qa-team.yaml` - Add `max_iterations: 20`
- `governance/contracts/dev-team.yaml` - Add `max_iterations: 50`

### Phase 3: Stop Hook System (Week 2)
**Files to create**:
- `governance/hooks/stop_hook.py` - Stop hook logic with human approval prompts

**Files to modify**:
- `harness/governed_session.py` - Integrate stop hook loop

**Decision logic**:
1. Check completion signal → ALLOW if matches
2. Check iteration budget → ASK_HUMAN if exhausted
3. Run Ralph verification
4. PASS → ALLOW
5. BLOCKED → Ask human (R)evert/(O)verride/(A)bort
6. FAIL + safe_to_merge → ALLOW
7. FAIL + regression → BLOCK (agent retries)

### Phase 4: State File Format (Week 3)
**Files to create**:
- `orchestration/state_file.py` - Markdown + YAML frontmatter state management

### Phase 5: CLI Integration (Week 3)
**Files to create**:
- `cli/commands/ralph_loop.py` - `aibrain ralph-loop` command

---

## Key Design Decisions (User Approved)

### 1. Iteration Budget Defaults ✅
- **BugFixAgent**: 15 iterations
- **CodeQualityAgent**: 20 iterations
- **FeatureBuilder**: 50 iterations
- **TestWriter**: 15 iterations

**Rationale**: Liberal limits allow agents to explore solutions without artificial constraints.

### 2. BLOCKED Verdict Behavior ✅
When guardrail violation detected:
```
🚫 GUARDRAIL VIOLATION DETECTED
[Show verdict details]
OPTIONS:
  [R] Revert changes and exit
  [O] Override guardrail and continue
  [A] Abort session immediately
Your choice [R/O/A]:
```

**Rationale**: Human flexibility to override false positives while maintaining safety.

### 3. Completion Promises ✅
**Required for all agents** - Every task must specify `expected_completion_signal`.

**Rationale**: Clear exit criteria prevents ambiguity.

### 4. Human Approval Interface ✅
**Interactive terminal prompts** using `input()` - synchronous, blocks until decision made.

**Rationale**: Appropriate for governed sessions requiring human oversight.

---

## Critical Files Reference

### Read These First (Next Session)
1. `/Users/tmac/.claude/plans/jaunty-humming-hartmanis.md` - Full implementation plan
2. `/Users/tmac/Vaults/AI_Orchestrator/RALPH-COMPARISON.md` - Ralph systems comparison
3. `/Users/tmac/Vaults/AI_Orchestrator/agents/base.py` - Current BaseAgent protocol
4. `/Users/tmac/Vaults/AI_Orchestrator/harness/governed_session.py` - Session orchestration

### Contracts to Modify
- `governance/contracts/bugfix.yaml`
- `governance/contracts/codequality.yaml`
- `governance/contracts/qa-team.yaml`
- `governance/contracts/dev-team.yaml`

### New Files to Create (Week 2-3)
- `governance/hooks/stop_hook.py`
- `orchestration/state_file.py`
- `cli/commands/ralph_loop.py`

---

## Next Session Start Prompt

```markdown
# Ralph-Wiggum Integration - Implementation Session

## Context
I'm continuing work on integrating Ralph-Wiggum iteration patterns into the AI-Orchestrator.

**Previous session**: Created comprehensive implementation plan
**This session**: Begin implementation starting with Phase 1

## What to do
1. Read the implementation plan: `/Users/tmac/.claude/plans/jaunty-humming-hartmanis.md`
2. Read the session handoff: `/Users/tmac/Vaults/AI_Orchestrator/sessions/2026-01-06-ralph-wiggum-integration.md`
3. Start with Phase 1.1: Add completion signal detection to `agents/base.py`
4. Follow the 19-task todo list
5. Run tests after each phase

## Key Points
- All design decisions are APPROVED by user
- Iteration limits: BugFix=15, CodeQuality=20, Feature=50
- Completion promises are REQUIRED for all agents
- Stop hook asks human on BLOCKED (Revert/Override/Abort)
- Changes are ADDITIVE - don't modify core Ralph verification

## Success Criteria for Phase 1
- ✅ Agents detect `<promise>TEXT</promise>` in output
- ✅ Exact string matching works (case-sensitive)
- ✅ Multi-word promises supported

Start with Phase 1.1 and work through the todo list systematically.
```

---

## Handoff Notes

### Architecture Understanding
- **Agent Protocol**: All agents extend BaseAgent with execute() → dict return
- **Session Flow**: GovernedSession orchestrates 4-tier verification (pre-check, real-time, post-task, commit-time)
- **Ralph Integration**: @require_harness decorator enforces harness context
- **Iteration Model**: Currently single-shot (execute once), will become loop (execute until complete/budget)

### Key Insights from Exploration
1. **Stop hook integration point**: GovernedSession.run() is the natural place for iteration loop
2. **Baseline recording**: Already exists (`ralph/baseline.py`) for regression detection
3. **Contract enforcement**: Already robust via `governance/contract.py`
4. **Hook infrastructure**: KareMatch has extensive hook system, can learn from patterns

### Testing Strategy
- Unit tests for each component (completion signals, iteration budgets, stop hook)
- Integration tests with real BugFixAgent and CodeQualityAgent
- Manual testing scenarios: happy path, iteration limit, BLOCKED verdict, regression fix

### Risks Mitigated
- ✅ Infinite loops: max_iterations enforced
- ✅ Agent bypass: stop hook at harness level
- ✅ False completion: exact string matching + Ralph verification
- ✅ Performance: baseline cached, stop hook runs post-execution

---

## Files Modified This Session

### Created
- `/Users/tmac/Vaults/AI_Orchestrator/RALPH-COMPARISON.md` - 864 lines
- `/Users/tmac/.claude/plans/jaunty-humming-hartmanis.md` - 804 lines
- `/Users/tmac/Vaults/AI_Orchestrator/sessions/2026-01-06-ralph-wiggum-integration.md` - This file

### Read (for context)
- `agents/base.py`
- `agents/bugfix.py`
- `agents/codequality.py`
- `ralph/engine.py`
- `ralph/cli.py`
- `harness/governed_session.py`
- `governance/require_harness.py`
- `governance/contract.py`
- All contract YAML files

### Not Modified Yet
- No production code changes this session (planning only)

---

## References

### External Resources
- anthropics/claude-code repository: https://github.com/anthropics/claude-code
- Ralph-Wiggum plugin commit: `68f90e0` (Nov 16, 2025)
- Original Ralph technique: https://ghuntley.com/ralph/

### Internal Documents
- [v5-Planning.md](../docs/planning/v5-Planning.md) - Dual-Team Architecture
- [v4-RALPH-GOVERNANCE-ENGINE.md](../docs/planning/v4-RALPH-GOVERNANCE-ENGINE.md) - Original Ralph spec
- [CLAUDE.md](../CLAUDE.md) - Main project documentation
- [STATE.md](../STATE.md) - Current system state
- [DECISIONS.md](../DECISIONS.md) - Implementation decisions

---

## Session Statistics

- **Duration**: ~2 hours
- **Explore agents launched**: 3 (parallel)
- **Plan agents launched**: 0 (manual plan creation)
- **Files read**: ~15
- **Files created**: 3
- **Files modified**: 0 (planning phase)
- **User questions asked**: 4 (via AskUserQuestion)
- **Design decisions finalized**: 4
- **Todo items created**: 19
- **Estimated implementation time**: 3 weeks

---

## Implementation Priority

### Week 1 (Foundation)
1. Phase 1: Completion signals
2. Phase 2: Iteration budgets
**Deliverable**: Agents can detect promises and track iterations

### Week 2 (Core Loop)
3. Phase 3: Stop hook system
**Deliverable**: Full iteration loop with Ralph verification

### Week 3 (Polish)
4. Phase 4: State file format
5. Phase 5: CLI commands
**Deliverable**: Production-ready system

---

**Session complete. Ready for implementation in next session.**
