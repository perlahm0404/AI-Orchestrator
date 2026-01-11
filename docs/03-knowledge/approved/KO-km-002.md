---
{
  "id": "KO-km-002",
  "project": "karematch",
  "title": "TypeScript strict mode requires explicit types in map callbacks",
  "what_was_learned": "When TypeScript strict mode is enabled, Array.map() callbacks must have explicit parameter types or TypeScript infers 'any' and fails compilation. Adding type annotations to arrow function parameters resolves the issue.",
  "why_it_matters": "Type errors block builds and deployments. Strict mode violations are caught at compile time, preventing runtime errors.",
  "prevention_rule": "Always add explicit types to callback parameters when using array methods (map, filter, reduce) in strict mode.",
  "tags": [
    "typescript",
    "strict-mode",
    "array-methods",
    "type-errors"
  ],
  "status": "approved",
  "created_at": "2026-01-06T15:00:00.000000",
  "approved_at": "2026-01-06T12:40:50.746442",
  "detection_pattern": "error TS7006.*implicitly has an 'any' type",
  "file_patterns": [
    "packages/*/src/**/*.ts"
  ]
}
---

# TypeScript strict mode requires explicit types in map callbacks

## What Was Learned

When TypeScript strict mode is enabled, Array.map() callbacks must have explicit parameter types or TypeScript infers 'any' and fails compilation. Adding type annotations to arrow function parameters resolves the issue.

## Why It Matters

Type errors block builds and deployments. Strict mode violations are caught at compile time, preventing runtime errors.

## Prevention Rule

Always add explicit types to callback parameters when using array methods (map, filter, reduce) in strict mode.

## Tags

typescript, strict-mode, array-methods, type-errors

## Detection Pattern

```
error TS7006.*implicitly has an 'any' type
```

## File Patterns

packages/*/src/**/*.ts

---

**Status**: approved
**Project**: karematch
**Created**: 2026-01-06T15:00:00.000000
**Approved**: 2026-01-06T12:40:50.746442
