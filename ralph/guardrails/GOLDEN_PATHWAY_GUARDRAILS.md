# Golden Pathway Guardrails

**Created**: 2026-01-08
**Source**: CredentialMate golden pathway regression incident
**Purpose**: Prevent infrastructure configuration drift that breaks critical user workflows

---

## Overview

The "Golden Pathway" represents critical end-user workflows that must NEVER break. Infrastructure configuration mismatches (S3 bucket names, environment variables) can break these pathways silently without failing tests.

**Example Golden Pathway**: Document Upload → Classify → Extract → Review

**Root Cause of 2026-01-08 Incident**:
```
LocalStack init script: awslocal s3 mb s3://credmate-documents-local
Application config:     S3_DOCUMENTS_BUCKET=credmate-documents-development

Result: Files uploaded to wrong bucket → DocumentFileMissing errors
```

---

## Guardrail Categories

### 1. **Infrastructure File Protection**

**Trigger**: Modifications to infrastructure files
**Action**: Enforce mandatory validation before commit

**Protected Files**:
- `docker-compose.yml` - Service orchestration
- `docker-compose.prod.yml` - Production orchestration
- `apps/*/.env*` - Environment configuration
- `infra/docker/localstack-init/**` - LocalStack initialization
- `infra/config/service-contracts.yaml` - SSOT for cross-service contracts
- `infra/lambda/template.yaml` - AWS Lambda configuration

**Mandatory Validations**:
1. YAML syntax check: `docker compose config --quiet`
2. Service contracts: `python infra/scripts/validate_service_contracts.py`
3. Pre-flight validation: `python infra/scripts/validate_env_preflight.py`
4. Golden path test: `python infra/scripts/test_golden_path.py --pre-commit`

**Enforcement**:
```python
if file_modified in INFRASTRUCTURE_FILES:
    run_mandatory_validations()
    if any_validation_fails():
        BLOCK_COMMIT()
```

---

### 2. **Forbidden Pattern Detection**

**Trigger**: Dangerous patterns in commit
**Action**: Block commit immediately

**Forbidden Patterns**:

| Pattern | Risk | Action |
|---------|------|--------|
| `--no-verify` | Bypasses all pre-commit hooks | BLOCK |
| `git commit -n` | Bypasses all pre-commit hooks | BLOCK |
| `S3_DOCUMENTS_BUCKET` (in wrong files) | Bucket name contract violation | Require service contract validation |
| `awslocal s3 mb` (without SSOT check) | Bucket creation mismatch | Require service contract validation |
| `SKIP_PREFLIGHT=true` | Emergency bypass | WARN (allow with justification) |

**Implementation**:
```python
FORBIDDEN_PATTERNS = {
    "--no-verify": {"action": "BLOCK", "message": "Never bypass pre-commit hooks"},
    "git commit -n": {"action": "BLOCK", "message": "Never bypass pre-commit hooks"},
}

def check_forbidden_patterns(commit_message, changed_files):
    for pattern, rule in FORBIDDEN_PATTERNS.items():
        if pattern in commit_message or any(pattern in file_content for file in changed_files):
            if rule["action"] == "BLOCK":
                raise GuardrailViolation(rule["message"])
```

---

### 3. **Service Contract Enforcement**

**Trigger**: Changes to files containing service contracts
**Action**: Validate against SSOT

**Contracts Protected**:
- S3 bucket names (local vs production)
- S3 endpoint URLs
- Database connection strings
- Redis connection strings
- AWS regions

**SSOT Location**: `infra/config/service-contracts.yaml`

**Validation Logic**:
```python
def validate_service_contracts():
    """
    Ensures all service contracts match SSOT.

    Checks:
    - .env files match service-contracts.yaml
    - docker-compose.yml env vars match SSOT
    - LocalStack init scripts match SSOT

    Returns:
        bool: True if all contracts valid, False otherwise
    """
    contracts = load_yaml("infra/config/service-contracts.yaml")

    for contract_name, contract_def in contracts.items():
        expected_value = contract_def["local"]  # or "production"

        for file_ref in contract_def["validation"]["must_match"]:
            actual_value = extract_value_from_file(file_ref)

            if actual_value != expected_value:
                report_violation(contract_name, expected_value, actual_value, file_ref)
                return False

    return True
```

---

### 4. **Golden Pathway Regression Prevention**

**Trigger**: Changes to critical pathway files
**Action**: Run end-to-end golden path test

**Critical Files** (upload → review pathway):

| File | Stage | Risk | Test Required |
|------|-------|------|---------------|
| `*/api/v1/documents.py` | Upload | High | Golden path test |
| `*/storage/s3_service.py` | Storage | Critical | Golden path test + contracts |
| `*/document_processing/process_document_task.py` | Processing | High | Golden path test |
| `infra/docker/localstack-init/**` | Infrastructure | Critical | All validations |
| `docker-compose*.yml` | Infrastructure | Critical | All validations |

**Test Stages**:
1. Document upload succeeds
2. File saved to S3
3. Worker retrieves file
4. Document classified
5. Fields extracted
6. Status reaches `review_pending`
7. View endpoint returns file

**Enforcement**:
```python
CRITICAL_PATHWAY_FILES = [
    "*/api/v1/documents.py",
    "*/storage/s3_service.py",
    "*/document_processing/*.py",
    "infra/docker/localstack-init/**",
    "docker-compose*.yml",
]

def check_golden_pathway(changed_files):
    if any(matches_pattern(file, CRITICAL_PATHWAY_FILES) for file in changed_files):
        result = run_test("python infra/scripts/test_golden_path.py --pre-commit")
        if result.exit_code != 0:
            raise GuardrailViolation(
                f"Golden pathway test failed at stage: {result.failed_stage}\n"
                f"Error: {result.error_message}\n"
                f"This change would break the critical user workflow."
            )
```

---

## Integration with Ralph

### Pre-Commit Hook Integration

```python
# ralph/hooks/pre_commit.py

def run_pre_commit_checks(changed_files, commit_message):
    """
    Runs before git commit completes.
    Returns True to allow commit, False to block.
    """

    # Check 1: Forbidden patterns
    if has_forbidden_patterns(commit_message, changed_files):
        print("❌ BLOCKED: Forbidden pattern detected")
        return False

    # Check 2: Infrastructure file validations
    if touches_infrastructure_files(changed_files):
        if not run_infrastructure_validations():
            print("❌ BLOCKED: Infrastructure validation failed")
            return False

    # Check 3: Service contract validation
    if touches_contract_files(changed_files):
        if not validate_service_contracts():
            print("❌ BLOCKED: Service contract violation")
            return False

    # Check 4: Golden pathway test
    if touches_critical_pathway_files(changed_files):
        if not run_golden_path_test():
            print("❌ BLOCKED: Golden pathway regression detected")
            return False

    return True
```

---

## Guardrail Bypass Procedures

### Emergency Override

**When to Use**: Critical hotfix required, validations temporarily broken

**How to Override**:
```bash
# Set emergency bypass flag
export SKIP_PREFLIGHT=true
git commit -m "Emergency fix: [justification]"

# IMPORTANT: Create follow-up ticket immediately
# IMPORTANT: Remove bypass as soon as possible
```

**Requirements**:
1. Must document justification in commit message
2. Must create follow-up ticket to fix validations
3. Must notify team in Slack (#infra-alerts)
4. Bypass automatically expires after 1 commit

### Temporary Disable

**When to Use**: Working on validation scripts themselves

**How to Disable**:
```bash
# Disable specific validation
export SKIP_CONTRACT_VALIDATION=true

# Or disable golden path test only
export SKIP_GOLDEN_PATH_TEST=true
```

**NEVER Disable**:
- Forbidden pattern detection (always enforced)
- YAML syntax validation (prevents Docker failures)

---

## Metrics & Monitoring

### Tracked Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `contract_violations_caught` | Service contract mismatches blocked | > 0 per week |
| `golden_path_regressions_prevented` | Commits blocked by golden path test | > 0 per week |
| `forbidden_patterns_detected` | `--no-verify` usage attempts | > 0 ever |
| `infrastructure_changes` | Infrastructure files modified | > 5 per week |

### Alert Configuration

```yaml
# ralph/alerts/golden-pathway.yaml

alerts:
  - name: "golden_pathway_regression"
    trigger: "golden_path_test_failed"
    severity: "P0"
    channels: ["slack:#incidents", "github:issue"]
    message: "Golden pathway BROKEN - critical user workflow blocked"

  - name: "service_contract_violation"
    trigger: "contract_validation_failed"
    severity: "P1"
    channels: ["slack:#infra-alerts"]
    message: "Service contract violation detected - potential configuration drift"

  - name: "forbidden_pattern_usage"
    trigger: "bypass_attempt_detected"
    severity: "P1"
    channels: ["slack:#infra-alerts", "audit-log"]
    message: "Attempt to bypass pre-commit hooks detected"
```

---

## Recovery Procedures

### If Golden Pathway Breaks in Production

**Symptoms**:
- Documents stuck at `status="uploaded"`
- `processing_errors: "DocumentFileMissing"`
- Worker logs: "S3 object missing"

**Recovery Steps**:
1. **Identify breaking commit**:
   ```bash
   git log --oneline -20
   git diff HEAD~10 -- infra/docker/localstack-init/
   git diff HEAD~10 -- docker-compose.yml
   ```

2. **Revert immediately**:
   ```bash
   git revert <breaking-commit-sha>
   git push origin main
   ```

3. **Diagnose root cause**:
   ```bash
   python infra/scripts/validate_service_contracts.py --verbose
   python infra/scripts/validate_env_preflight.py
   ```

4. **Fix and re-deploy**:
   - Update incorrect configuration to match SSOT
   - Run all validations
   - Test golden pathway
   - Re-apply changes

5. **Document incident**:
   - Create session reflection in `sessions/YYYY-MM-DD-incident-name.md`
   - Update guardrails if needed
   - Share learnings with team

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-08 | Initial golden pathway guardrails created from CredentialMate incident |

---

## Related Documents

- [Service Contracts SSOT](../../infra/config/service-contracts.yaml) (if exists in target project)
- [Infra Team Contract](../../governance/contracts/infra-team.yaml)
- [Session Reflection: Golden Pathway Fix](../../sessions/2026-01-08-golden-pathway-fix-session.md) (CredentialMate)
- [Ralph Guardrails Patterns](./patterns.py)
