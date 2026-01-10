# Implementation Plan: Provider Dashboard Report Generation (ADR-001)

**Feature**: Downloadable At-Risk/Urgent Credential Reports
**ADR**: [ADR-001](./decisions/ADR-001-provider-report-generation.md)
**Work Queue**: [work_queue_adr001.json](./tasks/work_queue_adr001.json)
**Target Project**: CredentialMate (L1 autonomy, HIPAA-compliant)

---

## Executive Summary

Enable providers to download PDF/CSV reports summarizing credentials that are "at risk" (expiring soon) or "urgent" (expired/critical). Reports are generated asynchronously by Celery workers, stored in encrypted S3 buckets with auto-deletion after 24 hours, and comply with HIPAA audit logging requirements.

**Estimated Scope**: 15 tasks across 4 phases
**Complexity**: High (new infrastructure, async processing, HIPAA compliance)
**Estimated Timeline**: Deploy-ready after all tasks complete

---

## Architecture Overview

```
┌─────────────┐
│  Provider   │
│  Dashboard  │
│  (Next.js)  │
└──────┬──────┘
       │ POST /api/v1/reports/at-risk
       ▼
┌──────────────┐
│  FastAPI     │◄─── Poll GET /api/v1/reports/jobs/{id}
│  Backend     │
└──────┬───────┘
       │ Enqueue Celery task
       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Redis      │◄────►│   Celery     │─────►│  S3 Bucket   │
│   Queue      │      │   Worker     │      │  (KMS enc.)  │
└──────────────┘      └──────────────┘      └──────┬───────┘
                                                    │
                                                    ▼
                                            Signed URL (5 min)
                                            Auto-delete (24 hrs)
```

---

## Phases & Dependencies

### Phase 1: Foundation & Infrastructure (P0)
**Goal**: Set up database schema, dependencies, and AWS infrastructure

| Task ID | Description | Agent | Dependencies |
|---------|-------------|-------|--------------|
| TASK-001 | Database migration (report_jobs, report_access_logs) | Manual | None |
| TASK-002 | Add backend dependencies (reportlab, celery, boto3) | Manual | None |
| TASK-003 | S3 bucket with KMS + lifecycle policy | Manual | None |

**Critical Path**: All Phase 2 tasks depend on Phase 1 completion

---

### Phase 2: Backend API Development (P1)
**Goal**: Build API endpoints, Celery workers, report builders

| Task ID | Description | Agent | Dependencies |
|---------|-------------|-------|--------------|
| TASK-004 | Pydantic schemas for report requests/responses | FeatureBuilder | TASK-001 |
| TASK-005 | SQLAlchemy models (ReportJob, ReportAccessLog) | FeatureBuilder | TASK-001 |
| TASK-006 | API routes (POST /reports/at-risk, GET /jobs/{id}) | FeatureBuilder | TASK-004, TASK-005 |
| TASK-007 | Report service layer (create_job, get_status, etc.) | FeatureBuilder | TASK-005 |
| TASK-008 | Celery task for report generation | FeatureBuilder | TASK-007 |
| TASK-009 | PDF builder (ReportLab templates) | FeatureBuilder | TASK-002 |
| TASK-010 | CSV builder | FeatureBuilder | TASK-002 |
| TASK-011 | S3 uploader utility with KMS encryption | FeatureBuilder | TASK-003 |

**Critical Path**: TASK-006, TASK-008, TASK-009/010, TASK-011 must complete before frontend work

---

### Phase 3: Frontend Integration (P1-P2)
**Goal**: Build React components for report generation and history

| Task ID | Description | Agent | Dependencies |
|---------|-------------|-------|--------------|
| TASK-012 | ReportDownloader component (form + submit) | FeatureBuilder | TASK-006 |
| TASK-013 | useReportJobStatus hook (polling logic) | FeatureBuilder | TASK-012 |
| TASK-014 | ReportHistory component (list recent reports) | FeatureBuilder | TASK-006 |

**Critical Path**: TASK-012 + TASK-013 are minimum for MVP (TASK-014 is nice-to-have)

---

### Phase 4: Testing & HIPAA Compliance (P0)
**Goal**: Comprehensive testing and security audit

| Task ID | Description | Agent | Dependencies |
|---------|-------------|-------|--------------|
| TASK-015 | Write tests (API, workers, integration) | TestWriter | TASK-006, TASK-008, TASK-009, TASK-010 |

**Critical Path**: Must achieve 90% coverage (L1 requirement) before production deploy

**Manual Review Required**:
- HIPAA security audit (manual)
- Penetration testing (manual)
- Compliance officer sign-off (manual)

---

## Agent Assignments

| Agent Type | Tasks | Notes |
|------------|-------|-------|
| **Manual** | TASK-001, TASK-002, TASK-003 | Infrastructure setup requires human approval |
| **FeatureBuilder** | TASK-004 to TASK-014 | Dev Team, feature/* branches, 50 max iterations |
| **TestWriter** | TASK-015 | Dev Team, must reach 90% coverage |

---

## HIPAA Compliance Checklist

All tasks must satisfy these requirements:

- ✅ **Audit Logging**: Every PHI access logged to `report_access_logs`
- ✅ **Encryption at Rest**: S3 + KMS encryption enforced
- ✅ **Encryption in Transit**: HTTPS only, signed URLs
- ✅ **Time-Limited Access**: 5-minute URL expiry, 24-hour auto-delete
- ✅ **Access Control**: Provider role required, rate limiting (10/hour)
- ✅ **Minimum Necessary**: Only include relevant credentials in reports
- ⚠️ **Manual Security Review**: Required before production deployment

---

## Risk Assessment

| Risk | Mitigation | Status |
|------|------------|--------|
| **Performance**: Large reports (10k+ records) timeout | Stream data in chunks (500 records), 5-min timeout | Addressed in TASK-008 |
| **Storage Costs**: Reports accumulate quickly | Auto-delete after 24 hours (S3 lifecycle) | Addressed in TASK-003 |
| **Data Leakage**: Signed URLs shared externally | Single-use URLs, 5-min expiry, audit logs | Addressed in TASK-007 |
| **Infrastructure Complexity**: New Celery workers | Document deployment steps, Docker Compose for dev | Documented in notes |
| **L1 Autonomy Violations**: Agents exceed 50 lines/change | Break large tasks into smaller subtasks | Work queue sized for L1 |

---

## Deployment Checklist

**Pre-Deployment**:
1. ✅ All tasks in work queue completed
2. ✅ Tests passing with 90% coverage (TASK-015)
3. ✅ Database migration applied (TASK-001)
4. ✅ S3 bucket created with lifecycle policy (TASK-003)
5. ✅ Redis instance running
6. ⚠️ Security audit completed (manual)
7. ⚠️ HIPAA compliance officer sign-off (manual)

**Deployment Steps**:
1. Apply database migration: `alembic upgrade head`
2. Deploy backend API (with new dependencies)
3. Deploy Celery workers (new process)
4. Deploy frontend (new components)
5. Verify environment variables set:
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - `S3_BUCKET_NAME`, `KMS_KEY_ID`
   - `REDIS_URL`
6. Run smoke tests in staging
7. Monitor audit logs for first 24 hours

**Rollback Plan**:
- Database migration is additive (safe to rollback)
- Feature-flag the "Reports" tab in frontend (disable if issues)
- No breaking changes to existing APIs

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|---------------|
| **Report Generation Time** | < 30 seconds (95th percentile) | Celery task duration logs |
| **Download Success Rate** | > 99% | Report job status = completed |
| **HIPAA Compliance** | 100% audit trail coverage | Verify all downloads logged |
| **Test Coverage** | ≥ 90% | Pytest coverage report |
| **User Adoption** | 50% of providers use in first month | Analytics on /reports endpoint |

---

## Coordinator Instructions

**For Autonomous Loop**:

1. Load work queue: `adapters/credentialmate/plans/tasks/work_queue_adr001.json`
2. Execute tasks in dependency order (respect `dependencies` field)
3. For tasks with `agent: "manual"`, notify human for approval
4. For tasks with `agent: "FeatureBuilder"` or `agent: "TestWriter"`:
   - Create feature branch: `feature/ADR001-TASK-XXX`
   - Run iteration loop with Wiggum control
   - On COMPLETED, commit and continue
   - On BLOCKED, prompt human for R/O/A decision
5. Track progress in PROJECT_HQ.md
6. Update work queue status after each task
7. Create session handoff when blocked or at end of session

**Human Approval Points**:
- TASK-001: Database migration (schema changes)
- TASK-002: New dependencies (security review)
- TASK-003: Infrastructure setup (AWS costs)
- TASK-015: Test suite completion (coverage validation)
- Final: Security audit + HIPAA compliance sign-off

---

## Related Documents

- **ADR**: [ADR-001-provider-report-generation.md](./decisions/ADR-001-provider-report-generation.md)
- **Work Queue**: [work_queue_adr001.json](./tasks/work_queue_adr001.json)
- **Project Config**: [../../config.yaml](../../config.yaml)
- **Governance**: `/governance/contracts/dev-team.yaml` (L1 autonomy rules)

---

## Questions?

- **Architecture questions**: Consult @app-advisor
- **Database schema questions**: Consult @data-advisor
- **UI/UX questions**: Consult @uiux-advisor
- **HIPAA compliance questions**: Escalate to human (tmac)

---

**Last Updated**: 2026-01-09
**Status**: Ready for coordinator to begin task execution
