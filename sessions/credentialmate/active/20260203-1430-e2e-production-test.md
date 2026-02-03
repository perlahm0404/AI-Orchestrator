# E2E Document Processing Test - Production

**Date:** 2026-02-03
**Test User:** real1@test.com (Dr. Ashok Sehgal, NPI 1536531478)
**Environment:** Production (credentialmate.com)
**Objective:** Validate end-to-end document upload → Lambda processing → extraction → display workflow

---

## Phase 0: Pre-Test Backup & Rollback Preparation

### 0.1 Pre-Test Baseline

**Test Start Time:** 2026-02-03 13:01:16 UTC

**Environment Details:**
- AWS Account: 051826703172
- Region: us-east-1
- Frontend: https://credentialmate.com (CloudFront: E3C4D2B3O2P8FS)
- API: https://api.credentialmate.com
- Database: RDS Production (prod-credmate-db)
- Lambda Worker: credmate-worker-prod

**Test Data Source:**
- Location: `/Users/tmac/1_REPOS/credentialmate/test-fixtures/real-users/sehgal/`
- Available Documents: 37 CME certificates
- Test Account: real1@test.com / Test1234
- Organization ID: 1001

### Database Baseline (Captured at 13:01 UTC)

**Current Record Counts:**
- users: 163
- organizations: 12
- providers: 852
- documents: **0** (clean slate - no existing documents!)
- extraction_results: **0**

**Test User Check:**
- real1@test.com: **Does NOT exist** (clean slate)
- Organization ID 1001: **Does NOT exist** (clean slate)

### S3 Baseline

**S3 Bucket Status:**
- Bucket `credmate-documents-prod`: Does not exist yet
- Expected: Will be auto-created on first document upload
- Current document count: 0

### RDS Snapshot Created

**Snapshot Details:**
- Snapshot ID: `credmate-e2e-test-backup-20260203-0702`
- Status: ✅ Available
- Created: 2026-02-03T13:02:26.849000+00:00
- Size: 20 GB
- Can be restored if rollback needed

**Full baseline saved to:** `sessions/credentialmate/active/20260203-1430-baseline.txt`

### Phase 0 Status: ✅ COMPLETE

**Rollback Capability Established:**
- RDS Snapshot: credmate-e2e-test-backup-20260203-0702 (20GB, available)
- Baseline captured: All current counts documented
- Clean slate confirmed: No test user, no documents, no extractions
- Ready to proceed to Phase 1

### Rollback Points Established

**Rollback Point 1:** After database seeding (delete test user and related data)
**Rollback Point 2:** After document upload (delete test documents only)
**Nuclear Option:** RDS snapshot restore (only if critical production issue)

### Rollback Triggers

**Automatic:**
- Lambda error rate >10%
- Database connection exhaustion
- S3 access denied errors
- Frontend 500 errors
- Customer complaints

**Manual Decision Points:**
- Extraction accuracy <80%
- Processing time >5 min per document
- Confidence scores <0.5
- Critical bugs in extraction logic

---

## Phase 1: File Review & Tier Selection

### Available Test Fixtures (from manifest.json)

**CME Certificates:** 37 PDFs
- 28 ACCME transcript PDFs (12642_729_1.pdf through 12642_913_1.pdf)
- 9 Individual certificates (Certificate_*.pdf)

### Recommended Test Tiers

**Tier 1: Smoke Test (5 documents, ~10 min, ~$0.075)**
1. 12642_740_1.pdf - CME Certificate (ACCME format)
2. Certificate_94151.pdf - CME Certificate (individual format)
3. [License PDF - TBD based on availability]
4. [DEA Certificate - TBD]
5. [CSR Certificate - TBD]

**Tier 2: Representative Sample (20 documents, 1-2 hours, ~$0.30)**
- 10 CME Certificates (mix of formats)
- 8 Medical Licenses (variety of states)
- 1 DEA Registration
- 1 CSR Certificate

**Tier 3: Full Batch (37+ documents, 3-4 hours, ~$0.56)**
- All available CME certificates
- All licenses, DEA, CSR documents

**USER APPROVAL GATE #1:** [PENDING - Awaiting tier selection]

---

## Phase 2: Environment Preparation

### 2.1 Database Seeding Status
[PENDING]

### 2.2 Frontend Access Verification
[PENDING]

### 2.3 Backend API Health
[PENDING]

### 2.4 Lambda Worker Status
[PENDING]

**USER APPROVAL GATE #2:** [PENDING - Confirm environment ready]

---

## Phase 3: Test Execution

### Upload Strategy
[PENDING - Will be determined based on tier selection]

### Test Results

| Document ID | Filename | Type | Status | Confidence | Duration | Notes |
|-------------|----------|------|--------|------------|----------|-------|
| [PENDING] | [PENDING] | [PENDING] | [PENDING] | [PENDING] | [PENDING] | [PENDING] |

### Monitoring Logs
[Will capture CloudWatch logs, database status, S3 verification]

---

## Phase 4: Data Validation

### Extraction Accuracy Validation
[PENDING - Manual verification of 3-5 sample documents]

### Aggregate Metrics
[PENDING - Will run SQL queries for completeness analysis]

---

## Phase 5: Documentation & Cleanup

### Test Results Summary

**Total Documents:** [PENDING]
**Processing Success Rate:** [PENDING]
**Average Processing Time:** [PENDING]
**Average Confidence Score:** [PENDING]
**Extraction Accuracy:** [PENDING]
**Total Cost:** [PENDING]

### Issues Found
[PENDING]

### Screenshots
[PENDING - Will save to sessions/credentialmate/active/screenshots/]

### Cleanup Decision
**USER APPROVAL GATE #3:** [PENDING - Keep, delete, or archive test data]

---

## Notes & Observations

[Running log of findings during test execution]
