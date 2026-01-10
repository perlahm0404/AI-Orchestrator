# ADR-002: CME Topic Hierarchy for Cross-State Aggregation

**Date**: 2026-01-10
**Status**: approved
**Advisor**: data-advisor, app-advisor
**Deciders**: tmac (approved 2026-01-10)

---

## Tags

```yaml
tags: [cme-compliance, data-model, topic-hierarchy, cross-state-aggregation, rules-engine]
applies_to:
  - "infra/lambda/functions/backend/src/contexts/cme/**"
  - "apps/rules-engine/rules_engine/src/**"
  - "ssot/cme/**"
domains: [backend, data, rules-engine]
```

---

## Context

CredentialMate calculates CME compliance across multiple states for healthcare providers. A provider licensed in KY, OH, and FL may complete a single CME activity that satisfies requirements in multiple states. However, the current system uses a **flat topic structure** that cannot express:

1. **Specificity relationships**: KY KASPER training (state-specific) should satisfy general opioid requirements in other states
2. **Hierarchical satisfaction**: Controlled substance CME should count toward general Category 1 requirements
3. **Board-specific constraints**: Some requirements ONLY accept the state's specific course (not equivalent topics)

**Current Problem**:
```
Provider completes: "KY KASPER Opioid Training" (3h)

Current behavior:
  - KY kasper requirement: ✓ SATISFIED (exact match)
  - OH opioid requirement: ✗ NOT SATISFIED (different topic string)
  - FL controlled substance: ✗ NOT SATISFIED (different topic string)

Expected behavior:
  - KY kasper requirement: ✓ SATISFIED (exact match)
  - OH opioid requirement: ✓ SATISFIED (kasper IS opioid)
  - FL controlled substance: ✓ SATISFIED (opioid IS controlled substance)
```

**Current flat structure** (`constants.py`):
```python
CANONICAL_TOPICS = {
    "opioid_prescribing": {"aliases": ["opioid", ...]},
    "kasper_pain_addiction": {"aliases": ["kasper"]},  # No parent relationship
}
```

---

## Decision

**Implement explicit topic hierarchy** with parent/child relationships and satisfaction rules:

1. **Topic Hierarchy Data Structure**: New `TOPIC_HIERARCHY` mapping with `parent` and `satisfies` fields
2. **topic_satisfies() Function**: Determines if an activity's topic satisfies a requirement's topic
3. **Board-Specific Flag**: New `board_specific_course` field on CMEActivity model
4. **Migration**: Backfill existing topics with hierarchy relationships

---

## Options Considered

### Option A: Explicit Topic Hierarchy (Selected)

**Approach**:
- Create `TOPIC_HIERARCHY` dictionary with parent/child relationships
- Each topic declares what it "satisfies" (more general topics)
- `topic_satisfies(activity_topic, required_topic)` function for matching
- Add `board_specific_course` field to CMEActivity for state-specific courses

**Data Structure**:
```python
TOPIC_HIERARCHY = {
    "kasper_opioid": {
        "display_name": "KASPER Opioid Training",
        "parent": "opioid_prescribing",
        "board_specific": "KY",
        "satisfies": ["opioid_prescribing", "controlled_substance_prescribing", "pain_management"]
    },
    "opioid_prescribing": {
        "display_name": "Opioid Prescribing",
        "parent": "controlled_substance_prescribing",
        "board_specific": None,
        "satisfies": ["controlled_substance_prescribing", "pain_management"]
    },
    "controlled_substance_prescribing": {
        "display_name": "Controlled Substance Prescribing",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "category_1": {
        "display_name": "General CME (AMA Category 1)",
        "parent": None,
        "board_specific": None,
        "satisfies": []
    }
}
```

**Tradeoffs**:
- **Pro**: Explicit, auditable relationships
- **Pro**: O(1) lookup for satisfaction check (precomputed `satisfies` list)
- **Pro**: Supports both hierarchy traversal AND explicit overrides
- **Pro**: Board-specific courses clearly marked
- **Con**: Requires manual maintenance of hierarchy
- **Con**: Initial data migration effort

**Best for**: Regulatory compliance systems requiring explicit, auditable logic

### Option B: Tag-Based Inheritance (Rejected)

**Approach**:
- Each topic has multiple tags: `["opioid", "controlled_substance", "category_1"]`
- Matching uses tag intersection
- No explicit parent/child, just overlapping tags

**Tradeoffs**:
- **Pro**: Flexible, easy to add new relationships
- **Pro**: No hierarchy maintenance
- **Con**: Implicit relationships harder to audit
- **Con**: Tag explosion for complex topics
- **Con**: Cannot express "board-specific ONLY" constraint
- **Con**: Risk of unintended matches

**Best for**: Flexible content categorization, not regulatory compliance

### Option C: Database-Stored Hierarchy (Rejected)

**Approach**:
- Store topic hierarchy in database tables
- CMETopic table with `parent_id` foreign key
- Recursive queries for satisfaction check

**Tradeoffs**:
- **Pro**: Dynamic updates without code deployment
- **Pro**: Admin UI for hierarchy management
- **Con**: Recursive queries are slow (O(n) depth)
- **Con**: More complex schema
- **Con**: Regulatory rules change infrequently (code-based is fine)
- **Con**: Harder to version control and audit

**Best for**: Systems with frequently changing hierarchies

---

## Rationale

**Option A (Explicit Topic Hierarchy) was chosen** because:

1. **Regulatory Auditability**: Healthcare CME rules are audited. Explicit `satisfies` lists are defensible:
   - "Why does KY KASPER satisfy FL opioid?" → "Because `kasper_opioid.satisfies` includes `opioid_prescribing`"
   - Implicit tag matching would require explaining inference logic

2. **Performance**: O(1) satisfaction check via precomputed `satisfies` list:
   ```python
   def topic_satisfies(activity_topic, required_topic):
       if activity_topic == required_topic:
           return True
       return required_topic in TOPIC_HIERARCHY.get(activity_topic, {}).get("satisfies", [])
   ```

3. **Board-Specific Enforcement**: `board_specific` field enables strict matching:
   ```python
   # KY KASPER requirement: ONLY accepts kasper-tagged activities
   # General opioid activity does NOT satisfy KY KASPER
   if requirement.board_specific and activity.board_specific_course != requirement.board_specific:
       return False
   ```

4. **Stability**: CME topic relationships change rarely (1-2x/year). Code-based hierarchy with version control is appropriate.

5. **Alignment with FSMB**: Topic hierarchy mirrors FSMB's own categorization (controlled substance → opioid → state-specific).

---

## Implementation Notes

### Schema Changes

**CMEActivity model** (`cme_activity.py`):
```python
# ADD new field
board_specific_course = Column(String(50), nullable=True, index=True)
# Values: "KY_KASPER", "PA_RISK_MGMT", "NJ_ORIENTATION", "LA_ORIENTATION", "FL_LAWS_RULES"
```

**Migration file**: `alembic/versions/002_add_board_specific_course.py`
```python
def upgrade():
    op.add_column('cme_activities',
        sa.Column('board_specific_course', sa.String(50), nullable=True))
    op.create_index('idx_cme_activities_board_specific', 'cme_activities', ['board_specific_course'])

def downgrade():
    op.drop_index('idx_cme_activities_board_specific')
    op.drop_column('cme_activities', 'board_specific_course')
```

### New Files

**1. Topic Hierarchy** (`contexts/cme/topic_hierarchy.py`):
```python
"""
CME Topic Hierarchy for Cross-State Aggregation

Rules:
- More specific topics SATISFY more general topics
- More general topics do NOT satisfy more specific topics
- Board-specific topics require exact match for that state

Example:
  KY KASPER (specific) → satisfies → opioid_prescribing (general)
  opioid_prescribing (general) → does NOT satisfy → KY KASPER (specific)
"""

from typing import Optional, List, Dict

TOPIC_HIERARCHY: Dict[str, Dict] = {
    # ═══════════════════════════════════════════════════════════════
    # LEVEL 4: State/Board-Specific (Most Specific)
    # ═══════════════════════════════════════════════════════════════
    "kasper_opioid": {
        "display_name": "KASPER Opioid Training (KY)",
        "parent": "opioid_prescribing",
        "board_specific": "KY",
        "satisfies": [
            "opioid_prescribing",
            "pain_management",
            "controlled_substance_prescribing",
            "category_1"
        ]
    },
    "pa_risk_management": {
        "display_name": "Board-Approved Risk Management (PA)",
        "parent": "risk_management",
        "board_specific": "PA",
        "satisfies": ["risk_management", "patient_safety", "category_1"]
    },
    "fl_laws_rules": {
        "display_name": "Florida Laws and Rules",
        "parent": "medical_jurisprudence",
        "board_specific": "FL",
        "satisfies": ["medical_jurisprudence", "category_1"]
    },
    "nj_orientation": {
        "display_name": "NJ Board Orientation Course",
        "parent": "medical_jurisprudence",
        "board_specific": "NJ",
        "satisfies": ["medical_jurisprudence", "category_1"]
    },
    "sbirt_training": {
        "display_name": "SBIRT Training (NV)",
        "parent": "substance_abuse_screening",
        "board_specific": "NV",
        "satisfies": ["substance_abuse_screening", "opioid_prescribing", "category_1"]
    },

    # ═══════════════════════════════════════════════════════════════
    # LEVEL 3: Specific Topics
    # ═══════════════════════════════════════════════════════════════
    "opioid_prescribing": {
        "display_name": "Opioid Prescribing",
        "parent": "controlled_substance_prescribing",
        "board_specific": None,
        "satisfies": ["controlled_substance_prescribing", "pain_management", "category_1"]
    },
    "buprenorphine_training": {
        "display_name": "Buprenorphine/MAT Training",
        "parent": "opioid_prescribing",
        "board_specific": None,
        "satisfies": ["opioid_prescribing", "controlled_substance_prescribing", "addiction_medicine", "category_1"]
    },
    "pain_management": {
        "display_name": "Pain Management",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "suicide_prevention": {
        "display_name": "Suicide Prevention",
        "parent": "mental_health",
        "board_specific": None,
        "satisfies": ["mental_health", "category_1"]
    },
    "human_trafficking": {
        "display_name": "Human Trafficking Recognition",
        "parent": "patient_safety",
        "board_specific": None,
        "satisfies": ["patient_safety", "category_1"]
    },
    "implicit_bias": {
        "display_name": "Implicit Bias Training",
        "parent": "cultural_competency",
        "board_specific": None,
        "satisfies": ["cultural_competency", "ethics", "category_1"]
    },
    "domestic_violence": {
        "display_name": "Domestic Violence Recognition",
        "parent": "patient_safety",
        "board_specific": None,
        "satisfies": ["patient_safety", "category_1"]
    },
    "infectious_disease": {
        "display_name": "Infectious Disease",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "hiv_aids": {
        "display_name": "HIV/AIDS",
        "parent": "infectious_disease",
        "board_specific": None,
        "satisfies": ["infectious_disease", "category_1"]
    },
    "geriatric_medicine": {
        "display_name": "Geriatric Medicine",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "end_of_life_care": {
        "display_name": "End of Life Care",
        "parent": "ethics",
        "board_specific": None,
        "satisfies": ["ethics", "category_1"]
    },

    # ═══════════════════════════════════════════════════════════════
    # LEVEL 2: Topic Categories
    # ═══════════════════════════════════════════════════════════════
    "controlled_substance_prescribing": {
        "display_name": "Controlled Substance Prescribing",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "mental_health": {
        "display_name": "Mental Health",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "patient_safety": {
        "display_name": "Patient Safety",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "risk_management": {
        "display_name": "Risk Management",
        "parent": "patient_safety",
        "board_specific": None,
        "satisfies": ["patient_safety", "category_1"]
    },
    "ethics": {
        "display_name": "Medical Ethics",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "cultural_competency": {
        "display_name": "Cultural Competency",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "medical_jurisprudence": {
        "display_name": "Medical Jurisprudence",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "addiction_medicine": {
        "display_name": "Addiction Medicine",
        "parent": "category_1",
        "board_specific": None,
        "satisfies": ["category_1"]
    },
    "substance_abuse_screening": {
        "display_name": "Substance Abuse Screening",
        "parent": "addiction_medicine",
        "board_specific": None,
        "satisfies": ["addiction_medicine", "category_1"]
    },

    # ═══════════════════════════════════════════════════════════════
    # LEVEL 1: Root Categories (Most General)
    # ═══════════════════════════════════════════════════════════════
    "category_1": {
        "display_name": "General CME (AMA Category 1)",
        "parent": None,
        "board_specific": None,
        "satisfies": []
    },
    "aoa_category_1a": {
        "display_name": "Osteopathic CME (AOA Category 1-A)",
        "parent": None,
        "board_specific": None,
        "satisfies": ["category_1"]  # AOA 1-A can satisfy AMA Cat 1
    },
    "aoa_category_1b": {
        "display_name": "AOA Category 1-B",
        "parent": None,
        "board_specific": None,
        "satisfies": []
    },
    "category_2": {
        "display_name": "AMA Category 2",
        "parent": None,
        "board_specific": None,
        "satisfies": []
    },
}


def topic_satisfies(activity_topic: str, required_topic: str) -> bool:
    """
    Check if an activity's topic satisfies a requirement's topic.

    More specific satisfies more general, but NOT vice versa.

    Args:
        activity_topic: The topic of the completed CME activity
        required_topic: The topic required by the state rule

    Returns:
        True if activity_topic can satisfy required_topic

    Examples:
        topic_satisfies("kasper_opioid", "opioid_prescribing") → True
        topic_satisfies("opioid_prescribing", "kasper_opioid") → False
        topic_satisfies("opioid_prescribing", "opioid_prescribing") → True
    """
    # Exact match always satisfies
    if activity_topic == required_topic:
        return True

    # Check if activity_topic declares it satisfies required_topic
    topic_info = TOPIC_HIERARCHY.get(activity_topic, {})
    return required_topic in topic_info.get("satisfies", [])


def get_topic_display_name(topic: str) -> str:
    """Get user-friendly display name for a topic."""
    topic_info = TOPIC_HIERARCHY.get(topic, {})
    return topic_info.get("display_name", topic.replace("_", " ").title())


def is_board_specific(topic: str) -> Optional[str]:
    """
    Check if a topic is board-specific.

    Returns:
        State code if board-specific, None otherwise
    """
    topic_info = TOPIC_HIERARCHY.get(topic, {})
    return topic_info.get("board_specific")


def get_all_satisfied_topics(topic: str) -> List[str]:
    """
    Get all topics that are satisfied by this topic.

    Includes the topic itself plus all topics in its 'satisfies' list.
    """
    result = [topic]
    topic_info = TOPIC_HIERARCHY.get(topic, {})
    result.extend(topic_info.get("satisfies", []))
    return list(set(result))  # Deduplicate


def get_topic_ancestry(topic: str) -> List[str]:
    """
    Get the full ancestry chain from topic to root.

    Returns:
        List from most specific (input topic) to most general (root)
    """
    ancestry = [topic]
    current = topic

    while current:
        topic_info = TOPIC_HIERARCHY.get(current, {})
        parent = topic_info.get("parent")
        if parent:
            ancestry.append(parent)
            current = parent
        else:
            break

    return ancestry
```

**2. Updated Compliance Calculator** (`services/cme_compliance_service.py`):
```python
from ..topic_hierarchy import topic_satisfies, is_board_specific

def activity_satisfies_requirement(
    activity: CMEActivity,
    requirement: CMERule
) -> bool:
    """
    Check if a CME activity satisfies a requirement.

    Considers:
    1. Topic hierarchy (specific satisfies general)
    2. Board-specific constraints (exact match required)
    3. Credit type/category matching
    """
    req_topic = requirement.topic

    # Check board-specific constraint
    req_board_specific = is_board_specific(req_topic)
    if req_board_specific:
        # Requirement is board-specific - activity MUST have matching board_specific_course
        if activity.board_specific_course != req_board_specific:
            return False

    # Check topic satisfaction (hierarchy-aware)
    for activity_topic in activity.topics:
        if topic_satisfies(activity_topic, req_topic):
            return True

    return False
```

### Files to Create

| File | Purpose |
|------|---------|
| `contexts/cme/topic_hierarchy.py` | Topic hierarchy data structure + functions |
| `alembic/versions/002_add_board_specific_course.py` | Database migration |
| `tests/unit/cme/test_topic_hierarchy.py` | Unit tests for hierarchy logic |

### Files to Modify

| File | Changes |
|------|---------|
| `contexts/cme/models/cme_activity.py` | Add `board_specific_course` field |
| `core/services/cme_compliance_service.py` | Use `topic_satisfies()` in matching |
| `contexts/cme/constants.py` | Import and re-export hierarchy |
| `apps/rules-engine/rules_engine/src/compliance_calculator.py` | Integrate hierarchy |

### Data Migration

**Backfill existing activities with board_specific_course**:
```sql
-- Identify activities that are board-specific based on topics
UPDATE cme_activities
SET board_specific_course = 'KY_KASPER'
WHERE 'kasper_pain_addiction' = ANY(topics)
  AND applicable_state = 'KY';

UPDATE cme_activities
SET board_specific_course = 'FL_LAWS_RULES'
WHERE 'florida_laws_rules' = ANY(topics)
  AND applicable_state = 'FL';

-- Continue for other board-specific courses...
```

### Estimated Scope

- **Files to create**: 3
  - Topic hierarchy module
  - Database migration
  - Unit tests

- **Files to modify**: 4
  - CMEActivity model
  - CME compliance service
  - Constants module
  - Compliance calculator

- **Complexity**: Medium
  - Reason: Well-defined data structure, but requires careful testing of hierarchy logic

- **Dependencies**: None (pure Python, no new packages)

---

## Test Cases

```python
# tests/unit/cme/test_topic_hierarchy.py

def test_exact_match_satisfies():
    """Same topic always satisfies itself."""
    assert topic_satisfies("opioid_prescribing", "opioid_prescribing") == True

def test_specific_satisfies_general():
    """More specific topics satisfy more general ones."""
    assert topic_satisfies("kasper_opioid", "opioid_prescribing") == True
    assert topic_satisfies("kasper_opioid", "controlled_substance_prescribing") == True
    assert topic_satisfies("kasper_opioid", "category_1") == True

def test_general_does_not_satisfy_specific():
    """More general topics do NOT satisfy more specific ones."""
    assert topic_satisfies("opioid_prescribing", "kasper_opioid") == False
    assert topic_satisfies("category_1", "opioid_prescribing") == False

def test_board_specific_requires_exact_match():
    """Board-specific requirements need exact course match."""
    # KY KASPER requirement
    kasper_activity = CMEActivity(topics=["kasper_opioid"], board_specific_course="KY_KASPER")
    general_opioid = CMEActivity(topics=["opioid_prescribing"], board_specific_course=None)

    # KY KASPER rule (board-specific)
    kasper_rule = CMERule(topic="kasper_opioid")

    assert activity_satisfies_requirement(kasper_activity, kasper_rule) == True
    assert activity_satisfies_requirement(general_opioid, kasper_rule) == False

def test_cross_state_aggregation():
    """Single activity can satisfy multiple states."""
    kasper_activity = CMEActivity(
        topics=["kasper_opioid"],
        board_specific_course="KY_KASPER",
        credits_earned=3.0
    )

    # KY: Requires KASPER specifically
    assert activity_satisfies_requirement(kasper_activity, CMERule(topic="kasper_opioid")) == True

    # OH: Accepts general opioid
    assert activity_satisfies_requirement(kasper_activity, CMERule(topic="opioid_prescribing")) == True

    # FL: Accepts controlled substance
    assert activity_satisfies_requirement(kasper_activity, CMERule(topic="controlled_substance_prescribing")) == True

def test_aoa_satisfies_ama():
    """AOA Category 1-A can satisfy AMA Category 1 requirements."""
    assert topic_satisfies("aoa_category_1a", "category_1") == True
    assert topic_satisfies("category_1", "aoa_category_1a") == False
```

---

## Consequences

### Enables

- **Cross-state efficiency**: Single CME activity correctly credited across multiple states
- **Board-specific compliance**: KY KASPER, PA Risk Management, etc. properly enforced
- **Accurate gap calculation**: Providers see real gaps, not false positives
- **Audit defensibility**: Explicit `satisfies` lists are auditable
- **Future extensibility**: Easy to add new topics and relationships

### Constrains

- **Manual hierarchy maintenance**: New topics require updating `TOPIC_HIERARCHY`
- **Data migration**: Existing activities need `board_specific_course` backfill
- **Testing burden**: Hierarchy logic requires comprehensive test coverage

---

## Related ADRs

- **ADR-001**: Provider Dashboard Report Generation (uses gap calculation that depends on this)
- **Future**: ADR-003 may cover CME activity auto-classification (using NLP to infer topics)

---

<!--
SYSTEM SECTION - DO NOT EDIT
-->

```yaml
_system:
  created_by: "data-advisor, app-advisor"
  created_at: "2026-01-10T00:00:00Z"
  approved_at: "2026-01-10T00:00:00Z"
  approved_by: "tmac"
  confidence: 91
  auto_decided: false
  escalation_reason: "Strategic domain (data model change, cross-state compliance logic)"
```
