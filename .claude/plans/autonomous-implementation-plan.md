# AI Orchestrator: Autonomous Agent Implementation Plan

**Created**: 2026-01-06
**Status**: Ready for Implementation
**Goal**: Transform AI Orchestrator from manual CLI invocation to fully autonomous operation

---

## Executive Summary

**Problem**: AI Orchestrator requires manual `run_agent.py` invocation and lacks self-correction loops.

**Solution**: Implement 5-phase plan adopting Anthropic's proven patterns while leveraging existing infrastructure (Ralph verification, iteration loops, stop hooks, contracts).

**Key Insight**: Most infrastructure already exists! We need to:
1. Complete `autonomous_loop.py` (agent execution)
2. Wire up `fast_verify.py` to iteration loop
3. Implement self-correction analysis
4. Add progress file management
5. Simplify governance (remove ceremony)

---

## Current State Analysis

### ✅ What Already Works

| Component | Status | File |
|-----------|--------|------|
| **Ralph Verification** | ✅ Complete | `ralph/engine.py` (319 lines) |
| **Fast Verify** | ✅ Complete | `ralph/fast_verify.py` (307 lines) |
| **Iteration Loop** | ✅ Complete | `orchestration/iteration_loop.py` (187 lines) |
| **Stop Hook** | ✅ Complete | `governance/hooks/stop_hook.py` (179 lines) |
| **Session Reflection** | ✅ Complete | `orchestration/reflection.py` |
| **Contracts** | ✅ Complete | 4 YAML files (qa-team, dev-team, bugfix, codequality) |
| **Work Queue** | ✅ Complete | `tasks/work_queue.py` + `tasks_to_run.json` |
| **Agent Base** | ✅ Complete | `agents/base.py` (completion signals, iteration tracking) |
| **State Persistence** | ✅ Complete | `orchestration/state_file.py` (write only) |

### 🚧 What Needs Completion

| Component | Status | Needs |
|-----------|--------|-------|
| **autonomous_loop.py** | 🚧 Placeholder | Agent execution via Claude Agent SDK |
| **Self-correction** | ❌ Missing | `agents/self_correct.py` module |
| **State resume** | 🚧 Partial | Read logic for `.aibrain/agent-loop.local.md` |
| **Progress files** | 🚧 Partial | `claude-progress.txt` update logic |
| **Simplified governance** | ❌ Optional | Remove `@require_harness` ceremony |

---

## Architecture Decision: Claude Agent SDK vs Claude Code CLI

**Current Plan** (from `autonomous-agent-improvements.md`): Uses Claude Code CLI
**Recommendation**: Switch to **Claude Agent SDK** for better control

### Why Claude Agent SDK?

1. **You already have it**: Imported in exploration findings
2. **Better for long-running agents**: Designed for autonomous operation
3. **More control**: Hooks, subagents, permissions built-in
4. **Session management**: Resume capability, state preservation
5. **No subprocess overhead**: Direct Python API

### Example Pattern

```python
from claude.sdk import query, ClaudeAgentOptions, AgentDefinition

# In autonomous_loop.py
async def execute_task(task: Task, app_context):
    """Execute task via Claude Agent SDK"""

    # Build prompt from task
    prompt = f"""
    {task.description}

    Files to modify: {task.file}
    Tests to verify: {task.tests}

    Use the Edit and Write tools to make changes.
    When complete, output: <promise>COMPLETE</promise>
    """

    # Execute with SDK
    messages = []
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            max_iterations=15,  # From contract
            tools=["Read", "Edit", "Write", "Bash"],
            hooks={'Stop': [stop_hook_handler]}
        )
    ):
        messages.append(message)

    return {"output": messages[-1].content, "messages": messages}
```

---

## Phase 1: Complete Autonomous Loop (2 days)

**Goal**: Make `autonomous_loop.py` fully operational with Claude Agent SDK

### 1.1 Integrate Claude Agent SDK

**File**: `autonomous_loop.py` (lines 161-167 are placeholders)

**Changes Needed**:

```python
# Replace placeholder at line 161-167 with:

from claude.sdk import query, ClaudeAgentOptions

async def execute_task_with_sdk(task: Task, agent_name: str, app_context):
    """Execute task via Claude Agent SDK"""

    # Build prompt
    prompt = build_task_prompt(task, agent_name, app_context)

    # Get contract for tool restrictions
    contract = load_contract(agent_name)

    # Map contract actions to Claude tools
    allowed_tools = map_contract_to_tools(contract)

    # Execute
    messages = []
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            max_iterations=contract.limits.max_iterations,
            tools=allowed_tools,
            working_directory=app_context.project_path
        )
    ):
        messages.append(message)
        print(f"  Agent: {message.content[:100]}...")

    return {
        "output": messages[-1].content,
        "messages": messages,
        "changed_files": get_git_changed_files(app_context.project_path)
    }
```

**Helper Functions to Add**:

```python
def build_task_prompt(task: Task, agent_name: str, app_context) -> str:
    """Build complete task prompt with context"""
    contract = load_contract(agent_name)

    return f"""
You are a {agent_name} agent working on {app_context.project_name}.

**YOUR TASK**:
{task.description}

**TARGET FILES**:
{task.file}

**TESTS TO VERIFY**:
{', '.join(task.tests)}

**CONTRACT LIMITS**:
- Max files: {contract.limits.max_files_changed}
- Max lines: {contract.limits.max_lines_added}
- Forbidden actions: {', '.join(contract.forbidden_actions)}

**WORKFLOW**:
1. Read the relevant files
2. Make necessary changes (respect limits)
3. Verify your changes work
4. When complete, output: <promise>COMPLETE</promise>

Begin work.
"""

def map_contract_to_tools(contract) -> list[str]:
    """Map contract actions to Claude tools"""
    tool_map = {
        'read_file': 'Read',
        'write_file': 'Edit',
        'create_file': 'Write',
        'run_tests': 'Bash',
        'run_lint': 'Bash',
        'run_typecheck': 'Bash',
    }

    tools = []
    for action in contract.allowed_actions:
        if action in tool_map:
            tool = tool_map[action]
            if tool not in tools:
                tools.append(tool)

    return tools

def get_git_changed_files(project_path: Path) -> list[str]:
    """Get files changed in working directory"""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
```

**Integration Point**:

Replace lines 161-185 in `autonomous_loop.py`:

```python
# 4. Execute task with Claude Agent SDK
print("🤖 Executing task with Claude Agent SDK...")
try:
    result = await execute_task_with_sdk(
        task=task,
        agent_name=task.agent_type if hasattr(task, 'agent_type') else 'bugfix',
        app_context=app_context
    )

    # Extract completion signal
    promise = None
    if '<promise>' in result['output']:
        start = result['output'].find('<promise>') + len('<promise>')
        end = result['output'].find('</promise>', start)
        promise = result['output'][start:end].strip()

    changed_files = result['changed_files']

except Exception as e:
    print(f"❌ Task execution failed: {e}")
    queue.mark_blocked(task.id, f"Execution error: {str(e)}")
    queue.save(queue_path)
    continue
```

### 1.2 Add Verification Integration

After agent execution, run fast verification:

```python
# 5. Fast verify results
if changed_files:
    from ralph.fast_verify import fast_verify

    print(f"🔍 Verifying {len(changed_files)} changed files...")
    verify_result = fast_verify(changed_files, actual_project_dir, app_context)

    if verify_result.status == "PASS":
        print("✅ Fast verification PASSED")

        # Commit changes
        if git_commit(f"[{task.id}] {task.description}", actual_project_dir):
            queue.mark_complete(task.id)
            update_progress_file(actual_project_dir, task, "complete",
                                f"Committed {len(changed_files)} files")
        else:
            queue.mark_blocked(task.id, "Git commit failed")

    else:
        # Verification failed
        print(f"❌ Verification FAILED: {verify_result.reason}")
        queue.update_progress(task.id, verify_result.reason)
else:
    print("⚠️  No changes detected")
    queue.mark_complete(task.id)

queue.save(queue_path)
```

### 1.3 Simplify Work Queue Format

**Current**: `tasks_to_run.json` (complex with full prompts)
**Target**: Simpler format matching Anthropic pattern

**New Format** (`tasks/work_queue.json`):

```json
{
  "project": "karematch",
  "tasks": [
    {
      "id": "BUG-001",
      "type": "bugfix",
      "description": "Fix authentication timeout in session.ts",
      "file": "src/auth/session.ts",
      "tests": ["tests/auth/session.test.ts"],
      "status": "pending",
      "attempts": 0,
      "last_error": null
    },
    {
      "id": "QA-001",
      "type": "qa-team",
      "description": "Fix 72 test failures",
      "file": "tests/",
      "tests": ["npm test"],
      "status": "pending",
      "attempts": 0
    }
  ]
}
```

**Migration Script**: Create `scripts/migrate_work_queue.py` to convert `tasks_to_run.json` → `work_queue.json`

### 1.4 Remove Complex Orchestration (Optional)

**Consider Deleting** (if not used elsewhere):
- `harness/governed_session.py` (461 lines) - replaced by autonomous_loop
- `orchestration/parallel_agents.py` (227 lines) - not needed with work queue
- `ralph/watcher.py` (~297 lines) - file watching not needed

**Keep**:
- `orchestration/reflection.py` - valuable for handoffs
- `orchestration/iteration_loop.py` - used by advanced agents
- `orchestration/checkpoint.py` - future resume capability

**Decision Point**: Ask user if these should be deleted or kept as "advanced mode"

### Deliverables

- [ ] `autonomous_loop.py` executes tasks via Claude Agent SDK
- [ ] Contract actions mapped to Claude tools
- [ ] Fast verification integrated after execution
- [ ] Git commits on success
- [ ] Progress file updated
- [ ] Work queue simplified (optional migration)

---

## Phase 2: Fast Verification Loop (1 day)

**Goal**: Wire `fast_verify.py` into iteration loop for 30-second feedback

### 2.1 Current State

**Good news**: `ralph/fast_verify.py` already exists and is complete!

```python
# ralph/fast_verify.py (307 lines)
def fast_verify(changed_files: list[str], project_dir: Path, app_context) -> VerifyResult:
    """Fast verification (~30 seconds)"""
    # Tier 1: Lint (changed files only) - <5s
    # Tier 2: Typecheck (incremental) - <30s
    # Tier 3: Related tests only - <60s
```

### 2.2 Integration Points

**Needed**: Wire into `IterationLoop` (currently runs full Ralph)

**File**: `orchestration/iteration_loop.py`

**Change at line 127-135** (currently runs full Ralph):

```python
# Before (slow - 5 minutes):
from ralph.engine import verify
verdict = verify(project, changes, session_id, app_context)

# After (fast - 30 seconds):
from ralph.fast_verify import fast_verify
verify_result = fast_verify(changes, self.project_path, self.app_context)

# Convert VerifyResult → Verdict for compatibility
if verify_result.status == "PASS":
    verdict = Verdict(type=VerdictType.PASS, steps=[], reason="Fast verify passed")
elif verify_result.has_guardrails:
    verdict = Verdict(type=VerdictType.BLOCKED, reason=verify_result.reason)
else:
    verdict = Verdict(type=VerdictType.FAIL, reason=verify_result.reason,
                     safe_to_merge=False)
```

### 2.3 Two-Tier Verification Strategy

| When | Verification | Time | File |
|------|--------------|------|------|
| **During iteration** | `fast_verify()` | ~30s | `ralph/fast_verify.py` |
| **Before commit** | `fast_verify()` | ~30s | `ralph/fast_verify.py` |
| **On PR creation** | `verify()` (full Ralph) | ~5min | `ralph/engine.py` |

**Pre-commit Hook**: Should run fast_verify (not full Ralph)

```bash
# hooks/pre-commit (update)
# Before: Run full Ralph (5 min)
python -m ralph.cli verify ...

# After: Run fast verify (30 sec)
python -m ralph.cli fast-verify ...
```

### 2.4 Add CLI Command for Fast Verify

**File**: `ralph/cli.py` (add command)

```python
@click.command()
@click.option('--project', required=True)
@click.option('--branch')
def fast_verify_cmd(project: str, branch: str):
    """Fast verification for iteration loops (~30 seconds)"""
    # Get changed files
    # Run fast_verify()
    # Print result
    # Exit 0 (PASS) or 1 (FAIL/BLOCKED)
```

### 2.5 Optional: Simplify Ralph

**Consider** (but not required):
- Remove `@require_harness` decorator (144 lines) - enforce at process level instead
- Remove `ralph/watcher.py` (297 lines) - not needed with git hooks
- Keep guardrail scanning (critical for safety)
- Keep full test suite (needed for PRs)

### Deliverables

- [ ] `fast_verify()` wired into `IterationLoop`
- [ ] Pre-commit hook uses fast verify
- [ ] CLI command `ralph fast-verify` added
- [ ] Iteration feedback in <60 seconds
- [ ] Full Ralph still runs on PR

---

## Phase 3: Self-Correction Loop (2 days)

**Goal**: Agent analyzes failures and fixes automatically

### 3.1 Create Self-Correction Module

**New File**: `agents/self_correct.py` (~150 lines)

```python
"""
Self-Correction Module - Analyzes failures and generates fix strategies.

Based on Anthropic's autonomous-coding pattern where agents analyze
their own failures and retry with corrected approach.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FixAction(Enum):
    """Type of fix to apply"""
    RUN_AUTOFIX = "run_autofix"          # Deterministic (lint --fix)
    FIX_TYPES = "fix_types"              # Claude analyzes type errors
    FIX_TESTS = "fix_tests"              # Claude fixes failing tests
    FIX_IMPLEMENTATION = "fix_impl"      # Claude fixes implementation
    ESCALATE = "escalate"                # Cannot auto-fix, need human


@dataclass
class FixStrategy:
    """Strategy for fixing a failure"""
    action: FixAction
    prompt: Optional[str] = None
    command: Optional[str] = None
    retry_immediately: bool = False
    reason: str = ""


def analyze_failure(verify_result) -> FixStrategy:
    """
    Analyze verification failure and determine fix strategy.

    Args:
        verify_result: VerifyResult from fast_verify()

    Returns:
        FixStrategy with action and context
    """

    # Lint errors → auto-fix (deterministic)
    if verify_result.has_lint_errors:
        return FixStrategy(
            action=FixAction.RUN_AUTOFIX,
            command="npm run lint:fix",
            retry_immediately=True,
            reason="Lint errors can be auto-fixed"
        )

    # Type errors → Claude analyzes and fixes
    if verify_result.has_type_errors:
        error_details = "\n".join(verify_result.type_errors)
        return FixStrategy(
            action=FixAction.FIX_TYPES,
            prompt=f"""
Fix these TypeScript type errors:

{error_details}

Read the relevant files, understand the type mismatch, and fix the code.
When done, output: <promise>TYPES_FIXED</promise>
""",
            retry_immediately=False,  # Let Claude think
            reason="Type errors require code analysis"
        )

    # Test failures → Claude fixes implementation or tests
    if verify_result.has_test_failures:
        test_output = "\n".join(verify_result.test_failures)
        return FixStrategy(
            action=FixAction.FIX_TESTS,
            prompt=f"""
These tests are failing:

{test_output}

Analyze why and fix either:
1. The implementation (if tests are correct)
2. The tests (if implementation is correct and tests need updating)

When done, output: <promise>TESTS_FIXED</promise>
""",
            retry_immediately=False,
            reason="Test failures require implementation or test fixes"
        )

    # Unknown failure type → escalate
    return FixStrategy(
        action=FixAction.ESCALATE,
        reason=f"Unknown failure type: {verify_result.reason}"
    )


async def apply_fix_strategy(strategy: FixStrategy, app_context):
    """
    Apply a fix strategy.

    Args:
        strategy: FixStrategy to apply
        app_context: Application context

    Returns:
        Success boolean
    """
    from claude.sdk import query, ClaudeAgentOptions
    import subprocess

    if strategy.action == FixAction.RUN_AUTOFIX:
        # Run auto-fix command
        print(f"🔧 Running auto-fix: {strategy.command}")
        result = subprocess.run(
            strategy.command.split(),
            cwd=app_context.project_path,
            capture_output=True,
            text=True
        )
        return result.returncode == 0

    elif strategy.action in [FixAction.FIX_TYPES, FixAction.FIX_TESTS, FixAction.FIX_IMPLEMENTATION]:
        # Use Claude to analyze and fix
        print(f"🤖 Claude analyzing and fixing...")

        messages = []
        async for message in query(
            prompt=strategy.prompt,
            options=ClaudeAgentOptions(
                max_iterations=3,  # Short iteration for fixes
                tools=["Read", "Edit", "Bash"],
                working_directory=app_context.project_path
            )
        ):
            messages.append(message)

        # Check if fix was successful (look for completion signal)
        last_message = messages[-1].content
        return '<promise>' in last_message

    else:  # ESCALATE
        print(f"⚠️  Cannot auto-fix: {strategy.reason}")
        return False
```

### 3.2 Integration with IterationLoop

**File**: `orchestration/iteration_loop.py`

**Add at end of iteration** (after stop hook returns BLOCK):

```python
# At line 186 (after "Continue iteration")
from agents.self_correct import analyze_failure, apply_fix_strategy

# If stop hook blocked due to FAIL verdict
if stop_result.decision == StopDecision.BLOCK and stop_result.verdict:
    # Analyze failure
    strategy = analyze_failure(stop_result.verdict)

    print(f"\n🔍 Analyzing failure: {strategy.reason}")
    print(f"   Fix action: {strategy.action.value}")

    # Try to fix
    if strategy.action != FixAction.ESCALATE:
        print("🔧 Attempting self-correction...")
        fixed = await apply_fix_strategy(strategy, self.app_context)

        if fixed:
            print("✅ Self-correction succeeded")
        else:
            print("❌ Self-correction failed")
    else:
        print("⚠️  Cannot auto-fix, escalating")

# Continue to next iteration
continue
```

### 3.3 Bounded Retry Logic

**Already Implemented!** The existing `IterationLoop` handles bounded retries:

- Max iterations from contract (15-50)
- Stop hook checks iteration budget
- Returns ASK_HUMAN if budget exhausted

### Deliverables

- [ ] `agents/self_correct.py` module created
- [ ] Lint errors auto-fixed with `npm run lint:fix`
- [ ] Type errors analyzed and fixed by Claude
- [ ] Test failures analyzed and fixed by Claude
- [ ] Integration with `IterationLoop`
- [ ] Bounded retries respected (from contracts)

---

## Phase 4: Progress Persistence (1 day)

**Goal**: Git commits + progress files for session continuity

### 4.1 Progress File Management

**File**: `autonomous_loop.py` (already has `update_progress_file` function)

**Enhance to match Anthropic pattern**:

```python
def update_progress_file(project_dir: Path, task: Task, status: str, details: str) -> None:
    """Update claude-progress.txt with latest status (Anthropic pattern)"""
    progress_file = project_dir / "claude-progress.txt"

    # Create header if file doesn't exist
    if not progress_file.exists():
        progress_file.write_text("# Progress Log\n\n")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read existing content
    content = progress_file.read_text()

    # Build entry
    if status == "complete":
        # Get git commit hash
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        commit = result.stdout.strip() if result.returncode == 0 else "unknown"

        entry = f"""
## Session {timestamp}

### Completed
- [x] {task.id}: {task.description}
  - Files: {task.file}
  - Tests: {', '.join(task.tests)}
  - Status: ✅ Complete
  - Commit: {commit}
  - {details}

"""
    elif status == "in_progress":
        entry = f"""
## Session {timestamp}

### In Progress
- [ ] {task.id}: {task.description}
  - Attempt: {task.attempts}
  - Status: 🔄 Working
  - {details}

"""
    elif status == "blocked":
        entry = f"""
## Session {timestamp}

### Blocked
- [ ] {task.id}: {task.description}
  - Status: 🛑 Blocked
  - Reason: {details}
  - Action needed: Human review required

"""

    # Append to file
    with progress_file.open("a") as f:
        f.write(entry)
```

### 4.2 State File Resume Logic

**File**: `orchestration/state_file.py`

**Add read function** (currently only has write):

```python
def load_state_file(state_file_path: Path) -> dict:
    """
    Load state file with YAML frontmatter + Markdown body.

    Returns:
        dict with frontmatter fields + 'body' key for markdown
    """
    if not state_file_path.exists():
        return {}

    content = state_file_path.read_text()

    # Parse frontmatter
    if content.startswith("---\n"):
        parts = content.split("---\n", 2)
        if len(parts) >= 3:
            import yaml
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return {**frontmatter, 'body': body}

    return {}


def resume_from_state_file(state_file_path: Path) -> Optional[dict]:
    """
    Resume agent state from state file.

    Returns:
        dict with: task_description, iteration, max_iterations, session_id
        or None if no resumable state
    """
    state = load_state_file(state_file_path)

    if not state:
        return None

    # Check if session is resumable
    if state.get('iteration', 0) >= state.get('max_iterations', 0):
        # Session exhausted
        return None

    return {
        'task_description': state.get('task_description'),
        'iteration': state.get('iteration', 0),
        'max_iterations': state.get('max_iterations', 15),
        'session_id': state.get('session_id'),
        'agent_name': state.get('agent_name')
    }
```

### 4.3 Session Startup Protocol

**Add to `autonomous_loop.py`**:

```python
async def start_session(project_dir: Path, app_context) -> Optional[Task]:
    """
    Start or resume session.

    Returns:
        Task to work on, or None if no work
    """
    from orchestration.state_file import resume_from_state_file
    from ralph.fast_verify import fast_verify

    print("\n🔍 Checking session state...")

    # 1. Check for resumable state
    state_file = project_dir / ".aibrain" / "agent-loop.local.md"
    resume_state = resume_from_state_file(state_file)

    if resume_state:
        print(f"📋 Resumable session found: {resume_state['task_description']}")
        print(f"   Iteration: {resume_state['iteration']}/{resume_state['max_iterations']}")
        # TODO: Reconstruct task from state

    # 2. Read progress file
    progress_file = project_dir / "claude-progress.txt"
    if progress_file.exists():
        recent = progress_file.read_text()[-500:]  # Last 500 chars
        print(f"\n📝 Recent progress:\n{recent}")

    # 3. Check git log
    result = subprocess.run(
        ["git", "log", "--oneline", "-5"],
        cwd=project_dir,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"\n📚 Recent commits:\n{result.stdout}")

    # 4. Verify working state
    print("\n🔍 Verifying working tree state...")
    all_src = list(project_dir.glob("src/**/*.ts"))
    verify_result = fast_verify([str(f.relative_to(project_dir)) for f in all_src[:10]],
                                project_dir, app_context)

    if verify_result.status != "PASS":
        print("⚠️  Working tree has issues, attempting auto-fix...")
        # Run lint --fix
        subprocess.run(["npm", "run", "lint:fix"], cwd=project_dir)

    return None  # Will pull from work queue in main loop
```

### 4.4 Git Commit Enhancement

**Already exists in `autonomous_loop.py`** but enhance:

```python
def git_commit(message: str, project_dir: Path, files: list[str] = None) -> bool:
    """
    Create git commit with better error handling.

    Args:
        message: Commit message
        project_dir: Project directory
        files: Specific files to commit (or None for all changes)
    """
    try:
        # Add files
        if files:
            for file in files:
                subprocess.run(
                    ["git", "add", file],
                    cwd=project_dir,
                    check=True,
                    capture_output=True
                )
        else:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

        # Commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_dir,
            check=True,
            capture_output=True
        )

        print(f"✅ Committed: {message}")
        return True

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"❌ Git commit failed: {error_msg}")
        return False
```

### Deliverables

- [ ] Progress file follows Anthropic pattern (completed/in_progress/blocked sections)
- [ ] State file resume logic implemented
- [ ] Session startup protocol (read state, verify, resume)
- [ ] Git commits after each successful task
- [ ] Agents can resume from interruption

---

## Phase 5: Simplified Governance (1 day)

**Goal**: Remove ceremony while keeping safety

### 5.1 Evaluate @require_harness Necessity

**Current**: `governance/require_harness.py` (141 lines)

**Question**: Is this still needed if agents only run via `autonomous_loop.py`?

**Options**:
1. **Keep it**: Enforce at function level (defense in depth)
2. **Remove it**: Enforce at process level (simpler)
3. **Simplify it**: Just check environment variable (no thread-local)

**Recommendation**: **Simplify to environment variable only**

```python
# governance/require_harness.py (simplified to ~20 lines)

class HarnessRequiredError(Exception):
    """Raised when code requires harness but is not running in one."""
    pass


def require_harness():
    """Check if running in harness. Raise if not."""
    if os.environ.get("AI_ORCHESTRATOR_HARNESS_ACTIVE") != "true":
        raise HarnessRequiredError(
            "This operation must be run via autonomous_loop.py or run_agent.py"
        )


# Usage in critical functions:
@require_harness
def dangerous_operation():
    pass
```

Set environment in `autonomous_loop.py`:

```python
# At start of main()
os.environ["AI_ORCHESTRATOR_HARNESS_ACTIVE"] = "true"
```

### 5.2 Remove File Watcher (Optional)

**File**: `ralph/watcher.py` (297 lines)

**Purpose**: Real-time file watching during agent execution

**Question**: Still needed with git-based checkpoint/commit approach?

**Recommendation**: **Delete** - use git hooks instead

- Pre-commit hook runs fast_verify
- No need for real-time watching
- Simpler architecture

### 5.3 Simplify Contract Loader (Optional)

**File**: `governance/contract.py` (248 lines)

**Current**: Comprehensive loader with many helper functions

**Simplification Opportunity**: Merge related functions

```python
# Before: Multiple functions
contract = load("qa-team")
require_allowed(contract, "write_file")
check_limits(contract, lines_added=50)
require_branch(contract, "main")

# After: Single check function
contract = load("qa-team")
contract.validate_action("write_file", context={
    'lines_added': 50,
    'branch': 'main'
})
```

**Effort**: Medium (need to refactor consumers)
**Value**: Low (current API is fine)
**Recommendation**: **Keep as-is** unless problems arise

### 5.4 Governance Enforcement Summary

**Keep** (essential safety):
- Kill-switch (`governance/kill_switch/mode.py`) - 90 lines
- Contracts (`governance/contracts/*.yaml`) - 4 files
- Contract loader (`governance/contract.py`) - 248 lines
- Pre-commit hook (`hooks/pre-commit-branch-check`) - 147 lines
- Stop hook (`governance/hooks/stop_hook.py`) - 179 lines
- Ralph verification (`ralph/engine.py`, `ralph/fast_verify.py`) - 626 lines

**Simplify**:
- `@require_harness` → environment variable only (141 → ~20 lines)

**Delete** (not needed):
- File watcher (`ralph/watcher.py`) - 297 lines
- Governed session (`harness/governed_session.py`) - 461 lines (if not used)
- Parallel orchestrator (`orchestration/parallel_agents.py`) - 227 lines (if not used)

**Total Reduction**: ~985 lines removed, governance still strong

### Deliverables

- [ ] `@require_harness` simplified to env var check
- [ ] File watcher deleted (use git hooks)
- [ ] Optional: Complex orchestration removed
- [ ] Governance still enforced (contracts, kill-switch, stop hooks)
- [ ] System is simpler and faster

---

## Implementation Timeline

### Week 1: Core Autonomy

**Monday-Tuesday: Phase 1**
- Wire Claude Agent SDK into `autonomous_loop.py`
- Build task prompt generation
- Map contracts to tools
- Add verification + git commits
- Simplify work queue format

**Wednesday: Phase 2**
- Wire `fast_verify()` into iteration loop
- Add CLI command
- Update pre-commit hook
- Test 30-second verification

**Thursday-Friday: Phase 3**
- Create `agents/self_correct.py`
- Implement failure analysis
- Integrate with iteration loop
- Test auto-fix for lint/type/test errors

### Week 2: Polish & Testing

**Monday: Phase 4**
- Enhance progress file management
- Add state file resume logic
- Session startup protocol
- Test interruption/resume

**Tuesday: Phase 5**
- Simplify `@require_harness`
- Delete file watcher
- Optional: Remove complex orchestration
- Document governance architecture

**Wednesday-Friday: Integration Testing**
- Run 10 bugs from VERIFIED-BUGS.md through system
- Measure metrics (see below)
- Fix issues discovered
- Document learnings

---

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| **Time to start working** | Manual CLI invocation | Automatic (0 human input) | Agent pulls task from queue |
| **Verification time (iteration)** | 5 minutes (full Ralph) | 30 seconds (fast_verify) | Time fast_verify() calls |
| **Self-correction** | 0 iterations | 3-5 retries avg | Track iteration_summary stats |
| **Session continuity** | Manual handoff | Automatic resume | Test interruption → resume |
| **Governance LOC** | ~1,753 lines | ~768 lines | Count files in governance/ |
| **Agent autonomy** | 0% (fully manual) | 80% (human approves PRs only) | % of tasks completed without human input |
| **Bugs fixed per day** | 1-2 (manual) | 5-10 (autonomous) | Track completed tasks |

---

## Key Files Summary

### Files to Create

| File | Purpose | LOC | Phase |
|------|---------|-----|-------|
| `agents/self_correct.py` | Failure analysis & fix strategies | ~150 | 3 |
| `scripts/migrate_work_queue.py` | Convert tasks_to_run.json → work_queue.json | ~50 | 1 |
| `.claude/plans/autonomous-implementation-plan.md` | This document | ~1000 | 0 |

### Files to Modify

| File | Changes | LOC Changed | Phase |
|------|---------|-------------|-------|
| `autonomous_loop.py` | Wire Claude Agent SDK, verification, progress | ~100 | 1 |
| `orchestration/iteration_loop.py` | Use fast_verify, add self-correction | ~30 | 2, 3 |
| `orchestration/state_file.py` | Add resume logic | ~50 | 4 |
| `governance/require_harness.py` | Simplify to env var only | -121 | 5 |
| `ralph/cli.py` | Add fast-verify command | ~30 | 2 |
| `hooks/pre-commit-branch-check` | Use fast_verify | ~10 | 2 |

### Files to Delete (Optional)

| File | Reason | LOC Saved | Phase |
|------|--------|-----------|-------|
| `ralph/watcher.py` | Not needed with git hooks | 297 | 5 |
| `harness/governed_session.py` | Replaced by autonomous_loop | 461 | 5 |
| `orchestration/parallel_agents.py` | Not needed with work queue | 227 | 5 |

**Total New Code**: ~230 lines
**Total Modified**: ~220 lines
**Total Deleted**: ~985 lines
**Net Change**: -535 lines (simpler system!)

---

## Risk Assessment

### Low Risk

✅ **Phase 1**: Claude Agent SDK integration
- Well-documented API
- Similar to existing `run_agent.py` flow
- Can test incrementally

✅ **Phase 2**: Fast verification
- `fast_verify.py` already complete
- Just wiring, no new logic
- Can fall back to full Ralph if issues

✅ **Phase 4**: Progress files
- Simple file I/O
- Non-breaking additions
- Already partially implemented

### Medium Risk

⚠️ **Phase 3**: Self-correction loop
- New module, new patterns
- Needs careful testing
- Mitigation: Bounded retries (5 max), escalate on unknown failures

⚠️ **Phase 5**: Deleting orchestration
- May be used elsewhere
- Mitigation: Search codebase first, keep if dependencies found

### Mitigation Strategies

1. **Incremental Testing**: Test each phase before moving to next
2. **Feature Flags**: Keep old code path alongside new (can toggle)
3. **Rollback Plan**: Git branches per phase, easy to revert
4. **Manual Fallback**: `run_agent.py` still works for manual operation
5. **Kill-Switch**: `AI_BRAIN_MODE=OFF` stops all autonomous operation

---

## Decision Points for User

### 1. Claude Agent SDK vs Claude Code CLI

**Recommendation**: Claude Agent SDK
**Reason**: Better control, session management, no subprocess overhead
**User Decision**: ☐ SDK ☐ CLI

### 2. Delete Complex Orchestration?

**Files**: `governed_session.py`, `parallel_agents.py`, `watcher.py`
**Savings**: ~985 lines
**Risk**: May break advanced features
**User Decision**: ☐ Delete ☐ Keep as "advanced mode" ☐ Decide later

### 3. Simplify Work Queue Format?

**Current**: `tasks_to_run.json` with full prompts (complex)
**Target**: Simple `work_queue.json` with task metadata
**Effort**: Need migration script
**User Decision**: ☐ Simplify ☐ Keep current format

### 4. Governance Simplification Level?

**Option A**: Aggressive (delete @require_harness, watcher, etc.) - saves ~985 LOC
**Option B**: Conservative (simplify @require_harness only) - saves ~121 LOC
**User Decision**: ☐ Aggressive ☐ Conservative

---

## Next Steps

1. **Review this plan** - User approves approach
2. **Make decisions** - Answer 4 decision points above
3. **Begin Phase 1** - Wire Claude Agent SDK into autonomous_loop.py
4. **Test incrementally** - Verify each phase before proceeding
5. **Measure metrics** - Track success criteria throughout

---

## Appendices

### A. Comparison to Anthropic's Autonomous-Coding Pattern

| Feature | Anthropic Pattern | Our Implementation |
|---------|-------------------|-------------------|
| **Work Queue** | `feature_list.json` | `work_queue.json` ✅ |
| **Progress File** | `claude-progress.txt` | `claude-progress.txt` ✅ |
| **Autonomous Loop** | `main.py` while loop | `autonomous_loop.py` ✅ |
| **Agent Execution** | Claude Agent SDK | Claude Agent SDK ✅ (Phase 1) |
| **Verification** | Tests only | Ralph (guardrails + tests) ✅ Better |
| **Self-Correction** | Retry on test fail | Failure analysis + fix strategies ✅ (Phase 3) |
| **Git Commits** | After each task | After each task ✅ |
| **State Persistence** | Git + progress file | Git + progress + state files ✅ Better |
| **Governance** | None | Contracts + kill-switch + stop hooks ✅ Better |

**Conclusion**: We're implementing the proven pattern PLUS enterprise governance.

### B. Existing Infrastructure Leverage

**What We DON'T Need to Build**:
- ✅ Ralph verification engine (complete)
- ✅ Fast verification (complete)
- ✅ Iteration loop (complete)
- ✅ Stop hook system (complete)
- ✅ Session reflection (complete)
- ✅ Contracts & enforcement (complete)
- ✅ Work queue structure (complete)
- ✅ Agent base protocol (complete)
- ✅ State file format (complete)

**What We DO Need to Build**:
- 🚧 Claude Agent SDK integration (~100 LOC)
- 🚧 Self-correction module (~150 LOC)
- 🚧 State resume logic (~50 LOC)
- 🚧 Progress file enhancement (~30 LOC)

**Total New Code**: ~330 lines (very achievable!)

### C. Example Session Flow (After Implementation)

```
1. Agent starts autonomous_loop.py
   → Reads claude-progress.txt (last session context)
   → Checks .aibrain/agent-loop.local.md (resumable state)
   → Verifies working tree (git status + fast_verify)

2. Agent pulls task from work_queue.json
   → id: BUG-001
   → description: Fix authentication timeout
   → file: src/auth/session.ts

3. Agent executes via Claude Agent SDK
   → Builds prompt with contract limits
   → Maps contract → tools (Read, Edit, Bash)
   → Claude reads, edits, tests
   → Outputs: <promise>COMPLETE</promise>

4. Fast verification (30 seconds)
   → Lint: PASS ✅
   → Typecheck: PASS ✅
   → Tests: PASS ✅

5. Git commit
   → git add src/auth/session.ts tests/auth/session.test.ts
   → git commit -m "[BUG-001] Fix authentication timeout"

6. Update work queue
   → Mark BUG-001 as complete
   → Save work_queue.json

7. Update progress file
   → Append to claude-progress.txt:
     - [x] BUG-001: Fixed authentication timeout
     - Commit: abc123
     - Files: src/auth/session.ts

8. Continue to next task
   → Repeat from step 2
```

### D. References

- [Claude Agent SDK Documentation](https://platform.claude.com/docs/agent-sdk)
- [Anthropic Autonomous Coding Quickstart](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

---

**End of Plan** - Ready for User Approval
