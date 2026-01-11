# Quick Start Guide

Get AI Orchestrator running in 5 minutes.

## Prerequisites

- Python 3.11+
- Git
- Access to target repos (KareMatch or CredentialMate)

## Setup (2 minutes)

### 1. Clone & Install
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Verify Installation
```bash
aibrain --version
python autonomous_loop.py --help
```

## Run Your First Agent (3 minutes)

### Option A: Autonomous Loop (Recommended)
```bash
# Discover and fix bugs on KareMatch
python autonomous_loop.py --project karematch --max-iterations 10

# What happens:
# 1. Scans for bugs (ESLint, TypeScript, Vitest, guardrails)
# 2. Creates work queue
# 3. Assigns tasks to appropriate agents
# 4. Agents fix bugs iteratively
# 5. Ralph verifies each fix (PASS/FAIL/BLOCKED)
# 6. On BLOCKED: Prompts for human decision (Revert/Override/Abort)
# 7. On PASS: Commits and continues
```

### Option B: Manual Bug Discovery
```bash
# Scan for bugs and generate tasks
aibrain discover-bugs --project karematch

# View generated tasks
cat data/bugs_to_fix.json

# Run specific task
python run_agent.py --task-id BUG-001
```

### Option C: Use Deployment Scripts
```bash
# KareMatch
./bin/scripts/autonomous-karematch.sh

# CredentialMate
./bin/scripts/autonomous-credentialmate.sh
```

## Common Commands

### Knowledge Objects
```bash
aibrain ko list                      # List approved KOs
aibrain ko search --tags typescript  # Search by tags
aibrain ko show KO-km-001            # Show details
```

### Bug Discovery
```bash
aibrain discover-bugs --project karematch --dry-run  # Preview
aibrain discover-bugs --project karematch            # Execute
```

### Status & Approval
```bash
aibrain status                       # Overall system status
aibrain status TASK-123              # Specific task
aibrain approve TASK-123             # Approve fix
aibrain reject TASK-123 "reason"     # Reject fix
```

## Emergency Controls

```bash
aibrain emergency-stop    # Stop all agents (AI_BRAIN_MODE=OFF)
aibrain pause             # Pause agents (AI_BRAIN_MODE=PAUSED)
aibrain resume            # Resume agents (AI_BRAIN_MODE=NORMAL)
```

## What Just Happened?

When you run the autonomous loop:

1. **Bug Discovery** scans your target repo for:
   - ESLint errors
   - TypeScript type errors
   - Test failures
   - Guardrail violations (`@ts-ignore`, `.only()`, etc.)

2. **Task Queue** groups bugs by file and priority:
   - P0: Blocks users (test failures, type errors)
   - P1: Degrades UX (lint errors)
   - P2: Tech debt (guardrails)

3. **Agents Execute**:
   - BugFixAgent → Fixes bugs
   - CodeQualityAgent → Cleans up code
   - TestFixer → Fixes broken tests

4. **Ralph Verifies** each change:
   - ✅ PASS → Commit and continue
   - ❌ FAIL → Agent retries (max 15 iterations)
   - 🚫 BLOCKED → Human decision required

5. **Wiggum Controls** iteration:
   - Detects completion signals (`<promise>BUGFIX_COMPLETE</promise>`)
   - Manages retry budgets
   - Prevents infinite loops

## Next Steps

- **Read**: [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system design
- **Read**: [AGENTS.md](AGENTS.md) - Learn about different agent types
- **Read**: [GOVERNANCE.md](GOVERNANCE.md) - Understand autonomy boundaries
- **Explore**: Vault for detailed documentation (see [VAULT-REFERENCE.md](VAULT-REFERENCE.md))

## Troubleshooting

### "Module not found" errors
```bash
# Reinstall in development mode
pip install -e .
```

### "Permission denied" on scripts
```bash
chmod +x bin/scripts/*.sh
```

### Agents not finding vault
```bash
# Check vault path exists
ls "/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/"

# If not, vault may not be synced yet - wait for iCloud sync
```

### Ralph verification failing
```bash
# Check git hooks are installed
ls -la .git/hooks/pre-commit

# If missing, reinstall hooks
governance/install-hooks.sh
```

## Getting Help

- **For Agents**: Read [CLAUDE.md](../CLAUDE.md)
- **For Detailed Docs**: See vault ([VAULT-REFERENCE.md](VAULT-REFERENCE.md))
- **For Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
