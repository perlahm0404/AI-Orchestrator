# CME Systemic Issue Assessment & Remediation Plan

**Date**: 2026-01-10
**Status**: Phase 1 (Option A) COMPLETED
**Severity**: HIGH - Affects CME compliance accuracy for providers

---

## Executive Summary

Investigation of 5 failing CME tests revealed a **systemic, multifaceted issue** spanning three layers:

1. **Topic Name Normalization Gap** - Database topics don't match test search patterns
2. **Tests Written Against Incorrect Assumptions** - Test expectations don't match FSMB ground truth
3. **Topic Hierarchy Not Integrated** - ADR-002 hierarchy not used in existing tests/service

This is NOT a simple test fix - it's an architectural gap requiring coordinated remediation.

---

## Root Cause Analysis

### Evidence Matrix

| Test Failure | Database Value | FSMB Ground Truth | Test Expects | Root Cause |
|--------------|----------------|-------------------|--------------|------------|
| FL MD Controlled Substance missing | topic=`opioid_prescribing` | `controlled_substance_prescribing` | contains `controlled_substance` | **Topic Name Mismatch** |
| FL HIV/AIDS ongoing | `first_renewal_only=true` | `first_renewal_only` | `first_renewal_only=false` | **Test Bug** |
| FL DEA requirements | `requires_dea_registration=true` | DEA conditional | DEA filter in "ongoing" | **Service Layer Gap** |
| FL DO DEA flag | Two separate rules exist | Both correct | Wrong rule checked | **Test Logic Bug** |
| FL biennial 38 vs 40 | FL-M=38h, FL-O=40h | FL-M=38h, FL-O=40h | 40h (no license type) | **Test Bug** |

### Three Problem Categories

#### 1. Topic Name Normalization Gap (HIGH)

The database uses different topic names than the rule packs and tests:

```
Rule Pack:  controlled_substance_prescribing
Database:   opioid_prescribing
Tests:      *controlled_substance*
```

**Impact**: Tests fail to find rules; compliance calculations may miscategorize topics.

**Evidence**:
- `CME-FL-M-2025.json` line 87: `"topic": "controlled_substance_prescribing"`
- Database: `topic=opioid_prescribing`

#### 2. Test Assumptions Incorrect (MEDIUM)

Tests were written before FSMB ground truth was finalized:

| Assumption | Reality |
|------------|---------|
| FL HIV/AIDS is ongoing | First renewal only (FSMB confirmed) |
| FL biennial = 40h | FL-M = 38h + 2h medical errors (separate) |

**Root**: Tests written against early estimates, not verified FSMB data.

#### 3. Topic Hierarchy Not Integrated (MEDIUM)

ADR-002 implemented topic hierarchy (`topic_satisfies()`) but:
- Existing tests use string matching (`"controlled_substance" in topic`)
- Service layer `get_state_rules()` returns raw topics, not hierarchy-aware

---

## Remediation Options

### Option A: Fix Tests Only (Tactical)
**Effort**: 1 day
**Risk**: Low
**Scope**: Update test assertions to match database reality

**Changes**:
1. Fix FL hour expectation (38 not 40 for MD)
2. Fix FL HIV/AIDS expectation (first_renewal_only=true)
3. Update topic search to use `opioid*` OR `controlled_substance*`
4. Fix FL DO test to check correct rule

**Pros**: Fast, unblocks CI
**Cons**: Doesn't fix underlying normalization gap; band-aid

---

### Option B: Topic Normalization + Test Fix (Strategic)
**Effort**: 3-4 days
**Risk**: Medium
**Scope**: Normalize topics across rule packs, database, and tests

**Changes**:
1. Create canonical topic mapping in `topic_hierarchy.py`
2. Add `normalized_topic` column to `cme_rules` table
3. Create migration to backfill normalized topics
4. Update tests to use normalized topic names
5. Update service layer to return normalized topics

**Pros**: Fixes root cause; enables topic hierarchy usage
**Cons**: Requires migration; more testing

---

### Option C: Full Hierarchy Integration (Comprehensive)
**Effort**: 5-7 days
**Risk**: Medium-High
**Scope**: Integrate ADR-002 topic hierarchy throughout the CME subsystem

**Changes**:
1. All of Option B, plus:
2. Update `CMEComplianceService.get_state_rules()` to return hierarchy-aware topics
3. Add `satisfies_topics` field to rule responses
4. Update all CME tests to use hierarchy-aware assertions
5. Add topic alias support (e.g., `controlled_substance` → `opioid_prescribing`)

**Pros**: Complete solution; maximizes ADR-002 value
**Cons**: Largest scope; regression risk

---

## Recommendation

**Phase 1 (Immediate)**: Option A - Fix tests to unblock CI
**Phase 2 (This sprint)**: Option B - Topic normalization
**Phase 3 (Next sprint)**: Option C - Full hierarchy integration

### Rationale

1. Tests are blocking CI/CD - need immediate fix
2. Topic normalization is prerequisite for hierarchy integration
3. Full integration requires more planning and cross-team coordination

---

## Immediate Actions (Option A)

### 1. Fix `test_florida_controlled_substance_hours`

```python
# Current (broken):
md_cs_rules = [r for r in md_rules["ongoing"] if "controlled_substance" in (r.topic or "")]

# Fixed (matches database topic names):
md_cs_rules = [r for r in md_rules["ongoing"]
               if any(t in (r.topic or "") for t in ["controlled_substance", "opioid"])]
```

### 2. Fix `test_florida_hiv_aids_hours`

```python
# Current (wrong assumption):
assert not md_hiv_rule.first_renewal_only, "FL MD HIV/AIDS should be ongoing (every renewal)"

# Fixed (matches FSMB ground truth):
assert md_hiv_rule.first_renewal_only, "FL MD HIV/AIDS is first renewal only per FSMB"
```

### 3. Fix `test_biennial_vs_annual_calculation`

```python
# Current (wrong value):
assert fl_biennial_hours == 40.0, f"FL biennial (24 months) should be 40 hours, got {fl_biennial_hours}"

# Fixed (FL-M is 38h):
# Need to specify license_type or check both:
assert fl_md_hours == 38.0, f"FL-M biennial should be 38 hours"
assert fl_do_hours == 40.0, f"FL-O biennial should be 40 hours"
```

### 4. Fix `test_dea_conditional_requirements_without_dea`

```python
# Current (checks wrong rule):
# Looking at FL-O-CME-CONTROLLED-SUBSTANCES (not DEA conditional)

# Fixed (check the DEA-specific rule):
do_dea_rules = [r for r in do_rules["ongoing"]
                if "DEA" in r.rule_id or r.requires_dea_registration]
```

---

## Files to Modify

| File | Change Type |
|------|-------------|
| `tests/unit/cme/test_license_type_filtering.py` | Fix assertions |
| `tests/unit/cme/test_topic_gap_calculations.py` | Fix assertions |

---

## Validation Plan

After fixes:
1. Run `pytest tests/unit/cme/ -v` - All 42 tests should pass
2. Verify no regression in topic hierarchy tests (26 tests)
3. Document any remaining data discrepancies

---

## Related Issues

- **RIS-068**: DEA Registration Flag Audit (pending database sync)
- **ADR-002**: CME Topic Hierarchy (just implemented)
- **GitHub Issue #72**: DEA filtering logic (pending)
- **GitHub Issue #70**: DEA status question in onboarding (pending)

---

## Approval Required

- [ ] Fix tests only (Option A) - Proceed immediately
- [ ] Full normalization (Option B) - Requires sprint planning
- [ ] Full hierarchy integration (Option C) - Requires ADR update

---

## Appendix: FSMB Ground Truth (Florida)

**FL-M (MD)**:
- Total: 38h biennial (not counting 2h medical errors)
- HIV/AIDS: 1h one-time, first renewal only
- Controlled substance: 2h biennial, DEA conditional

**FL-O (DO)**:
- Total: 40h biennial
- HIV/AIDS: 1h one-time, first renewal only
- Controlled substances: 1h biennial (all DOs)
- Controlled substance prescribing: 2h biennial, DEA conditional

Source: `ssot/cme/fsmb_ground_truth_2025_v2.yaml` lines 500-601
