# AI Brain V4 - Complete Implementation Plan

**Date**: 2026-01-05
**Version**: 4.0
**Phase**: Pre-Phase Complete → Ready for Phase -1 (Trust Calibration)
**Based On**: V3 Plan + Expert Review + Schema/Observability Analysis

---

## What's New in V4

This version incorporates expert recommendations from comprehensive analysis of 30+ repos and evaluation of ChatGPT's schema/observability suggestions.

### Key Additions

| Addition | Phase | Rationale |
|----------|-------|-----------|
| **Phase -1: Trust Calibration Sprint** | Before Phase 0 | Prove the system works before building more |
| **Autonomy Contracts (YAML)** | Phase 0 | Machine-readable, enforceable policy |
| **Negative Capability Tests** | Phase 0 | Prove safety systems actually work |
| **Kill-Switch / Safe Mode** | Phase 0 | Production necessity for incidents |
| **Enhanced Audit Schema** | Phase 0 | Causality tracking without over-engineering |
| **Human Review UX (REVIEW.md)** | Phase 1 | Make human-in-the-loop sustainable |
| **No-New-Features Guardrail** | Phase 1 | Prevent bug-fix drift |
| **Knowledge Objects** | Phase 1 | Durable semantic memory from resolutions |

### What We Explicitly Rejected

| Rejected | Rationale |
|----------|-----------|
| Full OpenTelemetry trace/span/event schema | Over-engineering for Phase 1 scale |
| Temporal workflow infrastructure | Heavyweight for 2 target apps |
| Cross-language abstraction layer | Accept duplication, maintain simplicity |
| Evidence schema versioning | Defer to Phase 3 when needed |
| Drift detection between repos | Defer to Phase 4 (multi-project) |

---

## Executive Summary

**Status**: All repos analyzed. V4 incorporates validated best practices.

**Core Strategy**: BugFix-first approach with Ralph Wiggum governance, proven on real production apps.

**Target Apps**:
- **CredentialMate** (App A): Production app with users, FastAPI + Next.js + PostgreSQL, HIPAA compliance
- **KareMatch** (App B): Production-ready app, Node/TS monorepo with Vitest/Playwright, extensive automation

**Key Discovery**: Both apps already have Ralph Wiggum + mature governance → we can bootstrap from existing patterns.

**Timeline**:
- Phase -1: 1 week (Trust Calibration)
- Phase 0: 2 weeks (Governance Foundation)
- Phase 1: 4-6 weeks (BugFix + CodeQuality agents working on real bugs)

---

## Table of Contents

1. [Phase -1: Trust Calibration Sprint](#phase--1-trust-calibration-sprint) **[NEW]**
2. [Autonomy Contracts](#autonomy-contracts) **[NEW]**
3. [Kill-Switch & Safe Mode](#kill-switch--safe-mode) **[NEW]**
4. [Enhanced Audit Schema](#enhanced-audit-schema) **[NEW]**
5. [Human Review UX](#human-review-ux) **[NEW]**
6. [Negative Capability Tests](#negative-capability-tests) **[NEW]**
7. [No-New-Features Guardrail](#no-new-features-guardrail) **[NEW]**
8. [Knowledge Objects](#knowledge-objects) **[NEW]**
9. [Ralph Wiggum Verification System](#ralph-wiggum-verification-system)
10. [AMADO Orchestrator Patterns](#amado-orchestrator-patterns)
10. [Target Application Analysis](#target-application-analysis)
11. [Complete Architecture](#complete-architecture)
12. [Database Schema (Enhanced)](#database-schema-enhanced)
13. [Implementation Phases](#implementation-phases)
14. [Success Metrics](#success-metrics)

---

## Phase -1: Trust Calibration Sprint

**NEW IN V4**

**Duration**: 1 week (before Phase 0)

**Goal**: Validate assumptions before committing to full build. Prove the core loop works.

### Calibration Tasks

#### Task 1: Fix 3 Trivial Bugs (Happy Path)

**Purpose**: Prove the basic workflow works end-to-end.

**Selection Criteria**:
- Single-file changes only
- Clear reproduction steps
- Obvious fix (typo, missing null check, etc.)
- Low blast radius

**Process**:
1. Manually select 3 trivial bugs from KareMatch `TODO-stub-tests.md`
2. Run BugFix workflow manually (no AI yet):
   - Write reproduction test → verify fails
   - Apply fix → verify test passes
   - Run Ralph → verify all green
   - Capture evidence manually
3. Document friction points and gaps

**Success**: 3 bugs fixed with full evidence trail.

#### Task 2: Fix 1 Medium Bug (Complexity Test)

**Purpose**: Prove the workflow handles realistic complexity.

**Selection Criteria**:
- 2-3 file changes
- Requires root cause analysis
- Non-obvious fix

**Process**:
1. Select 1 medium bug from KareMatch
2. Run full workflow with human-in-the-loop
3. Measure time, decisions, evidence quality

**Success**: 1 medium bug fixed with complete audit trail.

#### Task 3: Attempt 2 Forbidden Actions (Safety Test)

**Purpose**: Prove guardrails actually work.

**Tests**:
```bash
# Test 1: Ralph guardrails block skipped test
echo "test.skip('broken test', () => {})" >> tests/example.test.ts
bash tools/ralph/verify.sh
# Expected: BLOCKED by guardrail.sh

# Test 2: Bash security hook blocks dangerous command
# (Simulated - don't actually run)
bash_security_hook({"command": "rm -rf /"})
# Expected: decision=block
```

**Success**: Both forbidden actions blocked with clear error messages.

#### Task 4: Measure Evidence Quality

**Purpose**: Validate evidence is sufficient for human review.

**Process**:
1. Review evidence from Tasks 1-2
2. Answer: "Can a human reviewer understand what happened?"
3. Score each evidence package (1-5)

**Success**: Average evidence score >= 4.

#### Task 5: Tune Thresholds

**Purpose**: Calibrate governance rules based on real data.

**Tuning Targets**:
- Max lines added (currently 100) - adjust if too restrictive
- Max files changed (currently 5) - adjust if too restrictive
- Circuit breaker threshold (currently 3) - adjust based on failure patterns

**Success**: Documented threshold decisions with rationale.

### Phase -1 Exit Criteria

- [ ] 3 trivial bugs fixed with full evidence
- [ ] 1 medium bug fixed with complete audit trail
- [ ] 2 forbidden actions blocked by guardrails
- [ ] Average evidence quality score >= 4
- [ ] Threshold decisions documented
- [ ] Go/No-Go decision for Phase 0

---

## Autonomy Contracts

**NEW IN V4**

Machine-readable policy files that turn governance intent into enforceable rules.

### Contract Structure

```yaml
# contracts/bugfix.yaml
agent: bugfix
version: "1.0"

allowed_actions:
  - read_file
  - write_file
  - run_tests
  - run_ralph
  - create_branch
  - commit_changes

forbidden_actions:
  - modify_migrations
  - modify_ci_config
  - deploy
  - delete_tests
  - modify_coverage_config

approval_required:
  - database_schema_change
  - security_config_change
  - api_contract_change

constraints:
  max_iterations: 3
  max_lines_added: 100
  max_files_changed: 5
  require_reproduction_test: true
  require_passing_tests: true

escalation:
  on_constraint_violation: human
  on_forbidden_action: block_and_alert
  on_max_iterations: human
```

```yaml
# contracts/codequality.yaml
agent: codequality
version: "1.0"

allowed_actions:
  - read_file
  - write_file
  - run_lint
  - run_typecheck
  - run_tests
  - run_ralph

forbidden_actions:
  - delete_tests
  - modify_test_assertions
  - add_new_functionality
  - modify_api_contracts

constraints:
  max_batch_size: 20
  test_count_must_match: true
  no_new_lint_errors: true
  require_baseline: true

escalation:
  on_test_count_change: block
  on_test_failure: rollback
```

```yaml
# contracts/refactor.yaml
agent: refactor
version: "1.0"

allowed_actions:
  - read_file
  - write_file
  - rename_symbol
  - move_code
  - extract_function

forbidden_actions:
  - add_new_functionality
  - modify_behavior
  - delete_tests

constraints:
  behavior_must_preserve: true
  all_tests_must_pass: true
  max_files_changed: 20

escalation:
  on_test_failure: rollback_and_alert
```

### Contract Enforcement

```python
# contracts/enforcer.py
from pathlib import Path
import yaml

class ContractEnforcer:
    def __init__(self, agent_type: str):
        contract_path = Path(f"contracts/{agent_type}.yaml")
        self.contract = yaml.safe_load(contract_path.read_text())

    def check_action(self, action: str) -> tuple[bool, str]:
        if action in self.contract["forbidden_actions"]:
            return False, f"Action '{action}' is forbidden for {self.contract['agent']}"

        if action in self.contract.get("approval_required", []):
            return False, f"Action '{action}' requires human approval"

        if action not in self.contract["allowed_actions"]:
            return False, f"Action '{action}' is not in allowed list"

        return True, ""

    def check_constraints(self, metrics: dict) -> list[str]:
        violations = []
        constraints = self.contract["constraints"]

        if metrics.get("lines_added", 0) > constraints.get("max_lines_added", float("inf")):
            violations.append(f"Lines added ({metrics['lines_added']}) exceeds max ({constraints['max_lines_added']})")

        if metrics.get("files_changed", 0) > constraints.get("max_files_changed", float("inf")):
            violations.append(f"Files changed ({metrics['files_changed']}) exceeds max ({constraints['max_files_changed']})")

        if constraints.get("test_count_must_match") and metrics.get("test_count_before") != metrics.get("test_count_after"):
            violations.append(f"Test count changed: {metrics['test_count_before']} -> {metrics['test_count_after']}")

        return violations
```

---

## Kill-Switch & Safe Mode

**NEW IN V4**

Global controls for production incidents, audits, and "something feels wrong" moments.

### Operating Modes

```bash
# Environment variable controls
AI_BRAIN_MODE=OFF       # Observability only, no actions
AI_BRAIN_MODE=SAFE      # Read-only, tests allowed, no code writes
AI_BRAIN_MODE=NORMAL    # Full operation (default)
AI_BRAIN_MODE=PAUSED    # Pause current work, maintain state
```

### Mode Behaviors

| Mode | Read Files | Run Tests | Write Files | Create PRs | Deploy |
|------|------------|-----------|-------------|------------|--------|
| OFF | No | No | No | No | No |
| SAFE | Yes | Yes | No | No | No |
| NORMAL | Yes | Yes | Yes | Yes | No* |
| PAUSED | Yes | No | No | No | No |

*Deploy never allowed at any autonomy level without explicit human action.

### Implementation

```python
# core/mode.py
import os
from enum import Enum

class OperatingMode(Enum):
    OFF = "OFF"
    SAFE = "SAFE"
    NORMAL = "NORMAL"
    PAUSED = "PAUSED"

def get_mode() -> OperatingMode:
    mode_str = os.environ.get("AI_BRAIN_MODE", "NORMAL")
    return OperatingMode(mode_str)

def require_mode(allowed_modes: list[OperatingMode]):
    """Decorator to restrict actions by mode"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            current = get_mode()
            if current not in allowed_modes:
                raise ModeRestrictionError(
                    f"Action '{func.__name__}' not allowed in {current.value} mode. "
                    f"Allowed modes: {[m.value for m in allowed_modes]}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@require_mode([OperatingMode.NORMAL])
def write_file(path: str, content: str):
    ...

@require_mode([OperatingMode.NORMAL, OperatingMode.SAFE])
def run_tests(project_path: str):
    ...
```

### Emergency Stop

```bash
# Immediate stop - kills all running agents
aibrain emergency-stop

# Graceful pause - completes current action, then stops
aibrain pause

# Resume from pause
aibrain resume

# Check status
aibrain status
```

---

## Enhanced Audit Schema

**NEW IN V4**

Extends the existing `audit_log` table with causality tracking, without the complexity of full OpenTelemetry.

### Schema Changes

```sql
-- Enhanced audit_log (extends V3 schema)
ALTER TABLE audit_log ADD COLUMN parent_event_id INTEGER REFERENCES audit_log(id);
ALTER TABLE audit_log ADD COLUMN caused_by_event_id INTEGER REFERENCES audit_log(id);
ALTER TABLE audit_log ADD COLUMN decision_rationale TEXT;
ALTER TABLE audit_log ADD COLUMN risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical'));
ALTER TABLE audit_log ADD COLUMN session_id UUID;
ALTER TABLE audit_log ADD COLUMN agent_type VARCHAR(50);
ALTER TABLE audit_log ADD COLUMN duration_ms INTEGER;

-- Index for causality queries
CREATE INDEX idx_audit_log_parent ON audit_log(parent_event_id);
CREATE INDEX idx_audit_log_session ON audit_log(session_id);
CREATE INDEX idx_audit_log_task ON audit_log(task_id);

-- Full enhanced schema
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Context
    project_id INTEGER REFERENCES projects(id),
    task_id INTEGER REFERENCES tasks(id),
    session_id UUID,
    agent_type VARCHAR(50),

    -- Action details
    action TEXT NOT NULL,                    -- blocked|allowed|warned|completed|failed
    action_type VARCHAR(50),                 -- read_file|write_file|run_tests|etc.
    rule_id TEXT,
    details JSONB,

    -- Causality (NEW)
    parent_event_id INTEGER REFERENCES audit_log(id),
    caused_by_event_id INTEGER REFERENCES audit_log(id),

    -- Decision tracking (NEW)
    decision_rationale TEXT,
    risk_level VARCHAR(20),

    -- Blocking details
    blocked_command TEXT,
    block_reason TEXT,

    -- Performance (NEW)
    duration_ms INTEGER
);
```

### Causality Queries

```sql
-- Find all events in a session
SELECT * FROM audit_log
WHERE session_id = 'abc-123'
ORDER BY timestamp;

-- Find root cause chain for a blocked action
WITH RECURSIVE cause_chain AS (
    SELECT id, action, caused_by_event_id, decision_rationale, 1 as depth
    FROM audit_log
    WHERE id = 456  -- The blocked event

    UNION ALL

    SELECT al.id, al.action, al.caused_by_event_id, al.decision_rationale, cc.depth + 1
    FROM audit_log al
    JOIN cause_chain cc ON al.id = cc.caused_by_event_id
)
SELECT * FROM cause_chain ORDER BY depth;

-- Find all high-risk actions for a task
SELECT * FROM audit_log
WHERE task_id = 123
AND risk_level IN ('high', 'critical')
ORDER BY timestamp;
```

### Usage

```python
def log_action(
    action: str,
    action_type: str,
    task_id: int | None = None,
    parent_event_id: int | None = None,
    caused_by_event_id: int | None = None,
    decision_rationale: str | None = None,
    risk_level: str = "low",
    details: dict | None = None
) -> int:
    """Log an action with causality tracking"""
    event = {
        "action": action,
        "action_type": action_type,
        "task_id": task_id,
        "session_id": get_current_session_id(),
        "agent_type": get_current_agent_type(),
        "parent_event_id": parent_event_id,
        "caused_by_event_id": caused_by_event_id,
        "decision_rationale": decision_rationale,
        "risk_level": risk_level,
        "details": details,
        "timestamp": datetime.utcnow()
    }
    return db.insert("audit_log", event)
```

---

## Human Review UX

**NEW IN V4**

Standardized review packets make human-in-the-loop sustainable.

### REVIEW.md Template

Every fix generates a `REVIEW.md` in the PR or task directory:

```markdown
# Fix Review: [TASK-ID] [Title]

**Agent**: BugFix v1.0
**Generated**: 2026-01-05 14:32:00 UTC
**Review Time Estimate**: 5 minutes

---

## Summary

[One paragraph describing what was fixed and why]

Example:
> Fixed null pointer exception in `AuthService.validateToken()` that occurred
> when users had expired refresh tokens. The root cause was missing null check
> before accessing `token.claims`. Added defensive null check and early return.

---

## Root Cause

**Error**: `TypeError: Cannot read property 'claims' of null`
**Location**: `src/services/auth.ts:142`
**Trigger**: User with expired refresh token attempts re-authentication

**Analysis**:
The `refreshToken` parameter can be null when the token has expired and been
purged from the session store. The code assumed it would always be present.

---

## Changes Made

| File | Lines Changed | Type |
|------|---------------|------|
| `src/services/auth.ts` | +5, -1 | Fix |
| `tests/auth.test.ts` | +12 | Test |

**Total**: 17 lines added, 1 line removed, 2 files changed

### Key Changes

```typescript
// src/services/auth.ts:142
// Before:
const claims = token.claims;

// After:
if (!token) {
  return { valid: false, reason: 'token_missing' };
}
const claims = token.claims;
```

---

## Evidence

### Reproduction Test
- **Path**: `tests/auth.test.ts:89`
- **Before fix**: FAILED
- **After fix**: PASSED

### Full Test Suite
- **Tests run**: 142
- **Passed**: 142
- **Failed**: 0
- **Coverage**: 84.2%

### Ralph Verification
- **Run ID**: `20260105-143200-abc123`
- **Guardrails**: PASSED
- **Lint**: PASSED
- **Type Check**: PASSED
- **Tests**: PASSED
- **Coverage**: PASSED (84.2% >= 80%)

[View full Ralph log](./ralph/state/runs/20260105-143200-abc123/SUMMARY.txt)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Early return changes control flow | Low | Low | Covered by existing tests |
| Missing edge cases | Low | Medium | Added 3 new test cases |

---

## Rollback Plan

```bash
# If issues discovered after merge:
git revert abc123def  # The fix commit
npm test              # Verify rollback didn't break anything
```

---

## Reviewer Checklist

- [ ] Root cause analysis makes sense
- [ ] Fix is minimal and targeted
- [ ] Tests cover the fix
- [ ] No unintended side effects
- [ ] Ralph verification passed
- [ ] Ready to merge

---

**Approve**: `aibrain approve TASK-123`
**Request Changes**: `aibrain request-changes TASK-123 "reason"`
**Reject**: `aibrain reject TASK-123 "reason"`
```

### Auto-Generation

```python
def generate_review_md(task_id: int) -> str:
    task = db.get_task(task_id)
    evidence = task.evidence

    template = load_template("REVIEW.md.j2")

    return template.render(
        task=task,
        summary=generate_summary(task),
        root_cause=task.root_cause,
        changes=get_changes(task.fix_branch),
        evidence=evidence,
        risks=assess_risks(task),
        rollback_command=f"git revert {evidence['after_commit']}"
    )
```

---

## Negative Capability Tests

**NEW IN V4**

Prove safety systems work by deliberately testing failure modes.

### Test Suite

```python
# tests/governance/test_negative_capabilities.py
"""
Negative capability tests - prove the system fails safely.
These tests MUST pass for Phase 0 to be complete.
"""

import pytest
from aibrain.governance import ContractEnforcer, bash_security_hook
from aibrain.ralph import run_guardrails

class TestRalphGuardrails:
    """Ralph must block forbidden patterns"""

    def test_blocks_skipped_test(self, temp_project):
        """Skipped tests are forbidden shortcuts"""
        test_file = temp_project / "tests/example.test.ts"
        test_file.write_text("""
            describe('auth', () => {
                test.skip('should validate token', () => {
                    expect(true).toBe(true);
                });
            });
        """)

        result = run_guardrails(temp_project)

        assert result.blocked is True
        assert "skip" in result.reason.lower()

    def test_blocks_ts_ignore(self, temp_project):
        """TypeScript suppressions are forbidden"""
        src_file = temp_project / "src/auth.ts"
        src_file.write_text("""
            // @ts-ignore
            const x: string = 123;
        """)

        result = run_guardrails(temp_project)

        assert result.blocked is True
        assert "ts-ignore" in result.reason.lower()

    def test_blocks_eslint_disable(self, temp_project):
        """ESLint suppressions are forbidden"""
        src_file = temp_project / "src/utils.ts"
        src_file.write_text("""
            // eslint-disable-next-line
            const unused = 'value';
        """)

        result = run_guardrails(temp_project)

        assert result.blocked is True
        assert "eslint" in result.reason.lower()


class TestBashSecurityHook:
    """Bash hook must block dangerous commands"""

    def test_blocks_rm_rf_root(self):
        """rm -rf / is always blocked"""
        result = bash_security_hook({"command": "rm -rf /"})

        assert result["decision"] == "block"

    def test_blocks_rm_rf_home(self):
        """rm -rf ~ is always blocked"""
        result = bash_security_hook({"command": "rm -rf ~"})

        assert result["decision"] == "block"

    def test_blocks_chmod_777(self):
        """chmod 777 is blocked (too permissive)"""
        result = bash_security_hook({"command": "chmod 777 /etc/passwd"})

        assert result["decision"] == "block"

    def test_allows_safe_commands(self):
        """Safe commands are allowed"""
        safe_commands = ["ls -la", "cat src/auth.ts", "npm test", "git status"]

        for cmd in safe_commands:
            result = bash_security_hook({"command": cmd})
            assert result.get("decision") != "block", f"Safe command blocked: {cmd}"


class TestContractEnforcement:
    """Autonomy contracts must be enforced"""

    def test_bugfix_cannot_deploy(self):
        """BugFix agent cannot deploy"""
        enforcer = ContractEnforcer("bugfix")
        allowed, reason = enforcer.check_action("deploy")

        assert allowed is False
        assert "forbidden" in reason.lower()

    def test_codequality_cannot_delete_tests(self):
        """CodeQuality agent cannot delete tests"""
        enforcer = ContractEnforcer("codequality")
        allowed, reason = enforcer.check_action("delete_tests")

        assert allowed is False


class TestKillSwitch:
    """Kill switch must work instantly"""

    def test_off_mode_blocks_all_writes(self):
        """OFF mode blocks all file writes"""
        import os
        os.environ["AI_BRAIN_MODE"] = "OFF"

        with pytest.raises(ModeRestrictionError):
            write_file("test.txt", "content")

    def test_safe_mode_allows_tests(self):
        """SAFE mode allows running tests"""
        import os
        os.environ["AI_BRAIN_MODE"] = "SAFE"

        # Should not raise
        result = run_tests("/path/to/project")
        assert result is not None
```

---

## No-New-Features Guardrail

**NEW IN V4**

Simplified approach using line limits instead of AST parsing.

### Implementation

```python
# governance/no_new_features.py
def check_no_new_features(task_type: str, diff: str) -> list[str]:
    """
    Check that a bug fix doesn't accidentally add new features.
    Uses simple heuristics rather than full AST parsing.
    """
    warnings = []

    if task_type != "bugfix":
        return []

    lines_added = count_lines_added(diff)

    # Heuristic 1: Line count
    if lines_added > 100:
        warnings.append(f"Large change ({lines_added} lines) - review for scope creep")

    # Heuristic 2: New exports (TypeScript)
    new_exports = re.findall(r'^\+\s*export\s+(function|class|const)', diff, re.MULTILINE)
    if new_exports:
        warnings.append(f"New exports detected ({len(new_exports)}) - verify necessary")

    # Heuristic 3: New routes/endpoints
    new_routes = re.findall(r'^\+.*\.(get|post|put|delete|patch)\s*\(', diff, re.MULTILINE)
    if new_routes:
        warnings.append(f"New API routes detected - bug fixes shouldn't add routes")

    return warnings
```

---

## Knowledge Objects

**NEW IN V4**

Durable semantic memory that captures institutional learning from resolved issues.

> **Episodic memory explains *what happened*.**
> **Knowledge Objects explain *what must never be forgotten*.**

### Design Principle

Knowledge Objects convert episodic execution (audit_log, sessions, REVIEW.md) into permanent, actionable knowledge without heavyweight infrastructure.

### What a Knowledge Object Captures

| Field | Purpose |
|-------|---------|
| `what_was_learned` | The irreducible insight (1-3 sentences) |
| `why_it_matters` | Impact if ignored |
| `prevention_rule` | How to prevent recurrence |
| `detection_pattern` | Regex/glob to detect similar issues |
| `tags` | For pattern matching (no embeddings in v1) |
| `issue_id` | Traceability to source issue |

### Creation Rules

- Created **only** on `RESOLVED_FULL` status
- **Exactly one** per resolved issue (or zero if not insightful)
- **Human-approved** (draft → approved workflow)
- **Advisory** (inform agents, don't block)

### Integration Points

```
Issues ←──────── Knowledge Objects ──────→ REVIEW.md
   │                    │                      │
   │                    ▼                      │
   │              Agents consult               │
   │              before acting                │
   │                    │                      │
   └────────────────────┴──────────────────────┘
                        │
                        ▼
                   audit_log
              (tracks consultations)
```

### Storage

- **Primary**: Postgres `knowledge_objects` table
- **Mirror**: Markdown files in `knowledge/` for Obsidian
- **Matching**: Tag-based (no vector embeddings in v1)

**Full specification**: See [KNOWLEDGE-OBJECTS-v1.md](./KNOWLEDGE-OBJECTS-v1.md)

---

## Ralph Wiggum Verification System

*[Inherited from V3 - no changes]*

### Verification Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     RALPH VERIFICATION                       │
├─────────────────────────────────────────────────────────────┤
│  0. Initialize (RUN_ID, PRE snapshot)                        │
│  1. Guardrails (FAIL-FAST on shortcuts)                      │
│  2. Lint (ESLint/Ruff)                                       │
│  3. Type Check (TypeScript/mypy)                             │
│  4. Tests (full suite)                                       │
│  5. Coverage (≥ 80%)                                         │
│  6. Finalize (POST snapshot, SUMMARY.txt)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## AMADO Orchestrator Patterns

*[Inherited from V3]*

### Patterns to Reuse

1. **Bash Security Hook** (`security.py`): Allowlist + per-command validation
2. **Checkpoint Pattern** (`checkpoint.py`): Save state at milestones
3. **Circuit Breaker** (`circuit_breaker.py`): Prevent infinite loops
4. **Result Verifier** (`result_verifier.py`): Validate agent outputs

---

## Target Application Analysis

*[Inherited from V3]*

### KareMatch (App B)
- **Autonomy Level**: L2 (Autonomous with checkpoints)
- **Ralph Status**: Fully integrated

### CredentialMate (App A)
- **Autonomy Level**: L1 (Semi-supervised, HIPAA)
- **Ralph Status**: Fully integrated

---

## Complete Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI BRAIN V4                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐    ┌──────────────────┐                       │
│  │  CredentialMate  │    │    KareMatch     │                       │
│  │   (App A - L1)   │    │   (App B - L2)   │                       │
│  └────────┬─────────┘    └────────┬─────────┘                       │
│           │                       │                                 │
│           └───────────┬───────────┘                                 │
│                       ▼                                             │
│           ┌───────────────────────┐                                 │
│           │   AI Brain Database   │                                 │
│           │  + Enhanced Audit Log │  ← NEW: Causality tracking      │
│           └───────────┬───────────┘                                 │
│                       │                                             │
│        ┌──────────────┼──────────────┐                              │
│        ▼              ▼              ▼                              │
│  ┌─────────┐    ┌─────────┐    ┌──────────┐                        │
│  │ BugFix  │    │CodeQual │    │ Refactor │                        │
│  │ Agent   │    │ Agent   │    │  Agent   │                        │
│  └────┬────┘    └────┬────┘    └────┬─────┘                        │
│       └──────────────┼──────────────┘                               │
│                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Governance Engine                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │  │
│  │  │ Autonomy   │  │ Kill-Switch│  │ No-New-    │              │  │
│  │  │ Contracts  │  │ Safe Mode  │  │ Features   │              │  │
│  │  └────────────┘  └────────────┘  └────────────┘              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │  │
│  │  │ Safety     │  │ BugFix     │  │ CodeQual   │              │  │
│  │  │ Hooks      │  │ Rules      │  │ Rules      │              │  │
│  │  └���───────────┘  └────────────┘  └────────────┘              ���  │
│  └──────────────────────────────────────────────────────────────┘  │
│                      │                                              │
│                      ▼                                              │
│          ┌────────────────────────┐                                 │
│          │   Ralph Verification   │                                 │
│          │   + Human Review UX    │  ← NEW: REVIEW.md               │
│          └────────────────────────┘                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema (Enhanced)

### Enhanced Audit Log (NEW in V4)

```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Context
    project_id INTEGER REFERENCES projects(id),
    task_id INTEGER REFERENCES tasks(id),
    session_id UUID,
    agent_type VARCHAR(50),

    -- Action details
    action TEXT NOT NULL,
    action_type VARCHAR(50),
    rule_id TEXT,
    details JSONB,

    -- Causality (NEW in V4)
    parent_event_id INTEGER REFERENCES audit_log(id),
    caused_by_event_id INTEGER REFERENCES audit_log(id),

    -- Decision tracking (NEW in V4)
    decision_rationale TEXT,
    risk_level VARCHAR(20),

    -- Blocking details
    blocked_command TEXT,
    block_reason TEXT,

    -- Performance (NEW in V4)
    duration_ms INTEGER
);

CREATE INDEX idx_audit_log_session ON audit_log(session_id);
CREATE INDEX idx_audit_log_task ON audit_log(task_id);
CREATE INDEX idx_audit_log_parent ON audit_log(parent_event_id);
```

---

## Implementation Phases

### Phase -1: Trust Calibration Sprint (1 week) **[NEW]**

- [ ] 3 trivial bugs fixed manually with evidence
- [ ] 1 medium bug fixed with full audit trail
- [ ] 2 forbidden actions blocked by guardrails
- [ ] Evidence quality assessment (score >= 4)
- [ ] Go/No-Go decision

### Phase 0: Governance Foundation (2 weeks)

**Week 1**:
- [ ] Autonomy Contracts (YAML files)
- [ ] Kill-Switch / Safe Mode implementation
- [ ] Enhanced Audit Schema
- [ ] Core Safety Hooks

**Week 2**:
- [ ] BugFix Governance Rules
- [ ] CodeQuality Governance Rules
- [ ] Negative Capability Test Suite
- [ ] Stuck Detection

### Phase 1: BugFix + CodeQuality Agents (4-6 weeks)

- Week 1-2: BugFix Agent + Human Review UX (REVIEW.md)
- Week 3: **First Real Bug Fix in KareMatch**
- Week 4-5: CodeQuality Agent + No-New-Features Guard
- Week 6: **First Quality Batch in KareMatch**

### Phase 2-5: *[Same as V3]*

---

## Success Metrics

### Phase -1 Success
- [ ] 4/4 calibration tasks pass
- [ ] Evidence quality score >= 4
- [ ] Go decision for Phase 0

### Phase 0 Success
- [ ] All negative capability tests pass
- [ ] Kill-switch response time < 1 second
- [ ] Autonomy contracts enforced

### Phase 1 Success
- [ ] **First real bug in KareMatch fixed**
- [ ] **First quality batch completed**
- [ ] REVIEW.md generated and useful
- [ ] Human review time < 5 minutes
- [ ] Zero regressions

---

## Appendix: What We Explicitly Did NOT Add

| Recommendation | Reason for Rejection |
|----------------|---------------------|
| Full OpenTelemetry schema | Over-engineering. Extended audit_log instead. |
| Temporal workflow infrastructure | Heavyweight. Checkpoint pattern sufficient. |
| Cross-language abstraction layer | Maintenance burden. Accept duplication. |
| Evidence schema versioning | YAGNI. Defer to Phase 3. |
| Drift detection between repos | Only 2 repos. Defer to Phase 4. |

**The Meta-Principle**: Build for the scale you have, not the scale you imagine.

---

## Next Actions

### Immediate (This Week)
1. [ ] Review and approve V4 plan
2. [ ] Set up Phase -1 calibration environment
3. [ ] Select 3 trivial + 1 medium bug from KareMatch

### Phase -1 (Next Week)
4. [ ] Execute Trust Calibration Sprint
5. [ ] Document friction points
6. [ ] Make Go/No-Go decision for Phase 0