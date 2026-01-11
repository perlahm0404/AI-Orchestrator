# Quick Deployment Prompt for ADR-006

## For Operator Team / Manual Deployment

Copy and paste this prompt to initiate deployment:

---

## Deployment Request: ADR-006 Gap Calculation Fix

**Project**: CredentialMate
**Environment**: Staging → Production
**Priority**: HIGH (HIPAA data integrity fix)
**Branch**: main
**Commit**: 9b3ee81d

### What to Deploy

Deploy ADR-006 (CME Gap Calculation Standardization) which fixes contradictory gap calculations:
- **Problem**: Dashboard shows 4.0h gap, State Detail shows 2.0h gap (same provider/state)
- **Solution**: Single Calculation Service Architecture - all endpoints now consistent

### Changes Included

- 21 files modified (+3,722 lines)
- Backend: Unified gap calculation method
- Frontend: Removed client-side calculations, added overlap badges
- Scripts: Ad-hoc reports now use backend API
- Tests: 610 LOC new tests (all passing)

### Deployment Steps

#### 1. Deploy to Staging

```bash
cd /Users/tmac/1_REPOS/credentialmate
git checkout main
git pull origin main
# Verify commit: 9b3ee81d

# Deploy to staging (use your deployment method)
# Examples:
# ./deploy.sh staging
# OR push to staging branch for CI/CD
# OR manual deployment via hosting provider
```

**Health Checks After Staging Deploy**:
- [ ] Application starts successfully
- [ ] API health endpoint returns 200
- [ ] No errors in logs
- [ ] Frontend loads without errors

#### 2. QA Validation on Staging

**Critical Test**: Dr. Sehgal Florida Gap Consistency

1. Login to staging as test provider (51h earned, 0h Medical Errors)
2. Go to CME Dashboard → Verify Florida shows **2.0h gap** (NOT 4.0h)
3. Click Florida → Verify State Detail shows **2.0h gap**
4. Download ad-hoc CME report → Verify shows **2.0h gap**
5. Check for overlap badges in tooltips (blue "Overlaps", orange "Separate")

**Pass Criteria**: All three sources show identical 2.0h gap ✅

#### 3. Deploy to Production (REQUIRES APPROVAL)

**Pre-deployment**:
- [ ] Staging QA passed
- [ ] Database backup verified
- [ ] Deployment window scheduled (off-peak hours)
- [ ] Rollback plan confirmed

```bash
cd /Users/tmac/1_REPOS/credentialmate
git checkout main
# Verify commit: 9b3ee81d

# Deploy to production (use your deployment method)
# ./deploy.sh production
```

**Health Checks After Production Deploy**:
- [ ] Application responds to health endpoint (5 min)
- [ ] No 500 errors in logs (5 min)
- [ ] API response times normal <500ms (5 min)
- [ ] Error rate below 0.1% (15 min)
- [ ] No user complaints (30 min)

#### 4. Production Smoke Test

1. Login as test user
2. Check CME dashboard displays gaps correctly
3. Click through to state detail page
4. Verify overlap badges visible
5. Spot-check 3-5 real providers for gap consistency

### Rollback Plan

**If Issues Occur**:
```bash
cd /Users/tmac/1_REPOS/credentialmate
git revert 3a422807 --no-edit  # Revert ADR-006 merge
git push origin main
# Re-deploy to production
```

**Rollback Time**: ~5 minutes

### Success Criteria

Deployment successful when:
- ✅ All health checks pass
- ✅ Error rate at baseline
- ✅ Dr. Sehgal test shows 2.0h gap consistently
- ✅ Overlap badges display correctly
- ✅ No performance degradation
- ✅ Metrics stable for 24 hours

### Risk Assessment

**Overall Risk**: MEDIUM
- **Technical Risk**: LOW (610 LOC tests, comprehensive validation)
- **Business Risk**: LOW (fixes existing bug, improves HIPAA compliance)

### Estimated Timeline

- Staging deployment: 5 min
- Staging QA: 30 min
- Production deployment: 10 min
- Production monitoring: 30 min
- **Total**: ~75 minutes

### Support Information

**Full Deployment Plan**: See `deploy-adr006-production.md` for comprehensive details

**Key Commits**:
- Merge: 3a422807
- Latest: 9b3ee81d

**Documentation**:
- Completion Summary: `/adapters/credentialmate/plans/ADR-006-COMPLETION-SUMMARY.md`
- Session Summary: `/adapters/credentialmate/sessions/session-2026-01-10-autonomous-adr006.md`

---

## Quick Reference: Test Validation

### Expected Results After Deployment

**Dr. Sehgal Florida Case** (51h earned, 0h Medical Errors, 2h required):
```
Before:
- Dashboard (/harmonize):     4.0h gap ❌
- State Detail (/check):      2.0h gap ✓
- Ad-hoc Reports:             ??? (unreliable)

After:
- Dashboard (/harmonize):     2.0h gap ✅
- State Detail (/check):      2.0h gap ✅
- Ad-hoc Reports:             2.0h gap ✅
```

**Overlap Badge Display**:
- Medical Errors Prevention: Orange badge "Separate requirement (additive)"
- Other overlapping topics: Blue badge "Overlaps with general CME"

---

**Ready to Deploy**: Yes ✅
**Blocker**: None
**Next Step**: Deploy to staging and run QA validation
