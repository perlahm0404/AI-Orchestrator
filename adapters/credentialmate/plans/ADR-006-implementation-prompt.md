# ADR-006 Implementation Prompt - CME Gap Calculation Standardization

**IMPORTANT**: This is a continuity prompt for Claude CLI to implement ADR-006. Copy this entire prompt into a new Claude CLI session in the CredentialMate repository.

---

## Session Context

**Repository**: `/Users/tmac/1_REPOS/credentialmate` (CredentialMate - HIPAA-compliant healthcare app)
**Stack**: FastAPI backend + Next.js frontend + PostgreSQL
**ADR**: ADR-006 - CME Gap Calculation Standardization
**Status**: Approved by tmac (2026-01-10)
**Timeline**: 10 days, $11K budget
**Priority**: HIGH (HIPAA data integrity issue)

---

## Problem Statement

CredentialMate displays **contradictory CME gap calculations** for the same provider/state:

**Evidence** (Dr. Sehgal, Florida MD License):
- **Dashboard**: Shows 4.0 hrs gap (from `/harmonize` endpoint)
- **State Detail Page**: Shows 2.0 hrs gap (from `/check` endpoint)
- **Expected**: Both should show **2.0 hrs** (Medical Errors Prevention is a separate topic)

**Root Cause**:
- `/harmonize` endpoint implements overlap logic (lines 675-718 in `compliance_endpoints.py`)
- `/check` endpoint uses naive subtraction (line 1306 in `cme_compliance_service.py`)
- Frontend components do client-side calculations instead of trusting API
- Ad-hoc reports have duplicate logic

---

## Your Mission

Implement ADR-006 to establish **Single Calculation Service Architecture**:

1. **Extract overlap logic** into reusable `calculate_gap_with_overlap()` method
2. **Standardize API contracts** to include `counts_toward_total` field
3. **Refactor frontend** to display API data only (no client-side calculations)
4. **Update ad-hoc reports** to call backend API
5. **Add integration tests** to ensure 100% parity (harmonize == check == reports)

**Success Criteria**: Dr. Sehgal shows **2.0 hrs gap** on all pages (dashboard, state detail, reports)

---

## Implementation Plan

### Phase 1: Backend Consolidation (2 days)

**Objective**: Create single source of truth for gap calculation

#### Task 1.1: Create `calculate_gap_with_overlap()` Method

**File**: `apps/backend-api/src/core/services/cme_compliance_service.py`

**Action**: Add new method after line 1200 (before `calculate_compliance()`)

```python
@dataclass
class TopicGap:
    """Individual topic gap detail."""
    topic: str
    gap_hours: float
    counts_toward_total: bool

@dataclass
class CMEGapCalculation:
    """Structured gap calculation result."""
    total_gap: float
    general_gap: float
    overlap_topic_gaps: List[TopicGap]
    separate_topic_gaps: List[TopicGap]
    calculation_method: str  # "overlap" or "simple"

def calculate_gap_with_overlap(
    self,
    total_required: float,
    total_earned: float,
    topic_progress: List[Dict],  # [{topic, required_hours, earned_hours}, ...]
    state_rules: List[CMERule]
) -> CMEGapCalculation:
    """
    Single source of truth for CME gap calculation.

    Implements overlap logic per state board requirements:
    - Overlapping topics (counts_toward_total=True):
      Hours satisfy BOTH total requirement AND topic requirement.
      Gap = max(general_gap, sum(overlap_topic_gaps))

    - Separate topics (counts_toward_total=False):
      Hours are IN ADDITION to total requirement.
      Gap = additive on top of general gap

    Args:
        total_required: Total CME hours required (e.g., 40h)
        total_earned: Total CME hours earned (e.g., 51h)
        topic_progress: List of topic requirements and earned hours
        state_rules: CME rules for this state/license type

    Returns:
        CMEGapCalculation with breakdown by overlap type

    Example:
        # General: 40h required, 51h earned (11h surplus)
        # Medical Errors: 2h required, 0h earned, counts_toward_total=False
        result = calculate_gap_with_overlap(40, 51, [...], [...])
        # result.total_gap = 2.0 (0 general + 2 separate)
        # result.general_gap = 0.0
        # result.separate_topic_gaps = [TopicGap("medical_errors", 2.0, False)]
    """
    # Calculate general gap
    general_gap = max(0, total_required - total_earned)

    # Separate topics by counts_toward_total flag
    overlap_topics = []
    separate_topics = []

    for topic_prog in topic_progress:
        # Find corresponding rule
        topic_rule = next(
            (r for r in state_rules if r.topic == topic_prog["topic"]),
            None
        )
        if not topic_rule:
            continue

        # Calculate gap for this topic
        topic_gap_hours = max(0, topic_prog["required_hours"] - topic_prog["earned_hours"])
        if topic_gap_hours == 0:
            continue

        # Create gap detail
        gap_detail = TopicGap(
            topic=topic_prog["topic"],
            gap_hours=topic_gap_hours,
            counts_toward_total=topic_rule.counts_toward_total
        )

        # Categorize by overlap type
        if topic_rule.counts_toward_total:
            overlap_topics.append(gap_detail)
        else:
            separate_topics.append(gap_detail)

    # Calculate minimum hours needed (overlap logic)
    if overlap_topics:
        overlap_total = sum(t.gap_hours for t in overlap_topics)
        # Minimum is the LARGER of:
        # 1. General gap (e.g., 10h to reach total)
        # 2. Sum of overlapping topic gaps (e.g., 2h opioid + 1h ethics = 3h)
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
        calculation_method="overlap" if (overlap_topics or separate_topics) else "simple"
    )
```

**Why This Works**:
- **Overlapping topics**: If you need 40h total and 2h opioid (overlapping), you can satisfy both with 40h of opioid courses. Gap = max(40-earned, 2-opioid_earned).
- **Separate topics**: If you need 40h total and 2h Medical Errors (separate), you need 40h PLUS 2h. Gap = (40-earned) + (2-medical_errors).

---

#### Task 1.2: Update `calculate_compliance()` Method

**File**: `apps/backend-api/src/core/services/cme_compliance_service.py`

**Action**: Replace line 1306 naive calculation

**Current Code** (line 1306):
```python
total_gap = max(0, total_required - total_earned)
```

**New Code**:
```python
# Use standardized gap calculation with overlap logic
gap_calculation = self.calculate_gap_with_overlap(
    total_required=total_required,
    total_earned=total_earned,
    topic_progress=[
        {
            "topic": tp.topic,
            "required_hours": tp.required_hours,
            "earned_hours": tp.earned_hours
        }
        for tp in topic_progress
    ],
    state_rules=ongoing_rules
)
total_gap = gap_calculation.total_gap
```

**Also Update** (around line 1380):
Add `gap_detail` to response:
```python
return CMEComplianceResult(
    # ... existing fields ...
    total_gap=total_gap,
    gap_detail=CMEGapDetail(
        total_gap=gap_calculation.total_gap,
        general_gap=gap_calculation.general_gap,
        overlap_topic_gaps=[
            TopicGapResponse(
                topic=t.topic,
                gap_hours=t.gap_hours,
                counts_toward_total=t.counts_toward_total
            )
            for t in gap_calculation.overlap_topic_gaps
        ],
        separate_topic_gaps=[
            TopicGapResponse(
                topic=t.topic,
                gap_hours=t.gap_hours,
                counts_toward_total=t.counts_toward_total
            )
            for t in gap_calculation.separate_topic_gaps
        ],
        calculation_method=gap_calculation.calculation_method
    )
)
```

---

#### Task 1.3: Refactor `/harmonize` Endpoint

**File**: `apps/backend-api/src/contexts/cme/api/compliance_endpoints.py`

**Action**: Replace lines 675-718 with call to `calculate_gap_with_overlap()`

**Find Code** (lines 675-718):
```python
# CRITICAL: Implement topic overlap logic
# Determine actual minimum hours needed considering whether topics count toward total
total_rule = next((r for r in state_rules if r.requirement_type == "hours"), None)

if total_rule:
    total_required = total_rule.requirement_value

    # Separate topic requirements by whether they count toward total
    overlap_topics = []
    separate_topics = []

    # ... (40+ lines of overlap logic) ...

    total_gap = minimum_hours
```

**Replace With**:
```python
# Use standardized gap calculation service
from core.services.cme_compliance_service import CMEComplianceService

cme_service = CMEComplianceService(db)
gap_calculation = cme_service.calculate_gap_with_overlap(
    total_required=total_required,
    total_earned=state_earned,
    topic_progress=[
        {
            "topic": tg.topic,
            "required_hours": tg.required_hours,
            "earned_hours": tg.earned_hours
        }
        for tg in topic_gaps_detailed
    ],
    state_rules=state_rules
)
total_gap = gap_calculation.total_gap

# Update topic_gaps_detailed to include counts_toward_total flag
for tg in topic_gaps_detailed:
    # Find in gap_calculation result
    all_gaps = gap_calculation.overlap_topic_gaps + gap_calculation.separate_topic_gaps
    gap_detail = next((g for g in all_gaps if g.topic == tg.topic), None)
    if gap_detail:
        tg.counts_toward_total = gap_detail.counts_toward_total
```

---

#### Task 1.4: Add Unit Tests

**File**: `apps/backend-api/tests/unit/cme/test_gap_calculation.py` (NEW)

```python
import pytest
from core.services.cme_compliance_service import CMEComplianceService, CMEGapCalculation
from contexts.cme.models.cme_rule import CMERule

class TestGapCalculation:
    """Tests for CME gap calculation overlap logic."""

    def test_separate_topics_are_additive(self):
        """Separate topics (counts_toward_total=False) are additive."""
        # Setup
        service = CMEComplianceService(db=None)  # Mock DB not needed for this method

        # Scenario: General met (51/40), Medical Errors unmet (0/2, separate)
        topic_progress = [
            {"topic": "medical_errors_prevention", "required_hours": 2.0, "earned_hours": 0.0}
        ]
        state_rules = [
            CMERule(topic="medical_errors_prevention", counts_toward_total=False)
        ]

        # Execute
        result = service.calculate_gap_with_overlap(
            total_required=40.0,
            total_earned=51.0,
            topic_progress=topic_progress,
            state_rules=state_rules
        )

        # Assert
        assert result.total_gap == 2.0  # Separate topics are additive
        assert result.general_gap == 0.0  # General requirement met
        assert len(result.separate_topic_gaps) == 1
        assert result.separate_topic_gaps[0].gap_hours == 2.0

    def test_overlapping_topics_use_max(self):
        """Overlapping topics (counts_toward_total=True) use max(general, sum(topics))."""
        # Setup
        service = CMEComplianceService(db=None)

        # Scenario: General gap 10h, Opioid gap 2h (overlapping)
        topic_progress = [
            {"topic": "opioid_prescribing", "required_hours": 2.0, "earned_hours": 0.0}
        ]
        state_rules = [
            CMERule(topic="opioid_prescribing", counts_toward_total=True)
        ]

        # Execute
        result = service.calculate_gap_with_overlap(
            total_required=40.0,
            total_earned=30.0,  # 10h gap
            topic_progress=topic_progress,
            state_rules=state_rules
        )

        # Assert
        assert result.total_gap == 10.0  # max(10, 2) = 10
        assert result.general_gap == 10.0
        assert len(result.overlap_topic_gaps) == 1

    def test_mixed_overlap_and_separate(self):
        """Mixed overlapping and separate topics."""
        # Setup
        service = CMEComplianceService(db=None)

        # Scenario:
        # - General: 40h required, 35h earned → 5h gap
        # - Opioid: 2h required, 1h earned → 1h gap (overlapping)
        # - Medical Errors: 2h required, 0h earned → 2h gap (separate)
        topic_progress = [
            {"topic": "opioid_prescribing", "required_hours": 2.0, "earned_hours": 1.0},
            {"topic": "medical_errors_prevention", "required_hours": 2.0, "earned_hours": 0.0}
        ]
        state_rules = [
            CMERule(topic="opioid_prescribing", counts_toward_total=True),
            CMERule(topic="medical_errors_prevention", counts_toward_total=False)
        ]

        # Execute
        result = service.calculate_gap_with_overlap(
            total_required=40.0,
            total_earned=35.0,
            topic_progress=topic_progress,
            state_rules=state_rules
        )

        # Assert
        # Overlap: max(5, 1) = 5
        # Separate: +2
        # Total: 5 + 2 = 7
        assert result.total_gap == 7.0
        assert result.general_gap == 5.0
        assert len(result.overlap_topic_gaps) == 1
        assert len(result.separate_topic_gaps) == 1

    def test_dr_sehgal_florida_case(self):
        """Real-world case: Dr. Sehgal Florida MD license."""
        # Setup
        service = CMEComplianceService(db=None)

        # Dr. Sehgal FL scenario:
        # - General: 40h required, 51h earned (11h surplus)
        # - Medical Errors: 2h required, 0h earned (separate topic)
        topic_progress = [
            {"topic": "medical_errors_prevention", "required_hours": 2.0, "earned_hours": 0.0}
        ]
        state_rules = [
            CMERule(topic="medical_errors_prevention", counts_toward_total=False)
        ]

        # Execute
        result = service.calculate_gap_with_overlap(
            total_required=40.0,
            total_earned=51.0,
            topic_progress=topic_progress,
            state_rules=state_rules
        )

        # Assert - should be 2.0h (not 0h, not 4.0h)
        assert result.total_gap == 2.0
        assert result.calculation_method == "overlap"
```

**Run Tests**:
```bash
cd /Users/tmac/1_REPOS/credentialmate
pytest apps/backend-api/tests/unit/cme/test_gap_calculation.py -v
```

**Expected Output**:
```
test_gap_calculation.py::test_separate_topics_are_additive PASSED
test_gap_calculation.py::test_overlapping_topics_use_max PASSED
test_gap_calculation.py::test_mixed_overlap_and_separate PASSED
test_gap_calculation.py::test_dr_sehgal_florida_case PASSED
```

---

### Phase 2: API Contract Standardization (2 days)

#### Task 2.1: Update Response Schemas

**File**: `apps/backend-api/src/contexts/cme/schemas/cme_schemas.py`

**Action**: Add `counts_toward_total` field to existing schemas

**Find**: `TopicProgressResponse` class (around line 290)

**Update**:
```python
class TopicProgressResponse(BaseModel):
    topic: str
    normalized_topic: Optional[str] = None  # From ADR-002
    required_hours: float
    earned_hours: float
    gap: float
    completed: bool
    counts_toward_total: bool  # NEW
    explanation: Optional[str] = None  # NEW
```

**Find**: `HarmonizerTopicGapDetail` class (around line 410)

**Update**:
```python
class HarmonizerTopicGapDetail(BaseModel):
    topic: str
    normalized_topic: Optional[str] = None  # From ADR-002
    gap_hours: float
    counts_toward_total: bool  # NEW
    explanation: Optional[str] = None  # NEW
```

**Add New Schemas** (after existing schemas):
```python
class TopicGapResponse(BaseModel):
    """Individual topic gap with overlap metadata."""
    topic: str
    gap_hours: float
    counts_toward_total: bool
    explanation: Optional[str] = None

class CMEGapDetail(BaseModel):
    """Detailed gap calculation breakdown."""
    total_gap: float
    general_gap: float
    overlap_topic_gaps: List[TopicGapResponse]
    separate_topic_gaps: List[TopicGapResponse]
    calculation_method: str  # "overlap" or "simple"

class CMEComplianceResult(BaseModel):
    # ... existing fields ...
    total_gap: float
    topic_progress: List[TopicProgressResponse]
    gap_detail: Optional[CMEGapDetail] = None  # NEW
```

---

#### Task 2.2: Populate New Fields in Service

**File**: `apps/backend-api/src/core/services/cme_compliance_service.py`

**Action**: Generate `explanation` text for topics

**Find**: Where `TopicProgressResponse` is created (around line 1350)

**Update**:
```python
# Find rule for this topic
topic_rule = next((r for r in ongoing_rules if r.topic == topic), None)
counts_toward_total = topic_rule.counts_toward_total if topic_rule else True

# Generate explanation
if gap > 0:
    if counts_toward_total:
        explanation = f"These {gap:.1f}h count toward your {total_required:.1f}h general CME requirement"
    else:
        explanation = f"These {gap:.1f}h are IN ADDITION to your {total_required:.1f}h general requirement"
else:
    explanation = None

topic_progress.append(
    TopicProgressResponse(
        topic=topic,
        normalized_topic=normalized_topic,  # From ADR-002
        required_hours=required,
        earned_hours=earned,
        gap=gap,
        completed=(earned >= required),
        counts_toward_total=counts_toward_total,  # NEW
        explanation=explanation  # NEW
    )
)
```

---

#### Task 2.3: Add Integration Test (Endpoint Parity)

**File**: `apps/backend-api/tests/integration/test_cme_parity.py` (NEW)

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestCMEEndpointParity:
    """Ensure /harmonize and /check return identical gaps."""

    def test_harmonize_check_parity_dr_sehgal_florida(self):
        """Dr. Sehgal FL should show 2.0h gap on both endpoints."""
        # Get provider ID
        provider_id = self._get_provider_id("real300@test.com")

        # Call /harmonize
        harmonize_response = client.post(
            "/api/v1/cme/compliance/harmonize",
            json={"provider_id": provider_id}
        )
        assert harmonize_response.status_code == 200
        harmonize_data = harmonize_response.json()

        fl_harmonize = next(
            (g for g in harmonize_data["state_gaps"] if g["state"] == "FL"),
            None
        )
        assert fl_harmonize is not None

        # Call /check
        check_response = client.post(
            "/api/v1/cme/compliance/check",
            json={
                "provider_id": provider_id,
                "state": "FL",
                "license_type": "MD",
                "cycle_start": "2024-01-01",
                "cycle_end": "2026-01-31"
            }
        )
        assert check_response.status_code == 200
        check_data = check_response.json()

        # Assert parity
        assert fl_harmonize["total_gap"] == check_data["total_gap"]
        assert fl_harmonize["total_gap"] == 2.0  # Expected gap

        # Both should use overlap calculation method
        assert check_data["gap_detail"]["calculation_method"] == "overlap"

    def test_harmonize_check_parity_multiple_states(self):
        """Verify parity across multiple states."""
        provider_id = self._get_provider_id("real300@test.com")

        # Call /harmonize
        harmonize_response = client.post(
            "/api/v1/cme/compliance/harmonize",
            json={"provider_id": provider_id}
        )
        harmonize_data = harmonize_response.json()

        # For each state in harmonize response, verify /check matches
        for state_gap in harmonize_data["state_gaps"]:
            state = state_gap["state"]

            # Call /check for this state
            check_response = client.post(
                "/api/v1/cme/compliance/check",
                json={
                    "provider_id": provider_id,
                    "state": state,
                    "license_type": "MD",  # Assume MD for test
                    "cycle_start": "2024-01-01",
                    "cycle_end": "2026-01-31"
                }
            )
            check_data = check_response.json()

            # Assert parity
            assert state_gap["total_gap"] == check_data["total_gap"], \
                f"Gap mismatch for {state}: harmonize={state_gap['total_gap']}, check={check_data['total_gap']}"

    def _get_provider_id(self, email: str) -> int:
        """Helper to get provider ID by email."""
        # Query database or use test fixture
        # For now, assume known test data
        if email == "real300@test.com":
            return 1  # Replace with actual provider ID from test DB
        raise ValueError(f"Unknown test provider: {email}")
```

**Run Tests**:
```bash
pytest apps/backend-api/tests/integration/test_cme_parity.py -v
```

---

### Phase 3: Frontend Refactor (3 days)

#### Task 3.1: Update State Detail Page

**File**: `apps/frontend-web/src/app/dashboard/states/[state]/page.tsx`

**Action**: Remove client-side calculation (lines 148-186), display API data

**Find Code** (lines 148-186):
```typescript
const requirements = [];
if (complianceResult.total_required > 0) {
  requirements.push({
    required: complianceResult.total_required,
    completed: complianceResult.total_earned,
    isMet: complianceResult.total_earned >= complianceResult.total_required,
  });
}

complianceResult.topic_progress.forEach((topic) => {
  requirements.push({
    required: topic.required_hours,
    completed: topic.earned_hours,
    isMet: topic.completed,
  });
});
```

**Replace With**:
```typescript
// Display API data directly (no client-side calculation)
const requirements = complianceResult.topic_progress.map((topic) => ({
  name: topic.topic,
  required: topic.required_hours,
  completed: topic.earned_hours,
  gap: topic.gap,
  isMet: topic.completed,
  countsTowardTotal: topic.counts_toward_total,  // NEW
  explanation: topic.explanation  // NEW
}));

// Add general requirement if total_required exists
if (complianceResult.total_required > 0) {
  requirements.unshift({
    name: "General CME",
    required: complianceResult.total_required,
    completed: complianceResult.total_earned,
    gap: complianceResult.total_gap,
    isMet: complianceResult.total_earned >= complianceResult.total_required,
    countsTowardTotal: true,
    explanation: null
  });
}
```

**Add Overlap Badge** (in the component rendering):
```tsx
{requirements.map((req) => (
  <div key={req.name} className="flex items-center justify-between p-4">
    <div className="flex items-center gap-2">
      <span className="font-medium">{req.name}</span>
      {req.countsTowardTotal ? (
        <Badge color="blue" size="sm" title="These hours count toward your general CME requirement">
          Overlaps
        </Badge>
      ) : (
        <Badge color="orange" size="sm" title="These hours are IN ADDITION to your general CME requirement">
          Additive
        </Badge>
      )}
      {req.explanation && (
        <Tooltip content={req.explanation}>
          <InfoIcon className="w-4 h-4 text-gray-400" />
        </Tooltip>
      )}
    </div>
    <div>
      <span className={req.isMet ? "text-green-600" : "text-red-600"}>
        {req.completed}/{req.required} hrs
      </span>
      {!req.isMet && <span className="ml-2 text-sm text-gray-500">({req.gap}h needed)</span>}
    </div>
  </div>
))}
```

---

#### Task 3.2: Update CME Compliance Table

**File**: `apps/frontend-web/src/components/dashboard/CMEComplianceTable.tsx`

**Action**: Remove any client-side gap calculations, add tooltips

**Find**: `getTopicGapsTooltip` function (lines 95-102)

**Update**:
```typescript
function getTopicGapsTooltip(license: StateLicenseWithCME): string {
  const gaps = license.cme_status.topic_gaps?.filter(gap => gap.gap > 0) || [];

  return gaps.map(gap => {
    const overlapType = gap.counts_toward_total ? "Overlaps" : "Additive";
    return `${gap.topic_name}: ${formatHours(gap.gap)} hrs (${overlapType})`;
  }).join('\n');
}
```

**Ensure**: No client-side calculation like `total_required - total_earned`. All gaps come from `license.cme_status.total_gap` or `topic_gaps[].gap`.

---

#### Task 3.3: Add Component Tests

**File**: `apps/frontend-web/src/app/dashboard/states/__tests__/StatePage.test.tsx` (NEW)

```typescript
import { render, screen } from '@testing-library/react';
import StatePage from '../[state]/page';

describe('State Detail Page', () => {
  it('displays overlap badge for overlapping topics', () => {
    const mockData = {
      topic_progress: [
        {
          topic: 'opioid_prescribing',
          required_hours: 2,
          earned_hours: 0,
          gap: 2,
          completed: false,
          counts_toward_total: true,
          explanation: 'These 2h count toward your 40h general requirement'
        }
      ]
    };

    render(<StatePage complianceResult={mockData} />);

    expect(screen.getByText('Overlaps')).toBeInTheDocument();
    expect(screen.getByTitle(/count toward your general/i)).toBeInTheDocument();
  });

  it('displays additive badge for separate topics', () => {
    const mockData = {
      topic_progress: [
        {
          topic: 'medical_errors_prevention',
          required_hours: 2,
          earned_hours: 0,
          gap: 2,
          completed: false,
          counts_toward_total: false,
          explanation: 'These 2h are IN ADDITION to your 40h general requirement'
        }
      ]
    };

    render(<StatePage complianceResult={mockData} />);

    expect(screen.getByText('Additive')).toBeInTheDocument();
    expect(screen.getByTitle(/IN ADDITION to your general/i)).toBeInTheDocument();
  });

  it('does not perform client-side gap calculations', () => {
    const mockData = {
      total_gap: 2.0,  // From API
      topic_progress: [
        { topic: 'medical_errors', gap: 2.0, counts_toward_total: false }
      ]
    };

    render(<StatePage complianceResult={mockData} />);

    // Gap should be displayed from API, not calculated
    expect(screen.getByText(/2.*hrs/i)).toBeInTheDocument();
  });
});
```

**Run Tests**:
```bash
cd apps/frontend-web
npm test -- StatePage.test.tsx
```

---

### Phase 4: Ad-hoc Reports (1 day)

#### Task 4.1: Refactor `generate_cme_v4.py`

**File**: `scripts/generate_cme_v4.py`

**Action**: Replace local calculation with API call

**Find**: Gap calculation logic (likely around line 200-300)

**Replace With**:
```python
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

def get_cme_gaps(provider_id: int) -> dict:
    """Call backend API for CME gap calculation."""
    response = requests.post(
        f"{API_URL}/api/v1/cme/compliance/harmonize",
        json={"provider_id": provider_id}
    )
    response.raise_for_status()
    return response.json()

def generate_cme_report(provider_email: str):
    """Generate CME report using backend API."""
    # Get provider ID from email
    provider_id = get_provider_id_by_email(provider_email)

    # Call API (no local calculation!)
    data = get_cme_gaps(provider_id)

    # Format for Excel/PDF output
    for state_gap in data["state_gaps"]:
        print(f"\n{state_gap['state']} - {state_gap['total_gap']:.1f}h gap")

        # Show overlap breakdown
        for topic in state_gap["topic_gaps_detailed"]:
            if topic["gap_hours"] > 0:
                overlap_type = "Overlaps" if topic["counts_toward_total"] else "Additive"
                print(f"  - {topic['topic']}: {topic['gap_hours']:.1f}h ({overlap_type})")
```

---

#### Task 4.2: Add Integration Test

**File**: `tests/integration/test_adhoc_parity.py` (NEW, per ADR-005)

```python
import subprocess
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_adhoc_report_matches_api():
    """Ad-hoc report shows same gaps as API (per ADR-005)."""
    provider_email = "real300@test.com"
    provider_id = 1  # Get from test DB

    # Run ad-hoc script
    result = subprocess.run(
        ["python", "scripts/generate_cme_v4.py", "--email", provider_email, "--json"],
        capture_output=True,
        text=True,
        cwd="/Users/tmac/1_REPOS/credentialmate"
    )
    assert result.returncode == 0
    adhoc_gaps = json.loads(result.stdout)

    # Call backend API
    api_response = client.post("/api/v1/cme/compliance/harmonize", json={"provider_id": provider_id})
    assert api_response.status_code == 200
    api_gaps = api_response.json()["state_gaps"]

    # Assert parity
    for state in ["FL", "OH", "MO"]:
        adhoc_state = next((s for s in adhoc_gaps if s["state"] == state), None)
        api_state = next((s for s in api_gaps if s["state"] == state), None)

        assert adhoc_state is not None, f"Ad-hoc missing {state}"
        assert api_state is not None, f"API missing {state}"
        assert adhoc_state["total_gap"] == api_state["total_gap"], \
            f"{state} gap mismatch: adhoc={adhoc_state['total_gap']}, api={api_state['total_gap']}"
```

---

### Phase 5: Testing & Validation (2 days)

#### Task 5.1: Dr. Sehgal End-to-End Test

**File**: `apps/backend-api/tests/e2e/test_dr_sehgal_consistency.py` (NEW)

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestDrSehgalConsistency:
    """Ensure Dr. Sehgal shows 2.0h gap everywhere (not 4.0h and 2.0h)."""

    def test_florida_gap_consistency_across_all_endpoints(self):
        """Dr. Sehgal FL shows 2.0h gap on dashboard, state detail, and reports."""
        provider_id = 1  # Dr. Sehgal test provider ID
        expected_gap = 2.0  # Medical Errors Prevention (separate topic)

        # 1. Dashboard (harmonizer)
        harmonize_response = client.post("/api/v1/cme/compliance/harmonize", json={"provider_id": provider_id})
        assert harmonize_response.status_code == 200
        fl_harmonize = next(g for g in harmonize_response.json()["state_gaps"] if g["state"] == "FL")

        assert fl_harmonize["total_gap"] == expected_gap, \
            f"Dashboard shows {fl_harmonize['total_gap']}h, expected {expected_gap}h"

        # 2. State detail page (/check)
        check_response = client.post("/api/v1/cme/compliance/check", json={
            "provider_id": provider_id, "state": "FL", "license_type": "MD"
        })
        assert check_response.status_code == 200
        check_data = check_response.json()

        assert check_data["total_gap"] == expected_gap, \
            f"State detail shows {check_data['total_gap']}h, expected {expected_gap}h"

        # 3. Verify gap breakdown
        gap_detail = check_data["gap_detail"]
        assert gap_detail["calculation_method"] == "overlap"
        assert gap_detail["general_gap"] == 0.0  # General requirement met
        assert len(gap_detail["separate_topic_gaps"]) == 1  # Medical Errors
        assert gap_detail["separate_topic_gaps"][0]["gap_hours"] == 2.0
        assert gap_detail["separate_topic_gaps"][0]["counts_toward_total"] is False

    def test_ohio_zero_gap_consistency(self):
        """Dr. Sehgal OH shows 0h gap everywhere (fully compliant)."""
        provider_id = 1
        expected_gap = 0.0

        # Dashboard
        harmonize_response = client.post("/api/v1/cme/compliance/harmonize", json={"provider_id": provider_id})
        oh_harmonize = next(g for g in harmonize_response.json()["state_gaps"] if g["state"] == "OH")
        assert oh_harmonize["total_gap"] == expected_gap

        # State detail
        check_response = client.post("/api/v1/cme/compliance/check", json={
            "provider_id": provider_id, "state": "OH", "license_type": "MD"
        })
        assert check_response.json()["total_gap"] == expected_gap
```

**Run E2E Tests**:
```bash
pytest apps/backend-api/tests/e2e/test_dr_sehgal_consistency.py -v
```

**Expected Output**:
```
test_dr_sehgal_consistency.py::test_florida_gap_consistency_across_all_endpoints PASSED
test_dr_sehgal_consistency.py::test_ohio_zero_gap_consistency PASSED
```

---

#### Task 5.2: Manual QA Checklist

**Perform these manual tests in browser:**

1. **Dashboard Page** (`/dashboard/cme`):
   - [ ] Dr. Sehgal shows **2.0 hrs gap** for Florida (not 4.0h)
   - [ ] Hover tooltip shows "Medical Errors Prevention: 2h (Additive)"
   - [ ] Ohio shows 0h gap
   - [ ] Missouri shows 0h gap

2. **Florida State Detail Page** (`/dashboard/states/FL`):
   - [ ] Total gap shows **2.0 hrs** (not 0h, not 4.0h)
   - [ ] Medical Errors Prevention shows "Additive" badge (orange)
   - [ ] Hover tooltip explains "IN ADDITION to general requirement"
   - [ ] Other topics (Domestic Violence, Opioid) show "Overlaps" badge (blue)

3. **Ad-hoc Report** (run `generate_cme_v4.py`):
   - [ ] Florida shows 2.0h gap in output
   - [ ] Report indicates "(Additive)" for Medical Errors
   - [ ] Matches UI exactly

**If any fail**: Check logs, verify API responses, re-run backend tests.

---

## Success Criteria

Your implementation is successful when:

✅ **All unit tests pass** (`test_gap_calculation.py`)
✅ **All integration tests pass** (`test_cme_parity.py`, `test_adhoc_parity.py`)
✅ **All E2E tests pass** (`test_dr_sehgal_consistency.py`)
✅ **Dr. Sehgal shows 2.0h gap** on dashboard, state detail, and reports (not 4.0h and 2.0h)
✅ **UI shows overlap badges** (blue for overlapping, orange for additive)
✅ **No client-side gap calculations** in frontend (all from API)
✅ **Ad-hoc reports call API** (no duplicate logic)

---

## Key Files to Modify

### Backend (Python/FastAPI)
1. `apps/backend-api/src/core/services/cme_compliance_service.py` - Add `calculate_gap_with_overlap()`, update `calculate_compliance()`
2. `apps/backend-api/src/contexts/cme/api/compliance_endpoints.py` - Refactor `/harmonize` to use service method
3. `apps/backend-api/src/contexts/cme/schemas/cme_schemas.py` - Add `counts_toward_total`, `explanation`, `CMEGapDetail`
4. `apps/backend-api/tests/unit/cme/test_gap_calculation.py` - NEW unit tests
5. `apps/backend-api/tests/integration/test_cme_parity.py` - NEW integration tests
6. `apps/backend-api/tests/e2e/test_dr_sehgal_consistency.py` - NEW E2E tests

### Frontend (Next.js/TypeScript)
7. `apps/frontend-web/src/app/dashboard/states/[state]/page.tsx` - Remove lines 148-186, display API data, add badges
8. `apps/frontend-web/src/components/dashboard/CMEComplianceTable.tsx` - Update tooltips to show overlap type
9. `apps/frontend-web/src/app/dashboard/states/__tests__/StatePage.test.tsx` - NEW component tests

### Scripts
10. `scripts/generate_cme_v4.py` - Call API instead of local calculation
11. `tests/integration/test_adhoc_parity.py` - NEW (per ADR-005)

---

## Common Pitfalls to Avoid

❌ **Don't**: Modify database schema (no migrations needed for this ADR)
❌ **Don't**: Create new API endpoints (use existing `/harmonize` and `/check`)
❌ **Don't**: Change frontend routing or page structure
❌ **Don't**: Modify authentication or authorization logic
❌ **Don't**: Add new dependencies without approval

✅ **Do**: Extract overlap logic into reusable method
✅ **Do**: Add comprehensive tests (unit, integration, E2E)
✅ **Do**: Remove all client-side gap calculations
✅ **Do**: Add user-friendly explanations (`counts_toward_total` badges)
✅ **Do**: Ensure 100% parity (harmonize == check == reports)

---

## Questions to Ask If Stuck

1. **Schema issues**: "Where is `CMERule.counts_toward_total` defined? Show me the model."
2. **Test failures**: "Why is test_dr_sehgal_florida_case failing? Show me the calculation breakdown."
3. **Frontend display**: "How do I add a Badge component in this Next.js project? Show me examples."
4. **API integration**: "How do I call the backend API from `generate_cme_v4.py`? Show me existing patterns."

---

## Final Validation

After completing all phases, run:

```bash
# Backend tests
cd /Users/tmac/1_REPOS/credentialmate
pytest apps/backend-api/tests/unit/cme/test_gap_calculation.py -v
pytest apps/backend-api/tests/integration/test_cme_parity.py -v
pytest apps/backend-api/tests/e2e/test_dr_sehgal_consistency.py -v

# Frontend tests
cd apps/frontend-web
npm test -- StatePage.test.tsx

# Ad-hoc report test
pytest tests/integration/test_adhoc_parity.py -v

# Manual QA
python scripts/generate_cme_v4.py --email real300@test.com
# Then open browser to /dashboard/cme and /dashboard/states/FL
```

**All tests must pass before marking ADR-006 as COMPLETE.**

---

## Timeline

- **Day 1-2**: Phase 1 (Backend Consolidation)
- **Day 3-4**: Phase 2 (API Contract Standardization)
- **Day 5-7**: Phase 3 (Frontend Refactor)
- **Day 8**: Phase 4 (Ad-hoc Reports)
- **Day 9-10**: Phase 5 (Testing & Validation)

**Total**: 10 days, $11K budget

---

## Reference Documents

- **ADR-006**: `/Users/tmac/1_REPOS/AI_Orchestrator/adapters/credentialmate/plans/decisions/ADR-006-cme-gap-calculation-standardization.md`
- **ADR-002**: CME Topic Hierarchy (for `normalized_topic`)
- **ADR-005**: Business Logic Consolidation (Backend SSOT principle)

---

**Good luck! This implementation will fix a critical HIPAA data integrity issue and establish single source of truth for CME gap calculations.**
