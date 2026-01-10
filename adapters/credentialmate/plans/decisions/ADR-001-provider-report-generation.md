# ADR-001: Provider Dashboard At-Risk/Urgent Report Generation

**Date**: 2026-01-09
**Status**: approved
**Advisor**: app-advisor
**Deciders**: tmac (approved 2026-01-10)

---

## Tags

```yaml
tags: [report-generation, hipaa-compliance, api-design, async-processing, pdf-generation]
applies_to:
  - "apps/backend-api/app/api/v1/reports/**"
  - "apps/worker-tasks/tasks/reports/**"
  - "apps/frontend-web/src/components/reports/**"
domains: [backend, frontend, security, compliance]
```

---

## Context

CredentialMate providers need a downloadable report summarizing credentials that are "at risk" (expiring soon) and "urgent" (expired or critical). This report:

- Helps providers prioritize credential remediation work
- Serves as audit documentation for compliance reviews
- Provides executive summary for management
- Must comply with HIPAA requirements (audit logging, encryption, access controls)

**Current gap**: Providers manually review the dashboard and take screenshots, which is error-prone and lacks audit trails.

---

## Decision

**Implement backend-generated async report system** with the following architecture:

1. **Backend (FastAPI)**: Async job queue for report generation
2. **Worker (Celery)**: Background processing with Redis queue
3. **Storage (S3)**: Time-limited signed URLs for downloads (5 min expiry)
4. **Formats**: PDF (primary), CSV (secondary), Excel (optional phase 2)
5. **HIPAA Controls**: Full audit logging, encryption at rest/transit, auto-deletion after 24 hours

---

## Options Considered

### Option A: Backend-Generated Reports (Async)

**Approach**:
- API endpoint creates async job → Celery worker generates report → Stores in S3 → Returns signed URL
- Frontend polls for completion status
- Reports auto-delete after 24 hours

**Tradeoffs**:
- **Pro**: Full HIPAA compliance with audit trails, consistent formatting, handles large datasets
- **Pro**: Server-side PHI protection (no PHI in browser memory)
- **Pro**: Can enforce access controls and retention policies
- **Con**: More infrastructure (Celery, Redis, S3)
- **Con**: Slightly slower UX (async processing vs instant)

**Best for**: HIPAA-compliant apps with sensitive data and regulatory requirements

### Option B: Client-Side Report Generation

**Approach**:
- Fetch data via API → Generate PDF/CSV in browser using JavaScript libraries
- No server-side processing needed

**Tradeoffs**:
- **Pro**: Simpler architecture (no workers needed)
- **Pro**: Instant generation for small datasets
- **Con**: PHI exposed in browser memory (HIPAA risk)
- **Con**: Inconsistent formatting across browsers
- **Con**: Cannot handle large datasets (>1000 records)
- **Con**: Difficult to audit who generated what report

**Best for**: Non-regulated applications with small datasets

### Option C: Synchronous Backend Generation

**Approach**:
- Blocking API endpoint generates report immediately
- Waits for completion before returning

**Tradeoffs**:
- **Pro**: Simpler than async (no workers)
- **Pro**: HIPAA-compliant (server-side)
- **Con**: Timeouts for large reports (FastAPI 60s default)
- **Con**: Blocks API resources during generation
- **Con**: Poor UX (user waits with no progress indicator)

**Best for**: Small reports (<500 records) with no performance concerns

---

## Rationale

**Option A (Backend Async) was chosen** because:

1. **HIPAA Compliance**: CredentialMate is L1 autonomy with strict HIPAA requirements. Server-side generation ensures:
   - PHI never enters browser memory
   - Complete audit trails (who generated, when, what data)
   - Encryption at rest (S3 + KMS) and in transit (HTTPS)
   - Controlled data retention (auto-delete after 24 hours)

2. **Scalability**: Providers may have 1000+ credentials. Async processing:
   - Prevents API timeouts
   - Provides progress feedback to users
   - Handles peak load without blocking

3. **Consistency**: Server-side templates ensure:
   - Uniform formatting across all reports
   - Watermarks and compliance headers
   - Controlled branding and data presentation

4. **Future-Proofing**: Architecture supports:
   - Scheduled reports (nightly email)
   - Historical report archives
   - Bulk report generation for multi-provider orgs

**Trade-off accepted**: Additional infrastructure complexity (Celery/Redis) is justified by regulatory requirements and scale needs.

---

## Implementation Notes

### Schema Changes

**New tables**:

```sql
-- Report generation jobs
CREATE TABLE report_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    provider_id UUID REFERENCES providers(id),
    report_type VARCHAR(50) NOT NULL,  -- 'at_risk_urgent'
    format VARCHAR(10) NOT NULL,       -- 'pdf', 'csv', 'excel'
    status VARCHAR(20) NOT NULL,       -- 'queued', 'processing', 'completed', 'failed'
    filters JSONB,                     -- Serialized filter criteria
    s3_key VARCHAR(500),               -- S3 object key (when completed)
    error_message TEXT,                -- Error details (if failed)
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP,              -- When S3 object auto-deletes
    record_count INTEGER,              -- Number of records in report
    file_size_bytes BIGINT
);

CREATE INDEX idx_report_jobs_user ON report_jobs(user_id);
CREATE INDEX idx_report_jobs_status ON report_jobs(status);

-- Audit log for PHI access
CREATE TABLE report_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES report_jobs(id),
    user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,       -- 'generated', 'downloaded', 'expired'
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_report_access_logs_user ON report_access_logs(user_id);
CREATE INDEX idx_report_access_logs_timestamp ON report_access_logs(timestamp);
```

**Migration file**: `alembic/versions/001_add_report_generation_tables.py`

### API Changes

**New endpoints** (apps/backend-api/app/api/v1/reports/):

```python
# 1. Initiate report generation
POST /api/v1/reports/at-risk
Request:
{
  "filters": {
    "urgency_levels": ["urgent", "at_risk"],
    "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
    "provider_ids": [uuid, ...]  # Optional
  },
  "format": "pdf" | "csv" | "excel",
  "include_sections": ["summary", "details", "recommendations"]
}
Response: 201 Created
{
  "job_id": "uuid",
  "status": "queued",
  "estimated_time_seconds": 30
}

# 2. Check job status
GET /api/v1/reports/jobs/{job_id}
Response: 200 OK
{
  "job_id": "uuid",
  "status": "completed",
  "progress_percentage": 100,
  "download_url": "https://s3-presigned-url...",
  "expires_at": "2024-01-15T12:05:00Z",
  "record_count": 247,
  "created_at": "2024-01-15T12:00:00Z"
}

# 3. List user's recent reports
GET /api/v1/reports/jobs?status=completed&limit=10
Response: 200 OK
{
  "jobs": [...],
  "total": 5,
  "page": 1
}
```

**Authentication**: Requires Bearer token, provider role
**Rate limiting**: 10 reports per hour per user

### UI Changes

**New components** (apps/frontend-web/src/components/reports/):

1. `ReportDownloader.tsx` - Main UI component
   - Format selector (PDF/CSV)
   - Date range picker
   - Urgency level checkboxes
   - "Generate Report" button
   - Progress indicator during generation

2. `ReportStatusPoller.tsx` - Polls job status
   - Shows progress percentage
   - Auto-downloads when complete
   - Error handling and retry logic

3. `ReportHistoryTable.tsx` - Shows recent reports
   - Re-download link (if not expired)
   - Expiration countdown
   - Status badges

**Integration point**: Provider Dashboard → New "Reports" tab

### Estimated Scope

- **Files to create**: ~15
  - Backend API: 4 files (routes, schemas, services, dependencies)
  - Worker tasks: 3 files (report generator, PDF builder, S3 uploader)
  - Frontend: 3 components
  - Tests: 5 files (API tests, worker tests, integration tests)

- **Files to modify**: ~5
  - Add route to main API router
  - Update frontend dashboard layout
  - Add migration to alembic
  - Update requirements.txt (ReportLab, celery)
  - Update frontend package.json (polling utils)

- **Complexity**: High
  - Reason: New infrastructure (Celery workers), HIPAA compliance requirements, async processing patterns

- **Dependencies**:
  - **Backend**: reportlab (PDF), openpyxl (Excel), celery, redis
  - **Frontend**: react-query (polling), date-fns (date handling)
  - **Infrastructure**: Redis instance, S3 bucket with lifecycle policy, Celery worker process

---

## Consequences

### Enables

- **Audit compliance**: Full trail of who generated reports with what data
- **Executive reporting**: Providers can share PDFs with management
- **Data analysis**: CSV exports enable trend analysis in Excel
- **Scalability**: Handles large datasets (10k+ credentials) without timeouts
- **Future features**: Foundation for scheduled reports, email delivery, custom report types

### Constrains

- **Infrastructure costs**: Requires Redis, S3 storage, worker processes (~$50/month)
- **Deployment complexity**: Must deploy Celery workers alongside API
- **Storage limits**: Reports auto-delete after 24 hours (no permanent archives without user action)
- **L1 autonomy impact**: Report generation logic must pass strict HIPAA guardrails (max 50 lines added per change)

---

## Related ADRs

- None (first ADR for CredentialMate in this system)

**Future ADRs may cover**:
- ADR-002: Scheduled report delivery via email
- ADR-003: Custom report templates for different provider types
- ADR-004: Report data retention policy extension

---

<!--
SYSTEM SECTION - DO NOT EDIT
-->

```yaml
_system:
  created_by: "app-advisor"
  created_at: "2026-01-09T00:00:00Z"
  approved_at: "2026-01-10T00:00:00Z"
  approved_by: "tmac"
  confidence: 88
  auto_decided: false
  escalation_reason: "Strategic domain (API design, HIPAA compliance, new infrastructure)"
```
