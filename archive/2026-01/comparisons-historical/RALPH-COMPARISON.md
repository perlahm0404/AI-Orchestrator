# Ralph Implementation Comparison

**Date**: 2026-01-06
**Your Implementation**: AI-Orchestrator v4/v5
**Their Implementation**: anthropics/claude-code Ralph-Wiggum Plugin

---

## Executive Summary

**Two completely different "Ralph" systems solving different problems:**

| Aspect | Your Ralph (AI-Orchestrator) | Their Ralph-Wiggum (Claude Code) |
|--------|------------------------------|-----------------------------------|
| **Purpose** | Code quality verification & governance | Self-referential AI development loops |
| **Domain** | Static analysis + testing + guardrails | Iterative task completion |
| **Architecture** | Python verification engine | Bash hook + state machine |
| **Execution** | Pre-commit/PR validation | Session loop blocker |
| **Output** | PASS/FAIL/BLOCKED verdicts | Continuous iteration until complete |
| **Integration** | Git hooks, CLI, agent harness | Claude Code Stop hook |

---

## Part 1: Your Ralph (AI-Orchestrator)

### Core Architecture

```python
# ralph/engine.py
def verify(project, changes, session_id, app_context, baseline) -> Verdict:
    """
    Verification pipeline:
    1. Guardrail scan (BLOCKED if violations)
    2. Lint check
    3. Typecheck
    4. Test execution
    5. Baseline comparison (regression detection)

    Returns: Verdict(type=PASS/FAIL/BLOCKED, safe_to_merge=bool)
    """
```

### Key Features

1. **Verdict System** - Three-state decision model
   - `PASS` - All checks passed
   - `FAIL` - Fixable issues (tests fail, lint errors)
   - `BLOCKED` - Guardrail violations (non-fixable)

2. **Baseline Comparison** - Regression detection
   - Records "before" state
   - Compares "after" state
   - Distinguishes new failures from pre-existing ones
   - Sets `safe_to_merge=True` if only pre-existing failures

3. **Guardrail Enforcement**
   - Pattern detection (e.g., `--no-verify`, bypass attempts)
   - File-level scanning
   - BLOCKED verdict halts immediately

4. **Evidence-Based**
   - Structured step results
   - Duration tracking
   - Detailed output capture
   - Audit trail integration

### Integration Points

```
Git Pre-Commit Hook → ralph.cli.py → ralph.engine.verify() → Verdict
                                          ↓
                                    governance.require_harness
                                          ↓
                                    Audit logging + contract enforcement
```

### Files Structure

```
ralph/
├── engine.py          # Core verification logic (320 lines)
├── cli.py            # CLI interface for git hooks (180 lines)
├── baseline.py       # Regression detection
├── verdict.py        # Verdict data structures
├── guardrails/       # Pattern detection
└── steps/            # Individual check steps

governance/
├── contracts/        # YAML autonomy contracts
├── require_harness.py # Harness decorator
└── guardrails/       # Policy enforcement
```

---

## Part 2: Their Ralph-Wiggum (anthropics/claude-code)

### Core Architecture

```bash
# hooks/stop-hook.sh
# Intercepts Claude's exit attempt
# Feeds SAME PROMPT back to Claude
# Creates self-referential feedback loop

while true; do
  # 1. Claude works on task
  # 2. Claude tries to exit
  # 3. Stop hook BLOCKS exit
  # 4. Stop hook feeds prompt back
  # 5. Claude sees its own work in files
  # 6. Repeat until completion promise detected
done
```

### Key Features

1. **Stop Hook Mechanism**
   - Intercepts session exit using Claude Code's Stop hook API
   - Blocks normal exit and feeds prompt back
   - Creates infinite loop until completion criteria met

2. **Completion Criteria**
   - `--completion-promise "<text>"` - Exact string match in `<promise>` tags
   - `--max-iterations N` - Safety escape hatch
   - No promise + no limit = infinite loop

3. **State Machine**
   - State stored in `.claude/ralph-loop.local.md`
   - Markdown frontmatter (YAML) for metadata
   - Prompt text after closing `---`

4. **Self-Referential Loop**
   - Prompt never changes
   - Claude reads its own previous work from files
   - Each iteration sees modified git history
   - Autonomous improvement through file system

### Implementation

```bash
# State file format: .claude/ralph-loop.local.md
---
iteration: 5
max_iterations: 20
completion_promise: "COMPLETE"
---

Your prompt goes here.
Build a REST API with tests.
Output <promise>COMPLETE</promise> when done.
```

```bash
# Stop hook logic
1. Read state file
2. Check if max_iterations reached → exit
3. Parse last Claude response from transcript
4. Check for <promise>TEXT</promise> matching completion_promise → exit
5. Extract prompt from state file
6. Increment iteration counter
7. Return JSON: {"decision": "block", "reason": "<prompt>"}
8. Claude receives same prompt again
```

### Files Structure

```
plugins/ralph-wiggum/
├── README.md                    # 179 lines of docs
├── hooks/
│   ├── hooks.json              # Stop hook registration
│   └── stop-hook.sh            # 177 lines - core loop logic
├── scripts/
│   └── setup-ralph-loop.sh     # 176 lines - state file creation
└── commands/
    ├── ralph-loop.md           # /ralph-loop command
    ├── cancel-ralph.md         # /cancel-ralph command
    └── help.md                 # Documentation
```

---

## Part 3: Key Differences

### 1. **Problem Domain**

| Your Ralph | Their Ralph-Wiggum |
|------------|-------------------|
| "Did this code change break anything?" | "Keep trying until task is complete" |
| Verification & governance | Iteration & persistence |
| Quality gatekeeper | Autonomous worker loop |

### 2. **When They Run**

| Your Ralph | Their Ralph-Wiggum |
|------------|-------------------|
| Pre-commit (git hook) | During active Claude session |
| PR merge time | Interactive development |
| CI/CD pipeline | User-initiated loops |

### 3. **Output**

| Your Ralph | Their Ralph-Wiggum |
|------------|-------------------|
| `Verdict(PASS/FAIL/BLOCKED)` | Continues until `<promise>` detected |
| Safe/unsafe to merge decision | Task completion or max iterations |
| Evidence bundle for audit | Iterative refinement |

### 4. **Philosophy**

| Your Ralph | Their Ralph-Wiggum |
|------------|-------------------|
| **Governance** - Prevent bad changes | **Persistence** - Keep trying until success |
| **Guardrails** - Block policy violations | **Iteration** - Failures are learning data |
| **Evidence** - Audit trail required | **Autonomy** - Walk away, let it work |

---

## Part 4: Naming Coincidence Analysis

### Why Both Named "Ralph"?

**Your Ralph**: Likely named after the governance concept from your research vault patterns, or as a shorthand for verification/approval systems.

**Their Ralph-Wiggum**: Explicitly named after Ralph Wiggum from The Simpsons:
> *"embodying the philosophy of persistent iteration despite setbacks"*

Original technique from Geoffrey Huntley: https://ghuntley.com/ralph/

### Are They Related?

**No direct lineage**, but both draw from similar AI governance concepts:
- Self-referential systems
- Autonomous operation
- Policy enforcement
- Evidence-based decisions

---

## Part 5: Can You Learn From Their Implementation?

### Patterns Worth Adopting

1. **Stop Hook Pattern**
   - You could implement a Stop hook for your agents
   - Block agent exit until governance approval received
   - Create approval loops for human-in-the-loop workflows

2. **State File Pattern**
   - Their `.claude/ralph-loop.local.md` approach is clean
   - Markdown + YAML frontmatter = human-readable + machine-parseable
   - You could adopt this for session state tracking

3. **Completion Signals**
   - `<promise>TEXT</promise>` pattern for agent completion signaling
   - Better than checking exit codes or parsing logs
   - Could integrate with your Verdict system

4. **Iteration Limits**
   - Their `--max-iterations` safety mechanism
   - Prevents infinite loops on impossible tasks
   - You could add iteration budgets to your agents

### Example Integration

```python
# Your future: Combine both Ralph approaches

# 1. Ralph-Wiggum style loop
while not task_complete:
    agent.execute(task)

    # 2. Your Ralph verification
    verdict = ralph.verify(
        project="karematch",
        changes=agent.get_modified_files(),
        session_id=session.id,
        app_context=app_context
    )

    if verdict.type == VerdictType.BLOCKED:
        # Stop hook blocks exit, asks human for approval
        human_override = await stop_hook.ask_human(verdict)
        if not human_override:
            break

    if agent.output_contains("<promise>COMPLETE</promise>"):
        task_complete = True
```

---

## Part 6: Implementation Comparison Matrix

| Feature | Your Ralph | Their Ralph-Wiggum | Winner |
|---------|-----------|-------------------|--------|
| **Code quality gates** | ✅ (lint, test, typecheck) | ❌ | You |
| **Guardrail enforcement** | ✅ (pattern detection) | ❌ | You |
| **Regression detection** | ✅ (baseline comparison) | ❌ | You |
| **Autonomous iteration** | ❌ | ✅ (stop hook loop) | Them |
| **Self-correction** | ❌ | ✅ (reads own work) | Them |
| **Human approval loops** | ✅ (via harness) | ❌ | You |
| **Audit evidence** | ✅ (structured logging) | ❌ | You |
| **Completion signals** | ❌ | ✅ (`<promise>` tags) | Them |
| **Safety escape hatch** | ✅ (BLOCKED verdict) | ✅ (max iterations) | Tie |
| **Multi-repo support** | ✅ (adapters) | ❌ | You |
| **Session isolation** | ✅ (harness context) | ⚠️  (state file per session) | You |

---

## Part 7: Recommended Actions

### 1. **Keep Your Ralph Core** ✅
Your verification engine is more sophisticated for governance use cases. Don't replace it.

### 2. **Adopt Stop Hook Pattern** 🎯
Implement a Stop hook in your agent system:

```python
# governance/hooks/stop_hook.py
def agent_stop_hook(agent, session):
    """Block agent exit until governance approval."""
    verdict = ralph.verify(...)

    if verdict.safe_to_merge:
        return {"decision": "allow"}
    else:
        return {
            "decision": "block",
            "reason": "Awaiting human approval",
            "systemMessage": verdict.summary()
        }
```

### 3. **Add Completion Signals** 🎯
Adopt their `<promise>` tag convention:

```python
# agents/base.py
def check_completion(self, output: str) -> bool:
    """Check if agent signaled completion."""
    import re
    match = re.search(r'<promise>(.*?)</promise>', output, re.DOTALL)
    if match:
        promise_text = match.group(1).strip()
        return promise_text == self.expected_completion_signal
    return False
```

### 4. **Create Iteration Budgets** 🎯
Add iteration limits to your agents:

```python
# agents/bugfix.py
class BugFixAgent(Agent):
    max_iterations: int = 10  # Safety limit
    current_iteration: int = 0

    def should_continue(self) -> bool:
        if self.current_iteration >= self.max_iterations:
            self.log_warning(f"Max iterations ({self.max_iterations}) reached")
            return False
        return not self.task_complete
```

### 5. **Document Both Patterns** 📝
Update your docs to clarify:
- **Ralph Verification** = Your governance engine
- **Ralph Loop** = Optional iteration pattern (inspired by Ralph-Wiggum)

---

## Part 8: KareMatch Integration Example

### Current: Your Ralph (Verification Only)

```bash
# .git/hooks/pre-commit (KareMatch)
python -m ralph.cli --staged --project karematch

# Output:
# ✅ PASS - safe to proceed
# OR
# 🚫 BLOCKED - guardrail violation
```

### Future: Your Ralph + Stop Hook (Verification + Iteration)

```python
# karematch/.claude/hooks/stop-hook.py

from ralph.engine import verify
from adapters.karematch import KareMatchAdapter

def stop_hook(transcript_path):
    """Block agent exit until Ralph verification passes."""

    # Get changes from transcript
    changes = extract_modified_files(transcript_path)

    # Run your Ralph verification
    adapter = KareMatchAdapter()
    verdict = verify(
        project="karematch",
        changes=changes,
        session_id=get_session_id(),
        app_context=adapter.get_context()
    )

    if verdict.safe_to_merge:
        return {"decision": "allow"}
    else:
        # Block exit, show verdict, give agent chance to fix
        return {
            "decision": "block",
            "reason": "Fix the issues below and try again:\n\n" + verdict.summary(),
            "systemMessage": "🔄 Ralph verification FAILED - fix and retry"
        }
```

---

## Conclusion

**Your Ralph and their Ralph-Wiggum are complementary, not competitive.**

- **Your Ralph** = Quality gatekeeper (verification at commit/PR time)
- **Their Ralph-Wiggum** = Autonomous worker (iteration during development)

**Recommendation**: Keep your Ralph verification engine and adopt their iteration patterns selectively for agent autonomy.

---

## References

- **Their Implementation**: https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum
- **Original Technique**: https://ghuntley.com/ralph/ (Geoffrey Huntley)
- **Your Implementation**: `/Users/tmac/Vaults/AI_Orchestrator/ralph/`
- **Your Docs**: [v4-RALPH-GOVERNANCE-ENGINE.md](./docs/planning/v4-RALPH-GOVERNANCE-ENGINE.md)
