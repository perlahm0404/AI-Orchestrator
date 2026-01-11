# Documentation Governance (ADR-010)

**Status**: Active
**Created**: 2026-01-10
**ADR**: [ADR-010](../AI-Team-Plans/decisions/ADR-010-documentation-organization-archival-strategy.md)

---

## Overview

This document describes the automated validation and governance system for maintaining documentation organization according to ADR-010.

### Three-Layer Defense

| Layer | Tool | When | Purpose | Byppassable |
|-------|------|------|---------|-------------|
| **1. Git Hook** | pre-commit | Before commit | Fast, local validation | Yes (`--no-verify`) |
| **2. CLI Validator** | `aibrain validate-docs` | On demand / CI | Comprehensive audit | N/A |
| **3. Ralph Integration** | Documentation checker | Pre-merge | Code quality gate | No |

---

## Layer 1: Git Pre-Commit Hook

### Installation

```bash
# Copy hook to git hooks directory
cp governance/hooks/pre-commit-documentation .git/hooks/pre-commit

# Make executable
chmod +x .git/hooks/pre-commit
```

### What It Checks

✅ **Blocks** (prevents commit):
- New markdown files at root (except allowed core docs)
- Missing frontmatter in work/ directory
- Missing compliance metadata (soc2/iso27001)
- Invalid queue naming (must be `{scope}-queue-active.json`)

⚠️ **Warns** (allows commit):
- Invalid ADR naming convention
- Invalid plan naming convention

### Bypass (Emergency Only)

```bash
# Bypass hook (use sparingly!)
git commit --no-verify -m "message"

# Note: Bypass is tracked in git history
# May still fail CI validation
```

### Example Output

```
🔍 Validating documentation structure (ADR-010)...
🚫 BLOCKED: Cannot add markdown file to root: my-plan.md
   Suggested locations:
     - work/plans-active/  (for active plans)
     - work/adrs-active/   (for active ADRs)
     - docs/guides/        (for guides)

🚫 BLOCKED: Missing frontmatter in work/plans-active/new-plan.md
   All work/ documents require SOC2/ISO compliance metadata
   See: work/README.md or plan file for template

============================================
❌ COMMIT BLOCKED: 2 violation(s)
============================================
```

---

## Layer 2: CLI Validator

### Installation

```bash
# Already available via aibrain CLI
# No installation needed
```

### Usage

```bash
# Validate entire repository
aibrain validate-docs

# Validate specific directory
aibrain validate-docs work/

# Generate compliance report
aibrain validate-docs --report

# Auto-fix violations (coming soon)
aibrain validate-docs --fix
```

### What It Checks

**Errors** (must fix):
- Root directory has >15 markdown files
- Missing frontmatter in work/ directory
- Invalid YAML frontmatter syntax
- Missing required fields (doc-id, compliance.*, project, domain)
- Invalid naming conventions (ADR, plan, queue)

**Warnings** (should fix):
- Files in wrong location (e.g., plans at root)
- CredentialMate docs not using 'confidential' classification
- Archive files without archival metadata

**Info** (informational):
- Statistics and metrics

### Example Output

```
============================================================
DOCUMENTATION STRUCTURE COMPLIANCE REPORT
============================================================

Repository: /Users/tmac/1_REPOS/AI_Orchestrator
Total violations: 3

  Errors:   1 🚫
  Warnings: 2 ⚠️
  Info:     0 ℹ️

============================================================
ERRORS (Must Fix)
============================================================

🚫 ERROR: work-frontmatter-incomplete
   File: work/plans-active/new-plan.md
   Missing required field: compliance.soc2.controls

============================================================
WARNINGS (Should Fix)
============================================================

⚠️  WARNING: hipaa-classification
   File: work/adrs-active/cm-ADR-007-duplicate-handling-data.md
   CredentialMate documents should use 'confidential' classification (found: internal)

⚠️  WARNING: file-location
   File: old-plan.md
   File should not be at root. Suggested location: work/plans-active/
```

---

## Layer 3: Ralph Integration

### How It Works

Ralph's documentation checker runs automatically during:
1. **Pre-commit** (if integrated with git hooks)
2. **CI pipeline** (before merge to main)
3. **Manual runs** via `ralph verify`

### What It Checks

- All changed files in work/ have frontmatter
- Frontmatter is valid YAML
- Required fields are present
- HIPAA compliance (CredentialMate uses 'confidential')

### Verdicts

| Verdict | Meaning | Action |
|---------|---------|--------|
| **PASS** | All checks passed | Allow merge |
| **FAIL** | Incomplete metadata | Fix recommended, warn |
| **BLOCKED** | Critical violation | Block merge |

### Example Integration

```python
# In ralph/verification.py
from ralph.checkers.documentation_checker import DocumentationChecker

def verify_changes(changed_files: List[str]) -> RalphVerdict:
    # ... existing checks ...

    # Documentation check
    doc_checker = DocumentationChecker()
    verdict, message, violations = doc_checker.check(changed_files)

    if verdict == "BLOCKED":
        return RalphVerdict.BLOCKED(
            message=message,
            details=violations,
            fix_hint="Add SOC2/ISO frontmatter to work/ documents"
        )

    # ... rest of verification ...
```

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

### Rule 2: work/ Frontmatter Required

**Target**: All .md files in work/ must have frontmatter
**Severity**: ERROR (blocks commit)
**Fix**: Add YAML frontmatter with SOC2/ISO metadata

**Required fields**:
```yaml
---
doc-id: "{scope}-{type}-{identifier}"
title: "Descriptive Title"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
author: "Claude AI / tmac"
status: "draft|active|approved"

compliance:
  soc2:
    controls: ["CC7.3", "CC8.1"]
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.12.1.1", "A.14.2.2"]
    classification: "internal|confidential"
    review-frequency: "quarterly"

project: "credentialmate|karematch|ai-orchestrator"
domain: "qa|dev|operator|governance"
relates-to: ["ADR-001"]

version: "1.0"
---
```

### Rule 3: ADR Naming Convention

**Pattern**: `{scope}-ADR-{number}-{description}.md`
**Severity**: WARNING
**Examples**:
- ✅ `cm-ADR-006-cme-gap-calculation.md`
- ✅ `g-ADR-003-lambda-cost-controls.md`
- ❌ `ADR-006-cme-gap.md` (missing scope)
- ❌ `cm-adr-6-gaps.md` (wrong format)

### Rule 4: Plan Naming Convention

**Pattern**: `{scope}-plan-{description}.md`
**Severity**: WARNING
**Examples**:
- ✅ `cm-plan-lambda-migration.md`
- ✅ `km-feature-status.md`
- ❌ `lambda-migration-plan.md` (missing scope)

### Rule 5: Queue Naming Convention

**Pattern**: `{scope}-queue-active.json`
**Severity**: ERROR (blocks commit)
**Examples**:
- ✅ `cm-queue-active.json`
- ✅ `km-queue-active.json`
- ❌ `work_queue_credentialmate.json` (old format)

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

### Rule 7: Archive Metadata

**Target**: Files in archive/ should have archival metadata
**Severity**: WARNING
**Fix**:
```yaml
---
status: archived
archived-date: "2026-01-10"
archived-reason: "Superseded by ADR-010"
superseded-by: "ADR-010"
safe-to-delete: false
---
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/documentation-validation.yml
name: Documentation Validation

on:
  pull_request:
    paths:
      - '**.md'
      - 'work/**'
      - 'docs/**'

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml

      - name: Validate documentation structure
        run: |
          python governance/validators/documentation_validator.py --check

      - name: Generate compliance report
        if: always()
        run: |
          python governance/validators/documentation_validator.py --report
```

---

## Maintenance

### Adding New Rules

1. **Update validator**:
   ```python
   # governance/validators/documentation_validator.py
   def check_new_rule(self):
       """Add new validation rule"""
       # Implementation
   ```

2. **Update git hook**:
   ```bash
   # governance/hooks/pre-commit-documentation
   # Add new check section
   ```

3. **Update Ralph checker**:
   ```python
   # ralph/checkers/documentation_checker.py
   # Add new check method
   ```

4. **Document rule**:
   Update this file (DOCUMENTATION-GOVERNANCE.md)

### Testing Validators

```bash
# Test git hook
git add test-file.md
git commit -m "test"  # Should trigger hook

# Test CLI validator
aibrain validate-docs work/

# Test Ralph checker
python -m ralph.checkers.documentation_checker
```

---

## Troubleshooting

### Hook Not Running

```bash
# Check hook is executable
ls -la .git/hooks/pre-commit

# Make executable
chmod +x .git/hooks/pre-commit

# Verify hook location
cat .git/hooks/pre-commit | head -1
# Should show: #!/bin/bash
```

### False Positives

```bash
# Temporary bypass (emergency only)
git commit --no-verify

# Or fix the violation
# See validation error message for guidance
```

### Validator Errors

```bash
# Check Python version
python3 --version  # Should be 3.9+

# Install dependencies
pip install pyyaml

# Run with verbose output
python3 -v governance/validators/documentation_validator.py --check
```

---

## Related Documents

- [ADR-010](../AI-Team-Plans/decisions/ADR-010-documentation-organization-archival-strategy.md) - Original decision
- [work/README.md](../work/README.md) - Active work directory guide
- [archive/README.md](../archive/README.md) - Archive directory guide
- [CATALOG.md](../CATALOG.md) - Master documentation index
- [DECISIONS.md](../DECISIONS.md) - D-022 migration decision
