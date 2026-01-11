---
{
  "id": "KO-km-001",
  "project": "karematch",
  "title": "Drizzle ORM version mismatches cause type errors",
  "what_was_learned": "When multiple packages in a monorepo use different versions of drizzle-orm, TypeScript will fail with \"No overload matches this call\" errors on eq/gte/lte/desc functions. All packages must use the same drizzle-orm version.",
  "why_it_matters": "Type errors block deployments and are confusing to debug because the code looks correct. Version mismatches are a silent dependency issue.",
  "prevention_rule": "Enforce single drizzle-orm version across monorepo. Add to package.json resolutions or use workspace protocol.",
  "tags": [
    "typescript",
    "drizzle-orm",
    "dependencies",
    "type-errors",
    "monorepo"
  ],
  "status": "approved",
  "created_at": "2026-01-06T00:53:14.813396",
  "approved_at": "2026-01-06T00:53:14.813580",
  "detection_pattern": "error TS2769.*No overload matches this call.*drizzle",
  "file_patterns": [
    "**/package.json",
    "packages/*/src/**/*.ts"
  ]
}
---

# Drizzle ORM version mismatches cause type errors

## What Was Learned

When multiple packages in a monorepo use different versions of drizzle-orm, TypeScript will fail with "No overload matches this call" errors on eq/gte/lte/desc functions. All packages must use the same drizzle-orm version.

## Why It Matters

Type errors block deployments and are confusing to debug because the code looks correct. Version mismatches are a silent dependency issue.

## Prevention Rule

Enforce single drizzle-orm version across monorepo. Add to package.json resolutions or use workspace protocol.

## Tags

typescript, drizzle-orm, dependencies, type-errors, monorepo

## Detection Pattern

```
error TS2769.*No overload matches this call.*drizzle
```

## File Patterns

**/package.json, packages/*/src/**/*.ts

---

**Status**: approved
**Project**: karematch
**Created**: 2026-01-06T00:53:14.813396
**Approved**: 2026-01-06T00:53:14.813580
