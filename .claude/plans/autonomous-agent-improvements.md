# AI Orchestrator: Autonomous Agent Improvements Plan

## Executive Summary

**Problem**: Current AI Orchestrator is "too slow and not truly autonomous" - requires manual invocation, no self-correction, no work discovery.

**Root Causes Identified**:
1. Manual entry point (`run_agent.py`) - agents can't pull work
2. No iteration loop - agents halt on FAIL instead of self-correcting
3. Over-engineered governance (1,753 lines in Ralph alone)
4. Missing work queue - no autonomous task discovery

**Solution**: Adopt Anthropic's proven autonomous agent patterns from `claude-quickstarts/autonomous-coding`.

---

## Anthropic's Proven Patterns (What Works)

### 1. Two-Agent Architecture
```
┌─────────────────────┐     ┌─────────────────────┐
│  Initializer Agent  │────▶│    Coding Agent     │
│  (Session 1 only)   │     │  (All subsequent)   │
└─────────────────────┘     └─────────────────────┘
```
- **Initializer**: Creates feature_list.json, sets up project structure
- **Coding Agent**: Iterates through features, commits after each

### 2. Simple State Files (Not Complex DB)
```
project/
├── feature_list.json       # Work queue (source of truth)
├── claude-progress.txt     # Human-readable progress log
└── .git/                   # Checkpoint via commits
```

### 3. The Autonomous Loop
```
while features_remaining and iterations < max_iterations:
    1. Read progress file + git log
    2. Pick next incomplete feature
    3. Implement feature
    4. Run tests
    5. If tests pass: commit + mark complete
    6. If tests fail: analyze + fix (same iteration)
    7. Update progress file
```

### 4. Git-Based Persistence
- Commit after EVERY successful iteration
- Enables `git revert` for recovery
- Clean state = always mergeable to main

---

## Current vs Target Architecture

### Current (Slow, Manual)
```
Human → run_agent.py → Agent → Ralph (5min) → Human reviews → Done
         ↑                           ↓
         └──── Manual retry ─────────┘
```

### Target (Autonomous, Fast)
```
Agent ◀──────────────────────────────▶ Work Queue
  │                                      (feature_list.json)
  ▼
Gather Context (read files, git log)
  │
  ▼
Implement Feature (code + tests)
  │
  ▼
Fast Verify (lint + type + test)────────▶ FAIL ─┐
  │                                              │
  │                                              ▼
  │                                      Analyze & Fix
  │                                              │
  ▼                                              │
PASS ──▶ Git Commit ──▶ Update Progress ◀───────┘
```

---

## Phase 1: Adopt Simple Work Queue (2 days)

**Goal**: Replace complex orchestration with `feature_list.json` pattern

### 1.1 Create Work Queue File Format
```json
// tasks/work_queue.json
{
  "project": "karematch",
  "features": [
    {
      "id": "BUG-001",
      "description": "Fix authentication timeout",
      "file": "src/auth/session.ts",
      "status": "pending",  // pending | in_progress | complete | blocked
      "tests": ["tests/auth/session.test.ts"],
      "passes": false
    }
  ]
}
```

### 1.2 Replace run_agent.py with Simple Loop
```python
# autonomous_loop.py (target: <100 lines)
async def run_autonomous_loop(project_dir: str, max_iterations: int = 50):
    queue = load_work_queue(project_dir / "work_queue.json")

    for iteration in range(max_iterations):
        task = queue.get_next_pending()
        if not task:
            print("All tasks complete!")
            break

        # Run Claude Agent SDK
        result = await run_coding_agent(
            task=task,
            project_dir=project_dir,
        )

        # Update queue
        if result.tests_pass:
            queue.mark_complete(task.id)
            git_commit(f"Complete: {task.description}")
        else:
            queue.update_progress(task.id, result.error)

        # Brief pause for rate limiting
        await asyncio.sleep(3)
```

### 1.3 Remove Complex Orchestration
- Delete: `harness/governed_session.py` (461 lines)
- Delete: `orchestration/parallel_agents.py` (227 lines)
- Keep: Session reflection (it's valuable for handoffs)

**Deliverable**: Agents pull work from JSON, not CLI args

---

## Phase 2: Fast Verification Loop (2 days)

**Goal**: Replace 5-minute Ralph with fast local checks

### 2.1 Tiered Verification
```python
# ralph/fast_verify.py
def fast_verify(changed_files: list[str]) -> VerifyResult:
    """Fast verification for iteration loop (~30 seconds)"""

    # Tier 1: Instant (<5s)
    lint_result = run_lint(changed_files)  # Only changed files
    if not lint_result.ok:
        return VerifyResult(status="FAIL", reason=lint_result.errors)

    # Tier 2: Quick (<30s)
    type_result = run_typecheck(changed_files)  # Incremental
    if not type_result.ok:
        return VerifyResult(status="FAIL", reason=type_result.errors)

    # Tier 3: Related tests only (<60s)
    tests = find_related_tests(changed_files)
    test_result = run_tests(tests)
    if not test_result.ok:
        return VerifyResult(status="FAIL", reason=test_result.errors)

    return VerifyResult(status="PASS")


def full_verify() -> VerifyResult:
    """Full verification before merge (~5 minutes)"""
    # Current Ralph implementation - run on PR only
    pass
```

### 2.2 Verification Timing
| When | Verification | Time |
|------|--------------|------|
| Each iteration | fast_verify() | ~30s |
| Before commit | fast_verify() | ~30s |
| PR creation | full_verify() (Ralph) | ~5min |

### 2.3 Simplify Ralph
- Keep: Guardrail scanning (important)
- Keep: Full test suite (for PRs)
- Remove: @require_harness decorator (144 lines)
- Remove: Real-time file watcher (unnecessary overhead)

**Deliverable**: Iteration feedback in <60 seconds

---

## Phase 3: Self-Correction Loop (2 days)

**Goal**: Agent analyzes failures and fixes automatically

### 3.1 Error Analysis Pattern
```python
# agents/self_correct.py
def analyze_failure(verify_result: VerifyResult) -> FixStrategy:
    """Determine fix strategy from failure type"""

    if verify_result.has_lint_errors:
        return FixStrategy(
            action="run_autofix",
            command="npm run lint:fix",
            retry_immediately=True
        )

    if verify_result.has_type_errors:
        return FixStrategy(
            action="fix_types",
            prompt=f"Fix these type errors:\n{verify_result.errors}",
            retry_immediately=False  # Let Claude think
        )

    if verify_result.has_test_failures:
        return FixStrategy(
            action="fix_implementation",
            prompt=f"""
            Tests failed:
            {verify_result.errors}

            Either fix the implementation or update tests if spec changed.
            """,
            retry_immediately=False
        )

    return FixStrategy(action="escalate", reason="Unknown failure")
```

### 3.2 Bounded Retry Loop
```python
async def implement_with_retries(task: Task, max_retries: int = 5):
    for attempt in range(max_retries):
        result = await implement_task(task)
        verify = fast_verify(result.changed_files)

        if verify.status == "PASS":
            return Success(result)

        if attempt < max_retries - 1:
            strategy = analyze_failure(verify)
            if strategy.action == "escalate":
                break  # Don't waste retries

            await apply_fix_strategy(strategy)
            continue

    return Failure(reason="Max retries exceeded", last_error=verify.errors)
```

**Deliverable**: Agents fix lint/type/test errors automatically

---

## Phase 4: Progress Persistence (1 day)

**Goal**: Git commits + progress file for session continuity

### 4.1 Progress File Format
```markdown
<!-- claude-progress.txt -->
# Progress Log

## Session 2025-01-06T14:30:00

### Completed
- [x] BUG-001: Fixed authentication timeout
  - Files: src/auth/session.ts
  - Tests: All passing
  - Commit: abc123

### In Progress
- [ ] BUG-002: Database connection leak
  - Attempt 1: Fixed pool cleanup
  - Attempt 2: Added timeout handling
  - Status: Tests still failing (2/5)

### Blocked
- [ ] BUG-003: Third-party API change
  - Reason: Need API key for staging env
  - Action needed: Human to provide credentials
```

### 4.2 Session Startup Protocol
```python
async def start_session(project_dir: str):
    # 1. Read current state
    progress = read_file("claude-progress.txt")
    git_log = run("git log --oneline -10")
    work_queue = load_json("work_queue.json")

    # 2. Verify working state
    verify = fast_verify(get_all_src_files())
    if verify.status == "FAIL":
        await fix_broken_state(verify)

    # 3. Resume work
    current_task = work_queue.get_in_progress() or work_queue.get_next_pending()
    return current_task
```

**Deliverable**: Agents resume from any point

---

## Phase 5: Simplified Governance (1 day)

**Goal**: Keep safety, remove ceremony

### 5.1 Contract Enforcement (Keep)
```yaml
# governance/contracts/qa-team.yaml (simplified)
name: qa-team
branches: ["main", "fix/*"]

allowed_actions:
  - read_file
  - write_file
  - run_tests
  - git_commit

limits:
  max_lines_changed: 100
  max_files_changed: 5
  max_iterations: 15

forbidden:
  - modify_migrations
  - push_to_main
  - deploy
```

### 5.2 Remove Unnecessary Complexity
| Component | Lines | Action |
|-----------|-------|--------|
| @require_harness | 144 | DELETE - enforce at process level |
| File watcher | ~200 | DELETE - use git hooks instead |
| Kill switch modes | 89 | KEEP - useful for emergencies |
| Contract loader | 248 | SIMPLIFY to ~100 lines |

### 5.3 Single Enforcement Point
```python
# governance/enforce.py (target: ~50 lines)
def check_action(action: str, context: dict) -> bool:
    """Single function to check all governance"""
    contract = load_contract(context.team)

    if not contract.allows(action):
        raise ContractViolation(f"Action {action} not allowed for {context.team}")

    if context.lines_changed > contract.limits.max_lines:
        raise ContractViolation("Too many lines changed")

    return True
```

**Deliverable**: Governance in ~200 lines (not 1,000+)

---

## Implementation Order

```
Week 1:
├── Phase 1: Work Queue (Mon-Tue)
│   └── Agents pull tasks from JSON
├── Phase 2: Fast Verify (Wed-Thu)
│   └── 30-second verification loop
└── Phase 3: Self-Correction (Fri)
    └── Auto-fix lint/type/test errors

Week 2:
├── Phase 4: Progress Persistence (Mon)
│   └── Git commits + progress file
├── Phase 5: Simplified Governance (Tue)
│   └── Remove @require_harness, simplify contracts
└── Integration Testing (Wed-Fri)
    └── Run 10 bugs through new system
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time to start working | Manual CLI | Automatic |
| Verification time | 5 minutes | 30 seconds |
| Self-correction | None | 5 retries |
| Session continuity | Manual handoff | Automatic |
| Governance code | 1,753 lines | ~400 lines |
| Agent autonomy | 0% (fully manual) | 80% (human approves PRs) |

---

## Key Files to Create

```
autonomous_loop.py          # Main entry point (<100 lines)
ralph/fast_verify.py        # Fast verification (~100 lines)
agents/self_correct.py      # Error analysis (~50 lines)
governance/enforce.py       # Single enforcement (~50 lines)
tasks/work_queue.json       # Task queue (data file)
claude-progress.txt         # Progress log (data file)
```

## Key Files to Delete/Simplify

```
DELETE: governance/require_harness.py (144 lines)
DELETE: harness/governed_session.py (461 lines - replace with autonomous_loop.py)
DELETE: orchestration/parallel_agents.py (227 lines - not needed with work queue)
DELETE: ralph/watcher.py (~200 lines - use git hooks)
SIMPLIFY: governance/contract.py (248 → ~100 lines)
SIMPLIFY: run_agent.py (315 → ~50 lines wrapper)
```

---

## Sources

- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Autonomous Coding Quickstart](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)
- [Claude Agent SDK Best Practices](https://skywork.ai/blog/claude-agent-sdk-best-practices-ai-agents-2025/)
