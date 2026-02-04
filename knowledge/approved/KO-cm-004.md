---
{
  "id": "KO-cm-004",
  "project": "credentialmate",
  "title": "Lambda Lazy Loading Import Patterns and Pitfalls",
  "what_was_learned": "After deploying Lambda with lazy-loaded routers, encountered ModuleNotFoundError due to incorrect import paths using 'src.' prefix. Lambda working directory is /var/task/, making 'src.api.v1.X' look for /var/task/src/src/api/v1/X (double nesting). Fixed by removing 'src.' prefix from all 30 router imports in lazy_app.py. MTTR: 10 minutes. Verified with comprehensive endpoint testing (13 endpoints, 100% success rate).",
  "why_it_matters": "This import path issue caused a P0 production outage affecting 30+ API endpoints. Understanding Lambda's working directory context is critical for lazy loading patterns. The fix is simple but non-obvious, and the pattern is likely to recur in other Lambda applications using dynamic imports. Proper testing methodology (direct Lambda invocation) enabled rapid diagnosis and verification.",
  "prevention_rule": "When implementing lazy-loaded routers in Lambda: (1) Use relative imports without 'src.' prefix in router maps, (2) Import paths must match actual file structure from /var/task/, (3) Test lazy loading locally with PYTHONPATH simulation, (4) Run comprehensive endpoint tests post-deployment, (5) Monitor CloudWatch logs for ModuleNotFoundError. Always verify import paths match file structure before deploying.",
  "tags": [
    "lambda",
    "aws",
    "python",
    "imports",
    "lazy-loading",
    "deployment",
    "credentialmate",
    "fastapi",
    "production-outage",
    "module-not-found"
  ],
  "status": "approved",
  "created_at": "2026-02-04T06:28:00.000000",
  "approved_at": "2026-02-04T06:30:22.576561",
  "detection_pattern": "ERROR.*ModuleNotFoundError.*No module named 'src\\.api\\.v1\\.",
  "file_patterns": [
    "infra/lambda/**/lazy_app.py",
    "**/lazy_app.py",
    "**/*_app.py"
  ]
}
---

# Lambda Lazy Loading Import Patterns and Pitfalls

## What Was Learned

After deploying Lambda with lazy-loaded routers, encountered ModuleNotFoundError due to incorrect import paths using 'src.' prefix. Lambda working directory is /var/task/, making 'src.api.v1.X' look for /var/task/src/src/api/v1/X (double nesting). Fixed by removing 'src.' prefix from all 30 router imports in lazy_app.py. MTTR: 10 minutes. Verified with comprehensive endpoint testing (13 endpoints, 100% success rate).

## Why It Matters

This import path issue caused a P0 production outage affecting 30+ API endpoints. Understanding Lambda's working directory context is critical for lazy loading patterns. The fix is simple but non-obvious, and the pattern is likely to recur in other Lambda applications using dynamic imports. Proper testing methodology (direct Lambda invocation) enabled rapid diagnosis and verification.

## Prevention Rule

When implementing lazy-loaded routers in Lambda: (1) Use relative imports without 'src.' prefix in router maps, (2) Import paths must match actual file structure from /var/task/, (3) Test lazy loading locally with PYTHONPATH simulation, (4) Run comprehensive endpoint tests post-deployment, (5) Monitor CloudWatch logs for ModuleNotFoundError. Always verify import paths match file structure before deploying.

## Tags

lambda, aws, python, imports, lazy-loading, deployment, credentialmate, fastapi, production-outage, module-not-found

## Detection Pattern

```
ERROR.*ModuleNotFoundError.*No module named 'src\.api\.v1\.
```

## File Patterns

infra/lambda/**/lazy_app.py, **/lazy_app.py, **/*_app.py

---

**Status**: approved
**Project**: credentialmate
**Created**: 2026-02-04T06:28:00.000000
**Approved**: 2026-02-04T06:30:22.576561
