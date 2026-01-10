# Advisor Automation Implementation Plan

**Status:** Planned
**Priority:** P1 (Critical Infrastructure Gap)
**Estimated Effort:** 2-3 days
**Owner:** AI Orchestrator Team
**Version:** 1.0
**Created:** 2026-01-10

---

## Executive Summary

**Problem:** Advisors provide strategic recommendations but require manual ADR creation and task logging. This breaks the autonomous workflow and creates governance gaps.

**Current Flow (Manual):**
```
Human asks question
  → Advisor consulted (via Skill tool)
  → Advisor returns decision with 78.5% confidence
  → ❌ STOPS - Human must manually create ADR
  → ❌ STOPS - Human must manually add tasks to work queue
  → ❌ STOPS - No governance audit trail
```

**Target Flow (Automated):**
```
Strategic decision detected (or confidence ≥ 85%)
  → Advisor auto-consulted
  → Decision with context captured
  → ✅ Auto-create draft ADR (markdown)
  → ✅ Parse ADR and extract tasks
  → ✅ Add tasks to work_queue.json
  → ✅ Log in governance/contracts/advisor_decisions.json
  → ✅ Trigger Coordinator.on_adr_approved()
  → ✅ Assign tasks to builders
```

**Impact:**
- **89% → 95%+ autonomy** (eliminates manual ADR creation bottleneck)
- **100% governance coverage** (all strategic decisions documented)
- **0-touch task registration** (advisors directly populate work queue)

---

## Architecture Overview

### New Components

```
orchestration/
├── advisor_to_adr.py          # NEW: Advisor decision → ADR converter
├── adr_to_tasks.py            # NEW: ADR markdown → Task objects
├── advisor_integration.py     # MODIFIED: Add auto-ADR trigger
└── adr_automation.py          # NEW: Orchestration layer

governance/contracts/
├── advisor_decisions.json     # NEW: Audit log of all advisor decisions
└── adr_metadata.json          # NEW: ADR lifecycle tracking

agents/coordinator/
└── coordinator.py             # MODIFIED: Accept advisor-generated ADRs
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Advisor Consultation                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Task description analyzed                                    │
│  2. Domain patterns matched (data/app/uiux)                      │
│  3. Advisor consulted with context                               │
│  4. AdvisorDecision returned                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              AdvisorADRGenerator (NEW)                           │
├─────────────────────────────────────────────────────────────────┤
│  5. Check: strategic OR confidence ≥ 85%?                        │
│  6. Generate ADR markdown with:                                  │
│     - Decision context                                           │
│     - Advisor recommendations                                    │
│     - Tags and metadata                                          │
│     - Implementation tasks section                               │
│  7. Write to docs/AI-Team-Plans/decisions/ADR-XXX-title.md      │
│  8. Log to governance/contracts/advisor_decisions.json          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ADRTaskExtractor (NEW)                              │
├─────────────────────────────────────────────────────────────────┤
│  9. Parse ADR markdown                                           │
│ 10. Extract tasks from ## Tasks or ## Implementation sections   │
│ 11. Detect dependencies (depends_on patterns)                   │
│ 12. Assign task types (bugfix/feature/test based on keywords)   │
│ 13. Generate Task objects                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Coordinator Integration                             │
├─────────────────────────────────────────────────────────────────┤
│ 14. Add tasks to adapters/{project}/tasks/work_queue.json       │
│ 15. Trigger Coordinator.on_adr_approved(adr_path)               │
│ 16. Coordinator assigns tasks to builders                        │
│ 17. Update PROJECT_HQ.md with new ADR                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Implementation Tasks

### Phase 1: Core Automation (Day 1)

#### **Task 1.1: Create AdvisorADRGenerator**
**File:** `orchestration/advisor_to_adr.py`

**Responsibilities:**
- Convert `AdvisorDecision` → ADR markdown
- Generate unique ADR numbers (scan existing ADRs)
- Apply ADR template with decision context
- Write to correct directory (`docs/AI-Team-Plans/decisions/`)

**Key Methods:**
```python
class AdvisorADRGenerator:
    def should_create_adr(self, decision: AdvisorDecision) -> bool:
        """
        Determine if decision warrants ADR creation.

        Criteria:
        - DecisionType.STRATEGIC (always)
        - OR confidence.total >= 0.85 (high confidence tactical)
        - AND auto_approved == True (no escalation)
        """

    def generate_adr_number(self) -> int:
        """
        Scan docs/AI-Team-Plans/decisions/ for existing ADRs.
        Return next available number (ADR-001, ADR-002, etc.)
        """

    def create_draft_adr(
        self,
        decision: AdvisorDecision,
        question: str,
        context: Dict[str, Any]
    ) -> Path:
        """
        Generate ADR markdown file.

        Returns: Path to created ADR file
        """

    def _build_adr_content(
        self,
        number: int,
        title: str,
        decision: AdvisorDecision,
        question: str,
        context: Dict[str, Any]
    ) -> str:
        """Build ADR markdown content from template."""

    def log_decision(
        self,
        decision: AdvisorDecision,
        adr_path: Path
    ) -> None:
        """Log to governance/contracts/advisor_decisions.json"""
```

**ADR Template:**
```markdown
# ADR-{number}: {title}

**Status:** Draft (Auto-generated by {advisor_type}-advisor)
**Date:** {timestamp}
**Confidence:** {confidence}%
**Decision Type:** {strategic/tactical}
**Tags:** {domain_tags}

---

## Context

{question}

**Detected Domains:** {detected_domains}
**Aligned ADRs:** {aligned_adrs}
**Conflicting ADRs:** {conflicting_adrs}

---

## Decision

{recommendation}

---

## Implementation Tasks

{parsed_tasks_from_recommendation}

---

## Consequences

### Positive
- {auto_generated_from_recommendation}

### Negative
- {auto_generated_risks}

---

## Metadata

- **Advisor:** {advisor_type}-advisor
- **Auto-approved:** {auto_approved}
- **Escalated:** {escalated}
- **Escalation Reason:** {escalation_reason}
- **Created by:** AI Team Automation
- **Source:** AdvisorDecision({decision_id})
```

**Acceptance Criteria:**
- ✅ ADR files numbered sequentially
- ✅ ADR markdown valid and parseable
- ✅ All decision metadata preserved
- ✅ Tasks section properly formatted for extraction

---

#### **Task 1.2: Create ADRTaskExtractor**
**File:** `orchestration/adr_to_tasks.py`

**Responsibilities:**
- Parse ADR markdown
- Extract implementation tasks
- Detect task dependencies
- Assign task types and priorities

**Key Methods:**
```python
class ADRTaskExtractor:
    def extract_tasks(self, adr_path: Path) -> List[Task]:
        """
        Parse ADR and extract tasks.

        Returns: List of Task objects ready for work queue
        """

    def _parse_task_section(self, content: str) -> List[Dict[str, Any]]:
        """
        Find ## Tasks or ## Implementation section.
        Parse task list items (- [ ] Task description).
        """

    def _detect_dependencies(self, task_desc: str) -> List[str]:
        """
        Look for patterns like:
        - "depends on T1.1"
        - "requires Task 2"
        - "after completing X"
        """

    def _infer_task_type(self, task_desc: str) -> TaskType:
        """
        Classify task based on keywords:
        - bugfix: "fix", "bug", "error", "issue"
        - feature: "add", "implement", "create", "new"
        - test: "test", "spec", "coverage"
        - refactor: "refactor", "clean", "improve"
        """

    def _assign_priority(
        self,
        task_desc: str,
        adr_status: str
    ) -> str:
        """
        P0: "critical", "blocking", "urgent"
        P1: "important", "required", "must"
        P2: everything else
        """
```

**Task Parsing Examples:**

```markdown
## Tasks

- [ ] **T1.1:** Create AdvisorADRGenerator class
  - File: orchestration/advisor_to_adr.py
  - Implements should_create_adr(), create_draft_adr()

- [ ] **T1.2:** Add integration tests (depends on T1.1)
  - File: tests/test_advisor_automation.py
```

**Parsed Output:**
```python
[
    Task(
        id="ADR-005-T1-1",
        description="Create AdvisorADRGenerator class",
        file_path="orchestration/advisor_to_adr.py",
        task_type=TaskType.FEATURE,
        priority="P1",
        depends_on=[],
        status=TaskStatus.PENDING
    ),
    Task(
        id="ADR-005-T1-2",
        description="Add integration tests",
        file_path="tests/test_advisor_automation.py",
        task_type=TaskType.TEST,
        priority="P1",
        depends_on=["ADR-005-T1-1"],
        status=TaskStatus.PENDING
    )
]
```

**Acceptance Criteria:**
- ✅ Handles both checkbox `- [ ]` and bullet `-` format
- ✅ Extracts task IDs (T1.1, T1.2) or generates them
- ✅ Detects dependencies from description text
- ✅ Assigns correct task types (80%+ accuracy)
- ✅ Preserves file paths and context

---

#### **Task 1.3: Create ADRAutomation Orchestrator**
**File:** `orchestration/adr_automation.py`

**Responsibilities:**
- Coordinate advisor → ADR → tasks flow
- Handle errors and fallbacks
- Provide CLI interface for testing

**Key Methods:**
```python
class ADRAutomation:
    def __init__(self, project_root: Path):
        self.adr_generator = AdvisorADRGenerator(project_root)
        self.task_extractor = ADRTaskExtractor()
        self.work_queue = WorkQueue(project_root)

    def process_advisor_decision(
        self,
        decision: AdvisorDecision,
        question: str,
        context: Dict[str, Any],
        auto_register: bool = True
    ) -> Dict[str, Any]:
        """
        Full automation pipeline:
        1. Check if ADR needed
        2. Create draft ADR
        3. Extract tasks
        4. Register with work queue
        5. Return summary
        """

    def create_adr_only(
        self,
        decision: AdvisorDecision,
        question: str,
        context: Dict[str, Any]
    ) -> Path:
        """Create ADR without task registration."""

    def register_tasks_only(self, adr_path: Path) -> List[Task]:
        """Extract and register tasks from existing ADR."""
```

**Return Format:**
```python
{
    "adr_created": True,
    "adr_path": "docs/AI-Team-Plans/decisions/ADR-005-advisor-automation.md",
    "adr_number": 5,
    "tasks_extracted": 14,
    "tasks_registered": 14,
    "work_queue_path": "adapters/ai_orchestrator/tasks/work_queue.json",
    "status": "success",
    "errors": []
}
```

**Acceptance Criteria:**
- ✅ Handles errors gracefully (rollback on failure)
- ✅ Returns detailed summary of actions taken
- ✅ Logs all steps for debugging
- ✅ Supports dry-run mode (no file writes)

---

### Phase 2: Integration (Day 2)

#### **Task 2.1: Update AdvisorIntegration**
**File:** `orchestration/advisor_integration.py`

**Changes:**
- Add `adr_automation` attribute
- Trigger ADR creation in `consult()` method
- Update `pre_task_analysis()` to return ADR info

**Modified Methods:**
```python
class AdvisorRouter:
    def __init__(self, project_root: Path):
        # ... existing code ...
        self.adr_automation = ADRAutomation(project_root)

    def consult(
        self,
        task_id: str,
        advisor_type: AdvisorType,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        on_escalate: Optional[Callable] = None,
    ) -> AdvisorConsultation:
        advisor = self._get_advisor(advisor_type)
        decision = advisor.consult(question, context or {}, on_escalate)

        # NEW: Auto-create ADR if strategic or high-confidence
        adr_result = None
        if self.adr_automation.adr_generator.should_create_adr(decision):
            adr_result = self.adr_automation.process_advisor_decision(
                decision=decision,
                question=question,
                context=context or {},
                auto_register=True
            )

        consultation = AdvisorConsultation(
            task_id=task_id,
            advisor_type=advisor_type,
            question=question,
            recommendation=decision.recommendation,
            confidence=decision.confidence.total,
            auto_approved=decision.auto_approved,
            escalated=decision.escalated,
            escalation_reason=decision.escalation_reason,
            adr_created=adr_result is not None,  # NEW
            adr_path=adr_result["adr_path"] if adr_result else None,  # NEW
        )

        self.consultations.append(consultation)
        return consultation
```

**Acceptance Criteria:**
- ✅ ADR creation only triggered for strategic/high-confidence
- ✅ Consultation records include ADR metadata
- ✅ Errors don't break existing consultation flow
- ✅ Backward compatible (works with old code)

---

#### **Task 2.2: Update Coordinator**
**File:** `agents/coordinator/coordinator.py`

**Changes:**
- Accept ADRs created by automation
- Skip duplicate detection for advisor-generated ADRs
- Log automation source in PROJECT_HQ.md

**Modified Methods:**
```python
class Coordinator:
    def on_adr_approved(self, adr_path: Path) -> List[Task]:
        adr = ADR.from_file(adr_path)

        # NEW: Check if ADR was auto-generated
        is_automated = self._is_automated_adr(adr)

        if is_automated:
            # Tasks already in work queue, just acknowledge
            self.logger.info(f"Automated ADR detected: {adr.id}")
            self._update_adr_index(adr)
            return []

        # Existing manual flow
        tasks = self._break_into_tasks(adr)
        for task in tasks:
            self.task_manager.add_task(task)

        return tasks

    def _is_automated_adr(self, adr: ADR) -> bool:
        """Check if ADR was created by automation."""
        return "Auto-generated by" in adr.implementation_notes.get("metadata", {}).get("created_by", "")
```

**Acceptance Criteria:**
- ✅ Coordinator recognizes automated ADRs
- ✅ No duplicate task creation
- ✅ PROJECT_HQ.md updated correctly
- ✅ Manual ADRs still work as before

---

#### **Task 2.3: Add Governance Logging**
**File:** `governance/contracts/advisor_decisions.json`

**Schema:**
```json
{
  "decisions": [
    {
      "id": "decision-001",
      "timestamp": "2026-01-10T13:45:00Z",
      "advisor_type": "data",
      "question": "Should we use UUID or Integer for report_jobs PK?",
      "recommendation": "Use Integer PKs consistently with existing schema",
      "confidence": 0.85,
      "decision_type": "strategic",
      "auto_approved": true,
      "escalated": false,
      "adr_created": true,
      "adr_number": 5,
      "adr_path": "docs/AI-Team-Plans/decisions/ADR-005-report-jobs-schema.md",
      "tasks_generated": 3,
      "project": "credentialmate",
      "context": {
        "task_id": "ADR-001-Phase1-T5",
        "file_path": "apps/backend-api/src/contexts/reports/models/report_job.py"
      }
    }
  ],
  "metadata": {
    "total_decisions": 1,
    "adrs_created": 1,
    "tasks_generated": 3,
    "last_updated": "2026-01-10T13:45:00Z"
  }
}
```

**Logging Functions:**
```python
def log_advisor_decision(
    decision: AdvisorDecision,
    adr_result: Dict[str, Any],
    project: str,
    context: Dict[str, Any]
) -> None:
    """Append decision to governance log."""

def get_decision_history(
    advisor_type: Optional[str] = None,
    project: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Query decision history with filters."""
```

**Acceptance Criteria:**
- ✅ All advisor decisions logged (even if no ADR created)
- ✅ JSON schema validated
- ✅ Log rotation (max 1000 entries, archive old)
- ✅ Query interface for analytics

---

### Phase 3: Testing & Documentation (Day 3)

#### **Task 3.1: Integration Tests**
**File:** `tests/test_advisor_automation.py`

**Test Scenarios:**
```python
def test_advisor_decision_to_adr_creation():
    """Test: Strategic decision → ADR created"""

def test_adr_task_extraction():
    """Test: ADR markdown → Task objects"""

def test_work_queue_registration():
    """Test: Tasks added to work_queue.json"""

def test_coordinator_integration():
    """Test: Coordinator.on_adr_approved() triggered"""

def test_governance_logging():
    """Test: Decision logged to advisor_decisions.json"""

def test_confidence_threshold():
    """Test: Only ≥85% confidence creates ADR"""

def test_escalation_handling():
    """Test: Escalated decisions don't auto-create ADR"""

def test_duplicate_adr_prevention():
    """Test: Don't create duplicate ADRs for same decision"""

def test_error_handling():
    """Test: Graceful failure and rollback"""
```

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ 90%+ code coverage for new modules
- ✅ Integration tests run E2E flow
- ✅ Mock advisors for deterministic testing

---

#### **Task 3.2: CLI Commands**
**File:** `cli/commands/advisor.py`

**New Commands:**
```bash
# Auto-create ADR from advisor decision
aibrain advisor create-adr \
  --advisor data \
  --question "Should we add indexes to users table?" \
  --project credentialmate

# Extract tasks from existing ADR
aibrain advisor extract-tasks \
  --adr-path docs/AI-Team-Plans/decisions/ADR-005-title.md

# List all advisor decisions
aibrain advisor decisions list \
  --advisor data \
  --project credentialmate

# Show decision details
aibrain advisor decisions show decision-001
```

**Acceptance Criteria:**
- ✅ Commands work from CLI
- ✅ Help text clear and complete
- ✅ Error messages actionable
- ✅ Supports dry-run mode

---

#### **Task 3.3: Documentation**
**Files to Update:**
- `docs/AI-Team-Plans/AI-TEAM-SPEC-V3.md` - Add automation section
- `README.md` - Update workflow diagram
- `orchestration/README.md` - Document new modules

**Documentation Sections:**
1. **Advisor Automation Overview**
   - Architecture diagram
   - Data flow
   - Decision criteria

2. **Developer Guide**
   - How to use automation
   - How to override (manual ADR)
   - How to query decisions

3. **Troubleshooting**
   - Common issues
   - Debug logging
   - Rollback procedures

**Acceptance Criteria:**
- ✅ All new modules documented
- ✅ Examples for common use cases
- ✅ Architecture diagrams updated
- ✅ Migration guide for existing projects

---

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Manual ADR Creation** | 100% | 0% | 0% |
| **Advisor Decision Logging** | 0% | 100% | 100% |
| **Strategic Decision → ADR** | 0% | 100% | 100% |
| **ADR → Tasks Automation** | 0% | 100% | 100% |
| **Autonomy Score** | 89% | 95%+ | 95% |
| **Decision Audit Coverage** | 50% | 100% | 100% |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ADR numbering conflicts | Low | Medium | File lock or atomic increment |
| Malformed ADR markdown | Medium | Low | Validate before write, rollback on error |
| Task extraction accuracy | Medium | Medium | Start with simple patterns, improve iteratively |
| Coordinator integration breaks | Low | High | Extensive integration tests, feature flag |
| Performance (parsing large ADRs) | Low | Low | Lazy loading, caching |

---

## Migration Strategy

### Week 1: Development
- Days 1-2: Implement Phase 1 (core automation)
- Day 3: Implement Phase 2 (integration)

### Week 2: Testing
- Days 1-2: Write tests, fix bugs
- Day 3: Documentation

### Week 3: Rollout
- Day 1: Deploy to AI_Orchestrator repo
- Day 2: Test with karematch project
- Day 3: Test with credentialmate project

### Rollback Plan
If automation causes issues:
1. Set feature flag `ENABLE_ADVISOR_AUTOMATION=false`
2. Advisors continue to work normally
3. ADRs created manually as before
4. No data loss (all decisions logged)

---

## Open Questions

1. **ADR Template Customization**: Should different advisor types have different ADR templates?
   - Recommendation: Start with single template, customize later if needed

2. **Task Numbering**: Should task IDs include ADR number (ADR-005-T1) or be sequential (T-001)?
   - Recommendation: Include ADR number for traceability

3. **Approval Workflow**: Should automated ADRs require human approval before task execution?
   - Recommendation: Auto-approve for confidence ≥85%, manual for 70-84%

4. **Conflict Resolution**: What if advisor recommends different approach than existing ADR?
   - Recommendation: Log as conflicting ADR, escalate to human

5. **ADR Updates**: If decision changes, update existing ADR or create new one?
   - Recommendation: Create new ADR with reference to superseded one

---

## Timeline

| Week | Days | Deliverable |
|------|------|-------------|
| **1** | 1-2 | Phase 1 complete (core modules) |
| **1** | 3 | Phase 2 complete (integration) |
| **2** | 1-2 | Phase 3 tests complete |
| **2** | 3 | Documentation complete |
| **3** | 1-3 | Production rollout |
| **Total** | **9 days** | Full automation live |

Compressed timeline: **3 days** if focused implementation (skip some docs, defer tests to post-launch).

---

## References

- **AI-TEAM-SPEC-V3**: Advisor roles and responsibilities
- **orchestration/advisor_integration.py**: Existing advisor infrastructure
- **agents/coordinator/coordinator.py**: ADR → Task flow
- **tasks/work_queue.py**: Work queue management

---

## Next Steps

1. **Review this plan** with team
2. **Approve Phase 1 implementation**
3. **Create GitHub issues** for each task (14 total)
4. **Start development** with Task 1.1 (AdvisorADRGenerator)

**Decision:** Proceed with implementation? [Y/N]
