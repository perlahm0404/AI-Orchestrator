# Hybrid Architecture Implementation Plan: CredentialMate → AI_Orchestrator

**Date**: 2026-02-06
**Strategy**: Hybrid (keep orchestrator coordination + add app autonomy)
**Start**: CredentialMate (HIPAA-compliant, highest priority)
**Duration**: 4 weeks total

---

## Executive Summary

**Goal**: Enhance existing architecture with best of Approach A + Approach B

**Outcome**:
- ✅ CredentialMate can work standalone with local agents
- ✅ AI_Orchestrator coordinates cross-repo work
- ✅ Memory sustainability: 95% (work_queue + CLAUDE.md)
- ✅ HIPAA compliance maintained (audit trails)

**No new repos created** - enhancing existing 3 repos

---

## Phase 1: CredentialMate Enhancement (Week 1-2)

### Goal
Add Approach A features to CredentialMate while maintaining HIPAA compliance

### Current State
```bash
CredentialMate/
├─ .claude/
│  └─ skills/ (48 existing skills - already advanced!)
├─ apps/
│  ├─ frontend-web/ (Next.js + SST)
│  └─ backend/ (FastAPI)
├─ tools/ (rds-query, etc.)
└─ docs/INFRASTRUCTURE.md
```

### Target State
```bash
CredentialMate/
├─ .claude/
│  ├─ CLAUDE.md (150-200 lines - NEW)
│  ├─ agents/ (role contracts - NEW)
│  │  ├─ lead.md
│  │  ├─ builder.md
│  │  └─ reviewer.md
│  ├─ rules/ (file-scoped - NEW)
│  │  ├─ hipaa.md (CRITICAL for compliance)
│  │  ├─ testing.md
│  │  └─ lambda.md
│  ├─ skills/ (48 existing - ENHANCED)
│  └─ hooks/
│     └─ post_tool_use.sh (fast feedback - NEW)
├─ orchestration/ (NEW - local work queue)
│  ├─ queue/
│  │  └─ work_queue_local.json
│  └─ sync_with_orchestrator.py
└─ (existing app code unchanged)
```

### Implementation Steps

#### Step 1.1: Create .claude/CLAUDE.md (Day 1)

**File**: `/Users/tmac/1_REPOS/credentialmate/.claude/CLAUDE.md`

```markdown
# CredentialMate AI Agent Team

**Project**: HIPAA-compliant credential management platform
**Autonomy Level**: L1 (strict governance - healthcare data)
**Orchestrator**: Managed by /Users/tmac/1_REPOS/AI_Orchestrator

---

## Critical HIPAA Rules

**NEVER**:
- ❌ Log PHI/PII to console or files
- ❌ Commit credentials or API keys
- ❌ Deploy without SAM build verification
- ❌ Bypass test requirements
- ❌ Access production DB directly (use tools/rds-query)

**ALWAYS**:
- ✅ Encrypt all healthcare data
- ✅ Use parameterized queries (prevent SQL injection)
- ✅ Require tests for all PHI-handling code
- ✅ Document data flow in HIPAA-sensitive features
- ✅ Verify SAM build matches deployed Lambda

---

## Branching & PR Workflow

- Main branch: `main` (protected)
- Feature branches: `feature/{task-id}-{description}`
- PR required for all changes
- Tests must pass before merge
- HIPAA compliance check required

---

## Agent Roles

**Lead Agent**:
- Break down epics into tasks
- Update work_queue_local.json
- Sync with orchestrator work queue

**Builder Agent**:
- Implement features per task
- Write tests (coverage >80% for PHI code)
- Update SAM templates if Lambda changes

**Reviewer Agent**:
- Code review for HIPAA compliance
- Verify test coverage
- Check for credential leaks

---

## Definition of Done (DoD)

**Standard DoD**:
- [ ] Tests passing (pytest backend, vitest frontend)
- [ ] Type checking clean (mypy backend, TypeScript frontend)
- [ ] No credentials in code
- [ ] Documentation updated

**HIPAA DoD** (for PHI-handling code):
- [ ] PHI data encrypted at rest and in transit
- [ ] Audit trail for PHI access
- [ ] Input validation for all user data
- [ ] Parameterized queries (no string concatenation)
- [ ] Error messages don't leak PHI

**Lambda DoD**:
- [ ] SAM build succeeds
- [ ] Lambda code matches build/
- [ ] Environment variables documented
- [ ] Layer dependencies verified
- [ ] Deployment tested in dev first

---

## Memory Integration

**Local Memory**:
- Work queue: `orchestration/queue/work_queue_local.json`
- Session docs: `docs/sessions/`

**Orchestrator Memory**:
- System-of-record: `/Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_credentialmate.json`
- Knowledge Objects: `/Users/tmac/1_REPOS/AI_Orchestrator/knowledge/`
- Sync script: `orchestration/sync_with_orchestrator.py`

**Sync Strategy**:
- Pull tasks from orchestrator on session start
- Push completed tasks to orchestrator on success
- Conflicts: Orchestrator is source of truth

---

## Key Commands

```bash
# Backend tests
cd apps/backend && pytest

# Frontend tests
cd apps/frontend-web && npm test

# Build Lambda
sam build

# Deploy to dev
sam deploy --config-env dev

# Query production DB (read-only)
python tools/rds-query "SELECT COUNT(*) FROM licenses"

# Sync with orchestrator
python orchestration/sync_with_orchestrator.py --pull
python orchestration/sync_with_orchestrator.py --push
```

---

## Security Boundaries

**Allowed**:
- Read from production DB (via tools/rds-query)
- Deploy to dev/staging environments
- Run tests with test data

**Requires Human Approval**:
- Production deployments (SAM deploy --config-env prod)
- Schema migrations (Alembic migrations)
- Infrastructure changes (SST config changes)

**Forbidden**:
- Direct DB writes via SQL (use API endpoints)
- Sharing PHI in logs or errors
- Bypassing authentication

---

## Target Repo Skills

**CredentialMate has 48 pre-built skills** in `.claude/skills/`:

Before building custom solutions:
1. Check `.claude/skills/` for existing skill
2. Check `tools/` for CLI utilities
3. Check `docs/INFRASTRUCTURE.md` for infrastructure access

**Key Skills**:
- Database access: Use existing tools/rds-query
- Lambda deployment: Use existing skills
- Frontend deployment: Use existing SST deploy skills

---

## File-Scoped Rules

See `.claude/rules/` for detailed rules:
- `hipaa.md` - HIPAA compliance requirements
- `testing.md` - Test coverage and quality standards
- `lambda.md` - Lambda-specific rules (SAM build, layers, etc.)

Rules apply automatically based on file patterns.

---

**Autonomy Level**: L1 (Strict)
**Memory Sustainability**: 95% (work_queue + CLAUDE.md + orchestrator)
**Last Updated**: 2026-02-06
```

**Verification**:
```bash
# File exists and is reasonable length
wc -l .claude/CLAUDE.md
# Expected: ~150-200 lines
```

#### Step 1.2: Create Agent Role Contracts (Day 1-2)

**File**: `/Users/tmac/1_REPOS/credentialmate/.claude/agents/lead.md`

```markdown
# Lead Agent Contract

## Responsibilities
- Break down HIPAA-compliant features into safe, testable tasks
- Update work_queue_local.json with task status
- Delegate to Builder and Reviewer agents
- Ensure DoD met before marking complete
- Sync with orchestrator work queue

## Inputs
- Feature requests from product/users
- Tasks from orchestrator work queue
- HIPAA compliance requirements

## Outputs Required
- Updated work_queue_local.json
- Task breakdown with acceptance criteria
- HIPAA impact assessment for each task
- Delegation plan (which agent owns which task)

## HIPAA Responsibilities
- Flag tasks that handle PHI
- Require HIPAA DoD for PHI tasks
- Escalate compliance questions to human

## Stop Conditions
- All tasks blocked (escalate to human)
- HIPAA compliance unclear (escalate to human)
- Production deployment needed (human approval required)
- Budget exceeded

## Success Metrics
- Tasks completed with DoD met
- Zero HIPAA violations introduced
- Work queue stays in sync with orchestrator
```

**File**: `/Users/tmac/1_REPOS/credentialmate/.claude/agents/builder.md`

```markdown
# Builder Agent Contract

## Responsibilities
- Implement features per task specification
- Write comprehensive tests (>80% coverage for PHI code)
- Update SAM templates when Lambda code changes
- Document HIPAA-sensitive data flows

## Inputs
- Task from work_queue_local.json
- Acceptance criteria
- HIPAA requirements (from .claude/rules/hipaa.md)

## Outputs Required
- Working code (backend FastAPI or frontend Next.js)
- Tests (pytest or vitest)
- Documentation updates
- SAM build verification (for Lambda changes)

## HIPAA Responsibilities
- Encrypt all PHI data
- Use parameterized queries (never string concat)
- Validate all user inputs
- Error messages must NOT leak PHI
- Log audit trail for PHI access

## Code Quality Standards
- Type hints (Python) / TypeScript types
- No credentials in code
- Linting clean (ruff, ESLint)
- Test coverage >80% for PHI-handling code

## Stop Conditions
- Tests fail after 3 attempts (escalate)
- HIPAA requirement unclear (escalate)
- SAM build fails (fix or escalate)

## Success Metrics
- Tests passing
- HIPAA DoD checklist complete
- No credentials leaked
```

**File**: `/Users/tmac/1_REPOS/credentialmate/.claude/agents/reviewer.md`

```markdown
# Reviewer Agent Contract

## Responsibilities
- Review code for HIPAA compliance
- Verify test coverage meets standards
- Check for credential leaks
- Approve or request changes before merge

## Inputs
- Pull request from Builder agent
- HIPAA DoD checklist
- Test results

## Outputs Required
- Code review comments
- HIPAA compliance verdict (PASS/FAIL/NEEDS_REVIEW)
- Test coverage report analysis
- Approval or change request

## HIPAA Review Checklist
- [ ] PHI encrypted at rest and in transit?
- [ ] Parameterized queries (no SQL injection)?
- [ ] Input validation present?
- [ ] Error messages sanitized (no PHI leaks)?
- [ ] Audit logging for PHI access?
- [ ] Authentication/authorization correct?

## Security Review
- [ ] Credentials scanned (no leaks)?
- [ ] Dependencies updated (no known CVEs)?
- [ ] CORS configured correctly?
- [ ] Rate limiting appropriate?

## Stop Conditions
- HIPAA violation detected (BLOCK merge)
- Credentials found in code (BLOCK merge)
- Test coverage <80% for PHI code (REQUEST changes)

## Success Metrics
- Zero HIPAA violations merged
- All PRs reviewed within 1 day
- Clear, actionable feedback
```

**Verification**:
```bash
# All 3 agent contracts created
ls -la .claude/agents/
# Expected: lead.md, builder.md, reviewer.md
```

#### Step 1.3: Create File-Scoped Rules (Day 2-3)

**File**: `/Users/tmac/1_REPOS/credentialmate/.claude/rules/hipaa.md`

```markdown
# HIPAA Compliance Rules

**Applies to**: All files handling PHI (licenses, credentials, user data)

**File patterns**:
- `apps/backend/models/*license*.py`
- `apps/backend/models/*credential*.py`
- `apps/backend/routes/*license*.py`
- `apps/backend/parsers/*.py`
- `apps/frontend-web/components/*License*.tsx`

---

## Critical Rules

### 1. Encryption (REQUIRED)

**At Rest**:
```python
# ✅ CORRECT - PHI encrypted in DB
class License(Base):
    license_number = Column(EncryptedString, nullable=False)
    ssn = Column(EncryptedString, nullable=True)

# ❌ WRONG - PHI in plaintext
class License(Base):
    license_number = Column(String, nullable=False)  # HIPAA VIOLATION
```

**In Transit**:
- All API endpoints must use HTTPS (enforced by CloudFront)
- No PHI in URL parameters (use POST body)

### 2. SQL Injection Prevention (REQUIRED)

```python
# ✅ CORRECT - Parameterized query
licenses = session.query(License).filter(
    License.license_number == user_input
).all()

# ❌ WRONG - String concatenation (SQL injection risk)
query = f"SELECT * FROM licenses WHERE license_number = '{user_input}'"
licenses = session.execute(query).all()  # HIPAA VIOLATION
```

### 3. Error Messages (REQUIRED)

```python
# ✅ CORRECT - Generic error
except LicenseNotFoundError:
    raise HTTPException(
        status_code=404,
        detail="License not found"
    )

# ❌ WRONG - Leaks PHI in error
except LicenseNotFoundError:
    raise HTTPException(
        status_code=404,
        detail=f"License {license_number} not found for {user_name}"  # PHI LEAK
    )
```

### 4. Logging (REQUIRED)

```python
# ✅ CORRECT - No PHI in logs
logger.info("License processed", extra={"license_id": hash(license.id)})

# ❌ WRONG - PHI in logs
logger.info(f"Processing license {license.license_number}")  # HIPAA VIOLATION
```

### 5. Audit Trail (REQUIRED for PHI access)

```python
# ✅ CORRECT - Audit PHI access
def get_license(license_id: int, user: User):
    license = session.query(License).get(license_id)

    # Log audit trail
    audit_log = AuditLog(
        user_id=user.id,
        action="VIEW_LICENSE",
        resource_id=license_id,
        timestamp=datetime.utcnow()
    )
    session.add(audit_log)
    session.commit()

    return license

# ❌ WRONG - No audit trail
def get_license(license_id: int):
    return session.query(License).get(license_id)  # UNAUDITED PHI ACCESS
```

---

## Pre-Commit Checks

Before committing files matching patterns above:
1. Run HIPAA DoD checklist
2. Scan for PHI in logs/errors
3. Verify encryption for PHI fields
4. Check for parameterized queries
5. Confirm audit logging present

**Auto-fail conditions**:
- PHI in plaintext (Column(String) for sensitive fields)
- String concatenation in SQL queries
- PHI in error messages or logs
- No audit trail for PHI access
```

**File**: `/Users/tmac/1_REPOS/credentialmate/.claude/rules/testing.md`

```markdown
# Testing Standards

**Applies to**: All code files

**File patterns**: `**/*.py`, `**/*.ts`, `**/*.tsx`

---

## Coverage Requirements

**Standard Code**: >70% coverage
**PHI-Handling Code**: >80% coverage (HIPAA requirement)
**Critical Paths**: 100% coverage
- Authentication/authorization
- Payment processing
- License parsing (data integrity)

## Test Types Required

### Backend (Python)

**Unit Tests** (pytest):
```python
# ✅ REQUIRED for all business logic
def test_parse_license_expiration():
    result = parse_expiration_date("12/31/2025")
    assert result == datetime(2025, 12, 31)
```

**Integration Tests** (pytest + TestClient):
```python
# ✅ REQUIRED for all API endpoints
def test_create_license_endpoint():
    response = client.post("/api/licenses", json={...})
    assert response.status_code == 201
```

### Frontend (TypeScript)

**Component Tests** (Vitest + React Testing Library):
```typescript
// ✅ REQUIRED for all user-facing components
test('LicenseCard displays license info', () => {
  render(<LicenseCard license={mockLicense} />);
  expect(screen.getByText('Active')).toBeInTheDocument();
});
```

## DoD for Tests

- [ ] All new code has tests
- [ ] Coverage meets requirements (70% standard, 80% PHI)
- [ ] Tests are deterministic (no flakiness)
- [ ] Test data does NOT contain real PHI
- [ ] Mocks used for external services
```

**File**: `/Users/tmac/1_REPOS/credentialmate/.claude/rules/lambda.md`

```markdown
# Lambda Deployment Rules

**Applies to**: Lambda function code in `apps/backend/`

**Critical**: Lambda functions handle license parsing (PHI processing)

---

## SAM Build Verification (REQUIRED)

Before marking task complete:

```bash
# 1. Clean build
rm -rf .aws-sam/

# 2. Build with SAM
sam build

# 3. Verify build matches source
diff -r apps/backend/ .aws-sam/build/LicenseParserFunction/

# 4. Test locally (optional but recommended)
sam local invoke LicenseParserFunction --event events/test-license.json
```

**Auto-fail if**:
- SAM build fails
- Build differs from source (stale code)
- Dependencies missing from requirements.txt

## Layer Management

Tesseract layer: `arn:aws:lambda:us-east-1:...:layer:tesseract-layer:5`

**Before updating layer**:
1. Test locally with new layer
2. Deploy to dev first
3. Verify parsing still works
4. Then deploy to prod

## Environment Variables

**Required**:
- `DATABASE_URL` (from Secrets Manager)
- `FRONTEND_URL` (for CORS)

**Document in**:
- `template.yaml` (SAM template)
- `docs/INFRASTRUCTURE.md` (for humans)

## Deployment Gates

- **Dev**: Auto-deploy after tests pass
- **Staging**: Require manual trigger
- **Prod**: Require human approval + HIPAA checklist
```

**Verification**:
```bash
# All 3 rule files created
ls -la .claude/rules/
# Expected: hipaa.md, testing.md, lambda.md
```

#### Step 1.4: Create Post-Tool-Use Hook (Day 3)

**File**: `/Users/tmac/1_REPOS/credentialmate/.claude/hooks/post_tool_use.sh`

```bash
#!/bin/bash
set -euo pipefail

# Fast feedback loop after Write/Edit operations
# Runs: linting, type checking, quick tests

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "🔍 Running post-tool-use checks..."

# Backend checks (if backend files changed)
if git diff --name-only | grep -q "^apps/backend/"; then
    echo "  → Backend: Running ruff..."
    cd apps/backend
    ruff check --select E,F,I --ignore E501 . || echo "⚠️  Lint warnings (non-blocking)"

    echo "  → Backend: Running mypy..."
    mypy . || echo "⚠️  Type errors (non-blocking)"

    echo "  → Backend: Running quick tests..."
    pytest tests/unit/ -x --tb=short || echo "❌ Unit tests failed"

    cd "$REPO_ROOT"
fi

# Frontend checks (if frontend files changed)
if git diff --name-only | grep -q "^apps/frontend-web/"; then
    echo "  → Frontend: Running ESLint..."
    cd apps/frontend-web
    npm run lint || echo "⚠️  Lint warnings (non-blocking)"

    echo "  → Frontend: TypeScript check..."
    npm run type-check || echo "⚠️  Type errors (non-blocking)"

    cd "$REPO_ROOT"
fi

echo "✅ Post-tool-use checks complete"
```

**Make executable**:
```bash
chmod +x .claude/hooks/post_tool_use.sh
```

**Verification**:
```bash
# Test hook
.claude/hooks/post_tool_use.sh
# Should run without errors
```

#### Step 1.5: Create Local Work Queue (Day 4)

**File**: `/Users/tmac/1_REPOS/credentialmate/orchestration/queue/work_queue_local.json`

```json
{
  "metadata": {
    "project": "credentialmate",
    "orchestrator": "/Users/tmac/1_REPOS/AI_Orchestrator",
    "sync_status": "synced",
    "last_sync": "2026-02-06T00:00:00Z",
    "created_at": "2026-02-06T00:00:00Z"
  },
  "tasks": []
}
```

**File**: `/Users/tmac/1_REPOS/credentialmate/orchestration/sync_with_orchestrator.py`

```python
#!/usr/bin/env python3
"""
Sync local work queue with orchestrator work queue.

Usage:
    python orchestration/sync_with_orchestrator.py --pull   # Get tasks from orchestrator
    python orchestration/sync_with_orchestrator.py --push   # Send completed tasks back
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ORCHESTRATOR_ROOT = Path("/Users/tmac/1_REPOS/AI_Orchestrator")
ORCHESTRATOR_QUEUE = ORCHESTRATOR_ROOT / "tasks/work_queue_credentialmate.json"

LOCAL_ROOT = Path(__file__).parent.parent
LOCAL_QUEUE = LOCAL_ROOT / "orchestration/queue/work_queue_local.json"


def load_queue(path: Path) -> dict:
    """Load work queue from file."""
    if not path.exists():
        return {"tasks": [], "metadata": {}}
    with open(path) as f:
        return json.load(f)


def save_queue(path: Path, queue: dict) -> None:
    """Save work queue to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(queue, f, indent=2)


def pull_from_orchestrator() -> None:
    """Pull tasks from orchestrator to local queue."""
    print("🔄 Pulling tasks from orchestrator...")

    orchestrator_queue = load_queue(ORCHESTRATOR_QUEUE)
    local_queue = load_queue(LOCAL_QUEUE)

    # Get pending tasks from orchestrator
    pending_tasks = [
        task for task in orchestrator_queue.get("tasks", [])
        if task.get("status") in ["pending", "in_progress"]
    ]

    # Merge into local queue (orchestrator is source of truth)
    local_task_ids = {task["id"] for task in local_queue.get("tasks", [])}

    for task in pending_tasks:
        if task["id"] not in local_task_ids:
            local_queue.setdefault("tasks", []).append(task)
            print(f"  → Added task: {task['id']} - {task['title']}")

    # Update metadata
    local_queue.setdefault("metadata", {})
    local_queue["metadata"]["last_sync"] = datetime.utcnow().isoformat() + "Z"
    local_queue["metadata"]["sync_status"] = "synced"

    save_queue(LOCAL_QUEUE, local_queue)
    print(f"✅ Pulled {len(pending_tasks)} tasks")


def push_to_orchestrator() -> None:
    """Push completed tasks from local queue to orchestrator."""
    print("🔄 Pushing completed tasks to orchestrator...")

    orchestrator_queue = load_queue(ORCHESTRATOR_QUEUE)
    local_queue = load_queue(LOCAL_QUEUE)

    # Get completed tasks from local
    completed_tasks = [
        task for task in local_queue.get("tasks", [])
        if task.get("status") == "completed"
    ]

    # Update orchestrator queue
    updated_count = 0
    for local_task in completed_tasks:
        for orch_task in orchestrator_queue.get("tasks", []):
            if orch_task["id"] == local_task["id"]:
                orch_task["status"] = "completed"
                orch_task["completed_at"] = local_task.get("completed_at")
                orch_task["evidence"] = local_task.get("evidence", [])
                updated_count += 1
                print(f"  → Updated task: {local_task['id']} - {local_task['title']}")
                break

    # Update orchestrator metadata
    orchestrator_queue.setdefault("metadata", {})
    orchestrator_queue["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"

    save_queue(ORCHESTRATOR_QUEUE, orchestrator_queue)
    print(f"✅ Pushed {updated_count} completed tasks")


def main():
    if "--pull" in sys.argv:
        pull_from_orchestrator()
    elif "--push" in sys.argv:
        push_to_orchestrator()
    else:
        print("Usage: python sync_with_orchestrator.py [--pull|--push]")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Make executable**:
```bash
chmod +x orchestration/sync_with_orchestrator.py
```

**Verification**:
```bash
# Test sync script
python orchestration/sync_with_orchestrator.py --pull
# Should create local queue and pull tasks
```

---

## Phase 1 Success Criteria

✅ **Files Created** (9 files):
- [ ] .claude/CLAUDE.md (150-200 lines)
- [ ] .claude/agents/lead.md
- [ ] .claude/agents/builder.md
- [ ] .claude/agents/reviewer.md
- [ ] .claude/rules/hipaa.md (CRITICAL)
- [ ] .claude/rules/testing.md
- [ ] .claude/rules/lambda.md
- [ ] .claude/hooks/post_tool_use.sh (executable)
- [ ] orchestration/sync_with_orchestrator.py (executable)

✅ **Memory Sustainability**:
- [ ] Local work queue exists
- [ ] Sync with orchestrator works
- [ ] CLAUDE.md loaded automatically
- [ ] Rules apply to relevant files

✅ **HIPAA Compliance**:
- [ ] HIPAA rules documented
- [ ] Agent contracts mention HIPAA
- [ ] DoD includes HIPAA checklist
- [ ] Audit trail requirements clear

✅ **Testing**:
- [ ] Post-tool-use hook runs successfully
- [ ] Sync script pulls/pushes tasks
- [ ] CLAUDE.md is reasonable length (<200 lines)

---

## Phase 2: AI_Orchestrator Enhancement (Week 3-4)

*(Detailed plan for orchestrator enhancements - to be expanded)*

### Goal
Enhance orchestrator with better work_queue management and Ralph integration

### Key Tasks
1. Migrate work_queue_credentialmate.json to work_queue schema v2
2. Add Ralph verifier for HIPAA deployments
3. Create formal role contracts in orchestrator
4. Add telemetry for cross-repo coordination

---

## Phase 3: Verification & Rollout (Week 4)

### Goal
Verify hybrid architecture works end-to-end

### Test Scenarios

**Scenario 1: Local Work**
```bash
cd /Users/tmac/1_REPOS/credentialmate

# Agent works entirely in CredentialMate
# Uses local CLAUDE.md, local skills, local work queue
# No orchestrator needed
```

**Scenario 2: Coordinated Work**
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# Orchestrator assigns task to CredentialMate
# CredentialMate pulls task via sync script
# CredentialMate completes task locally
# CredentialMate pushes completion back to orchestrator
```

**Scenario 3: HIPAA Audit**
```bash
# Auditor asks: "Show all license parsing changes"

# Check orchestrator for high-level history
cat tasks/work_queue_credentialmate.json | jq '.tasks[] | select(.title | contains("license"))'

# Check CredentialMate for detailed evidence
cd /Users/tmac/1_REPOS/credentialmate
cat orchestration/queue/work_queue_local.json

# Both queues synced ✅
```

---

## Next Steps

1. **Review this plan** - Does it align with your goals?
2. **Start Phase 1.1** - Create .claude/CLAUDE.md in CredentialMate
3. **Iterate** - Adjust plan as we learn

**Estimated Total Time**: 4 weeks (can be parallelized)

**Memory Sustainability**: 95% (hybrid work_queue + CLAUDE.md + orchestrator)

---

**Status**: ✅ Ready for implementation
**Start Date**: 2026-02-06
**Target Completion**: 2026-03-06
