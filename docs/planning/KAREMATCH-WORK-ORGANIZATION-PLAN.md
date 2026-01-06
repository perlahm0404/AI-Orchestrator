# KareMatch Work Organization Plan
## Coordinating Feature Development While AI Brain Handles QA

**Date**: 2026-01-06
**Status**: DRAFT - Awaiting Approval

---

## Executive Summary

KareMatch has significant incomplete work across 10+ features while the AI Brain runs bugfixes/QA on current code. This plan establishes **parallel workstreams** that don't conflict:

- **AI Brain** → QA/bugfixes on stable code (test infrastructure, lint, type errors)
- **Human Development** → New features on feature branches (isolated from QA)

---

## Current State Analysis

### AI Brain Scope (Automated QA)
| Category | Count | Status |
|----------|-------|--------|
| Verified bugs (VERIFIED-BUGS.md) | 10 | 4 trivial, 4 medium, 2 complex |
| Console.error removals (bugs_to_fix.json) | 4 | Ready for batch processing |
| Test failures to fix | 72 | ~45 stub tests, ~27 unit tests |
| Lint/typecheck issues | Ongoing | Ralph verification |

### Human Development Scope (Incomplete Features)
| Feature | Build Status | Effort | Priority |
|---------|-------------|--------|----------|
| **Matching Algorithm** | 20% (stubbed) | High | P0 - Core value prop |
| **Admin Dashboard** | 30% (8 TODOs) | Medium | P1 - Operations |
| **Credentialing Integration** | 60% (APIs stubbed) | High | P1 - Compliance |
| **Email Notifications** | 40% (6 TODOs) | Low | P2 - UX polish |
| **Proximity Matching** | Broken | Medium | P1 - Search quality |
| **Patient Engagement** | Stubbed | Medium | P2 - Retention |
| **SEO/Content** | 40% (static only) | Low | P3 - Growth |
| **Rate Limiting** | 0% | Low | P3 - Security |

---

## Recommended Work Organization

### Principle: **Parallel Streams, No Conflicts**

```
main branch
    │
    ├──► AI Brain (bugfix/qa)         Human Development (features)
    │    │                             │
    │    ├─ lint fixes                 ├─ feature/matching-algorithm
    │    ├─ type errors                ├─ feature/admin-dashboard
    │    ├─ test infrastructure        ├─ feature/credentialing-api
    │    ├─ accessibility              └─ feature/proximity-search
    │    └─ console.error cleanup
    │
    └──► Merge Points: Weekly integration after Ralph verification
```

### Stream 1: AI Brain QA (Autonomous)

**What AI Brain handles:**
1. Fix 72 test failures (test infrastructure)
2. Process VERIFIED-BUGS.md (10 bugs across 4 sprints)
3. Remove console.error statements (4 in bugs_to_fix.json)
4. Lint/typecheck enforcement via Ralph
5. Accessibility fixes (keyboard handlers, ARIA)

**Boundaries:**
- Works on `main` or `fix/*` branches
- Ralph must PASS before merge
- No behavior changes (test count stays same)
- Max 100 lines/commit, 5 files/PR

### Stream 2: Human Feature Development (Manual)

**Recommended Priority Order:**

#### P0 - Core Value (Matching Algorithm)
**Why**: The matching algorithm is the product's core value prop. Everything else is secondary.

| Task | Files | Effort |
|------|-------|--------|
| Implement deterministic matching logic | `services/matching/src/routes.ts` | 2-3 days |
| Fix proximity matching (returns null) | `services/matching/src/therapist-matcher.ts` | 1 day |
| Add match explainability | New component | 1 day |
| Zero-match UX | New component | 0.5 days |

**Branch**: `feature/matching-algorithm`

#### P1 - Operations (Admin Dashboard)
**Why**: Ops team needs visibility into therapist approvals, credentialing status.

| Task | Files | TODOs |
|------|-------|-------|
| Implement approval history tracking | `services/admin/src/routes.ts` | TODO present |
| Dashboard summary from patient-engagement | `services/admin/src/routes.ts` | TODO present |
| Escalations list | `services/admin/src/routes.ts` | TODO present |
| Activity tracking system | `services/admin/src/routes.ts` | TODO present |
| Send approval/rejection emails | `services/admin/src/therapist-management.ts` | 2 TODOs |

**Branch**: `feature/admin-dashboard`

#### P1 - Compliance (Credentialing APIs)
**Why**: HIPAA compliance requires verified credentials.

| Task | Files | TODOs |
|------|-------|-------|
| NPPES API integration (NPI verification) | `services/credentialing/src/routes.ts` | 2 TODOs |
| DEA validation API | `services/credentialing/src/routes.ts` | 2 TODOs |
| OIG check API | `services/credentialing/src/routes.ts` | TODO present |
| Document storage (Supabase) | `services/credentialing/src/document-storage.ts` | 3 TODOs |

**Branch**: `feature/credentialing-api`

#### P2 - UX Polish (Email Notifications)
**Why**: Users expect confirmation emails. Lower priority than core features.

| Task | Files | TODOs |
|------|-------|-------|
| Appointment confirmation emails | `services/appointments/src/routes.ts` | 3 TODOs |
| Auth notification emails | `services/auth/src/routes.ts` | 2 TODOs |
| Credentialing status emails | `services/credentialing/src/emailService.ts` | TODO present |

**Branch**: `feature/email-notifications`

#### P3 - Growth/Security (Defer)
- SEO metadata/sitemap (can wait for traffic)
- Rate limiting (low risk currently)
- Sponsor advertising (no immediate revenue need)

---

## Work Isolation Strategy

### How to Avoid Conflicts

1. **AI Brain stays out of feature files**
   - Only touches files with lint/type/test issues
   - Never modifies business logic
   - Uses `fix/*` branch naming

2. **Human development uses feature branches**
   - All new work on `feature/*` branches
   - Long-lived branches (1-2 weeks)
   - Rebases weekly from main after AI Brain merges

3. **Weekly Integration Points**
   - AI Brain PRs merged after Ralph PASS
   - Feature branches rebase on updated main
   - Resolve any conflicts at rebase time

### Conflict Prevention Matrix

| File Area | AI Brain | Human Dev |
|-----------|----------|-----------|
| `services/matching/` | Test mocks only | Full implementation |
| `services/admin/` | Lint/type only | New routes |
| `services/credentialing/` | Existing code QA | API integration |
| `web/src/components/` | A11y fixes | New components |
| `web/src/pages/` | Lint fixes | New pages |
| `tests/` | Infrastructure fixes | New tests |

---

## Recommended Sprint Structure

### Sprint 1 (Week 1): Matching Algorithm Foundation
**Human**: Implement core matching logic + proximity fix
**AI Brain**: Fix 72 test failures (parallel)

### Sprint 2 (Week 2): Admin + Integration
**Human**: Admin dashboard + credentialing API stubs
**AI Brain**: Process VERIFIED-BUGS.md (10 bugs)

### Sprint 3 (Week 3): Polish + Hardening
**Human**: Email notifications + remaining TODOs
**AI Brain**: Console.error cleanup + accessibility

### Sprint 4 (Week 4): Stabilization
**Human**: Testing new features end-to-end
**AI Brain**: Coverage improvements

---

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Test failures | 0 | `npx vitest run` |
| Lint issues | 0 | `npm run lint` |
| Type errors | 0 | `npm run check` |
| Matching algorithm | Functional | E2E test passing |
| Admin dashboard | Operational | Manual QA |
| Feature branch conflicts | <5 per sprint | Git merge analysis |

---

## Implementation Checklist

### Immediate Actions (Today)
- [ ] Create `feature/matching-algorithm` branch
- [ ] AI Brain continues test infrastructure fixes
- [ ] Set up weekly integration meeting

### This Week
- [ ] Complete deterministic matching logic
- [ ] AI Brain: Fix 45 stub tests
- [ ] First integration point (Friday)

### This Month
- [ ] All P0/P1 features implemented
- [ ] AI Brain: All VERIFIED-BUGS.md complete
- [ ] Test failures at 0

---

## Open Questions

1. **Matching Algorithm Design**: What scoring weights should be used? (Need product input)
2. **Credentialing APIs**: Which external APIs are approved? (NPPES is free, others may cost)
3. **Admin Access Control**: Who can approve/reject therapists? (Need role definitions)

---

## Summary

| Stream | Owner | Focus | Branch Pattern |
|--------|-------|-------|----------------|
| QA/Bugfixes | AI Brain | Test infra, lint, types, a11y | `fix/*`, `main` |
| Core Features | Human | Matching, Admin, Credentials | `feature/*` |
| Integration | Both | Weekly merges | main after Ralph PASS |

**Key Principle**: AI Brain improves code quality on stable code while humans build new features on isolated branches. Weekly integration prevents drift.
