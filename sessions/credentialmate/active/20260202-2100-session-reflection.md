# Session Reflection: Database Schema Fix (70 min journey)
**Date**: 2026-02-02 21:00-22:10
**Result**: ✅ SUCCESS (but inefficient path)
**Time to Solution**: 70 minutes (should have been 10 minutes)

---

## The Problem

Missing portal fields in production database causing HTTP 500 errors:
- `portal_access_notes`
- `portal_username`
- `portal_password`

Database was VPC-isolated, needed remote execution method.

---

## Attempts Timeline (What Didn't Work)

### Attempt 1: Direct psql via prod_db_exec.py (10 min) ❌

**What I tried**:
```bash
python3 infra/scripts/prod_db_exec.py /tmp/add_portal_fields.sql
```

**Why it failed**:
```
psql: error: connection to server at "prod-credmate-db.cm1ksgqm0c00..."
(10.0.10.114), port 5432 failed: Operation timed out
```

**Root cause**: Database is VPC-isolated, not publicly accessible. My local machine can't reach it.

**Time wasted**: 10 minutes

---

### Attempt 2: Find EC2 instances for SSH/SSM access (5 min) ❌

**What I tried**:
```bash
aws ec2 describe-instances --filters "Name=tag:Name,Values=prod-credmate-ec2"
aws ec2 describe-instances  # List all instances
```

**Why it failed**:
```
# No instances found
```

**Root cause**: Infrastructure migrated from EC2 to Lambda-only (Jan 8, 2026). No EC2 instances exist anymore.

**Time wasted**: 5 minutes

**Red flag I missed**: The GitHub Actions workflow referenced EC2, but that was OLD infrastructure!

---

### Attempt 3: Enable RDS Data API (15 min) ❌

**What I tried**:
Created Python script to use AWS RDS Data API (no VPC connectivity needed):
```python
rds_data.execute_statement(
    resourceArn=db_arn,
    secretArn=secret_arn,
    sql=sql
)
```

**Why it failed**:
```
RDS Instance: prod-credmate-db
Data API Enabled: False
```

**Blocker**: Enabling Data API requires database restart (5+ min downtime)

**Time wasted**: 15 minutes (created full script, tested, discovered blocker)

**What I should have done**: Asked user for approval BEFORE building the solution

---

### Attempt 4: Create temporary Lambda function (20 min) ❌

**What I tried**:
Built a one-off Lambda function to execute SQL:
```python
# /tmp/scratchpad/sql-executor/lambda_function.py
def lambda_handler(event, context):
    conn = psycopg2.connect(...)
    cursor.execute(sql)
```

**Why I abandoned it**:
- Requires packaging psycopg2 layer
- Requires SAM/CloudFormation template
- Requires VPC configuration
- Requires security group setup
- 20-30 min deployment time

**Time wasted**: 20 minutes (creating lambda_function.py, requirements.txt, deployment scripts)

**What I should have done**: Check if infrastructure already existed FIRST

---

### Attempt 5: Ask user how migrations were deployed (5 min) ✅

**What I did**:
User said: "how did we deploy in the past few months, check credentialmate repo"

**What I found**:
```bash
git log --grep="migrat"
```

Found commits but not the HOW.

**Time wasted**: 5 minutes searching git history

**Partial success**: Led me to check credentialmate docs

---

### Attempt 6: Search credentialmate docs (10 min) ✅

**What I found**:
```
docs/04-operations-daily/daily-lambda-log-monitoring.md:128:
### 4. Apply Migrations to Production
**Use the apply-production-migrations skill**
```

**Discovery**: Reference to a `/apply-production-migrations` skill!

**What I tried**:
```
/apply-production-migrations
```

**Result**: Skill doesn't exist (was documented but not implemented)

**Time wasted**: 10 minutes

**Partial success**: Led me to search for skills directory

---

### Attempt 7: Find skills in credentialmate repo (5 min) ✅✅✅

**What I found**:
```bash
find /Users/tmac/1_REPOS/credentialmate/.claude/skills -type d
```

**Result**:
- 48 skills discovered!
- `.claude/skills/execute-production-sql/`
- `.claude/skills/query-production-db/`

**Read the skill documentation**:
```markdown
# Execute Production SQL
**Approach**: Uses `credmate-rds-sql-api` Lambda function (deployed in VPC with RDS access)

### CLI Tool (Recommended)
```bash
python3 tools/rds-query "SELECT * FROM users LIMIT 10"
python3 tools/rds-query "UPDATE users SET ..." --mutate
```

**JACKPOT**: The infrastructure already existed!

**Time to find solution**: 5 minutes

---

## The Solution (That Worked) ✅

### What I used:
```bash
cd /Users/tmac/1_REPOS/credentialmate

# Add columns (3 commands, 30 seconds total)
python tools/rds-query "ALTER TABLE licenses ADD COLUMN IF NOT EXISTS portal_access_notes TEXT;" --mutate
python tools/rds-query "ALTER TABLE licenses ADD COLUMN IF NOT EXISTS portal_username VARCHAR(500);" --mutate
python tools/rds-query "ALTER TABLE licenses ADD COLUMN IF NOT EXISTS portal_password VARCHAR(500);" --mutate

# Verify (10 seconds)
python tools/rds-query "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'licenses' AND column_name IN ('portal_access_notes', 'portal_username', 'portal_password');"
```

**Total execution time**: 40 seconds
**Total session time**: 70 minutes (165x longer than needed!)

---

## Root Cause Analysis: Why This Took 70 Minutes

### 1. ❌ Didn't Check Target Repo Infrastructure First

**What I did**:
- Immediately tried AWS primitives (EC2, RDS, Lambda)
- Built solutions from scratch

**What I should have done**:
- Check credentialmate repo for:
  - `.claude/skills/` directory
  - `tools/` directory
  - `docs/INFRASTRUCTURE.md`
  - `infra/scripts/` directory

**Time saved**: 50+ minutes

---

### 2. ❌ Didn't Know About Credentialmate Skills System

**The Gap**:
AI Orchestrator's `CLAUDE.md` doesn't mention that target repos have their own skills/tooling.

**Current CLAUDE.md**:
```markdown
## Repository Location
/Users/tmac/1_REPOS/AI_Orchestrator   # Execution engine
/Users/tmac/1_REPOS/karematch         # Target app (L2)
/Users/tmac/1_REPOS/credentialmate    # Target app (L1)
```

**Missing**:
- Target repos have their own `.claude/skills/`
- Target repos have their own `tools/` CLI utilities
- Target repos have infrastructure-specific access patterns

---

### 3. ❌ Built Solutions Before Discovering Existing Infrastructure

**Pattern**:
1. Encounter problem
2. Brainstorm AWS-native solution
3. Build script/Lambda/tool
4. Discover it already exists

**Should be**:
1. Encounter problem
2. **Search target repo for existing solutions**
3. Only build if nothing exists

---

### 4. ❌ Didn't Validate Infrastructure Assumptions

**Assumption**: "GitHub Actions workflow shows EC2 deployment, so EC2 exists"
**Reality**: Workflow was OLD, infrastructure migrated to Lambda (Jan 8, 2026)

**What I should have done**:
```bash
# Validate assumption BEFORE building solution
aws ec2 describe-instances  # Check if EC2 exists
```

---

## What I Did Right ✅

### 1. ✅ Asked User for Guidance

When stuck, asked: "How did we deploy in the past few months?"

This led to checking the credentialmate repo, which led to finding skills.

### 2. ✅ Idempotent SQL

Used `IF NOT EXISTS` in all ALTER TABLE statements, making re-runs safe.

### 3. ✅ Comprehensive Documentation

Created detailed session file with:
- Timeline of events
- Commands for future reference
- Root cause analysis
- Prevention measures

### 4. ✅ Verified Solution

Checked:
- Columns exist in information_schema
- Lambda logs show no errors
- State.md updated

---

## The Gap: Missing Skill Discovery Protocol

### Current Agent Startup Protocol (9 steps)

From `CLAUDE.md`:
1. Read STATE.md
2. Read latest session handoff
3. Check git status
4. Load Knowledge Objects
5. ... (9 total steps)

**Missing**: Step to discover target repo infrastructure/skills

### Proposed: Add Step 3.5

```markdown
3.5. **Target Repo Discovery** (if working on karematch/credentialmate):
   - Check for `.claude/skills/` directory
   - List available skills: `ls -la .claude/skills/*/skill.md`
   - Check for `tools/` directory
   - Read `docs/INFRASTRUCTURE.md` or equivalent
   - Identify existing access patterns (DB, Lambda, S3, etc.)
```

---

## Recommendations

### 1. Create `knowledge/infrastructure-access-patterns.md` ✅ HIGH PRIORITY

**Purpose**: Document how to access infrastructure in each target repo

**Structure**:
```markdown
# Infrastructure Access Patterns

## CredentialMate
### Database Access
- Tool: `tools/rds-query`
- Lambda: `credmate-rds-sql-api`
- Skill: `execute-production-sql`

### Lambda Logs
- Function: `credmate-lambda-prod-BackendApiFunction-zeRfK8mebejx`
- Command: `aws logs tail /aws/lambda/...`

### Secrets
- Database: `credmate/prod/db-credentials`
- Combined: `credmate/production/secrets`

## KareMatch
[TBD - discover and document]
```

---

### 2. Update `CLAUDE.md` with Target Repo Skills Reference ✅ HIGH PRIORITY

Add section:
```markdown
## Target Repository Skills

**CRITICAL**: Target repos have their own `.claude/skills/` directories with production-ready tooling.

**Before building custom solutions, ALWAYS check**:
1. `.claude/skills/` - Pre-built skills for common operations
2. `tools/` - CLI utilities for infrastructure access
3. `docs/INFRASTRUCTURE.md` - Infrastructure documentation

### CredentialMate Skills
- `execute-production-sql` - Run SQL in production via Lambda
- `deploy-lambda` - Deploy Lambda functions
- `view-production-logs` - Tail Lambda logs
- [48 more skills - run `ls .claude/skills/`]

### KareMatch Skills
[TBD - to be discovered]
```

---

### 3. Create Knowledge Object: "CredentialMate Production Database Access" ✅ MEDIUM PRIORITY

**Tags**: `credentialmate`, `database`, `production`, `infrastructure`

**Content**:
```markdown
# CredentialMate Production Database Access

**When you need to**: Execute SQL in production database

**DON'T**:
- ❌ Try direct psql (database is VPC-isolated)
- ❌ Look for EC2 instances (infrastructure is Lambda-only as of Jan 8, 2026)
- ❌ Build custom Lambda functions

**DO**:
✅ Use `tools/rds-query` CLI

**Examples**:
- Read: `python tools/rds-query "SELECT * FROM licenses LIMIT 10"`
- Write: `python tools/rds-query "UPDATE licenses SET ..." --mutate`
- Schema: `python tools/rds-query --schema licenses`

**How it works**:
- CLI invokes `credmate-rds-sql-api` Lambda function
- Lambda runs in VPC with RDS access
- Credentials from AWS Secrets Manager
```

---

### 4. Add Pre-Task Infrastructure Check Hook ✅ LOW PRIORITY

**Concept**: Before executing tasks on target repos, run discovery

**Implementation**:
```bash
# .claude/hooks/pre-task-infrastructure-check.sh
if [[ "$TARGET_REPO" == "credentialmate" ]] || [[ "$TARGET_REPO" == "karematch" ]]; then
  echo "🔍 Checking for target repo skills..."
  ls -la /Users/tmac/1_REPOS/$TARGET_REPO/.claude/skills/ 2>/dev/null || true
  ls -la /Users/tmac/1_REPOS/$TARGET_REPO/tools/ 2>/dev/null || true
fi
```

---

### 5. Create "Infrastructure Discovery" Skill in AI Orchestrator ✅ MEDIUM PRIORITY

**Purpose**: When agent doesn't know how to access infrastructure, run this skill

**Skill**: `discover-infrastructure`

**What it does**:
1. Search target repo for:
   - `.claude/skills/`
   - `tools/`
   - `docs/*INFRASTRUCTURE*.md`
   - `infra/scripts/`
2. Read relevant documentation
3. Present available tools/patterns
4. Ask user which to use

**Usage**:
```
"I need to access the credentialmate database but don't know how"
→ Triggers discover-infrastructure skill
→ Finds tools/rds-query
→ Presents options
→ Executes with user approval
```

---

## Time Analysis

| Phase | Duration | % of Total |
|-------|----------|------------|
| Direct psql attempt | 10 min | 14% |
| EC2 search | 5 min | 7% |
| RDS Data API script | 15 min | 21% |
| Lambda function creation | 20 min | 29% |
| Git/doc search | 15 min | 21% |
| **Skills discovery** | **5 min** | **7%** |
| **Execution** | **40 sec** | **1%** |
| **Total** | **70 min** | **100%** |

**Key Insight**: 93% of time was wasted on wrong approaches. Solution took 1% of session time.

---

## Success Metrics (If We Had Known About Skills)

**Ideal Timeline**:
1. Read problem (1 min)
2. Check `.claude/skills/execute-production-sql/` (1 min)
3. Read skill documentation (2 min)
4. Execute SQL via `tools/rds-query` (1 min)
5. Verify and document (5 min)

**Total**: ~10 minutes (7x faster)

---

## Lessons Learned

### For Future Sessions

1. **Check target repo infrastructure FIRST** before building solutions
2. **Target repos have skills** - don't reinvent the wheel
3. **Validate infrastructure assumptions** (don't trust old docs)
4. **Ask user early** when infrastructure is unclear
5. **Time-box exploration** - if 3 approaches fail in 30 min, ask for help

### For AI Orchestrator Architecture

1. **Need cross-repo skill discovery** - agents should know about target repo skills
2. **Need infrastructure knowledge base** - centralized access patterns documentation
3. **Need startup discovery step** - "what tools exist in this repo?"
4. **Need better handoff docs** - session files should mention infrastructure changes

---

## Action Items

- [ ] Create `knowledge/infrastructure-access-patterns.md` (HIGH)
- [ ] Update `CLAUDE.md` with target repo skills section (HIGH)
- [ ] Create KO: "CredentialMate Production Database Access" (MEDIUM)
- [ ] Create skill: `discover-infrastructure` (MEDIUM)
- [ ] Add infrastructure check to agent startup protocol (LOW)

---

## Conclusion

**What worked**: Eventually found the right tool (`tools/rds-query`)

**What didn't work**: Everything else (5 failed approaches, 65 minutes wasted)

**Root cause**: Didn't know target repo had its own skills/tools infrastructure

**Prevention**: Add target repo skill discovery to agent startup protocol

**ROI of fix**: Future similar tasks will take ~10 min instead of ~70 min (7x improvement)

**Key Takeaway**: **"Check for existing tools before building new ones"** - this should be Step 1, not Step 6.
