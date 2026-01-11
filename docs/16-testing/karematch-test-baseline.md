# KareMatch Test Baseline

**Date**: 2026-01-06
**Environment**: Local dev (after Docker rebuild)
**Purpose**: Establish baseline for Phase 0 BugFix agent calibration

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| TypeScript Errors | 9 | ❌ Failing |
| ESLint Errors | 4 | ❌ Failing |
| ESLint Warnings | 4 | ⚠️ Warning |
| Test Files Failed | 11 | ❌ Failing |
| Test Cases Failed | 71 | ❌ Failing |
| Test Cases Passed | 758 | ✅ Passing |
| Test Cases Skipped | 781 | ⏭️ Skipped |

---

## TypeScript Errors (9 total)

**Package**: `@karematch/audit-logger`
**File**: `services/audit-logger/src/audit-logger.ts`
**Root Cause**: Drizzle ORM type incompatibilities

### Error Details

All 9 errors are variations of `TS2769: No overload matches this call` related to Drizzle column type mismatches:

1. Line 116: `eq(auditLogs.userId, userId)` - Column type mismatch
2. Line 120: `eq(auditLogs.action, action)` - Column type mismatch
3. Line 124: `gte(auditLogs.createdAt, startDate)` - Column type mismatch
4. Line 128: `lte(auditLogs.createdAt, endDate)` - Column type mismatch
5. Line 132: `eq(auditLogs.resourceType, resourceType)` - Column type mismatch
6. Line 136: `eq(auditLogs.resourceId, resourceId)` - Column type mismatch
7. Line 143: `SQL<unknown> | undefined` type mismatch
8. Line 147: `desc()` overload mismatch
9. Line 147: `createdAt` column type mismatch

**Impact**: Compilation fails for audit-logger package, but workspace continues (turbo cache)

**Complexity**: Medium (requires Drizzle API understanding)

---

## ESLint Errors (4 total)

**Package**: `karematch-core-web`
**File**: `web/src/pages/therapist-dashboard/schedule.tsx`
**Root Cause**: Accessibility violations (jsx-a11y)

### Error Details

1. **Line 294** - Click handler without keyboard listener
   - Rule: `jsx-a11y/click-events-have-key-events`
   - Element: Interactive div without keyboard support

2. **Line 294** - Non-native interactive element
   - Rule: `jsx-a11y/no-static-element-interactions`
   - Element: Div used as button without proper ARIA

3. **Line 320** - Click handler without keyboard listener
   - Rule: `jsx-a11y/click-events-have-key-events`
   - Element: Interactive div without keyboard support

4. **Line 320** - Non-native interactive element
   - Rule: `jsx-a11y/no-static-element-interactions`
   - Element: Div used as button without proper ARIA

**Impact**: Lint fails with exit code 1 (blocks CI if enforced)

**Complexity**: Trivial (add `onKeyDown` handlers + `role="button"`)

---

## ESLint Warnings (4 total)

**Package**: `karematch-core-web`

1. **web/src/pages/therapist-dashboard/index.tsx:46** - Import order violation
2. **web/src/pages/therapist-dashboard/availability.tsx:2** - Unused import `startOfWeek`
3. **web/src/pages/therapist-dashboard/availability.tsx:16** - Unused import `Link`
4. **web/src/pages/therapist-dashboard/availability.tsx:22** - Import order violation

**Impact**: Cosmetic (--max-warnings=0 blocks build)

**Complexity**: Trivial (auto-fixable with `npm run lint -- --fix`)

---

## Test Failures (71 total)

### Failed Test Files (11 files)

1. `tests/unit/server/services/appointmentStatusMachine.test.ts` (2 failures)
2. `tests/unit/server/services/appointmentWorkflow.observability.test.ts` (9 failures)
3. `tests/unit/server/services/therapistMatcher.boundaries.test.ts` (7 failures)
4. `tests/unit/server/services/therapistMatcher.invariants.test.ts` (1 failure)
5. *(7 more files with detailed failures not shown in summary)*

### Sample Failures

#### appointmentStatusMachine.test.ts (2 failures)

1. "should throw error for non-existent appointment"
   - Expected error not thrown

2. "should preserve error details in InvalidTransitionError"
   - Error details not preserved

#### appointmentWorkflow.observability.test.ts (9 failures)

1. "should emit structured logs with correlation_id on success path"
2. "should use same correlation_id across all logs in single workflow execution"
3. "should generate different correlation_id for each workflow execution"
4. "should include correlation_id in audit trail metadata"
5. "should complete workflow successfully even if logger.info throws"
6. "should complete workflow successfully even if logger throws on every call"
7. "should not affect warning classification when logging fails"
8. "should maintain Phase 3 invariant: success=true when only warnings exist"
9. "should emit workflow_start and workflow_complete logs"

**Pattern**: Observability/logging infrastructure not working as expected

#### therapistMatcher.boundaries.test.ts (7 failures)

1. "should filter by location before returning results"
2. "should filter by minimum score threshold (30)"
3. "should persist matches only for first batch (offset=0)"
4. "should NOT persist matches for offset > 0"
5. "should return identical results for identical inputs (workflow determinism)"
6. "should sort results by score descending"
7. *(1 more)*

**Pattern**: Business logic boundary violations

#### therapistMatcher.invariants.test.ts (1 failure)

1. "should provide reasons for all points awarded"

**Pattern**: Match scoring logic incomplete

---

## Test Baseline Interpretation

### Passing Tests (758)

- Core functionality appears to work
- 758/1615 (47%) tests passing is reasonable for active development
- Skipped tests (781) suggest intentional test stubs or disabled tests

### Failed Tests (71)

**Categories**:
1. **Observability** (~9 tests) - Logging/tracing infrastructure issues
2. **State Machine** (~2 tests) - Error handling gaps
3. **Business Logic** (~10 tests) - Matcher boundary violations
4. **Stub Tests** (~50 estimated) - Tests awaiting implementation (from TODO-stub-tests.md)

---

## Recommendations for Phase 0

### Priority 1: Trivial Bugs (Quick Wins)

1. **ESLint warnings** (4 warnings)
   - Auto-fixable with `--fix`
   - <5 minutes total

2. **ESLint accessibility errors** (4 errors)
   - Add keyboard handlers + ARIA roles
   - ~10-15 minutes each = ~1 hour total

### Priority 2: Medium Bugs

3. **Drizzle type errors** (9 errors in audit-logger)
   - Requires understanding Drizzle column API changes
   - ~1-2 hours total (all in same file)

### Priority 3: Complex Bugs (Later)

4. **Observability failures** (9 tests)
   - Correlation ID infrastructure missing
   - Requires architecture changes

5. **Business logic failures** (10+ tests)
   - Matcher boundary enforcement
   - Requires domain knowledge

---

## Success Criteria for Phase 0

**Minimum Viable**:
- ✅ ESLint warnings fixed (0 warnings)
- ✅ ESLint errors fixed (0 errors)
- ✅ TypeScript compiles (0 TS errors)
- ✅ No new test failures introduced

**Stretch Goal**:
- ✅ 5-10 test failures fixed (bring 71 down to <65)

---

## Commands for Re-Baseline

```bash
cd /Users/tmac/karematch

# TypeScript
npm run check 2>&1 | tee karematch-typecheck-baseline.txt

# ESLint
npm run lint 2>&1 | tee karematch-lint-baseline.txt

# Tests
npx vitest run 2>&1 | tee karematch-test-baseline.txt
```

---

## Appendix: Raw Output Excerpts

### TypeScript Check Output

```
@karematch/audit-logger:check: src/audit-logger.ts(116,26): error TS2769: No overload matches this call.
@karematch/audit-logger:check: src/audit-logger.ts(120,26): error TS2769: No overload matches this call.
[... 7 more similar errors ...]
Tasks: 10 successful, 16 total
```

### ESLint Output

```
karematch-core-web:lint: ✖ 8 problems (4 errors, 4 warnings)
karematch-core-web:lint:   0 errors and 4 warnings potentially fixable with the `--fix` option.
```

### Test Output

```
Test Files  11 failed | 32 passed | 29 skipped (72)
     Tests  71 failed | 758 passed | 781 skipped (1615)
```

---

**Baseline Established**: 2026-01-06
**Next Baseline**: After Phase 0 completion (compare deltas)
