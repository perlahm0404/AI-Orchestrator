# Next Session: Fix Appointment Routes (20 Test Failures)

**Priority**: 🔥 HIGH (QA Team work)
**Estimated Time**: 1-2 hours
**Expected Impact**: -20 test failures (70 → 50)

---

## CONTEXT: You are continuing QA Team work on KareMatch

**Previous Session**: Fixed workflow error handling bug (4 failures eliminated)
**Current State**: 70 test failures remaining, lint ✅ passing, typecheck ✅ passing
**Branch**: `main` at `/Users/tmac/karematch`

**Read these files FIRST** (memory protocol):
1. `/Users/tmac/Vaults/AI_Orchestrator/STATE.md` - Current build state
2. `/Users/tmac/Vaults/AI_Orchestrator/sessions/2026-01-06-qa-team-workflow-fix.md` - Previous session handoff

---

## YOUR TASK: Fix Appointment Routes API (20 failures)

### Problem Statement

The `/api/public/*` appointment routes are returning **404 "Not Found"** instead of the expected responses. Tests in `tests/appointments-routes.test.ts` are failing because API endpoints either:
1. Don't exist (routes not registered)
2. Are registered with wrong paths
3. Are blocked by middleware
4. Handler functions are missing

### Failing Tests (20 total)

**Test File**: `/Users/tmac/karematch/tests/appointments-routes.test.ts`
- **Status**: 5 passing, 20 failing, 54 skipped
- **Expected**: 25 passing (aim for 100% on public routes)

**Sample Failures**:
```
❌ GET /api/public/therapist/:therapistId/availability
   Expected: 200 with { slots: [...] }
   Actual:   404 "Not Found"

❌ GET /api/public/therapists/:therapistId/upcoming-slots
   Expected: 200 with next 14 days of slots
   Actual:   404 "Not Found"

❌ GET /api/public/therapists/:therapistId/available-dates
   Expected: 200 with available dates array
   Actual:   404 "Not Found"

❌ POST /api/public/book
   Expected: 201 with { appointment: {...} }
   Actual:   404 "Not Found"

❌ GET /api/public/appointment/:id
   Expected: 200 with appointment details
   Actual:   404 "Not Found"
   Error message: "Not found" (should be "Appointment not found")
```

### Expected Endpoints

Based on test file, these routes MUST exist:

| Method | Path | Handler | Expected Response |
|--------|------|---------|-------------------|
| GET | `/api/public/therapist/:therapistId/availability` | Get slots for date | `{ slots: TimeSlot[] }` |
| GET | `/api/public/therapists/:therapistId/upcoming-slots` | Next 14 days | `{ slots: TimeSlot[] }` |
| GET | `/api/public/therapists/:therapistId/available-dates` | Next 30 days | `{ dates: string[] }` |
| POST | `/api/public/book` | Create appointment | `201 { appointment: {...} }` |
| GET | `/api/public/appointment/:id` | Get appointment | `200 { appointment: {...} }` |

---

## STEP-BY-STEP INVESTIGATION PLAN

### Phase 1: Locate Route Definitions (15 min)

1. **Find Express app setup**
   ```bash
   cd /Users/tmac/karematch
   find api -name "*.ts" -type f | xargs grep -l "express()"
   # Likely: api/src/index.ts or api/src/app.ts
   ```

2. **Find public routes file**
   ```bash
   find api -name "*public*" -o -name "*routes*" | grep -v node_modules
   # Likely locations:
   # - api/src/routes/public.ts
   # - api/src/routes/appointments/public.ts
   # - api/src/routes/public/appointments.ts
   ```

3. **Search for route registrations**
   ```bash
   grep -r "/api/public" api/src --include="*.ts"
   grep -r "router.get.*availability" api/src --include="*.ts"
   grep -r "router.post.*book" api/src --include="*.ts"
   ```

### Phase 2: Check If Routes Exist (15 min)

**Scenario A: Routes don't exist at all**
- Create `/Users/tmac/karematch/api/src/routes/public/appointments.ts`
- Implement all 5 endpoints
- Register router in main app

**Scenario B: Routes exist but not registered**
- Find the router definition
- Add `app.use('/api/public', publicRouter)` in main app
- Verify middleware order (auth should not block public routes)

**Scenario C: Routes exist with wrong paths**
- Fix path mismatches (e.g., `/therapist/:id` vs `/therapists/:id`)
- Update route definitions to match test expectations

### Phase 3: Implement/Fix Handlers (30-45 min)

For **each missing/broken endpoint**, ensure:

1. **Route registration**:
   ```typescript
   router.get('/therapist/:therapistId/availability', async (req, res) => {
     // Handler implementation
   });
   ```

2. **Handler implementation**:
   - Use existing service functions from `@karematch/appointments`
   - Return correct status codes (200, 201, 404, 400)
   - Return correct data shape matching tests

3. **Error handling**:
   - 404 for not found (with specific message)
   - 400 for validation errors
   - Consistent error format

### Phase 4: Verify Fixes (15 min)

1. **Run test file**:
   ```bash
   cd /Users/tmac/karematch
   npx vitest run tests/appointments-routes.test.ts
   # Target: 25/25 passing
   ```

2. **Run full test suite**:
   ```bash
   npx vitest run 2>&1 | tail -20
   # Target: 50 failures (down from 70)
   ```

3. **Verify no regressions**:
   ```bash
   npm run lint   # Should still pass
   npm run check  # Should still pass
   ```

---

## IMPLEMENTATION HINTS

### Hint 1: Check Existing Appointment Service

The business logic likely already exists in:
```
/Users/tmac/karematch/services/appointments/src/
```

Look for functions like:
- `getAvailability(therapistId, date)`
- `getUpcomingSlots(therapistId, days)`
- `getAvailableDates(therapistId, days)`
- `createAppointment(data)`
- `getAppointmentById(id)`

**Your job**: Wire these to Express routes, don't reimplement logic.

### Hint 2: Route Path Inconsistency

Notice the inconsistency in test expectations:
- `/api/public/therapist/:id/availability` (singular)
- `/api/public/therapists/:id/upcoming-slots` (plural)

This suggests the routes may have been partially implemented with inconsistent naming. Check both patterns.

### Hint 3: Middleware Order Matters

Public routes should NOT require authentication. Ensure:
```typescript
// CORRECT order
app.use('/api/public', publicRouter);  // No auth middleware
app.use('/api/therapist', authMiddleware, therapistRouter);  // Auth required

// WRONG order (would block public routes)
app.use(authMiddleware);  // Blocks everything
app.use('/api/public', publicRouter);  // Never reached
```

### Hint 4: Test File is Your Spec

The test file shows exactly what each endpoint should do:
```typescript
// Example from tests/appointments-routes.test.ts
const response = await request(app)
  .get(`/api/public/therapist/${therapistId}/availability`)
  .query({ date: '2024-03-15' })
  .expect(200);

expect(response.body.slots).toBeDefined();
expect(response.body.slots).toHaveLength(2);
```

Match this contract exactly.

---

## DELIVERABLES

### Required
1. ✅ All 5 public appointment endpoints implemented/fixed
2. ✅ Test file passing: `tests/appointments-routes.test.ts` (25/25)
3. ✅ No regressions (lint, typecheck, other tests unchanged)
4. ✅ Session handoff document created

### Success Criteria
- **Test count**: 70 failures → 50 failures (-20)
- **Passing tests**: 759 → 779 (+20)
- **Route tests**: 5/25 → 25/25 (+20)

---

## SAFETY CHECKS

Before marking session complete:

1. **Lint still passes**:
   ```bash
   npm run lint  # 0 errors, 0 warnings
   ```

2. **Typecheck still passes**:
   ```bash
   npm run check  # All packages pass
   ```

3. **Target test file passes**:
   ```bash
   npx vitest run tests/appointments-routes.test.ts
   # 25 passed, 0 failed
   ```

4. **Full suite improved**:
   ```bash
   npx vitest run 2>&1 | grep "Tests"
   # Should show ~50 failures (down from 70)
   ```

---

## GOVERNANCE: QA Team Contract

You are operating under **QA Team autonomy contract**:
- ✅ **Allowed**: Fix existing routes, modify handlers, add missing routes
- ✅ **Allowed**: Use existing service functions
- ❌ **Forbidden**: Add new dependencies
- ❌ **Forbidden**: Modify database schema
- ❌ **Forbidden**: Change existing API behavior (only add missing routes)
- ❌ **Forbidden**: Use `--no-verify` git flag

**Limits**:
- Max 100 lines added per file
- Max 5 files changed
- Must halt on Ralph BLOCKED (run Ralph via: `cd /Users/tmac/Vaults/AI_Orchestrator && python3 -m ralph.engine verify /Users/tmac/karematch`)

---

## EXAMPLE ROUTE IMPLEMENTATION

```typescript
// File: api/src/routes/public/appointments.ts
import { Router } from 'express';
import { appointmentService } from '@karematch/appointments';

const router = Router();

// GET /api/public/therapist/:therapistId/availability
router.get('/therapist/:therapistId/availability', async (req, res) => {
  try {
    const { therapistId } = req.params;
    const { date } = req.query;

    const slots = await appointmentService.getAvailability(
      therapistId,
      date as string
    );

    res.json({ slots });
  } catch (error) {
    console.error('Error fetching availability:', error);
    res.status(500).json({ error: 'Failed to fetch availability' });
  }
});

// POST /api/public/book
router.post('/book', async (req, res) => {
  try {
    const appointment = await appointmentService.createAppointment(req.body);
    res.status(201).json({ appointment });
  } catch (error) {
    if (error.message.includes('not found')) {
      return res.status(404).json({ error: error.message });
    }
    if (error.message.includes('already booked')) {
      return res.status(409).json({ error: error.message });
    }
    res.status(400).json({ error: error.message });
  }
});

export default router;
```

---

## COMMIT MESSAGE TEMPLATE

```
fix(appointments): Implement missing public appointment API routes

PROBLEM:
Public appointment routes were returning 404 because routes were either
not registered or implemented with wrong paths. This caused 20 test
failures in appointments-routes.test.ts.

Missing/broken endpoints:
- GET /api/public/therapist/:id/availability
- GET /api/public/therapists/:id/upcoming-slots
- GET /api/public/therapists/:id/available-dates
- POST /api/public/book
- GET /api/public/appointment/:id

SOLUTION:
[Describe what you did - created routes file, fixed paths, etc.]

IMPACT:
- 20 test failures fixed (appointments-routes.test.ts)
- All public appointment endpoints now working
- No breaking changes to existing APIs

FILES CHANGED:
[List files you modified]

TESTS:
✅ appointments-routes.test.ts (25/25 passing, was 5/25)
✅ All other tests unchanged
✅ Total failures: 70 → 50

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## TROUBLESHOOTING

### Issue: Routes still return 404 after registration
**Check**: Middleware order, ensure public router comes before auth middleware

### Issue: "Cannot find module @karematch/appointments"
**Check**: Import path, verify service exports, check package.json workspaces

### Issue: TypeScript errors in route handlers
**Check**: Service function signatures, verify types match test expectations

### Issue: Tests pass but real API still 404s
**Check**: You're in test mode - that's expected! Routes work in test server.

---

## FINAL CHECKLIST

Before ending session:

- [ ] Located route files (or determined they don't exist)
- [ ] Implemented/fixed all 5 public appointment endpoints
- [ ] Verified routes registered in Express app
- [ ] Test file passing: `appointments-routes.test.ts` (25/25)
- [ ] Lint passing: `npm run lint`
- [ ] Typecheck passing: `npm run check`
- [ ] Full suite improved: 70 → ~50 failures
- [ ] Session handoff created
- [ ] Files modified listed
- [ ] Commit message drafted (but NOT committed yet)

---

**START HERE**:
1. Read STATE.md and previous session handoff
2. Begin Phase 1: Locate route definitions
3. Follow the step-by-step plan above
4. Ask for human approval before committing changes

**Good luck!** This is a high-value fix that will eliminate 20 test failures in one session. 🎯
