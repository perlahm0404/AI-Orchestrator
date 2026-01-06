# AI Orchestrator - Build Decisions Log

**Purpose**: Track decisions made during implementation (not planning decisions - those are in v4-DECISION-v4-recommendations.md)

---

## How to Use This File

When making implementation decisions during the build:

1. Add entry with date, context, decision, rationale
2. Reference this file in future sessions to avoid re-litigating
3. If a decision needs revisiting, mark it as SUPERSEDED with link to new decision

---

## Decisions

### 2026-01-05: Memory Infrastructure Approach

**Context**: Need external artifacts for agent memory before building the repo.

**Decision**: Create three-tier memory system:
1. `STATE.md` - Current build state, what's done/in-progress/blocked
2. `DECISIONS.md` - This file, build-time decisions
3. `sessions/` - Per-session handoff notes for continuity

**Rationale**:
- Matches the "externalized memory" principle from v4 design
- Simple markdown files work with Obsidian
- Can be upgraded to database later without changing pattern

**Status**: ACTIVE

---

### 2026-01-05: Directory Structure Timing

**Context**: Should we create empty directories now or during Phase 0?

**Decision**: Scaffold NOW (user confirmed)

**Rationale**: Provides structure for agents to understand where things go, enables parallel work.

**Status**: ACTIVE

---

### 2026-01-05: Target Repository Locations

**Context**: Need to know where target apps live for Phase -1 calibration and adapter config.

**Decision**: Confirmed locations:
- KareMatch: `/Users/tmac/karematch`
- CredentialMate: `/Users/tmac/credentialmate`

**Status**: ACTIVE

---

---

### 2026-01-05: Autonomous Operation Configuration

**Context**: User requested long autonomous sessions without approval prompts for routine operations.

**Decision**: Created `.claude/settings.json` with permissive allow-list for git, file operations, and Python tools. Restructured `.claude` from file to directory.

**Configuration**:
- Allow: git, npm, pytest, python, pip, file operations (Edit/Write/Read/Glob/Grep)
- Deny: secrets, rm -rf, sudo, curl/wget
- Mode: `acceptEdits` with sandboxing **disabled** (updated after initial setup)

**Rationale**:
- This is a meta-project about autonomous AI - should eat its own dogfood
- Session continuity requires autonomous commits to STATE.md and sessions/
- Security maintained via deny-list and sandboxing

**Status**: ACTIVE

---

## Template for New Decisions

```markdown
### YYYY-MM-DD: Decision Title

**Context**: What situation prompted this decision?

**Decision**: What was decided?

**Alternatives Considered**:
- Option A: ...
- Option B: ...

**Rationale**: Why this choice?

**Status**: ACTIVE | SUPERSEDED by [link] | PENDING
```