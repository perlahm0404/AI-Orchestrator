# Ralph Wiggum: Centralized Governance Engine

**Date**: 2026-01-05
**Status**: Design Specification
**Principle**: Ralph is the law. Apps provide context. Agents obey. Humans trust the verdict.

---

## Design Principle

Ralph Wiggum is a **centralized governance engine** owned by AI Brain. It is:

- **The single source of truth** for verification verdicts
- **App-agnostic** in policy, **context-aware** in execution
- **Immutable in governance** — apps cannot override rules
- **Auditable** — every verdict has evidence

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI BRAIN                                 │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                  RALPH GOVERNANCE ENGINE                 │   │
│   │                                                         │   │
│   │   Policy (immutable)    +    Context (from app)         │   │
│   │           │                        │                    │   │
│   │           └────────────┬───────────┘                    │   │
│   │                        ▼                                │   │
│   │                   VERIFICATION                          │   │
│   │                        │                                │   │
│   │                        ▼                                │   │
│   │              PASS │ FAIL │ BLOCKED                      │   │
│   │                        │                                │   │
│   │                        ▼                                │   │
│   │                 AUDIT ARTIFACT                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. AI Brain–Level Design

### 1.1 Ralph Core Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Policy enforcement** | Define what PASS, FAIL, BLOCKED mean |
| **Guardrail detection** | Scan for forbidden patterns (skips, suppressions, etc.) |
| **Step sequencing** | Execute verification steps in correct order |
| **Verdict emission** | Produce canonical PASS / FAIL / BLOCKED |
| **Audit artifact generation** | Create immutable evidence of verification |
| **Threshold enforcement** | Enforce coverage, line limits, file limits |
| **Autonomy contract integration** | Check agent actions against contracts |

### 1.2 Directory Structure

```
ai-brain/
├─ ralph/
│  ├─ __init__.py
│  ├─ engine.py                    # Core verification engine
│  ├─ verdict.py                   # Verdict types and semantics
│  ├─ policy/
│  │  ├─ __init__.py
│  │  ├─ v1.yaml                   # Policy set v1 (immutable once released)
│  │  ├─ v2.yaml                   # Policy set v2 (future)
│  │  └─ schema.py                 # Policy validation
│  ├─ guardrails/
│  │  ├─ __init__.py
│  │  ├─ shortcuts.py              # Detect @ts-ignore, .skip(), etc.
│  │  ├─ suppressions.py           # Detect eslint-disable, etc.
│  │  ├─ config_tampering.py       # Detect coverage/TS config changes
│  │  └─ patterns.yaml             # Forbidden patterns (language-agnostic)
│  ├─ steps/
│  │  ├─ __init__.py
│  │  ├─ guardrail_step.py         # Step 1: Guardrail scan
│  │  ├─ lint_step.py              # Step 2: Lint
│  │  ├─ typecheck_step.py         # Step 3: Type check
│  │  ├─ test_step.py              # Step 4: Tests
│  │  └─ coverage_step.py          # Step 5: Coverage
│  ├─ audit/
│  │  ├─ __init__.py
│  │  ├─ artifact.py               # Audit artifact generation
│  │  ├─ snapshot.py               # PRE/POST snapshot logic
│  │  └─ evidence.py               # Evidence collection
│  └─ context/
│     ├─ __init__.py
│     ├─ schema.py                 # AppContext schema
│     └─ loader.py                 # Load context from app adapter
```

### 1.3 Core Types

```python
# ralph/verdict.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

class VerdictType(Enum):
    PASS = "PASS"           # All steps succeeded
    FAIL = "FAIL"           # One or more steps failed (fixable)
    BLOCKED = "BLOCKED"     # Guardrail violation (not fixable without removing violation)

@dataclass(frozen=True)
class Verdict:
    """Immutable verification verdict."""
    type: VerdictType
    run_id: str                          # {timestamp}-{git_sha}
    ralph_version: str                   # e.g., "1.0.0"
    policy_version: str                  # e.g., "v1"

    # Step results
    guardrail_passed: bool
    lint_passed: bool
    typecheck_passed: bool
    tests_passed: bool
    coverage_passed: bool

    # Failure details (if any)
    failed_step: Optional[str]
    failure_reason: Optional[str]
    blocked_patterns: list[str]          # Guardrail violations found

    # Metrics
    test_count: int
    coverage_percent: float
    lint_errors: int
    type_errors: int

    # Timestamps
    started_at: datetime
    completed_at: datetime
    duration_ms: int

    # Evidence paths
    artifact_path: str                   # Path to full audit artifact

    def is_terminal_pass(self) -> bool:
        """True if all steps passed and verdict is PASS."""
        return self.type == VerdictType.PASS

    def requires_human_intervention(self) -> bool:
        """True if blocked by guardrail (cannot be auto-fixed)."""
        return self.type == VerdictType.BLOCKED
```

### 1.4 Policy Schema

```yaml
# ralph/policy/v1.yaml
policy:
  version: "v1"
  released_at: "2026-01-05"
  immutable: true  # Once released, never modified

# Guardrail rules (BLOCKED if violated)
guardrails:
  forbidden_patterns:
    typescript:
      - pattern: "@ts-ignore"
        reason: "TypeScript suppressions bypass type safety"
      - pattern: "@ts-nocheck"
        reason: "TypeScript suppressions bypass type safety"
      - pattern: "@ts-expect-error"
        reason: "TypeScript suppressions bypass type safety"

    javascript:
      - pattern: "eslint-disable"
        reason: "ESLint suppressions bypass lint rules"
      - pattern: "eslint-disable-next-line"
        reason: "ESLint suppressions bypass lint rules"

    testing:
      - pattern: "\\.skip\\s*\\("
        reason: "Skipped tests indicate incomplete verification"
      - pattern: "\\.only\\s*\\("
        reason: "Focused tests exclude other tests from running"
      - pattern: "test\\.todo"
        reason: "TODO tests indicate incomplete implementation"

    python:
      - pattern: "# type: ignore"
        reason: "Type ignore comments bypass type checking"
      - pattern: "# noqa"
        reason: "Noqa comments bypass lint rules"
      - pattern: "@pytest.mark.skip"
        reason: "Skipped tests indicate incomplete verification"

  config_tampering:
    coverage_threshold:
      min_allowed: 80
      tampering_detection: true
    typescript_strict:
      must_be_enabled: true
      tampering_detection: true

# Step requirements (FAIL if not met)
steps:
  lint:
    required: true
    max_errors: 0

  typecheck:
    required: true
    max_errors: 0

  tests:
    required: true
    must_all_pass: true

  coverage:
    required: true
    min_percent: 80

# Thresholds (FAIL if exceeded, unless exempted)
thresholds:
  max_lines_added: 100
  max_files_changed: 5

# Verdict semantics
verdicts:
  PASS:
    meaning: "All steps succeeded, no guardrail violations"
    agent_action: "May proceed to next phase"
    human_action: "Review REVIEW.md, approve/reject"

  FAIL:
    meaning: "One or more steps failed, but no guardrail violations"
    agent_action: "Must fix failures before proceeding"
    human_action: "None until agent produces PASS"

  BLOCKED:
    meaning: "Guardrail violation detected, cannot proceed"
    agent_action: "Must remove violation, cannot bypass"
    human_action: "Investigate if agent is misbehaving"
```

### 1.5 Versioning Strategy

```
Ralph Version: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes to verdict semantics
- MINOR: New guardrails or steps (backward compatible)
- PATCH: Bug fixes only

Policy Version: v1, v2, v3, ...
- Each policy version is IMMUTABLE once released
- New policy = new version number
- Old policies remain available for audit replay

Example:
  Ralph 1.0.0 + Policy v1 → Verdict
  Ralph 1.1.0 + Policy v1 → Same verdict (backward compatible)
  Ralph 2.0.0 + Policy v2 → Different verdict semantics
```

### 1.6 Audit Artifact Generation

```python
# ralph/audit/artifact.py
@dataclass
class AuditArtifact:
    """Complete audit trail for a Ralph run."""

    # Identity
    run_id: str
    ralph_version: str
    policy_version: str

    # Context
    project: str
    commit_before: str
    commit_after: str
    branch: str

    # Snapshots
    pre_snapshot: dict          # Git state before
    post_snapshot: dict         # Git state after
    diff: str                   # Full diff

    # Step logs
    guardrail_log: str
    lint_log: str
    typecheck_log: str
    test_log: str
    coverage_log: str

    # Verdict
    verdict: Verdict

    # Timestamps
    created_at: datetime

    def to_markdown(self) -> str:
        """Generate human-readable summary."""
        ...

    def to_json(self) -> str:
        """Generate machine-readable artifact."""
        ...

    def save(self, path: Path):
        """Save artifact to disk."""
        artifact_dir = path / self.run_id
        artifact_dir.mkdir(parents=True)

        (artifact_dir / "SUMMARY.md").write_text(self.to_markdown())
        (artifact_dir / "verdict.json").write_text(self.verdict.to_json())
        (artifact_dir / "PRE-snapshot.json").write_text(json.dumps(self.pre_snapshot))
        (artifact_dir / "POST-snapshot.json").write_text(json.dumps(self.post_snapshot))
        (artifact_dir / "diff.patch").write_text(self.diff)
        (artifact_dir / "guardrail.log").write_text(self.guardrail_log)
        (artifact_dir / "lint.log").write_text(self.lint_log)
        (artifact_dir / "typecheck.log").write_text(self.typecheck_log)
        (artifact_dir / "test.log").write_text(self.test_log)
        (artifact_dir / "coverage.log").write_text(self.coverage_log)
```

### 1.7 Integration with Autonomy Contracts

Ralph enforces autonomy contracts at verification time:

```python
# ralph/engine.py
class RalphEngine:
    def verify(
        self,
        context: AppContext,
        contract: AutonomyContract,
        agent_type: str
    ) -> Verdict:
        """
        Run verification with contract enforcement.
        """
        # 1. Check diff against contract thresholds
        diff_stats = self._get_diff_stats(context)

        if diff_stats.lines_added > contract.max_lines_added:
            return Verdict(
                type=VerdictType.BLOCKED,
                failed_step="contract_check",
                failure_reason=f"Lines added ({diff_stats.lines_added}) exceeds contract max ({contract.max_lines_added})"
            )

        if diff_stats.files_changed > contract.max_files_changed:
            return Verdict(
                type=VerdictType.BLOCKED,
                failed_step="contract_check",
                failure_reason=f"Files changed ({diff_stats.files_changed}) exceeds contract max ({contract.max_files_changed})"
            )

        # 2. Run standard verification steps
        return self._run_verification_steps(context)
```

---

## 2. Application-Level Adapter Design

### 2.1 Adapter Responsibilities

| Adapter Does | Adapter Does NOT |
|--------------|------------------|
| Declare test command | Define what "pass" means |
| Declare coverage location | Override coverage threshold |
| Declare language/tooling | Define guardrail patterns |
| Provide project path | Modify policy |
| Execute commands locally | Interpret results |

### 2.2 AppContext Schema

```yaml
# adapters/karematch/ralph-context.yaml
project:
  name: karematch
  path: /Users/tmac/karematch
  language: typescript

commands:
  lint: "npm run lint"
  typecheck: "npm run typecheck"
  test: "npm test"
  coverage: "npm run test:coverage"

paths:
  source: ["src/"]
  tests: ["tests/", "__tests__/"]
  coverage_report: "coverage/lcov.info"
  tsconfig: "tsconfig.json"

# App-specific context (NOT policy overrides)
context:
  package_manager: npm
  test_framework: vitest
  lint_tool: eslint

# Autonomy level (from AI Brain, not overridable)
autonomy_level: L2
```

```yaml
# adapters/credentialmate/ralph-context.yaml
project:
  name: credentialmate
  path: /Users/tmac/credentialmate
  language: python

commands:
  lint: "ruff check ."
  typecheck: "mypy ."
  test: "pytest"
  coverage: "pytest --cov=src --cov-report=json"

paths:
  source: ["src/"]
  tests: ["tests/"]
  coverage_report: "coverage.json"
  pyproject: "pyproject.toml"

context:
  package_manager: uv
  test_framework: pytest
  lint_tool: ruff

autonomy_level: L1
```

### 2.3 What Apps Are NOT Allowed to Change

| Locked by Ralph | Reason |
|-----------------|--------|
| Guardrail patterns | Prevents "just this once" exceptions |
| Coverage threshold | Prevents threshold erosion |
| Verdict semantics | Ensures consistent interpretation |
| Policy version | Ensures audit reproducibility |
| Step order | Ensures fail-fast on guardrails |

**Enforcement**:

```python
# ralph/context/loader.py
def load_app_context(adapter_path: Path) -> AppContext:
    """Load context from adapter, validate no policy overrides."""

    config = yaml.safe_load((adapter_path / "ralph-context.yaml").read_text())

    # Validate no forbidden keys
    FORBIDDEN_KEYS = [
        "guardrails",
        "policy",
        "thresholds.coverage_min",
        "verdicts",
        "steps.required"
    ]

    for key in FORBIDDEN_KEYS:
        if _has_nested_key(config, key):
            raise PolicyOverrideError(
                f"App context cannot override '{key}'. "
                f"This is controlled by Ralph policy."
            )

    return AppContext(**config)
```

### 2.4 Thin Adapter Implementation

```python
# adapters/karematch/adapter.py
from ralph.context import AppContext
from ralph.engine import RalphEngine
from ralph.verdict import Verdict
from pathlib import Path

class KareMatchAdapter:
    """Thin adapter for KareMatch. Provides context only."""

    def __init__(self):
        self.context = AppContext.from_yaml(
            Path(__file__).parent / "ralph-context.yaml"
        )

    def verify(self, engine: RalphEngine, contract: AutonomyContract) -> Verdict:
        """
        Invoke Ralph with KareMatch context.

        The adapter does NOT interpret the result.
        The adapter does NOT modify policy.
        The adapter just provides context.
        """
        return engine.verify(
            context=self.context,
            contract=contract,
            agent_type="bugfix"
        )
```

---

## 3. Invocation Flow

### 3.1 Step-by-Step Sequence

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RALPH INVOCATION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

1. AGENT ACTION
   │
   │  Agent completes a code change and needs verification
   │
   ▼
2. AGENT REQUESTS VERIFICATION
   │
   │  agent.request_verification(project="karematch", contract=bugfix_contract)
   │
   ▼
3. ORCHESTRATOR LOADS ADAPTER
   │
   │  adapter = load_adapter("karematch")
   │  context = adapter.context
   │
   ▼
4. ORCHESTRATOR INVOKES RALPH
   │
   │  verdict = ralph_engine.verify(context, contract, agent_type="bugfix")
   │
   ▼
5. RALPH EXECUTES VERIFICATION
   │
   │  ┌─────────────────────────────────────────────────────────────────┐
   │  │  5a. PRE-SNAPSHOT                                               │
   │  │      - Capture git state (branch, commit, diff)                │
   │  │      - Record timestamp, run_id                                │
   │  │                                                                 │
   │  │  5b. CONTRACT CHECK                                             │
   │  │      - Verify diff stats within contract limits                │
   │  │      - If violated → BLOCKED                                   │
   │  │                                                                 │
   │  │  5c. GUARDRAIL SCAN (fail-fast)                                │
   │  │      - Scan for forbidden patterns                             │
   │  │      - If found → BLOCKED                                      │
   │  │                                                                 │
   │  │  5d. LINT                                                       │
   │  │      - Execute: context.commands.lint                          │
   │  │      - If errors > 0 → FAIL                                    │
   │  │                                                                 │
   │  │  5e. TYPECHECK                                                  │
   │  │      - Execute: context.commands.typecheck                     │
   │  │      - If errors > 0 → FAIL                                    │
   │  │                                                                 │
   │  │  5f. TESTS                                                      │
   │  │      - Execute: context.commands.test                          │
   │  │      - If any fail → FAIL                                      │
   │  │                                                                 │
   │  │  5g. COVERAGE                                                   │
   │  │      - Execute: context.commands.coverage                      │
   │  │      - Parse: context.paths.coverage_report                    │
   │  │      - If < policy.steps.coverage.min_percent → FAIL           │
   │  │                                                                 │
   │  │  5h. POST-SNAPSHOT                                              │
   │  │      - Capture final git state                                 │
   │  │      - Generate audit artifact                                 │
   │  │                                                                 │
   │  │  5i. EMIT VERDICT                                               │
   │  │      - Return Verdict(PASS | FAIL | BLOCKED)                   │
   │  └─────────────────────────────────────────────────────────────────┘
   │
   ▼
6. ORCHESTRATOR RECEIVES VERDICT
   │
   │  verdict = Verdict(type=PASS, ...)
   │
   ▼
7. ORCHESTRATOR LOGS TO AUDIT
   │
   │  audit_log.insert(
   │      action="ralph_verification",
   │      details={"verdict": verdict.type, "run_id": verdict.run_id}
   │  )
   │
   ▼
8. AGENT RESPONSE (based on verdict type)
   │
   ├─── PASS ───────────────────────────────────────────────────────────┐
   │    Agent proceeds to next phase (generate REVIEW.md, etc.)        │
   │                                                                    │
   ├─── FAIL ───────────────────────────────────────────────────────────┤
   │    Agent must fix the failure and re-run verification             │
   │    (within circuit breaker limits)                                │
   │                                                                    │
   └─── BLOCKED ────────────────────────────────────────────────────────┤
        Agent CANNOT proceed                                           │
        Must remove guardrail violation                                │
        Human escalation triggered                                     │
```

### 3.2 Failure Path: FAIL

```
Agent receives FAIL verdict
        │
        ▼
Agent checks failure_reason
        │
        ├─── lint_errors > 0 ─────────────→ Agent runs auto-fix, re-verifies
        │
        ├─── type_errors > 0 ─────────────→ Agent fixes types, re-verifies
        │
        ├─── tests_failed ────────────────→ Agent investigates, fixes, re-verifies
        │
        └─── coverage < threshold ────────→ Agent adds tests, re-verifies
                                                      │
                                                      ▼
                                            If failures repeat 3x
                                                      │
                                                      ▼
                                            CIRCUIT BREAKER TRIGGERED
                                                      │
                                                      ▼
                                            Human escalation
```

### 3.3 Failure Path: BLOCKED

```
Agent receives BLOCKED verdict
        │
        ▼
Agent CANNOT proceed (no retry)
        │
        ▼
Agent logs blocked_patterns to audit_log
        │
        ▼
Agent generates BLOCKED_REPORT.md
        │
        ▼
Human escalation triggered
        │
        ▼
Human investigates:
  - Is the guardrail violation legitimate?
  - Is the agent misbehaving?
  - Is policy too strict?
        │
        ├─── Agent misbehaving ───────────→ Fix agent, restart
        │
        ├─── Legitimate violation ────────→ Agent must remove it manually
        │
        └─── Policy too strict ───────────→ Consider policy v2 (rare)
```

---

## 4. Human Trust Model

### 4.1 Why Humans Trust Ralph Output

| Trust Factor | Implementation |
|--------------|----------------|
| **Immutable policy** | Policy v1 cannot be edited after release |
| **No app overrides** | Apps cannot modify guardrails or thresholds |
| **Complete audit trail** | Every verdict has full evidence |
| **Deterministic execution** | Same inputs → same verdict |
| **Fail-fast guardrails** | Violations detected before any "work" happens |
| **Versioned verdicts** | Can replay verification with same policy |

### 4.2 What Humans Never Need to Re-Check

| Ralph Guarantees | Human Does NOT Need To |
|------------------|------------------------|
| No @ts-ignore in diff | Manually grep for suppressions |
| No .skip() in tests | Manually check for skipped tests |
| All tests passed | Re-run tests locally |
| Coverage >= 80% | Calculate coverage manually |
| Lint errors = 0 | Re-run linter |
| Type errors = 0 | Re-run type checker |
| Diff within limits | Count lines/files manually |

### 4.3 What Humans SHOULD Check

| Human Responsibility | Why |
|----------------------|-----|
| Semantic correctness | Ralph checks syntax, not semantics |
| Root cause accuracy | Ralph verifies tests pass, not that fix is right |
| Unintended side effects | Ralph checks regressions via tests, but tests may be incomplete |
| Security implications | Ralph blocks shortcuts, but can't assess security logic |

### 4.4 Trust Equation

```
Human Trust =
    Ralph Verdict (PASS)
    + REVIEW.md (explains what happened)
    + Audit Artifact (proves it happened)
    + Knowledge Objects (prevents recurrence)

If Ralph says PASS:
    Human reviews REVIEW.md (~5 min)
    Human approves or requests changes
    Human does NOT re-run verification manually

If Ralph says BLOCKED:
    Human investigates immediately
    Something is wrong (agent or policy)
```

---

## 5. Summary

### Ralph Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI BRAIN REPO                                   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         ralph/                                       │   │
│   │                                                                     │   │
│   │   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │   │
│   │   │   policy/    │   │  guardrails/ │   │    steps/    │           │   │
│   │   │   v1.yaml    │   │  shortcuts   │   │  guardrail   │           │   │
│   │   │   (locked)   │   │  suppressions│   │  lint        │           │   │
│   │   └──────────────┘   │  tampering   │   │  typecheck   │           │   │
│   │                      └──────────────┘   │  test        │           │   │
│   │                                         │  coverage    │           │   │
│   │   ┌──────────────┐   ┌──────────────┐   └──────────────┘           │   │
│   │   │   engine.py  │   │   audit/     │                              │   │
│   │   │   (core)     │   │   artifact   │                              │   │
│   │   │              │   │   snapshot   │                              │   │
│   │   └──────────────┘   │   evidence   │                              │   │
│   │                      └──────────────┘                              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        adapters/                                     │   │
│   │                                                                     │   │
│   │   ┌──────────────────────┐   ┌──────────────────────┐              │   │
│   │   │     karematch/       │   │   credentialmate/    │              │   │
│   │   │  ralph-context.yaml  │   │  ralph-context.yaml  │              │   │
│   │   │  (context only)      │   │  (context only)      │              │   │
│   │   └──────────────────────┘   └──────────────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION REPOS                                  │
│                                                                             │
│   ┌───────────────────────┐         ┌───────────────────────┐              │
│   │       karematch/      │         │    credentialmate/    │              │
│   │                       │         │                       │              │
│   │   src/                │         │   src/                │              │
│   │   tests/              │         │   tests/              │              │
│   │   package.json        │         │   pyproject.toml      │              │
│   │                       │         │                       │              │
│   │   (NO ralph logic)    │         │   (NO ralph logic)    │              │
│   └───────────────────────┘         └───────────────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Invariants

1. **Ralph is the law** — Verdicts are canonical
2. **Policy is immutable** — v1 is locked forever
3. **Apps provide context** — Commands, paths, not rules
4. **Agents obey** — BLOCKED means stop, no exceptions
5. **Humans trust** — PASS means verified, no re-checking needed
6. **Audit is complete** — Every verdict has evidence

---

## References

- [v4 Planning.md](./v4%20Planning.md) — Implementation plan
- [HITL-PROJECT-PLAN.md](./HITL-PROJECT-PLAN.md) — Human-in-the-loop operations
- [PRD-AI-Brain-v1.md](./PRD-AI-Brain-v1.md) — Product requirements