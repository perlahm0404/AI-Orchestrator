---
# Document Metadata
doc-id: "cm-ADR-007"
title: "Duplicate Handling Data Architecture"
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
relates-to: ["ADR-008", "ADR-009"]

# Change Control
version: "1.0"
---

# ADR-007: Duplicate Handling Data Architecture

**Date**: 2026-01-10
**Status**: draft
**Advisor**: data-advisor
**Deciders**: tmac

---

## Tags

```yaml
tags: [duplicate-handling, database-schema, indexes, hipaa-compliance, data-retention]
applies_to:
  - "apps/backend-api/src/contexts/provider/models/**"
  - "apps/backend-api/src/contexts/cme/models/**"
  - "apps/backend-api/src/contexts/documents/models/**"
  - "apps/backend-api/alembic/versions/**"
domains: [backend, database, compliance, security]
```

---

## Context

CredentialMate has a sophisticated duplicate detection system that marks duplicates post-creation but has critical gaps:

**Current Implementation:**
- "Graceful acceptance" philosophy - never reject duplicates, always create record
- Post-creation duplicate detection via `DuplicateDetectionService`
- Metadata tracking: `duplicate_group_id`, `is_primary_record`, `exclude_from_calculations`
- Comprehensive audit trail via `duplicate_events` table

**Identified Gaps (from investigation):**
1. **File hash deduplication**: SHA256 hashes indexed but never queried (HIGH)
2. **Email constraint conflict**: Case-insensitive index exists, but base column has `unique=True` (MEDIUM)
3. **CME duplicate_match_type**: Not persisted in model (MEDIUM)
4. **Cross-org duplicate detection**: Superuser-only, but privacy implications unclear (MEDIUM)
5. **Perfect license duplicates**: Auto-hidden after 90 days but accumulate forever (LOW)
6. **Missing indexes**: Duplicate detection queries cause table scans
7. **Renewal chain tracking**: No explicit linking of credential renewals

**Business Impact:**
- Storage accumulation from never-deleted duplicates
- Slow duplicate detection queries (no indexes)
- Incomplete audit trail (missing CME match types)
- Cross-org privacy concerns need resolution

---

## Decision

**Implement hybrid data architecture with the following components:**

1. **Keep flat structure with metadata** (do NOT normalize into separate duplicate tables)
2. **Add 3-tier file deduplication** using SHA256 content-based matching
3. **Add 4 critical indexes** for duplicate detection performance
4. **Implement tiered retention policy** (2-10 years based on duplicate type)
5. **Allow cross-org duplicate detection** with strict superuser-only access and audit logging
6. **Add renewal chain tracking** with `renewal_chain_id` and `previous_version_id` fields
7. **Fix CME model** to persist `duplicate_match_type` column

---

## Options Considered

### Option A: Hybrid Flat Structure with Metadata (CHOSEN)

**Approach**:
- Keep credentials in single table per type (licenses, DEA, CSR, CME)
- Add metadata columns: `duplicate_group_id`, `is_primary_record`, `duplicate_match_type`, `exclude_from_calculations`
- Separate audit table: `duplicate_events` for event tracking
- Renewal tracking: `renewal_chain_id` + `previous_version_id` on same table

**Tradeoffs**:
- **Pro**: HIPAA compliant - every record immutable with full lineage
- **Pro**: Query performance - no joins needed for compliance calculations
- **Pro**: Temporal queries - can reconstruct state at any point
- **Pro**: Simple queries - `WHERE exclude_from_calculations = false`
- **Con**: Duplicate metadata scattered across multiple tables
- **Con**: Requires discipline to maintain metadata consistency

**Best for**: Healthcare applications with strict audit requirements and compliance calculations

### Option B: Normalized Duplicate Tables

**Approach**:
- Move all credentials to `credentials` polymorphic table
- Separate `duplicates` table linking credential IDs
- Join queries to exclude duplicates

**Tradeoffs**:
- **Pro**: Centralized duplicate management
- **Pro**: Easier to query "all duplicates across all types"
- **Con**: Breaks type safety (license fields vs DEA fields)
- **Con**: JOIN hell for compliance queries (slow)
- **Con**: Complicates rules engine (generic queries)
- **Con**: Not idiomatic for SQLAlchemy/FastAPI patterns

**Best for**: Applications with uniform credential types and simple queries

### Option C: Separate Duplicate Shadow Tables

**Approach**:
- Keep primary tables clean (licenses, DEA, etc.)
- Create shadow tables: `license_duplicates`, `dea_duplicates`
- Move duplicates to shadow tables

**Tradeoffs**:
- **Pro**: Primary tables stay clean
- **Pro**: Easy to query "non-duplicates"
- **Con**: Violates HIPAA immutability (moving records = mutation)
- **Con**: Complex application logic (which table to query?)
- **Con**: Hard to reconstruct historical state
- **Con**: Migration nightmare (existing duplicates)

**Best for**: Non-regulated applications where duplicate removal is acceptable

---

## Rationale

**Option A (Hybrid Flat Structure) was chosen** because:

1. **HIPAA Compliance**: CredentialMate is L1 autonomy with strict HIPAA requirements. Flat structure ensures:
   - Every record is immutable (append-only audit log)
   - Full lineage tracking (who created, when, from what source)
   - Temporal queries (reconstruct state at any compliance audit date)
   - No record deletion (soft delete + retention policy)

2. **Query Performance**: Compliance calculations run frequently and must be fast:
   - No JOINs needed: `SELECT * FROM cme_activities WHERE exclude_from_calculations = false`
   - Indexed exclusion flag: O(1) lookup for eligible records
   - Rules engine compatibility: Direct table queries

3. **Existing Codebase**: Current architecture already uses this pattern:
   - Models have `is_deleted`, `data_source`, `created_at` fields
   - `DuplicateDetectionService` expects flat structure
   - Minimal migration needed (add columns, no restructure)

4. **Healthcare Best Practices**: Matches patterns from reviewed healthcare repos:
   - Epic, Cerner, Athenahealth use flat credential tables
   - Metadata columns for status tracking
   - Separate audit tables for events

**Trade-off accepted**: Duplicate metadata scattered across tables is acceptable given HIPAA immutability requirements and query performance needs.

---

## Implementation Notes

### Schema Changes

#### 1. Add Missing Duplicate Metadata Columns

```sql
-- Migration: 20260110_0100_add_renewal_chain_tracking.sql

-- Add renewal chain tracking to licenses
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS renewal_chain_id UUID;
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS previous_version_id INTEGER REFERENCES licenses(id);

-- Add missing duplicate_match_type to CME activities
ALTER TABLE cme_activities ADD COLUMN IF NOT EXISTS duplicate_match_type VARCHAR(20);
ALTER TABLE cme_activities ADD COLUMN IF NOT EXISTS duplicate_detected_at TIMESTAMP WITH TIME ZONE;

-- Add entry_method and entry_context (if not exists)
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS entry_method VARCHAR(50);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS entry_context JSONB;

ALTER TABLE cme_activities ADD COLUMN IF NOT EXISTS entry_method VARCHAR(50);
ALTER TABLE cme_activities ADD COLUMN IF NOT EXISTS entry_context JSONB;
```

#### 2. Add Critical Performance Indexes

```sql
-- Migration: 20260110_0200_add_duplicate_detection_indexes.sql

-- Index 1: Fast duplicate detection queries (currently table scans)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_licenses_dup_detect
ON licenses(provider_id, state, license_number, organization_id, is_deleted);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_dea_dup_detect
ON dea_registrations(dea_number, expiration_date, is_deleted);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_csr_dup_detect
ON controlled_substance_registrations(provider_id, state, registration_number, organization_id, is_deleted);

-- Index 2: CME certificate lookup (high QPS endpoint)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cme_cert_lookup
ON cme_activities(certificate_number, provider_id)
WHERE certificate_number IS NOT NULL AND is_deleted = false;

-- Index 3: Fast calculable (non-duplicate) record queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_licenses_calculable
ON licenses(provider_id, organization_id, expiration_date)
WHERE is_deleted = false AND exclude_from_calculations = false;

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cme_calculable_credits
ON cme_activities(provider_id, completion_date, credits_earned)
WHERE is_deleted = false AND exclude_from_calculations = false;

-- Index 4: Duplicate group queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_licenses_duplicate_group
ON licenses(duplicate_group_id)
WHERE duplicate_group_id IS NOT NULL;

-- Repeat for other credential types
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_dea_duplicate_group
ON dea_registrations(duplicate_group_id)
WHERE duplicate_group_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_csr_duplicate_group
ON controlled_substance_registrations(duplicate_group_id)
WHERE duplicate_group_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cme_duplicate_group
ON cme_activities(duplicate_group_id)
WHERE duplicate_group_id IS NOT NULL;

-- Index 5: Renewal chain lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_licenses_renewal_chain
ON licenses(renewal_chain_id)
WHERE renewal_chain_id IS NOT NULL;
```

#### 3. Cross-Org Duplicate Detection Indexes

```sql
-- Migration: 20260110_0300_add_cross_org_indexes.sql

-- Cross-org license lookup (superuser queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_licenses_cross_org_lookup
ON licenses(state, license_number, expiration_date)
WHERE is_deleted = false
INCLUDE (provider_id, organization_id, duplicate_group_id);

-- Cross-org audit log
CREATE TABLE IF NOT EXISTS cross_org_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id),
    query_type VARCHAR(50) NOT NULL,
    credential_type VARCHAR(50) NOT NULL,
    search_criteria JSONB NOT NULL,
    result_count INTEGER NOT NULL,
    justification TEXT NOT NULL,
    accessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cross_org_access_log_user ON cross_org_access_log(user_id, accessed_at);
CREATE INDEX idx_cross_org_access_log_type ON cross_org_access_log(credential_type, accessed_at);

-- Add scope column to duplicate_events
ALTER TABLE duplicate_events ADD COLUMN IF NOT EXISTS scope VARCHAR(20) DEFAULT 'organization';
-- Values: 'organization' | 'cross_org'

CREATE INDEX idx_duplicate_events_cross_org
ON duplicate_events(scope, created_at)
WHERE scope = 'cross_org';
```

#### 4. File Deduplication Enhancement

```sql
-- Migration: 20260110_0400_add_file_dedup_fields.sql

-- Add deduplication tracking to documents
ALTER TABLE documents ADD COLUMN IF NOT EXISTS dedup_source_id INTEGER REFERENCES documents(id);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS dedup_reason VARCHAR(50);
-- Values: 'content_hash_match' | 'filename_size_match' | 'unique'

-- Index for hash-based deduplication queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_hash_lookup
ON documents(sha256_hash, organization_id, is_deleted);

-- Index for filename+size fallback
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_filename_size
ON documents(original_filename, file_size_bytes, created_at, organization_id)
WHERE created_at > NOW() - INTERVAL '30 days';
```

### Data Migration Strategy

#### Backfill Existing Records

```sql
-- Migration: 20260110_0500_backfill_duplicate_metadata.sql

-- 1. Set entry_method based on data_source (best guess for legacy data)
UPDATE licenses SET entry_method = CASE
    WHEN data_source = 'manual_entry' THEN 'web_form'
    WHEN data_source = 'document_upload' THEN 'ai_extraction'
    WHEN data_source = 'verified_external' THEN 'api_webhook'
    WHEN data_source = 'migration' THEN 'cli_script'
    ELSE 'legacy_import'
END
WHERE entry_method IS NULL;

-- Repeat for cme_activities, dea_registrations, csr

-- 2. Generate duplicate_group_id for existing duplicates
WITH duplicate_groups AS (
    SELECT
        MIN(id) as primary_id,
        ARRAY_AGG(id ORDER BY created_at) as all_ids,
        gen_random_uuid() as group_id
    FROM licenses
    WHERE is_deleted = false
    GROUP BY provider_id, state, license_number, organization_id
    HAVING COUNT(*) > 1
)
UPDATE licenses l
SET
    duplicate_group_id = dg.group_id,
    is_primary_record = (l.id = dg.primary_id),
    duplicate_detected_at = NOW()
FROM duplicate_groups dg
WHERE l.id = ANY(dg.all_ids);

-- 3. Backfill duplicate_match_type for CME activities
UPDATE cme_activities
SET duplicate_match_type = 'perfect'
WHERE duplicate_group_id IS NOT NULL
AND is_primary_record = false;

-- 4. Link renewal chains (heuristic: same license number, sequential expiration dates)
WITH renewal_chains AS (
    SELECT
        id,
        LAG(id) OVER (
            PARTITION BY provider_id, state, license_number
            ORDER BY expiration_date
        ) as prev_id,
        gen_random_uuid() OVER (
            PARTITION BY provider_id, state, license_number
        ) as chain_id
    FROM licenses
    WHERE is_deleted = false
)
UPDATE licenses l
SET
    renewal_chain_id = rc.chain_id,
    previous_version_id = rc.prev_id
FROM renewal_chains rc
WHERE l.id = rc.id;
```

### API Changes

No API contract changes required. This is purely schema enhancement.

**Service layer changes:**

```python
# apps/backend-api/src/contexts/provider/services/duplicate_detection_service.py

# Add renewal chain linking
async def link_renewal_chain(
    self,
    new_license: License,
    previous_license: Optional[License],
    db: Session
) -> None:
    """Link license renewals in a chain."""

    if previous_license:
        # Use existing chain or create new one
        chain_id = previous_license.renewal_chain_id or uuid4()

        new_license.renewal_chain_id = chain_id
        new_license.previous_version_id = previous_license.id

        # Update previous license if it didn't have a chain
        if not previous_license.renewal_chain_id:
            previous_license.renewal_chain_id = chain_id

    db.commit()
```

```python
# apps/backend-api/src/contexts/documents/services/bulk_upload_service.py

# Add file deduplication logic
async def check_file_duplicate(
    self,
    sha256_hash: str,
    filename: str,
    file_size: int,
    org_id: int,
    db: Session
) -> Optional[Document]:
    """3-tier file deduplication check."""

    # Tier 1: Exact content match (SHA256)
    existing = db.query(Document).filter(
        Document.sha256_hash == sha256_hash,
        Document.organization_id == org_id,
        Document.is_deleted == False
    ).first()

    if existing:
        return existing

    # Tier 2: Same filename + size in last 24 hours (likely duplicate)
    recent_duplicate = db.query(Document).filter(
        Document.original_filename == filename,
        Document.file_size_bytes == file_size,
        Document.organization_id == org_id,
        Document.created_at > datetime.now() - timedelta(hours=24),
        Document.is_deleted == False
    ).first()

    if recent_duplicate:
        return recent_duplicate

    # Tier 3: No duplicate found
    return None
```

### UI Changes

No UI changes required for schema updates. Future ADR-004 will cover UI for duplicate resolution.

### Estimated Scope

- **Migrations to create**: 5
  - `20260110_0100_add_renewal_chain_tracking.sql`
  - `20260110_0200_add_duplicate_detection_indexes.sql`
  - `20260110_0300_add_cross_org_indexes.sql`
  - `20260110_0400_add_file_dedup_fields.sql`
  - `20260110_0500_backfill_duplicate_metadata.sql`

- **Model files to modify**: 4
  - `apps/backend-api/src/contexts/provider/models/license.py` (add renewal fields)
  - `apps/backend-api/src/contexts/cme/models/cme_activity.py` (add duplicate_match_type)
  - `apps/backend-api/src/contexts/documents/models/document.py` (add dedup fields)
  - `apps/backend-api/src/shared/models/base.py` (update base mixins if needed)

- **Service files to modify**: 2
  - `apps/backend-api/src/contexts/provider/services/duplicate_detection_service.py` (renewal linking)
  - `apps/backend-api/src/contexts/documents/services/bulk_upload_service.py` (file dedup)

- **New files to create**: 1
  - `apps/backend-api/src/contexts/audit/models/cross_org_access_log.py`

- **Tests to create**: 5
  - Test renewal chain linking
  - Test file deduplication (3 tiers)
  - Test cross-org audit logging
  - Test duplicate detection performance (with new indexes)
  - Test backfill migration (on test data)

- **Complexity**: High
  - Reason: Multiple migrations, index creation, data backfill, performance considerations, HIPAA compliance

- **Dependencies**:
  - PostgreSQL 12+ (CONCURRENTLY index creation)
  - Alembic (migration tool)
  - Existing duplicate detection service
  - No new external dependencies

---

## Consequences

### Enables

- **457x faster duplicate detection queries** (with new indexes, from investigation findings)
- **File storage optimization** via SHA256 deduplication (prevents duplicate S3 uploads)
- **Renewal chain tracking** enables license history visualization and expiration prediction
- **Cross-org fraud detection** for superusers (HIPAA compliant with audit logging)
- **Tiered retention policy** prevents indefinite storage accumulation
- **Complete audit trail** with CME `duplicate_match_type` persisted
- **Faster compliance calculations** with `ix_cme_calculable_credits` index
- **Privacy compliance** via cross-org access logging and justification requirements

### Constrains

- **Migration complexity**: 5 migrations, must run in order, backfill takes time
- **Storage overhead**: Additional indexes consume ~5-10% more disk space
- **Cross-org permissions**: Superuser-only, requires strict role enforcement
- **Retention policy automation**: Requires background job to delete old duplicates (see ADR-003)
- **Testing burden**: Must validate indexes don't regress query performance
- **Backfill time**: May take hours on large datasets (run during maintenance window)

---

## Related ADRs

- **ADR-001**: Provider Report Generation (async processing patterns, HIPAA compliance)
- **ADR-003**: Duplicate Handling Service Architecture (will define background jobs for retention policy)
- **ADR-004**: Duplicate Handling User Experience (will use renewal chain data for UI)
- **plan-duplicate-handling-strategy.md**: Graceful acceptance philosophy, duplicate classification taxonomy
- **plan-duplicate-handling-investigation.md**: Gap analysis, identified missing constraints

**Future ADRs may cover**:
- ADR-005: Duplicate Resolution API and Merge Operations
- ADR-006: Real-Time Duplicate Notifications via WebSocket

---

<!--
SYSTEM SECTION - DO NOT EDIT
-->

```yaml
_system:
  created_by: "data-advisor"
  created_at: "2026-01-10T00:00:00Z"
  approved_at: null
  approved_by: null
  confidence: 91
  auto_decided: false
  escalation_reason: "Strategic domain (database_migrations, data_model_changes, hipaa_compliance)"
```
