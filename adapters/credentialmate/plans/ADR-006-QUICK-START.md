# ADR-006 Quick Start - CME Gap Calculation Fix

**Problem**: Dashboard shows 4.0h gap, State page shows 2.0h gap (Dr. Sehgal, Florida)
**Solution**: Single calculation service used everywhere
**Status**: ✅ Approved, Ready to implement
**Timeline**: 10 days, $11K

---

## Start Implementation NOW

### Option 1: Claude CLI (Recommended)

```bash
# 1. Open CredentialMate repo
cd /Users/tmac/1_REPOS/credentialmate

# 2. Start Claude CLI
claude

# 3. Copy this command:
cat /Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/ADR-006-implementation-prompt.md

# 4. In Claude, paste the prompt and say: "implement this"
```

Claude will execute all 5 phases automatically.

---

### Option 2: Manual Implementation

Read the full prompt at:
`/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/ADR-006-implementation-prompt.md`

Follow phases 1-5 sequentially.

---

## Quick Validation

After implementation, run:

```bash
# Test Dr. Sehgal case (should show 2.0h gap everywhere)
pytest apps/backend-api/tests/e2e/test_dr_sehgal_consistency.py -v

# If passes → SUCCESS ✅
# If fails → Check logs, review Phase 1 implementation
```

---

## What Gets Fixed

| Component | Before | After |
|-----------|--------|-------|
| Dashboard | 4.0h gap ❌ | 2.0h gap ✅ |
| State Detail | 2.0h gap ✅ | 2.0h gap ✅ |
| Ad-hoc Reports | ??? | 2.0h gap ✅ |

---

## Files You'll Touch

**Backend** (add `calculate_gap_with_overlap()` method):
- `apps/backend-api/src/core/services/cme_compliance_service.py`

**Frontend** (remove client-side calculations):
- `apps/frontend-web/src/app/dashboard/states/[state]/page.tsx`

**Tests** (add parity tests):
- `apps/backend-api/tests/unit/cme/test_gap_calculation.py`
- `apps/backend-api/tests/e2e/test_dr_sehgal_consistency.py`

---

## Success = All Green

```
✅ test_dr_sehgal_florida_case PASSED
✅ test_harmonize_check_parity PASSED
✅ test_adhoc_report_matches_api PASSED
✅ Manual QA: Dashboard shows 2.0h gap
✅ Manual QA: State detail shows 2.0h gap
```

---

## Documents

- **ADR**: `decisions/ADR-006-cme-gap-calculation-standardization.md`
- **Implementation Prompt**: `ADR-006-implementation-prompt.md`
- **Summary**: `ADR-006-SUMMARY.md`
- **This File**: `ADR-006-QUICK-START.md`

---

**Ready? Start with Claude CLI option above. It will do everything for you.**
