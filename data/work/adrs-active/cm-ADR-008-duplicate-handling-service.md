---
# Document Metadata
doc-id: "cm-ADR-008"
title: "Duplicate Handling Service Architecture"
created: "2026-01-10"
updated: "2026-01-10"
author: "Claude AI"
status: "draft"

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
relates-to: ["ADR-007", "ADR-009"]

# Change Control
version: "1.0"
---

# ADR-008: Duplicate Handling Service Architecture

**Date**: 2026-01-10
**Status**: draft
**Advisor**: app-advisor
**Deciders**: tmac

---

## Tags

```yaml
tags: [duplicate-handling, service-architecture, api-design, event-driven, caching, background-jobs]
applies_to:
  - "apps/backend-api/src/contexts/provider/services/**"
  - "apps/backend-api/src/contexts/cme/services/**"
  - "apps/backend-api/app/api/v1/duplicates/**"
  - "apps/worker-tasks/tasks/duplicates/**"
domains: [backend, architecture, api-design, performance]
```

---

## Context

CredentialMate's current duplicate handling has two services (`DuplicateDetectionService` and `DuplicateHandlingService`) but lacks:

**Service Architecture Gaps:**
1. **No resolution service**: Backend marks duplicates but no API to merge/resolve them
2. **No event-driven architecture**: Duplicate detection is synchronous, blocks API requests
3. **No caching layer**: Expensive duplicate detection queries run on every create (table scans)
4. **No background jobs**: Perfect duplicates auto-hidden but never cleaned up
5. **No cross-cutting coordination**: Duplicate detection scattered across bounded contexts

**Current Services:**
- `DuplicateDetectionService`: Finds perfect/partial/cross-source matches (read-only)
- `DuplicateHandlingService`: Creates records, marks duplicates, emits events (write operations)

**API Gaps:**
- HTTP 409 errors contain duplicate info but no resolution endpoints
- No way to merge duplicates via API
- No bulk duplicate resolution
- No undo functionality

**Performance Issues (from investigation):**
- Duplicate detection queries cause table scans (no indexes until ADR-002)
- No request-scoped caching (same query runs multiple times in bulk creates)
- No Redis caching (cross-request duplicate checks)

---

## Decision

**Implement event-driven service architecture with 4 bounded contexts and background processing:**

1. **Split services into 4 specialized contexts** (DetectionService, ClassificationService, ResolutionService, AuditService)
2. **Expose duplicate resolution API endpoints** (merge, keep both, archive)
3. **Implement event-driven architecture** with pub/sub for async processing
4. **Add 3-layer caching strategy** (request-scoped, Redis, precomputed groups)
5. **Create 2 background jobs** (QA processor every 6 hours, cleanup daily)
6. **Use saga pattern** for cross-cutting duplicate coordination
7. **Enhance error handling** with structured HTTP 409 responses and resolution options

---

## Options Considered

### Option A: Event-Driven Service Architecture with Saga Pattern (CHOSEN)

**Approach**:
- Split into 4 services: Detection, Classification, Resolution, Audit
- Use domain events + saga coordinator for cross-context orchestration
- Background workers (Celery) for QA and cleanup
- 3-layer cache (request, Redis, precomputed)
- REST API for resolution operations

**Tradeoffs**:
- **Pro**: Scalable - async processing handles peak load
- **Pro**: Testable - services are pure functions with clear boundaries
- **Pro**: HIPAA compliant - full audit trail via event sourcing
- **Pro**: Performance - caching reduces duplicate query load by 90%+
- **Pro**: Maintainable - each service has single responsibility
- **Con**: More complex - multiple services, message queue, cache layer
- **Con**: Eventual consistency - background jobs process duplicates asynchronously
- **Con**: Infrastructure overhead - requires Redis, Celery workers

**Best for**: Healthcare applications with strict audit requirements, high scale, and complex duplicate workflows

### Option B: Monolithic Service with Synchronous Processing

**Approach**:
- Keep existing 2 services (Detection + Handling)
- Add resolution methods directly to DuplicateHandlingService
- Synchronous duplicate processing (no background jobs)
- No caching layer

**Tradeoffs**:
- **Pro**: Simple - fewer moving parts
- **Pro**: Consistent - no eventual consistency issues
- **Pro**: No infrastructure - works with current setup
- **Con**: Slow - blocks API requests during duplicate detection
- **Con**: Not scalable - single service becomes bottleneck
- **Con**: Hard to test - monolithic service with mixed concerns
- **Con**: Performance - no caching, repeated queries

**Best for**: Small-scale applications with low duplicate volume (<100/day)

### Option C: CQRS with Event Sourcing

**Approach**:
- Separate read (queries) and write (commands) models
- Event sourcing for all duplicate operations
- Materialized views for duplicate groups
- Command handlers for resolution operations

**Tradeoffs**:
- **Pro**: Ultimate scalability - read/write models scale independently
- **Pro**: Complete audit trail - event store is source of truth
- **Pro**: Temporal queries - can replay events to any point in time
- **Con**: High complexity - CQRS requires significant architectural shift
- **Con**: Eventual consistency - read model lags behind write model
- **Con**: Over-engineering - duplicate handling doesn't need full CQRS

**Best for**: Large-scale systems with millions of duplicates, complex temporal queries

---

## Rationale

**Option A (Event-Driven Service Architecture) was chosen** because:

1. **Performance Requirements**: CredentialMate has high duplicate detection load:
   - Document extraction: 100+ credentials per document
   - Bulk coordinator creates: 50 credentials per batch
   - Current synchronous approach causes API timeouts
   - Caching + async processing solves this

2. **HIPAA Compliance**: Event-driven architecture provides:
   - Immutable event log (append-only audit trail)
   - Actor tracking (who triggered each duplicate operation)
   - Temporal queries (reconstruct state for compliance audits)
   - Aligns with existing `duplicate_events` table from ADR-002

3. **Existing Infrastructure**: CredentialMate already has:
   - Celery + Redis (from ADR-001 report generation)
   - Event-driven patterns (WebSocket notifications)
   - Background job patterns (report cleanup, nightly sync)
   - Minimal new infrastructure needed

4. **Healthcare Best Practices**: Matches patterns from Epic, Cerner:
   - Async duplicate processing (doesn't block clinical workflows)
   - Background QA jobs (data quality assurance)
   - Resolution APIs (coordinator tools for duplicate management)

5. **Scalability**: Supports future growth:
   - Multi-organization deployment (1000+ orgs)
   - Real-time duplicate notifications (WebSocket)
   - ML-based duplicate detection (future enhancement)

**Trade-off accepted**: Eventual consistency is acceptable - duplicates processed within 6 hours by background job. Critical duplicates (confidence > 0.95) can auto-resolve immediately.

---

## Implementation Notes

### Service Architecture

#### 1. Service Boundaries (4 Specialized Contexts)

```python
# apps/backend-api/src/contexts/duplicates/services/

class DuplicateDetectionService:
    """Pure read service - finds potential matches."""

    async def find_matches(
        self,
        credential_type: str,
        data: dict,
        organization_id: int,
        db: Session
    ) -> List[Match]:
        """Find potential duplicate matches (cacheable)."""
        # Uses indexes from ADR-002
        # Returns list of matching records with scores
        pass

    async def find_matches_cross_org(
        self,
        credential_type: str,
        data: dict,
        db: Session,
        actor: User  # Must be superuser
    ) -> List[Match]:
        """Find duplicates across organizations (superuser only)."""
        # Logs to cross_org_access_log (ADR-002)
        pass


class DuplicateClassificationService:
    """Business logic - classify match types and confidence."""

    def classify(
        self,
        new_record: Any,
        matches: List[Match]
    ) -> DuplicateClassification:
        """Classify duplicate type and confidence score."""
        # Perfect/partial/cross-source/renewal detection
        # Confidence scoring based on data source ranking
        pass

    def calculate_confidence(
        self,
        new_record: Any,
        existing_record: Any
    ) -> float:
        """Calculate confidence score (0.0 - 1.0)."""
        # Source ranking: verified_external=1.0 to legacy_import=0.4
        pass


class DuplicateResolutionService:
    """Mutation service - merge, archive, undo operations."""

    async def merge_duplicates(
        self,
        group_id: UUID,
        primary_record_id: int,
        reason: str,
        actor: User,
        db: Session
    ) -> ResolutionResult:
        """Merge duplicate group into primary record."""
        # Sets is_primary_record, exclude_from_calculations
        # Creates audit event
        pass

    async def keep_both(
        self,
        group_id: UUID,
        reason: str,
        actor: User,
        db: Session
    ) -> ResolutionResult:
        """Keep both records (cross-source validation)."""
        # Clears exclude_from_calculations on both
        # Updates duplicate_match_type = 'cross_source'
        pass

    async def undo_resolution(
        self,
        group_id: UUID,
        actor: User,
        db: Session
    ) -> ResolutionResult:
        """Undo previous resolution (audit trail maintained)."""
        # Reverts flags, creates undo event
        pass


class DuplicateAuditService:
    """Event tracking - create, query audit events."""

    async def create_event(
        self,
        event_type: DuplicateEventType,
        credential_type: str,
        new_record_id: int,
        existing_record_ids: List[int],
        actor: User,
        classification: DuplicateClassification,
        db: Session
    ) -> DuplicateEvent:
        """Create audit event in duplicate_events table."""
        pass

    async def query_events(
        self,
        filters: EventFilters,
        db: Session
    ) -> List[DuplicateEvent]:
        """Query audit events (for reporting)."""
        pass
```

#### 2. Facade Pattern for Coordination

```python
# apps/backend-api/src/contexts/duplicates/services/duplicate_orchestrator.py

class DuplicateOrchestrator:
    """Facade pattern - coordinates all duplicate operations."""

    def __init__(self):
        self.detection = DuplicateDetectionService()
        self.classification = DuplicateClassificationService()
        self.resolution = DuplicateResolutionService()
        self.audit = DuplicateAuditService()
        self.event_bus = DuplicateEventBus()

    async def detect_and_accept(
        self,
        credential_type: str,
        data: dict,
        data_source: DataSource,
        entry_method: EntryMethod,
        actor: User,
        db: Session
    ) -> CredentialCreateResponse:
        """Main workflow - detect duplicates, create record, emit events."""

        # 1. Find matches (with caching)
        matches = await self.detection.find_matches(
            credential_type, data, actor.organization_id, db
        )

        # 2. Create record (ALWAYS - graceful acceptance)
        record = await self._create_record(
            credential_type, data, data_source, entry_method, db
        )

        # 3. Classify if duplicates found
        duplicate_info = None
        if matches:
            classification = self.classification.classify(record, matches)

            # 4. Link duplicates
            await self._link_duplicates(record, matches, classification, db)

            # 5. Auto-resolve if high confidence
            if classification.confidence > 0.95:
                await self.resolution.auto_resolve(record, matches, classification, actor, db)

            duplicate_info = self._build_duplicate_info(matches, classification)

        # 6. Create audit event
        if matches:
            event = await self.audit.create_event(
                event_type=DuplicateEventType.DUPLICATE_DETECTED,
                credential_type=credential_type,
                new_record_id=record.id,
                existing_record_ids=[m.id for m in matches],
                actor=actor,
                classification=classification,
                db=db
            )

            # 7. Emit to event bus (async processing)
            await self.event_bus.emit(event)

        # 8. Return response
        return CredentialCreateResponse(
            id=record.id,
            status='created_duplicate' if matches else 'created',
            duplicate_detected=bool(matches),
            duplicate_info=duplicate_info
        )
```

### API Changes

#### New REST Endpoints

```python
# apps/backend-api/app/api/v1/duplicates/duplicate_endpoints.py

@router.get("/suggestions")
async def get_duplicate_suggestions(
    provider_id: int,
    credential_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DuplicateSuggestionsResponse:
    """Get duplicate resolution suggestions for review."""
    # Returns prioritized list of duplicate groups
    # High confidence first, then medium, then low
    pass


@router.post("/resolve")
async def resolve_duplicate(
    request: DuplicateResolutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResolutionResult:
    """Resolve duplicate group (merge, keep_both, archive)."""
    # Validates permissions (coordinator/admin only for partial duplicates)
    # Calls ResolutionService
    # Returns resolution result with audit event ID
    pass


@router.post("/{group_id}/undo")
async def undo_resolution(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResolutionResult:
    """Undo previous resolution (audit trail maintained)."""
    # Admin-only operation
    pass


@router.get("/events")
async def query_duplicate_events(
    filters: EventFilters = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[DuplicateEvent]:
    """Query duplicate audit events (for reporting)."""
    pass
```

#### Enhanced Error Responses

```python
# apps/backend-api/src/shared/exceptions/duplicate_exceptions.py

class DuplicateDetectedError(HTTPException):
    """Structured HTTP 409 with resolution options."""

    def __init__(
        self,
        duplicate_info: DuplicateInfo,
        resolution_options: List[ResolutionOption]
    ):
        super().__init__(
            status_code=409,
            detail={
                "error_code": "DUPLICATE_DETECTED",
                "message": "Record already exists",
                "duplicate_info": duplicate_info.model_dump(),
                "resolution_options": [opt.model_dump() for opt in resolution_options]
            }
        )


# Usage in endpoints:
if existing:
    raise DuplicateDetectedError(
        duplicate_info=DuplicateInfo(
            existing_ids=[existing.id],
            match_type="perfect",
            confidence=0.98
        ),
        resolution_options=[
            ResolutionOption(action="merge", requires_approval=False),
            ResolutionOption(action="keep_both", requires_approval=False)
        ]
    )
```

### Event-Driven Architecture

#### Event Bus Implementation

```python
# apps/backend-api/src/contexts/duplicates/events/event_bus.py

class DuplicateEventBus:
    """Pub/sub for duplicate events."""

    def __init__(self):
        self.redis = get_redis_client()
        self.websocket = get_websocket_manager()

    async def emit(self, event: DuplicateEvent):
        """Emit event to multiple channels."""

        # 1. Store in database (source of truth)
        # Already done by AuditService

        # 2. Emit to Redis queue for background processing
        if event.match_type in ['perfect', 'partial']:
            await self.redis.lpush(
                'queue:duplicate_review',
                event.model_dump_json()
            )

        # 3. Emit WebSocket for real-time UI updates
        if event.confidence > 0.90:
            await self.websocket.broadcast(
                channel=f'org:{event.organization_id}:duplicates',
                message={
                    'type': 'duplicate_detected',
                    'event': event.model_dump()
                }
            )

        # 4. Emit to metrics collector
        await self._record_metric(event)


# apps/worker-tasks/tasks/duplicates/duplicate_event_consumer.py

@celery.task
def process_duplicate_event(event_json: str):
    """Background consumer for duplicate events."""

    event = DuplicateEvent.model_validate_json(event_json)

    # High confidence - auto-resolve
    if event.confidence > 0.95:
        resolution_service.auto_resolve(
            group_id=event.duplicate_group_id,
            reason="High confidence match",
            actor=SystemUser()
        )

    # Medium confidence - flag for review
    elif event.confidence > 0.80:
        review_queue.add(
            group_id=event.duplicate_group_id,
            priority='medium',
            event_id=event.id
        )

    # Low confidence - log only
    else:
        logger.info(f"Low confidence duplicate detected: {event.id}")
```

#### Saga Pattern for Cross-Context Coordination

```python
# apps/backend-api/src/contexts/duplicates/sagas/duplicate_detection_saga.py

class DuplicateDetectionSaga:
    """Orchestrates duplicate detection across bounded contexts."""

    @subscribe_to(CredentialCreatedEvent)
    async def on_credential_created(self, event: CredentialCreatedEvent):
        """React to credential creation from any context."""

        # 1. Trigger duplicate detection
        orchestrator = DuplicateOrchestrator()
        result = await orchestrator.detect_and_accept(
            credential_type=event.credential_type,
            data=event.data,
            data_source=event.data_source,
            entry_method=event.entry_method,
            actor=event.actor,
            db=event.db
        )

        # 2. If duplicates found, emit event
        if result.duplicate_detected:
            await event_bus.emit(DuplicateDetectedEvent(
                credential_id=event.aggregate_id,
                duplicate_info=result.duplicate_info
            ))

        # 3. Update compliance calculations if needed
        if event.credential_type == 'cme_activity':
            await compliance_service.recalculate(
                provider_id=event.provider_id
            )
```

### Caching Strategy

#### 3-Layer Cache Implementation

```python
# apps/backend-api/src/contexts/duplicates/services/cached_duplicate_detection.py

class CachedDuplicateDetection:
    """Multi-layer cache for duplicate detection."""

    def __init__(self):
        self.redis = get_redis_client()
        self.detection_service = DuplicateDetectionService()

    # Layer 1: Request-scoped cache (same API call)
    @lru_cache(maxsize=100)
    def _find_matches_request_scope(
        self,
        credential_hash: str,  # Hash of credential data
        organization_id: int
    ):
        """In-memory cache for current request."""
        # Cleared after request completes
        pass

    # Layer 2: Redis cache (cross-request, 5 min TTL)
    async def find_matches_cached(
        self,
        credential_type: str,
        data: dict,
        organization_id: int,
        db: Session
    ) -> List[Match]:
        """Redis-cached duplicate detection."""

        # Generate cache key
        credential_hash = self._hash_credential_data(data)
        cache_key = f"dup:check:{credential_type}:{credential_hash}:{organization_id}"

        # Try Redis cache
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info(f"Cache HIT: {cache_key}")
            return [Match.model_validate(m) for m in json.loads(cached)]

        # Cache miss - query database
        logger.info(f"Cache MISS: {cache_key}")
        matches = await self.detection_service.find_matches(
            credential_type, data, organization_id, db
        )

        # Store in cache (5 min TTL)
        await self.redis.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps([m.model_dump() for m in matches])
        )

        return matches

    # Layer 3: Precomputed duplicate groups (hourly refresh)
    async def get_precomputed_groups(
        self,
        provider_id: int,
        organization_id: int
    ) -> List[DuplicateGroup]:
        """Get precomputed duplicate groups (refreshed by background job)."""

        cache_key = f"dup:groups:{organization_id}:{provider_id}"

        cached = await self.redis.get(cache_key)
        if cached:
            return [DuplicateGroup.model_validate(g) for g in json.loads(cached)]

        # Fallback to database
        return await self._query_duplicate_groups(provider_id, organization_id)

    # Cache invalidation
    async def invalidate_provider_cache(
        self,
        provider_id: int,
        organization_id: int
    ):
        """Invalidate all caches for a provider (on create/update/delete)."""

        pattern = f"dup:*:{organization_id}:*"
        keys = await self.redis.keys(pattern)

        if keys:
            await self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys for org {organization_id}")
```

### Background Jobs

#### Job 1: Duplicate QA Processor (Every 6 Hours)

```python
# apps/worker-tasks/tasks/duplicates/qa_processor.py

@celery.task
@celery_schedule(crontab(minute=0, hour='*/6'))  # Every 6 hours
def duplicate_qa_processor():
    """Background QA for duplicate consolidation."""

    logger.info("Starting Duplicate QA Processor")

    db = SessionLocal()
    orchestrator = DuplicateOrchestrator()

    try:
        # 1. Find new potential duplicates since last run
        last_run = get_last_run_timestamp('duplicate_qa')
        candidates = find_duplicate_candidates_since(last_run, db)

        logger.info(f"Found {len(candidates)} duplicate candidates")

        # 2. Classify and auto-resolve high-confidence
        for candidate in candidates:
            classification = orchestrator.classification.classify(
                candidate.new_record,
                candidate.matches
            )

            # Auto-resolve if confidence > 95%
            if classification.confidence > 0.95:
                logger.info(f"Auto-resolving duplicate group {candidate.group_id}")
                orchestrator.resolution.auto_resolve(
                    candidate.new_record,
                    candidate.matches,
                    classification,
                    actor=SystemUser(),
                    db=db
                )
            else:
                # Flag for human review
                logger.info(f"Flagging duplicate group {candidate.group_id} for review")
                add_to_review_queue(candidate, classification, db)

        # 3. Generate daily report (if midnight run)
        if datetime.now().hour == 0:
            generate_duplicate_report(db)

        # 4. Update last run timestamp
        set_last_run_timestamp('duplicate_qa', datetime.now())

        logger.info("Duplicate QA Processor completed successfully")

    except Exception as e:
        logger.error(f"Duplicate QA Processor failed: {e}")
        raise
    finally:
        db.close()
```

#### Job 2: Duplicate Cleanup (Daily at 2 AM)

```python
# apps/worker-tasks/tasks/duplicates/cleanup_job.py

@celery.task
@celery_schedule(crontab(minute=0, hour=2))  # Daily at 2 AM
def duplicate_cleanup_job():
    """Delete old perfect duplicates based on retention policy."""

    logger.info("Starting Duplicate Cleanup Job")

    db = SessionLocal()

    try:
        # Retention policy from ADR-007:
        # - Perfect (same source): 2 years
        # - Perfect (cross-source): 10 years
        # - Partial: 10 years
        # - Cross-org: 10 years

        # Delete perfect duplicates (same source) older than 2 years
        cutoff_2y = datetime.now() - timedelta(days=730)

        deleted = db.query(License).filter(
            License.auto_hidden == True,
            License.duplicate_match_type == 'perfect',
            License.deleted_at < cutoff_2y,
            # Only delete if same source as primary
            License.data_source == (
                db.query(License.data_source)
                .filter(License.duplicate_group_id == License.duplicate_group_id)
                .filter(License.is_primary_record == True)
                .scalar_subquery()
            )
        ).delete(synchronize_session=False)

        logger.info(f"Deleted {deleted} old perfect duplicate licenses")

        # Repeat for DEA, CSR, CME activities
        # ... (similar queries)

        db.commit()

        logger.info("Duplicate Cleanup Job completed successfully")

    except Exception as e:
        logger.error(f"Duplicate Cleanup Job failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()
```

### UI Changes

No UI changes in this ADR. See ADR-004 for duplicate resolution UI.

**Frontend will call new API endpoints:**
- `GET /api/v1/duplicates/suggestions` - Fetch duplicate review queue
- `POST /api/v1/duplicates/resolve` - Resolve duplicate group

### Estimated Scope

- **New service files to create**: 6
  - `duplicate_orchestrator.py` (facade)
  - `duplicate_detection_service.py` (refactor existing)
  - `duplicate_classification_service.py` (new)
  - `duplicate_resolution_service.py` (new)
  - `duplicate_audit_service.py` (new)
  - `cached_duplicate_detection.py` (caching wrapper)

- **New API files to create**: 2
  - `app/api/v1/duplicates/duplicate_endpoints.py`
  - `app/api/v1/duplicates/schemas.py`

- **New worker files to create**: 4
  - `tasks/duplicates/qa_processor.py`
  - `tasks/duplicates/cleanup_job.py`
  - `tasks/duplicates/event_consumer.py`
  - `tasks/duplicates/duplicate_detection_saga.py`

- **New event files to create**: 2
  - `contexts/duplicates/events/event_bus.py`
  - `contexts/duplicates/events/domain_events.py`

- **Files to modify**: 3
  - `contexts/provider/services/duplicate_handling_service.py` (use orchestrator)
  - `app/main.py` (register duplicate router)
  - `worker-tasks/celery_app.py` (register new tasks)

- **Tests to create**: 12
  - Service unit tests (4)
  - API integration tests (3)
  - Background job tests (2)
  - Event bus tests (2)
  - Saga pattern test (1)

- **Complexity**: High
  - Reason: Event-driven architecture, caching layer, background jobs, saga pattern, API endpoints, HIPAA compliance

- **Dependencies**:
  - **Existing**: Celery, Redis, WebSocket manager (from ADR-001)
  - **New**: None (uses existing infrastructure)

---

## Consequences

### Enables

- **90%+ cache hit rate** for duplicate detection (reduces DB load)
- **Async duplicate processing** (doesn't block API requests during bulk creates)
- **Coordinator tools** for duplicate management (merge, resolution APIs)
- **Automated cleanup** of old duplicates (prevents storage accumulation)
- **Real-time notifications** via WebSocket (coordinators see duplicates immediately)
- **Audit compliance** with event sourcing pattern (full traceability)
- **Scalability** to 1000+ organizations (event-driven architecture)
- **Background QA** every 6 hours (maintains data quality)
- **Undo functionality** for resolution operations (safety net)

### Constrains

- **Eventual consistency**: Duplicates processed within 6 hours (not immediate)
- **Cache invalidation complexity**: Must invalidate on create/update/delete
- **Worker dependency**: Background jobs require Celery workers running
- **Testing complexity**: Must test event bus, saga, async workflows
- **Error handling**: Must handle Redis failures gracefully (fallback to DB)
- **Monitoring required**: Must track background job success/failure rates
- **L1 autonomy impact**: Service refactoring requires careful testing (HIPAA constraints)

---

## Related ADRs

- **ADR-001**: Provider Report Generation (Celery/Redis infrastructure)
- **ADR-002**: Duplicate Handling Data Architecture (indexes, schemas, retention policy)
- **ADR-004**: Duplicate Handling User Experience (will consume these APIs)
- **plan-duplicate-handling-strategy.md**: Graceful acceptance philosophy, service interface design
- **plan-duplicate-handling-investigation.md**: Backend gap analysis, missing validation

**Future ADRs may cover**:
- ADR-005: Real-Time Duplicate Notifications via WebSocket (detailed WebSocket architecture)
- ADR-006: ML-Based Duplicate Detection (confidence scoring enhancements)

---

<!--
SYSTEM SECTION - DO NOT EDIT
-->

```yaml
_system:
  created_by: "app-advisor"
  created_at: "2026-01-10T00:00:00Z"
  approved_at: null
  approved_by: null
  confidence: 89
  auto_decided: false
  escalation_reason: "Strategic domain (api_design, external_integrations, event-driven architecture)"
```
