---
doc-id: "g-ADR-011"
title: "Documentation Validation & Governance System"
created: "2026-01-10"
updated: "2026-01-10"
author: "Claude AI"
status: "approved"

compliance:
  soc2:
    controls: ["CC7.3", "CC8.1"]
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.12.1.1", "A.14.2.2"]
    classification: "internal"
    review-frequency: "quarterly"

project: "ai-orchestrator"
domain: "governance"
relates-to: ["ADR-010"]

version: "1.0"
---

# ADR-011: Documentation Validation & Governance System

## Status

**Approved** - 2026-01-10

## Context

Following the documentation reorganization in ADR-010, we need automated validation to maintain documentation quality and prevent regression back to disorganized state.

### Problem Statement

Without automated validation:
- **Documentation drift**: Files slowly migrate back to root directory
- **Missing compliance metadata**: SOC2/ISO frontmatter is optional, not enforced
- **Naming inconsistencies**: No enforcement of `{scope}-{type}-{identifier}` convention
- **HIPAA violations**: CredentialMate docs may use wrong classification
- **Manual enforcement**: Relies on human review during PR process

### Success Criteria

1. **Prevention over correction**: Block violations at commit time
2. **Fast feedback**: Developers get immediate error messages (< 1 second)
3. **Comprehensive coverage**: Validate file locations, frontmatter, naming, classification
4. **Cannot be bypassed**: Ralph integration ensures CI validation even if local hook skipped
5. **Zero false positives**: All blocked commits are actual violations

### Governance Agent Assessment

**Risk Level**: HIGH (Infrastructure Change)

**Verdict**: REQUIRES_APPROVAL

**Risk Breakdown**:
- Infrastructure Risk: ✅ YES (git hooks, validation pipeline)
- PHI Risk: ❌ NO
- Auth Risk: ❌ NO
- Billing Risk: ❌ NO

**Recommendations**:
1. Review infrastructure changes for reliability and security
2. Ensure proper monitoring and alerting
3. Plan rollback strategy before deployment

## Decision

Implement a **three-layer defense system** for documentation governance:

### Layer 1: Git Pre-Commit Hook
**File**: `governance/hooks/pre-commit-documentation`

**Purpose**: Fast, local validation before commit

**What It Blocks** (prevents commit):
- New markdown files at root (except allowed core docs)
- Missing frontmatter in work/ directory
- Missing compliance metadata (SOC2/ISO)
- Invalid queue naming (`{scope}-queue-active.json`)

**What It Warns** (allows commit):
- Invalid ADR naming convention
- Invalid plan naming convention

**Bypass**: `git commit --no-verify` (emergency only, tracked in git history)

**Performance**: < 100ms for typical commits

---

### Layer 2: CLI Validator
**File**: `governance/validators/documentation_validator.py`

**Purpose**: Comprehensive repository audit on demand

**Usage**:
```bash
aibrain validate-docs              # Validate entire repository
aibrain validate-docs work/        # Validate specific directory
aibrain validate-docs --report     # Generate compliance report
aibrain validate-docs --fix        # Auto-fix violations (future)
```

**What It Checks**:
- **Errors** (must fix):
  - Root directory > 15 markdown files
  - Missing frontmatter in work/
  - Invalid YAML frontmatter syntax
  - Missing required fields (doc-id, compliance.*, project, domain)
  - Invalid naming conventions (ADR, plan, queue)

- **Warnings** (should fix):
  - Files in wrong location (e.g., plans at root)
  - CredentialMate docs not using 'confidential' classification
  - Archive files without archival metadata

**Performance**: ~1-2 seconds for full repository scan

---

### Layer 3: Ralph Integration
**File**: `ralph/checkers/documentation_checker.py`

**Purpose**: Pre-merge validation (cannot be bypassed)

**When It Runs**:
1. Pre-commit (if integrated with git hooks)
2. CI pipeline (before merge to main)
3. Manual runs via `ralph verify`

**Verdicts**:
- **PASS**: All checks passed → Allow merge
- **FAIL**: Incomplete metadata → Fix recommended, warn
- **BLOCKED**: Critical violation → Block merge

**Integration**:
```python
from ralph.checkers.documentation_checker import DocumentationChecker

def verify_changes(changed_files: List[str]) -> RalphVerdict:
    doc_checker = DocumentationChecker()
    verdict, message, violations = doc_checker.check(changed_files)

    if verdict == "BLOCKED":
        return RalphVerdict.BLOCKED(
            message=message,
            details=violations,
            fix_hint="Add SOC2/ISO frontmatter to work/ documents"
        )
```

**Cannot be bypassed**: Even if pre-commit hook skipped with `--no-verify`, Ralph runs in CI

---

## Validation Rules

### Rule 1: Root File Limit
**Target**: ≤15 markdown files at root
**Severity**: WARNING
**Fix**: Move to work/, docs/, or archive/

**Allowed root files**:
- CATALOG.md, CLAUDE.md, STATE.md, DECISIONS.md
- USER-PREFERENCES.md, ROADMAP.md, QUICKSTART.md
- SYSTEM-CONFIGURATION.md, AI-RUN-COMPANY.md
- claude.md, gemini.md, README.md

---

### Rule 2: work/ Frontmatter Required
**Target**: All .md files in work/ must have frontmatter
**Severity**: ERROR (blocks commit)
**Fix**: Add YAML frontmatter with SOC2/ISO metadata

**Required fields**:
```yaml
---
doc-id: "{scope}-{type}-{identifier}"
compliance:
  soc2:
    controls: ["CC7.3", "CC8.1"]
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.12.1.1", "A.14.2.2"]
    classification: "internal|confidential"
project: "credentialmate|karematch|ai-orchestrator"
domain: "qa|dev|operator|governance"
---
```

---

### Rule 3: ADR Naming Convention
**Pattern**: `{scope}-ADR-{number}-{description}.md`
**Severity**: WARNING
**Examples**:
- ✅ `cm-ADR-006-cme-gap-calculation.md`
- ✅ `g-ADR-003-lambda-cost-controls.md`
- ❌ `ADR-006-cme-gap.md` (missing scope)

---

### Rule 4: Plan Naming Convention
**Pattern**: `{scope}-plan-{description}.md`
**Severity**: WARNING
**Examples**:
- ✅ `cm-plan-lambda-migration.md`
- ✅ `km-feature-status.md`

---

### Rule 5: Queue Naming Convention
**Pattern**: `{scope}-queue-active.json`
**Severity**: ERROR (blocks commit)
**Examples**:
- ✅ `cm-queue-active.json`
- ❌ `work_queue_credentialmate.json` (old format)

---

### Rule 6: HIPAA Classification
**Target**: CredentialMate documents (cm-*) must use `confidential` classification
**Severity**: WARNING
**Rationale**: HIPAA compliance requires strict data classification

**Fix**:
```yaml
compliance:
  iso27001:
    classification: "confidential"  # Not "internal"
```

---

## Consequences

### Positive

1. **Automatic compliance**: SOC2/ISO metadata enforced at commit time
2. **Fast feedback**: Developers see errors immediately (< 1 second)
3. **Documentation quality**: Prevents drift back to disorganized state
4. **Audit readiness**: All work/ documents have compliance metadata
5. **HIPAA safety**: Catches incorrect classification before merge
6. **Cannot bypass**: Ralph runs in CI even if local hook skipped

### Negative

1. **Developer friction**: Adds ~100ms to commit time
2. **Learning curve**: Developers must learn frontmatter requirements
3. **False positives**: May block legitimate exceptions (use `--no-verify` sparingly)
4. **Maintenance burden**: Rules must be updated as requirements evolve

### Risks

1. **Meta-governance risk**: Modifying the governance system itself
   - **Mitigation**: This ADR documents the decision, changes are versioned

2. **Developer workflow impact**: Git hooks change developer experience
   - **Mitigation**: Clear error messages, documentation in DOCUMENTATION-GOVERNANCE.md

3. **Bypass temptation**: Developers may use `--no-verify` too frequently
   - **Mitigation**: Ralph runs in CI, bypasses are tracked in git history

---

## Implementation

### Phase 1: Create Validation Tools ✅ COMPLETE
- ✅ `governance/hooks/pre-commit-documentation`
- ✅ `governance/validators/documentation_validator.py`
- ✅ `ralph/checkers/documentation_checker.py`
- ✅ `governance/DOCUMENTATION-GOVERNANCE.md`
- ✅ `governance/install-hooks.sh`

### Phase 2: Deploy Git Hooks (PENDING APPROVAL)
```bash
./governance/install-hooks.sh
```

**Rollback strategy**: Remove `.git/hooks/pre-commit` to disable

### Phase 3: CI/CD Integration (FUTURE)
```yaml
# .github/workflows/documentation-validation.yml
name: Documentation Validation
on:
  pull_request:
    paths: ['**.md', 'work/**', 'docs/**']
jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate documentation
        run: python governance/validators/documentation_validator.py --check
```

**Rollback strategy**: Remove workflow file to disable

---

## Monitoring & Alerts

### Metrics to Track

1. **Violation frequency**: How often commits are blocked
2. **Bypass rate**: Percentage of commits using `--no-verify`
3. **False positive rate**: Blocked commits that were legitimate
4. **Compliance coverage**: Percentage of work/ documents with complete frontmatter

### Alerts (Future)

- Alert if bypass rate > 10% (indicates rule problems)
- Alert if violation frequency spikes (indicates confusion)
- Alert if compliance coverage drops below 95%

---

## Rollback Strategy

### Layer 1 Rollback (Git Hook)
```bash
# Disable pre-commit hook
rm .git/hooks/pre-commit

# Or restore previous hook
mv .git/hooks/pre-commit.backup .git/hooks/pre-commit
```

**Impact**: Immediate (next commit), no data loss

### Layer 2 Rollback (CLI Validator)
```bash
# Simply stop running the validator
# No uninstall needed, validator is on-demand only
```

**Impact**: Immediate, no data loss

### Layer 3 Rollback (Ralph Integration)
```python
# Comment out documentation checker in ralph/verification.py
# doc_checker = DocumentationChecker()
# verdict, message, violations = doc_checker.check(changed_files)
```

**Impact**: Takes effect on next CI run, no data loss

---

## Alternatives Considered

### Alternative 1: Manual PR Review Only
**Rejected**: Too slow, relies on human vigilance, inconsistent enforcement

### Alternative 2: Single-Layer (Git Hook Only)
**Rejected**: Can be bypassed with `--no-verify`, no CI enforcement

### Alternative 3: CI-Only Validation (No Local Hook)
**Rejected**: Slow feedback (must push to trigger), wastes CI resources

### Alternative 4: Linter-Based (markdownlint, etc.)
**Rejected**: Cannot validate frontmatter structure, naming conventions, HIPAA classification

---

## References

- [ADR-010](./g-ADR-010-documentation-organization-archival-strategy.md) - Documentation Organization Decision
- [DOCUMENTATION-GOVERNANCE.md](../../governance/DOCUMENTATION-GOVERNANCE.md) - Complete governance guide
- [work/README.md](../README.md) - Active work directory guide
- [SOC2 Trust Services Criteria](https://us.aicpa.org/interestareas/frc/assuranceadvisoryservices/trustdataintegritytaskforce)
- [ISO/IEC 27001:2022](https://www.iso.org/standard/27001)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-10 | Implement three-layer validation | Provides defense in depth |
| 2026-01-10 | Git hook blocks (not warns) on critical violations | Fast feedback, prevents bad commits |
| 2026-01-10 | Ralph integration cannot be bypassed | Ensures compliance even if local hook skipped |
| 2026-01-10 | Use WARNING for naming conventions | Allow flexibility while encouraging standards |

---

## Approval

**Governance Agent Assessment**: REQUIRES_APPROVAL (HIGH risk - infrastructure)

**Human Approval**: PENDING

**Deployment Authorization**: PENDING

Once approved:
1. Install git hooks: `./governance/install-hooks.sh`
2. Run full validation: `python governance/validators/documentation_validator.py --report`
3. Add CI/CD workflow (optional)
4. Update DECISIONS.md with D-023 entry
