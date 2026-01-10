# Operator Team Usage Guide

## Quick Start

The Operator Team handles deployments, migrations, and rollbacks with environment-gated automation.

## How to Use the Operator Team

### 1. Manual Deployment (Interactive)

**For development deployments:**

```bash
# Simple prompt - Operator Team auto-deploys to dev
"Deploy version 1.2.3 to development environment for karematch"
```

**For staging deployments (first-time requires approval):**

```bash
# Operator Team will ask for approval on first staging deployment
"Deploy version 1.2.3 to staging environment for credentialmate"
```

**For production deployments (ALWAYS requires approval):**

```bash
# Operator Team will ALWAYS ask for approval
"Deploy version 2.0.0 to production environment for karematch with migrations"
```

### 2. Work Queue Deployment (Automated)

Add deployment tasks to `tasks/work_queue_<project>.json`:

```json
{
  "project": "karematch",
  "features": [
    {
      "id": "DEPLOY-001",
      "description": "Deploy v1.2.3 to staging with database migrations",
      "status": "pending",
      "agent_type": "deployment",
      "environment": "staging",
      "version": "1.2.3",
      "run_migrations": true,
      "migrations_path": "backend/alembic/versions",
      "completion_promise": "DEPLOYMENT_COMPLETE",
      "max_iterations": 10
    }
  ]
}
```

Then run:

```bash
python autonomous_loop.py --project karematch --max-iterations 50
```

### 3. Migration-Only Tasks

**Validate migrations without deploying:**

```bash
"Validate all Alembic migrations in credentialmate for production environment"
```

**Run migrations (with safety checks):**

```json
{
  "id": "MIGRATE-001",
  "description": "Run database migrations for credentialmate staging",
  "agent_type": "migration",
  "environment": "staging",
  "migrations_path": "apps/backend-api/alembic/versions",
  "completion_promise": "MIGRATIONS_COMPLETE"
}
```

### 4. Rollback Tasks

**Auto-rollback (dev/staging):**

```bash
# Operator Team auto-rolls back on failure in dev/staging
"If deployment fails, auto-rollback is enabled for dev and staging"
```

**Manual rollback (production):**

```bash
# Production rollback requires explicit approval
"Rollback production deployment to version 1.9.5"
```

---

## Environment Gates

| Environment | Auto-Deploy? | Auto-Rollback? | Approval Required? |
|-------------|--------------|----------------|--------------------|
| **Development** | ✅ Yes | ✅ Yes | ❌ No |
| **Staging** | ⚠️ First-time only | ✅ Yes | ⚠️ First-time only |
| **Production** | ❌ No | ❌ No | ✅ ALWAYS |

---

## Prompting Patterns

### Basic Deployment

```
Deploy karematch version 1.2.3 to development
```

**What happens:**
1. Pre-deployment validation (tests, safety checks)
2. Build application
3. Deploy to dev
4. Health checks
5. ✅ Done (auto-deploy in dev)

### Deployment with Migrations

```
Deploy credentialmate version 2.0.0 to staging with database migrations.
Migration path: apps/backend-api/alembic/versions
```

**What happens:**
1. Validate migrations (check for downgrade(), SQL safety)
2. Run tests
3. Build application
4. Deploy to staging (approval required on first-time)
5. Run migrations
6. Health checks
7. ✅ Done

### Production Deployment (Full Ceremony)

```
Deploy credentialmate version 2.1.0 to PRODUCTION.

Requirements:
- Run database migrations from apps/backend-api/alembic/versions
- Version tag: v2.1.0
- Include health checks post-deployment

I understand this requires my explicit approval.
```

**What happens:**
1. Validate migrations for production (STRICT: must have downgrade())
2. Scan for SQL safety violations (DROP TABLE, TRUNCATE, etc.)
3. Scan for S3 safety violations (bucket deletion, etc.)
4. Run full test suite
5. Build application
6. **⏸️ HALT: Request human approval**
7. (User approves)
8. Deploy to production
9. Run migrations
10. Health checks
11. ✅ Done (manual verification required)

---

## Safety Validations (Automatic)

### SQL Safety Scanner

**BLOCKED patterns (CRITICAL):**
- `DROP DATABASE` - Irreversible data loss
- `DROP TABLE` - Irreversible data loss
- `TRUNCATE TABLE` - Irreversible data deletion
- `DELETE FROM table;` (no WHERE clause) - Deletes all rows

**Example:**

```sql
-- ❌ BLOCKED in production
DROP TABLE old_users;

-- ✅ ALLOWED (with warning)
DELETE FROM sessions WHERE created_at < NOW() - INTERVAL '30 days';
```

### S3 Safety Scanner

**BLOCKED patterns (CRITICAL):**
- `s3.delete_bucket()` - Irreversible bucket deletion
- `awslocal s3 rb` - Remove bucket command
- `s3.delete_objects(Bucket=...)` (bulk deletion) - HIGH risk

**Example:**

```python
# ❌ BLOCKED
s3.delete_bucket(Bucket='production-data')

# ✅ ALLOWED (with warning)
s3.delete_object(Bucket='temp', Key='file.txt')  # Single object OK
```

### Migration Validator

**Production requirements:**
- ✅ Must have `upgrade()` method
- ✅ Must have `downgrade()` method (reversibility REQUIRED)
- ✅ No DROP TABLE in production migrations
- ✅ No TRUNCATE in production migrations

**Example:**

```python
# ✅ VALID for production
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(255)))

def downgrade():
    op.drop_column('users', 'email')  # Reversible


# ❌ INVALID for production (empty downgrade)
def upgrade():
    op.execute('DELETE FROM temp_data')

def downgrade():
    pass  # Not reversible!
```

---

## AWS Provisioning

When requesting new AWS resources, provide a business case:

```
Provision a new S3 bucket for karematch user uploads.

Business Case:
- Justification: Store user-uploaded profile photos (HIPAA-compliant storage)
- Cost estimate: $50/month (1TB storage + transfer)
- Alternatives considered:
  1. Use existing bucket (rejected - HIPAA isolation requirement)
  2. Cloudflare R2 (rejected - AWS ecosystem integration)
- Risk assessment:
  - Security: Bucket will have private ACL, encryption at rest
  - Operational: Standard S3 SLA (99.99% availability)
  - Data loss: Versioning enabled, lifecycle policy for backups
```

**Operator Team will:**
1. Review business case
2. Validate cost estimate
3. Request human approval
4. Provision resource (if approved)
5. Document in infrastructure repo

---

## Cascade Pattern (Multi-Environment Deployment)

To deploy across all environments in sequence:

```
Deploy credentialmate version 2.1.0 across all environments:

1. Development: Auto-deploy with migrations
2. Staging: Auto-deploy with migrations (I approve first-time)
3. Production: Deploy with migrations (I will approve when ready)

Migrations path: apps/backend-api/alembic/versions
Tag: v2.1.0

Process:
- Deploy to dev first
- If dev succeeds, deploy to staging
- If staging succeeds, wait for my approval for production
- If any step fails, halt and report
```

**What happens:**
1. Deploy to dev (auto)
2. ✅ Dev succeeds
3. Deploy to staging (approval required if first-time)
4. ✅ Staging succeeds
5. **⏸️ HALT: Request approval for production**
6. (User approves)
7. Deploy to production
8. ✅ Production succeeds

---

## Work Queue Example (Full Cascade)

```json
{
  "project": "credentialmate",
  "features": [
    {
      "id": "DEPLOY-DEV-001",
      "description": "Deploy v2.1.0 to development with migrations",
      "status": "pending",
      "agent_type": "deployment",
      "environment": "development",
      "version": "2.1.0",
      "run_migrations": true,
      "migrations_path": "apps/backend-api/alembic/versions",
      "completion_promise": "DEPLOYMENT_COMPLETE",
      "max_iterations": 10
    },
    {
      "id": "DEPLOY-STAGING-001",
      "description": "Deploy v2.1.0 to staging with migrations (after dev succeeds)",
      "status": "pending",
      "agent_type": "deployment",
      "environment": "staging",
      "version": "2.1.0",
      "run_migrations": true,
      "migrations_path": "apps/backend-api/alembic/versions",
      "completion_promise": "DEPLOYMENT_COMPLETE",
      "max_iterations": 10,
      "depends_on": ["DEPLOY-DEV-001"]
    },
    {
      "id": "DEPLOY-PROD-001",
      "description": "Deploy v2.1.0 to production with migrations (after staging succeeds)",
      "status": "pending",
      "agent_type": "deployment",
      "environment": "production",
      "version": "2.1.0",
      "run_migrations": true,
      "migrations_path": "apps/backend-api/alembic/versions",
      "completion_promise": "DEPLOYMENT_COMPLETE",
      "max_iterations": 10,
      "depends_on": ["DEPLOY-STAGING-001"],
      "requires_approval": true
    }
  ]
}
```

Then:

```bash
python autonomous_loop.py --project credentialmate --max-iterations 50
```

**Autonomous loop will:**
1. Execute DEPLOY-DEV-001 (auto)
2. Wait for completion
3. Execute DEPLOY-STAGING-001 (may pause for first-time approval)
4. Wait for completion
5. **⏸️ HALT at DEPLOY-PROD-001: Request approval**
6. (User approves via R/O/A prompt)
7. Execute DEPLOY-PROD-001
8. ✅ All deployments complete

---

## Approval Prompts

### Staging (First-Time)

```
============================================================
DEPLOYMENT APPROVAL REQUIRED
============================================================
Environment: STAGING
Version: 2.1.0
Project: credentialmate
Migrations: YES (path: apps/backend-api/alembic/versions)
============================================================

Proceed with deployment? [Y/N]
```

### Production (ALWAYS)

```
============================================================
DEPLOYMENT APPROVAL REQUIRED
============================================================
Environment: PRODUCTION
Version: 2.1.0
Project: credentialmate
Migrations: YES (path: apps/backend-api/alembic/versions)
============================================================

⚠️ WARNING: Production deployment requires explicit approval
============================================================

Pre-flight validation:
✅ All tests passed
✅ Migrations validated (reversible)
✅ No SQL safety violations
✅ No S3 safety violations
✅ Build successful

Proceed with deployment? [Y/N]
```

### Rollback (Production)

```
============================================================
ROLLBACK APPROVAL REQUIRED
============================================================
Environment: PRODUCTION
Target Version: PREVIOUS
Migration Rollback: YES (downgrade -1)

⚠️ WARNING: This will restore the previous deployment
============================================================

Proceed with rollback? [Y/N]
```

---

## Troubleshooting

### Deployment Blocked (SQL Violation)

```
🚫 DEPLOYMENT SAFETY VIOLATIONS DETECTED
============================================================
🔴 CRITICAL (1):
  migration_001.py:15
    Pattern: DROP TABLE
    Reason: DROP TABLE causes irreversible data loss
    Code: DROP TABLE old_users;
============================================================
ACTION REQUIRED: Fix violations before deployment
```

**Fix:**

```python
# Instead of DROP TABLE, use a reversible migration:
def upgrade():
    # Mark table as deprecated, schedule for cleanup later
    op.execute("ALTER TABLE old_users RENAME TO _deprecated_old_users")

def downgrade():
    op.execute("ALTER TABLE _deprecated_old_users RENAME TO old_users")
```

### Migration Not Reversible

```
🚫 MIGRATION VALIDATION FAILED
============================================================
Required Elements:
  upgrade():     ✅
  downgrade():   ❌
  reversible:    ❌

❌ Errors (1):
  - Missing downgrade() function - REQUIRED for production
============================================================
🚫 Migration BLOCKED - fix errors before deployment
```

**Fix:**

```python
# Add downgrade() method
def downgrade():
    # Reverse the changes from upgrade()
    op.drop_column('users', 'email')
```

---

## Best Practices

1. **Always test in dev first** - Let auto-deploy validate the deployment
2. **Validate migrations** - Run migration validation before adding to work queue
3. **Use work queue for cascades** - Automate multi-environment deployments
4. **Review approval prompts** - Check pre-flight validation before approving
5. **Tag releases** - Use semantic versioning (v2.1.0) for tracking
6. **Document rollback plans** - Know how to rollback before deploying
7. **Monitor health checks** - Verify post-deployment metrics
8. **Use safety-exception sparingly** - Only when absolutely necessary

---

## Commands Reference

```bash
# Manual deployment (interactive)
"Deploy <project> v<version> to <environment>"

# Automated deployment (work queue)
python autonomous_loop.py --project <project> --max-iterations 50

# Validate migrations only
"Validate all migrations in <project> for <environment> environment"

# Rollback (production requires approval)
"Rollback <environment> deployment to version <version>"

# AWS provisioning
"Provision <resource> for <project> [with business case]"
```

---

## Next Steps

1. **Test in dev**: Deploy a small change to development to verify the workflow
2. **Create work queue**: Add deployment tasks to `tasks/work_queue_<project>.json`
3. **Run autonomous loop**: Let the Operator Team handle the cascade
4. **Monitor deployments**: Check `.aibrain/deployments.json` for logs

**Documentation:**
- [Operator Team Contract](../governance/contracts/operator-team.yaml)
- [SQL Safety Patterns](../ralph/guardrails/deployment_patterns.py)
- [Migration Validator](../ralph/guardrails/migration_validator.py)
- [Deployment Orchestrator](../orchestration/deployment_orchestrator.py)
