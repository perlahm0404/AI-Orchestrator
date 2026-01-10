# TECH-DEBT-001: Ad Hoc Script Business Logic Divergence - Remediation Plan

**Date**: 2026-01-10
**Status**: Active
**Priority**: P0 (Critical Technical Debt)
**Severity**: HIGH
**Risk**: HIPAA compliance, data accuracy, provider trust

---

## Executive Summary

Investigation confirmed a systemic pattern where ad hoc scripts contain correct business logic that the production backend API either lacks or implements differently. This creates:
- **Data integrity risk**: Different outputs from scripts vs. API for same input
- **Compliance risk**: CME calculations affect medical provider licensing (HIPAA-relevant)
- **Technical debt**: Code duplication across 19+ ad hoc scripts
- **Maintenance burden**: Business logic changes must be synchronized across multiple codebases

**Impact**: 3 critical bugs (CME-BUG-001, CME-BUG-002, CME-BUG-003) were discovered when ad hoc report showed correct data while UI showed incorrect data.

**Root Cause**: Knowledge isolation + No canonical source of truth + No enforcement of single code path

---

## Problem Statement

### What Happened

1. **Ad hoc script developed** (`generate_cme_v4.py`) with correct CME calculation logic
2. **Backend API existed** (`cme_compliance_service.py`) with INCOMPLETE logic
3. **User requested report** - ad hoc script showed correct CME gaps
4. **UI showed different data** - backend API missing 3 critical rules:
   - Topic consolidation groups (child_abuse → domestic_violence)
   - Category 1 credit_type checking (credit_type field vs topics array)
   - Conditional requirement filtering (pain clinic owners only)
5. **Investigation revealed** ad hoc script had logic backend was missing
6. **Emergency fix** - logic reverse-ported from ad hoc script to backend

### Why This is Systemic

**19 ad hoc scripts found** containing business logic:
- 7 CME-focused scripts with calculation logic
- 12 other scripts with data validation, transformation, or analysis logic
- Pattern: Scripts evolve independently from backend services
- No mechanism to keep them synchronized

### Risk Assessment

| Impact Area | Risk Level | Consequence |
|-------------|------------|-------------|
| Data Accuracy | **CRITICAL** | Providers receive incorrect compliance status |
| HIPAA Compliance | **HIGH** | Healthcare provider data must be accurate |
| Financial Impact | **MEDIUM** | Providers may pay for unnecessary CME courses |
| Legal Exposure | **MEDIUM** | Inaccurate licensing status could affect practice |
| Technical Debt | **HIGH** | Code duplication across 19+ scripts |

---

## Current State Analysis

### Ad Hoc Scripts Inventory

**High-Risk Scripts (contain business logic):**

1. `/Users/tmac/1_REPOS/credentialmate/generate_cme_v4.py`
   - **Logic**: Topic consolidation, Category 1 checking, conditional filtering
   - **Backend equivalent**: `cme_compliance_service.py`
   - **Status**: Logic NOW in backend (reverse-ported)
   - **Action needed**: Remove duplicates, import from backend

2. `/Users/tmac/1_REPOS/credentialmate/generate_cme_action_plan.py`
   - **Logic**: Same as generate_cme_v4.py
   - **Status**: Duplicate logic
   - **Action needed**: Deprecate or refactor to call backend API

3. `/Users/tmac/1_REPOS/credentialmate/scripts/urgent_cme_gaps.py`
   - **Logic**: Gap calculation, deadline prioritization
   - **Status**: Unknown if matches backend
   - **Action needed**: Audit and compare

4. `/Users/tmac/1_REPOS/credentialmate/scripts/check_cme_details.py`
   - **Logic**: Category 1 detection
   - **Status**: Unknown if matches backend
   - **Action needed**: Audit and compare

**Medium-Risk Scripts (data transformation):**
- `scripts/debug_cme_manual.py` (read-only inspection)
- `scripts/audit_cme_rules_comprehensive.py` (YAML↔JSON comparison)
- `scripts/verify_cme_counts.py` (counting only)

**Low-Risk Scripts (infrastructure):**
- Seed scripts, backfill scripts in `/apps/backend-api/scripts/`

### Backend Service Coverage

**CMEComplianceService Status:**

| Business Rule | Backend Status | Ad Hoc Status | Synchronized? |
|---------------|----------------|---------------|---------------|
| Topic consolidation | ✅ Implemented | ✅ Implemented | ✅ YES (after CME-BUG-001 fix) |
| Category 1 credit_type | ✅ Implemented | ✅ Implemented | ✅ YES (after CME-BUG-002 fix) |
| Conditional filtering | ✅ Implemented | ✅ Implemented | ✅ YES (after CME-BUG-003 fix) |
| Topic aliases | ✅ Implemented | ❌ Missing | ⚠️ Backend more complete |
| DEA/CDS filtering | ✅ Implemented | ❌ Hardcoded | ⚠️ Backend more flexible |
| One-time requirements | ✅ Implemented | ❌ Missing | ⚠️ Backend more complete |

**Conclusion**: Backend service is NOW the most complete implementation, but ad hoc scripts still duplicate logic.

---

## Remediation Plan

### Phase 1: Immediate (Next 7 Days) - Stop the Bleeding

**Goal**: Prevent new divergence, eliminate duplicates

**Tasks:**

1. **Audit Remaining Ad Hoc Scripts** (1 day)
   - Complete scan of all 19 identified scripts
   - Extract business logic from each
   - Compare against backend equivalents
   - Create tracking matrix (script → backend service → status)

2. **Eliminate Code Duplication** (2 days)
   - `TOPIC_CONSOLIDATION_GROUPS`: Remove from all ad hoc scripts, import from `contexts/cme/constants.py`
   - Conditional keywords: Remove from scripts, import from backend constants
   - Category 1 logic: Remove from scripts, call backend service method
   - **Deliverable**: PR with consolidated imports

3. **Add Integration Tests** (2 days)
   - Test: `generate_cme_v4.py` output matches `CMEComplianceService.calculate_compliance()` output
   - Test: For same provider/state, API returns same gaps as Excel report
   - Test: Topic consolidation works identically in both
   - **Deliverable**: New test suite `tests/integration/test_adhoc_parity.py`

4. **Document "Do Not Duplicate" Policy** (1 day)
   - Update `CONTRIBUTING.md` with rule: "No business logic in ad hoc scripts"
   - Add pre-commit hook to detect duplicate constants
   - **Deliverable**: Updated docs + hook

**Success Criteria:**
- ✅ All ad hoc scripts audited and categorized
- ✅ Zero code duplication for topic consolidation, conditional keywords, Category 1 logic
- ✅ Integration tests pass (ad hoc output == backend output)
- ✅ Policy documented and enforceable

---

### Phase 2: Refactoring (Next 30 Days) - Establish Single Source of Truth

**Goal**: Make backend service the canonical implementation

**Tasks:**

1. **Refactor High-Risk Ad Hoc Scripts** (10 days)
   - Convert `generate_cme_v4.py` to call `CMEComplianceService` API
   - Convert `generate_cme_action_plan.py` to call `CMEComplianceService` API
   - Remove all SQL queries from scripts - use service layer instead
   - **Pattern**: Script becomes "presentation layer" (Excel formatting only)
   - **Deliverable**: Refactored scripts that call backend services

2. **Create Shared CME Calculation Library** (5 days)
   - Extract common logic from backend service into `shared/cme_calculator.py`
   - Backend API uses it
   - Ad hoc scripts use it
   - CLI tools use it
   - **Deliverable**: New shared library + migration plan

3. **Add API-First Development Workflow** (5 days)
   - Rule: New CME features must be added to backend service FIRST
   - Scripts are consumers, not producers, of business logic
   - Document workflow in `docs/development/api-first-workflow.md`
   - **Deliverable**: Updated workflow docs

4. **Deprecate Duplicate Scripts** (5 days)
   - Mark `generate_cme_action_plan.py` as deprecated (use v4 instead)
   - Consolidate `urgent_cme_gaps.py` logic into backend
   - Remove or refactor `check_cme_details.py`
   - **Deliverable**: Reduced script count from 19 → 10

5. **Add Monitoring** (5 days)
   - Log when ad hoc scripts are run
   - Compare script output to backend API output
   - Alert if divergence detected
   - **Deliverable**: DataDog/Sentry alerts for logic divergence

**Success Criteria:**
- ✅ Backend service is authoritative source for all CME calculations
- ✅ Ad hoc scripts call backend API, do not duplicate logic
- ✅ Shared library available for all CME logic consumers
- ✅ Script count reduced by 50%
- ✅ Monitoring detects divergence automatically

---

### Phase 3: Long-Term (Next 90 Days) - Prevent Recurrence

**Goal**: Architectural changes to prevent future divergence

**Tasks:**

1. **Rules Engine Consolidation** (30 days)
   - **Current state**: YAML SSOT → JSON rule packs → Database → Code constants
   - **Target state**: Single YAML source → Compile to all formats
   - Implement `apps/rules-engine` as canonical source
   - Auto-generate backend constants from rules engine
   - **Deliverable**: Rules engine compilation pipeline

2. **TDD for Business Rules** (20 days)
   - Test every state-specific CME rule explicitly
   - Test category_1 handling for all 51 states
   - Test conditional filtering with various provider profiles
   - Test topic consolidation groups for all groups
   - **Deliverable**: 500+ unit tests covering all rule combinations

3. **Feature Flags for Business Logic** (15 days)
   - Instead of hardcoding keywords/conditions in code
   - Store conditional keywords in database
   - Query feature flags at runtime
   - Allows A/B testing of logic changes
   - **Deliverable**: Feature flag system integrated

4. **Documentation as Code** (15 days)
   - Business logic documented in docstrings
   - Link requirements to state board regulatory docs
   - Auto-generate compliance matrix from code
   - **Deliverable**: Auto-generated compliance documentation

5. **Architecture Decision Record** (10 days)
   - Document decision: "Backend service is SSOT for business logic"
   - Document anti-pattern: "Ad hoc scripts with business logic"
   - Document enforcement: Pre-commit hooks, code review guidelines
   - **Deliverable**: ADR-002-business-logic-consolidation.md

**Success Criteria:**
- ✅ Rules engine is single source of truth
- ✅ Code constants auto-generated from YAML
- ✅ TDD coverage >80% for all CME rules
- ✅ Feature flags allow runtime logic changes
- ✅ Documentation auto-generated and always current

---

## Implementation Roadmap

```
Week 1:  [Phase 1] Audit, Eliminate Duplicates, Integration Tests, Policy Docs
Week 2:  [Phase 2] Refactor generate_cme_v4.py to call backend
Week 3:  [Phase 2] Refactor generate_cme_action_plan.py to call backend
Week 4:  [Phase 2] Create shared CME calculator library
Week 5:  [Phase 2] Deprecate duplicate scripts, Add monitoring
Week 6:  [Phase 2] API-First workflow documentation
Week 7:  [Phase 3] Rules engine consolidation (start)
Week 8:  [Phase 3] Rules engine consolidation (continue)
Week 9:  [Phase 3] Rules engine consolidation (finish), TDD (start)
Week 10: [Phase 3] TDD (continue)
Week 11: [Phase 3] TDD (finish), Feature flags
Week 12: [Phase 3] Documentation as code, ADR
```

**Total Duration**: 12 weeks (3 months)

---

## Risk Mitigation

### Risks During Remediation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing scripts | HIGH | Run integration tests before every change |
| Backend API changes break scripts | MEDIUM | Version API endpoints, maintain backward compatibility |
| Performance degradation | MEDIUM | Benchmark script performance before/after refactoring |
| Data accuracy issues | CRITICAL | Compare output byte-for-byte against baseline |
| Developer resistance | MEDIUM | Show value (fewer bugs, faster development) |

### Rollback Plan

If remediation introduces bugs:
1. **Immediate**: Revert to previous script versions (keep in `scripts/legacy/`)
2. **Short-term**: Run old and new scripts in parallel, compare outputs
3. **Long-term**: Only promote scripts to production after 2-week validation period

---

## Success Metrics

**Quantitative:**
- ❌ → ✅ Zero code duplication for business logic (currently 3 duplicates identified)
- ❌ → ✅ 100% parity between ad hoc script output and backend API output
- 19 scripts → 10 scripts (50% reduction)
- 0 tests → 500+ tests for CME rules (100% coverage of state rules)
- 0 monitoring → 5 alerts for logic divergence

**Qualitative:**
- ✅ Developers consult backend service first, not ad hoc scripts
- ✅ New CME features added to backend API before scripts
- ✅ Business logic documented in single location (rules engine)
- ✅ No "shadow implementations" of business logic

---

## Budget Estimate

**Engineering Time:**

| Phase | Developer Days | Cost Estimate |
|-------|----------------|---------------|
| Phase 1 (Immediate) | 7 days | $7,000 |
| Phase 2 (Refactoring) | 30 days | $30,000 |
| Phase 3 (Long-term) | 90 days | $90,000 |
| **Total** | **127 days** | **$127,000** |

**Assumptions:**
- 1 senior developer @ $1,000/day
- Parallelizable tasks could reduce timeline by 40% if 2 developers assigned

**ROI:**
- **Cost of inaction**: 3 critical bugs discovered in 1 week → extrapolate to ~150 bugs/year
- **Cost per bug**: ~$5,000 (investigation, fix, testing, deployment)
- **Annual cost**: $750,000 in bug fixes
- **ROI**: $127K investment prevents $750K annual cost = 5.9x return

---

## Next Steps

1. **Immediate (Today)**:
   - Review this plan with engineering lead
   - Assign owner for Phase 1 execution
   - Schedule kickoff meeting

2. **This Week**:
   - Complete Phase 1 tasks (audit, eliminate duplicates, integration tests)
   - Update work queue with remediation tasks
   - Create tracking GitHub project

3. **This Month**:
   - Complete Phase 2 refactoring
   - Launch monitoring for logic divergence
   - Begin Phase 3 planning

---

## Appendices

### Appendix A: Ad Hoc Scripts Inventory

See investigation report from agent ae269ca for full list of 19 scripts.

### Appendix B: Backend Service Coverage Matrix

See investigation report section "Backend Service Coverage" for detailed comparison.

### Appendix C: Integration Test Examples

```python
# tests/integration/test_adhoc_parity.py

def test_generate_cme_v4_matches_backend_api():
    """Ensure ad hoc script output matches backend API for same input."""
    provider_email = "real300@test.com"

    # Run ad hoc script
    adhoc_output = run_adhoc_script("generate_cme_v4.py", email=provider_email)

    # Query backend API
    api_output = cme_compliance_service.calculate_compliance(
        provider_id=get_provider_id(provider_email),
        state="FL",
        license_type="MD",
        cycle_start=date(2024, 1, 31),
        cycle_end=date(2026, 1, 31)
    )

    # Compare
    assert adhoc_output["gaps"] == api_output["gaps"]
    assert adhoc_output["total_earned"] == api_output["total_earned"]
```

---

**Plan Author**: AI Orchestrator Investigation Team
**Reviewed By**: TBD
**Approved By**: TBD
**Implementation Start Date**: TBD
