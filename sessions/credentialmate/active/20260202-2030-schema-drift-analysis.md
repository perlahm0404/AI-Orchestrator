# CredentialMate Schema Drift Analysis

**Date**: 2026-02-02 20:30
**Comparison**: Production RDS vs Local Development Database
**Status**: ⚠️ **CRITICAL DRIFT DETECTED**

---

## Executive Summary

The local development database is **16 days ahead** of production in terms of migrations, resulting in:
- **12 tables** in local that don't exist in RDS (missing features in production)
- **2 tables** in RDS that don't exist in local (possibly renamed/refactored)
- **22+ columns** added to existing tables (significant schema changes)
- **10 migrations** not applied to production

**Impact**: Production is missing critical new features and schema enhancements added between Jan 15-31, 2026.

**Recommendation**: Apply pending migrations to production IMMEDIATELY to maintain feature parity.

---

## Migration Status

| Environment | Latest Migration | Date | Status |
|-------------|------------------|------|--------|
| **Production (RDS)** | `20260115_0200_add_license_is_imlc_field` | Jan 15, 2026 02:00 | ⚠️ **16 days behind** |
| **Local (Dev)** | `20260131_0000_add_blueshift_provider_fields` | Jan 31, 2026 00:00 | ✅ Current |
| **Gap** | 16 days | ~10 migrations | **CRITICAL** |

---

## Table Count Summary

```
Production (RDS):  55 tables
Local (Dev):       65 tables
Difference:        +10 tables (18% more in local)
```

---

## Part 1: Missing Tables in Production

### Critical Missing Tables (12 tables not in RDS)

#### 1. **Accuracy Testing Infrastructure**
**Migration**: `20260109_0200_create_accuracy_tables.py`

| Table | Purpose |
|-------|---------|
| `accuracy_test_results` | Store test execution results |
| `accuracy_test_runs` | Track test run metadata |
| `ground_truth_documents` | Reference documents for validation |

**Risk**: ⚠️ Production cannot validate AI extraction accuracy or run quality tests

#### 2. **Duplicate Detection System**
**Migration**: `20260109_0100_add_duplicate_handling_infrastructure.py`

| Table | Purpose |
|-------|---------|
| `duplicate_events` | Track detected duplicates |
| `duplicate_review_queue` | Manual review queue for duplicates |

**Risk**: ⚠️ Production may accumulate duplicate credentials/CME activities without detection

#### 3. **Team Messaging System**
**Migration**: `20260108_0400_add_team_messaging_tables.py`

| Table | Purpose |
|-------|---------|
| `threads` | Message thread containers |
| `thread_messages` | Individual messages in threads |
| `channels` | Communication channels (replaces `team_channels`) |

**Risk**: ⚠️ Production users cannot access in-app messaging features

#### 4. **Report Access Auditing**
**Migration**: `20260109_0300_add_report_generation_tables.py`

| Table | Purpose |
|-------|---------|
| `report_access_logs` | Audit trail for report views/downloads |

**Risk**: ⚠️ No compliance trail for HIPAA-required report access tracking

#### 5. **Provider Credentials Consolidation**
**Migration**: `20260115_0300_add_provider_credentials_table.py`

| Table | Purpose |
|-------|---------|
| `provider_credentials` | Unified view of all provider credentials |

**Risk**: ⚠️ Production missing unified credential management interface

#### 6. **Payment Processing**
**Migration**: `20260131_0000_add_blueshift_provider_fields.py`

| Table | Purpose |
|-------|---------|
| `payment_methods` | Payment methods for subscriptions/billing |

**Risk**: 🚨 **CRITICAL** - Production cannot process payments if billing enabled

#### 7. **Coordinator Preferences**
**Migration**: `20260127_1121_7702d353e5b8_add_coordinator_notification_.py`

| Table | Purpose |
|-------|---------|
| `coordinator_notification_preferences` | Per-coordinator notification settings |

**Risk**: ⚠️ Production coordinators cannot customize notification preferences

---

### Legacy Tables in Production (2 tables not in local)

| Table | Status | Action Required |
|-------|--------|-----------------|
| `session` (singular) | Likely renamed to `sessions` | Verify rename migration, check for data |
| `team_channels` | Replaced by `channels` | Migrate data to `channels` table |

**Note**: These may require data migration before applying new migrations.

---

## Part 2: Column-Level Schema Drift

### Licenses Table
**New columns in local** (Migration: `20260115_0100_add_license_portal_fields`):
- `portal_pin` - Portal access PIN
- `renewal_notes` - Renewal-specific notes

### Providers Table
**New columns in local** (Migration: `20260131_0000_add_blueshift_provider_fields`):

**🚨 20 NEW COLUMNS** - Major schema enhancement for credentialing completeness:

| Column | Purpose |
|--------|---------|
| `aoa_number` | American Osteopathic Association number |
| `citizenship_status` | Citizenship verification |
| `cv_reference` | CV document reference |
| `disclosure_notes` | Disclosure/attestation notes |
| `employer_start_date` | Current employer start date |
| `fcvs_fid` | FCVS Federation ID |
| `gender` | Provider gender |
| `green_card_uscis_number` | Immigration documentation |
| `height` | Physical characteristics |
| `weight` | Physical characteristics |
| `home_address` | Residential address line 1 |
| `home_city` | Residential city |
| `home_state` | Residential state |
| `home_zip` | Residential ZIP code |
| `name_change_documents` | Legal name change documentation |
| `place_of_birth` | Birth location |
| `previous_names` | Historical names |
| `race` | Demographic information |
| `references` | Professional references |
| `renewal_preferences` | License renewal preferences |

**Risk**: 🚨 **CRITICAL** - Production missing essential credentialing fields required for complete applications

---

## Part 3: Pending Migrations (NOT in Production)

### Migrations Applied to Local but NOT to RDS

| Migration | Date | Type | Impact |
|-----------|------|------|--------|
| `20260115_0300` | Jan 15 | Table | `provider_credentials` table |
| `20260108_0200` | Jan 8 | Columns | Specialty conditional fields |
| `20260108_0400` | Jan 8 | Tables | Messaging infrastructure |
| `20260108_0500` | Jan 8 | Columns | Applicability constraints |
| `20260109_0100` | Jan 9 | Tables | Duplicate detection |
| `20260109_0200` | Jan 9 | Tables | Accuracy testing |
| `20260109_0300` | Jan 9 | Tables | Report access logging |
| `20260110_0100` | Jan 10 | Columns | Board-specific course fields |
| `20260110_0200` | Jan 10 | Columns | Normalized topic column |
| `20260111_0100` | Jan 11 | Columns | CME rule state-specific |
| `20260112_0100` | Jan 12 | Columns | CME rule source restricted |
| `20260114_0100` | Jan 14 | Indexes | Batch state coverage indexes |
| `20260114_1830` | Jan 14 | Columns | Campaign `started_at` field |
| `20260127_0100` | Jan 27 | Enum | Stage changed action type |
| `20260127_1121` | Jan 27 | Table | Coordinator notification prefs |
| `20260131_0000` | Jan 31 | Columns+Table | **20 provider fields** + `payment_methods` |

**Total**: ~16 migrations pending

---

## Part 4: Risk Assessment

### 🚨 Critical Risks

1. **Payment Processing Disabled**
   - `payment_methods` table missing
   - Cannot process subscriptions if billing enabled

2. **Incomplete Credentialing Applications**
   - 20 provider fields missing in production
   - Applications may be rejected for missing required information

3. **HIPAA Compliance Gap**
   - No report access logging
   - Potential audit trail violation

### ⚠️ High Risks

4. **Duplicate Data Accumulation**
   - No duplicate detection in production
   - Data quality degradation over time

5. **Feature Functionality Broken**
   - Messaging system unavailable
   - Coordinator preferences not customizable
   - Unified credential view missing

### ⚙️ Medium Risks

6. **Test/QA Capability Missing**
   - Cannot run accuracy tests in production
   - No validation framework

7. **Schema Inconsistency**
   - Development and production diverging
   - Increased deployment risk

---

## Part 5: Data Integrity Checks

### Tables Requiring Data Migration

| From (RDS) | To (Local) | Action Required |
|------------|------------|-----------------|
| `session` | `sessions` | Verify rename, migrate active sessions |
| `team_channels` | `channels` | Migrate channel data, update references |

### New Tables Requiring Seeding

| Table | Seed Data Needed |
|-------|------------------|
| `coordinator_notification_preferences` | Default preferences for existing coordinators |
| `payment_methods` | Default billing configurations (if applicable) |

---

## Part 6: Recommendations

### Immediate Actions (Next 24 Hours)

1. **📋 Review Migration Safety**
   - Read through all 16 pending migrations
   - Identify any destructive operations
   - Check for data migrations vs schema-only

2. **🔄 Apply Migrations to Production**
   - Execute migrations in chronological order
   - Monitor for errors
   - Verify schema changes applied correctly

3. **🔍 Validate Data Integrity**
   - Check for orphaned records after migration
   - Verify foreign key constraints
   - Test new table constraints

4. **🧪 Test Critical Features**
   - Payment processing (if enabled)
   - Provider credentialing forms
   - Report access logging
   - Duplicate detection

### Short-Term Actions (Next Week)

5. **📊 Seed New Tables**
   - Add default coordinator notification preferences
   - Configure payment methods if needed
   - Initialize duplicate detection rules

6. **📖 Update Documentation**
   - Document new schema in INFRASTRUCTURE.md
   - Update API documentation for new fields
   - Training for new provider fields

7. **🔒 Compliance Verification**
   - Verify report access logging working
   - Audit HIPAA compliance after migration
   - Test data retention policies

### Long-Term Actions (Next Month)

8. **🚀 Establish Migration CI/CD**
   - Automate migration application
   - Add pre-deployment schema validation
   - Prevent drift from recurring

9. **📈 Monitor New Features**
   - Track duplicate detection effectiveness
   - Monitor accuracy test usage
   - Review payment processing metrics

---

## Part 7: Migration Application Plan

### Pre-Migration Checklist

- [ ] Backup production database
- [ ] Test migrations on staging/copy of production data
- [ ] Verify rollback procedures
- [ ] Schedule maintenance window
- [ ] Notify stakeholders

### Migration Execution Order

```bash
# Connect to production RDS via migration Lambda or direct connection
cd /Users/tmac/1_REPOS/credentialmate/apps/backend-api

# Apply migrations in order (after RDS version 20260115_0200)
alembic upgrade 20260115_0300  # provider_credentials table
alembic upgrade 20260127_1121  # coordinator_notification_preferences
alembic upgrade 20260131_0000  # blueshift provider fields + payment_methods

# Or apply all pending:
alembic upgrade head
```

### Post-Migration Validation

```bash
# Verify migration status
python3 /Users/tmac/1_REPOS/credentialmate/tools/rds-query \
  "SELECT version_num FROM alembic_version"

# Check table count
python3 /Users/tmac/1_REPOS/credentialmate/tools/rds-query --tables | wc -l
# Expected: 65 tables (matching local)

# Verify new tables exist
python3 /Users/tmac/1_REPOS/credentialmate/tools/rds-query \
  --schema provider_credentials

python3 /Users/tmac/1_REPOS/credentialmate/tools/rds-query \
  --schema payment_methods
```

---

## Part 8: Comparison Artifacts

All comparison outputs saved to:
```
/tmp/credmate-db-comparison/
├── rds/
│   ├── tables-list.txt
│   ├── migration-version.txt
│   └── *-columns.txt
├── local/
│   ├── tables-list.txt
│   ├── migration-version.txt
│   └── *-columns.txt
└── diff/
    ├── tables-local-only.txt
    ├── tables-rds-only.txt
    └── summary.txt
```

---

## Part 9: Summary Statistics

```
Schema Drift Metrics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Migration Lag:            16 days
Migrations Pending:       ~16 migrations
Tables Missing in RDS:    12 tables (18% of local total)
Columns Missing in RDS:   22+ columns across multiple tables
Critical Tables Missing:  3 (payment_methods, provider_credentials, report_access_logs)
Features Unavailable:     5 (payments, messaging, duplicates, accuracy tests, unified credentials)
Compliance Risk:          MEDIUM (missing audit logs)
Data Quality Risk:        MEDIUM (no duplicate detection)
Business Risk:            HIGH (missing payment processing)
```

---

## Conclusion

**Status**: 🚨 **PRODUCTION DATABASE CRITICALLY OUT OF DATE**

**Primary Issue**: Production RDS is 16 days behind local development database, missing 12 tables, 22+ columns, and critical features including payment processing, credentialing fields, and compliance logging.

**Root Cause**: Migrations created between Jan 8-31 have not been applied to production. Possible causes:
- Deployment pipeline not running
- Manual migration steps skipped
- Migration failures not detected

**Next Steps**:
1. **URGENT**: Review and apply pending migrations to production
2. Test critical features after migration
3. Establish automated migration deployment
4. Add schema validation to CI/CD pipeline

---

**Report Generated**: 2026-02-02 20:30 UTC
**Generated By**: AI Orchestrator Schema Comparison Tool
**Files**: See `/tmp/credmate-db-comparison/` for raw comparison data
