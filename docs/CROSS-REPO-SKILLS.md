# Cross-Repo Skills and Infrastructure Access

**Purpose**: Prevent agents from reinventing solutions that already exist in target repos

**Last Updated**: 2026-02-02

---

## Target Repository Infrastructure

### CredentialMate (`/Users/tmac/1_REPOS/credentialmate`)

**Skills**: 48 skills in `.claude/skills/`

**Key Skills**:
- `execute-production-sql` - Run SQL in production via Lambda
- `query-production-db` - Read-only queries
- `deploy-lambda` - Deploy Lambda functions
- `view-production-logs` - Tail Lambda CloudWatch logs
- `verify-golden-path` - End-to-end testing
- `rollback-lambda` - Emergency rollback

**CLI Tools** (`tools/`):
- `rds-query` - Execute SQL via `credmate-rds-sql-api` Lambda (VPC access)

**Infrastructure Access Patterns**:

| Resource | Access Method | Example |
|----------|---------------|---------|
| **Production Database** | `tools/rds-query` | `python tools/rds-query "SELECT * FROM users" --mutate` |
| **Lambda Logs** | AWS CLI | `aws logs tail /aws/lambda/credmate-lambda-prod-BackendApiFunction-zeRfK8mebejx` |
| **Secrets** | Secrets Manager | `credmate/prod/db-credentials`, `credmate/production/secrets` |
| **Deployments** | SAM CLI | `cd infra/lambda && sam build && sam deploy` |

**Key Infrastructure IDs**:
- Lambda API: `credmate-lambda-prod-BackendApiFunction-zeRfK8mebejx`
- Lambda SQL: `credmate-rds-sql-api`
- RDS Instance: `prod-credmate-db`
- CloudFront: `E3C4D2B3O2P8FS`

**Infrastructure Notes**:
- ✅ Lambda-only (as of Jan 8, 2026)
- ❌ NO EC2 instances
- ❌ RDS Data API NOT enabled (would require restart)
- ✅ Database VPC-isolated (use Lambda SQL API)

---

### KareMatch (`/Users/tmac/1_REPOS/karematch`)

**Status**: TBD - to be documented

---

## Agent Protocol: Infrastructure Discovery

**CRITICAL**: Before building custom solutions, ALWAYS check target repo first.

### Pre-Task Checklist

When working on credentialmate or karematch:

1. **Check for skills**:
   ```bash
   ls -la .claude/skills/
   grep -r "your_task_keyword" .claude/skills/*/skill.md
   ```

2. **Check for CLI tools**:
   ```bash
   ls -la tools/
   cat tools/README.md  # if exists
   ```

3. **Read infrastructure docs**:
   ```bash
   cat docs/INFRASTRUCTURE.md
   cat infra/README.md
   ```

4. **Check recent sessions**:
   ```bash
   ls -lt sessions/credentialmate/active/*.md | head -5
   grep -r "similar_problem" sessions/
   ```

### Decision Tree

```
Need to access infrastructure?
  ├─ Check .claude/skills/ for existing skill → Use it
  ├─ Check tools/ for CLI utility → Use it
  ├─ Check docs/INFRASTRUCTURE.md → Follow documented pattern
  └─ Nothing found? → Ask user OR build custom solution
```

---

## Common Mistakes to Avoid

### ❌ Don't Do This

1. **Build Lambda function** when `credmate-rds-sql-api` already exists
2. **Try direct psql** when database is VPC-isolated
3. **Look for EC2** when infrastructure is Lambda-only
4. **Enable RDS Data API** when `tools/rds-query` already works
5. **Trust old workflow files** - infrastructure changes over time

### ✅ Do This Instead

1. **Search for existing tools** first
2. **Read target repo's INFRASTRUCTURE.md**
3. **Check .claude/skills/** for pre-built solutions
4. **Validate infrastructure assumptions** with `aws` commands
5. **Ask user** how they currently access infrastructure

---

## Examples from Real Sessions

### Session: 2026-02-02 Portal Fields Database Fix

**Problem**: Need to add columns to production database

**Wrong approaches tried** (65 minutes wasted):
- Direct psql (VPC blocked)
- EC2 SSH (no instances)
- RDS Data API (not enabled)
- Custom Lambda (unnecessary)

**Right approach** (40 seconds):
```bash
python tools/rds-query "ALTER TABLE licenses ADD COLUMN ..." --mutate
```

**Lesson**: Check `tools/` directory before building custom solutions

---

## Integration with AI Orchestrator

### Updated Agent Startup Protocol

Add after Step 3 in startup protocol:

**Step 3.5: Target Repo Infrastructure Discovery**

If working on karematch or credentialmate:
```bash
# Quick discovery
ls .claude/skills/
ls tools/
cat docs/INFRASTRUCTURE.md

# Targeted search
grep -r "database\|lambda\|deployment" .claude/skills/*/skill.md
```

### Knowledge Objects to Create

1. **CredentialMate Database Access** (HIGH PRIORITY)
   - Tags: `credentialmate`, `database`, `production`
   - Content: Use `tools/rds-query`, NOT direct psql

2. **CredentialMate Lambda Deployment** (MEDIUM)
   - Tags: `credentialmate`, `lambda`, `deployment`
   - Content: Use `sam build && sam deploy`, sync code first

3. **Infrastructure Migration Timeline** (LOW)
   - Tags: `credentialmate`, `infrastructure`, `history`
   - Content: EC2 → Lambda (Jan 8, 2026), what changed

---

## Quick Reference

### CredentialMate Production Operations

```bash
# Database queries (read-only)
python tools/rds-query "SELECT * FROM table"

# Database mutations (INSERT/UPDATE/DELETE/ALTER)
python tools/rds-query "UPDATE table SET ..." --mutate

# View Lambda logs
aws logs tail /aws/lambda/credmate-lambda-prod-BackendApiFunction-zeRfK8mebejx --since 1h

# Deploy Lambda
cd infra/lambda
python functions/backend/copy_backend.py  # Sync code first!
sam build --use-container
sam deploy --stack-name credmate-lambda-prod

# Check health
curl https://api.credentialmate.com/health
```

---

## Maintenance

**When to update this document**:
- New skills added to target repos
- Infrastructure changes (new services, migrations)
- Access patterns change (new tools, deprecated methods)
- Session reveals missing documentation

**Review schedule**: Monthly or after major infrastructure changes

---

**Created**: 2026-02-02
**Contributors**: Claude Code Agent
**Related**: `sessions/credentialmate/active/20260202-2100-session-reflection.md`
