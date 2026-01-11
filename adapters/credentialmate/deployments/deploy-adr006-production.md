# Production Deployment: ADR-006 Gap Calculation Fix

**Date**: 2026-01-10
**Priority**: HIGH (HIPAA Data Integrity Fix)
**Risk Level**: MEDIUM (Core calculation logic change)
**Rollback Plan**: Available (revert to commit 6c71c9d6)

---

## Deployment Request

Deploy ADR-006 (CME Gap Calculation Standardization) to production environment.

**What This Fixes**: Contradictory gap calculations showing 4.0h on dashboard vs 2.0h on state detail page for same provider/state

**Impact**: All CME compliance gap displays will now show consistent values across dashboard, state detail pages, and downloadable reports

---

## Pre-Deployment Validation

### Code Status ✅

- **Branch**: `main`
- **Commit**: `9b3ee81d` (includes merge commit 3a422807)
- **Tests**: All passing (unit, integration, E2E)
- **Pre-commit Hooks**: All passed
- **Code Review**: Completed via autonomous execution

### Changes Summary ✅

**Files Modified**: 21
- Backend: 7 files (core calculation service, endpoints, schemas, tests)
- Frontend: 3 files (gap display, tooltips, tests)
- Scripts: 1 file (ad-hoc report generation)

**Lines Changed**: +3,722 (3,955 insertions, 233 deletions)
- Production code: 440 LOC
- Test code: 610 LOC

**Database Migrations**: None (schema changes already deployed)

---

## Deployment Workflow

### Step 1: Deploy to Staging ⏳

**Environment**: `staging.credentialmate.com`
**Branch**: `main` (commit 9b3ee81d)

**Pre-deployment Checklist**:
- [ ] Pull latest main branch
- [ ] Verify all tests pass locally
- [ ] Check environment variables configured
- [ ] Verify database migrations up to date

**Deployment Commands**:
```bash
cd /Users/tmac/1_REPOS/credentialmate

# Verify we're on correct commit
git log -1 --oneline
# Expected: 9b3ee81d chore: Update progress tracking

# Deploy to staging (replace with actual deployment command)
# Example: ./deploy.sh staging
# OR: Push to staging branch and CI/CD handles it
# OR: Manual deployment via hosting provider
```

**Post-deployment Health Checks**:
- [ ] Application starts successfully
- [ ] API health endpoint returns 200
- [ ] Database connection successful
- [ ] No errors in application logs
- [ ] Frontend loads without errors

---

### Step 2: QA Validation on Staging ⏳

**Critical Test Cases**:

#### Test Case 1: Dr. Sehgal Florida Gap Consistency
**Provider**: Test provider with 51h earned, 0h Medical Errors
**Expected**: 2.0h gap shown on ALL pages

1. Login to staging as test provider
2. Navigate to CME Dashboard
3. **Verify**: Florida shows 2.0h gap (NOT 4.0h)
4. Click on Florida state
5. **Verify**: State detail page shows 2.0h gap
6. **Verify**: Overlap badge visible on Medical Errors Prevention topic
7. Download ad-hoc CME report
8. **Verify**: Report shows 2.0h gap for Florida

**Pass Criteria**: All three sources show identical 2.0h gap ✅

#### Test Case 2: Overlap Badge Display
**Expected**: UI tooltips show overlap indicators

1. Navigate to state detail page with topic requirements
2. Hover over topic gaps
3. **Verify**: Blue badge "Overlaps with general CME" for overlapping topics
4. **Verify**: Orange badge "Separate requirement (additive)" for separate topics
5. **Verify**: Explanation text appears in tooltip

**Pass Criteria**: Badges display correctly with proper colors and text ✅

#### Test Case 3: Multiple Providers Spot Check
**Expected**: Gap calculations consistent for various scenarios

Test with 3-5 different provider profiles:
- Provider with all requirements met → 0h gap
- Provider with overlapping topic gaps → Uses max() logic
- Provider with separate topic gaps → Uses additive logic
- Provider with mixed scenario → Correct combination

**Pass Criteria**: All calculations match expected values ✅

#### Test Case 4: Backend Endpoint Parity
**Expected**: `/harmonize` and `/check` return same gaps

1. Call `/api/v1/cme/compliance/harmonize` for test provider
2. Call `/api/v1/cme/compliance/check` for same provider + state
3. **Verify**: Gap values match exactly
4. **Verify**: Both return `counts_toward_total` metadata
5. **Verify**: Both return `explanation` fields

**Pass Criteria**: 100% parity between endpoints ✅

---

### Step 3: Staging Approval Gate 🚦

**QA Sign-off Required**:
- [ ] All test cases passed
- [ ] No errors in staging logs
- [ ] Performance acceptable (no degradation)
- [ ] UI displays correctly
- [ ] Gap calculations validated

**Decision Point**:
- ✅ **PASS** → Proceed to production deployment
- ❌ **FAIL** → Investigate issues, fix, re-deploy to staging

---

### Step 4: Deploy to Production 🚀

**Environment**: `app.credentialmate.com`
**Approval**: **REQUIRED** (HIPAA application)

**Pre-deployment Checklist**:
- [ ] Staging validation completed successfully
- [ ] QA sign-off obtained
- [ ] Rollback plan confirmed
- [ ] Database backup verified (within last 24 hours)
- [ ] Deployment window scheduled (low-traffic period)
- [ ] On-call engineer identified
- [ ] Monitoring alerts configured

**Deployment Commands**:
```bash
cd /Users/tmac/1_REPOS/credentialmate

# Final verification
git status
# Expected: On branch main, up to date with origin/main

# Deploy to production (replace with actual deployment command)
# Example: ./deploy.sh production
# OR: Tag release and CI/CD handles it
# OR: Manual deployment via hosting provider
```

**Deployment Steps**:
1. Enable maintenance mode (optional, if zero-downtime not available)
2. Deploy application code
3. Restart application servers
4. Verify health checks pass
5. Disable maintenance mode
6. Monitor error rates for 15 minutes

---

### Step 5: Production Health Checks 🏥

**Immediate Checks** (within 5 minutes):
- [ ] Application responds to health endpoint
- [ ] No 500 errors in logs
- [ ] Database connections healthy
- [ ] API response times normal (<500ms p95)
- [ ] Frontend loads successfully
- [ ] No JavaScript errors in console

**Extended Monitoring** (first 30 minutes):
- [ ] Error rate below baseline (<0.1%)
- [ ] API endpoint response times stable
- [ ] Database query performance acceptable
- [ ] Memory usage normal
- [ ] CPU usage normal
- [ ] No user-reported issues

**Smoke Tests on Production**:
1. Login as test user
2. Navigate to CME dashboard
3. Verify gaps display correctly
4. Click through to state detail page
5. Verify overlap badges visible
6. Download test report (if safe in production)

---

### Step 6: Post-Deployment Validation 📊

**Critical Metrics to Monitor**:

| Metric | Baseline | Threshold | Action if Exceeded |
|--------|----------|-----------|-------------------|
| Error rate | <0.1% | >0.5% | Investigate immediately |
| API latency (p95) | <500ms | >1000ms | Check query performance |
| Database CPU | <40% | >80% | Check slow queries |
| Memory usage | <60% | >85% | Check for memory leaks |
| User complaints | 0 | >2 | Investigate UX issues |

**Data Integrity Checks**:
- [ ] Run Dr. Sehgal E2E test against production API
- [ ] Spot-check 5-10 real providers for gap consistency
- [ ] Compare dashboard vs state detail gaps (should match)
- [ ] Verify ad-hoc reports show same gaps as dashboard

---

## Rollback Plan 🔄

**Trigger Conditions for Rollback**:
- Error rate >1%
- Critical functionality broken
- Data integrity issues detected
- Performance degradation >50%
- Multiple user complaints (>5 within 30 minutes)

**Rollback Procedure**:

### Option 1: Revert to Previous Commit (Fast)
```bash
cd /Users/tmac/1_REPOS/credentialmate

# Revert to commit before ADR-006 merge
git revert 3a422807 --no-edit
git push origin main

# Re-deploy using standard deployment process
# ./deploy.sh production
```

**Rollback Time**: ~5 minutes

### Option 2: Roll Forward with Hotfix (If Partial Issue)
```bash
# Create hotfix branch
git checkout -b hotfix/adr006-issue
# Fix specific issue
# Test
# Deploy hotfix
```

**Rollback Time**: ~15-30 minutes (depending on fix complexity)

### Post-Rollback Actions:
- [ ] Verify error rates return to normal
- [ ] Confirm users can access application
- [ ] Document what went wrong
- [ ] Create incident report
- [ ] Plan remediation strategy

---

## Communication Plan 📢

### Internal Stakeholders

**Before Deployment**:
- Engineering team: "Deploying ADR-006 gap calculation fix to production at [TIME]"
- Support team: "Be aware of deployment, monitor for user feedback on gap displays"

**During Deployment**:
- Status updates every 5 minutes during deployment window
- Immediate notification if issues arise

**After Deployment**:
- Success notification: "ADR-006 deployed successfully, monitoring metrics"
- Summary report after 24 hours

### External Users (If Needed)

**Status Page Update** (optional):
```
[Date/Time] Deployed: CME gap calculation improvements
We've improved the consistency of CME gap calculations across
all dashboard views and reports. You may notice that gap values
are now identical whether viewed on the main dashboard, state
detail pages, or in downloaded reports.
```

---

## Success Criteria ✅

Deployment is considered **successful** when:

1. ✅ All health checks pass
2. ✅ Error rate remains below baseline
3. ✅ Dr. Sehgal test case shows 2.0h gap consistently
4. ✅ Overlap badges display correctly in UI
5. ✅ No performance degradation
6. ✅ No user complaints within first 4 hours
7. ✅ Metrics stable for 24 hours

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Calculation errors | LOW | HIGH | 610 LOC of tests, E2E validation |
| Performance degradation | LOW | MEDIUM | Monitored, rollback available |
| Frontend display issues | LOW | LOW | Component tests, staging validation |
| Database load increase | LOW | MEDIUM | Same queries, better logic |

### Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| User confusion (gap changes) | MEDIUM | LOW | Gap now CORRECT (was broken) |
| Support ticket increase | LOW | LOW | Support team briefed |
| Compliance audit issue | VERY LOW | VERY LOW | Fix improves HIPAA compliance |

### Overall Risk Level: **MEDIUM**

**Justification**: Core calculation logic change, but comprehensive testing and validation reduce risk significantly. The change FIXES a data integrity issue, so risk of NOT deploying is higher than deploying.

---

## Deployment Timeline Estimate

| Phase | Duration | Window |
|-------|----------|--------|
| Staging deployment | 5 min | Immediate |
| Staging QA validation | 30 min | Immediate |
| Staging approval | 5 min | After QA |
| Production deployment | 10 min | Scheduled window |
| Production health checks | 15 min | Immediately after |
| Extended monitoring | 30 min | After health checks |
| **Total** | **~95 min** | **~2 hours** |

**Recommended Deployment Window**:
- **Weekday**: 6:00 AM - 8:00 AM PT (low traffic)
- **OR**: 10:00 PM - 11:00 PM PT (minimal user impact)

---

## Post-Deployment Monitoring (24 hours)

**Dashboards to Monitor**:
- [ ] Application error logs (Sentry, Datadog, etc.)
- [ ] API response time metrics
- [ ] Database performance metrics
- [ ] Frontend error tracking
- [ ] User session analytics

**Alert Thresholds**:
- Error rate >0.5%: Page on-call engineer
- API latency >1s: Investigate immediately
- Database CPU >80%: Check slow queries

**Success Indicators** (after 24 hours):
- Zero rollbacks
- Error rate at or below baseline
- No user-reported gap inconsistencies
- Performance metrics stable
- Support tickets related to gaps: 0

---

## Approval Signatures

**Required Approvals**:

- [ ] **Engineering Lead**: ___________________ Date: _______
  - Code review complete
  - Tests passing
  - Deployment plan approved

- [ ] **QA Lead**: ___________________ Date: _______
  - Staging validation complete
  - Test cases passed
  - Ready for production

- [ ] **Product Owner**: ___________________ Date: _______
  - Business impact understood
  - User communication plan approved
  - Deployment timing approved

- [ ] **Security/Compliance**: ___________________ Date: _______
  - HIPAA compliance verified
  - Data integrity improvements confirmed
  - Audit trail complete

---

## Appendix: Technical Details

### Commits Included in Deployment

**Merge Commit**: `3a422807` - ADR-006 feature branch merge

**Included Work** (16 implementation commits):
- Backend: Single Calculation Service (SSOT)
- Frontend: Removed client-side calculations
- Tests: 610 LOC comprehensive coverage
- Documentation: 8 ADR documents

**Post-Merge Documentation** (7 commits):
- ADR auto-generation
- Progress tracking updates

### Key Files Modified

**Backend**:
- `apps/backend-api/src/core/services/cme_compliance_service.py`
- `apps/backend-api/src/contexts/cme/api/compliance_endpoints.py`
- `apps/backend-api/src/contexts/cme/schemas/cme_schemas.py`

**Frontend**:
- `apps/frontend-web/src/components/dashboard/CMEComplianceTable.tsx`
- `apps/frontend-web/src/app/dashboard/states/[state]/page.tsx`

**Scripts**:
- `scripts/generate_cme_v4.py`

### Environment Variables Required

No new environment variables needed. Existing configuration sufficient.

### Database Migrations

No new migrations required (schemas already support new fields from previous deployments).

---

**Deployment Status**: ⏳ **READY FOR STAGING**

**Next Action**: Deploy to staging environment and begin QA validation

**Prepared By**: AI Orchestrator (Autonomous Execution)
**Date Prepared**: 2026-01-10
**Document Version**: 1.0
