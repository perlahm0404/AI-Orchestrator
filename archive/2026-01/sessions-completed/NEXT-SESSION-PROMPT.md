# Ralph-Wiggum Integration - Implementation Session

## Context
I'm continuing work on integrating Ralph-Wiggum iteration patterns into the AI-Orchestrator system.

**Previous session**: Created comprehensive implementation plan with user approval
**This session**: Begin implementation starting with Phase 1 (Completion Signals)

---

## Required Reading (Start Here)

### Primary Documents
1. **Implementation Plan**: `/Users/tmac/.claude/plans/jaunty-humming-hartmanis.md`
   - Full 5-phase implementation plan (804 lines)
   - All design decisions finalized and user-approved

2. **Session Handoff**: `/Users/tmac/Vaults/AI_Orchestrator/sessions/2026-01-06-ralph-wiggum-integration.md`
   - What was accomplished in planning session
   - Architecture insights from codebase exploration
   - Critical files reference

3. **Ralph Comparison**: `/Users/tmac/Vaults/AI_Orchestrator/RALPH-COMPARISON.md`
   - Detailed comparison of two Ralph systems
   - Pattern recommendations
   - Integration examples

### Architecture Context
- Read: `agents/base.py` - Current BaseAgent protocol
- Read: `harness/governed_session.py` - Session orchestration
- Read: `ralph/engine.py` - Verification engine (keep unchanged)
- Read: `governance/contract.py` - Contract loading system

---

## Implementation Task List

### Phase 1: Completion Signal Protocol (Start Here)

#### Task 1.1: Add Completion Signal Detection to BaseAgent ⭐ START HERE
**File**: `agents/base.py`

Add this method to BaseAgent class:
```python
def check_completion_signal(self, output: str) -> Optional[str]:
    """
    Check if agent output contains completion promise.

    Returns promise text if found, None otherwise.

    Example:
        output = "Task complete. <promise>DONE</promise>"
        result = agent.check_completion_signal(output)
        # result = "DONE"
    """
    import re
    match = re.search(r'<promise>(.*?)</promise>', output, re.DOTALL)
    if match:
        promise_text = match.group(1).strip()
        # Normalize whitespace
        promise_text = ' '.join(promise_text.split())
        return promise_text
    return None
```

**Also add to AgentConfig**:
```python
@dataclass
class AgentConfig:
    # ... existing fields ...
    expected_completion_signal: Optional[str] = None  # e.g., "COMPLETE", "DONE"
    max_iterations: int = 10  # Default, will be overridden by contract
```

#### Task 1.2: Update BugFixAgent
**File**: `agents/bugfix.py`

Add completion checking to execute() method (see plan for details)

#### Task 1.3: Update CodeQualityAgent
**File**: `agents/codequality.py`

Add completion checking to execute() method (see plan for details)

### Phase 2: Iteration Budget System

#### Task 2.1: Add Iteration Tracking to BaseAgent
**File**: `agents/base.py`

Add fields and methods:
- `current_iteration: int = 0`
- `iteration_history: list[dict] = field(default_factory=list)`
- `record_iteration(verdict, changes)`
- `get_iteration_summary()`

#### Task 2.2-2.6: Update Contracts
Add `max_iterations` to all YAML contracts:
- `bugfix.yaml` → 15
- `codequality.yaml` → 20
- `qa-team.yaml` → 20
- `dev-team.yaml` → 50

Update `governance/contract.py` to load max_iterations field.

### Phase 3: Stop Hook System (Week 2)

Create `governance/hooks/stop_hook.py` with full stop hook logic (see plan).

Integrate into `harness/governed_session.py`.

---

## Key Implementation Rules

### User-Approved Design Decisions (DO NOT CHANGE)
1. ✅ **Iteration Budgets**: BugFix=15, CodeQuality=20, Feature=50
2. ✅ **BLOCKED Behavior**: Interactive prompt (R)evert/(O)verride/(A)bort
3. ✅ **Completion Promises**: REQUIRED for all agents
4. ✅ **Approval Interface**: Terminal `input()` prompts (synchronous)

### Critical Constraints
- **Preserve Ralph Core**: DO NOT modify `ralph/engine.py` verification logic
- **Additive Only**: All changes are additions, not modifications to existing behavior
- **@require_harness**: All Ralph verification must stay decorated
- **Contract Enforcement**: max_iterations must be loaded from YAML contracts
- **Exact Matching**: Completion promises use exact string match (case-sensitive)

### Testing Requirements
- Write unit tests after each phase
- Run existing tests to ensure no regressions
- Manual testing scenarios defined in plan

---

## Expected Workflow

### Step 1: Setup
```bash
cd /Users/tmac/Vaults/AI_Orchestrator
source .venv/bin/activate  # Ensure venv active
```

### Step 2: Start with Phase 1.1
Read `agents/base.py` and add completion signal detection method.

### Step 3: Progress Through Todo List
Use the 19-task todo list tracked in the session. Mark tasks as in_progress → completed.

### Step 4: Test Each Phase
Run tests after completing each phase:
```bash
pytest tests/agents/test_completion_signals.py  # After Phase 1
pytest tests/agents/test_iteration_budget.py    # After Phase 2
pytest tests/governance/test_stop_hook.py       # After Phase 3
```

### Step 5: Update Documentation
After implementation:
- Update `CLAUDE.md` with Ralph Loop usage
- Update `STATE.md` with new components
- Create session handoff for next session

---

## Success Criteria

### Phase 1 Complete When:
- ✅ Agents detect `<promise>TEXT</promise>` in output
- ✅ Exact string matching works (case-sensitive)
- ✅ Multi-word promises supported
- ✅ Tests pass

### Phase 2 Complete When:
- ✅ Agents track iteration count
- ✅ Iteration history recorded with verdicts
- ✅ Max iterations enforced from contracts
- ✅ Tests pass

### Phase 3 Complete When:
- ✅ Stop hook integrated into GovernedSession
- ✅ Decision logic works: ALLOW/BLOCK/ASK_HUMAN
- ✅ Agent can self-correct on FAIL verdict
- ✅ BLOCKED verdict escalates to human with R/O/A prompt
- ✅ Tests pass

---

## Quick Reference

### File Paths
- **Plan**: `/Users/tmac/.claude/plans/jaunty-humming-hartmanis.md`
- **Handoff**: `/Users/tmac/Vaults/AI_Orchestrator/sessions/2026-01-06-ralph-wiggum-integration.md`
- **Comparison**: `/Users/tmac/Vaults/AI_Orchestrator/RALPH-COMPARISON.md`

### Agents to Modify
- `agents/base.py` - Add completion signals + iteration tracking
- `agents/bugfix.py` - Integrate patterns
- `agents/codequality.py` - Integrate patterns

### Contracts to Modify
- `governance/contracts/bugfix.yaml` - Add max_iterations: 15
- `governance/contracts/codequality.yaml` - Add max_iterations: 20
- `governance/contracts/qa-team.yaml` - Add max_iterations: 20
- `governance/contracts/dev-team.yaml` - Add max_iterations: 50
- `governance/contract.py` - Load max_iterations field

### New Files to Create (Later Phases)
- `governance/hooks/stop_hook.py` (Phase 3)
- `orchestration/state_file.py` (Phase 4)
- `cli/commands/ralph_loop.py` (Phase 5)

---

## If You Get Stuck

### Question 1: "Which file should I start with?"
**Answer**: `agents/base.py` - Add the `check_completion_signal()` method (Task 1.1)

### Question 2: "Where is the full implementation code?"
**Answer**: In the plan file at `/Users/tmac/.claude/plans/jaunty-humming-hartmanis.md` - contains full code examples for each phase

### Question 3: "Can I modify ralph/engine.py?"
**Answer**: NO - Ralph verification engine stays unchanged. Only add iteration patterns around it.

### Question 4: "Should I implement all phases at once?"
**Answer**: NO - Implement phase by phase, test after each phase, ensure no regressions.

### Question 5: "What if iteration limits seem too high?"
**Answer**: They're user-approved (liberal limits). Don't change without asking user first.

---

## Estimated Timeline

- **Phase 1 (Completion Signals)**: 2-3 hours
- **Phase 2 (Iteration Budgets)**: 2-3 hours
- **Phase 3 (Stop Hook)**: 4-6 hours
- **Phase 4 (State Files)**: 2-3 hours
- **Phase 5 (CLI)**: 2-3 hours
- **Testing & Documentation**: 3-4 hours

**Total**: ~15-22 hours over 3 weeks

---

## Start Command

When you're ready to begin:

```markdown
I'm starting implementation of the Ralph-Wiggum integration.

I've read:
- Implementation plan: /Users/tmac/.claude/plans/jaunty-humming-hartmanis.md
- Session handoff: sessions/2026-01-06-ralph-wiggum-integration.md
- Ralph comparison: RALPH-COMPARISON.md

Starting with Phase 1.1: Adding completion signal detection to agents/base.py

Let me read the current base.py file and begin implementation.
```

---

**Good luck! The plan is comprehensive, user-approved, and ready to execute. Start with Phase 1.1 and work systematically through the todo list.**
