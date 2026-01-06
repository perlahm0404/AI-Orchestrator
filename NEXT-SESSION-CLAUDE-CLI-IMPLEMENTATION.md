# Next Session: Implement Claude Code CLI Integration

## Context

We've built the autonomous agent v2 infrastructure but need to implement the critical missing piece: **Claude Code CLI integration**.

**Branch**: `feature/autonomous-agent-v2`
**Status**: Infrastructure complete, execution layer missing

---

## What's Complete ✅

- ✅ Work queue system (`tasks/work_queue.py`)
- ✅ Fast verification (`ralph/fast_verify.py`) - 30-second checks
- ✅ Self-correction loop (`agents/self_correct.py`) - Error analysis
- ✅ Simplified governance (`governance/enforce.py`)
- ✅ Autonomous loop skeleton (`autonomous_loop.py`)
- ✅ Comprehensive tests
- ✅ Full documentation

---

## What's Missing ❌

### Critical: Claude Code CLI Integration

**Current state**: Placeholders everywhere
```python
# TODO: This is where Claude Code CLI would execute
print("⚠️  Claude Code CLI execution not yet implemented")
```

**What needs to happen**: Replace placeholders with actual subprocess calls to `claude` command

---

## Your Task: Implement Phase 1

**Goal**: Get basic Claude Code CLI execution working

**Time estimate**: 2-3 hours

---

## Step-by-Step Implementation

### Step 1: Create Claude Module Structure (15 min)

```bash
# Create directory
mkdir -p claude
touch claude/__init__.py

# Create test directory
mkdir -p tests/claude
touch tests/claude/__init__.py
```

### Step 2: Implement CLI Wrapper (45 min)

**File**: `claude/cli_wrapper.py`

Copy the implementation from the execution plan:
- See: `docs/planning/v5-CLAUDE-CLI-EXECUTION-PLAN.md` (Phase 1, Section 1.1)

**Key components**:
```python
class ClaudeCliWrapper:
    def execute_task(self, prompt: str, files: List[str], timeout: int) -> ClaudeResult
    def _parse_changed_files(self, output: str) -> List[str]
```

### Step 3: Write Tests (30 min)

**File**: `tests/claude/test_cli_wrapper.py`

Copy the test implementation from the execution plan.

**Run tests**:
```bash
pytest tests/claude/test_cli_wrapper.py -v
```

### Step 4: Integration with autonomous_loop.py (30 min)

Replace this placeholder code:
```python
# Line ~159-171 in autonomous_loop.py
# 4. TODO: Run Claude Code CLI here
print("⚠️  Claude Code CLI execution not yet implemented")
```

With this:
```python
# 4. Run Claude Code CLI
from claude.cli_wrapper import ClaudeCliWrapper

wrapper = ClaudeCliWrapper(actual_project_dir)

try:
    result = wrapper.execute_task(
        prompt=task.description,
        files=[task.file],
        timeout=300
    )

    if result.success:
        print(f"✅ Task executed successfully")
        print(f"   Changed files: {result.files_changed}")
        changed_files = result.files_changed
    else:
        print(f"❌ Task failed: {result.error}")
        queue.mark_blocked(task.id, result.error or "Execution failed")
        queue.save(queue_path)
        update_progress_file(actual_project_dir, task, "blocked", result.error or "Unknown error")
        continue

except Exception as e:
    print(f"❌ Exception during execution: {e}")
    queue.mark_blocked(task.id, str(e))
    queue.save(queue_path)
    update_progress_file(actual_project_dir, task, "blocked", str(e))
    continue
```

### Step 5: Manual Testing (30 min)

#### 5.1 Check Claude CLI is installed
```bash
claude --version
```

If not installed, install from: https://claude.com/code

#### 5.2 Check authentication
```bash
claude auth status
```

If not authenticated:
```bash
claude auth login
```

#### 5.3 Test wrapper manually
```bash
python -c "
from claude.cli_wrapper import ClaudeCliWrapper
from pathlib import Path

wrapper = ClaudeCliWrapper(Path('/Users/tmac/karematch'))
result = wrapper.execute_task(
    prompt='List the files in src/',
    files=[],
    timeout=30
)

print(f'Success: {result.success}')
print(f'Output: {result.output[:200]}...')
print(f'Error: {result.error}')
"
```

#### 5.4 Test autonomous loop
```bash
# Create simple test task
cat > tasks/test_simple.json <<EOF
{
  "project": "karematch",
  "features": [
    {
      "id": "TEST-CLI-001",
      "description": "List all TypeScript files in src/ directory",
      "file": "src/",
      "status": "pending",
      "tests": [],
      "passes": false,
      "error": null,
      "attempts": 0,
      "last_attempt": null,
      "completed_at": null
    }
  ]
}
EOF

# Run with test queue
python autonomous_loop.py --project karematch --max-iterations 1
```

---

## Success Criteria

By the end of this session, you should have:

- ✅ `claude/cli_wrapper.py` implemented with subprocess calls
- ✅ `tests/claude/test_cli_wrapper.py` passing
- ✅ Claude CLI verified as installed and authenticated
- ✅ Manual test of wrapper succeeds
- ✅ `autonomous_loop.py` successfully calls Claude CLI
- ✅ No more placeholder code in autonomous_loop.py

---

## Expected Outcome

After this session:
```bash
# This should work:
python autonomous_loop.py --project karematch --max-iterations 1

# Output should show:
# ✅ Task executed successfully
# Changed files: [...]
# (Instead of placeholder message)
```

---

## Troubleshooting

### Issue: Claude CLI not found
```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code
# OR follow instructions at https://claude.com/code
```

### Issue: Authentication failed
```bash
claude auth login
# Follow prompts to authenticate via claude.ai
```

### Issue: Timeout errors
```python
# Increase timeout in wrapper.execute_task()
result = wrapper.execute_task(prompt=..., timeout=600)  # 10 minutes
```

### Issue: Output parsing fails
```python
# Debug by printing raw output
print(f"Raw output:\n{result.output}")
# Adjust _parse_changed_files() logic
```

---

## Files to Reference

1. **Execution Plan**: `docs/planning/v5-CLAUDE-CLI-EXECUTION-PLAN.md`
   - Full code examples for Phase 1

2. **Current Placeholders**:
   - `autonomous_loop.py` line ~159-171
   - `agents/self_correct.py` line ~142-147, ~183-185

3. **Integration Guide**: `docs/CLAUDE-CODE-INTEGRATION.md`
   - Options for CLI vs Extension integration

---

## Next Steps After This Session

Once Phase 1 is complete:

**Phase 2**: Smart Prompt Generation (Day 2)
- Create `claude/prompts.py`
- Context-aware prompts for bugs vs quality vs features
- See execution plan section 2.1

**Phase 3**: Full Integration (Day 3)
- Connect to `agents/self_correct.py`
- End-to-end autonomous loop
- See execution plan section 3.1

**Phase 4**: Real Testing (Day 4)
- Test with real KareMatch bugs
- Measure success rate
- See execution plan section 4.1

---

## Commit Message Template

When you're done:

```bash
git add claude/ tests/claude/ autonomous_loop.py
git commit -m "feat: Implement Claude Code CLI integration (Phase 1)

Add basic Claude CLI subprocess wrapper for autonomous agent execution.

## Changes

- claude/cli_wrapper.py: Subprocess interface to \`claude\` command
  - execute_task(): Run prompts via CLI
  - _parse_changed_files(): Extract modified files from output
  - Error handling for timeouts, auth failures

- tests/claude/test_cli_wrapper.py: Unit tests for wrapper
  - Test initialization
  - Test output parsing
  - Test error handling

- autonomous_loop.py: Replace placeholder with actual CLI calls
  - Integrate ClaudeCliWrapper
  - Handle execution results
  - Update queue based on success/failure

## Testing

- ✅ Unit tests pass
- ✅ Manual CLI test succeeds
- ✅ Autonomous loop executes real task

## Next Steps

- Phase 2: Smart prompt generation
- Phase 3: Full integration with self_correct
- Phase 4: Real-world testing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"
```

---

## Questions to Ask If Stuck

1. **Is Claude CLI installed?** → Run `claude --version`
2. **Is it authenticated?** → Run `claude auth status`
3. **Can you call it manually?** → Run `claude --prompt "Say hello"`
4. **Is the project path correct?** → Check adapter.get_context().project_path
5. **Are tests passing?** → Run `pytest tests/claude/ -v`

---

## Time Allocation

| Task | Time | Priority |
|------|------|----------|
| Create module structure | 15 min | High |
| Implement cli_wrapper.py | 45 min | **Critical** |
| Write tests | 30 min | High |
| Integrate with autonomous_loop | 30 min | **Critical** |
| Manual testing | 30 min | High |
| Debug/fix issues | 30 min | Medium |
| **Total** | **3 hours** | |

---

## Ready to Start?

Your first command:
```bash
cd /Users/tmac/Vaults/AI_Orchestrator
git checkout feature/autonomous-agent-v2
mkdir -p claude tests/claude
```

Then follow Step 2 from the execution plan!

**Good luck! 🚀**
