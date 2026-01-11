# Vault Reference

How to access the Obsidian Knowledge Vault for detailed documentation.

## Vault Location

**Primary**: `/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/`

**Project Folders**:
- `01-AI-Orchestrator/` - This project's documentation
- `02-KareMatch/` - KareMatch documentation
- `03-CredentialMate/` - CredentialMate documentation
- `04-Repo-Analysis/` - 30+ analyzed repositories
- `05-Knowledge-Base/` - Cross-repo learnings

## What's in the Vault?

The vault contains comprehensive documentation that's too detailed for the repo:

| Section | Contents | When to Read |
|---------|----------|--------------|
| **Architecture/** | Detailed system design, component diagrams | Understanding internals |
| **Sessions/** | Historical session handoffs (46 files, 524K) | Learning from past work |
| **Plans/** | Strategic plans, PRDs, roadmaps | Long-term planning |
| **Decisions/** | ADRs with full context and alternatives | Understanding why decisions were made |
| **Governance/** | Complete team contracts, policy details | Policy questions |
| **Operations/** | Deployment guides, runbooks | Day-to-day operations |
| **Knowledge-Objects/** | Links to approved KOs (actual KOs in repo) | Cross-reference only |

## Accessing from Code

```python
from agents.core.context import get_vault_path, detect_context

# Auto-detect vault location based on current repo
context = detect_context()
vault_path = get_vault_path(context)

# Example: Read sessions
import os
sessions_dir = os.path.join(vault_path, "Sessions")
session_files = os.listdir(sessions_dir)

# Example: Read decisions
decisions_file = os.path.join(vault_path, "DECISIONS.md")
with open(decisions_file) as f:
    decisions = f.read()
```

## Agent Protocol

### When to Consult Vault

**FROM CODE REPO** (you're an execution agent):
1. **Historical Context** - Check `Sessions/` for past work on similar problems
2. **Strategic Planning** - Review `Plans/` and `ROADMAP.md` for feature direction
3. **Governance Details** - Read `Governance/` for complete policy context
4. **Cross-Project Learning** - Browse other project folders for patterns

**FROM VAULT** (you're in knowledge management mode):
- ✅ Read files, create notes, organize, link, summarize
- ❌ Execute code, run tests, commit to code repos

### When NOT to Use Vault

- **Runtime Execution** - Don't read vault during normal agent loops (use repo files)
- **Governance Contracts** - Contracts are enforced from `governance/contracts/*.yaml` in repo
- **Knowledge Object Queries** - KOs are loaded from `knowledge/approved/` in repo
- **Current State** - `STATE.md` is in repo, not vault

## Cross-Platform Access

### Mac
1. Open Obsidian
2. Select vault: `Knowledge_Vault`
3. Navigate to: `AI-Engineering/`

### iOS
1. Open Obsidian Mobile
2. Vault should auto-sync via iCloud
3. Navigate to: `AI-Engineering/`

**Sync**: Automatic via iCloud Drive (already configured)

## Vault vs Repo: Quick Reference

| Need | Location | Why |
|------|----------|-----|
| Quick start | `docs/QUICKSTART.md` (repo) | Fast access, no vault needed |
| Agent types | `docs/AGENTS.md` (repo) | Runtime reference |
| System design | `docs/ARCHITECTURE.md` (repo) | High-level overview |
| Deep architecture | `Vault/Architecture/` | Detailed diagrams, alternatives |
| Governance rules | `docs/GOVERNANCE.md` (repo) | Contract summary |
| Complete contracts | `Vault/Governance/` | Full policy details |
| Current state | `STATE.md` (repo) | Always in repo |
| Historical context | `Vault/Sessions/` | Past work patterns |
| Build decisions | `Vault/DECISIONS.md` | Why things were built this way |

## Navigation Tips

**In Obsidian**:
- `Cmd+O` - Quick switcher (search all files)
- `Cmd+P` - Command palette
- `[[link]]` - Wiki-style linking between notes
- Tags: `#bugfix`, `#typescript`, `#architecture`

**File Organization**:
- Each project has its own folder (01-05)
- Each folder has README.md as index
- Use Obsidian graph view to see connections

## For More Details

See vault README: `AI-Engineering/README.md`
