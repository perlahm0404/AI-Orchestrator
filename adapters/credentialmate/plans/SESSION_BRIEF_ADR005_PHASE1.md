# Session Initiation Brief: ADR-005 Phase 1 - Business Logic Consolidation

**Project**: CredentialMate
**ADR**: ADR-005 - Business Logic Consolidation
**Phase**: 1 of 3 (Week 1 - Stop the Bleeding)
**Status**: Approved by tmac on 2026-01-10
**Duration**: 1 week (7 days)
**Budget**: $7,000
**Priority**: P0 (CRITICAL - HIPAA compliance)

---

## Executive Summary

You are tasked with executing **Phase 1 of ADR-005**: eliminating business logic divergence between 19 ad hoc Python scripts and the production backend API that caused 3 critical HIPAA compliance bugs in CredentialMate's CME calculation system.

**What Happened**: Investigation of CME bugs (CME-BUG-001, CME-BUG-002, CME-BUG-003) revealed that ad hoc scripts contained correct business logic while the backend API had incomplete/incorrect logic. This systemic pattern affects 19 scripts and presents CRITICAL risk to healthcare provider licensing data.

**What's Approved**: Full remediation plan (Phases 1-3, 12 weeks, $127K) with 5.9x ROI ($750K annual bug cost prevented).

**Your Mission (Phase 1)**: Stop the bleeding by eliminating code duplication, adding integration tests, and documenting enforcement policies.

---

## Critical Context

### The Problem

| Metric | Value |
|--------|-------|
| **Ad hoc scripts audited** | 19 scripts |
| **Critical bugs discovered** | 3 (CME-BUG-001, 002, 003) |
| **Bug discovery rate** | 3 bugs/week |
| **Extrapolated annual cost** | $750K |
| **HIPAA severity** | CRITICAL (provider licensing data) |
| **Root cause** | Business logic duplicated across scripts, backend, DB, YAML |

### Bugs Fixed (Background Context)

These bugs were ALREADY FIXED in backend API during investigation:

| Bug ID | Description | Severity | Impact |
|--------|-------------|----------|--------|
| CME-BUG-001 | Topic consolidation groups not used | CRITICAL | False gaps (3h domestic violence shown as 0h) |
| CME-BUG-002 | Category 1 not checking credit_type field | CRITICAL | 51h Category 1 shown as 0h |
| CME-BUG-003 | Conditional requirements showing for all providers | CRITICAL | Pain clinic requirements shown to non-pain-clinic doctors |

**Current State**: Backend API is NOW correct (bugs fixed), but ad hoc scripts STILL contain duplicate logic that could diverge again.

---

## Phase 1 Objectives

**Goal**: Prevent new divergence, eliminate existing duplicates

### Success Criteria

- ✅ All 19 ad hoc scripts audited and categorized
- ✅ Zero code duplication for business logic (imports only)
- ✅ Integration tests pass (ad hoc output == API output)
- ✅ Policy documented and enforceable via pre-commit hooks
- ✅ Tracking matrix created: script → backend service → status

---

## Phase 1 Tasks (4 Tasks, 7 Days)

### Task 1: Audit Remaining Scripts (1 day)

**Objective**: Complete analysis of all 19 identified scripts

**Deliverables**:
1. **Tracking matrix** (`adapters/credentialmate/plans/ADHOC_SCRIPT_AUDIT.md`):
   ```markdown
   | Script | Business Logic | Backend Equivalent | Status | Risk |
   |--------|----------------|-------------------|--------|------|
   | generate_cme_v4.py | Topic consolidation, Category 1, conditional filtering | CMEComplianceService | ✅ FIXED | LOW (logic now in backend) |
   | generate_cme_action_plan.py | Same as v4 | CMEComplianceService | ⚠️ DUPLICATE | HIGH (needs refactor) |
   | scripts/urgent_cme_gaps.py | Gap calculation, deadline priority | CMEComplianceService | ❓ UNKNOWN | MEDIUM (needs audit) |
   | ... | ... | ... | ... | ... |
   ```

2. **Business Logic Inventory** (extract from each script):
   - Constants duplicated (TOPIC_CONSOLIDATION_GROUPS, conditional keywords, etc.)
   - SQL queries that duplicate service layer logic
   - Calculation algorithms that exist in backend

3. **Categorization**:
   - **High Risk**: Contains business logic that could diverge
   - **Medium Risk**: Data transformation/validation logic
   - **Low Risk**: Infrastructure only (seed scripts, backfill)

**Starting Point**: Investigation report already identified 19 scripts (see TECH-DEBT-001-adhoc-logic-divergence-remediation.md lines 60-93)

**Files to Create**:
- `adapters/credentialmate/plans/ADHOC_SCRIPT_AUDIT.md`

**Tools**:
- Read all 19 scripts
- Extract constants, SQL queries, calculation logic
- Compare against backend service (`apps/backend-api/src/core/services/cme_compliance_service.py`)

---

### Task 2: Eliminate Code Duplication (2 days)

**Objective**: Remove all duplicate business logic constants, import from backend instead

**Known Duplicates** (from bug investigation):

1. **TOPIC_CONSOLIDATION_GROUPS** (CRITICAL)
   - **Current state**: Defined in BOTH:
     - `apps/backend-api/src/contexts/cme/constants.py` (lines 571-667)
     - `generate_cme_v4.py` (local copy)
   - **Action**: Remove from scripts, import from constants
   - **Test**: Verify script still works after import

2. **Conditional Keywords** (CRITICAL)
   ```python
   # Duplicate in multiple scripts:
   conditional_keywords = [
       'only if', 'pain management clinic', 'pain clinic owner',
       'physician owner', 'owner/operator', ...
   ]
   ```
   - **Action**: Move to `contexts/cme/constants.py`, import everywhere
   - **Test**: Verify conditional filtering still works

3. **Category 1 Detection Logic** (CRITICAL)
   ```python
   # Duplicate in scripts:
   if topic == 'category_1' and activity.credit_type:
       credit_type_upper = activity.credit_type.upper()
       if any(keyword in credit_type_upper for keyword in ['AMA', 'AOA', 'CATEGORY 1']):
           # ... logic
   ```
   - **Action**: Create `CMEComplianceService.is_category_1(activity)` method
   - **Action**: Scripts call service method instead of duplicating logic

**Deliverables**:
1. **PR**: "refactor: Consolidate CME business logic imports"
   - Remove duplicate constants from all scripts
   - Import from `contexts/cme/constants.py`
   - Create helper methods in `CMEComplianceService` for shared logic

2. **Verification**:
   - Run each script before/after refactor
   - Compare outputs (should be identical)

**Files to Modify**:
- `generate_cme_v4.py`
- `generate_cme_action_plan.py`
- `scripts/urgent_cme_gaps.py`
- `scripts/check_cme_details.py`
- Any others identified in Task 1 audit

**Files to Update**:
- `apps/backend-api/src/contexts/cme/constants.py` (add CONDITIONAL_KEYWORDS)
- `apps/backend-api/src/core/services/cme_compliance_service.py` (add is_category_1() helper)

---

### Task 3: Add Integration Tests (2 days)

**Objective**: Create tests that ensure ad hoc script output matches backend API output

**Test Pattern**:
```python
# tests/integration/test_adhoc_parity.py

def test_generate_cme_v4_matches_backend_api():
    """
    Ensure ad hoc script output matches backend API for same input.

    This test PREVENTS future divergence by catching logic differences.
    """
    provider_email = "real300@test.com"

    # Run ad hoc script
    adhoc_output = run_adhoc_script(
        script_path="/Users/tmac/1_REPOS/credentialmate/generate_cme_v4.py",
        args=["--email", provider_email]
    )

    # Query backend API
    provider = get_provider_by_email(provider_email)
    api_output = cme_compliance_service.calculate_compliance(
        provider_id=provider.id,
        state="FL",
        license_type="MD",
        cycle_start=date(2024, 1, 31),
        cycle_end=date(2026, 1, 31)
    )

    # Assert parity
    assert adhoc_output["gaps"] == api_output["gaps"], \
        "Ad hoc script gaps must match backend API gaps"
    assert adhoc_output["total_earned"] == api_output["total_earned"], \
        "Ad hoc script total credits must match backend API"
    assert adhoc_output["category_1_earned"] == api_output.get("category_1_earned"), \
        "Category 1 credits must match"
```

**Test Coverage Required**:

1. `test_generate_cme_v4_matches_backend_api()` - Florida cycle
2. `test_generate_cme_v4_matches_backend_api_ohio()` - Ohio cycle
3. `test_generate_cme_v4_matches_backend_api_missouri()` - Missouri cycle
4. `test_topic_consolidation_parity()` - Topic consolidation groups work identically
5. `test_category_1_detection_parity()` - Category 1 detection matches
6. `test_conditional_filtering_parity()` - Conditional requirements filtered identically

**Test Data**: Use existing test provider `real300@test.com` (Dr. Sehgal) with known CME activities.

**Deliverables**:
- `tests/integration/test_adhoc_parity.py` (new file, 6 tests minimum)
- All tests PASS (green)
- CI integration (tests run on every PR)

**Success Metric**: 100% parity (ad hoc == API for all test cases)

---

### Task 4: Document "Do Not Duplicate" Policy (1 day)

**Objective**: Create enforceable policy preventing future business logic duplication

**Deliverables**:

1. **CONTRIBUTING.md Update** (`/Users/tmac/1_REPOS/credentialmate/CONTRIBUTING.md`):
   ```markdown
   ## Business Logic Policy (ADR-005)

   **RULE**: No business logic in ad hoc scripts.

   ### What is Business Logic?
   - Constants that define CME rules (topics, consolidation groups, keywords)
   - Calculation algorithms (gap calculation, credit matching)
   - Conditional logic (requirement filtering, topic matching)
   - Data validation rules

   ### What's Allowed in Ad Hoc Scripts?
   - Database queries (read-only)
   - Excel/PDF formatting (presentation layer)
   - Imports from backend services
   - Data transformation for reporting

   ### Enforcement
   - **Pre-commit hook**: Detects duplicate constants
   - **Integration tests**: Assert ad hoc output == API output
   - **Code review**: Reviewer checks for business logic in ad hoc scripts
   - **CI**: Fails if ad hoc parity tests fail

   ### How to Add New Business Logic
   1. Add to backend service FIRST (`apps/backend-api/src/core/services/`)
   2. Write unit tests for backend service
   3. Import from backend in ad hoc scripts (do NOT duplicate)
   4. Add integration test to verify parity

   ### Rationale
   See ADR-005 for full context. TL;DR: Duplicate business logic caused 3 critical
   HIPAA compliance bugs (CME-BUG-001, 002, 003) in 1 week. Backend is SSOT.
   ```

2. **Pre-commit Hook** (`.pre-commit-config.yaml` or `scripts/pre-commit-hook.sh`):
   ```bash
   #!/bin/bash
   # Pre-commit hook: Detect duplicate business logic in ad hoc scripts

   DUPLICATES_FOUND=0

   # Check for TOPIC_CONSOLIDATION_GROUPS in ad hoc scripts
   if git diff --cached --name-only | grep -E "^(generate_|scripts/).*\.py$"; then
       for file in $(git diff --cached --name-only | grep -E "^(generate_|scripts/).*\.py$"); do
           if grep -q "TOPIC_CONSOLIDATION_GROUPS.*=" "$file"; then
               echo "ERROR: $file contains duplicate TOPIC_CONSOLIDATION_GROUPS"
               echo "  Import from contexts.cme.constants instead"
               DUPLICATES_FOUND=1
           fi

           if grep -q "conditional_keywords.*=.*\[" "$file"; then
               echo "ERROR: $file contains duplicate conditional_keywords"
               echo "  Import CONDITIONAL_KEYWORDS from contexts.cme.constants instead"
               DUPLICATES_FOUND=1
           fi
       done
   fi

   if [ $DUPLICATES_FOUND -eq 1 ]; then
       echo ""
       echo "❌ Pre-commit hook FAILED: Business logic duplication detected"
       echo "   See CONTRIBUTING.md for policy (ADR-005)"
       exit 1
   fi

   echo "✅ Pre-commit hook PASSED: No business logic duplication"
   exit 0
   ```

3. **Update ADR-005** (if needed):
   - Add "Enforcement Mechanisms" section documenting hook, tests, policy

**Deliverables**:
- Updated `CONTRIBUTING.md`
- Pre-commit hook script
- Hook enabled and tested (try to commit duplicate constant → blocked)

---

## Reference Documents

### Primary References

1. **ADR-005**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/decisions/ADR-005-business-logic-consolidation.md`
   - Full architectural decision with all 3 phases
   - Approved by tmac on 2026-01-10
   - Status: ✅ approved, Option A, All phases

2. **TECH-DEBT-001**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/TECH-DEBT-001-adhoc-logic-divergence-remediation.md`
   - Detailed remediation plan
   - 19 scripts inventory (lines 60-93)
   - Phase breakdowns

3. **Work Queue**: `/Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_credentialmate.json`
   - Entry ADHOC-CME-20260110-008 documents bug investigation
   - Shows 3 bugs fixed in backend

### Code References

**Backend Service** (canonical source):
- `/Users/tmac/1_REPOS/credentialmate/apps/backend-api/src/core/services/cme_compliance_service.py`
  - `calculate_compliance()` method (main entry point)
  - `_topic_matches_requirement()` (lines 81-89, CME-BUG-001 fix)
  - `_calculate_completed_hours_for_topic()` (lines 782-788, CME-BUG-002 fix)
  - `get_topic_specific_requirements()` (lines 656-670, CME-BUG-003 fix)

**Constants** (canonical source):
- `/Users/tmac/1_REPOS/credentialmate/apps/backend-api/src/contexts/cme/constants.py`
  - `TOPIC_CONSOLIDATION_GROUPS` (lines 571-667)
  - `TOPIC_TO_GROUP` (reverse mapping)

**Ad Hoc Scripts** (to refactor):
- `/Users/tmac/1_REPOS/credentialmate/generate_cme_v4.py` - HIGH RISK (duplicate logic)
- `/Users/tmac/1_REPOS/credentialmate/generate_cme_action_plan.py` - HIGH RISK (duplicate)
- `/Users/tmac/1_REPOS/credentialmate/scripts/urgent_cme_gaps.py` - MEDIUM RISK (unknown)
- See TECH-DEBT-001 lines 60-93 for full list

---

## Work Queue Integration

**After Phase 1 completion**, update work queue:

```json
{
  "id": "ADHOC-PHASE1-20260110-001",
  "description": "ADR-005 Phase 1: Business logic consolidation - Stop the bleeding",
  "file": "adapters/credentialmate/plans/decisions/ADR-005-business-logic-consolidation.md",
  "status": "complete",
  "type": "technical_debt_remediation",
  "agent": "manual",
  "priority": 0,
  "source": "ADR-005",
  "completed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "time_spent_hours": 40,
  "deliverables": [
    "adapters/credentialmate/plans/ADHOC_SCRIPT_AUDIT.md (tracking matrix)",
    "tests/integration/test_adhoc_parity.py (6 integration tests)",
    "CONTRIBUTING.md (updated with policy)",
    "scripts/pre-commit-hook.sh (duplicate detection)",
    "PR: refactor - Consolidate CME business logic imports"
  ],
  "success_criteria": [
    "✅ All 19 scripts audited",
    "✅ Zero code duplication",
    "✅ Integration tests pass (100% parity)",
    "✅ Pre-commit hook enforces policy"
  ]
}
```

---

## Starting the Session

### Quick Start Commands

```bash
# 1. Navigate to credentialmate repository
cd /Users/tmac/1_REPOS/credentialmate

# 2. Create tracking document
touch /Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/ADHOC_SCRIPT_AUDIT.md

# 3. Start with Task 1: Audit scripts
# Read the 19 scripts identified in TECH-DEBT-001

# 4. Document findings in tracking matrix

# 5. Move to Task 2: Eliminate duplicates
# (After Task 1 completes)

# 6. Move to Task 3: Integration tests
# Create tests/integration/test_adhoc_parity.py

# 7. Move to Task 4: Document policy
# Update CONTRIBUTING.md, create pre-commit hook
```

### Environment Context

**Repository Paths**:
- AI Orchestrator: `/Users/tmac/1_REPOS/AI_Orchestrator`
- CredentialMate: `/Users/tmac/1_REPOS/credentialmate`

**Database**: Local dev (credmate_dev @ localhost:5432)

**Python Environment**: Use Docker (project runs in containers)

---

## Risk Mitigation

### Risks During Phase 1

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Script breaks after refactor | MEDIUM | HIGH | Run script before/after, compare outputs byte-for-byte |
| Integration tests flaky | MEDIUM | MEDIUM | Use fixed test data (real300@test.com), deterministic |
| Pre-commit hook false positives | LOW | MEDIUM | Test hook with edge cases, allow imports |
| Missed duplicate constants | MEDIUM | HIGH | Thorough audit (grep for patterns), code review |

### Rollback Plan

If Phase 1 introduces issues:
1. **Immediate**: Revert commits (keep originals in `scripts/legacy/`)
2. **Validate**: Run integration tests to confirm rollback worked
3. **Investigate**: Review what went wrong, update approach
4. **Retry**: Fix issue, re-attempt with updated strategy

---

## Success Metrics (Phase 1 Exit Criteria)

**Quantitative**:
- ✅ 19 scripts audited (100% coverage)
- ✅ 0 duplicate constants (imports only)
- ✅ 6+ integration tests created
- ✅ 100% test pass rate (ad hoc == API)
- ✅ Pre-commit hook blocks 100% of duplicate attempts (test with deliberate violation)

**Qualitative**:
- ✅ Tracking matrix complete and accurate
- ✅ Policy clearly documented in CONTRIBUTING.md
- ✅ Pre-commit hook enabled and tested
- ✅ Code review checklist updated with ADR-005 requirements

**Financial**:
- ✅ Phase 1 complete within $7K budget (~40 hours)
- ✅ Zero new bugs introduced (verified by integration tests)

---

## What Comes Next

**After Phase 1 completes**:

1. **Session handoff**: Document Phase 1 completion, blockers, learnings
2. **Phase 2 kickoff**: Initiate Phase 2 (Weeks 2-6) - Refactor scripts to call backend API
3. **Work queue update**: Mark Phase 1 complete, create Phase 2 tasks

**Phase 2 Preview** (Weeks 2-6, $30K):
- Refactor high-risk scripts to call `CMEComplianceService` API
- Create shared CME calculator library
- Deprecate duplicate scripts (19 → 10 reduction)
- Add monitoring for divergence detection

---

## Questions for Session Agent

Before starting Phase 1, confirm:

1. **Access**: Can you read files in both repositories?
   - `/Users/tmac/1_REPOS/AI_Orchestrator`
   - `/Users/tmac/1_REPOS/credentialmate`

2. **Permissions**: Can you create/modify files in credentialmate?

3. **Docker**: Can you run scripts inside Docker containers? (Needed to test ad hoc scripts)

4. **Testing**: Can you run pytest in credentialmate backend environment?

5. **Git**: Can you create commits and PRs?

---

## Summary

**Your Mission**: Execute ADR-005 Phase 1 to eliminate business logic duplication between 19 ad hoc scripts and backend API, preventing future HIPAA compliance bugs.

**Timeline**: 1 week (7 days)
**Budget**: $7K (~40 hours)
**Priority**: P0 (CRITICAL)

**Tasks**:
1. Audit 19 scripts (1 day)
2. Eliminate duplicates (2 days)
3. Add integration tests (2 days)
4. Document policy (1 day)
+ 1 day buffer for testing/validation

**Success**: Zero duplicate logic, 100% test parity, enforced policy, documented tracking matrix.

**Go/No-Go**: You are CLEARED to begin Phase 1 execution immediately.

---

**Session Start Prompt**:

"I am executing ADR-005 Phase 1 for CredentialMate. I have read the session brief at `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/SESSION_BRIEF_ADR005_PHASE1.md`. I will start with Task 1: Audit 19 ad hoc scripts and create tracking matrix. Proceeding now."
