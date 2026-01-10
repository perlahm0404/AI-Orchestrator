# Quick Start: Autonomous Mode

Get the AI Orchestrator running autonomously in under 2 minutes.

## 🚀 Fastest Path to Autonomy

### Option 1: Shell Scripts (Recommended)

```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# Make scripts executable (first time only)
chmod +x scripts/*.sh

# Run for CredentialMate
./scripts/autonomous-credentialmate.sh --discover

# OR run for KareMatch
./scripts/autonomous-karematch.sh --discover
```

### Option 2: Direct Python

```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# Discover bugs
python3 -m cli.main discover-bugs --project credentialmate

# Run autonomous loop
python3 autonomous_loop.py --project credentialmate --max-iterations 100
```

### Option 3: Claude Code Skills (Future)

Skills have been created in `.claude/skills/` for potential integration:
- `/autonomous-credentialmate`
- `/autonomous-karematch`

(These may require skill registration - see `.claude/skills/*.skill.md` for details)

## What You'll See

```
🤖 AI Orchestrator - Autonomous CredentialMate Mode
==================================================

🔍 Discovering bugs in CredentialMate...
📋 Task Summary:
  🆕 [P0] TEST-LOGIN-001: Fix 2 test error(s) (NEW REGRESSION)
  🆕 [P0] TYPE-SESSION-002: Fix 1 typecheck error(s) (NEW REGRESSION)
     [P1] LINT-MATCHING-003: Fix 3 lint error(s) (baseline)

🚀 Starting autonomous loop...
   Project: credentialmate
   Max iterations: 100
   Queue type: bugs

────────────────────────────────────────────────────────────────────────────
Iteration 1/100
────────────────────────────────────────────────────────────────────────────

📌 Current Task: TEST-LOGIN-001
   Description: Fix 2 test error(s) in tests/auth/login.test.ts
   File: tests/auth/login.test.ts
   Attempts: 0

🤖 Agent type: TestFixer

[Agent begins work...]
```

## When You'll Be Interrupted

**ONLY for**:
- 🚫 Guardrail violations (e.g., `--no-verify` detected)
- ⏱️ Iteration budget exhausted (tried 15-50 times, still failing)
- 🔐 Strategic decisions (CredentialMate only: HIPAA, auth, schema)

**NEVER for**:
- ✅ Lint errors (auto-fixed)
- ✅ Type errors (auto-fixed)
- ✅ Test failures (auto-fixed with retries)

## Session Resume

Interrupted by Ctrl+C? Just run the same command again:

```bash
./scripts/autonomous-credentialmate.sh
# Automatically resumes from .aibrain/agent-loop.local.md
```

## Quick Commands

```bash
# Check status
python3 -m cli.main status

# View specific task
python3 -m cli.main status TASK-123

# Approve completed fix
python3 -m cli.main approve TASK-123

# Emergency stop
python3 -m cli.main emergency-stop
```

## What Gets Fixed Automatically

| Issue Type | Auto-Fixed | Retries |
|------------|-----------|---------|
| ESLint errors | ✅ Yes | 15-20 |
| TypeScript errors | ✅ Yes | 15-20 |
| Test failures | ✅ Yes | 15 |
| Guardrail violations | ❌ No | Requires human |
| Schema changes | ❌ No (L1 only) | Requires approval |

## Current Autonomy Level

- **CredentialMate**: L1 (89% autonomous, HIPAA-compliant)
- **KareMatch**: L2 (89% autonomous, higher freedom)

## Next Steps

After your first autonomous run:

1. Review completed tasks: `python3 -m cli.main status`
2. Approve fixes: `python3 -m cli.main approve TASK-123`
3. Check git commits: `cd /Users/tmac/1_REPOS/credentialmate && git log`
4. Merge fixes to main (after review)

## Troubleshooting

### "No tasks in queue"
```bash
python3 -m cli.main discover-bugs --project credentialmate
```

### "Iteration budget exhausted"
The agent tried 15-50 times and couldn't fix it. Manual intervention needed.

### "Guardrail violation"
You'll see an R/O/A prompt. Choose:
- **R** = Revert changes and exit
- **O** = Override guardrail (not recommended)
- **A** = Abort session

## Full Documentation

- [CLAUDE.md](./CLAUDE.md) - Complete system documentation
- [STATE.md](./STATE.md) - Current implementation status
- [scripts/README.md](./scripts/README.md) - Script documentation
- [knowledge/README.md](./knowledge/README.md) - Knowledge Object system
