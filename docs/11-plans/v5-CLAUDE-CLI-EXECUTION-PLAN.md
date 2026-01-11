# Claude Code CLI Integration - Execution Plan

## Overview

This plan details how to implement the missing Claude Code CLI integration for the autonomous agent v2 system.

**Current State**: Infrastructure complete, execution layer missing
**Goal**: Fully autonomous bug fixing with Claude Code CLI
**Timeline**: 3-5 days

---

## Phase 1: Basic CLI Integration (Day 1)

### 1.1 Create Claude CLI Wrapper Module

**File**: `claude/cli_wrapper.py`

```python
"""
Claude Code CLI Wrapper - Subprocess interface to claude command

Provides clean Python interface to Claude Code CLI with:
- Error handling
- Timeout management
- Output parsing
- Session management
"""

import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
import json
import time


@dataclass
class ClaudeResult:
    """Result from Claude Code CLI execution"""
    success: bool
    output: str
    error: Optional[str] = None
    files_changed: List[str] = None
    duration_ms: int = 0

    def __post_init__(self):
        if self.files_changed is None:
            self.files_changed = []


class ClaudeCliWrapper:
    """Wrapper for Claude Code CLI subprocess calls"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def execute_task(
        self,
        prompt: str,
        files: Optional[List[str]] = None,
        timeout: int = 300  # 5 minutes
    ) -> ClaudeResult:
        """
        Execute a task via Claude Code CLI

        Args:
            prompt: Task description
            files: Optional list of files to focus on
            timeout: Max execution time in seconds

        Returns:
            ClaudeResult with execution details
        """
        start = time.time()

        # Build command
        cmd = ["claude"]

        # Add prompt
        cmd.extend(["--prompt", prompt])

        # Add files if specified
        if files:
            for file in files:
                cmd.extend(["--file", file])

        # Add flags for automation
        cmd.append("--dangerously-skip-permissions")

        try:
            # Execute
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            duration = int((time.time() - start) * 1000)

            # Parse output
            files_changed = self._parse_changed_files(result.stdout)

            if result.returncode == 0:
                return ClaudeResult(
                    success=True,
                    output=result.stdout,
                    files_changed=files_changed,
                    duration_ms=duration
                )
            else:
                return ClaudeResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr,
                    duration_ms=duration
                )

        except subprocess.TimeoutExpired:
            duration = int((time.time() - start) * 1000)
            return ClaudeResult(
                success=False,
                output="",
                error=f"Timeout after {timeout} seconds",
                duration_ms=duration
            )
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            return ClaudeResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=duration
            )

    def _parse_changed_files(self, output: str) -> List[str]:
        """
        Parse changed files from Claude output

        Look for patterns like:
        - "Modified: src/foo.ts"
        - "Created: src/bar.ts"
        """
        files = []
        for line in output.split('\n'):
            if line.startswith(('Modified:', 'Created:', 'Updated:')):
                # Extract filename
                parts = line.split(':', 1)
                if len(parts) == 2:
                    files.append(parts[1].strip())
        return files
```

**Tests**: `tests/claude/test_cli_wrapper.py`

```python
"""Tests for Claude CLI wrapper"""

import pytest
from pathlib import Path
from claude.cli_wrapper import ClaudeCliWrapper, ClaudeResult


def test_cli_wrapper_init(tmp_path):
    """Test wrapper initialization"""
    wrapper = ClaudeCliWrapper(tmp_path)
    assert wrapper.project_dir == tmp_path


def test_parse_changed_files():
    """Test parsing changed files from output"""
    wrapper = ClaudeCliWrapper(Path("/tmp"))

    output = """
Modified: src/auth.ts
Created: tests/auth.test.ts
Some other output
Updated: src/utils.ts
"""

    files = wrapper._parse_changed_files(output)
    assert len(files) == 3
    assert "src/auth.ts" in files
    assert "tests/auth.test.ts" in files
    assert "src/utils.ts" in files


def test_result_dataclass():
    """Test ClaudeResult dataclass"""
    result = ClaudeResult(
        success=True,
        output="Task complete",
        files_changed=["src/test.ts"]
    )

    assert result.success is True
    assert result.error is None
    assert len(result.files_changed) == 1
```

### 1.2 Update autonomous_loop.py

Replace placeholder with actual CLI execution:

```python
# 4. Run Claude Code CLI
from claude.cli_wrapper import ClaudeCliWrapper

wrapper = ClaudeCliWrapper(actual_project_dir)
result = wrapper.execute_task(
    prompt=task.description,
    files=[task.file],
    timeout=300
)

if result.success:
    print(f"✅ Task executed successfully")
    changed_files = result.files_changed
else:
    print(f"❌ Task failed: {result.error}")
    queue.mark_blocked(task.id, result.error)
    continue
```

**Deliverable**: Basic CLI execution working

---

## Phase 2: Smart Prompt Generation (Day 2)

### 2.1 Create Prompt Templates

**File**: `claude/prompts.py`

```python
"""
Prompt templates for different task types

Generates context-rich prompts for Claude Code CLI based on:
- Task type (bug fix, quality improvement, feature)
- Available context (tests, documentation, related files)
- Project conventions
"""

from typing import Optional, List
from pathlib import Path


def generate_bugfix_prompt(
    bug_description: str,
    file_path: str,
    test_files: List[str],
    context: Optional[str] = None
) -> str:
    """Generate prompt for bug fix tasks"""

    prompt = f"""Fix this bug: {bug_description}

**File to fix**: {file_path}

**Test files**: {', '.join(test_files) if test_files else 'None'}

**Requirements**:
1. Read the file and understand the current implementation
2. Fix the bug described above
3. Ensure all existing tests still pass
4. Do NOT add new features or refactor unrelated code
5. Keep changes minimal and focused

"""

    if context:
        prompt += f"**Additional Context**:\n{context}\n\n"

    prompt += """**Verification**:
- Run tests after fixing
- Verify lint and typecheck pass
- Ensure behavior is preserved

Begin by reading the file, then make your fix."""

    return prompt


def generate_quality_prompt(
    issue_description: str,
    file_path: str,
    issue_type: str = "general"
) -> str:
    """Generate prompt for code quality tasks"""

    prompts = {
        "console_error": f"""Remove console.error from {file_path}

**Task**: {issue_description}

**Requirements**:
1. Find all console.error statements
2. Replace with proper error logging
3. Use project's logging utility if available
4. Preserve error information
5. Don't change other logging (console.log, etc.)

Make the change and verify tests still pass.""",

        "unused_import": f"""Remove unused import from {file_path}

**Task**: {issue_description}

**Requirements**:
1. Identify the unused import
2. Remove it cleanly
3. Verify no other code uses it
4. Run linter to confirm

Make the change.""",

        "type_annotation": f"""Fix type annotation in {file_path}

**Task**: {issue_description}

**Requirements**:
1. Add or fix the type annotation
2. Use proper TypeScript types
3. Avoid 'any' unless necessary
4. Run typecheck to verify

Make the change."""
    }

    return prompts.get(issue_type, f"""Fix code quality issue in {file_path}

**Task**: {issue_description}

**Requirements**:
1. Understand the issue
2. Fix it cleanly
3. Verify tests and checks pass

Make the change.""")


def generate_feature_prompt(
    feature_description: str,
    files: List[str],
    acceptance_criteria: Optional[List[str]] = None
) -> str:
    """Generate prompt for feature implementation"""

    prompt = f"""Implement this feature: {feature_description}

**Files involved**: {', '.join(files)}

"""

    if acceptance_criteria:
        prompt += "**Acceptance Criteria**:\n"
        for i, criteria in enumerate(acceptance_criteria, 1):
            prompt += f"{i}. {criteria}\n"
        prompt += "\n"

    prompt += """**Requirements**:
1. Read existing code to understand patterns
2. Implement the feature following project conventions
3. Write tests for new functionality
4. Ensure all tests pass
5. Update any relevant documentation

Begin by reading the related files, then implement the feature."""

    return prompt
```

### 2.2 Integrate Prompts into Loop

Update `autonomous_loop.py`:

```python
from claude.prompts import generate_bugfix_prompt, generate_quality_prompt

# Determine task type and generate appropriate prompt
if task.id.startswith("BUG-"):
    prompt = generate_bugfix_prompt(
        bug_description=task.description,
        file_path=task.file,
        test_files=task.tests
    )
elif task.id.startswith("QUALITY-"):
    prompt = generate_quality_prompt(
        issue_description=task.description,
        file_path=task.file,
        issue_type="console_error"  # Could be extracted from task
    )
else:
    prompt = task.description

result = wrapper.execute_task(prompt=prompt, files=[task.file])
```

**Deliverable**: Smart, context-aware prompts

---

## Phase 3: Integration with Fast Verify & Self-Correct (Day 3)

### 3.1 Connect CLI to Fast Verify

Update `autonomous_loop.py` to run verification after CLI execution:

```python
from ralph.fast_verify import fast_verify
from agents.self_correct import implement_with_retries

# Use self-correction loop instead of direct CLI call
result = await implement_with_retries(
    task_id=task.id,
    task_description=prompt,
    changed_files=[task.file],
    project_dir=actual_project_dir,
    max_retries=5
)

if result["status"] == "success":
    queue.mark_complete(task.id)
    git_commit(f"Complete: {task.description}", actual_project_dir)
    update_progress_file(actual_project_dir, task, "complete",
                        f"Fixed in {result['attempts']} attempts")
else:
    queue.mark_blocked(task.id, result["reason"])
    update_progress_file(actual_project_dir, task, "blocked", result["reason"])
```

### 3.2 Update self_correct.py

Replace placeholder with actual CLI execution:

```python
# In implement_with_retries function
from claude.cli_wrapper import ClaudeCliWrapper

wrapper = ClaudeCliWrapper(project_dir)

for attempt in range(max_retries):
    # Execute task
    result = wrapper.execute_task(
        prompt=task_description,
        files=changed_files,
        timeout=300
    )

    if not result.success:
        print(f"❌ Execution failed: {result.error}")
        continue

    # Verify the changes
    verify_result = fast_verify(project_dir, result.files_changed)

    if verify_result.status == "PASS":
        return {"status": "success", "attempts": attempt + 1}

    # Failed - apply fix strategy
    strategy = analyze_failure(verify_result)

    if strategy.action == "run_autofix":
        apply_autofix(project_dir, strategy.command)
        continue
    elif strategy.action in ["fix_types", "fix_implementation"]:
        # Re-run Claude with error feedback
        task_description = strategy.prompt
        continue
    else:
        break
```

**Deliverable**: Full integration with verification and self-correction

---

## Phase 4: Real-World Testing (Day 4)

### 4.1 Create Test Work Queue

**File**: `tasks/test_queue.json`

```json
{
  "project": "karematch",
  "features": [
    {
      "id": "TEST-001",
      "description": "Remove console.error from src/utils/logger.ts line 42",
      "file": "src/utils/logger.ts",
      "status": "pending",
      "tests": [],
      "passes": false
    },
    {
      "id": "TEST-002",
      "description": "Fix type error in src/auth/session.ts - sessionId should be string not number",
      "file": "src/auth/session.ts",
      "status": "pending",
      "tests": ["tests/auth/session.test.ts"],
      "passes": false
    },
    {
      "id": "TEST-003",
      "description": "Fix failing test in tests/db/connection.test.ts - timeout issue",
      "file": "tests/db/connection.test.ts",
      "status": "pending",
      "tests": ["tests/db/connection.test.ts"],
      "passes": false
    }
  ]
}
```

### 4.2 Run Tests

```bash
# Test 1: Single simple task
python autonomous_loop.py --project karematch --max-iterations 1

# Test 2: Multiple tasks
python autonomous_loop.py --project karematch --max-iterations 3

# Test 3: With self-correction
# (Intentionally create a task that will fail first time)
```

### 4.3 Measure Results

Create tracking spreadsheet:

| Test ID | Description | Attempts | Duration | Result | Notes |
|---------|-------------|----------|----------|--------|-------|
| TEST-001 | Remove console.error | 1 | 45s | ✅ Pass | Clean fix |
| TEST-002 | Fix type error | 2 | 90s | ✅ Pass | Needed retry |
| TEST-003 | Fix timeout | 3 | 180s | ❌ Fail | Too complex |

**Deliverable**: Real-world validation with metrics

---

## Phase 5: Error Handling & Edge Cases (Day 5)

### 5.1 Add Robust Error Handling

**File**: `claude/cli_wrapper.py` (enhancements)

```python
class ClaudeError(Exception):
    """Base exception for Claude CLI errors"""
    pass

class ClaudeTimeoutError(ClaudeError):
    """Raised when Claude CLI times out"""
    pass

class ClaudeAuthError(ClaudeError):
    """Raised when Claude CLI auth fails"""
    pass

class ClaudeNotInstalledError(ClaudeError):
    """Raised when Claude CLI is not installed"""
    pass


def check_cli_available() -> bool:
    """Check if Claude CLI is installed and authenticated"""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            raise ClaudeNotInstalledError("Claude CLI not installed")

        # Check auth
        result = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True,
            timeout=5
        )
        if "authenticated" not in result.stdout.lower():
            raise ClaudeAuthError("Claude CLI not authenticated")

        return True
    except FileNotFoundError:
        raise ClaudeNotInstalledError("Claude CLI not found in PATH")
```

### 5.2 Add Retry Logic

```python
def execute_task_with_retry(
    self,
    prompt: str,
    files: Optional[List[str]] = None,
    max_retries: int = 3
) -> ClaudeResult:
    """Execute task with automatic retry on transient failures"""

    for attempt in range(max_retries):
        result = self.execute_task(prompt, files)

        if result.success:
            return result

        # Check if error is retryable
        if result.error and "timeout" in result.error.lower():
            # Retryable - try again with longer timeout
            continue
        elif result.error and "rate limit" in result.error.lower():
            # Retryable - wait and retry
            time.sleep(60)
            continue
        else:
            # Non-retryable - fail fast
            return result

    return result
```

**Deliverable**: Production-ready error handling

---

## Success Criteria

### Must Have
- ✅ Claude CLI wrapper with subprocess calls
- ✅ Smart prompt generation for different task types
- ✅ Integration with fast_verify and self_correct
- ✅ Successfully fix 3 real bugs autonomously
- ✅ Error handling for common failure modes

### Nice to Have
- ⏳ Metrics dashboard (bugs fixed, time saved)
- ⏳ Human approval UI for complex tasks
- ⏳ Automatic rollback on failures
- ⏳ Integration with existing agents

### Quality Gates
- All new code has tests (>80% coverage)
- Documentation updated
- No regressions in existing functionality
- Real-world testing passes

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Claude CLI crashes | Timeout + error handling + retry logic |
| Bad fixes merged | Fast verify + git commits + human approval |
| Infinite loops | Max iterations limit + circuit breaker |
| Rate limits | Exponential backoff + queue throttling |
| Auth failures | Pre-check auth status + clear error messages |

---

## Timeline Summary

| Day | Phase | Deliverable |
|-----|-------|-------------|
| 1 | Basic CLI Integration | CLI wrapper + tests |
| 2 | Smart Prompts | Context-aware prompt generation |
| 3 | Full Integration | CLI + verify + self-correct working |
| 4 | Real Testing | 3+ bugs fixed autonomously |
| 5 | Production Ready | Error handling + edge cases |

**Total**: 3-5 days to production-ready system

---

## Next Actions

1. **Create `claude/` module** directory
2. **Implement `cli_wrapper.py`** with basic subprocess calls
3. **Test manually** with `claude` command
4. **Integrate into `autonomous_loop.py`**
5. **Run first real bug fix**

Ready to start Phase 1?
