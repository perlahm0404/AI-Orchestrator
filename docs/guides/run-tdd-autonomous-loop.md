# Run Autonomous Loop with TDD - KareMatch Bug Fixes

## 🎯 Mission: Fix 70 Test Failures Using TDD Approach

**Work Queue**: `tasks/karematch_tdd_queue.json`

**TDD Philosophy**: Tests define the contract. Read tests first, understand expectations, then implement to satisfy tests.

---

## 📋 Tasks Overview (9 Tasks)

### Category 1: Appointment Routes (~20 failures)
- **BUG-APT-001**: Fix 404 errors on appointment endpoints
- **BUG-APT-002**: Fix route registration

### Category 2: Credentialing Wizard (~7 failures)
- **BUG-CRED-001**: Fix wizard API endpoints

### Category 3: Therapist Matcher (~5 failures)
- **BUG-MATCH-001**: Fix boundary conditions
- **BUG-MATCH-002**: Fix score calculation invariants

### Category 4: MFA Tests (2 test files)
- **BUG-MFA-001**: Fix email functionality
- **BUG-MFA-002**: Fix SMS functionality

### Category 5: Proximity Tests (~3 failures)
- **BUG-PROX-001**: Fix distance calculations

### Category 6: Test Interference
- **TEST-INTERF-001**: Fix shared state causing interference

---

## 🚀 Command to Run

### Option 1: Run All Tasks (Recommended)
```bash
cd /Users/tmac/Vaults/AI_Orchestrator

# Backup current work queue
cp tasks/work_queue.json tasks/work_queue.backup.json

# Use TDD queue
cp tasks/karematch_tdd_queue.json tasks/work_queue.json

# Run autonomous loop
python3 autonomous_loop.py --project karematch --max-iterations 9

# Restore original queue when done
# cp tasks/work_queue.backup.json tasks/work_queue.json
```

### Option 2: Run One Category at a Time
```bash
# Appointment routes first (high priority)
python3 autonomous_loop.py --project karematch --max-iterations 2

# Then credentialing
python3 autonomous_loop.py --project karematch --max-iterations 1

# Then matcher
python3 autonomous_loop.py --project karematch --max-iterations 2

# etc.
```

### Option 3: Dry Run (Test Without Executing)
```bash
# Check queue format
python3 -c "
from tasks.work_queue import WorkQueue
from pathlib import Path
queue = WorkQueue.load(Path('tasks/karematch_tdd_queue.json'))
print(f'Loaded {len(queue.features)} tasks')
for t in queue.features:
    print(f'  {t.id}: {t.description[:60]}...')
"
```

---

## 📝 What Will Happen

### Per Task Flow (TDD-Focused)

```
1. Load task (e.g., BUG-APT-001)
   ↓
2. Generate TDD-focused prompt:
   "Fix appointment routes returning 404 - TDD approach:
    First verify test expectations, then fix route handlers to match.
    Focus on /api/appointments endpoints."
   ↓
3. Execute via Claude CLI
   - Claude will READ the test files first
   - Understand what tests expect
   - Implement to satisfy tests
   ↓
4. Fast Verification
   - Lint (changed files)
   - Typecheck (incremental)
   - Run related tests
   ↓
5. If tests FAIL → Self-Correct
   - Analyze failure (lint/type/test)
   - Auto-fix lint errors
   - Send error context to Claude
   - Retry (max 5 attempts)
   ↓
6. If tests PASS → Git Commit
   - Commit with task ID
   - Update progress file
   - Mark task complete
   ↓
7. Next task
```

---

## 🎯 Expected Results

### Success Metrics

| Metric | Target | Optimistic |
|--------|--------|------------|
| Tasks completed | 7/9 (78%) | 9/9 (100%) |
| Test failures fixed | 50/70 (71%) | 70/70 (100%) |
| Average attempts per task | 2-3 | 1-2 |
| Total time | 30-45 min | 15-25 min |

### Per Task Estimates

| Task | Complexity | Est. Time | Est. Attempts |
|------|-----------|-----------|---------------|
| BUG-APT-001 | Medium | 3-5 min | 2-3 |
| BUG-APT-002 | Easy | 2-3 min | 1-2 |
| BUG-CRED-001 | Medium | 3-5 min | 2-3 |
| BUG-MATCH-001 | Hard | 5-8 min | 3-4 |
| BUG-MATCH-002 | Medium | 3-5 min | 2-3 |
| BUG-MFA-001 | Easy | 2-3 min | 1-2 |
| BUG-MFA-002 | Easy | 2-3 min | 1-2 |
| BUG-PROX-001 | Easy | 2-3 min | 1-2 |
| TEST-INTERF-001 | Hard | 5-8 min | 3-5 |

**Total**: 27-45 minutes

---

## 📊 Monitoring Progress

### Real-Time Monitoring

```bash
# Terminal 1: Run autonomous loop
python3 autonomous_loop.py --project karematch --max-iterations 9

# Terminal 2: Watch progress file
tail -f /Users/tmac/karematch/claude-progress.txt

# Terminal 3: Watch git commits
watch -n 5 'cd /Users/tmac/karematch && git log --oneline -10'

# Terminal 4: Watch test results
cd /Users/tmac/karematch
npm test -- --reporter=dot --watch
```

### Check Status

```bash
# Queue status
cat tasks/work_queue.json | jq '.features[] | {id, status, attempts, error}'

# Test count
cd /Users/tmac/karematch
npm test 2>&1 | grep -E "passing|failing"

# Git commits
git log --oneline --since="1 hour ago" | wc -l
```

---

## 🎓 TDD Principles Applied

### Each Task Follows TDD

1. **Read tests first** - Understand contract
2. **Understand expectations** - What should code do?
3. **Implement to satisfy** - Write code that passes tests
4. **Verify** - Run tests to confirm
5. **Refactor** - If needed, improve while keeping tests green

### Prompts Emphasize TDD

Example for BUG-APT-001:
```
"Fix appointment routes returning 404 - TDD approach:
 First verify test expectations, then fix route handlers to match."
```

This tells Claude to:
1. ✅ Read the test files
2. ✅ Understand what tests expect
3. ✅ Fix implementation to match
4. ✅ NOT guess or assume behavior

---

## 🔍 Verification Strategy

### Fast Verification (Per Attempt)

```
Tier 1: Lint (5s)
  ↓
Tier 2: Typecheck (30s)
  ↓
Tier 3: Related Tests (60s)
  ↓
Total: ~90s per verification
```

### Full Verification (After All Tasks)

```bash
cd /Users/tmac/karematch

# Run full test suite
npm test

# Expected improvement:
# Before: 70 failures, 759 passing
# After:  <20 failures, >810 passing
```

---

## 🚨 Error Handling

### Common Issues & Solutions

**Issue 1: Timeout on complex tasks**
```bash
# Increase timeout in autonomous_loop.py
# timeout=300 → timeout=600
```

**Issue 2: Tests still failing after 5 retries**
```bash
# Check what went wrong
cat tasks/work_queue.json | jq '.features[] | select(.status=="blocked")'

# Review error
# Manually investigate and update prompt
```

**Issue 3: Test interference persists**
```bash
# Run tests in isolation
npm test -- --maxWorkers=1

# May need manual investigation
```

---

## 📈 Success Criteria

### Must Have (Minimum Success)
- ✅ At least 5/9 tasks complete (56%)
- ✅ At least 40 test failures fixed (57%)
- ✅ No regressions introduced
- ✅ All changes committed to git

### Should Have (Good Success)
- ✅ At least 7/9 tasks complete (78%)
- ✅ At least 55 test failures fixed (79%)
- ✅ Average <3 attempts per task
- ✅ Complete in <45 minutes

### Stretch Goal (Excellent Success)
- ✅ All 9/9 tasks complete (100%)
- ✅ All 70 test failures fixed (100%)
- ✅ Average <2 attempts per task
- ✅ Complete in <30 minutes

---

## 🎯 Post-Execution Analysis

### After Run, Generate Report

```bash
# Summary
cat tasks/work_queue.json | jq '{
  total: .features | length,
  completed: [.features[] | select(.status=="complete")] | length,
  blocked: [.features[] | select(.status=="blocked")] | length,
  pending: [.features[] | select(.status=="pending")] | length
}'

# Per-task results
cat tasks/work_queue.json | jq '.features[] | {
  id,
  status,
  attempts,
  error: (.error // "none")
}'

# Test improvement
cd /Users/tmac/karematch
npm test 2>&1 | grep -E "Tests:|passing|failing"
```

---

## 🚀 Ready to Run!

**Command**:
```bash
cd /Users/tmac/Vaults/AI_Orchestrator
cp tasks/karematch_tdd_queue.json tasks/work_queue.json
python3 autonomous_loop.py --project karematch --max-iterations 9
```

**Expected Duration**: 30-45 minutes
**Expected Success**: 7-9 tasks complete
**Expected Impact**: 50-70 test failures fixed

---

## 📚 What This Tests

1. **TDD Workflow** - Can AI follow test-first approach?
2. **Self-Correction** - Can it fix its own errors?
3. **Test Reading** - Can it understand test expectations?
4. **Fast Verification** - Does 90s verification work?
5. **Git Automation** - Does commit-per-task work?
6. **Real-World Scale** - Can it handle 9 production bugs?

---

**Let's fix those 70 test failures! 🎉**
