# Optimal Workflows: When to Use AI_Orchestrator vs Direct Repo Work

**Last Updated**: 2026-01-18
**Post-Optimization**: Phase 2 Complete (92.8% token reduction)

---

## Token Cost Reference (After Phase 2)

### Interactive Session Startup (Manual Claude Code)

**What loads**: CLAUDE.md only (9-step protocol NOT auto-injected)

| Repository | CLAUDE.md | Startup Cost | Use Case |
|------------|-----------|--------------|----------|
| **AI_Orchestrator** | 1,948 tokens | **1,948 tokens** | Meta-work on orchestrator itself |
| **KareMatch** | ~1,380 tokens | **1,380 tokens** | Direct work in KareMatch |
| **CredentialMate** | ~1,380 tokens | **1,380 tokens** | Direct work in CredentialMate |

**When you run**: `cd /Users/tmac/1_REPOS/karematch && claude` (interactive)

**Advantage**: Lightweight, fast startup, good for exploration and single tasks

---

### Autonomous Loop Startup (via autonomous_loop.py)

**What loads**: CLAUDE.md + Full 9-step protocol + Governance contracts

| Repository | Full Protocol | Governance | Total Startup | Tasks/Session |
|------------|---------------|------------|---------------|---------------|
| **AI_Orchestrator** | ~7,786 tokens | 3,253 tokens | **11,039 tokens** | 15-20 |
| **KareMatch** | ~6,266 tokens | 0 tokens | **6,266 tokens** | 25-35 |
| **CredentialMate** | ~5,034 tokens | 0 tokens | **5,034 tokens** | 35-45 |

**Breakdown (AI_Orchestrator example)**:
```
CLAUDE.md:                1,948 tokens
STATE.md:                   645 tokens
CATALOG.md:               1,960 tokens
Session file:             2,990 tokens
global-state-cache.md:      133 tokens
Work queue:                 260 tokens
─────────────────────────────────────
Protocol subtotal:        7,936 tokens
Governance contracts:     3,253 tokens
─────────────────────────────────────
TOTAL:                   11,189 tokens
```

**When you run**: `python autonomous_loop.py --project karematch --max-iterations 100`

**Advantage**: Full context, autonomous execution, multi-task capability

---

### Simple Task Completion Cost

**Single bugfix/test task** (no autonomous loop):

| Scenario | Startup | Task Execution | Total | Use Case |
|----------|---------|----------------|-------|----------|
| **Interactive (KareMatch)** | 1,380 | ~5,000 | **~6,380 tokens** | Quick fix, exploration |
| **Interactive (CredentialMate)** | 1,380 | ~5,000 | **~6,380 tokens** | Quick fix, exploration |
| **Autonomous (KareMatch)** | 6,266 | ~5,000 | **~11,266 tokens** | Full context, verification |
| **Autonomous (CredentialMate)** | 5,034 | ~5,000 | **~10,034 tokens** | Full context, verification |

**Where "Task Execution" includes**:
- Reading relevant code files (~2,000 tokens)
- Making edits (~1,000 tokens)
- Running tests (~1,000 tokens)
- Ralph verification (~1,000 tokens)

---

## Decision Matrix: When to Use What

### Use Direct Repo Work (Interactive Claude Code)

**Command**: `cd /Users/tmac/1_REPOS/karematch && claude`

**When**:
- ✅ Quick exploration ("what does this function do?")
- ✅ Single file changes
- ✅ Reading documentation
- ✅ Understanding error messages
- ✅ Testing ideas/prototypes
- ✅ Manual debugging sessions
- ✅ Code review
- ✅ 1-3 related changes max

**Token Cost**: 1,380 tokens (just CLAUDE.md)

**Pros**:
- Fast startup (1.4k tokens vs 5-11k)
- Interactive feedback
- Good for learning/exploration
- No governance overhead

**Cons**:
- No full context (no STATE.md, session files, etc.)
- No autonomous retry capability
- No Ralph auto-verification
- No Wiggum iteration control
- Manual work queue management

**Example Tasks**:
```bash
# Quick bug investigation
cd /Users/tmac/1_REPOS/karematch && claude
> "Why is the login test failing? Show me the test file and the auth module"

# Single feature addition
cd /Users/tmac/1_REPOS/credentialmate && claude
> "Add a new validation rule for phone numbers in the User model"

# Code review
cd /Users/tmac/1_REPOS/karematch && claude
> "Review the recent changes to the matching algorithm for performance issues"
```

---

### Use AI_Orchestrator Autonomous Loop

**Command**: `python autonomous_loop.py --project karematch --max-iterations 50`

**When**:
- ✅ Multiple related tasks (5+ tasks)
- ✅ Work queue processing
- ✅ Bug discovery and fixes
- ✅ Systematic refactoring
- ✅ Cross-file changes
- ✅ Need Ralph verification on every change
- ✅ Need Wiggum retry capability
- ✅ Want autonomous iteration until PASS

**Token Cost**:
- KareMatch: 6,266 tokens (startup) + ~5k per task
- CredentialMate: 5,034 tokens (startup) + ~5k per task

**Pros**:
- Full context (STATE.md, session files, cross-repo state)
- Autonomous retry (15-50 iterations per task)
- Ralph auto-verification
- Work queue integration
- Can process 25-45 tasks per session
- Wiggum stop hooks prevent premature exit

**Cons**:
- Higher startup cost (5-11k tokens)
- Less interactive (batch processing)
- Governance overhead

**Example Tasks**:
```bash
# Process work queue (multiple bugs)
python autonomous_loop.py --project karematch --max-iterations 100
# Loads 253 task sequences, processes until queue empty or max iterations

# Bug discovery and fixes
aibrain discover-bugs --project credentialmate
python autonomous_loop.py --project credentialmate --max-iterations 50
# Discovers bugs, generates tasks, processes them autonomously

# Systematic refactoring
# Add tasks to work queue manually, then:
python autonomous_loop.py --project karematch --max-iterations 30
```

---

## Optimal Workflows by Task Type

### 🐛 Debugging (Single Bug)

**Recommended**: Direct repo work (interactive)

**Workflow**:
```bash
# 1. Navigate to repo
cd /Users/tmac/1_REPOS/karematch

# 2. Start interactive Claude session
claude

# 3. Investigate
> "The login test is failing. Show me the test file and explain what's wrong"

# 4. Fix
> "Fix the issue and run the test again"

# 5. Verify
> "Run all auth tests to make sure nothing else broke"

# 6. Commit
> "Commit these changes with an appropriate message"
```

**Token Cost**: ~6,380 tokens total (1,380 startup + 5,000 execution)

**Why**: Fast, interactive, good for single issues

---

### 🐛 Debugging (Multiple Bugs from Discovery)

**Recommended**: AI_Orchestrator autonomous loop

**Workflow**:
```bash
# 1. Run bug discovery
cd /Users/tmac/1_REPOS/AI_Orchestrator
aibrain discover-bugs --project karematch

# Example output:
# 📋 Task Summary:
#   🆕 [P0] TEST-LOGIN-001: Fix 2 test errors (NEW REGRESSION)
#   🆕 [P0] TYPE-SESSION-002: Fix 1 typecheck error (NEW REGRESSION)
#      [P1] LINT-MATCHING-003: Fix 3 lint errors (baseline)
#      [P2] GUARD-CONFIG-007: Fix 2 guardrails errors (baseline)

# 2. Process work queue autonomously
python autonomous_loop.py --project karematch --max-iterations 100

# Agent will:
# - Load full context (STATE.md, session files, contracts)
# - Process each task with Wiggum retry (15-50 iterations)
# - Run Ralph verification after each change
# - Auto-commit on PASS
# - Continue until queue empty or max iterations
```

**Token Cost**: 6,266 startup + (~11,000 × 4 tasks) = **~50,266 tokens total**

**Why**: Processes multiple bugs autonomously, Ralph verification on each, auto-commits on PASS

---

### ✨ New Feature (Simple, Single File)

**Recommended**: Direct repo work (interactive)

**Workflow**:
```bash
# 1. Navigate to repo
cd /Users/tmac/1_REPOS/credentialmate

# 2. Start interactive Claude session
claude

# 3. Implement
> "Add a new API endpoint POST /api/credentials/verify that validates a credential ID"

# 4. Test
> "Write a test for this endpoint and run it"

# 5. Verify
> "Run Ralph verification to check code quality"

# 6. Commit
> "Commit with message about the new endpoint"
```

**Token Cost**: ~8,000 tokens total (1,380 startup + 6,620 execution)

**Why**: Fast, interactive, good for focused work

---

### ✨ New Feature (Complex, Multi-File)

**Recommended**: AI_Orchestrator autonomous loop

**Workflow**:
```bash
# 1. Add feature task to work queue
cd /Users/tmac/1_REPOS/AI_Orchestrator
aibrain tasks add \
  --project karematch \
  --id FEAT-MATCHING-001 \
  --description "Implement advanced matching algorithm with ML scoring" \
  --files "src/matching/algorithm.ts,src/matching/scorer.ts,tests/matching.test.ts" \
  --type feature \
  --max-iterations 50

# 2. Run autonomous loop
python autonomous_loop.py --project karematch --max-iterations 50

# Agent will:
# - Load full context (cross-repo state, past decisions)
# - Implement across multiple files
# - Write comprehensive tests
# - Iterate until Ralph PASS (up to 50 times)
# - Create git commit on success
```

**Token Cost**: 6,266 startup + ~25,000 execution = **~31,266 tokens total**

**Why**: Complex features need full context, retry capability, cross-file coordination

---

### 🧪 Test Writing

**Recommended**: Direct repo work (interactive)

**Workflow**:
```bash
# 1. Navigate to repo
cd /Users/tmac/1_REPOS/karematch

# 2. Start interactive Claude session
claude

# 3. Write tests
> "Write comprehensive tests for the UserProfile component, including edge cases"

# 4. Run tests
> "Run the tests and fix any failures"

# 5. Check coverage
> "What's the test coverage for UserProfile now?"

# 6. Commit
> "Commit the new tests"
```

**Token Cost**: ~7,000 tokens total (1,380 startup + 5,620 execution)

**Why**: Test writing is often iterative and benefits from interactive feedback

---

### 🔄 Refactoring

**Recommended**: Depends on scope

#### Small Refactor (1-3 files)
**Use**: Direct repo work (interactive)

```bash
cd /Users/tmac/1_REPOS/karematch && claude
> "Refactor the auth module to use async/await instead of promises"
```

**Token Cost**: ~8,000 tokens

#### Large Refactor (5+ files)
**Use**: AI_Orchestrator autonomous loop

```bash
# Add refactor tasks to work queue
aibrain tasks add --project karematch --id REFACTOR-AUTH-001 \
  --description "Convert all auth modules to async/await" \
  --type refactor --max-iterations 30

python autonomous_loop.py --project karematch --max-iterations 50
```

**Token Cost**: 6,266 startup + ~40,000 execution = **~46,266 tokens**

---

## Cross-Repo Work

### When Work Spans Multiple Repos

**Problem**: Need to make coordinated changes across KareMatch and CredentialMate

**Recommended**: AI_Orchestrator with cross-repo state sync

**Workflow**:
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# 1. Update AI_Orchestrator STATE.md with cross-repo context
# This triggers auto-sync to karematch/.aibrain/global-state-cache.md

# 2. Work on first repo
python autonomous_loop.py --project karematch --max-iterations 30
# Agent has full context of CredentialMate state via global-state-cache.md

# 3. Work on second repo
python autonomous_loop.py --project credentialmate --max-iterations 30
# Agent has full context of KareMatch state via global-state-cache.md
```

**Token Cost**:
- KareMatch session: 6,266 startup + ~30,000 execution = ~36,266 tokens
- CredentialMate session: 5,034 startup + ~30,000 execution = ~35,034 tokens
- **Total**: ~71,300 tokens (but ensures consistency across repos)

**Why**: Cross-repo state cache ensures agents know about work in other repos

---

## Token Efficiency Recommendations

### Maximize Efficiency (Lowest Token Cost)

**For**: Simple tasks, single files, exploration

**Do**:
1. `cd` into target repo (karematch or credentialmate)
2. Start interactive Claude session
3. Work on 1-3 related tasks
4. Commit when done

**Token Cost**: 1,380 startup + ~5,000 per task = **~6,380 per task**

**Example**:
```bash
cd /Users/tmac/1_REPOS/karematch
claude
> "Fix the login timeout bug and add a test for it"
# Cost: ~6,380 tokens (1 session, 1 task)
```

---

### Maximize Throughput (Most Tasks per Session)

**For**: Multiple bugs, systematic work, work queue processing

**Do**:
1. Run bug discovery (generates work queue)
2. Run autonomous loop with high max-iterations
3. Let agents process 25-45 tasks per session

**Token Cost**: 5,034-6,266 startup + (~11,000 × 35 tasks) = **~385,000 tokens per 35-task session**

**But**: Within 200k context window with auto-summarization, processes ~25-35 tasks before hitting limit

**Example**:
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator
aibrain discover-bugs --project karematch
python autonomous_loop.py --project karematch --max-iterations 100
# Cost: ~6,266 startup + processes until context limit
# Result: 25-35 tasks completed autonomously
```

---

### Maximize Quality (Best Results)

**For**: Complex features, HIPAA-critical work, production deployments

**Do**:
1. Use autonomous loop for full context
2. Enable Ralph verification on every change
3. Use Wiggum retry (high max-iterations)
4. Let agent iterate until PASS

**Token Cost**: Higher (5-11k startup + retries), but ensures quality

**Example**:
```bash
# High-stakes HIPAA work
python autonomous_loop.py --project credentialmate --max-iterations 50

# Agent will:
# - Load HIPAA compliance context
# - Verify against 5-layer deletion defense
# - Run multi-tenant permission tests
# - Iterate up to 50 times until Ralph PASS
# - No shortcuts, no --no-verify bypasses
```

**Cost**: ~5,034 startup + (~11,000 × retries) = **~50,000+ tokens**

**Worth it**: For HIPAA compliance, production safety, critical features

---

## Practical Decision Tree

```
┌─────────────────────────────────┐
│ What are you trying to do?     │
└─────────────────┬───────────────┘
                  │
                  ├─ Single bug/task, simple
                  │  └─> Direct repo work (interactive)
                  │      cd karematch && claude
                  │      Cost: ~6,380 tokens
                  │
                  ├─ Multiple bugs from discovery
                  │  └─> Autonomous loop
                  │      aibrain discover-bugs --project karematch
                  │      python autonomous_loop.py --project karematch
                  │      Cost: ~6,266 + (11k × tasks)
                  │
                  ├─ Simple feature (1-3 files)
                  │  └─> Direct repo work (interactive)
                  │      cd credentialmate && claude
                  │      Cost: ~8,000 tokens
                  │
                  ├─ Complex feature (5+ files)
                  │  └─> Autonomous loop
                  │      aibrain tasks add --project karematch
                  │      python autonomous_loop.py --project karematch
                  │      Cost: ~31,000+ tokens
                  │
                  ├─ Test writing
                  │  └─> Direct repo work (interactive)
                  │      cd karematch && claude
                  │      Cost: ~7,000 tokens
                  │
                  ├─ Small refactor (1-3 files)
                  │  └─> Direct repo work (interactive)
                  │      Cost: ~8,000 tokens
                  │
                  ├─ Large refactor (5+ files)
                  │  └─> Autonomous loop
                  │      Cost: ~46,000+ tokens
                  │
                  └─ Cross-repo work
                     └─> Autonomous loop with cross-repo state
                         Cost: ~71,000+ tokens
```

---

## Summary: Quick Reference

| Task Type | Recommended Approach | Token Cost | Command |
|-----------|---------------------|------------|---------|
| **Single bug** | Direct repo (interactive) | ~6,380 | `cd karematch && claude` |
| **Multiple bugs** | Autonomous loop | ~6,266 + (11k × tasks) | `python autonomous_loop.py --project karematch` |
| **Simple feature** | Direct repo (interactive) | ~8,000 | `cd credentialmate && claude` |
| **Complex feature** | Autonomous loop | ~31,000+ | `python autonomous_loop.py --project karematch` |
| **Test writing** | Direct repo (interactive) | ~7,000 | `cd karematch && claude` |
| **Small refactor** | Direct repo (interactive) | ~8,000 | `cd karematch && claude` |
| **Large refactor** | Autonomous loop | ~46,000+ | `python autonomous_loop.py --project karematch` |
| **Cross-repo** | Autonomous loop | ~71,000+ | `python autonomous_loop.py --project X` (both) |
| **HIPAA-critical** | Autonomous loop | ~50,000+ | `python autonomous_loop.py --project credentialmate` |

---

## Key Takeaways

1. **Interactive sessions (direct repo work)** are 3-5x cheaper in startup cost (1.4k vs 5-11k tokens)
   - Best for: Single tasks, exploration, quick fixes, learning

2. **Autonomous loop** has higher startup but processes many tasks efficiently
   - Best for: Multiple tasks, work queues, systematic work, quality-critical work

3. **Context window is 200k tokens** - you'll hit limits at:
   - Interactive: ~30 simple tasks before summarization
   - Autonomous: ~25-35 complex tasks before summarization

4. **After Phase 2 optimization**, startup costs are drastically reduced:
   - AI_Orchestrator: 92.8% reduction (21,532 → 1,540 avg)
   - This enables 40-60 tasks per session (6x improvement)

5. **Use the right tool for the job**:
   - Quick task? → Direct repo work
   - Many tasks? → Autonomous loop
   - HIPAA-critical? → Autonomous loop (full context + verification)

---

## Real-World Examples

### Morning Workflow: Fix bugs discovered overnight

```bash
# 1. Discover new bugs
cd /Users/tmac/1_REPOS/AI_Orchestrator
aibrain discover-bugs --project karematch

# 2. Review work queue
aibrain status

# 3. Process autonomously (coffee break!)
python autonomous_loop.py --project karematch --max-iterations 100

# Agent processes 25-35 bugs while you're away
# All auto-committed with Ralph PASS verification
```

**Cost**: ~6,266 + (~11,000 × 30 tasks) = **~336,266 tokens** (fits in context window with summarization)

---

### Afternoon Workflow: Add new feature

```bash
# 1. Interactive exploration
cd /Users/tmac/1_REPOS/credentialmate
claude
> "I want to add a feature to export credentials to CSV. What files would I need to change?"

# 2. Get guidance (cost: ~2,000 tokens)

# 3. Decide: Simple (1-3 files) or Complex (5+ files)?

# If simple:
> "Implement the CSV export feature in the Credentials service"
# Cost: ~8,000 tokens total

# If complex:
# Exit interactive, use autonomous loop
cd /Users/tmac/1_REPOS/AI_Orchestrator
aibrain tasks add --project credentialmate --id FEAT-CSV-001 \
  --description "Implement CSV export across all credential types" \
  --type feature --max-iterations 50
python autonomous_loop.py --project credentialmate --max-iterations 50
# Cost: ~31,000 tokens, but ensures quality across all files
```

---

**Remember**: After Phase 2 optimization, startup costs are no longer the bottleneck - you can afford to use autonomous loop more often for higher quality results!
