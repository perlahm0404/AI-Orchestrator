# CME Data Validator - Usage Guide

**Domain-Specific Agent for CredentialMate**

## Overview

The CME Data Validator is a specialized agent that validates CME (Continuing Medical Education) data integrity and business rule compliance for CredentialMate.

**Purpose**: Prevent regressions in CME credit calculations, certification overlays, and gap calculations that could cause compliance failures for healthcare providers.

## What It Validates

| Check | Severity | Description |
|-------|----------|-------------|
| **CME Cycles Linked** | Critical | Ensures all CME activities have non-NULL `cme_cycle_id` |
| **Gap Calculation Parity** | Critical | Ensures `/check` and `/harmonize` endpoints return consistent gaps |
| **Certification Overlays** | Critical | Ensures certification overlays (e.g., ANCC +10h) are applied correctly |
| **Category 1 Accuracy** | Warning | Ensures Category 1 CME credits are counted correctly |
| **Topic Matching** | Warning | Ensures topics are correctly categorized (overlapping vs additive) |

## When to Run

- **Schema changes**: After alembic migrations touching `cme_*` tables
- **Business rule updates**: When state/certification requirements change
- **Pre-deployment**: Before every CredentialMate deployment
- **Manual validation**: On-demand via CLI
- **Scheduled**: Weekly automated validation (cron)

## Usage

### CLI (Manual Validation)

```bash
# Run full CME validation
python -m agents.domain.cme_data_validator /Users/tmac/1_REPOS/credentialmate

# Example output:
================================================================================
CME Data Validation Results
================================================================================

Total Checks: 5
Passed: 4
Failed: 1
Warnings: 0
Pass Rate: 80.0%

❌ Critical Failures:

  certification_overlays:
    Message: Found 2 CA NP+ANCC providers with incorrect requirements (should be 40h)
    Affected: providers:['123', '456']
    Fix: Update CME calculator to add ANCC overlay: total = base_hours + certification_hours
```

### Python API

```python
from agents.domain.cme_data_validator import CMEDataValidator

validator = CMEDataValidator(project_path="/path/to/credentialmate")
results = validator.validate_all()

if results.has_failures:
    print(f"❌ {len(results.failures)} critical failures")
    for failure in results.failures:
        print(f"  {failure.check_name}: {failure.message}")
else:
    print(f"✅ All checks passed ({results.pass_rate:.1f}%)")
```

### CI/CD Integration

Add to your `.github/workflows/deploy.yml`:

```yaml
- name: Run CME Validation
  run: |
    python -m agents.domain.cme_data_validator /app/credentialmate
  env:
    DOCKER_CONTAINER: credmate-backend-dev
```

## Validation Checks Explained

### 1. CME Cycles Linked

**Rule**: Every `cme_activity` must have a non-NULL `cme_cycle_id`

**Why**: Orphaned CME activities don't count toward compliance, causing providers to appear non-compliant when they actually are.

**Fix**:
```sql
UPDATE cme_activities
SET cme_cycle_id = <appropriate_cycle_id>
WHERE cme_cycle_id IS NULL;
```

### 2. Gap Calculation Parity

**Rule**: `/check` endpoint gap === `/harmonize` endpoint gap (within 0.01h)

**Why**: Inconsistent gap calculations cause user confusion and trust erosion (EVIDENCE-002).

**Validation**: Runs `test_cme_parity.py` integration test

**Fix**: Review gap calculation logic to ensure both endpoints use the same method.

### 3. Certification Overlays

**Rule**: CA NP + ANCC = 30 (base) + 10 (ANCC) = 40 hours

**Why**: Missing certification overlays cause providers to under-comply with CME requirements (EVIDENCE-001).

**Fix**: Update CME calculator to add certification-specific hours:
```python
total_cme = state_base_hours + sum(certification_overlay_hours)
```

### 4. Category 1 Accuracy

**Rule**: Category 1 credit counts must match actual Category 1 hours completed

**Why**: Incorrect category counting causes compliance failures.

**Fix**: Recalculate Category 1 hours for affected providers.

### 5. Topic Matching

**Rule**: Topics must be correctly categorized as overlapping vs additive

**Why**: Incorrect topic matching causes gap calculation errors.

**Validation**: Runs `test_topic_normalization.py` unit test

**Fix**: Review topic normalization logic.

## Autonomy Level: L1 (Stricter)

The CME validator operates under **L1 autonomy** due to HIPAA compliance requirements:

**Allowed**:
- ✅ Read CME models, services, and endpoints
- ✅ Execute read-only database queries
- ✅ Run CME unit/integration tests
- ✅ Generate validation reports

**Forbidden**:
- ❌ Modify production database
- ❌ Execute UPDATE/DELETE queries
- ❌ Modify alembic migrations
- ❌ Deploy code
- ❌ Access PHI (patient health information)

## Exit Codes

- `0`: All critical checks passed
- `1`: One or more critical failures detected

## Integration with Work Queue

When critical failures are detected, the validator can automatically create tasks:

```python
if results.has_failures:
    # Auto-create work queue task
    task = {
        "id": "CME-VALIDATION-FAILURE-001",
        "description": f"Fix CME validation failure: {failure.check_name}",
        "priority": "P0",
        "agent": "bugfix",
        "suggested_fix": failure.suggested_fix
    }
```

## Evidence-Based Validation

The validator's checks are based on real user-reported bugs:

- **EVIDENCE-001**: CA NP CME tracking (certification overlays)
- **EVIDENCE-002**: CME gap calculation contradictions (parity)

This ensures the validator catches real-world issues that affect users.

## Limitations

**Current limitations**:
- Database queries are mocked (need real Docker integration)
- Pytest execution is simplified (need subprocess integration)
- No automatic GitHub issue creation (future enhancement)

**Roadmap**:
- [ ] Real database query execution via Docker
- [ ] Live pytest execution with detailed results
- [ ] Auto-create GitHub issues for critical failures
- [ ] Weekly summary reports
- [ ] Historical trend analysis

## Support

For issues or questions about the CME validator:
- File GitHub issue with tag `cme-validator`
- Slack: `#credentialmate-compliance`
- Owner: @tmac

## Related Documentation

- [EVIDENCE-001: CA NP CME Tracking](../../evidence/EVIDENCE-001-ca-np-cme-tracking.md)
- [EVIDENCE-002: CME Gap Calculation Contradictions](../../evidence/EVIDENCE-002-cme-gap-calculation-contradictions.md)
- [CME Validator Contract](../../governance/contracts/cme-validator.yaml)
- [CME Validator Tests](../../tests/agents/test_cme_validator.py)
