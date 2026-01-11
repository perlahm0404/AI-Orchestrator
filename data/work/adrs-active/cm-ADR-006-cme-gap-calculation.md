---
# Document Metadata
doc-id: "cm-ADR-006"
title: "CME Gap Calculation Standardization"
created: "2026-01-05"
updated: "2026-01-10"
author: "Claude AI"
status: "approved"

# Compliance Metadata
compliance:
  soc2:
    controls: ["CC8.1"]
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.14.2.2"]
    classification: "confidential"
    review-frequency: "annual"

# Project Context
project: "credentialmate"
domain: "dev"
relates-to: ["ADR-005", "ADR-007"]

# Change Control
version: "1.0"
---

# ADR-006: CME Gap Calculation Standardization

**Date**: 2026-01-10
**Status**: approved
**Advisor**: app-advisor
**Deciders**: tmac (approved 2026-01-10)

---

## Tags

```yaml
tags: [cme-compliance, api-design, data-standardization, ssot, frontend-backend-parity]
applies_to:
  - "apps/backend-api/src/core/services/cme_compliance_service.py"
  - "apps/backend-api/src/contexts/cme/api/compliance_endpoints.py"
  - "apps/backend-api/src/contexts/cme/schemas/cme_schemas.py"
  - "apps/frontend-web/src/components/dashboard/CMEComplianceTable.tsx"
  - "apps/frontend-web/src/app/dashboard/states/[state]/page.tsx"
  - "scripts/generate_cme_v4.py"
domains: [backend, frontend, api-design, data-integrity]
```

---

## Context

### The Problem

**Production Issue**: CredentialMate displays **contradictory CME gap calculations** for the same provider/state across different UI components.

**Evidence** (Dr. Sehgal, Florida MD License):
- **CME Harmonizer Dashboard**: Shows "Urgent" with **4.0 hrs gap**
- **Florida State Detail Page**: Shows "At Risk" with **2 hrs gap**
- **Expected**: Both should show **identical gap** (same data, same state, same license)

### Root Cause Analysis

**Three different gap calculation methods exist:**

| Location | Endpoint | Calculation Method | Overlap Logic? |
|----------|----------|-------------------|----------------|
| **Dashboard** | `/harmonize` | `max(general_gap, overlap_total) + separate_topics` | ✅ **YES** |
| **State Detail** | `/check` | `total_required - total_earned` | ❌ **NO** |
| **Ad-hoc Reports** | Direct DB | Unknown (likely same as dashboard) | ❓ Unknown |

**The Discrepancy:**

In `compliance_endpoints.py` (lines 675-718), the `/harmonize` endpoint implements **sophisticated overlap logic**:

```python
# Overlapping topics: max(general_gap, sum(topic_gaps))
# Separate topics: additive on top of total
if topic_rule.counts_toward_total:
    overlap_topics.append(topic_gap)
else:
    separate_topics.append(topic_gap)

minimum_hours = max(general_gap, overlap_total) + sum(separate_topics)
```

But in `cme_compliance_service.py` (line 1306), the `calculate_compliance()` method uses **naive subtraction**:

```python
# WRONG - no overlap logic!
total_gap = max(0, total_required - total_earned)
```

**Why This Matters:**

Consider a provider with:
- General CME requirement: 40 hours (met with 51 hours)
- Medical Errors Prevention: 2 hours (unmet, 0 hours completed)
- Medical Errors is a **separate topic** (`counts_toward_total = False`)

**Correct calculation** (with overlap logic):
```
general_gap = max(0, 40 - 51) = 0
separate_gap = 2 (Medical Errors)
total_gap = 0 + 2 = 2 hours  ← CORRECT
```

**Naive calculation** (without overlap logic):
```
total_gap = max(0, (40 + 2) - 51) = 0 hours  ← WRONG! Missing the separate requirement
```

OR with a different interpretation:
```
total_gap = max(0, 40 - 51) + max(0, 2 - 0) = 0 + 2 = 2 hours  ← CORRECT by accident
```

The issue is **inconsistent application** of overlap logic across endpoints.

### Impact

- **User Confusion**: Providers see different gap numbers on different pages
- **HIPAA Compliance Risk**: Incorrect CME data affects medical licensing
- **Data Integrity**: No single source of truth for gap calculations
- **Maintenance Burden**: Business logic duplicated across 3+ locations
- **Violates ADR-005**: Backend SSOT principle not enforced for gap calculations

---

## Decision

**Approved**: Implement **Single Calculation Service Architecture** with standardized API contracts.

### Core Principles

1. **Single Source of Truth**: One gap calculation method, used everywhere
2. **Backend SSOT**: Frontend displays data, never calculates
3. **Explicit Data Contracts**: `counts_toward_total` exposed to frontend
4. **100% Parity**: All endpoints return identical gaps for same input

---

## Architecture

### Layer 1: Consolidate Gap Calculation Logic

**Extract overlap logic into reusable service method:**

```python
# apps/backend-api/src/core/services/cme_compliance_service.py

@dataclass
class CMEGapCalculation:
    """Structured gap calculation result."""
    total_gap: float
    general_gap: float
    overlap_topic_gaps: List[TopicGap]
    separate_topic_gaps: List[TopicGap]
    calculation_method: Literal["overlap", "simple"]

def calculate_gap_with_overlap(
    total_required: float,
    total_earned: float,
    topic_progress: List[TopicProgress],
    state_rules: List[CMERule]
) -> CMEGapCalculation:
    """
    Single source of truth for CME gap calculation.

    Implements overlap logic per state board requirements:
    - Overlapping topics (counts_toward_total=True):
      Hours satisfy BOTH total requirement AND topic requirement
      Gap = max(general_gap, sum(overlap_topic_gaps))

    - Separate topics (counts_toward_total=False):
      Hours are IN ADDITION to total requirement
      Gap = additive on top

    Returns:
        Structured gap calculation with breakdown by overlap type
    """
    # Find total hours rule
    total_rule = next((r for r in state_rules if r.requirement_type == "hours"), None)
    if not total_rule:
        return CMEGapCalculation(
            total_gap=0, general_gap=0,
            overlap_topic_gaps=[], separate_topic_gaps=[],
            calculation_method="simple"
        )

    # Calculate general gap
    general_gap = max(0, total_required - total_earned)

    # Separate topics by counts_toward_total flag
    overlap_topics = []
    separate_topics = []

    for topic_prog in topic_progress:
        topic_rule = next((r for r in state_rules if r.topic == topic_prog.topic), None)
        if not topic_rule:
            continue

        topic_gap = max(0, topic_prog.required_hours - topic_prog.earned_hours)
        if topic_gap == 0:
            continue

        gap_detail = TopicGap(
            topic=topic_prog.topic,
            gap_hours=topic_gap,
            counts_toward_total=topic_rule.counts_toward_total
        )

        if topic_rule.counts_toward_total:
            overlap_topics.append(gap_detail)
        else:
            separate_topics.append(gap_detail)

    # Calculate minimum hours needed (overlap logic)
    if overlap_topics:
        overlap_total = sum(t.gap_hours for t in overlap_topics)
        minimum_hours = max(general_gap, overlap_total)
    else:
        minimum_hours = general_gap

    # Add separate topics (always additive)
    if separate_topics:
        minimum_hours += sum(t.gap_hours for t in separate_topics)

    return CMEGapCalculation(
        total_gap=minimum_hours,
        general_gap=general_gap,
        overlap_topic_gaps=overlap_topics,
        separate_topic_gaps=separate_topics,
        calculation_method="overlap"
    )
```

**All endpoints must call this method:**
- `/api/v1/cme/compliance/harmonize` (refactor lines 675-718)
- `/api/v1/cme/compliance/check` (replace line 1306)
- Ad-hoc reports (`generate_cme_v4.py`)

---

### Layer 2: Standardize API Contracts

**Update response schemas to include overlap metadata:**

```python
# apps/backend-api/src/contexts/cme/schemas/cme_schemas.py

class TopicGap(BaseModel):
    """Individual topic gap detail."""
    topic: str
    normalized_topic: Optional[str]  # From ADR-002
    gap_hours: float
    counts_toward_total: bool  # NEW: expose to frontend
    explanation: Optional[str] = None  # NEW: user-friendly text

class CMEGapDetail(BaseModel):
    """Standardized gap calculation response."""
    total_gap: float
    general_gap: float  # NEW: breakdown
    overlap_topic_gaps: List[TopicGap]  # NEW: which topics overlap
    separate_topic_gaps: List[TopicGap]  # NEW: which are additive
    calculation_method: str  # NEW: "overlap" or "simple"

# Update existing schemas
class TopicProgressResponse(BaseModel):
    topic: str
    normalized_topic: Optional[str]  # From ADR-002
    required_hours: float
    earned_hours: float
    gap: float
    completed: bool
    counts_toward_total: bool  # NEW
    explanation: Optional[str] = None  # NEW

class CMEComplianceResult(BaseModel):
    # Existing fields...
    total_gap: float
    topic_progress: List[TopicProgressResponse]

    # NEW: gap breakdown
    gap_detail: Optional[CMEGapDetail] = None

class HarmonizerTopicGapDetail(BaseModel):
    topic: str
    normalized_topic: Optional[str]  # From ADR-002
    gap_hours: float
    counts_toward_total: bool  # NEW
    explanation: Optional[str] = None  # NEW
```

---

### Layer 3: Frontend Displays Only

**Remove all client-side gap calculations:**

```typescript
// apps/frontend-web/src/app/dashboard/states/[state]/page.tsx

// BEFORE (lines 148-186): Client-side calculation
const requirements = [];
if (complianceResult.total_required > 0) {
  requirements.push({
    required: complianceResult.total_required,
    completed: complianceResult.total_earned,
    isMet: complianceResult.total_earned >= complianceResult.total_required,
  });
}

// AFTER: Display API data directly
const requirements = complianceResult.topic_progress.map(topic => ({
  name: topic.topic,
  required: topic.required_hours,
  completed: topic.earned_hours,
  isMet: topic.completed,
  countsTowardTotal: topic.counts_toward_total,  // NEW
  explanation: topic.explanation  // NEW
}));
```

**Add UI badges for overlap status:**

```tsx
{topic.countsTowardTotal ? (
  <Badge color="blue" title="These hours count toward your general CME requirement">
    Counts toward general CME
  </Badge>
) : (
  <Badge color="orange" title="These hours are IN ADDITION to your general CME requirement">
    In addition to general CME
  </Badge>
)}
```

---

## Implementation Plan

### Phase 1: Backend Consolidation (2 days, $2K)

**Tasks:**

1. **Create `calculate_gap_with_overlap()` method**
   - File: `apps/backend-api/src/core/services/cme_compliance_service.py`
   - Extract logic from `compliance_endpoints.py` lines 675-718
   - Return structured `CMEGapCalculation` dataclass
   - Add comprehensive docstring with examples

2. **Update `calculate_compliance()` method**
   - File: `apps/backend-api/src/core/services/cme_compliance_service.py`
   - Replace line 1306 naive calculation
   - Call `calculate_gap_with_overlap()` instead
   - Populate `gap_detail` field in response

3. **Refactor `/harmonize` endpoint**
   - File: `apps/backend-api/src/contexts/cme/api/compliance_endpoints.py`
   - Replace lines 675-718 with call to `calculate_gap_with_overlap()`
   - Remove duplicate overlap logic
   - Ensure identical calculation

4. **Add unit tests**
   ```python
   def test_overlap_logic_separate_topics():
       """Separate topics are additive."""
       # General: 40h required, 51h earned → 0h gap
       # Medical Errors: 2h required, 0h earned, counts_toward_total=False
       result = calculate_gap_with_overlap(
           total_required=40, total_earned=51,
           topic_progress=[TopicProgress(topic="medical_errors", required=2, earned=0)],
           state_rules=[CMERule(topic="medical_errors", counts_toward_total=False)]
       )
       assert result.total_gap == 2.0  # Separate topics are additive
       assert result.general_gap == 0.0
       assert len(result.separate_topic_gaps) == 1

   def test_overlap_logic_overlapping_topics():
       """Overlapping topics use max(general, sum(topics))."""
       # General: 40h required, 30h earned → 10h gap
       # Opioid: 2h required, 0h earned, counts_toward_total=True
       result = calculate_gap_with_overlap(
           total_required=40, total_earned=30,
           topic_progress=[TopicProgress(topic="opioid", required=2, earned=0)],
           state_rules=[CMERule(topic="opioid", counts_toward_total=True)]
       )
       assert result.total_gap == 10.0  # max(10, 2) = 10
       assert result.general_gap == 10.0
       assert len(result.overlap_topic_gaps) == 1
   ```

**Success Criteria:**
- ✅ `calculate_gap_with_overlap()` method created
- ✅ All endpoints call this method
- ✅ Unit tests pass
- ✅ No duplicate overlap logic

---

### Phase 2: API Contract Standardization (2 days, $2K)

**Tasks:**

1. **Update response schemas**
   - File: `apps/backend-api/src/contexts/cme/schemas/cme_schemas.py`
   - Add `counts_toward_total` to `TopicProgressResponse`
   - Add `explanation` field (optional)
   - Add `normalized_topic` field (from ADR-002)
   - Create `CMEGapDetail` schema

2. **Populate new fields in service**
   - File: `apps/backend-api/src/core/services/cme_compliance_service.py`
   - Set `counts_toward_total` from `CMERule.counts_toward_total`
   - Generate `explanation` text:
     ```python
     if counts_toward_total:
         explanation = f"These {gap}h count toward your {total_required}h general CME requirement"
     else:
         explanation = f"These {gap}h are IN ADDITION to your {total_required}h general requirement"
     ```
   - Use `normalized_topic` from ADR-002 topic hierarchy

3. **Update OpenAPI/Swagger docs**
   - Regenerate API documentation
   - Add examples showing `counts_toward_total` field

4. **Integration test: endpoint parity**
   ```python
   def test_harmonize_check_parity():
       """Both endpoints return identical gaps."""
       provider_id = get_provider_id("real300@test.com")
       state = "FL"
       license_type = "MD"

       # Call /harmonize
       harmonize_response = client.post("/api/v1/cme/compliance/harmonize", json={"provider_id": provider_id})
       fl_gap = next(g for g in harmonize_response.json()["state_gaps"] if g["state"] == "FL")

       # Call /check
       check_response = client.post("/api/v1/cme/compliance/check", json={
           "provider_id": provider_id, "state": state, "license_type": license_type
       })

       # Assert parity
       assert fl_gap["total_gap"] == check_response.json()["total_gap"]
       assert fl_gap["calculation_method"] == "overlap"
       assert check_response.json()["calculation_method"] == "overlap"
   ```

**Success Criteria:**
- ✅ `counts_toward_total` in all CME responses
- ✅ `explanation` text generated
- ✅ Integration test passes (harmonize == check)
- ✅ API docs updated

---

### Phase 3: Frontend Refactor (3 days, $3K)

**Tasks:**

1. **Update CME Compliance Table**
   - File: `apps/frontend-web/src/components/dashboard/CMEComplianceTable.tsx`
   - Remove any client-side gap calculations
   - Display `total_gap` from API response
   - Add tooltip showing gap breakdown (overlap vs separate)

2. **Update State Detail Page**
   - File: `apps/frontend-web/src/app/dashboard/states/[state]/page.tsx`
   - Remove lines 148-186 (local calculation)
   - Display `topic_progress` from API directly
   - Add `counts_toward_total` badge:
     ```tsx
     <div className="flex items-center gap-2">
       <span>{topic.topic}</span>
       {topic.countsTowardTotal ? (
         <Badge color="blue" size="sm">Overlaps</Badge>
       ) : (
         <Badge color="orange" size="sm">Additive</Badge>
       )}
     </div>
     ```

3. **Add explanatory tooltips**
   ```tsx
   <Tooltip content={topic.explanation}>
     <InfoIcon className="w-4 h-4" />
   </Tooltip>
   ```

4. **Component tests**
   ```typescript
   test('displays overlap badge for overlapping topics', () => {
     const topic = {
       topic: 'opioid_prescribing',
       gap: 2,
       countsTowardTotal: true,
       explanation: 'These 2h count toward your 40h general requirement'
     };
     render(<TopicRow topic={topic} />);
     expect(screen.getByText('Overlaps')).toBeInTheDocument();
   });
   ```

**Success Criteria:**
- ✅ No client-side gap calculations
- ✅ Badges show overlap status
- ✅ Tooltips explain overlap logic
- ✅ Component tests pass

---

### Phase 4: Ad-hoc Reports (1 day, $1K)

**Tasks:**

1. **Refactor `generate_cme_v4.py`**
   - File: `scripts/generate_cme_v4.py`
   - Remove local gap calculation logic
   - Call `/harmonize` endpoint instead:
     ```python
     import requests

     response = requests.post(
         f"{API_URL}/api/v1/cme/compliance/harmonize",
         json={"provider_id": provider_id}
     )
     state_gaps = response.json()["state_gaps"]

     for state_gap in state_gaps:
         print(f"{state_gap['state']}: {state_gap['total_gap']}h gap")
         for topic in state_gap['topic_gaps_detailed']:
             overlap_type = "Overlaps" if topic['counts_toward_total'] else "Additive"
             print(f"  - {topic['topic']}: {topic['gap_hours']}h ({overlap_type})")
     ```

2. **Integration test (per ADR-005)**
   ```python
   def test_adhoc_report_matches_api():
       """Ad-hoc report shows same gaps as API."""
       provider_email = "real300@test.com"

       # Run ad-hoc script
       adhoc_output = subprocess.check_output([
           "python", "scripts/generate_cme_v4.py",
           "--email", provider_email
       ])
       adhoc_gaps = parse_adhoc_output(adhoc_output)

       # Query backend API
       provider_id = get_provider_id(provider_email)
       api_response = client.post("/api/v1/cme/compliance/harmonize", json={"provider_id": provider_id})
       api_gaps = api_response.json()["state_gaps"]

       # Assert parity
       for state in ["FL", "OH", "MO"]:
           adhoc_gap = next(g for g in adhoc_gaps if g["state"] == state)
           api_gap = next(g for g in api_gaps if g["state"] == state)
           assert adhoc_gap["total_gap"] == api_gap["total_gap"]
   ```

**Success Criteria:**
- ✅ Ad-hoc script calls API (no local calculation)
- ✅ Integration test passes
- ✅ Report shows overlap badges

---

### Phase 5: Testing & Validation (2 days, $3K)

**Tasks:**

1. **Dr. Sehgal test case**
   ```python
   def test_dr_sehgal_florida_gap_consistency():
       """All components show identical gap for Dr. Sehgal FL."""
       provider_id = get_provider_id("real300@test.com")

       # Dashboard (harmonizer)
       harmonize_response = client.post("/api/v1/cme/compliance/harmonize", json={"provider_id": provider_id})
       fl_harmonize = next(g for g in harmonize_response.json()["state_gaps"] if g["state"] == "FL")

       # State detail (/check)
       check_response = client.post("/api/v1/cme/compliance/check", json={
           "provider_id": provider_id, "state": "FL", "license_type": "MD"
       })

       # Ad-hoc report
       adhoc_output = generate_cme_v4("real300@test.com")
       fl_adhoc = next(g for g in adhoc_output if g["state"] == "FL")

       # All must show 2.0 hrs (Medical Errors is separate topic)
       expected_gap = 2.0
       assert fl_harmonize["total_gap"] == expected_gap
       assert check_response.json()["total_gap"] == expected_gap
       assert fl_adhoc["total_gap"] == expected_gap
   ```

2. **Test matrix**
   | Provider | State | General | Overlap Topic | Separate Topic | Expected Gap |
   |----------|-------|---------|---------------|----------------|--------------|
   | Dr. Sehgal | FL | 51/40 (met) | None | Medical Errors (0/2) | 2.0 |
   | Dr. Sehgal | OH | 51/40 (met) | None | None | 0.0 |
   | Dr. Sehgal | MO | 51/40 (met) | None | None | 0.0 |

3. **Regression tests**
   - Ensure existing gap calculations unchanged for providers without separate topics
   - Verify overlap logic works for various combinations

4. **Manual QA**
   - Load Dr. Sehgal dashboard → verify gap matches state detail
   - Run ad-hoc report → verify matches UI
   - Check tooltip explanations

**Success Criteria:**
- ✅ Dr. Sehgal test case passes
- ✅ All test matrix cases pass
- ✅ Regression tests pass
- ✅ Manual QA confirms consistency

---

## Files Modified

### Backend
- `apps/backend-api/src/core/services/cme_compliance_service.py` (add `calculate_gap_with_overlap()`, update `calculate_compliance()`)
- `apps/backend-api/src/contexts/cme/api/compliance_endpoints.py` (refactor `/harmonize` to use service method)
- `apps/backend-api/src/contexts/cme/schemas/cme_schemas.py` (add `counts_toward_total`, `explanation`, `CMEGapDetail`)

### Frontend
- `apps/frontend-web/src/components/dashboard/CMEComplianceTable.tsx` (remove client-side calc, add tooltips)
- `apps/frontend-web/src/app/dashboard/states/[state]/page.tsx` (remove lines 148-186, display API data)

### Scripts
- `scripts/generate_cme_v4.py` (call API instead of local calculation)

### Tests
- `apps/backend-api/tests/unit/cme/test_gap_calculation.py` (NEW)
- `apps/backend-api/tests/integration/test_cme_parity.py` (NEW)
- `apps/frontend-web/src/components/dashboard/__tests__/CMEComplianceTable.test.tsx` (UPDATE)

---

## Estimated Scope

| Phase | Days | Cost | Complexity |
|-------|------|------|------------|
| Backend Consolidation | 2 | $2K | Medium |
| API Contract Standardization | 2 | $2K | Low |
| Frontend Refactor | 3 | $3K | Medium |
| Ad-hoc Reports | 1 | $1K | Low |
| Testing & Validation | 2 | $3K | Medium |
| **Total** | **10 days** | **$11K** | **Medium** |

**Dependencies:**
- ADR-002 (CME Topic Hierarchy) - Leverage `normalized_topic`
- ADR-005 (Business Logic Consolidation) - This completes Phase 1

---

## Consequences

### Enables

✅ **Guaranteed Consistency**: All UI components show identical gaps
✅ **HIPAA Compliance**: Single auditable source for gap calculations
✅ **User Trust**: No more contradictory data across pages
✅ **Easier Maintenance**: Change logic once, everywhere updates
✅ **Testable**: Integration tests verify parity (UI == API == reports)
✅ **Transparency**: Users see why gaps exist (overlap vs additive)
✅ **ADR-005 Completion**: Backend SSOT principle fully enforced

### Constrains

⚠️ **Breaking API Change**: Adds new fields to existing responses (backward compatible)
⚠️ **Frontend Refactor**: Multiple components need updates
⚠️ **Ad-hoc Scripts**: Must call API (slower than direct DB)
⚠️ **10 Days Effort**: $11K investment required

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing integrations | MEDIUM | New fields are additive (backward compatible) |
| Data accuracy regression | CRITICAL | Byte-for-byte comparison vs baseline (Dr. Sehgal test case) |
| Frontend display errors | MEDIUM | Component tests + manual QA |
| Ad-hoc scripts slower | LOW | Acceptable tradeoff for consistency |
| User confusion about badges | LOW | Add tooltip explanations |

**Rollback Plan:**
1. Keep old calculation methods in `_legacy` functions for 30 days
2. Run old/new in parallel, log discrepancies
3. Only remove legacy code after 100% validation

---

## Success Metrics

**Quantitative:**
- ✅ 100% parity: harmonize == check == ad-hoc reports
- ✅ Zero client-side gap calculations (all from API)
- ✅ Integration tests pass (3+ test cases)
- ✅ Dr. Sehgal shows 2.0h gap everywhere (not 4.0h and 2.0h)

**Qualitative:**
- ✅ Users see consistent gap numbers everywhere
- ✅ Developers call `calculate_gap_with_overlap()` for all gaps
- ✅ Ad-hoc reports use API (no duplicate logic)
- ✅ UI shows overlap badges (user understanding improved)

---

## Related ADRs

- **ADR-002**: CME Topic Hierarchy - Leverage `normalized_topic` field
- **ADR-005**: Business Logic Consolidation - This completes Phase 1 (Backend SSOT)
- **Future ADR-007**: API Versioning Strategy (if breaking changes needed)

---

<!--
SYSTEM SECTION - DO NOT EDIT
-->

```yaml
_system:
  created_by: "app-advisor"
  created_at: "2026-01-10T23:00:00Z"
  approved_at: "2026-01-10T23:15:00Z"
  approved_by: "tmac"
  confidence: 93
  auto_decided: false
  escalation_reason: "Strategic domain (api_design, data_integrity, breaking_changes, multi-component impact)"
  domain_classification: "strategic"
  pattern_match_score: 97
  adr_alignment_score: 92
  historical_success_score: 90
  domain_certainty_score: 95
```

---

## Implementation Owner

**Team**: Backend + Frontend (coordinated effort)
**Timeline**: 10 days (2 weeks sprint)
**Priority**: HIGH (HIPAA data integrity issue)
**Start Date**: 2026-01-11 (approved for immediate start)
