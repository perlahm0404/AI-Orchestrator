# Autonomous Loop Verification Fix Plan

**Date**: 2026-01-06
**Status**: 🔴 CRITICAL - Zero tasks actually completed despite 6/9 claimed success
**Priority**: P0 - Blocking all autonomous work

---

## Executive Summary

**Problem**: Autonomous loop marks tasks as complete without verifying actual work was done, resulting in **0/9 real completions** despite claiming 6/9 success.

**Root Causes**:
1. **Skips verification when no files changed** - Sets `verification_passed = True` without any checks
2. **Signature mismatch** - Calls `fast_verify()` with wrong parameters (`app_context` doesn't exist)
3. **No actual code changes** - Agents make zero file modifications but get marked complete
4. **Missing verification in agents** - BugFixAgent and CodeQualityAgent never call fast_verify
5. **Fragile file detection** - Relies on Claude outputting specific patterns like "Modified: file.ts"

**Impact**:
- 7 tasks marked complete with **zero code changes**
- 2 tasks timed out and marked blocked
- False positives in `work_queue.json` (`passes: true` without evidence)
- No verification verdicts stored for audit trail

---

## Evidence of Critical Failure

### 1. False Completions in work_queue.json

```json
{
  "id": "BUG-CRED-001",
  "status": "complete",
  "passes": true,  // ← FALSE: No verification was run
  "error": null,
  "completed_at": "2026-01-06T11:41:05.379075"
}
```

**Reality**: No code was actually changed. Git diff shows empty.

### 2. Git Commits Show No Real Work

```bash
# Commit claims to fix services/matching/src/matcher.ts
$ git show 5fd6ebf --stat
commit 5fd6ebfcac9c5a492da0d386d6dca4372507b6f6
Author: TMAC <tmac@tmacs-mbp.lan>
Date:   Tue Jan 6 11:43:13 2026 -0600

    feat: Fix therapist matcher boundary conditions

    Task ID: BUG-MATCH-001
    Files: services/matching/src/matcher.ts

 claude-progress.txt                | 13 +++++++++++++
 package-lock.json                  |  1 +
 services/auth/package.json         |  1 +
 services/auth/tsconfig.tsbuildinfo |  2 +-
 4 files changed, 16 insertions(+), 1 deletion(-)

# Check actual changes to claimed file
$ git diff 5fd6ebf^..5fd6ebf -- services/matching/src/matcher.ts
# → EMPTY DIFF (no changes to the file!)
```

**Only file changed**: `claude-progress.txt` (a progress log, not source code)

### 3. Test Files Don't Exist

```bash
$ npm test -- services/credentialing/tests/wizard.test.ts
> karematch@2.0.0 test
> vitest run services/credentialing/tests/wizard.test.ts

No test files found, exiting with code 1
```

Work queue references **non-existent test files**, yet tasks marked as passing tests.

### 4. Tests Still Failing

```bash
$ npm test
✅ 8 tests skipped
❌ 16 admin-actions tests FAILING
❌ Multiple test files not found
```

No improvement in test pass rate despite "6 bugs fixed".

---

## Code Analysis: Critical Bugs Found

### Bug #1: Skips Verification on No Changes
**File**: `/Users/tmac/Vaults/AI_Orchestrator/autonomous_loop.py`
**Lines**: 259-261

```python
if changed_files:
    # ... verification loop ...
else:
    print("⚠️  No changed files detected, skipping verification\n")
    verification_passed = True  # ← DANGEROUS: Auto-passes without any checks
```

**Problem**: If Claude doesn't modify any files:
1. Sets `verification_passed = True` without running any checks
2. Immediately marks task as complete
3. Commits "changes" even though there are none

**Risk**: Task that fails to make required changes is marked successful.

---

### Bug #2: Signature Mismatch
**File**: `/Users/tmac/Vaults/AI_Orchestrator/autonomous_loop.py`
**Lines**: 204-207

```python
verify_result = fast_verify(
    changed_files=changed_files,
    project_dir=actual_project_dir,
    app_context=app_context  # ← ERROR: Parameter doesn't exist
)
```

**Actual signature** (`ralph/fast_verify.py:258`):
```python
def fast_verify(project_dir: Path, changed_files: list[str]) -> VerifyResult:
    # Only accepts project_dir and changed_files
```

**Impact**: This call will fail at runtime with `TypeError: fast_verify() got an unexpected keyword argument 'app_context'`

---

### Bug #3: Unconditional Task Completion
**File**: `/Users/tmac/Vaults/AI_Orchestrator/autonomous_loop.py`
**Lines**: 263-265

```python
# 6. Mark as complete
queue.mark_complete(task.id)  # ← PROBLEM: Always executes
queue.save(queue_path)
```

**Problem**: After the `if changed_files` block, the code **always** marks the task complete, even if:
- No files were modified
- Verification was skipped

---

### Bug #4: Passes Always True
**File**: `/Users/tmac/Vaults/AI_Orchestrator/tasks/work_queue.py`
**Lines**: 82-89

```python
def mark_complete(self, task_id: str) -> None:
    """Mark task as complete"""
    for task in self.features:
        if task.id == task_id:
            task.status = "complete"
            task.passes = True  # ← Always True, regardless of verification result
            task.completed_at = datetime.now().isoformat()
            break
```

**Problem**: Method unconditionally sets `passes = True`, creating false positive records.

---

### Bug #5: Missing Verification in Agents
**Files**:
- `/Users/tmac/Vaults/AI_Orchestrator/agents/bugfix.py` (line ~150)
- `/Users/tmac/Vaults/AI_Orchestrator/agents/codequality.py` (line ~150)

**Current flow**:
```python
def execute(self, task_id: str, context: dict) -> AgentResult:
    # 1. Check kill switch
    # 2. Check contract
    # 3. Execute Claude CLI
    # 4. Get output
    # 5. Return result
    # ← NO VERIFICATION CALLED
```

**Missing**: Agents should call `fast_verify()` after Claude CLI execution to catch immediate issues.

---

## 5-Phase Fix Strategy

### Phase 1: Fix Critical Verification Bugs ⚠️ PRIORITY
**Time**: 30 minutes
**Status**: Not started

#### 1.1 Fix Signature Mismatch
**File**: `autonomous_loop.py` (lines 204-207)

```python
# CURRENT (broken)
verify_result = fast_verify(
    changed_files=changed_files,
    project_dir=actual_project_dir,
    app_context=app_context  # ← Remove this
)

# FIX
verify_result = fast_verify(
    project_dir=actual_project_dir,
    changed_files=changed_files
)
```

#### 1.2 Enforce Verification on No File Changes
**File**: `autonomous_loop.py` (lines 259-284)

```python
# CURRENT (broken)
if changed_files:
    # ... verification loop ...
else:
    print("⚠️  No changed files detected, skipping verification\n")
    verification_passed = True  # ← PROBLEM

# FIX: Block tasks with no changes
if changed_files:
    # ... verification loop ...
    verification_passed = (verify passed after retries)
else:
    # No changes means task wasn't completed
    print("❌ No changed files detected - task appears incomplete")
    queue.mark_blocked(
        task.id,
        "No code changes detected. Agent may have failed silently or misunderstood task."
    )
    queue.save(queue_path)
    continue  # Skip to next task

# Only mark complete if verification passed
if verification_passed:
    queue.mark_complete(task.id, verdict=verify_result.verdict)
    queue.save(queue_path)
    # ... git commit ...
```

#### 1.3 Store Verification Verdict in Queue
**File**: `tasks/work_queue.py`

```python
# Update mark_complete signature
def mark_complete(self, task_id: str, verdict: Optional[str] = None) -> None:
    task.status = "complete"
    task.passes = (verdict == "PASS") if verdict else True
    task.verification_verdict = verdict  # NEW: Store actual verdict
    task.completed_at = datetime.now().isoformat()

# Add field to Task dataclass
@dataclass
class Task:
    # ... existing fields ...
    verification_verdict: Optional[str] = None  # NEW: "PASS", "FAIL", "BLOCKED"
```

#### 1.4 Improve File Change Detection
**File**: `claude/cli_wrapper.py` (lines 178-195)

Add git-based fallback when pattern matching fails:

```python
def _parse_changed_files(self, output: str, project_dir: Path) -> List[str]:
    """Parse changed files from Claude output AND git status"""

    # Method 1: Parse Claude's output
    files = []
    for line in output.split('\n'):
        if line.strip().startswith(('Modified:', 'Created:', 'Updated:')):
            parts = line.strip().split(':', 1)
            if len(parts) == 2:
                files.append(parts[1].strip())

    # Method 2: Git fallback if no files detected
    if not files:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                git_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
                print(f"[Git Fallback] Detected {len(git_files)} changed files")
                return git_files
        except Exception as e:
            print(f"[Git Fallback] Failed: {e}")

    return files
```

---

### Phase 2: Add Missing Verification to Agents
**Time**: 45 minutes
**Status**: Not started

#### 2.1 Add Verification to BugFixAgent
**File**: `agents/bugfix.py` (after line 150)

```python
def execute(self, task_id: str, context: dict) -> AgentResult:
    # ... execute Claude CLI ...
    result = self.cli.execute_task(prompt, files, timeout)

    # NEW: Verify changes immediately
    if result.success and result.files_changed:
        from ralph.fast_verify import fast_verify
        verify_result = fast_verify(
            project_dir=self.project_dir,
            changed_files=result.files_changed
        )

        return AgentResult(
            success=(verify_result.status == "PASS"),
            output=result.output,
            verification=verify_result,
            files_changed=result.files_changed
        )

    return AgentResult(
        success=result.success,
        output=result.output,
        files_changed=result.files_changed
    )
```

#### 2.2 Add Verification to CodeQualityAgent
**File**: `agents/codequality.py` (after line 150)

Same pattern as BugFixAgent - add `fast_verify()` after Claude CLI execution.

---

### Phase 3: Work Queue Validation
**Time**: 30 minutes
**Status**: Not started

#### 3.1 Validate Task Definitions on Load
**File**: `tasks/work_queue.py`

```python
def validate_tasks(self, project_dir: Path) -> List[str]:
    """Validate that task file paths and test files exist"""
    errors = []

    for task in self.features:
        # Check target file exists
        file_path = project_dir / task.file
        if not file_path.exists():
            errors.append(f"Task {task.id}: File not found: {task.file}")

        # Check test files exist
        for test_file in task.tests:
            test_path = project_dir / test_file
            if not test_path.exists():
                errors.append(f"Task {task.id}: Test not found: {test_file}")

    return errors
```

#### 3.2 Call Validation from Autonomous Loop
**File**: `autonomous_loop.py` (after loading queue)

```python
# Load work queue
queue = WorkQueue.load(queue_path)

# Validate task definitions
validation_errors = queue.validate_tasks(project_dir)
if validation_errors:
    print("⚠️  Work Queue Validation Errors:")
    for error in validation_errors:
        print(f"   - {error}")
    print("\nContinuing with caution...\n")
```

#### 3.3 Pre-Execution File Check
**File**: `autonomous_loop.py` (in main loop before execution)

```python
# Before executing task
task = queue.get_next_pending()
if not task:
    break

# Validate task has valid file paths
task_file = project_dir / task.file
if not task_file.exists():
    print(f"❌ Task {task.id}: Target file not found: {task.file}")
    queue.mark_blocked(task.id, f"File not found: {task.file}")
    queue.save(queue_path)
    continue

# ... proceed with execution ...
```

---

### Phase 4: Enhanced Audit Trail
**Time**: 20 minutes
**Status**: Not started

#### 4.1 Expand Task Schema
**File**: `tasks/work_queue.py`

```python
@dataclass
class Task:
    # ... existing fields ...

    # NEW: Verification audit trail
    verification_verdict: Optional[str] = None  # "PASS", "FAIL", "BLOCKED"
    verification_details: Optional[dict] = None  # Lint/type/test results
    files_actually_changed: Optional[List[str]] = None  # What files were modified
```

#### 4.2 Store Verification Details
**File**: `autonomous_loop.py` (after fast_verify)

```python
verify_result = fast_verify(project_dir, changed_files)

# Store detailed results
task.verification_details = {
    "status": verify_result.status,
    "lint_errors": verify_result.lint_errors,
    "type_errors": verify_result.type_errors,
    "test_failures": verify_result.test_failures,
    "duration_ms": verify_result.duration_ms
}
task.files_actually_changed = changed_files

if verify_result.status == "PASS":
    queue.mark_complete(task.id, verdict="PASS")
else:
    queue.mark_blocked(task.id, f"Verification failed: {verify_result.reason}")
```

---

### Phase 5: Self-Healing with Auto-Fix
**Time**: 30 minutes
**Status**: Not started

#### 5.1 Enhanced Retry Loop
**File**: `autonomous_loop.py` (lines 198-247)

```python
# PHASE 2: Fast verification with retry and auto-fix
max_retries = 3
verification_passed = False

for retry in range(max_retries):
    verify_result = fast_verify(project_dir, changed_files)

    if verify_result.status == "PASS":
        verification_passed = True
        break

    # Auto-fix lint errors
    if retry < max_retries - 1 and verify_result.lint_errors:
        print(f"   Retry {retry + 1}/{max_retries - 1}: Auto-fixing lint errors...")

        lint_fix_result = subprocess.run(
            ["npm", "run", "lint:fix"],
            cwd=project_dir,
            capture_output=True,
            timeout=30
        )

        if lint_fix_result.returncode == 0:
            print(f"   ✓ Lint auto-fix successful")
            changed_files = _get_git_changed_files(project_dir)
            continue  # Retry verification

    # Auto-fix type errors with rebuild
    if retry < max_retries - 1 and verify_result.type_errors:
        print(f"   Retry {retry + 1}/{max_retries - 1}: Rebuilding TypeScript...")

        ts_build_result = subprocess.run(
            ["npm", "run", "build"],
            cwd=project_dir,
            capture_output=True,
            timeout=60
        )

        if ts_build_result.returncode == 0:
            print(f"   ✓ TypeScript build successful")
            continue  # Retry verification

    print(f"   ✗ Verification failed on retry {retry + 1}")

if not verification_passed:
    queue.mark_blocked(task.id, f"Verification failed after {max_retries} retries: {verify_result.reason}")
    queue.save(queue_path)
    continue
```

---

## Implementation Timeline

### Week 1: Critical Fixes (Must Complete)

| Day | Phase | Time | Deliverable |
|-----|-------|------|-------------|
| **Day 1** | Phase 1 | 2 hours | Fix verification bugs, test on 2 tasks |
| **Day 2** | Phase 2 | 3 hours | Add verification to agents, integration test |
| **Day 3** | Phase 3 | 2 hours | Work queue validation, update existing queue |

### Week 2: Enhancements (Optional but Recommended)

| Day | Phase | Time | Deliverable |
|-----|-------|------|-------------|
| **Day 4** | Phase 4 | 1.5 hours | Audit trail, verify JSON output |
| **Day 5** | Phase 5 | 2 hours | Self-healing, end-to-end testing |

**Total time**: ~10.5 hours (7 hours critical, 3.5 hours enhancements)

---

## Testing Strategy

### Unit Tests
```python
# tests/test_autonomous_loop_verification.py

def test_no_changes_marks_blocked():
    """Task with no file changes should be blocked, not completed"""
    result = execute_task_mock(changed_files=[])
    assert result.status == "blocked"
    assert "No code changes detected" in result.error

def test_verification_fail_marks_blocked():
    """Task with failing verification should be blocked"""
    result = execute_task_mock(
        changed_files=["src/bug.ts"],
        verify_result=VerifyResult(status="FAIL", reason="Tests failed")
    )
    assert result.status == "blocked"
    assert result.verification_verdict == "FAIL"

def test_verification_pass_marks_complete():
    """Task with passing verification should be complete"""
    result = execute_task_mock(
        changed_files=["src/bug.ts"],
        verify_result=VerifyResult(status="PASS")
    )
    assert result.status == "complete"
    assert result.verification_verdict == "PASS"
    assert result.passes == True
```

### Integration Test
```bash
# Test with real work queue
cd /Users/tmac/Vaults/AI_Orchestrator

# Backup current queue
cp tasks/work_queue.json tasks/work_queue.json.backup

# Reset queue to pending
python scripts/reset_work_queue.py

# Run autonomous loop on 1 task
python autonomous_loop.py --project karematch --max-iterations 1

# Expected outcome:
# - Task picks up first pending item
# - Claude executes
# - Files detected via git fallback if needed
# - fast_verify runs
# - Task marked complete ONLY if verification PASS
# - Verification verdict stored in work_queue.json
```

---

## Success Metrics

| Metric | Current (Broken) | Target (Fixed) |
|--------|------------------|----------------|
| False positives | 7/9 (78%) | 0/9 (0%) |
| Verification enforcement | Optional | Required |
| Audit trail | None | Full verdict + details |
| File detection | Pattern-only (fragile) | Pattern + git fallback |
| Auto-fix capability | None | Lint + TypeScript |
| Task validation | None | Pre-execution checks |
| Completion criteria | Always True | Only on PASS verdict |

---

## Rollback Plan

If critical issues arise during implementation:

```bash
# Revert autonomous_loop.py changes
cd /Users/tmac/Vaults/AI_Orchestrator
git checkout HEAD -- autonomous_loop.py

# Revert work_queue.py changes
git checkout HEAD -- tasks/work_queue.py

# Revert cli_wrapper.py changes
git checkout HEAD -- claude/cli_wrapper.py

# Restore backup queue
cp tasks/work_queue.json.backup tasks/work_queue.json
```

---

## Critical Files to Modify

| File | Lines | Changes | Priority |
|------|-------|---------|----------|
| `autonomous_loop.py` | 204-207, 259-284 | Fix signature, enforce verification | P0 |
| `tasks/work_queue.py` | 82-89, add fields | Store verdict, add validation | P0 |
| `claude/cli_wrapper.py` | 178-195 | Add git fallback for file detection | P0 |
| `agents/bugfix.py` | After 150 | Add fast_verify call | P1 |
| `agents/codequality.py` | After 150 | Add fast_verify call | P1 |

---

## Risk Assessment

### Low Risk (Safe to implement immediately)
- Phase 1 fixes (signature, verification enforcement) - Clear bugs with clear fixes
- Phase 3 validation (pre-execution checks) - Defensive only, no behavioral changes

### Medium Risk (Requires testing)
- Phase 2 agent integration - Could slow down agent execution by ~30-60 seconds per task
- Phase 5 auto-fix - Might change files unexpectedly if linter introduces issues

### Mitigation Strategy
1. Test each phase independently before combining
2. Run on isolated test tasks first (not production work queue)
3. Keep git commits granular for easy rollback
4. Monitor `claude-progress.txt` for unexpected behavior
5. Create backup of `work_queue.json` before each test run

---

## Post-Fix Actions

After implementing all phases:

1. **Clear work_queue.json** - Remove false-positive completions
   ```bash
   python scripts/reset_work_queue.py --status complete
   ```

2. **Recreate task definitions** - Ensure files and tests actually exist
   ```bash
   python scripts/validate_work_queue.py --fix
   ```

3. **Re-run autonomous loop** - Verify proper verification enforcement
   ```bash
   python autonomous_loop.py --project karematch --max-iterations 5
   ```

4. **Monitor first 5 tasks** - Ensure fixes work end-to-end
   - Check git commits for actual code changes
   - Verify `verification_verdict` field populated
   - Confirm no false positives

5. **Update documentation** - Reflect new verification requirements
   - Update CLAUDE.md with verification flow
   - Update STATE.md with fix completion
   - Create session handoff

---

## Dependencies

**Required** (all already available):
- `ralph/fast_verify.py` - Exists and working
- Git installed in project directories - Available
- npm scripts (`lint:fix`, `build`) - Available in karematch

**No new external dependencies needed** ✅

---

## References

- **Investigation**: Analysis of 9 tasks showing 0/9 actual completions
- **Plan File**: `/Users/tmac/.claude/plans/shimmying-mapping-crane.md`
- **Work Queue**: `/Users/tmac/Vaults/AI_Orchestrator/tasks/work_queue.json`
- **Git Repo**: `/Users/tmac/karematch` (target application)

---

## Next Session: Start with Phase 1

When beginning implementation:

1. Read this document
2. Read STATE.md for current system state
3. Start with Phase 1.1 (fix signature mismatch) - 10 minutes
4. Test immediately before proceeding
5. Continue through Phase 1 sequentially

**Expected outcome after Phase 1**: Autonomous loop properly blocks tasks without file changes, enforces verification, stores verdicts.
