# Implementation Prompt: Automated Bug Discovery System

**Session Goal**: Implement automated bug discovery and work queue generation system to achieve 89% autonomy (+2% gain).

---

## Quick Start

```bash
# Read the implementation plan first
cat /Users/tmac/.claude/plans/soft-strolling-kazoo.md

# Then begin implementation following the 5 phases below
```

---

## What to Implement

Build a system that automatically:
1. **Scans** KareMatch codebase for bugs (ESLint, TypeScript, test failures, guardrails)
2. **Tracks** baseline bugs vs. new regressions (fingerprint-based deduplication)
3. **Prioritizes** bugs by user impact (P0=blocks users, P1=degrades UX, P2=tech debt)
4. **Generates** work queue tasks grouped by file (reduces 79 errors → 23 tasks)
5. **CLI integration** via `aibrain discover-bugs --project karematch`

**Autonomy Impact**: 87% → **89%** (+2%)

---

## Implementation Phases

### Phase 1: Error Parsers (~550 lines, 4 files)

Create parsers to extract structured bugs from tool outputs.

**Files to create**:
1. `discovery/parsers/eslint.py` (~150 lines)
   - Parse `npm run lint -- --format=json` output
   - Extract: file, line, rule_id, severity, message
   - Priority: P0=security, P1=correctness, P2=style

2. `discovery/parsers/typescript.py` (~120 lines)
   - Parse `npm run check` output (plain text)
   - Extract: file, line, error_code (TS2345), message
   - Priority: P0=critical paths, P1=missing types, P2=general

3. `discovery/parsers/test.py` (~180 lines)
   - Parse `npm test -- --reporter=json` output
   - Extract: test_file, test_name, failure_message
   - Infer source file from test file path
   - Priority: P0=auth/payment, P1=features, P2=flaky

4. `discovery/parsers/guardrails.py` (~100 lines)
   - Parse `rg --json` output for patterns
   - Patterns: `@ts-ignore`, `eslint-disable`, `.skip()`, `.only()`
   - Priority: P0=.only/.skip, P1=@ts-ignore, P2=@ts-nocheck

**Key Classes**:
```python
@dataclass
class LintError:
    file: str
    line: int
    column: int
    rule_id: str
    severity: int
    message: str
    priority: int

@dataclass
class TypeScriptError:
    file: str
    line: int
    column: int
    error_code: str
    message: str
    priority: int

@dataclass
class TestFailure:
    test_file: str
    test_name: str
    failure_message: str
    source_file: str  # Inferred
    priority: int

@dataclass
class GuardrailViolation:
    file: str
    line: int
    pattern: str
    context: str
    priority: int
```

---

### Phase 2: Scanner Engine (~200 lines, 1 file)

Orchestrate all parsers and collect results.

**File to create**: `discovery/scanner.py`

**Core Logic**:
```python
class BugScanner:
    def __init__(self, project_path: Path, project_name: str):
        self.project_path = project_path
        self.project_name = project_name
        self.parsers = {
            'lint': ESLintParser(),
            'typecheck': TypeScriptParser(),
            'test': TestParser(),
            'guardrails': GuardrailParser()
        }

    def scan(self, sources: list[str] = None) -> ScanResult:
        """Run all scanners and return structured bugs."""
        # Run each scanner command
        # Parse output with appropriate parser
        # Return ScanResult with all errors

@dataclass
class ScanResult:
    timestamp: datetime
    project: str
    lint_errors: list[LintError]
    type_errors: list[TypeScriptError]
    test_failures: list[TestFailure]
    guardrail_violations: list[GuardrailViolation]

    def total_errors(self) -> int:
        """Total count across all types."""

    def by_file(self) -> dict[str, list]:
        """Group all errors by file path."""
```

**Commands to run**:
- Lint: `npm run lint -- --format=json`
- Typecheck: `npm run check 2>&1`
- Test: `npm test -- --reporter=json`
- Guardrails: `rg '@ts-ignore|@ts-nocheck|eslint-disable|\.skip\(|\.only\(' --json --type typescript`

---

### Phase 3: Baseline Tracking (~150 lines, 1 file)

Track known bugs vs. new regressions using fingerprinting.

**File to create**: `discovery/baseline.py`

**Baseline Format** (`discovery/baselines/karematch-baseline.json`):
```json
{
  "timestamp": "2026-01-06T10:00:00",
  "project": "karematch",
  "commit_sha": "abc123def",
  "bugs": [
    {
      "file": "services/auth/src/login.ts",
      "line": 42,
      "type": "lint",
      "rule": "unused-imports/no-unused-imports",
      "fingerprint": "sha256:abc123..."
    }
  ]
}
```

**Core Logic**:
```python
class BaselineManager:
    def create_baseline(self, scan_result: ScanResult) -> None:
        """Create initial baseline snapshot."""
        # Compute fingerprints (sha256 of file:line:rule)
        # Save to discovery/baselines/{project}-baseline.json

    def compare_with_baseline(self, scan_result: ScanResult) -> tuple[list, list]:
        """
        Compare current scan with baseline.
        Returns: (new_bugs, baseline_bugs)
        """
        # Load baseline
        # Compute current fingerprints
        # Set difference to find new bugs
        # Return both lists
```

**Fingerprinting**:
- Lint: `sha256(file:line:rule_id)`
- Type: `sha256(file:line:error_code)`
- Test: `sha256(test_file:test_name)`
- Guardrail: `sha256(file:line:pattern)`

---

### Phase 4: Task Generator (~250 lines, 1 file)

Convert bugs → work queue tasks (grouped by file).

**File to create**: `discovery/task_generator.py`

**Core Logic**:
```python
class TaskGenerator:
    def generate_tasks(
        self,
        scan_result: ScanResult,
        new_bugs: list[dict],
        baseline_bugs: list[dict]
    ) -> list[Task]:
        """
        Generate work queue tasks from scan results.
        Strategy: Group by file (all errors in same file = 1 task)
        Priority: New bugs = P0, baseline bugs = P1-P2
        """
        # Group all bugs by file
        # Create one task per file
        # Compute priority based on impact
        # Sort by priority (P0 first)
        # Return task list

    def _compute_priority(self, file_path: str, bugs: list[dict]) -> int:
        """
        Compute priority (P0/P1/P2) based on user impact.

        P0 (blocks users):
        - Auth/payment failures
        - Test failures in critical paths
        - Security issues

        P1 (degrades UX):
        - Type errors in user-facing code
        - Test failures in features
        - New regressions

        P2 (tech debt):
        - Linting issues
        - Guardrail violations
        - Baseline bugs (not new)
        """
```

**Task ID Prefixes**:
- `TEST-*` → TestWriter agent (15 iterations, TESTS_COMPLETE)
- `TYPE-*` → CodeQuality agent (20 iterations, CODEQUALITY_COMPLETE)
- `LINT-*` → CodeQuality agent (20 iterations, CODEQUALITY_COMPLETE)
- `GUARD-*` → CodeQuality agent (20 iterations, CODEQUALITY_COMPLETE)

**New Task Fields** (add to `tasks/work_queue.py`):
```python
@dataclass
class Task:
    # ... existing fields ...
    priority: Optional[int] = None       # 0=P0, 1=P1, 2=P2
    bug_count: Optional[int] = None      # How many bugs in this file
    is_new: Optional[bool] = None        # True if any bugs are new regressions
```

---

### Phase 5: CLI Integration (~150 lines, 1 file)

Add `aibrain discover-bugs` command.

**File to create**: `cli/commands/discover.py`

**Command Signature**:
```python
@click.command()
@click.option('--project', required=True, type=click.Choice(['karematch', 'credentialmate']))
@click.option('--sources', default='lint,typecheck,test,guardrails',
              help='Bug sources to scan (comma-separated)')
@click.option('--reset-baseline', is_flag=True, help='Reset baseline snapshot')
@click.option('--dry-run', is_flag=True, help='Show tasks without modifying work queue')
def discover_bugs(project: str, sources: str, reset_baseline: bool, dry_run: bool):
    """
    Scan codebase for bugs and generate work queue tasks.

    First run creates baseline. Subsequent runs flag new bugs as P0.
    """
```

**Workflow**:
1. Load project adapter (KareMatch or CredentialMate)
2. Run scanner (`BugScanner.scan()`)
3. Compare with baseline (`BaselineManager.compare_with_baseline()`)
4. Generate tasks (`TaskGenerator.generate_tasks()`)
5. Display summary (P0/P1/P2 counts, first 10 tasks)
6. If not dry-run: Update work_queue.json (ask for merge strategy)

**Merge Strategies**:
- **Append**: Add new tasks to end of existing queue
- **Replace**: Clear existing queue and use new tasks
- **Merge**: Deduplicate by file path (only add new files)

**File to modify**: `cli/__main__.py`
- Import and register `discover_bugs` command

---

## Testing Plan

### Unit Tests (~300 lines)

**File**: `tests/discovery/test_parsers.py`

Test each parser with sample outputs:
```python
def test_eslint_parser():
    sample_json = '[{"filePath": "foo.ts", "messages": [...]}]'
    parser = ESLintParser()
    errors = parser.parse(sample_json)
    assert len(errors) == expected_count
    assert errors[0].rule_id == "unused-imports/no-unused-imports"

def test_typescript_parser():
    sample_output = "src/auth/session.ts(42,10): error TS2345: ..."
    parser = TypeScriptParser()
    errors = parser.parse(sample_output)
    assert errors[0].error_code == "TS2345"

# Similar for test and guardrail parsers
```

### Integration Tests (~200 lines)

**File**: `tests/discovery/test_scanner.py`

Test end-to-end on mock project:
```python
def test_full_scan_workflow():
    # Create minimal TypeScript project with known bugs
    # Run scanner
    # Verify correct bugs detected
    # Verify baseline tracking works
    # Verify task generation groups by file
```

### Manual Testing

```bash
# 1. First scan (dry run)
aibrain discover-bugs --project karematch --dry-run

# 2. Create baseline
aibrain discover-bugs --project karematch

# 3. Verify baseline file created
ls discovery/baselines/karematch-baseline.json

# 4. Run again to test baseline comparison
aibrain discover-bugs --project karematch --dry-run

# 5. Check work queue
cat tasks/work_queue.json
```

---

## Implementation Checklist

### Phase 1: Parsers
- [ ] Create `discovery/parsers/__init__.py`
- [ ] Create `discovery/parsers/eslint.py`
- [ ] Create `discovery/parsers/typescript.py`
- [ ] Create `discovery/parsers/test.py`
- [ ] Create `discovery/parsers/guardrails.py`
- [ ] Test parsers with sample outputs

### Phase 2: Scanner
- [ ] Create `discovery/__init__.py`
- [ ] Create `discovery/scanner.py`
- [ ] Test scanner on KareMatch (dry run, no modifications)

### Phase 3: Baseline
- [ ] Create `discovery/baseline.py`
- [ ] Test baseline creation
- [ ] Test baseline comparison

### Phase 4: Task Generator
- [ ] Create `discovery/task_generator.py`
- [ ] Add `priority`, `bug_count`, `is_new` fields to Task dataclass
- [ ] Test task generation with sample bugs

### Phase 5: CLI
- [ ] Create `cli/commands/discover.py`
- [ ] Register command in `cli/__main__.py`
- [ ] Test CLI end-to-end

### Documentation
- [ ] Update `STATE.md` (87% → 89% autonomy)
- [ ] Update `CLAUDE.md` (add bug discovery section)
- [ ] Create session handoff document

### Testing
- [ ] Write unit tests (`tests/discovery/test_parsers.py`)
- [ ] Write integration tests (`tests/discovery/test_scanner.py`)
- [ ] Manual testing on KareMatch

---

## Key Design Decisions

### 1. Group by File (Not Per-Error)
**Rationale**: Reduces task count from 79 errors → 23 tasks. Agent fixes all issues in a file at once.

**Example**:
- Before: `LINT-001`, `LINT-002`, `LINT-003` (3 lint errors in same file)
- After: `LINT-AUTH-LOGIN-001` (1 task with 3 bugs)

### 2. Impact-Based Priority
**Rationale**: User-facing impact matters more than error type.

**Priority Logic**:
- **P0**: Security issues, auth/payment test failures, critical path type errors
- **P1**: New regressions, type errors, feature test failures
- **P2**: Baseline bugs, lint issues, guardrail violations, style

### 3. Hybrid Baseline Approach
**Rationale**: Track all bugs but prioritize new regressions.

**First Run**: Creates baseline, treats all bugs as baseline (P1-P2)
**Subsequent Runs**: Flags new bugs as P0, baseline bugs as P1-P2

### 4. Fingerprint Deduplication
**Rationale**: Prevents re-processing same bugs across scans.

**Fingerprint**: `sha256(file:line:rule)` uniquely identifies each bug
**Comparison**: Set difference finds new bugs introduced since baseline

---

## Expected Output

```bash
$ aibrain discover-bugs --project karematch

================================================================================
🔍 Bug Discovery - karematch
================================================================================

📊 Step 1: Scanning codebase...

🔍 Scanning lint...
   Found 42 issues
🔍 Scanning typecheck...
   Found 18 issues
🔍 Scanning test...
   Found 7 issues
🔍 Scanning guardrails...
   Found 12 issues

✅ Scan complete:
   Lint errors: 42
   Type errors: 18
   Test failures: 7
   Guardrail violations: 12
   Total: 79

📊 Step 2: Comparing with baseline...

⚠️  No baseline found - creating one now
✅ Baseline created: 79 bugs tracked

📊 Step 3: Generating tasks...

✅ Generated 23 tasks:
   P0 (blocks users): 3
   P1 (degrades UX): 8
   P2 (tech debt): 12

📋 Task Summary (first 10):

  🆕 [P0] TEST-LOGIN-001: Fix 2 test error(s) in services/auth/tests/login.test.ts (NEW REGRESSION)
  🆕 [P0] TYPE-SESSION-002: Fix 1 typecheck error(s) in services/auth/src/session.ts (NEW REGRESSION)
     [P1] LINT-MATCHING-003: Fix 3 lint error(s) in services/matching/src/matcher.ts (baseline)
     [P1] TYPE-ROUTES-004: Fix 2 typecheck error(s) in services/appointments/src/routes.ts (baseline)

  ... and 19 more

📊 Step 4: Updating work queue...

✅ Work queue updated: tasks/work_queue.json
   Total tasks: 23
   Pending: 23

🚀 Ready to run: python autonomous_loop.py --project karematch
```

---

## Success Criteria

- [ ] Scanner completes in < 10 minutes for KareMatch
- [ ] Task grouping reduces count by 50-70% (vs. per-error tasks)
- [ ] Priority accuracy: 80% of P0 tasks are truly high impact
- [ ] Baseline deduplication: 100% prevents re-processing known bugs
- [ ] False positive rate: < 10%
- [ ] Autonomy increase: 87% → 89% (+2%)

---

## Files Summary

### New Files (10 total, ~1800 lines)
1. `discovery/__init__.py`
2. `discovery/parsers/__init__.py`
3. `discovery/parsers/eslint.py` (~150 lines)
4. `discovery/parsers/typescript.py` (~120 lines)
5. `discovery/parsers/test.py` (~180 lines)
6. `discovery/parsers/guardrails.py` (~100 lines)
7. `discovery/scanner.py` (~200 lines)
8. `discovery/baseline.py` (~150 lines)
9. `discovery/task_generator.py` (~250 lines)
10. `cli/commands/discover.py` (~150 lines)
11. `tests/discovery/test_parsers.py` (~300 lines)
12. `tests/discovery/test_scanner.py` (~200 lines)

### Modified Files (4 total, ~50 lines)
1. `tasks/work_queue.py`: Add 3 fields to Task dataclass
2. `cli/__main__.py`: Register discover-bugs command
3. `STATE.md`: Update autonomy 87% → 89%
4. `CLAUDE.md`: Add bug discovery documentation

---

## References

**Implementation Plan**: `/Users/tmac/.claude/plans/soft-strolling-kazoo.md`

**Current State**:
- Autonomy: 87% (after KO auto-approval)
- Work queue: Manual entry only
- Bug triaging: 100% manual

**Target State**:
- Autonomy: 89% (+2%)
- Work queue: Auto-generated from scans
- Bug triaging: 10% manual (review only)

---

## Quick Commands for Next Session

```bash
# 1. Read the plan
cat /Users/tmac/.claude/plans/soft-strolling-kazoo.md

# 2. Start with Phase 1 (parsers)
# Create discovery/parsers/ directory and implement parsers

# 3. Test each parser as you go
python -m pytest tests/discovery/test_parsers.py -v

# 4. Move to Phase 2 (scanner)
# Create discovery/scanner.py

# 5. Test on KareMatch (dry run)
cd /Users/tmac/karematch
npm run lint -- --format=json > /tmp/lint-output.json
npm run check 2>&1 > /tmp/type-output.txt

# 6. Phase 3-5: baseline, task generator, CLI
# Follow plan step-by-step

# 7. Final integration test
aibrain discover-bugs --project karematch --dry-run
```

---

**Ready to implement!** Start with Phase 1 (parsers) and work through each phase systematically. The plan has all the details you need.
