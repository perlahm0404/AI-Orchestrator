# Repository Registry

**Last Updated**: 2026-01-10
**Purpose**: Metadata and quick reference for all managed repositories

---

## Overview

| Repo | Purpose | Autonomy | Status |
|------|---------|----------|--------|
| [AI_Orchestrator](#ai_orchestrator) | Autonomous multi-agent orchestration system | N/A (control plane) | ✅ Production Ready (v5.2) |
| [CredentialMate](#credentialmate) | HIPAA-compliant healthcare credential management | L1 (strict) | 🔄 Active Development |
| [KareMatch](#karematch) | Therapy/client matching platform | L2 (higher) | 🚀 Pre-Production |

---

## AI_Orchestrator

**Location**: `/Users/tmac/1_REPOS/AI_Orchestrator`

### Purpose

Autonomous multi-agent system for governed code quality improvement AND feature development. Deploys two specialized teams:
- **QA Team**: Maintain code quality on stable code (L2 autonomy)
- **Dev Team**: Build new features in isolation (L1 autonomy)

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.11+ |
| **Orchestration** | Custom agent loop with Wiggum iteration control |
| **Verification** | Ralph guardrail system |
| **Knowledge** | Knowledge Objects (KO) with in-memory caching |
| **CLI** | Click-based `aibrain` command |
| **Testing** | pytest |

### Key Metrics

- **Version**: v5.2
- **Autonomy**: 89% (up from 60%)
- **Tasks/Session**: 30-50 (up from 10-15)
- **KO Query Speed**: 457x faster (caching)
- **Retry Budget**: 15-50 per task

### Branch Strategy

| Branch | Purpose | Ralph Timing |
|--------|---------|--------------|
| `main` | Protected, stable | Always |
| `fix/*` | QA Team changes | Every commit |
| `feature/*` | Dev Team changes | PR only |

### Documentation

- [CLAUDE.md](../CLAUDE.md) - Project instructions
- [STATE.md](../STATE.md) - Current implementation status
- [DECISIONS.md](../DECISIONS.md) - Build decisions
- [knowledge/README.md](../knowledge/README.md) - KO system guide

### Quick Links

- [Session Handoffs](../sessions/)
- [ADR Index](../AI-Team-Plans/ADR-INDEX.md)
- [Work Queues](../tasks/)
- [Adapters](../adapters/) - Project-specific configs

---

## CredentialMate

**Location**: `/Users/tmac/1_REPOS/credentialmate`

### Purpose

HIPAA-compliant healthcare credential management platform for medical providers. Tracks licenses, certifications, CME credits, and compliance requirements.

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.11+) |
| **Frontend** | Next.js 14 (TypeScript) |
| **Database** | PostgreSQL 15+ |
| **ORM** | SQLAlchemy 2.0 |
| **Auth** | Supabase Auth |
| **Task Queue** | Celery + Redis |
| **Storage** | S3 (time-limited signed URLs) |

### Autonomy Level

**L1 (Strict)** - HIPAA compliance requirements:
- Max 50 lines added per change
- Max 5 files changed
- No schema changes without approval
- Full audit logging required
- No PHI exposure

### Key Features

- Provider Dashboard (at-risk/urgent credentials)
- CME Credit Tracking (state-specific rules)
- Report Generation (PDF, CSV, Excel)
- Partner File Bulk Download
- Multi-coordinator management

### Branch Strategy

| Branch | Purpose | Status |
|--------|---------|--------|
| `main` | Production | Protected |
| `staging` | Pre-prod testing | Active |
| `feature/*` | New features | Dev Team |

### Documentation

Located in `docs/`:
- `15-kb/` - Knowledge base articles
- `06-ris/` - RIS (Rapid Incident Summary) sessions
- `sessions/` - Working session handoffs
- `testing/` - E2E test plans

### Recent Work

- ✅ ADR-001: Provider Report Generation (async, HIPAA-compliant)
- 🔄 ADR-002: CME Topic Hierarchy (cross-state aggregation)
- 📋 ADR-005: Business Logic Consolidation (backend as SSOT)

---

## KareMatch

**Location**: `/Users/tmac/1_REPOS/karematch`

### Purpose

Therapy/client matching platform connecting mental health providers with clients. Focuses on secure scheduling, availability management, and profile matching.

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Monorepo** | Turborepo |
| **Backend** | Node.js + TypeScript |
| **Frontend** | Next.js 14 (TypeScript) |
| **Database** | PostgreSQL (Drizzle ORM) |
| **Testing** | Vitest (unit), Playwright (E2E) |
| **Auth** | Custom (session-based) |

### Autonomy Level

**L2 (Higher)** - Less strict than CredentialMate:
- Max 100 lines added per change
- Max 10 files changed
- Faster iteration cycles
- Fewer regulatory constraints

### Key Features

- Therapist/Client Profiles
- Availability Calendar & Scheduling
- Proximity-based Search
- Wizard-based Onboarding Flow
- Responsive UI (mobile-first)

### Branch Strategy

| Branch | Purpose | Status |
|--------|---------|--------|
| `main` | Production | Protected |
| `fix/*` | QA Team fixes | Active |
| `feature/*` | Dev Team features | Active |

### Documentation

Located in `docs/`:
- `sessions/` - Working sessions (20+ archived)
- `archive/plans/superseded/` - Historical plans
- `.claude/plans/` - Active implementation plans

### Recent Work

- ✅ Unified Availability Calendar
- ✅ Wizard Flow Test Results
- 🔄 Feature Status Scan
- 🔄 Amado Phase 1 Proximity Fix

---

## Repository Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    AI_Orchestrator                          │
│  (Control Plane - Governance, Agents, Knowledge)            │
│                                                              │
│  ┌──────────────────────┐     ┌──────────────────────┐     │
│  │   QA Team (L2)       │     │   Dev Team (L1)      │     │
│  │   - BugFix           │     │   - FeatureBuilder   │     │
│  │   - CodeQuality      │     │   - TestWriter       │     │
│  │   - TestFixer        │     │                      │     │
│  └──────────┬───────────┘     └──────────┬───────────┘     │
│             │                            │                  │
│             ▼                            ▼                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Ralph Verification Engine                 │   │
│  │           (PASS/FAIL/BLOCKED verdicts)              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                       │                │
         ┌─────────────┴────────┬───────┴─────────────┐
         ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────┐  ┌──────────────────┐
│  CredentialMate  │   │   KareMatch      │  │  (Future Apps)   │
│   (L1/HIPAA)     │   │   (L2/Higher)    │  │                  │
└──────────────────┘   └──────────────────┘  └──────────────────┘
```

---

## Development Workflow

### 1. AI_Orchestrator → Target App

```bash
# From AI_Orchestrator repo
cd /Users/tmac/1_REPOS/AI_Orchestrator

# Run autonomous loop on target project
python autonomous_loop.py --project credentialmate --max-iterations 100
python autonomous_loop.py --project karematch --max-iterations 100
```

### 2. Local Development (Target App)

```bash
# CredentialMate
cd /Users/tmac/1_REPOS/credentialmate
# (local development, manual testing)

# KareMatch
cd /Users/tmac/1_REPOS/karematch
# (local development, manual testing)
```

### 3. Knowledge Sync

Knowledge Objects and configuration sync from AI_Orchestrator to target apps via:
- Symlinks (planned)
- Copy on deploy (current)

---

## Directory Conventions

All repos follow similar patterns:

| Directory | Purpose |
|-----------|---------|
| `docs/` | User-facing documentation |
| `sessions/` | Session handoffs |
| `.claude/` | Claude Code config, skills, plans |
| `tests/` | Test suites |
| `AI-Team-Plans/` | ADRs, decisions, templates |

---

## Git Conventions

### Commit Message Format

```
<type>: <summary>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

### Branch Naming

| Pattern | Purpose |
|---------|---------|
| `fix/description` | QA Team fixes |
| `feature/description` | Dev Team features |
| `hotfix/description` | Emergency production fixes |

---

## Quick Navigation

**Jump to repo**:
```bash
# Bash aliases (add to ~/.zshrc or ~/.bashrc)
alias aio="cd /Users/tmac/1_REPOS/AI_Orchestrator"
alias cm="cd /Users/tmac/1_REPOS/credentialmate"
alias km="cd /Users/tmac/1_REPOS/karematch"
```

**Search across all repos**:
```bash
# From AI_Orchestrator
grep -r "keyword" . ../credentialmate ../karematch
```

---

## Related Resources

- [CATALOG.md](../CATALOG.md) - Master documentation index
- [STATE.md](../STATE.md) - Current implementation status
- [CLAUDE.md](../CLAUDE.md) - Project instructions
