# ADR-006 Implementation Summary

**Date**: 2026-01-10
**Status**: ✅ Ready for Implementation
**Approved By**: tmac

---

## Quick Start

### For Claude CLI Implementation:

1. **Open new Claude CLI session** in CredentialMate repository:
   ```bash
   cd /Users/tmac/1_REPOS/credentialmate
   claude
   ```

2. **Copy the implementation prompt**:
   ```bash
   cat /Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/ADR-006-implementation-prompt.md
   ```

3. **Paste into Claude CLI** and say "implement this"

4. **Claude will execute** all 5 phases automatically (10 days of work)

---

## What This Fixes

**Problem**: Dashboard shows 4.0 hrs gap, State detail shows 2.0 hrs gap for same provider/state

**Root Cause**: Two different gap calculation methods (overlap logic vs naive subtraction)

**Solution**: Extract overlap logic into single service method, used by all endpoints

---

## Deliverables

### ADR Document
✅ **Created**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/decisions/ADR-006-cme-gap-calculation-standardization.md`

**Contents**:
- Problem context (contradictory gaps)
- Architecture recommendation (Single Calculation Service)
- 5-phase implementation plan (10 days, $11K)
- Success criteria (100% parity across all endpoints)

### Implementation Prompt
✅ **Created**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/ADR-006-implementation-prompt.md`

**Contents**:
- Complete step-by-step instructions for Claude CLI
- Code snippets for all phases
- Test cases (unit, integration, E2E)
- Manual QA checklist
- Success validation

---

## Implementation Phases

| Phase | Tasks | Duration | Cost |
|-------|-------|----------|------|
| 1. Backend Consolidation | Extract overlap logic, create `calculate_gap_with_overlap()` | 2 days | $2K |
| 2. API Contract Standardization | Add `counts_toward_total` to schemas | 2 days | $2K |
| 3. Frontend Refactor | Remove client-side calculations, add badges | 3 days | $3K |
| 4. Ad-hoc Reports | Call API instead of local calculation | 1 day | $1K |
| 5. Testing & Validation | E2E tests, Dr. Sehgal case, manual QA | 2 days | $3K |
| **Total** | | **10 days** | **$11K** |

---

## Success Criteria

Implementation is complete when:

✅ **Dr. Sehgal shows 2.0 hrs gap** on dashboard, state detail, and reports (not 4.0h and 2.0h)
✅ **All tests pass** (unit, integration, E2E)
✅ **UI shows overlap badges** (blue for overlapping topics, orange for additive)
✅ **No client-side calculations** (all gaps from API)
✅ **100% parity** (harmonize == check == ad-hoc reports)

---

## Key Architecture Changes

### Before (BROKEN):
```
Dashboard → /harmonize → overlap logic ✅ → 4.0h gap
State Detail → /check → naive subtraction ❌ → 2.0h gap
Ad-hoc Reports → local SQL → ??? → ???
```

### After (FIXED):
```
All Components → calculate_gap_with_overlap() → 2.0h gap
                        ↑
                Single Source of Truth
```

---

## Test Cases Added

1. **Unit Tests** (`test_gap_calculation.py`):
   - `test_separate_topics_are_additive()`
   - `test_overlapping_topics_use_max()`
   - `test_mixed_overlap_and_separate()`
   - `test_dr_sehgal_florida_case()`

2. **Integration Tests** (`test_cme_parity.py`):
   - `test_harmonize_check_parity_dr_sehgal_florida()`
   - `test_harmonize_check_parity_multiple_states()`

3. **E2E Tests** (`test_dr_sehgal_consistency.py`):
   - `test_florida_gap_consistency_across_all_endpoints()`
   - `test_ohio_zero_gap_consistency()`

4. **Ad-hoc Parity** (`test_adhoc_parity.py`):
   - `test_adhoc_report_matches_api()`

---

## Files Modified

### Backend (7 files)
1. `apps/backend-api/src/core/services/cme_compliance_service.py` - Add `calculate_gap_with_overlap()`
2. `apps/backend-api/src/contexts/cme/api/compliance_endpoints.py` - Refactor `/harmonize`
3. `apps/backend-api/src/contexts/cme/schemas/cme_schemas.py` - Add `counts_toward_total` field
4. `apps/backend-api/tests/unit/cme/test_gap_calculation.py` - NEW
5. `apps/backend-api/tests/integration/test_cme_parity.py` - NEW
6. `apps/backend-api/tests/e2e/test_dr_sehgal_consistency.py` - NEW
7. `tests/integration/test_adhoc_parity.py` - NEW

### Frontend (3 files)
8. `apps/frontend-web/src/app/dashboard/states/[state]/page.tsx` - Remove client-side calc
9. `apps/frontend-web/src/components/dashboard/CMEComplianceTable.tsx` - Update tooltips
10. `apps/frontend-web/src/app/dashboard/states/__tests__/StatePage.test.tsx` - NEW

### Scripts (1 file)
11. `scripts/generate_cme_v4.py` - Call API instead of local calculation

**Total**: 11 files (7 backend, 3 frontend, 1 script)

---

## Validation Steps

After implementation, verify:

```bash
# 1. Run all backend tests
cd /Users/tmac/1_REPOS/credentialmate
pytest apps/backend-api/tests/unit/cme/test_gap_calculation.py -v
pytest apps/backend-api/tests/integration/test_cme_parity.py -v
pytest apps/backend-api/tests/e2e/test_dr_sehgal_consistency.py -v
pytest tests/integration/test_adhoc_parity.py -v

# 2. Run frontend tests
cd apps/frontend-web
npm test -- StatePage.test.tsx

# 3. Run ad-hoc report
python scripts/generate_cme_v4.py --email real300@test.com

# 4. Manual QA in browser
# - Open /dashboard/cme → verify FL shows 2.0h gap
# - Open /dashboard/states/FL → verify shows 2.0h gap
# - Verify badges show "Additive" for Medical Errors Prevention
```

---

## Rollback Plan

If issues arise:

1. **Keep old methods** in `_legacy` namespace for 30 days
2. **Run old/new in parallel**, log discrepancies
3. **Feature flag** to toggle between old/new calculations
4. **Only remove legacy code** after 100% validation

---

## Related ADRs

- **ADR-002**: CME Topic Hierarchy (provides `normalized_topic`)
- **ADR-005**: Business Logic Consolidation (Backend SSOT principle)
- **ADR-006**: CME Gap Calculation Standardization (THIS)

---

## Next Steps

1. ✅ **ADR approved** (tmac, 2026-01-10)
2. ✅ **Implementation prompt created** (ready for Claude CLI)
3. ⏳ **Start implementation** (10 days, 5 phases)
4. ⏳ **Validate success** (all tests pass + manual QA)
5. ⏳ **Mark ADR-006 as COMPLETE**

---

## Questions?

- **ADR Document**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/decisions/ADR-006-cme-gap-calculation-standardization.md`
- **Implementation Prompt**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/ADR-006-implementation-prompt.md`
- **Contact**: Review with tmac if blockers arise

---

**Status**: ✅ Ready to implement (all planning complete)
