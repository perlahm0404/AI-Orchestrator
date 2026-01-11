# Autonomous Mode Scripts

Quick-launch scripts for running the AI Orchestrator in autonomous mode.

## Available Scripts

### CredentialMate (L1 Autonomy - HIPAA Compliant)

```bash
# Make executable (first time only)
chmod +x scripts/autonomous-credentialmate.sh

# Run autonomous mode
./scripts/autonomous-credentialmate.sh

# With bug discovery first
./scripts/autonomous-credentialmate.sh --discover

# Process feature queue
./scripts/autonomous-credentialmate.sh --queue features

# Limit iterations
./scripts/autonomous-credentialmate.sh --max-iterations 50
```

### KareMatch (L2 Autonomy - Higher)

```bash
# Make executable (first time only)
chmod +x scripts/autonomous-karematch.sh

# Run autonomous mode
./scripts/autonomous-karematch.sh

# With bug discovery first
./scripts/autonomous-karematch.sh --discover

# Process feature queue
./scripts/autonomous-karematch.sh --queue features

# Limit iterations
./scripts/autonomous-karematch.sh --max-iterations 50
```

## What Happens

When you run these scripts, the autonomous loop will:

1. ✅ **Load work queue** from `tasks/work_queue_{project}.json`
2. ✅ **Process each task** with 15-50 retry iterations
3. ✅ **Auto-fix** lint, type, and test errors
4. ✅ **Auto-commit** when Ralph verification passes
5. ⚠️  **Only interrupt** for:
   - Guardrail violations (R/O/A prompt)
   - Iteration budget exhausted
   - Strategic domain changes (for CredentialMate: HIPAA, auth, schema)

## Session Resume

If interrupted (Ctrl+C or crash), simply run the same command again - it automatically resumes from the last state file (`.aibrain/agent-loop.local.md`).

## Alternative: Direct Python Invocation

If you prefer to call Python directly:

```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# CredentialMate
python3 autonomous_loop.py --project credentialmate --max-iterations 100

# KareMatch
python3 autonomous_loop.py --project karematch --max-iterations 100

# With options
python3 autonomous_loop.py \
    --project credentialmate \
    --max-iterations 50 \
    --queue features
```

## Autonomy Levels

| Project | Level | Constraints | Human Interaction |
|---------|-------|-------------|-------------------|
| **CredentialMate** | L1 (stricter) | HIPAA compliance, no schema changes without approval | Strategic decisions, guardrails |
| **KareMatch** | L2 (higher) | Stable codebase, fewer restrictions | Guardrails only |

## Work Queue Management

```bash
# Discover bugs and populate work queue
python3 -m cli.main discover-bugs --project credentialmate
python3 -m cli.main discover-bugs --project karematch

# Check queue status
python3 -m cli.main status

# View specific task
python3 -m cli.main status TASK-123
```

## Related Documentation

- [autonomous_loop.py](../autonomous_loop.py) - Main loop implementation
- [governance/contracts/](../governance/contracts/) - Autonomy contracts
- [CLAUDE.md](../CLAUDE.md) - Full system documentation
