# CredentialMate RDS Database Data Exploration Plan

**Created**: 2026-02-02 20:30
**Purpose**: Execute systematic queries on production RDS to understand existing data
**Status**: READY FOR EXECUTION

---

## Executive Summary

This plan outlines a safe, systematic approach to explore the CredentialMate production RDS database AND compare it with the local development database to understand data differences, schema drift, and migration status.

**Production Tool**: `/Users/tmac/1_REPOS/credentialmate/tools/rds-query`
**Local Tool**: `psql` or direct PostgreSQL connection
**Lambda Function**: `credmate-rds-sql-api` (VPC-connected, read/write capable)
**Approach**: Read-only queries only, no mutations

**Key Comparisons**:
- Schema differences (missing tables, columns, indexes)
- Migration status (which migrations applied where)
- Data volume differences (row counts per table)
- Data content sampling (what data exists in prod vs local)

---

## Prerequisites

### 1. AWS Access Verification

```bash
# Verify AWS credentials are configured
aws sts get-caller-identity

# Expected output should show:
# - Account: 051826703172
# - Region: us-east-1
```

### 2. Tool Availability

```bash
# Verify rds-query tool exists
ls -l /Users/tmac/1_REPOS/credentialmate/tools/rds-query

# Tool should be executable (chmod +x if needed)
```

### 3. Lambda Function Health Check

```bash
# Verify Lambda function exists and is accessible
aws lambda get-function --function-name credmate-rds-sql-api
```

### 4. Local Database Access Verification

```bash
# Check if local PostgreSQL is running
docker ps | grep postgres

# Or if running via docker-compose
cd /Users/tmac/1_REPOS/credentialmate
docker-compose ps | grep postgres

# Test local database connection
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" -c "SELECT version();"
```

**Alternative**: Use Python script for local queries if psql not available:
```python
# Save as /tmp/local-query.py
import psycopg2
import sys
import json

conn = psycopg2.connect(
    "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local"
)
cur = conn.cursor()
cur.execute(sys.argv[1])
rows = cur.fetchall()
cols = [desc[0] for desc in cur.description]
for row in rows:
    print(dict(zip(cols, row)))
cur.close()
conn.close()
```

---

## Phase 0: Environment Comparison Setup

### Step 0.1: Define Query Helpers

```bash
# Create helper functions for consistent querying
# Add to ~/.bashrc or run in current shell

# Query production RDS
rds_query() {
  python3 /Users/tmac/1_REPOS/credentialmate/tools/rds-query "$@"
}

# Query local database
local_query() {
  psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" -t -A -c "$1"
}

# Export for use in subshells
export -f rds_query local_query
```

### Step 0.2: Create Comparison Output Directory

```bash
mkdir -p /tmp/credmate-db-comparison/{rds,local,diff}
```

---

## Phase 1: Database Metadata Discovery & Comparison

### Step 1.1: Database Version & Health

```bash
cd /Users/tmac/1_REPOS/credentialmate

# Check PostgreSQL version
python3 tools/rds-query --version
```

**Expected**: PostgreSQL version info (e.g., "PostgreSQL 14.x on x86_64")

### Step 1.2: List All Tables (Both Environments)

```bash
# RDS (Production) tables
python3 tools/rds-query --tables > /tmp/credmate-db-comparison/rds/tables.txt

# Local tables
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -c "\dt" > /tmp/credmate-db-comparison/local/tables.txt

# Or using SQL query for consistent format
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -t -A -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;" \
  > /tmp/credmate-db-comparison/local/tables-list.txt
```

### Step 1.2.1: Compare Table Lists

```bash
# Extract just table names from RDS output
python3 tools/rds-query "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name
" > /tmp/credmate-db-comparison/rds/tables-list.txt

# Compare tables (find differences)
comm -3 \
  <(sort /tmp/credmate-db-comparison/rds/tables-list.txt) \
  <(sort /tmp/credmate-db-comparison/local/tables-list.txt) \
  > /tmp/credmate-db-comparison/diff/tables-diff.txt

# Tables only in RDS (production-only tables)
comm -23 \
  <(sort /tmp/credmate-db-comparison/rds/tables-list.txt) \
  <(sort /tmp/credmate-db-comparison/local/tables-list.txt) \
  > /tmp/credmate-db-comparison/diff/tables-rds-only.txt

# Tables only in local (local-only tables)
comm -13 \
  <(sort /tmp/credmate-db-comparison/rds/tables-list.txt) \
  <(sort /tmp/credmate-db-comparison/local/tables-list.txt) \
  > /tmp/credmate-db-comparison/diff/tables-local-only.txt

echo "Tables only in RDS:"
cat /tmp/credmate-db-comparison/diff/tables-rds-only.txt
echo ""
echo "Tables only in Local:"
cat /tmp/credmate-db-comparison/diff/tables-local-only.txt
```

**Expected Tables** (from Alembic migrations):
- Core: `users`, `sessions`, `token_blacklist`, `organizations`, `organization_memberships`
- Providers: `providers`, `licenses`, `dea_registrations`, `credentials`
- Documents: `documents`, `document_classifications`, `extraction_results`, `partner_files`
- CME: `cme_activities`, `cme_requirements`, `cme_cycles`, `cme_topics`, `cme_rule_packs`
- Audit: `audit_logs`, `event_log`, `coordinator_actions`
- Messaging: `notifications`, `messages`, `campaigns`
- Practice: `practice_entities`, `practice_profiles`
- Other: `alembic_version`, `reports`, `accuracy_tracking`

### Step 1.3: Migration Status Comparison

```bash
# RDS migration status
python3 tools/rds-query "SELECT * FROM alembic_version ORDER BY version_num DESC LIMIT 10" \
  > /tmp/credmate-db-comparison/rds/migrations.txt

# Local migration status
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -t -A -c "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 10;" \
  > /tmp/credmate-db-comparison/local/migrations.txt

# Compare migration status
echo "=== RDS Migrations ==="
cat /tmp/credmate-db-comparison/rds/migrations.txt
echo ""
echo "=== Local Migrations ==="
cat /tmp/credmate-db-comparison/local/migrations.txt
echo ""
echo "=== Difference ==="
diff /tmp/credmate-db-comparison/rds/migrations.txt /tmp/credmate-db-comparison/local/migrations.txt
```

**Expected**: Both should show same latest migration, or RDS may be ahead if recent migrations not run locally

### Step 1.4: Schema Inspection & Comparison (Key Tables)

```bash
# Function to compare schema for a table
compare_table_schema() {
  local table=$1
  echo "Comparing schema for: $table"

  # RDS schema
  python3 tools/rds-query --schema $table > /tmp/credmate-db-comparison/rds/schema-${table}.txt

  # Local schema
  psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
    -c "\d $table" > /tmp/credmate-db-comparison/local/schema-${table}.txt

  # Diff
  diff /tmp/credmate-db-comparison/rds/schema-${table}.txt \
       /tmp/credmate-db-comparison/local/schema-${table}.txt \
       > /tmp/credmate-db-comparison/diff/schema-${table}-diff.txt

  if [ -s /tmp/credmate-db-comparison/diff/schema-${table}-diff.txt ]; then
    echo "  ⚠️  DIFFERENCES FOUND"
    cat /tmp/credmate-db-comparison/diff/schema-${table}-diff.txt
  else
    echo "  ✅ Schemas match"
  fi
  echo ""
}

# Compare critical tables
for table in users providers licenses organizations documents cme_activities; do
  compare_table_schema $table
done
```

### Step 1.5: Column-Level Schema Comparison

```bash
# Detailed column comparison for a specific table
compare_columns() {
  local table=$1

  echo "=== Columns in $table (RDS) ==="
  python3 tools/rds-query "
  SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
  FROM information_schema.columns
  WHERE table_schema = 'public' AND table_name = '$table'
  ORDER BY ordinal_position
  " > /tmp/credmate-db-comparison/rds/columns-${table}.txt
  cat /tmp/credmate-db-comparison/rds/columns-${table}.txt

  echo ""
  echo "=== Columns in $table (Local) ==="
  psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
    -c "SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
  FROM information_schema.columns
  WHERE table_schema = 'public' AND table_name = '$table'
  ORDER BY ordinal_position;" \
    > /tmp/credmate-db-comparison/local/columns-${table}.txt
  cat /tmp/credmate-db-comparison/local/columns-${table}.txt

  echo ""
  echo "=== Diff ==="
  diff /tmp/credmate-db-comparison/rds/columns-${table}.txt \
       /tmp/credmate-db-comparison/local/columns-${table}.txt
}

# Run for key tables
compare_columns users
compare_columns licenses
```

**Output**: Column names, types, constraints for each table with differences highlighted

---

## Phase 2: Data Volume Analysis & Comparison

### Step 2.1: Row Counts (Both Environments)

```bash
# Function to get row count from both DBs
compare_row_counts() {
  local table=$1

  # RDS count
  rds_count=$(python3 tools/rds-query --count $table 2>/dev/null | grep -oE '[0-9]+' | head -1)

  # Local count
  local_count=$(psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
    -t -A -c "SELECT COUNT(*) FROM $table;" 2>/dev/null)

  # Calculate difference
  diff=$((rds_count - local_count))

  printf "%-30s | RDS: %10s | Local: %10s | Diff: %10s\n" \
    "$table" "$rds_count" "$local_count" "$diff"
}

# Create header
echo "=== Row Count Comparison ==="
printf "%-30s | %-12s | %-12s | %-12s\n" "Table" "RDS" "Local" "Difference"
printf "%.s-" {1..75}
echo ""

# Compare all major tables
for table in users providers licenses organizations documents \
             cme_activities cme_requirements audit_logs sessions \
             notifications partner_files practice_entities \
             extraction_results document_classifications \
             cme_topics cme_cycles token_blacklist; do
  compare_row_counts $table
done | tee /tmp/credmate-db-comparison/diff/row-counts-comparison.txt
```

### Step 2.1.1: Comprehensive Table Count Comparison

```bash
# Get ALL tables and compare counts
echo "=== Complete Database Row Count Comparison ==="

# Get list of common tables
comm -12 \
  <(sort /tmp/credmate-db-comparison/rds/tables-list.txt) \
  <(sort /tmp/credmate-db-comparison/local/tables-list.txt) \
  > /tmp/credmate-db-comparison/diff/tables-common.txt

# Compare counts for all common tables
while read table; do
  compare_row_counts "$table"
done < /tmp/credmate-db-comparison/diff/tables-common.txt \
  | tee /tmp/credmate-db-comparison/diff/all-row-counts.txt
```

### Step 2.2: Data Volume Summary

```bash
# Generate summary statistics
echo "=== Database Size Comparison Summary ===" > /tmp/credmate-db-comparison/diff/summary.txt
echo "" >> /tmp/credmate-db-comparison/diff/summary.txt

# Total row counts
rds_total=$(awk '{sum+=$4} END {print sum}' /tmp/credmate-db-comparison/diff/all-row-counts.txt)
local_total=$(awk '{sum+=$6} END {print sum}' /tmp/credmate-db-comparison/diff/all-row-counts.txt)

echo "Total Rows (RDS):   $rds_total" >> /tmp/credmate-db-comparison/diff/summary.txt
echo "Total Rows (Local): $local_total" >> /tmp/credmate-db-comparison/diff/summary.txt
echo "Difference:         $((rds_total - local_total))" >> /tmp/credmate-db-comparison/diff/summary.txt
echo "" >> /tmp/credmate-db-comparison/diff/summary.txt

# Tables with most data in RDS
echo "=== Top 10 Tables by Row Count (RDS) ===" >> /tmp/credmate-db-comparison/diff/summary.txt
python3 tools/rds-query "
SELECT
  schemaname || '.' || tablename as table_name,
  n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 10
" >> /tmp/credmate-db-comparison/diff/summary.txt

cat /tmp/credmate-db-comparison/diff/summary.txt
```

---

## Phase 3: Index & Constraint Comparison

### Step 3.1: Compare Indexes

```bash
# Get indexes from RDS
python3 tools/rds-query "
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname
" > /tmp/credmate-db-comparison/rds/indexes.txt

# Get indexes from Local
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -c "SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;" \
  > /tmp/credmate-db-comparison/local/indexes.txt

# Compare
diff /tmp/credmate-db-comparison/rds/indexes.txt \
     /tmp/credmate-db-comparison/local/indexes.txt \
     > /tmp/credmate-db-comparison/diff/indexes-diff.txt

# Show missing indexes
echo "=== Indexes in RDS but not in Local ==="
comm -23 \
  <(grep "CREATE" /tmp/credmate-db-comparison/rds/indexes.txt | sort) \
  <(grep "CREATE" /tmp/credmate-db-comparison/local/indexes.txt | sort)

echo ""
echo "=== Indexes in Local but not in RDS ==="
comm -13 \
  <(grep "CREATE" /tmp/credmate-db-comparison/rds/indexes.txt | sort) \
  <(grep "CREATE" /tmp/credmate-db-comparison/local/indexes.txt | sort)
```

### Step 3.2: Compare Foreign Keys

```bash
# Get foreign keys from RDS
python3 tools/rds-query "
SELECT
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name,
  tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name
" > /tmp/credmate-db-comparison/rds/foreign-keys.txt

# Get foreign keys from Local
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -c "SELECT
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name,
  tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name;" \
  > /tmp/credmate-db-comparison/local/foreign-keys.txt

# Compare
diff /tmp/credmate-db-comparison/rds/foreign-keys.txt \
     /tmp/credmate-db-comparison/local/foreign-keys.txt \
     > /tmp/credmate-db-comparison/diff/foreign-keys-diff.txt

if [ -s /tmp/credmate-db-comparison/diff/foreign-keys-diff.txt ]; then
  echo "⚠️  Foreign key differences found:"
  cat /tmp/credmate-db-comparison/diff/foreign-keys-diff.txt
else
  echo "✅ Foreign keys match between environments"
fi
```

---

## Phase 4: Data Sample Queries (Read-Only)

### Step 4.1: User Data Overview (Both Environments)

```bash
# RDS user statistics
echo "=== User Statistics (RDS) ==="
python3 tools/rds-query "
SELECT
  role,
  COUNT(*) as count,
  COUNT(*) FILTER (WHERE is_active = true) as active_count,
  COUNT(*) FILTER (WHERE mfa_enabled = true) as mfa_enabled_count
FROM users
WHERE is_deleted = false
GROUP BY role
ORDER BY count DESC
"

echo ""
echo "=== User Statistics (Local) ==="
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -c "SELECT
  role,
  COUNT(*) as count,
  COUNT(*) FILTER (WHERE is_active = true) as active_count,
  COUNT(*) FILTER (WHERE mfa_enabled = true) as mfa_enabled_count
FROM users
WHERE is_deleted = false
GROUP BY role
ORDER BY count DESC;"

# Count active sessions
python3 tools/rds-query "
SELECT
  COUNT(*) as total_sessions,
  COUNT(*) FILTER (WHERE is_active = true) as active_sessions,
  COUNT(DISTINCT user_id) as unique_users_with_sessions
FROM sessions
"
```

### Step 3.2: Organization Data Overview

```bash
# Organization statistics
python3 tools/rds-query "
SELECT
  COUNT(*) as total_organizations,
  COUNT(*) FILTER (WHERE is_deleted = false) as active_organizations
FROM organizations
"

# Organization membership breakdown
python3 tools/rds-query "
SELECT
  o.name as organization_name,
  COUNT(om.user_id) as member_count,
  COUNT(*) FILTER (WHERE om.is_active = true) as active_members
FROM organizations o
LEFT JOIN organization_memberships om ON o.id = om.organization_id
WHERE o.is_deleted = false
GROUP BY o.id, o.name
ORDER BY member_count DESC
LIMIT 20
"
```

### Step 3.3: Provider & License Data Overview

```bash
# Provider statistics by organization
python3 tools/rds-query "
SELECT
  o.name as organization_name,
  COUNT(DISTINCT p.id) as provider_count,
  COUNT(DISTINCT p.specialty) as unique_specialties
FROM organizations o
LEFT JOIN providers p ON o.id = p.organization_id
WHERE o.is_deleted = false AND (p.is_deleted = false OR p.is_deleted IS NULL)
GROUP BY o.id, o.name
ORDER BY provider_count DESC
LIMIT 20
"

# License statistics by state
python3 tools/rds-query "
SELECT
  state,
  COUNT(*) as total_licenses,
  COUNT(*) FILTER (WHERE status = 'active') as active_licenses,
  COUNT(*) FILTER (WHERE expiration_date < CURRENT_DATE) as expired_licenses,
  COUNT(*) FILTER (WHERE expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days') as expiring_soon
FROM licenses
WHERE is_deleted = false
GROUP BY state
ORDER BY total_licenses DESC
"

# License type breakdown
python3 tools/rds-query "
SELECT
  license_type,
  COUNT(*) as count
FROM licenses
WHERE is_deleted = false
GROUP BY license_type
ORDER BY count DESC
LIMIT 20
"
```

### Step 3.4: Document & Extraction Data Overview

```bash
# Document upload statistics
python3 tools/rds-query "
SELECT
  COUNT(*) as total_documents,
  COUNT(*) FILTER (WHERE processing_status = 'completed') as processed_count,
  COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_count,
  COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_count
FROM documents
WHERE is_deleted = false
"

# Document classification breakdown
python3 tools/rds-query "
SELECT
  dc.classification,
  COUNT(*) as document_count,
  AVG(dc.confidence_score) as avg_confidence
FROM document_classifications dc
JOIN documents d ON dc.document_id = d.id
WHERE d.is_deleted = false
GROUP BY dc.classification
ORDER BY document_count DESC
"

# Extraction results summary
python3 tools/rds-query "
SELECT
  extraction_type,
  COUNT(*) as count,
  AVG(confidence_score) as avg_confidence,
  COUNT(*) FILTER (WHERE is_verified = true) as verified_count
FROM extraction_results
GROUP BY extraction_type
ORDER BY count DESC
"
```

### Step 3.5: CME Data Overview

```bash
# CME activities by provider
python3 tools/rds-query "
SELECT
  COUNT(DISTINCT provider_id) as providers_with_cme,
  COUNT(*) as total_activities,
  SUM(credits_earned) as total_credits,
  AVG(credits_earned) as avg_credits_per_activity
FROM cme_activities
WHERE is_deleted = false
"

# CME topic distribution
python3 tools/rds-query "
SELECT
  topic,
  COUNT(*) as activity_count,
  SUM(credits_earned) as total_credits
FROM cme_activities
WHERE is_deleted = false AND topic IS NOT NULL
GROUP BY topic
ORDER BY activity_count DESC
LIMIT 20
"

# CME requirements by state
python3 tools/rds-query "
SELECT
  state,
  license_type,
  required_credits,
  cycle_years
FROM cme_requirements
ORDER BY state, license_type
LIMIT 50
"
```

### Step 3.6: Audit & Activity Logs Overview

```bash
# Audit log summary by event type
python3 tools/rds-query "
SELECT
  event_type,
  COUNT(*) as event_count,
  MAX(created_at) as most_recent_event
FROM audit_logs
GROUP BY event_type
ORDER BY event_count DESC
LIMIT 30
"

# Recent audit activity (last 24 hours)
python3 tools/rds-query "
SELECT
  event_type,
  COUNT(*) as count_24h
FROM audit_logs
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY event_type
ORDER BY count_24h DESC
"

# Event log summary
python3 tools/rds-query "
SELECT
  event_category,
  COUNT(*) as event_count
FROM event_log
GROUP BY event_category
ORDER BY event_count DESC
"
```

### Step 3.7: Notification & Messaging Overview

```bash
# Notification statistics
python3 tools/rds-query "
SELECT
  notification_type,
  COUNT(*) as total_sent,
  COUNT(*) FILTER (WHERE is_read = true) as read_count,
  COUNT(*) FILTER (WHERE delivery_status = 'delivered') as delivered_count
FROM notifications
GROUP BY notification_type
ORDER BY total_sent DESC
"

# Campaign performance (if campaigns exist)
python3 tools/rds-query "
SELECT
  campaign_name,
  status,
  COUNT(*) as recipient_count
FROM campaigns
GROUP BY campaign_name, status
ORDER BY recipient_count DESC
LIMIT 20
"
```

### Step 3.8: Data Integrity Checks

```bash
# Check for orphaned records (providers without organizations)
python3 tools/rds-query "
SELECT COUNT(*) as orphaned_providers
FROM providers p
LEFT JOIN organizations o ON p.organization_id = o.id
WHERE o.id IS NULL AND p.is_deleted = false
"

# Check for licenses without providers
python3 tools/rds-query "
SELECT COUNT(*) as orphaned_licenses
FROM licenses l
LEFT JOIN providers p ON l.provider_id = p.id
WHERE p.id IS NULL AND l.is_deleted = false
"

# Check for expired credentials
python3 tools/rds-query "
SELECT
  COUNT(*) as expired_licenses,
  COUNT(DISTINCT provider_id) as providers_affected
FROM licenses
WHERE expiration_date < CURRENT_DATE
  AND status = 'active'
  AND is_deleted = false
"
```

---

## Phase 5: Data Content Comparison

### Step 5.1: Compare Specific Records

```bash
# Compare organization names (to see if same orgs exist)
echo "=== Organizations (RDS) ==="
python3 tools/rds-query "
SELECT id, name, is_deleted, created_at
FROM organizations
WHERE is_deleted = false
ORDER BY id
LIMIT 10
"

echo ""
echo "=== Organizations (Local) ==="
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -c "SELECT id, name, is_deleted, created_at
FROM organizations
WHERE is_deleted = false
ORDER BY id
LIMIT 10;"

# Compare user emails (hashed for privacy)
echo ""
echo "=== User Email Hashes (RDS) ==="
python3 tools/rds-query "
SELECT
  id,
  role,
  MD5(email) as email_hash,
  is_active
FROM users
WHERE is_deleted = false
ORDER BY id
LIMIT 10
"

echo ""
echo "=== User Email Hashes (Local) ==="
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -c "SELECT
  id,
  role,
  MD5(email) as email_hash,
  is_active
FROM users
WHERE is_deleted = false
ORDER BY id
LIMIT 10;"
```

### Step 5.2: Compare Data Distributions

```bash
# License distribution by state
echo "=== License Distribution by State (RDS) ==="
python3 tools/rds-query "
SELECT state, COUNT(*) as count
FROM licenses
WHERE is_deleted = false
GROUP BY state
ORDER BY count DESC
LIMIT 10
" > /tmp/credmate-db-comparison/rds/licenses-by-state.txt
cat /tmp/credmate-db-comparison/rds/licenses-by-state.txt

echo ""
echo "=== License Distribution by State (Local) ==="
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -c "SELECT state, COUNT(*) as count
FROM licenses
WHERE is_deleted = false
GROUP BY state
ORDER BY count DESC
LIMIT 10;" \
  > /tmp/credmate-db-comparison/local/licenses-by-state.txt
cat /tmp/credmate-db-comparison/local/licenses-by-state.txt

# Compare
echo ""
echo "=== Difference ==="
diff /tmp/credmate-db-comparison/rds/licenses-by-state.txt \
     /tmp/credmate-db-comparison/local/licenses-by-state.txt
```

### Step 5.3: Check for Production-Only Data

```bash
# Check if RDS has data that local doesn't
echo "=== Checking for Production-Only Data ==="

# Example: Users that exist in RDS but not in local
python3 tools/rds-query "SELECT COUNT(*) as user_count FROM users WHERE is_deleted = false" \
  > /tmp/rds-user-count.txt
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -t -A -c "SELECT COUNT(*) FROM users WHERE is_deleted = false;" \
  > /tmp/local-user-count.txt

rds_users=$(cat /tmp/rds-user-count.txt | grep -oE '[0-9]+')
local_users=$(cat /tmp/local-user-count.txt)

if [ "$rds_users" -gt "$local_users" ]; then
  echo "⚠️  RDS has $((rds_users - local_users)) more users than local"
  echo "   This is expected - production has real user data"
else
  echo "✅ User counts similar or local has test data"
fi
```

---

## Phase 6: Sample Data Inspection (Anonymized)

### Step 4.1: Sample Records (NO PII)

```bash
# Sample user roles (emails masked)
python3 tools/rds-query "
SELECT
  id,
  role,
  is_active,
  mfa_enabled,
  created_at
FROM users
WHERE is_deleted = false
ORDER BY created_at DESC
LIMIT 5
"

# Sample provider records (names/PII excluded)
python3 tools/rds-query "
SELECT
  id,
  organization_id,
  specialty,
  subspecialty,
  practice_state,
  created_at
FROM providers
WHERE is_deleted = false
ORDER BY created_at DESC
LIMIT 10
"

# Sample license records
python3 tools/rds-query "
SELECT
  id,
  provider_id,
  state,
  license_type,
  status,
  issue_date,
  expiration_date
FROM licenses
WHERE is_deleted = false
ORDER BY created_at DESC
LIMIT 10
"
```

---

## Phase 7: Data Quality Analysis (Both Environments)

### Step 5.1: Completeness Checks

```bash
# Check for NULL critical fields in providers
python3 tools/rds-query "
SELECT
  COUNT(*) FILTER (WHERE npi IS NULL) as missing_npi,
  COUNT(*) FILTER (WHERE email IS NULL) as missing_email,
  COUNT(*) FILTER (WHERE specialty IS NULL) as missing_specialty,
  COUNT(*) FILTER (WHERE practice_state IS NULL) as missing_state
FROM providers
WHERE is_deleted = false
"

# Check for NULL critical fields in licenses
python3 tools/rds-query "
SELECT
  COUNT(*) FILTER (WHERE license_number IS NULL) as missing_license_number,
  COUNT(*) FILTER (WHERE expiration_date IS NULL) as missing_expiration,
  COUNT(*) FILTER (WHERE license_type IS NULL) as missing_type
FROM licenses
WHERE is_deleted = false
"
```

### Step 5.2: Date Range Analysis

```bash
# User creation timeline
python3 tools/rds-query "
SELECT
  DATE(created_at) as creation_date,
  COUNT(*) as users_created
FROM users
WHERE is_deleted = false
GROUP BY DATE(created_at)
ORDER BY creation_date DESC
LIMIT 30
"

# Document upload timeline
python3 tools/rds-query "
SELECT
  DATE(uploaded_at) as upload_date,
  COUNT(*) as documents_uploaded
FROM documents
WHERE is_deleted = false
GROUP BY DATE(uploaded_at)
ORDER BY upload_date DESC
LIMIT 30
"
```

---

## Output & Documentation

### 1. Create Summary Report

After running all queries, compile findings into:

**File**: `/Users/tmac/1_REPOS/AI_Orchestrator/sessions/credentialmate/active/20260202-2030-rds-data-exploration-results.md`

**Contents**:
- Database version and health (both environments)
- Complete table list with row counts (comparison)
- Schema differences (tables, columns, indexes, constraints)
- Migration status comparison
- Data distribution summaries (users, orgs, providers, licenses, CME, etc.)
- Data volume differences between RDS and local
- Data quality findings (missing fields, orphaned records, etc.)
- Recommendations for:
  - Schema synchronization (if drift detected)
  - Missing migrations to apply
  - Data cleanup (if needed)
  - Local DB refresh (if too out of sync)

### 2. Export JSON Data (If Needed)

```bash
# Export specific data sets as JSON for analysis
python3 tools/rds-query "SELECT * FROM organizations WHERE is_deleted = false" --json > /tmp/organizations.json
python3 tools/rds-query "SELECT state, COUNT(*) as count FROM licenses GROUP BY state" --json > /tmp/licenses-by-state.json
```

---

## Safety Considerations

### ✅ Safe Practices (READ-ONLY)
- Using `SELECT` queries only
- Using aggregation functions (COUNT, SUM, AVG)
- Using LIMIT clauses
- Filtering with `WHERE is_deleted = false`
- Excluding PII in sample queries

### ⚠️ Avoid During Exploration
- `UPDATE` / `DELETE` / `INSERT` statements
- `TRUNCATE` / `DROP` statements
- Queries without `LIMIT` on large tables
- Exposing PII (emails, SSN, DOB) in outputs
- Large data exports (>5MB payload limit)

### 🔒 Protected by Lambda
- All queries wrapped in read-only transaction
- 5-minute timeout limit
- 5MB payload size limit
- CloudTrail audit logging enabled
- VPC security group restrictions

---

## Troubleshooting

### Error: "Database connection failed"
**Fix**: Check Lambda VPC configuration and security groups
```bash
aws lambda get-function-configuration --function-name credmate-rds-sql-api \
  --query 'VpcConfig'
```

### Error: "Timeout"
**Fix**: Add `LIMIT` clause or optimize query
```bash
# Instead of: SELECT * FROM audit_logs
# Use: SELECT * FROM audit_logs LIMIT 100
```

### Error: "Payload too large"
**Fix**: Reduce result set with LIMIT or aggregation
```bash
# Instead of: SELECT * FROM documents
# Use: SELECT COUNT(*), processing_status FROM documents GROUP BY processing_status
```

### No Results Returned
**Fix**: Check table names and verify data exists
```bash
# Verify table exists
python3 tools/rds-query --tables | grep "table_name"

# Check row count
python3 tools/rds-query --count table_name
```

---

## Estimated Execution Time

- Phase 0 (Setup): ~2 minutes
- Phase 1 (Metadata & Comparison): ~8 minutes
- Phase 2 (Volume Comparison): ~5 minutes
- Phase 3 (Index/Constraint Comparison): ~5 minutes
- Phase 4 (Data Samples): ~15 minutes
- Phase 5 (Content Comparison): ~10 minutes
- Phase 6 (Sample Inspection): ~5 minutes
- Phase 7 (Quality Analysis): ~5 minutes

**Total**: ~55-60 minutes for complete exploration and comparison

**Quick Comparison Only** (Phases 0-3): ~20 minutes

---

## Key Comparison Insights to Look For

### 1. Schema Drift Indicators
- **Missing tables**: Tables in RDS but not local (or vice versa)
- **Column differences**: Different columns, types, or constraints
- **Index mismatches**: Missing or different indexes
- **Migration lag**: RDS ahead of local in migration versions

### 2. Data Volume Indicators
- **Zero local data**: Local DB empty or minimal test data
- **Large RDS datasets**: Production has real user/provider data
- **Audit log differences**: Production accumulates logs, local doesn't

### 3. Expected Differences
- **Production should have MORE**:
  - Users, providers, licenses (real data)
  - Audit logs, sessions (activity history)
  - Documents, extractions (uploaded files)
  - CME activities (user-generated)

- **Local might have MORE**:
  - Test users with predictable data
  - Development-only tables (if any)

### 4. Unexpected Differences (Investigate)
- **Local has tables RDS doesn't**: Old test migrations?
- **RDS missing indexes**: Performance risk
- **Foreign key mismatches**: Data integrity risk
- **Migration version mismatch**: Deployment issue?

---

## Next Steps After Completion

1. **Review findings** in results summary document
2. **Identify schema drift** and plan synchronization
3. **Check migration status** - apply missing migrations
4. **Identify data quality issues** (if any)
5. **Plan data cleanup** (separate session if needed)
6. **Update INFRASTRUCTURE.md** with data insights
7. **Consider local DB refresh** from RDS snapshot if too out of sync
8. **Document comparison** in session file for future reference

---

## Quick Start Comparison

For a fast sanity check before running the full plan:

```bash
cd /Users/tmac/1_REPOS/credentialmate

# 1. Check if local DB is running
docker-compose ps | grep postgres

# 2. Compare migration versions
echo "RDS Migration:"
python3 tools/rds-query "SELECT version_num FROM alembic_version"
echo "Local Migration:"
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -t -A -c "SELECT version_num FROM alembic_version;"

# 3. Compare table counts
echo "RDS Tables:"
python3 tools/rds-query --tables | wc -l
echo "Local Tables:"
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -t -A -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# 4. Compare user counts
echo "RDS Users:"
python3 tools/rds-query --count users
echo "Local Users:"
psql "postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local" \
  -t -A -c "SELECT COUNT(*) FROM users;"
```

**Time**: ~2 minutes

---

## References

- Infrastructure Docs: `/Users/tmac/1_REPOS/credentialmate/docs/INFRASTRUCTURE.md`
- RDS Query Tool: `/Users/tmac/1_REPOS/credentialmate/tools/rds-query`
- Alembic Migrations: `/Users/tmac/1_REPOS/credentialmate/apps/backend-api/alembic/versions/`
- Alembic Config: `/Users/tmac/1_REPOS/credentialmate/apps/backend-api/alembic.ini`
- Execute SQL Skill: `/Users/tmac/1_REPOS/credentialmate/.claude/skills/execute-production-sql/skill.md`
- Local DB Connection: `postgresql://credmate_user:credmate_local_pass@localhost:5432/credmate_local`

---

**Plan Status**: ✅ READY FOR EXECUTION
**Reviewed By**: AI Orchestrator
**Approval Required**: None (read-only queries)
