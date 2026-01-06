# Session: Appointment Routes Test Debugging

**Date**: 2026-01-06
**Task**: Fix public appointment API routes returning 404 errors
**Agent**: QA Team (BugFix workflow)
**Project**: KareMatch

## Session Summary

**Status**: 🟡 Partial Progress (test data seeding fixed, route issues remain)

**Impact**:
- Test failures: 70 → 50 (expected after full fix)
- Currently: 70 → 70 (no net change yet, but infrastructure improved)
- **Key Win**: Test data now seeds successfully (was completely broken)

## What Was Accomplished

### 1. Root Cause Analysis ✅

Identified THREE major issues causing 20 test failures in `tests/appointments-routes.test.ts`:

1. **Missing Service Initialization**
   - Tests started before async service loading completed
   - `createAppointmentRoutes()` returned empty router
   - **Fix**: Added `await waitForInit(10000)` to `beforeAll` hook

2. **Schema Mismatch**
   - Test imported from `@karematch/types` (has `password` field)
   - Actual DB uses `@karematch/data` schema (has `passwordHash` field)
   - **Fix**: Import `users` from `@karematch/data` instead

3. **ID/FK Confusion**
   - Multiple schemas with different FK relationships
   - `therapistAvailability.therapistId` → FKs to `users.id`
   - Therapist profile IDs vs user IDs confusion

### 2. Files Modified ✅

**File**: `tests/appointments-routes.test.ts`

**Changes**:
1. Line 12: Added `waitForInit` import from `../api/src/index`
2. Line 15: Changed import to `users } from "@karematch/data"` (correct schema)
3. Lines 814-815: Added `await waitForInit(10000)` in `beforeAll` hook
4. Lines 827-828: Fixed user creation to use `passwordHash` field

**Diff summary**:
```diff
+ import app, { waitForInit } from "../api/src/index";
+ import { users } from "@karematch/data";
+ await waitForInit(10000); // Wait for service initialization
  passwordHash: "test-hash-not-used-in-tests",  // was: password
```

### 3. Key Discoveries ✅

**Schema Architecture**:
- `/packages/types/src/database/schema.ts` → OUTDATED (has `password` field)
- `/data/schema/identity.ts` → ACTUAL DB SCHEMA (has `passwordHash` field)
- Tests must import from `@karematch/data` for correct schema

**Route Mounting**:
- Routes defined in `services/appointments/src/routes.ts`
- Mounted at `/api/public` in `api/src/index.ts:644`
- Lazy initialization requires `waitForInit()` before testing

**FK Relationships** (from actual schema):
```typescript
// /data/schema/identity.ts:756
therapistAvailability.therapistId → references users.id

// Therapist profile table
therapists.id = "test-therapist-1"
therapists.userId = "therapist-user-1"  // FK to users.id
```

## What Was NOT Done

### Remaining Issues

1. **Routes Still Return 404** (20 failures)
   - Test data seeds successfully now (no more "Failed to seed" errors)
   - But routes still can't find the data
   - Likely issue: ID mismatch between test data and route queries

2. **ID/FK Alignment**
   - Need to verify exact FK relationships in deployed DB vs schema files
   - Test uses `therapistId = "test-therapist-1"`
   - Routes may expect different ID format

3. **Route Handler Investigation Needed**
   - Check how routes query data (which fields/FKs)
   - Verify test data structure matches route expectations
   - May need to adjust test IDs or route logic

## Test Status Breakdown

**File**: `tests/appointments-routes.test.ts`

**Total**: 79 tests | 20 failed | 5 passed | 54 skipped

**Failing Tests** (all 404 errors):
- `GET /api/public/therapist/:therapistId/availability` (5 tests)
- `GET /api/public/therapists/:therapistId/upcoming-slots` (2 tests)
- `GET /api/public/therapists/:therapistId/available-dates` (2 tests)
- `POST /api/public/book` (9 tests)
- `GET /api/public/appointment/:id` (2 tests)

**Passing Tests** (5):
- Some basic validation tests that don't require data lookups

**Skipped Tests** (54):
- Therapist authenticated endpoints (not in scope for this task)

## Next Steps

### Immediate (Next Session)

1. **Debug ID Mismatch**:
   ```bash
   # Check what therapistId values routes expect
   # vs what test data provides
   grep -A 10 "therapistId.*req.params" services/appointments/src/routes.ts
   ```

2. **Verify Route Queries**:
   - Line 1422 in routes.ts: How does availability route query data?
   - Line 1660 in routes.ts: How does booking route query therapist?
   - Do they use `users.id` or `therapists.id`?

3. **Test Data Alignment**:
   - If routes expect `users.id`: Use `"therapist-user-1"` as therapistId
   - If routes expect `therapists.id`: Use `"test-therapist-1"` as therapistId
   - Verify FK chain: users → therapists → availability

### Medium Priority

4. **Schema Consolidation**:
   - Why do we have TWO schema packages (`@karematch/types` and `@karematch/data`)?
   - Should deprecate one to avoid confusion
   - Document canonical schema location

5. **Test All Fixed Routes**:
   ```bash
   npx vitest run tests/appointments-routes.test.ts
   ```

### Validation

6. **Run Ralph Verification**:
   ```bash
   cd /Users/tmac/karematch
   # After tests pass, verify no regressions
   ```

## Evidence & Artifacts

**Test Output** (before fixes):
```
Failed to seed test data: column "password" of relation "users" does not exist
❯ 20 failed | 0 passed | 54 skipped
```

**Test Output** (after fixes):
```
# No "Failed to seed" error!
❯ 20 failed | 5 passed | 54 skipped
```

**Modified Files**:
- `/Users/tmac/karematch/tests/appointments-routes.test.ts`

## Lessons Learned

1. **Always Check Schema Sources**: Multiple schema definitions (types vs data packages) can cause confusion

2. **Test Data Seeding First**: Verify test fixtures load before debugging route logic

3. **Async Initialization Matters**: Services with lazy loading need `waitForInit()` in tests

4. **FK Relationships Are Critical**: User IDs vs profile IDs confusion is easy to introduce

## Risks & Blockers

**Risks**:
- Schema drift between `@karematch/types` and `@karematch/data`
- Other tests may have same schema issue
- ID/FK mismatches may exist in production code

**Blockers**:
- None (can continue debugging in next session)

## Team Handoff

**For Next Developer**:
1. Start by running the test to see current state
2. Add debug logging to route handlers (line 1422, 1660 in routes.ts)
3. Log what `therapistId` value routes receive vs what they query for
4. Adjust test data or route logic to align IDs

**Quick Win**:
The `waitForInit()` and `passwordHash` fixes are solid improvements that will help all future tests.

## References

- [Task Prompt](/Users/tmac/Vaults/AI_Orchestrator/NEXT-SESSION-APPOINTMENT-ROUTES.md)
- [Route Definitions](/Users/tmac/karematch/services/appointments/src/routes.ts)
- [Test File](/Users/tmac/karematch/tests/appointments-routes.test.ts)
- [Schema (Actual)](/Users/tmac/karematch/data/schema/identity.ts)
- [Schema (Outdated)](/Users/tmac/karematch/packages/types/src/database/schema.ts)

---

**Session Duration**: ~90 minutes
**Commits**: 0 (waiting for full fix before committing)
**Next Session**: Continue ID/FK debugging to get tests passing
