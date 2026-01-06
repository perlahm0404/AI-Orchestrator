# v5 Planning: Dual-Team Architecture

**Version**: 5.0
**Date**: 2026-01-06
**Status**: DRAFT - Awaiting Approval
**Builds On**: v4 (All phases complete, system operational)

---

## Executive Summary

v5 introduces a **Dual-Team Architecture** that separates concerns between:

| Team | Mission | Scope |
|------|---------|-------|
| **QA Team** (AI Brain) | Maintain code quality | Existing stable code on `main` |
| **Dev Team** | Build new features | Feature branches only |

This allows continuous QA improvement on production code while new features are built in isolation, merging only when complete and tested.

---

## Problem Statement

### Current State (v4 Complete)
- AI Brain operational with BugFix + CodeQuality agents
- 10 bugs fixed, 34 governance tests passing
- Ralph verification working end-to-end
- KareMatch has 72 test failures + 10+ incomplete features

### Challenge
KareMatch needs both:
1. **QA work**: Fix 72 test failures, process verified bugs, improve coverage
2. **Feature work**: Complete matching algorithm, admin dashboard, credentialing APIs

Running both on `main` creates conflicts:
- QA fixes may touch files being actively developed
- Feature work may introduce new issues that confuse QA metrics
- Hard to track "what broke" when both streams merge together

### Solution: Dual-Team Architecture
Separate the work streams with clear boundaries, handoff protocols, and isolation guarantees.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Orchestrator                            │
│                                                                 │
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │    QA Team       │           │    Dev Team      │           │
│  │  (AI Brain v4)   │           │   (NEW in v5)    │           │
│  │                  │           │                  │           │
│  │  - BugFix Agent  │           │  - Feature Agent │           │
│  │  - CodeQuality   │           │  - Test Writer   │           │
│  │  - Test Fixer    │           │                  │           │
│  └────────┬─────────┘           └────────┬─────────┘           │
│           │                              │                      │
│           ▼                              ▼                      │
│    ┌─────────────┐               ┌─────────────┐               │
│    │    main     │◄──────────────│  feature/*  │               │
│    │   branch    │  PR + Ralph   │  branches   │               │
│    └─────────────┘   PASS        └─────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   KareMatch     │
                    │   Repository    │
                    └─────────────────┘
```

---

## Team Specifications

### QA Team (Existing - Enhanced)

**Mission**: Maintain and improve code quality on stable production code.

**Agents**:
| Agent | Purpose | Status |
|-------|---------|--------|
| BugFix | Fix verified bugs | ✅ Operational |
| CodeQuality | Lint, types, accessibility | ✅ Operational |
| TestFixer | Fix test infrastructure | 🆕 New in v5 |

**Scope**:
- Works on `main` branch and `fix/*` branches
- Only touches existing code (no new features)
- Must not change behavior (test count stays same)
- Ralph verification on every commit

**Autonomy Contract**: `governance/contracts/qa-team.yaml`
```yaml
name: qa-team
version: "1.0"
autonomy_level: L2  # Higher autonomy for safe operations

allowed:
  - read_files
  - write_files
  - run_tests
  - run_lint
  - run_typecheck
  - git_commit
  - git_push_fix_branch
  - create_pr

forbidden:
  - modify_migrations
  - modify_ci_config
  - push_to_main_direct
  - deploy
  - add_new_features
  - change_behavior
  - delete_tests
  - use_no_verify

limits:
  max_lines_added: 100
  max_files_changed: 5
  max_commits_per_session: 10

halt_on:
  - ralph_blocked
  - test_count_decreased
  - new_lint_errors
```

---

### Dev Team (New in v5)

**Mission**: Build new features in isolation until ready for integration.

**Agents**:
| Agent | Purpose | Status |
|-------|---------|--------|
| FeatureBuilder | Implement new functionality | 🆕 New |
| TestWriter | Write tests for new features | 🆕 New |

**Scope**:
- Works ONLY on `feature/*` branches
- Creates new code, new tests, new components
- Can break things during development (isolated)
- Ralph verification only at PR time (not every commit)

**Autonomy Contract**: `governance/contracts/dev-team.yaml`
```yaml
name: dev-team
version: "1.0"
autonomy_level: L1  # Stricter - more human review for new code

allowed:
  - read_files
  - write_files
  - create_files
  - run_tests
  - run_lint
  - run_typecheck
  - git_commit
  - git_push_feature_branch
  - create_pr

forbidden:
  - modify_migrations  # Requires human review
  - modify_ci_config
  - push_to_main
  - push_to_fix_branch  # Stay in your lane
  - deploy
  - delete_existing_tests  # Can skip, not delete
  - use_no_verify

requires_approval:
  - new_dependencies
  - new_api_endpoints
  - schema_changes
  - external_api_integration

limits:
  max_lines_added: 500  # Higher limit for features
  max_files_changed: 20
  max_new_files: 10

halt_on:
  - ralph_blocked_at_pr
  - approval_required_item
```

---

## Branch Strategy

### Branch Naming Convention

```
main                           # Production-ready code
├── fix/BUG-T1-unused-import   # QA Team bug fixes
├── fix/test-infrastructure    # QA Team test fixes
├── feature/matching-algorithm # Dev Team features
├── feature/admin-dashboard    # Dev Team features
└── feature/credentialing-api  # Dev Team features
```

### Branch Rules

| Branch Pattern | Owner | Ralph | Merge Target |
|----------------|-------|-------|--------------|
| `main` | Protected | Always | N/A |
| `fix/*` | QA Team | Every commit | main |
| `feature/*` | Dev Team | PR only | main |

### Integration Protocol

```
1. Dev Team completes feature on feature/* branch
2. Dev Team opens PR against main
3. Ralph runs full verification (lint + typecheck + tests)
4. If PASS → Merge allowed
5. If FAIL → Dev Team fixes, re-runs Ralph
6. After merge → Feature code becomes QA Team's scope
```

---

## KareMatch Feature Backlog (Dev Team Scope)

### Priority 0: Core Value (Matching Algorithm)

**Branch**: `feature/matching-algorithm`

| Task | Files | Status |
|------|-------|--------|
| Implement deterministic matching logic | `services/matching/src/routes.ts` | TODO |
| Fix proximity matching (returns null) | `services/matching/src/therapist-matcher.ts` | TODO |
| Add match scoring algorithm | `services/matching/src/scoring.ts` | TODO |
| Implement saved matches retrieval | `services/matching/src/routes.ts` | TODO |
| Write matching tests | `tests/unit/matching/` | TODO |

**Exit Criteria**:
- [ ] `/api/matching/find` returns scored results
- [ ] Proximity filter works correctly
- [ ] 90%+ test coverage on matching module
- [ ] Ralph PASS on PR

---

### Priority 1: Operations (Admin Dashboard)

**Branch**: `feature/admin-dashboard`

| Task | Files | Status |
|------|-------|--------|
| Implement approval history tracking | `services/admin/src/routes.ts` | TODO |
| Dashboard summary endpoint | `services/admin/src/routes.ts` | TODO |
| Escalations list endpoint | `services/admin/src/routes.ts` | TODO |
| Activity tracking system | `services/admin/src/routes.ts` | TODO |
| Send approval/rejection emails | `services/admin/src/therapist-management.ts` | TODO |

**Exit Criteria**:
- [ ] Admin can view approval history
- [ ] Dashboard shows key metrics
- [ ] Email notifications sent on status change
- [ ] Ralph PASS on PR

---

### Priority 1: Compliance (Credentialing APIs)

**Branch**: `feature/credentialing-api`

| Task | Files | Status |
|------|-------|--------|
| NPPES API integration | `services/credentialing/src/routes.ts` | TODO |
| DEA validation API | `services/credentialing/src/routes.ts` | TODO |
| OIG exclusion check | `services/credentialing/src/routes.ts` | TODO |
| Document storage (Supabase) | `services/credentialing/src/document-storage.ts` | TODO |

**Exit Criteria**:
- [ ] NPI verification returns real data
- [ ] DEA number validation works
- [ ] OIG check integrated
- [ ] Documents upload to Supabase
- [ ] Ralph PASS on PR

---

### Priority 2: UX (Email Notifications)

**Branch**: `feature/email-notifications`

| Task | Files | Status |
|------|-------|--------|
| Appointment confirmation emails | `services/appointments/src/routes.ts` | TODO |
| Auth notification emails | `services/auth/src/routes.ts` | TODO |
| Credentialing status emails | `services/credentialing/src/emailService.ts` | TODO |

---

## QA Team Backlog (Existing + Enhanced)

### Test Infrastructure (72 failures)

| Category | Count | Priority |
|----------|-------|----------|
| Stub tests (appointments-email/workflow) | ~45 | P0 |
| Unit test failures | ~27 | P1 |
| therapistMatcher.observability | 1-2 | P2 |

### Verified Bugs (VERIFIED-BUGS.md)

| Bug ID | Type | Status |
|--------|------|--------|
| BUG-T1 to T4 | Trivial (lint) | Ready |
| BUG-M1 to M4 | Medium (a11y, types) | Ready |
| BUG-C1 to C2 | Complex | Phase 1 |

### Code Quality (bugs_to_fix.json)

| Item | File | Type |
|------|------|------|
| BUG-H2 | TherapistMobileNav.tsx | console.error removal |
| BUG-H3 | CrisisIntercept.tsx | console.error removal |
| BUG-H4 | AvailabilityWizardStep.tsx | console.error removal |
| BUG-H5 | IntentCapture.tsx | console.error removal |

---

## Handoff Protocol

### Feature Complete → QA Scope

When Dev Team completes a feature:

```markdown
## Feature Handoff: [feature-name]

**Branch**: feature/[name]
**PR**: #[number]
**Ralph Status**: PASS

### What Was Built
- [List of new functionality]

### New Files Added
| File | Purpose |
|------|---------|
| path/to/file.ts | Description |

### Tests Added
- [ ] Unit tests: X passing
- [ ] Integration tests: X passing
- [ ] E2E tests: X passing (if applicable)

### Known Limitations
- [Any technical debt or future improvements]

### Post-Merge QA Tasks
- [ ] Run full test suite
- [ ] Verify no regressions
- [ ] Add to QA Team scope
```

---

## Implementation Phases

### Phase 5.0: Dev Team Setup (This Sprint)

**Goal**: Establish Dev Team infrastructure

| Task | Owner | Status |
|------|-------|--------|
| Create v5-Planning.md | Claude | ✅ |
| Create dev-team.yaml contract | Claude | TODO |
| Update STATE.md | Claude | TODO |
| Update CLAUDE.md | Claude | TODO |
| Update DECISIONS.md | Claude | TODO |
| Create session handoff | Claude | TODO |

### Phase 5.1: First Feature Branch

**Goal**: Validate Dev Team workflow with matching algorithm

| Task | Owner | Status |
|------|-------|--------|
| Create feature/matching-algorithm branch | Dev Team | TODO |
| Implement core matching logic | Dev Team | TODO |
| Write matching tests | Dev Team | TODO |
| Open PR, run Ralph | Dev Team | TODO |
| Merge to main | Dev Team | TODO |

### Phase 5.2: Parallel Operations

**Goal**: Both teams running simultaneously

| QA Team | Dev Team |
|---------|----------|
| Fix 72 test failures | Build admin dashboard |
| Process VERIFIED-BUGS.md | Build credentialing APIs |
| Console.error cleanup | Build email notifications |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Branch conflicts | <5 per sprint | Git merge analysis |
| Feature cycle time | <2 weeks | PR open → merge |
| QA regression rate | 0% | Tests passing after merge |
| Ralph PASS rate | >95% | PR verification stats |
| Test coverage (new code) | >80% | Coverage report |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Branch divergence | Weekly rebases from main |
| Merge conflicts | Clear file ownership per team |
| Feature scope creep | Strict PR review against spec |
| Test infrastructure blocks features | QA Team prioritizes test fixes |

---

## Open Questions

1. **Should Dev Team have separate Knowledge Objects?**
   - Option A: Shared KO system (both teams learn together)
   - Option B: Team-specific KOs (domain separation)
   - **Recommendation**: Shared (Option A) - learning should cross-pollinate

2. **How often should teams sync?**
   - Option A: Daily standups (too heavy)
   - Option B: Weekly integration (recommended)
   - Option C: Per-PR only (too loose)
   - **Recommendation**: Weekly (Option B)

3. **Who resolves merge conflicts?**
   - Option A: Dev Team (they know the feature)
   - Option B: QA Team (they know main)
   - **Recommendation**: Dev Team rebases, QA Team reviews

---

## Appendix: File Ownership Matrix

| Directory | QA Team | Dev Team |
|-----------|---------|----------|
| `services/matching/` | Tests only | Full ownership |
| `services/admin/` | Lint/types | New routes |
| `services/credentialing/` | Existing code | API integration |
| `services/appointments/` | Full ownership | Email features |
| `services/auth/` | Full ownership | Email features |
| `web/src/components/` | A11y fixes | New components |
| `web/src/pages/` | Lint fixes | New pages |
| `tests/` | Infrastructure | New tests |
| `lib/` | Shared | Shared |

---

**Document Status**: DRAFT
**Next Review**: After team approval
**Implementation Start**: Upon approval
