# Operator Team Quick Start

## Copy-Paste Prompts to Test Operator Team

### 1. Simple Development Deployment (Auto-Deploy)

```
Deploy karematch version 1.2.3 to development environment.

Verify:
- Run pre-deployment tests
- Build application
- Deploy to dev
- Run health checks
- Report success
```

**Expected behavior:**
- ✅ Auto-deploys (no approval needed)
- ✅ Auto-rolls back on failure
- ✅ Reports deployment status

---

### 2. Staging Deployment with Migrations (First-Time Approval)

```
Deploy credentialmate version 2.0.0 to staging environment with database migrations.

Configuration:
- Migrations path: apps/backend-api/alembic/versions
- Run migrations after deployment
- Validate migrations for reversibility

I understand this requires first-time approval for staging.
```

**Expected behavior:**
- ⏸️ Asks for approval (first-time only)
- ✅ Validates migrations (must have downgrade())
- ✅ Runs SQL safety checks
- ✅ Deploys after approval
- ✅ Auto-rolls back on failure

---

### 3. Production Deployment (ALWAYS Requires Approval)

```
Deploy credentialmate version 2.1.0 to PRODUCTION environment.

Configuration:
- Version tag: v2.1.0
- Run database migrations: YES
- Migrations path: apps/backend-api/alembic/versions
- Post-deployment health checks: REQUIRED

Pre-flight requirements:
- All tests must pass
- Migrations must be reversible (downgrade() required)
- No SQL safety violations (DROP TABLE, TRUNCATE, etc.)
- No S3 safety violations (bucket deletion, etc.)

I understand this ALWAYS requires my explicit approval.
```

**Expected behavior:**
- 🔍 Runs full pre-flight validation
- 🔍 Scans for SQL safety violations
- 🔍 Scans for S3 safety violations
- 🔍 Validates migration reversibility
- ⏸️ Halts and requests approval
- ✅ Deploys only after approval
- ⚠️ NO auto-rollback (manual only)

---

### 4. Cascade Deployment (Dev → Staging → Prod)

```
Deploy credentialmate version 2.1.0 across all environments in sequence.

Deployment sequence:
1. Development: Auto-deploy with migrations
2. Staging: Deploy with migrations (I approve if first-time)
3. Production: Deploy with migrations (I will approve when ready)

Configuration:
- Migrations path: apps/backend-api/alembic/versions
- Version tag: v2.1.0
- Stop on any failure
- Auto-rollback for dev/staging only

Process:
- Deploy to dev first (auto)
- If dev succeeds, deploy to staging
- If staging succeeds, pause and request approval for production
- If production approved, deploy
- Report final status
```

**Expected behavior:**
1. Deploys to dev (auto)
2. ✅ Dev succeeds
3. Deploys to staging (may ask for approval)
4. ✅ Staging succeeds
5. ⏸️ HALTS before production
6. Requests approval
7. (User approves)
8. Deploys to production
9. ✅ Production succeeds
10. Reports full cascade status

---

### 5. Migration Validation Only (No Deployment)

```
Validate all Alembic migrations in credentialmate for production environment.

Validation checks:
- Verify all migrations have upgrade() and downgrade() methods
- Check for SQL safety violations (DROP TABLE, TRUNCATE, DELETE without WHERE)
- Verify migration reversibility
- Report any violations found

Migrations path: apps/backend-api/alembic/versions
Environment: production (strict validation)
```

**Expected behavior:**
- 🔍 Scans all migrations in directory
- 🔍 Checks for downgrade() methods
- 🔍 Detects SQL safety violations
- 📊 Reports validation results
- ❌ Does NOT execute migrations (validation only)

---

### 6. Rollback Production Deployment (Manual Approval)

```
Rollback credentialmate production deployment to version 2.0.5.

Rollback configuration:
- Environment: production
- Target version: 2.0.5
- Rollback migrations: YES (downgrade to matching revision)

I understand production rollback requires my explicit approval.
```

**Expected behavior:**
- ⏸️ Requests approval (ALWAYS for production)
- ✅ Rolls back application to v2.0.5
- ✅ Runs migration downgrade (if configured)
- ✅ Verifies rollback health
- 📊 Reports rollback status

---

## Testing the Operator Team (Recommended Flow)

### Step 1: Test in Development (Safe)

```
Deploy karematch version 1.0.0-test to development environment for testing the Operator Team workflow.

This is a test deployment to verify:
- Pre-deployment validation works
- Build process executes
- Health checks run
- Auto-deploy functions correctly

Report the full deployment workflow and any issues encountered.
```

### Step 2: Test Migration Validation

```
Validate all Alembic migrations in credentialmate for production environment.

Report:
- How many migrations were found
- How many have downgrade() methods
- Any SQL safety violations detected
- Overall validation status
```

### Step 3: Test SQL Safety Scanner

Create a test migration with violations:

```
Create a test migration file to verify SQL safety scanner works.

Test migration content:
- Include DROP TABLE statement (should be BLOCKED)
- Include DELETE without WHERE (should be BLOCKED)
- Include TRUNCATE TABLE (should be BLOCKED)

Then validate this migration and confirm violations are detected.
```

---

## Work Queue Example (Automated Cascade)

Create `tasks/work_queue_test.json`:

```json
{
  "project": "karematch",
  "features": [
    {
      "id": "DEPLOY-DEV-TEST-001",
      "description": "Deploy v1.0.0-test to development",
      "status": "pending",
      "agent_type": "deployment",
      "environment": "development",
      "version": "1.0.0-test",
      "run_migrations": false,
      "completion_promise": "DEPLOYMENT_COMPLETE",
      "max_iterations": 10
    }
  ]
}
```

Then run:

```bash
python autonomous_loop.py --project test --max-iterations 20
```

---

## Approval Response Examples

### When Operator Team Asks for Approval

```
============================================================
DEPLOYMENT APPROVAL REQUIRED
============================================================
Environment: STAGING
Version: 2.1.0
Project: credentialmate
Migrations: YES
============================================================

Proceed with deployment? [Y/N]
```

**Your responses:**

✅ **Approve**: `Y` or `Yes` or `Approved` or `Proceed`

❌ **Reject**: `N` or `No` or `Reject` or `Cancel`

⏸️ **Pause**: `Wait` or `Hold` or `Not yet`

---

## Safety Violation Examples

### SQL Violation (DROP TABLE)

If Operator Team detects:

```
🚫 DEPLOYMENT SAFETY VIOLATIONS DETECTED
============================================================
🔴 CRITICAL (1):
  migration_001.py:15
    Pattern: DROP TABLE
    Reason: DROP TABLE causes irreversible data loss
    Code: DROP TABLE old_users;
============================================================
```

**Your response:**

```
Fix the migration to be reversible instead:

Replace DROP TABLE with:
1. Rename table to _deprecated_old_users
2. Add downgrade() to restore original name

Then re-validate the migration.
```

### Missing Downgrade Method

If Operator Team detects:

```
🚫 MIGRATION VALIDATION FAILED
============================================================
❌ Errors (1):
  - Missing downgrade() function - REQUIRED for production
============================================================
```

**Your response:**

```
Add a downgrade() method to the migration that reverses the changes in upgrade().

Show me the migration file so I can review what downgrade() should do.
```

---

## Next Actions

1. **Read**: [Full Usage Guide](./OPERATOR_TEAM_USAGE.md)
2. **Test**: Copy one of the quick-start prompts above
3. **Monitor**: Check `.aibrain/deployments.json` for logs
4. **Automate**: Create work queue for multi-environment cascades

**Files to check:**
- `.aibrain/deployments.json` - Deployment logs
- `governance/contracts/operator-team.yaml` - Full governance rules
- `ralph/guardrails/deployment_patterns.py` - SQL/S3 safety patterns
