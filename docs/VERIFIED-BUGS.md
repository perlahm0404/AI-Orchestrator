# Verified Bugs for Phase 0 Calibration

**Date**: 2026-01-06
**Source**: karematch-test-baseline.md
**Status**: VERIFIED - All bugs confirmed present in codebase
**Total**: 10 bugs (4 trivial, 4 medium, 2 complex)

---

## Selection Criteria

- ✅ **Real**: Confirmed by actual test/lint/typecheck runs
- ✅ **Unfixed**: Still present in codebase as of 2026-01-06
- ✅ **Verifiable**: Can confirm fix with automated checks (Ralph-ready)
- ✅ **Variety**: Mix of trivial/medium/complex for calibration
- ✅ **Independent**: Each bug can be fixed in isolation

---

## Trivial Bugs (4 total)

### BUG-T1: Unused Import - startOfWeek

**File**: `web/src/pages/therapist-dashboard/availability.tsx:2`
**Type**: ESLint warning
**Rule**: `unused-imports/no-unused-imports`

**Current Code**:
```typescript
import { startOfWeek } from 'date-fns'; // ← Imported but never used
```

**Fix**:
Remove the unused import or use it

**Verification**:
```bash
npm run lint -- web/src/pages/therapist-dashboard/availability.tsx
# Should show 0 unused-imports warnings
```

**Estimate**: <2 minutes
**Lines Changed**: 1
**Files Changed**: 1
**Complexity**: Trivial

---

### BUG-T2: Unused Import - Link

**File**: `web/src/pages/therapist-dashboard/availability.tsx:16`
**Type**: ESLint warning
**Rule**: `unused-imports/no-unused-imports`

**Current Code**:
```typescript
import { Link } from 'react-router-dom'; // ← Imported but never used
```

**Fix**:
Remove the unused import or use it

**Verification**:
```bash
npm run lint -- web/src/pages/therapist-dashboard/availability.tsx
# Should show 0 unused-imports warnings
```

**Estimate**: <2 minutes
**Lines Changed**: 1
**Files Changed**: 1
**Complexity**: Trivial

---

### BUG-T3: Import Order - endorsements before schedule

**File**: `web/src/pages/therapist-dashboard/index.tsx:46`
**Type**: ESLint warning
**Rule**: `import/order`

**Current Code**:
```typescript
import { SchedulePage } from '@/pages/therapist-dashboard/schedule';
import { EndorsementsPage } from '@/pages/therapist-dashboard/endorsements'; // ← Wrong order
```

**Fix**:
Reorder imports alphabetically or by import/order rules

**Verification**:
```bash
npm run lint -- web/src/pages/therapist-dashboard/index.tsx
# Should show 0 import/order warnings
```

**Estimate**: <2 minutes
**Lines Changed**: 2 (swap lines)
**Files Changed**: 1
**Complexity**: Trivial

---

### BUG-T4: Import Order - AppointmentsList before AvailabilityCalendar

**File**: `web/src/pages/therapist-dashboard/availability.tsx:22`
**Type**: ESLint warning
**Rule**: `import/order`

**Current Code**:
```typescript
import { AvailabilityCalendar } from '@/components/scheduling/AvailabilityCalendar';
import { AppointmentsList } from '@/components/scheduling/AppointmentsList'; // ← Wrong order
```

**Fix**:
Reorder imports alphabetically

**Verification**:
```bash
npm run lint -- web/src/pages/therapist-dashboard/availability.tsx
# Should show 0 import/order warnings
```

**Estimate**: <2 minutes
**Lines Changed**: 2 (swap lines)
**Files Changed**: 1
**Complexity**: Trivial

---

## Medium Bugs (4 total)

### BUG-M1: Missing Keyboard Handler - Interactive Div (line 294)

**File**: `web/src/pages/therapist-dashboard/schedule.tsx:294`
**Type**: ESLint error
**Rules**: `jsx-a11y/click-events-have-key-events`, `jsx-a11y/no-static-element-interactions`

**Current Code**:
```tsx
<div onClick={handleClick} className="...">
  {/* Interactive content */}
</div>
```

**Fix**:
```tsx
<div
  onClick={handleClick}
  onKeyDown={(e) => e.key === 'Enter' && handleClick(e)}
  role="button"
  tabIndex={0}
  className="..."
>
  {/* Interactive content */}
</div>
```

**Verification**:
```bash
npm run lint -- web/src/pages/therapist-dashboard/schedule.tsx
# Should show 0 jsx-a11y errors at line 294
```

**Estimate**: ~10 minutes
**Lines Changed**: ~5 (add props)
**Files Changed**: 1
**Complexity**: Medium (requires understanding event handlers)

---

### BUG-M2: Missing Keyboard Handler - Interactive Div (line 320)

**File**: `web/src/pages/therapist-dashboard/schedule.tsx:320`
**Type**: ESLint error
**Rules**: `jsx-a11y/click-events-have-key-events`, `jsx-a11y/no-static-element-interactions`

**Current Code**:
```tsx
<div onClick={handleClick} className="...">
  {/* Interactive content */}
</div>
```

**Fix**:
Same as BUG-M1 (add keyboard handler + ARIA)

**Verification**:
```bash
npm run lint -- web/src/pages/therapist-dashboard/schedule.tsx
# Should show 0 jsx-a11y errors at line 320
```

**Estimate**: ~10 minutes
**Lines Changed**: ~5 (add props)
**Files Changed**: 1
**Complexity**: Medium

---

### BUG-M3: Drizzle Type Mismatch - eq(userId)

**File**: `services/audit-logger/src/audit-logger.ts:116`
**Type**: TypeScript error TS2769
**Root Cause**: Drizzle ORM column type incompatibility

**Current Code**:
```typescript
const filters = [eq(auditLogs.userId, userId)];
```

**Error**:
```
TS2769: No overload matches this call.
Argument of type 'PgColumn<...>' is not assignable to parameter of type 'Column<...>'
```

**Fix**:
Update to use Drizzle 0.39 API (likely needs explicit type casting or column reference)

**Verification**:
```bash
npm run check -- --filter=@karematch/audit-logger
# Should show 0 TS errors in audit-logger.ts
```

**Estimate**: ~30-60 minutes (research Drizzle API changes)
**Lines Changed**: ~15-20 (all eq/gte/lte calls in file)
**Files Changed**: 1
**Complexity**: Medium (requires Drizzle ORM knowledge)

---

### BUG-M4: Test Failure - Appointment Error Handling

**File**: `tests/unit/server/services/appointmentStatusMachine.test.ts`
**Type**: Test failure
**Test**: "should throw error for non-existent appointment"

**Symptom**:
Test expects `AppointmentNotFoundError` but error is not thrown

**Root Cause**:
State machine not validating appointment existence before state transitions

**Fix**:
Add appointment existence check in state machine before processing transitions

**Verification**:
```bash
npx vitest run tests/unit/server/services/appointmentStatusMachine.test.ts
# Should show 2/2 tests passing
```

**Estimate**: ~45-60 minutes
**Lines Changed**: ~10-15
**Files Changed**: 1-2 (state machine + possibly repository)
**Complexity**: Medium (requires understanding state machine)

---

## Complex Bugs (2 total - for Phase 1)

### BUG-C1: Missing Correlation ID Infrastructure

**Files**: Multiple (observability infrastructure)
**Type**: Test failures (9 tests)
**Tests**: `appointmentWorkflow.observability.test.ts`

**Symptom**:
All correlation ID tests failing - infrastructure not implemented

**Root Cause**:
- Correlation ID generation missing
- Correlation ID propagation across logs not implemented
- Audit trail metadata missing correlation context

**Fix Scope**:
- Add correlation ID generation to workflow entry points
- Thread correlation ID through logger calls
- Update audit trail schema/inserts

**Verification**:
```bash
npx vitest run tests/unit/server/services/appointmentWorkflow.observability.test.ts
# Should show 9/9 correlation ID tests passing
```

**Estimate**: ~3-4 hours
**Lines Changed**: ~50-100
**Files Changed**: 3-5 (workflow, logger, audit-logger, types)
**Complexity**: Complex (architecture change)

**Phase**: Phase 1 (too complex for Phase 0 calibration)

---

### BUG-C2: Therapist Matcher Boundary Violations

**Files**: `services/matching/src/therapist-matcher.ts`
**Type**: Test failures (7 tests)
**Tests**: `therapistMatcher.boundaries.test.ts`

**Symptom**:
- Location filtering not applied
- Score threshold (30) not enforced
- Persistence logic incorrect for offset batches
- Results not sorted by score

**Root Cause**:
Boundary enforcement missing in matcher pipeline

**Fix Scope**:
- Add location filter before returning results
- Add minimum score filter (threshold = 30)
- Fix persistence logic (only offset=0)
- Add score-based sorting

**Verification**:
```bash
npx vitest run tests/unit/server/services/therapistMatcher.boundaries.test.ts
# Should show 7/7 boundary tests passing
```

**Estimate**: ~2-3 hours
**Lines Changed**: ~40-60
**Files Changed**: 1-2 (matcher + possibly types)
**Complexity**: Complex (requires domain knowledge)

**Phase**: Phase 1 (too complex for Phase 0 calibration)

---

## Phase 0 Bug Selection (Recommended Order)

### Sprint 1: Trivial Wins (All 4 trivial bugs)

**Goal**: Validate workflow with zero-risk fixes

1. BUG-T1: Remove unused import `startOfWeek`
2. BUG-T2: Remove unused import `Link`
3. BUG-T3: Fix import order (endorsements)
4. BUG-T4: Fix import order (AppointmentsList)

**Total Estimate**: <10 minutes
**Expected Outcome**: ESLint warnings drop from 4 → 0

---

### Sprint 2: Accessibility Fixes (2 medium bugs)

**Goal**: Validate medium complexity fixes

5. BUG-M1: Add keyboard handler to interactive div (line 294)
6. BUG-M2: Add keyboard handler to interactive div (line 320)

**Total Estimate**: ~20 minutes
**Expected Outcome**: ESLint errors drop from 4 → 0, lint passes

---

### Sprint 3: Type Safety (1 medium bug)

**Goal**: Validate TypeScript fixes

7. BUG-M3: Fix Drizzle type mismatches in audit-logger

**Total Estimate**: ~30-60 minutes
**Expected Outcome**: TypeScript compilation passes (0 TS errors)

---

### Sprint 4: Business Logic (1 medium bug)

**Goal**: Validate test-driven fixes

8. BUG-M4: Fix appointment error handling in state machine

**Total Estimate**: ~45-60 minutes
**Expected Outcome**: 2 more tests pass

**Phase 0 Exit Criteria**: 8 bugs fixed, 0 regressions

---

## Metrics Tracking

| Bug ID | Complexity | Estimated Time | Files | Lines | Status |
|--------|-----------|----------------|-------|-------|--------|
| BUG-T1 | Trivial | 2 min | 1 | 1 | 🔴 Not Started |
| BUG-T2 | Trivial | 2 min | 1 | 1 | 🔴 Not Started |
| BUG-T3 | Trivial | 2 min | 1 | 2 | 🔴 Not Started |
| BUG-T4 | Trivial | 2 min | 1 | 2 | 🔴 Not Started |
| BUG-M1 | Medium | 10 min | 1 | 5 | 🔴 Not Started |
| BUG-M2 | Medium | 10 min | 1 | 5 | 🔴 Not Started |
| BUG-M3 | Medium | 45 min | 1 | 18 | 🔴 Not Started |
| BUG-M4 | Medium | 60 min | 2 | 12 | 🔴 Not Started |
| BUG-C1 | Complex | 3-4 hrs | 5 | 75 | ⏭️ Phase 1 |
| BUG-C2 | Complex | 2-3 hrs | 2 | 50 | ⏭️ Phase 1 |

**Total (Phase 0)**: 8 bugs, ~2.5 hours estimated

---

## Verification Commands

### Full Re-Check After Fixes

```bash
cd /Users/tmac/karematch

# Should pass with 0 errors/warnings
npm run lint

# Should pass with 0 TS errors
npm run check

# Should pass with 0 new failures
npx vitest run

# Summary
echo "✅ Lint: $(npm run lint 2>&1 | grep -c 'error')"
echo "✅ Types: $(npm run check 2>&1 | grep -c 'error TS')"
echo "✅ Tests: $(npx vitest run 2>&1 | grep 'Tests' | grep failed)"
```

---

## Notes

- **All bugs verified**: Confirmed present as of 2026-01-06 baseline
- **Ralph-ready**: All bugs have automated verification (no manual checking required)
- **Complexity distribution**: 4 trivial (50%), 4 medium (50%), 2 complex (deferred)
- **Phase 0 target**: Fix 8 bugs in ~2.5 hours total
- **Phase 1 target**: Fix remaining 2 complex bugs in ~5-7 hours

---

**Last Updated**: 2026-01-06
**Next Review**: After Phase 0 Sprint 1 completion
