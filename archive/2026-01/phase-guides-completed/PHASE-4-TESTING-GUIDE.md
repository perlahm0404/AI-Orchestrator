# Phase 4: Real-World Testing Guide

## Status: Ready for Testing

**Prerequisites Complete**:
- ✅ Phase 1: CLI wrapper operational
- ✅ Phase 2: Smart prompts working
- ✅ Phase 3: Self-correction integrated
- ✅ Test queue created
- ✅ Prompt generation verified

---

## Test Work Queue Created

**File**: `tasks/test_queue.json`

Contains 3 test tasks:
1. **TEST-001**: Create hello world function (simple)
2. **QUALITY-001**: Fix TypeScript type annotation (medium)
3. **BUG-001**: Fix off-by-one error (complex)

---

## How to Run Autonomous Loop

### Option 1: Use Test Queue

```bash
# Edit autonomous_loop.py line 113 to use test_queue.json
# queue_path = Path(__file__).parent / "tasks" / "test_queue.json"

python3 autonomous_loop.py --project karematch --max-iterations 3
```

### Option 2: Use Work Queue

```bash
# Uses default work_queue.json
python3 autonomous_loop.py --project karematch --max-iterations 5
```

### Option 3: With Self-Correction Disabled

```bash
# To test without verification loop (faster, less safe)
# Modify main() to pass enable_self_correction=False
python3 autonomous_loop.py --project karematch --max-iterations 1
```

---

## What Will Happen

### Per Task Flow

```
1. Load task from queue
   ├─ Detect type (BUG/QUALITY/TEST)
   └─ Mark as in_progress

2. Generate smart prompt
   ├─ Context-aware based on type
   └─ Include test files if available

3. Execute via Claude CLI
   ├─ Run: claude --print --dangerously-skip-permissions "prompt"
   ├─ Timeout: 5 minutes
   └─ Parse output for changed files

4. [If self-correction enabled] Verify changes
   ├─ Run lint (changed files only)
   ├─ Run typecheck (incremental)
   ├─ Run related tests
   └─ If FAIL → analyze & retry (max 5 attempts)

5. Git commit
   ├─ Message: "feat: {description}"
   └─ Include task ID

6. Update progress
   ├─ Mark complete or blocked
   ├─ Write to claude-progress.txt
   └─ Save queue

7. Brief pause (rate limiting)
   └─ 3 second delay

8. Next task or exit
```

---

## Expected Results

### Success Scenarios

**TEST-001** (Create hello world):
- Expected: 1 attempt, ~30-60s
- Prompt type: TEST (quality prompt)
- Files: test-hello.ts created
- Verification: Should pass (no existing tests)

**QUALITY-001** (Fix type annotation):
- Expected: 1-2 attempts, ~1-2min
- Prompt type: QUALITY (type_annotation)
- Files: test-types.ts modified
- Verification: Typecheck should pass

**BUG-001** (Fix off-by-one):
- Expected: 2-3 attempts, ~2-4min
- Prompt type: BUG (bugfix prompt)
- Files: test-array.ts modified
- Verification: Tests must pass

### Failure Scenarios

**Common failures**:
- File doesn't exist yet → Claude creates it
- Lint fails → Auto-fix applies
- Type errors → Retry with error context
- Test failures → Retry with failure details
- Max retries exceeded → Mark as blocked

---

## Monitoring Output

### What to Watch For

**Good Signs** ✅:
```
🚀 Executing task via Claude CLI...
   Prompt type: BUG
✅ Task executed successfully (15249ms)
   Changed files: ['test-array.ts']

🔍 Running fast verification...
  🔍 Tier 1: Running lint...
     PASS (450ms)
  🔍 Tier 2: Running typecheck...
     PASS (2100ms)
  🔍 Tier 3: Running related tests...
     PASS (1800ms)

✅ Verification passed!
✅ Changes committed to git
```

**Warning Signs** ⚠️:
```
❌ Verification failed: Lint errors found
   Duration: 450ms

📋 Fix Strategy: run_autofix
   Running: npm run lint:fix
   ✅ Lint auto-fix completed
```

**Error Signs** ❌:
```
❌ Task failed: Timeout after 300 seconds
❌ Exception during execution: Claude CLI not found
❌ Max retries exceeded (5/5)
```

---

## Metrics to Collect

### Per Task

Track in a spreadsheet or log:

| Metric | Description | Example |
|--------|-------------|---------|
| Task ID | Identifier | TEST-001 |
| Type | BUG/QUALITY/TEST | BUG |
| Attempts | Retry count | 2 |
| Duration | Total time | 125s |
| Execution Time | Claude execution | 45s |
| Verification Time | Fast verify | 35s |
| Result | Success/Failed/Blocked | Success |
| Files Changed | Modified files | test-array.ts |
| Error (if any) | Failure reason | Type errors |

### Overall

- **Success Rate**: Completed / Total tasks
- **Average Attempts**: Total attempts / Completed tasks
- **Average Duration**: Total time / Completed tasks
- **Verification Pass Rate**: Passed first time / Total
- **Self-Correction Success**: Fixed by retry / Total retries

---

## Verification Steps

### Before Running

1. **Check Claude CLI**:
   ```bash
   claude --version  # Should show 2.0.76 or later
   claude auth status  # Should show "authenticated"
   ```

2. **Check Test Suite**:
   ```bash
   cd /Users/tmac/karematch
   npm run lint  # Should work
   npx tsc --noEmit  # Should work
   npm test  # Should work (may have failures)
   ```

3. **Check Git Status**:
   ```bash
   cd /Users/tmac/karematch
   git status  # Should be clean or have expected changes
   git log --oneline -5  # Check recent commits
   ```

### During Execution

1. **Monitor output** in terminal
2. **Check progress file**: `cat /Users/tmac/karematch/claude-progress.txt`
3. **Check git log**: `git log --oneline -5` (should see new commits)
4. **Check queue**: `cat tasks/test_queue.json` (status updates)

### After Completion

1. **Review changes**:
   ```bash
   git diff HEAD~3..HEAD  # See last 3 commits
   ```

2. **Run full verification**:
   ```bash
   npm run lint
   npx tsc --noEmit
   npm test
   ```

3. **Check queue final state**:
   ```bash
   cat tasks/test_queue.json | jq '.features[] | {id, status, attempts, error}'
   ```

---

## Troubleshooting

### Issue: Claude CLI not found

**Error**: `Claude CLI not found in PATH`

**Solution**:
```bash
# Check if installed
which claude

# If not installed, install Claude Code
# Visit: https://claude.com/code
```

### Issue: Authentication failed

**Error**: `Claude CLI not authenticated`

**Solution**:
```bash
claude auth login
# Follow prompts to authenticate
```

### Issue: Timeout errors

**Error**: `Timeout after 300 seconds`

**Solution**:
- Increase timeout in `cli_wrapper.py`: `timeout=600` (10 min)
- Or break task into smaller subtasks

### Issue: Verification always fails

**Error**: Same verification error on every retry

**Check**:
1. Is the file in the right location?
2. Are tests expecting different behavior?
3. Is Ralph too strict?

**Solution**:
- Review verification output
- Check if tests need updating
- Consider disabling self-correction for complex tasks

### Issue: Git commit fails

**Error**: `Git commit failed`

**Check**:
1. Are there uncommitted changes?
2. Is git configured?

**Solution**:
```bash
git config user.name "AI Agent"
git config user.email "agent@local"
```

---

## Safety Notes

### Before Production Use

1. **Test on feature branch**: Don't run on `main`
2. **Backup important work**: `git stash` or commit first
3. **Review all commits**: Before pushing to remote
4. **Start with simple tasks**: Build confidence gradually
5. **Monitor closely**: Don't leave running unattended

### Rate Limiting

- Current: 3 second delay between tasks
- Claude API has rate limits
- May need longer delays for many tasks

### Cost Awareness

- Each task calls Claude API
- 3 tasks × 5 retries = up to 15 API calls
- Monitor usage in Claude dashboard

---

## Next Steps After Testing

### If Tests Pass ✅

1. **Document results** in session handoff
2. **Commit test queue** and results
3. **Update STATE.md** with Phase 4 completion
4. **Plan Phase 5** (if needed)

### If Tests Fail ❌

1. **Analyze failures**: Which tasks? What errors?
2. **Improve prompts**: Based on failure patterns
3. **Adjust retry logic**: If needed
4. **Re-test**: With improvements

### Performance Tuning

Based on results:
- Adjust timeout values
- Tune verification thresholds
- Improve error analysis
- Optimize prompt templates

---

## Success Criteria

Phase 4 is complete when:

- ✅ At least 2/3 test tasks complete successfully
- ✅ Self-correction loop demonstrates value (fixes errors)
- ✅ No regressions introduced
- ✅ Performance is acceptable (<5 min per task)
- ✅ Results documented in session handoff

---

## Ready to Test!

Everything is in place. The autonomous agent v2 system is ready for real-world testing.

**Command to run**:
```bash
cd /Users/tmac/Vaults/AI_Orchestrator
python3 autonomous_loop.py --project karematch --max-iterations 3
```

**What you'll see**:
- Task-by-task execution
- Real-time verification
- Automatic retries
- Git commits
- Progress updates

**Time estimate**: 5-15 minutes for 3 tasks

🚀 **Good luck with testing!**
