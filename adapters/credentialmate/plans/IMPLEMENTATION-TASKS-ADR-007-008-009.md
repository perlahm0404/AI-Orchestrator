# Implementation Tasks: Duplicate Handling System (ADR-007, 008, 009)

**Generated**: 2026-01-10
**Source**: ADR-007 (Data), ADR-008 (Services), ADR-009 (UX)
**Total Tasks**: 24
**Est. Completion**: 4-6 weeks

---

## Phase 1: Foundation (ADR-007 - Data Architecture)

**Priority**: P1 (Foundation for all other work)
**Estimated**: 1-2 weeks
**Dependencies**: None

### Migration Tasks

#### TASK-ADR007-001: Create migration - Renewal chain tracking
**Type**: migration | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 20

```
Description:
Create Alembic migration to add renewal chain tracking fields to licenses table.

Fields to add:
- renewal_chain_id (UUID)
- previous_version_id (INTEGER FK to licenses.id)
- entry_method (VARCHAR(50))
- entry_context (JSONB)

Also add duplicate_match_type and duplicate_detected_at to cme_activities.

File: apps/backend-api/alembic/versions/20260110_XXXX_01_add_renewal_chain_tracking.py
Tests: Migration rollback test
Completion: MIGRATION_COMPLETE
```

#### TASK-ADR007-002: Create migration - Duplicate detection indexes
**Type**: migration | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 20

```
Description:
Create Alembic migration with 5 categories of indexes for duplicate detection performance:

1. Duplicate detection indexes (licenses, DEA, CSR)
2. CME certificate lookup index
3. Calculable records indexes (exclude_from_calculations filter)
4. Duplicate group indexes (all credential types)
5. Renewal chain index

Use CONCURRENTLY to avoid table locking.

File: apps/backend-api/alembic/versions/20260110_XXXX_02_add_duplicate_detection_indexes.py
Tests: Index existence test, query performance test
Completion: MIGRATION_COMPLETE
```

#### TASK-ADR007-003: Create migration - Cross-org duplicate detection
**Type**: migration | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 20

```
Description:
Create Alembic migration for cross-org duplicate detection infrastructure:

1. Cross-org license lookup index with INCLUDE clause
2. cross_org_access_log table (audit superuser queries)
3. Add 'scope' column to duplicate_events table ('organization' | 'cross_org')
4. Index on duplicate_events where scope='cross_org'

File: apps/backend-api/alembic/versions/20260110_XXXX_03_add_cross_org_indexes.py
Tests: Cross-org query test, audit log test
Completion: MIGRATION_COMPLETE
```

#### TASK-ADR007-004: Create migration - File deduplication fields
**Type**: migration | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 20

```
Description:
Create Alembic migration for file deduplication tracking:

1. Add dedup_source_id (FK to documents.id)
2. Add dedup_reason (VARCHAR(50): 'content_hash_match', 'filename_size_match', 'unique')
3. Index on sha256_hash + organization_id + is_deleted
4. Index on original_filename + file_size_bytes (WHERE created_at > NOW() - 30 days)

File: apps/backend-api/alembic/versions/20260110_XXXX_04_add_file_dedup_fields.py
Tests: Dedup chain test, index test
Completion: MIGRATION_COMPLETE
```

#### TASK-ADR007-005: Create migration - Backfill duplicate metadata
**Type**: migration | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 20

```
Description:
Create data migration to backfill existing records:

1. Set entry_method based on data_source (best guess)
2. Generate duplicate_group_id for existing duplicates (GROUP BY identity fields)
3. Set is_primary_record (MIN(id) per group)
4. Backfill duplicate_match_type for CME activities
5. Link renewal chains (heuristic: same license#, sequential expiration dates)

File: apps/backend-api/alembic/versions/20260110_XXXX_05_backfill_duplicate_metadata.py
Tests: Backfill validation test, rollback test
Completion: MIGRATION_COMPLETE
```

### Model Updates

#### TASK-ADR007-006: Update License model with renewal chain fields
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Add new fields to License model:
- renewal_chain_id: Mapped[UUID | None]
- previous_version_id: Mapped[int | None]
- entry_method: Mapped[str | None]
- entry_context: Mapped[dict | None]

Add relationship:
- previous_version: Mapped["License"] = relationship(foreign_keys=[previous_version_id])

File: apps/backend-api/src/contexts/provider/models/license.py
Tests: Model test, relationship test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR007-007: Update CME Activity model with duplicate fields
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Add missing duplicate tracking fields to CMEActivity model:
- duplicate_match_type: Mapped[str | None]
- duplicate_detected_at: Mapped[datetime | None]
- entry_method: Mapped[str | None]
- entry_context: Mapped[dict | None]

File: apps/backend-api/src/contexts/cme/models/cme_activity.py
Tests: Model test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR007-008: Create CrossOrgAccessLog model
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Create new SQLAlchemy model for cross-org access audit:

class CrossOrgAccessLog(Base):
    id: UUID
    user_id: int (FK to users)
    query_type: str
    credential_type: str
    search_criteria: dict (JSONB)
    result_count: int
    justification: str (required business reason)
    accessed_at: datetime

File: apps/backend-api/src/contexts/audit/models/cross_org_access_log.py
Tests: Model test, FK constraint test
Completion: FEATURE_COMPLETE
```

---

## Phase 2: Service Layer (ADR-008 - Service Architecture)

**Priority**: P1 (Core business logic)
**Estimated**: 2-3 weeks
**Dependencies**: Phase 1 (migrations must be run first)

### Service Refactoring

#### TASK-ADR008-001: Split DuplicateDetectionService (read-only)
**Type**: refactor | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 20

```
Description:
Refactor existing DuplicateDetectionService to be pure read operations:
- find_matches() - Returns list of potential duplicates
- find_matches_cross_org() - Superuser-only, logs to cross_org_access_log

Remove write operations (move to DuplicateHandlingService).

File: apps/backend-api/src/contexts/provider/services/duplicate_detection_service.py
Tests: Unit tests, cross-org audit test
Completion: REFACTOR_COMPLETE
```

#### TASK-ADR008-002: Create DuplicateClassificationService
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
New service for duplicate classification logic:

class DuplicateClassificationService:
    def classify(new_record, matches) -> DuplicateClassification:
        # Perfect/partial/cross-source/renewal detection
        # Confidence scoring based on data source ranking

    def calculate_confidence(new, existing) -> float:
        # Source ranking: verified_external=1.0 to legacy_import=0.4

File: apps/backend-api/src/contexts/duplicates/services/duplicate_classification_service.py
Tests: Classification tests (perfect/partial/cross-source/renewal), confidence tests
Completion: FEATURE_COMPLETE
```

#### TASK-ADR008-003: Create DuplicateResolutionService
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
New service for duplicate resolution operations:

class DuplicateResolutionService:
    async def merge_duplicates(group_id, primary_id, reason, actor)
    async def keep_both(group_id, reason, actor)
    async def undo_resolution(group_id, actor)
    async def auto_resolve(record, matches, classification, actor)

All methods create audit events.

File: apps/backend-api/src/contexts/duplicates/services/duplicate_resolution_service.py
Tests: Merge test, undo test, audit event test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR008-004: Create DuplicateAuditService
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
New service for duplicate event tracking:

class DuplicateAuditService:
    async def create_event(event_type, credential_type, new_id, existing_ids, actor, classification)
    async def query_events(filters) -> List[DuplicateEvent]

Uses existing duplicate_events table.

File: apps/backend-api/src/contexts/duplicates/services/duplicate_audit_service.py
Tests: Event creation test, query test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR008-005: Create DuplicateOrchestrator facade
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Facade pattern to coordinate all duplicate services:

class DuplicateOrchestrator:
    def __init__(self):
        self.detection = DuplicateDetectionService()
        self.classification = DuplicateClassificationService()
        self.resolution = DuplicateResolutionService()
        self.audit = DuplicateAuditService()
        self.event_bus = DuplicateEventBus()

    async def detect_and_accept(credential_type, data, data_source, entry_method, actor)

This is the main entry point used by all credential creation endpoints.

File: apps/backend-api/src/contexts/duplicates/services/duplicate_orchestrator.py
Tests: Integration tests, workflow tests
Completion: FEATURE_COMPLETE
```

### Caching Layer

#### TASK-ADR008-006: Implement 3-layer caching for duplicate detection
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Add multi-layer cache wrapper around DuplicateDetectionService:

Layer 1: Request-scoped (@lru_cache, 100 entries)
Layer 2: Redis cache (5 min TTL)
Layer 3: Precomputed duplicate groups (hourly refresh by background job)

class CachedDuplicateDetection:
    @lru_cache(maxsize=100)
    def find_matches_request_scope(key)

    async def find_matches_cached(type, data, org_id)  # Redis

    async def get_precomputed_groups(provider_id, org_id)  # Precomputed

Cache invalidation on create/update/delete.

File: apps/backend-api/src/contexts/duplicates/services/cached_duplicate_detection.py
Tests: Cache hit test, invalidation test, performance test
Completion: FEATURE_COMPLETE
```

### Event Bus

#### TASK-ADR008-007: Create DuplicateEventBus for pub/sub
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Event bus for async duplicate processing:

class DuplicateEventBus:
    async def emit(event: DuplicateEvent):
        # 1. Store in database (already done by AuditService)
        # 2. Emit to Redis queue for background processing
        # 3. Emit WebSocket for real-time UI updates
        # 4. Record metrics

Integrates with existing Celery workers.

File: apps/backend-api/src/contexts/duplicates/events/event_bus.py
Tests: Event emission test, queue test, WebSocket test
Completion: FEATURE_COMPLETE
```

### Background Jobs

#### TASK-ADR008-008: Create DuplicateQAProcessor background job
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Celery task that runs every 6 hours:

@celery.task
@celery_schedule(crontab(minute=0, hour='*/6'))
def duplicate_qa_processor():
    # 1. Find new duplicate candidates since last run
    # 2. Classify each candidate
    # 3. Auto-resolve if confidence > 0.95
    # 4. Flag for review if confidence 0.80-0.95
    # 5. Generate daily report (midnight run)

File: apps/worker-tasks/tasks/duplicates/qa_processor.py
Tests: Job execution test, auto-resolve test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR008-009: Create DuplicateCleanupJob background job
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Celery task that runs daily at 2 AM:

@celery.task
@celery_schedule(crontab(minute=0, hour=2))
def duplicate_cleanup_job():
    # Delete perfect duplicates (same source) older than 2 years
    # Keep perfect duplicates (cross-source) for 10 years
    # Keep partial duplicates for 10 years
    # Keep cross-org duplicates for 10 years

Implements tiered retention policy from ADR-007.

File: apps/worker-tasks/tasks/duplicates/cleanup_job.py
Tests: Retention policy test, deletion test
Completion: FEATURE_COMPLETE
```

### API Endpoints

#### TASK-ADR008-010: Create duplicate resolution API endpoints
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
New FastAPI router for duplicate management:

GET /api/v1/duplicates/suggestions?provider_id={id}&credential_type={type}
  → Returns prioritized list of duplicate groups for review

POST /api/v1/duplicates/resolve
  → Body: {group_id, action: merge|keep_both|unrelated, primary_record_id, reason}
  → Calls ResolutionService

POST /api/v1/duplicates/{group_id}/undo
  → Undo previous resolution (admin-only)

GET /api/v1/duplicates/events?filters={...}
  → Query duplicate audit events

File: apps/backend-api/app/api/v1/duplicates/duplicate_endpoints.py
Tests: API tests (201/409/200), permission tests
Completion: FEATURE_COMPLETE
```

#### TASK-ADR008-011: Create Pydantic schemas for duplicate API
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Pydantic schemas for duplicate resolution API:

- DuplicateResolutionRequest (group_id, action, primary_record_id, reason)
- ResolutionResult (success, message, audit_event_id)
- DuplicateSuggestionsResponse (suggestions: List[DuplicateGroup])
- DuplicateGroup (group_id, records, match_type, confidence, priority)
- ResolutionOption (action, requires_approval)

File: apps/backend-api/app/api/v1/duplicates/schemas.py
Tests: Schema validation tests
Completion: FEATURE_COMPLETE
```

#### TASK-ADR008-012: Update credential creation endpoints to use orchestrator
**Type**: refactor | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 20

```
Description:
Update all credential creation endpoints to use DuplicateOrchestrator:

- POST /licenses
- POST /cme/activities
- POST /dea-registrations
- POST /csrs
- POST /coordinator/credentials/bulk-create

Replace direct calls to DuplicateHandlingService with orchestrator.detect_and_accept().

Files:
- apps/backend-api/src/contexts/provider/api/provider_endpoints.py
- apps/backend-api/src/contexts/cme/api/cme_endpoints.py
- apps/backend-api/src/contexts/coordinator/api/coordinator_credential_endpoints.py
Tests: Integration tests, HTTP 409 response tests
Completion: REFACTOR_COMPLETE
```

---

## Phase 3: User Experience (ADR-009 - UX/UI Design)

**Priority**: P1 (User-facing functionality)
**Estimated**: 2-3 weeks
**Dependencies**: Phase 2 (services must exist first)

### UI Components

#### TASK-ADR009-001: Create DuplicateWarningToast component
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
React component for inline duplicate warning (non-blocking):

- Alert banner with orange color scheme
- AlertTriangle icon + message
- "Review duplicates" link to dashboard
- Dismissible
- Appears after form submission if duplicate detected

File: apps/frontend-web/src/components/duplicates/DuplicateWarningToast.tsx
Tests: Component test, accessibility test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR009-002: Create ConfidenceIndicator component
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Traffic light visualization for duplicate confidence (0.0-1.0 → high/medium/low):

- High (>0.95): Red, "Very Likely Duplicate", AlertCircle icon
- Medium (0.80-0.95): Orange, "Possible Duplicate", AlertTriangle icon
- Low (<0.80): Yellow, "Similarity Detected", Info icon

Color + icon + text (WCAG AA compliant).

File: apps/frontend-web/src/components/duplicates/ConfidenceIndicator.tsx
Tests: Component test, color contrast test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR009-003: Create SourceBadge component
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Badge showing data source trust level:

- verified_external: "Verified by Board", green, CheckCircle icon
- document_upload: "From Document", blue, FileText icon
- manual_entry: "Manual Entry", gray, Edit icon

Tooltip with description.

File: apps/frontend-web/src/components/duplicates/SourceBadge.tsx
Tests: Component test, tooltip test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR009-004: Create ComparisonTable component
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Side-by-side diff view for duplicate records:

- Semantic HTML table with ARIA labels
- Matched fields: gray background, green checkmark
- Differing fields: orange background, AlertTriangle icon
- Source badges for each record
- Keyboard navigable
- Screen reader compatible

File: apps/frontend-web/src/components/duplicates/ComparisonTable.tsx
Tests: Component test, accessibility test (jest-axe), keyboard nav test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR009-005: Create ResolutionWizard component (3-step)
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Multi-step wizard for duplicate resolution:

Step 1: Review Matches
  - Show ConfidenceIndicator
  - Show ComparisonTable
  - "Next: Choose Action" button

Step 2: Choose Action
  - Radio group: keep_both | merge | unrelated
  - Description for each option
  - "Next: Select Primary" (if merge) or "Complete" button

Step 3: Select Primary (only for merge)
  - Radio group of records with SourceBadge
  - Recommend based on data_source confidence
  - "Merge Records" button

All steps keyboard accessible, ARIA live regions announce changes.

File: apps/frontend-web/src/components/duplicates/ResolutionWizard.tsx
Tests: Wizard flow test, keyboard nav test, screen reader test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR009-006: Create DuplicatesDashboard page
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Prioritized review queue dashboard:

- Priority tabs: All | High (red) | Medium (orange) | Low (yellow)
- DuplicateReviewCard for each group
- Export CSV button
- Empty state when no duplicates
- Loading state

Fetches data from GET /api/v1/duplicates/suggestions.

File: apps/frontend-web/src/pages/duplicates/DuplicatesDashboard.tsx
Tests: Page test, tab switching test, export test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR009-007: Add real-time duplicate check to LicenseForm
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Add debounced duplicate detection to license entry form:

- useQuery with duplicate check API
- Enabled when license_number.length >= 5 && state
- 30s stale time (cache)
- Show inline warning (non-blocking) if duplicate detected
- NEVER disable submit button

File: apps/frontend-web/src/components/credentials/LicenseForm.tsx
Tests: Form test, debounce test, warning display test
Completion: FEATURE_COMPLETE
```

#### TASK-ADR009-008: Add real-time duplicate check to CMEActivityForm
**Type**: feature | **Agent**: FeatureBuilder | **Priority**: P1 | **Iterations**: 50

```
Description:
Same as TASK-ADR009-007 but for CME activity form.

Duplicate check triggers when:
- certificate_number exists OR
- activity_title + completion_date + activity_provider filled

File: apps/frontend-web/src/components/cme/CMEActivityForm.tsx
Tests: Form test, warning display test
Completion: FEATURE_COMPLETE
```

---

## Summary Statistics

**Total Tasks**: 24
**By Type**:
- Migration: 5
- Feature: 16
- Refactor: 3

**By Phase**:
- Phase 1 (Data): 8 tasks
- Phase 2 (Services): 12 tasks
- Phase 3 (UX): 8 tasks

**By Priority**:
- P0: 0
- P1: 24

**Estimated Iterations**: 810 total (avg 34 per task)

**Critical Path**:
1. Run migrations (TASK-ADR007-001 through 005)
2. Update models (TASK-ADR007-006 through 008)
3. Build services (TASK-ADR008-001 through 005)
4. Add caching/events (TASK-ADR008-006 through 007)
5. Build UI components (TASK-ADR009-001 through 005)
6. Integrate UI (TASK-ADR009-006 through 008)

---

## Next Steps

1. **Approve ADRs**: Review and approve ADR-007, 008, 009
2. **Register tasks**: Add these tasks to work_queue_credentialmate_features.json
3. **Run migrations**: Execute migrations 001-005 in CredentialMate dev environment
4. **Start autonomous loop**: Begin with Phase 1 tasks
5. **Incremental deployment**: Deploy and test each phase before proceeding

---

**Generated by**: AI Orchestrator ADR-to-Tasks System
**Generation Date**: 2026-01-10
