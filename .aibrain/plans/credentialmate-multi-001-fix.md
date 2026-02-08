# Plan: Fix CredentialMate MULTI-001 (PDF Parsing Timeout)

## Executive Summary

**Task**: MULTI-001 - Fix PDF parsing timeout for large documents
**Status**: BLOCKED after 6 attempts
**Error**: `'dict' object has no attribute 'type'`
**Priority**: P1

This plan outlines a multi-agent orchestration approach to fix the blocked task.

---

## Root Cause Analysis

After investigation, the error `'dict' object has no attribute 'type'` is occurring when:
1. Ralph verification returns a `Verdict` object
2. Somewhere in the orchestration pipeline, the verdict is serialized to dict (via `to_dict()`)
3. A consumer then tries to access `.type` on the dict instead of the object

**Primary File**: The error likely originates in one of:
- `orchestration/ko_helpers.py` - handles verdict normalization
- `agents/base.py:118-144` - records iteration with verdict

The PDF processing code itself (`process_document_task.py`) has already been updated with MULTI-001 timeout fixes including:
- Page limits for large PDFs (MAX_OCR_PAGES=10)
- Lower DPI (200 vs 300)
- Early termination when sufficient text extracted
- Memory monitoring

---

## Multi-Agent Fix Strategy

### Phase 1: Orchestration Bug Fix (BugFix Agent)

**Target**: Fix the dict/object type mismatch in verdict handling

**Files to Modify**:
1. `orchestration/ko_helpers.py:228-235` - Already has hasattr checks, but need to verify all callers
2. `agents/base.py:137-139` - Already has hasattr checks

**Action**:
- Search for all places where `verdict.type` is accessed without `hasattr` guard
- Add defensive checks where needed
- Ensure all verdict consumers use `_normalize_verdict()` function from ko_helpers.py

### Phase 2: Verify PDF Processing Fixes (TestWriter Agent)

**Target**: Ensure the MULTI-001 timeout fixes work correctly

**Acceptance Criteria**:
- 20+ page PDFs process without timeout
- Chunking strategy is working
- Memory usage stays under 512MB
- No PHI logged during processing

**Test Files to Create/Verify**:
- `apps/worker-tasks/tests/test_process_document_timeout.py`
- `apps/worker-tasks/tests/test_textract_strategy_chunking.py`

### Phase 3: Integration Testing (TestWriter Agent)

**Target**: End-to-end verification that:
1. Large PDF processing completes
2. Ralph verification returns proper Verdict object
3. No more dict/type attribute errors

---

## Implementation Steps

### Step 1: Identify All Verdict Type Access Points
```bash
grep -rn "\.type" --include="*.py" /Users/tmac/1_REPOS/credentialmate | grep -i verdict
```

### Step 2: Fix Missing HasAttr Guards
For each location accessing `verdict.type`:
- Wrap in `hasattr(verdict, 'type')` check
- Or convert using `_normalize_verdict()` helper

### Step 3: Verify PDF Processing Changes Already Applied
Check that `process_document_task.py` has:
- `MAX_OCR_PAGES` environment variable
- `soft_time_limit=600` and `time_limit=900`
- Memory monitoring with psutil
- Early termination logic

### Step 4: Create Test for Large PDF Processing
```python
# Test that verifies 20+ page PDF processing
def test_large_pdf_processing_completes():
    # Create/use a test PDF with 25 pages
    # Verify processing completes within timeout
    # Verify only first 10 pages were OCR'd
    # Verify memory usage under 512MB
```

### Step 5: Update Task Status
After verification passes:
- Mark MULTI-001 as complete
- Update work queue with evidence

---

## Agent Assignment

| Phase | Agent | Autonomy | Max Iterations |
|-------|-------|----------|----------------|
| Phase 1 | BugFix | L1 | 15 |
| Phase 2 | TestWriter | L1 | 15 |
| Phase 3 | TestWriter | L1 | 15 |

---

## Success Criteria

1. **No more dict type errors** - Verdicts handled polymorphically
2. **Large PDFs process** - 20+ pages complete without timeout
3. **Memory compliant** - Under 512MB usage
4. **HIPAA compliant** - No PHI logged
5. **Ralph passes** - All verification steps pass

---

## Rollback Plan

If fixes cause regressions:
1. Revert to commit before changes
2. Mark task as blocked with updated error details
3. Escalate to human review

---

## Evidence Requirements

- [ ] Test file created: `test_process_document_timeout.py`
- [ ] Test passes for 20+ page PDF
- [ ] Ralph verification returns PASS
- [ ] No `'dict' object has no attribute 'type'` errors in logs
- [ ] Memory monitoring shows <512MB usage

---

## Execution Command

```bash
# To execute this plan:
python autonomous_loop.py --project credentialmate --max-iterations 50

# Or run individual phases:
# Phase 1: BugFix agent on orchestration files
# Phase 2-3: TestWriter agent on worker-tasks tests
```
