# AI Orchestrator

**Autonomous multi-agent system for governed code quality improvement, feature development, and safe deployments.**

[![Version](https://img.shields.io/badge/version-5.2-blue.svg)](CLAUDE.md)
[![Autonomy](https://img.shields.io/badge/autonomy-89%25-green.svg)](CLAUDE.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)

## What Is This?

AI Orchestrator deploys **three specialized teams** of AI agents, plus **advisor agents** and **meta-coordinators**, to autonomously improve code quality and ship features while maintaining strict governance.

### Execution Teams
- **QA Team** (L2 autonomy) - BugFix, CodeQuality, TestFixer
- **Dev Team** (L1 autonomy) - FeatureBuilder, TestWriter
- **Operator Team** (L0.5 autonomy) - Deployment, Migration, Rollback

### Advisory & Governance
- **Advisors** - App, UI/UX, Data (domain expertise)
- **Coordinator** - ADR → Task orchestration
- **Meta-Coordinators** - PM, CMO (evidence-based oversight)

### Core Systems
- **Ralph** - Verification engine (PASS/FAIL/BLOCKED)
- **Wiggum** - Iteration control & self-correction
- **Knowledge Objects** - Persistent learning system

## Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Run Autonomous Loop
```bash
# Start autonomous bug fixes on KareMatch
python autonomous_loop.py --project karematch --max-iterations 50

# Or use deployment scripts
./bin/scripts/autonomous-karematch.sh
./bin/scripts/autonomous-credentialmate.sh
```

### 3. Use CLI Commands
```bash
# Knowledge Objects
aibrain ko list                    # List approved KOs
aibrain ko search --tags typescript

# Bug Discovery
aibrain discover-bugs --project karematch

# ADR & Evidence Management
aibrain adr list
aibrain evidence list
```

## Target Applications

| App | Autonomy | Stack | Path |
|-----|----------|-------|------|
| **KareMatch** | L2 (higher) | React + Node + PostgreSQL | `/Users/tmac/1_REPOS/karematch` |
| **CredentialMate** | L1 (HIPAA) | FastAPI + Next.js + PostgreSQL | `/Users/tmac/1_REPOS/credentialmate` |

## Documentation

### Essential Reference (In This Repo)
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get running in 5 minutes
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - High-level system design
- **[AGENTS.md](docs/AGENTS.md)** - Agent types & usage guide
- **[GOVERNANCE.md](docs/GOVERNANCE.md)** - Autonomy contracts summary
- **[VAULT-REFERENCE.md](docs/VAULT-REFERENCE.md)** - Accessing detailed docs

### For AI Agents
- **[CLAUDE.md](CLAUDE.md)** - Complete agent operating instructions
- **[STATE.md](STATE.md)** - Current implementation status
- **[USER-PREFERENCES.md](USER-PREFERENCES.md)** - Working preferences

### Detailed Documentation (Obsidian Vault)
- **Architecture** - Detailed system design, ADRs, strategic plans
- **Sessions** - Historical session handoffs (46+ sessions)
- **Knowledge Objects** - Approved learnings & best practices
- **Plans** - Strategic roadmap, feature plans

**Vault Path**: `/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/`

## Repository Structure

```
AI_Orchestrator/
├── agents/          # Agent implementations (bugfix, codequality, etc.)
├── ralph/           # Verification engine (PASS/FAIL/BLOCKED)
├── orchestration/   # Session lifecycle, iteration control
├── discovery/       # Bug discovery system
├── cli/             # CLI commands (aibrain)
├── governance/      # Contracts, hooks, guardrails
├── knowledge/       # Knowledge Objects (runtime)
├── adapters/        # Project-specific configs
├── tasks/           # Work queue management
├── tests/           # Test suite
├── docs/            # Essential reference docs (NEW)
├── bin/             # Utility scripts
├── data/            # Configuration & state
└── .meta/           # Generated outputs (logs, reports)
```

## Key Metrics

- **Autonomy**: 89% (up from 60%)
- **Tasks per session**: 30-50 (up from 10-15)
- **KO query speed**: 457x faster (caching)
- **Repo size**: 205M (optimized for fast agent init)

## Core Principles

1. **Evidence-based completion** - No task marked done without proof
2. **Human-in-the-loop approval** - Agents execute, humans approve
3. **Institutional memory** - Knowledge Objects survive sessions
4. **Explicit governance** - Autonomy contracts define boundaries
5. **Team isolation** - QA and Dev work on separate branches

## Status

**Version**: v5.2 - Production Ready

**Implemented Systems**:
- ✅ v5.1 - Wiggum iteration control + autonomous loop
- ✅ v5.2 - Automated bug discovery with turborepo support
- ✅ v5.3 - Knowledge Object enhancements (cache, metrics)

## Contributing

This is a personal project. For questions or issues, see the governance documentation.

## License

Private - All Rights Reserved
