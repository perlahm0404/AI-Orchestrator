---
id: lambda-lazy-loading-imports-001
title: Lambda Lazy Loading Import Patterns and Pitfalls
type: resolved-issue
status: draft
confidence: high
priority: high
created: 2026-02-04
project: credentialmate
tags:
  - lambda
  - aws
  - python
  - imports
  - lazy-loading
  - deployment
applies_to:
  - FastAPI applications on Lambda
  - Lazy-loaded routers
  - Dynamic module imports
  - SAM deployments
---

## Problem Statement

When implementing lazy-loaded routers in AWS Lambda with FastAPI, **absolute import paths with `src.` prefix fail** with `ModuleNotFoundError`, breaking all lazy-loaded endpoints in production.

## Context

**Environment:**
- AWS Lambda (Python 3.11)
- FastAPI application
- Lazy-loaded routers (30+ endpoints)
- SAM deployment framework
- Working directory: `/var/task/`

**Symptom:**
```
ModuleNotFoundError: No module named 'src.api.v1.providers'
```

**Impact:**
- All lazy-loaded endpoints return 500 errors
- Only statically imported endpoints work
- Production API outage

## Root Cause

Lambda's working directory context causes import path resolution issues:

1. **Lambda extracts code to `/var/task/`**
2. **Import statements are relative to this directory**
3. **String-based dynamic imports in lazy loading use `importlib.import_module()`**
4. **Import path `"src.api.v1.providers"` looks for `/var/task/src/src/api/v1/providers`** (double nesting)

**File Structure:**
```
/var/task/
├── src/
│   ├── lazy_app.py          # Lazy loading entry point
│   └── api/
│       └── v1/
│           ├── providers.py
│           ├── licenses.py
│           └── ...
```

**Broken Import (from lazy_app.py):**
```python
_ROUTER_MAP = {
    "providers": "src.api.v1.providers",  # ❌ Looks for /var/task/src/src/api/v1/providers
}
```

**Working Import:**
```python
_ROUTER_MAP = {
    "providers": "api.v1.providers",  # ✅ Looks for /var/task/api/v1/providers
}
```

## Solution

**Fix:** Remove `src.` prefix from all lazy-loaded import paths

**File:** `infra/lambda/functions/backend/src/lazy_app.py`

**Changes:**
```python
# Before (broken)
_ROUTER_MAP: Dict[str, str] = {
    "providers": "src.api.v1.providers",
    "licenses": "src.api.v1.licenses",
    "documents": "src.api.v1.documents",
    # ... 27 more routers
}

# After (fixed)
_ROUTER_MAP: Dict[str, str] = {
    "providers": "api.v1.providers",
    "licenses": "api.v1.licenses",
    "documents": "api.v1.documents",
    # ... 27 more routers
}
```

**Deployment:**
```bash
cd /Users/tmac/1_REPOS/credentialmate/infra/lambda
sam build --use-container
sam deploy --config-env prod
```

## Verification

### Test Import Paths Work

**CloudWatch Log Check:**
```bash
aws logs tail /aws/lambda/{function-name} \
  --since 5m \
  --filter-pattern "ModuleNotFoundError"
```

**Expected:** No results

### Test Endpoint Response

**Direct Lambda Invocation:**
```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

event = {
    "resource": "/health",
    "path": "/health",
    "httpMethod": "GET",
    "headers": {},
    "requestContext": {"httpMethod": "GET", "path": "/health"}
}

response = lambda_client.invoke(
    FunctionName='your-lambda-function',
    InvocationType='RequestResponse',
    Payload=json.dumps(event)
)

payload = json.loads(response['Payload'].read())
print(f"Status: {payload.get('statusCode')}")  # Should be 200
```

### Test All Lazy-Loaded Endpoints

Run comprehensive endpoint test (see test script in session artifacts).

## When This Pattern Applies

✅ **Use relative imports (without `src.`)** when:
- Lazy loading routers in Lambda
- Using `importlib.import_module()` with string paths
- Working directory is `/var/task/`
- File structure has `api/` at top level (not `src/api/`)

❌ **Don't use `src.` prefix** when:
- Current module is already in `src/` directory
- Import path would create double nesting
- Using dynamic imports in Lambda

## Prevention Checklist

**Before Deployment:**
- [ ] Verify import paths match actual file structure
- [ ] Check no `src.` prefix in lazy loading map (unless file is in `src/src/`)
- [ ] Test locally with `PYTHONPATH=/path/to/lambda/layer`
- [ ] Review CloudWatch logs for existing import errors

**After Deployment:**
- [ ] Check CloudWatch logs for ModuleNotFoundError
- [ ] Test 3-5 representative endpoints
- [ ] Verify lazy loading works (check logs for "Lazy loading module: X")
- [ ] Run comprehensive endpoint test

## Testing Locally

**Simulate Lambda Environment:**
```bash
cd /Users/tmac/1_REPOS/credentialmate/infra/lambda/functions/backend

# Set PYTHONPATH to simulate Lambda working directory
export PYTHONPATH=$(pwd)

# Test import path
python3 -c "import importlib; importlib.import_module('api.v1.providers')"

# Should succeed without errors
```

## Related Issues

- S3 bucket environment variable mismatch (same session)
- boto3 timeout configuration in VPC Lambda
- Lazy loading initialization during first request

## Effectiveness Metrics

- **MTTR:** 10 minutes (diagnosis → deployment)
- **Fix Complexity:** LOW (30 string replacements)
- **Verification Time:** 5 minutes
- **Recurrence Risk:** LOW (once fixed, stays fixed)

## Consultation History

- **Created:** 2026-02-04 (Lambda import fix session)
- **Consultations:** 0 (newly created)
- **Success Rate:** N/A (not yet consulted)

## References

- Session: `sessions/credentialmate/active/20260203-1430-e2e-production-test.md` (Phase 9)
- Test Script: `/tmp/lambda-endpoint-tester.py`
- Test Report: `/tmp/LAMBDA_TESTING_REPORT.md`
- Python docs: `importlib.import_module()` - https://docs.python.org/3/library/importlib.html

## Confidence Level: HIGH

This solution has been:
- ✅ Deployed to production
- ✅ Verified with comprehensive endpoint testing
- ✅ Confirmed via CloudWatch log analysis
- ✅ Tested across 13 endpoints (100% success rate)
