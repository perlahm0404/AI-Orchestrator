# KareMatch Production Completion Plan

**Created**: 2026-01-08
**Scope**: All features to 100% production readiness (excluding E0 Patient Safety)
**Baseline**: ROADMAP.md v2.0 + tracker-2026-build-out.md

---

## Executive Summary

KareMatch is at ~75% overall completion. This plan details the remaining work to reach full production across all epics and infrastructure, organized into 5 phases with 76 discrete tasks.

### Completion Status by Epic

| Epic | Current | Target | Gap | Priority |
|------|---------|--------|-----|----------|
| E0 Patient Safety Entry | 100% | EXCLUDED | - | - |
| E1 Therapist Onboarding | 100% | 100% | 0% | Done |
| E2 Patient Search & Matching | 100% | 100% | 0% | Done |
| E3 Appointment Scheduling | 95% | 100% | 5% | P0 |
| E4 Credentialing System | 95% | 100% | 5% | P1 |
| E5 Content/SEO Platform | 85% | 100% | 15% | P1 |
| E6 Analytics & Reporting | 80%* | 100% | 20% | P2 |
| E7 Sponsor/Advertising | 0% | 100% | 100% | P3 |
| E8 UACC Integration | 0% | 50% | 50% | P2 |
| Remix Migration | 40% | 100% | 60% | P1 |
| Observability | 30% | 90% | 60% | P2 |
| Performance & Caching | 10% | 70% | 60% | P2 |
| Payment Processing | 0% | 80% | 80% | P3 |

*E6 is significantly more complete than roadmap indicates (49 API routes, 4 dashboards exist)

---

## Phase 1: Core Completion (Priority P0)

**Goal**: Complete mission-critical features to 100%

### 1.1 Appointment System Completion (E3) - 5% remaining

#### 1.1.1 Patient Reschedule Flow
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E3-T01 | Create `PUT /api/patient/appointments/:id/reschedule` API | `api/src/routes/patient/appointments.ts` | M |
| E3-T02 | Validate new time slot availability | `services/appointments/src/workflow.ts` | S |
| E3-T03 | Create workflow history entry for reschedule | `services/appointments/src/workflow.ts` | S |
| E3-T04 | Add "Reschedule" button to appointment card | `remix-frontend/app/routes/patient.appointments.$id.tsx` | M |
| E3-T05 | Build available slots picker for reschedule | `remix-frontend/app/components/scheduling/ReschedulePicker.tsx` | M |
| E3-T06 | Add confirmation modal | `remix-frontend/app/components/scheduling/ConfirmReschedule.tsx` | S |

#### 1.1.2 Email Notification Wiring (Infrastructure exists, triggers missing)
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E3-T07 | Wire `appointment.created` event to email trigger | `services/appointments/src/workflow.ts` | S |
| E3-T08 | Wire `appointment.approved` event | `services/appointments/src/workflow.ts` | S |
| E3-T09 | Wire `appointment.rejected` event | `services/appointments/src/workflow.ts` | S |
| E3-T10 | Wire `appointment.cancelled` event | `services/appointments/src/workflow.ts` | S |
| E3-T11 | Wire `appointment.rescheduled` event | `services/appointments/src/workflow.ts` | S |
| E3-T12 | Create booking confirmation email template | `services/communications/src/templates/booking-confirmation.ts` | M |
| E3-T13 | Create appointment approved template | `services/communications/src/templates/appointment-approved.ts` | S |
| E3-T14 | Create appointment rejected template | `services/communications/src/templates/appointment-rejected.ts` | S |
| E3-T15 | Create cancellation notice template | `services/communications/src/templates/cancellation.ts` | S |
| E3-T16 | Create reschedule notice template | `services/communications/src/templates/reschedule.ts` | S |
| E3-T17 | Implement reminder cron Lambda (24h before) | `functions/reminder-cron/handler.ts`, `sst.config.ts` | M |
| E3-T18 | Test email delivery with AWS SES sandbox | - | S |

#### 1.1.3 Calendar Sync (Google + Outlook)
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E3-T19 | Implement Google OAuth flow | `api/src/routes/therapist/calendar.ts` | L |
| E3-T20 | Create Google OAuth callback handler | `api/src/routes/therapist/calendar.ts` | M |
| E3-T21 | Implement Outlook/Microsoft OAuth flow | `api/src/routes/therapist/calendar.ts` | L |
| E3-T22 | Create Outlook OAuth callback handler | `api/src/routes/therapist/calendar.ts` | M |
| E3-T23 | Store encrypted refresh tokens (both providers) | `services/calendar/src/token-storage.ts` | M |
| E3-T24 | Create unified calendar abstraction layer | `services/calendar/src/calendar-provider.ts` | M |
| E3-T25 | Implement Google Calendar read | `services/calendar/src/google-sync.ts` | L |
| E3-T26 | Implement Outlook Calendar read | `services/calendar/src/outlook-sync.ts` | L |
| E3-T27 | Block conflicting times in KareMatch | `services/calendar/src/conflict-detection.ts` | M |
| E3-T28 | Write appointments to Google Calendar | `services/calendar/src/google-sync.ts` | M |
| E3-T29 | Write appointments to Outlook Calendar | `services/calendar/src/outlook-sync.ts` | M |
| E3-T30 | Create calendar settings UI (both providers) | `remix-frontend/app/routes/therapist.settings.calendar.tsx` | M |
| E3-T31 | Handle calendar disconnect/reconnect | `services/calendar/src/calendar-provider.ts` | S |

**E3 Subtotal**: 31 tasks (18 core + 13 calendar sync)

---

### 1.2 Credentialing System Completion (E4) - 5% remaining

#### 1.2.1 Background Check Vendor Integration
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E4-T01 | Evaluate Checkr vs Sterling pricing/API | - | S |
| E4-T02 | Create consent form UI | `remix-frontend/app/routes/therapist.credentialing.background-check.tsx` | M |
| E4-T03 | Create `POST /api/therapist/credentialing/background-check/consent` | `api/src/routes/therapist/credentialing.ts` | M |
| E4-T04 | Implement Checkr API client | `services/credentialing/src/checkr-client.ts` | L |
| E4-T05 | Create `POST /api/therapist/credentialing/background-check/initiate` | `api/src/routes/therapist/credentialing.ts` | M |
| E4-T06 | Create webhook receiver `POST /api/webhooks/checkr/results` | `api/src/routes/webhooks/checkr.ts` | M |
| E4-T07 | Validate webhook signature | `api/src/routes/webhooks/checkr.ts` | S |
| E4-T08 | Update background_check_results table on webhook | `services/credentialing/src/checkr-client.ts` | S |
| E4-T09 | Create status check `GET /api/therapist/credentialing/background-check/status` | `api/src/routes/therapist/credentialing.ts` | S |

#### 1.2.2 Auto-Suspend on Expiration
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E4-T10 | Implement expiration check cron Lambda | `functions/credential-expiration-cron/handler.ts` | M |
| E4-T11 | Query credentials expiring today | `services/credentialing/src/expiration-check.ts` | S |
| E4-T12 | Update profile_status to 'suspended' | `services/credentialing/src/expiration-check.ts` | S |
| E4-T13 | Create audit log entry | `services/credentialing/src/expiration-check.ts` | S |
| E4-T14 | Send notification to therapist | `services/credentialing/src/notifications.ts` | S |
| E4-T15 | Implement reactivation flow | `services/credentialing/src/reactivation.ts` | M |

#### 1.2.3 Bulk Verification Tools
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E4-T16 | Create `POST /api/admin/credentialing/bulk-verify-npi` | `api/src/routes/admin/credentialing.ts` | M |
| E4-T17 | Implement multi-select documents UI | `remix-frontend/app/routes/admin.credentialing._index.tsx` | M |
| E4-T18 | Add "Verify Selected" button with progress | `remix-frontend/app/routes/admin.credentialing._index.tsx` | S |

#### 1.2.4 Credentialing Wizard UI (6 remaining steps)
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E4-T19 | Complete wizard step 5 (DEA) | `remix-frontend/app/routes/therapist.credentialing.dea.tsx` | M |
| E4-T20 | Complete wizard step 6 (Insurance) | `remix-frontend/app/routes/therapist.credentialing.insurance.tsx` | M |
| E4-T21 | Complete wizard step 7 (Background) | `remix-frontend/app/routes/therapist.credentialing.background.tsx` | M |
| E4-T22 | Complete wizard step 8 (References) | `remix-frontend/app/routes/therapist.credentialing.references.tsx` | M |
| E4-T23 | Complete wizard step 9 (Review) | `remix-frontend/app/routes/therapist.credentialing.review.tsx` | M |
| E4-T24 | Complete wizard step 10 (Submit) | `remix-frontend/app/routes/therapist.credentialing.submit.tsx` | S |

**E4 Subtotal**: 24 tasks

---

## Phase 2: SEO & Content Completion (Priority P1)

**Goal**: Complete E5 to drive organic traffic

### 2.1 Content/SEO Platform (E5) - 15% remaining

#### 2.1.1 SEO Metadata Implementation
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E5-T01 | Add meta title/description fields to blog_articles | `data/schema/platform.ts` | S |
| E5-T02 | Create SEO component for meta tags | `remix-frontend/app/components/SEO.tsx` | M |
| E5-T03 | Add Open Graph tags to all pages | `remix-frontend/app/root.tsx` | M |
| E5-T04 | Add Twitter card markup | `remix-frontend/app/root.tsx` | S |
| E5-T05 | Implement canonical URLs | `remix-frontend/app/root.tsx` | S |

#### 2.1.2 Therapist Profile SEO
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E5-T06 | Add Schema.org LocalBusiness JSON-LD | `remix-frontend/app/routes/therapists.$id.tsx` | M |
| E5-T07 | Add Schema.org MedicalBusiness schema | `remix-frontend/app/routes/therapists.$id.tsx` | S |
| E5-T08 | Generate clean URLs from therapist name | `services/matching/src/slug-generator.ts` | M |
| E5-T09 | Dynamic meta tags from profile data | `remix-frontend/app/routes/therapists.$id.tsx` | M |

#### 2.1.3 Sitemap Generation
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E5-T10 | Create sitemap generation script | `scripts/generate-sitemap.ts` | M |
| E5-T11 | Include all public routes | `scripts/generate-sitemap.ts` | S |
| E5-T12 | Include all therapist profiles | `scripts/generate-sitemap.ts` | S |
| E5-T13 | Include all blog articles | `scripts/generate-sitemap.ts` | S |
| E5-T14 | Schedule daily regeneration (cron) | `sst.config.ts` | S |
| E5-T15 | Configure robots.txt | `public/robots.txt` | S |

#### 2.1.4 Location Landing Pages
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E5-T16 | Create city landing page template | `remix-frontend/app/routes/therapists.city.$city.tsx` | M |
| E5-T17 | Add local SEO content to city pages | `remix-frontend/app/routes/therapists.city.$city.tsx` | M |
| E5-T18 | Create state landing page template | `remix-frontend/app/routes/therapists.state.$state.tsx` | M |
| E5-T19 | Generate top 50 metro page seed data | `data/seed/metros.ts` | M |

#### 2.1.5 Blog Enhancements
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E5-T20 | Add featured_image column to blog_articles | `data/schema/platform.ts` | S |
| E5-T21 | Update article editor for featured images | `remix-frontend/app/routes/admin.blog.editor.tsx` | M |
| E5-T22 | Display featured images on article cards | `remix-frontend/app/routes/blog._index.tsx` | S |
| E5-T23 | Add related articles section | `remix-frontend/app/routes/blog.$slug.tsx` | M |

**E5 Subtotal**: 23 tasks

---

## Phase 3: Frontend Unification (Priority P1)

**Goal**: Complete Remix migration, remove legacy React SPA

### 3.1 Remix Migration - 60% remaining (24 routes)

#### 3.1.1 Dashboard Routes (5 remaining)
| Task ID | Description | From | To | Effort |
|---------|-------------|------|-----|--------|
| R-T01 | Migrate dashboard home | `web/src/pages/dashboard/index.tsx` | `remix-frontend/app/routes/dashboard._index.tsx` | M |
| R-T02 | Migrate dashboard settings | `web/src/pages/dashboard/settings.tsx` | `remix-frontend/app/routes/dashboard.settings.tsx` | M |
| R-T03 | Migrate dashboard notifications | `web/src/pages/dashboard/notifications.tsx` | `remix-frontend/app/routes/dashboard.notifications.tsx` | M |
| R-T04 | Migrate dashboard help | `web/src/pages/dashboard/help.tsx` | `remix-frontend/app/routes/dashboard.help.tsx` | S |
| R-T05 | Migrate dashboard billing | `web/src/pages/dashboard/billing.tsx` | `remix-frontend/app/routes/dashboard.billing.tsx` | M |

#### 3.1.2 Therapist Routes (6 remaining)
| Task ID | Description | From | To | Effort |
|---------|-------------|------|-----|--------|
| R-T06 | Migrate therapist clients | `web/src/pages/therapist/clients.tsx` | `remix-frontend/app/routes/therapist.clients._index.tsx` | L |
| R-T07 | Migrate therapist client detail | `web/src/pages/therapist/clients/[id].tsx` | `remix-frontend/app/routes/therapist.clients.$id.tsx` | M |
| R-T08 | Migrate therapist messages | `web/src/pages/therapist/messages.tsx` | `remix-frontend/app/routes/therapist.messages.tsx` | M |
| R-T09 | Migrate therapist earnings | `web/src/pages/therapist/earnings.tsx` | `remix-frontend/app/routes/therapist.earnings.tsx` | M |
| R-T10 | Migrate therapist reviews | `web/src/pages/therapist/reviews.tsx` | `remix-frontend/app/routes/therapist.reviews.tsx` | M |
| R-T11 | Migrate therapist documents | `web/src/pages/therapist/documents.tsx` | `remix-frontend/app/routes/therapist.documents.tsx` | M |

#### 3.1.3 Patient Routes (6 remaining)
| Task ID | Description | From | To | Effort |
|---------|-------------|------|-----|--------|
| R-T12 | Migrate patient messages | `web/src/pages/patient/messages.tsx` | `remix-frontend/app/routes/patient.messages.tsx` | M |
| R-T13 | Migrate patient find therapist | `web/src/pages/patient/find-therapist.tsx` | `remix-frontend/app/routes/patient.find-therapist.tsx` | L |
| R-T14 | Migrate patient favorites | `web/src/pages/patient/favorites.tsx` | `remix-frontend/app/routes/patient.favorites.tsx` | M |
| R-T15 | Migrate patient insurance | `web/src/pages/patient/insurance.tsx` | `remix-frontend/app/routes/patient.insurance.tsx` | M |
| R-T16 | Migrate patient notes | `web/src/pages/patient/notes.tsx` | `remix-frontend/app/routes/patient.notes.tsx` | M |
| R-T17 | Migrate patient history | `web/src/pages/patient/history.tsx` | `remix-frontend/app/routes/patient.history.tsx` | M |

#### 3.1.4 Public Routes (4 remaining)
| Task ID | Description | From | To | Effort |
|---------|-------------|------|-----|--------|
| R-T18 | Migrate about page | `web/src/pages/about.tsx` | `remix-frontend/app/routes/about.tsx` | S |
| R-T19 | Migrate contact page | `web/src/pages/contact.tsx` | `remix-frontend/app/routes/contact.tsx` | S |
| R-T20 | Migrate privacy page | `web/src/pages/privacy.tsx` | `remix-frontend/app/routes/privacy.tsx` | S |
| R-T21 | Migrate terms page | `web/src/pages/terms.tsx` | `remix-frontend/app/routes/terms.tsx` | S |

#### 3.1.5 Admin Routes (3 remaining)
| Task ID | Description | From | To | Effort |
|---------|-------------|------|-----|--------|
| R-T22 | Migrate admin blog editor | `web/src/pages/admin/blog/editor.tsx` | `remix-frontend/app/routes/admin.blog.editor.tsx` | L |
| R-T23 | Migrate admin analytics | `web/src/pages/admin/analytics.tsx` | `remix-frontend/app/routes/admin.analytics.tsx` | M |
| R-T24 | Migrate admin settings | `web/src/pages/admin/settings.tsx` | `remix-frontend/app/routes/admin.settings.tsx` | M |

#### 3.1.6 Cleanup
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| R-T25 | Verify all 24 routes migrated | - | S |
| R-T26 | Remove legacy web/ folder | `web/` | S |
| R-T27 | Update turbo.json workspaces | `turbo.json` | S |
| R-T28 | Update deployment scripts | `package.json`, `sst.config.ts` | S |

**Remix Subtotal**: 28 tasks

---

## Phase 4: Platform Maturity (Priority P2)

**Goal**: Production-grade observability, analytics completion, performance

### 4.1 Observability Stack - 60% remaining

#### 4.1.1 CloudWatch Dashboards
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| O-T01 | Create API health dashboard (request count, error rate, latency) | CloudWatch Console | M |
| O-T02 | Create business metrics dashboard (DAU, bookings, searches) | CloudWatch Console | M |

#### 4.1.2 X-Ray Tracing
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| O-T03 | Add X-Ray SDK to Lambda | `api/src/middleware/tracing.ts` | M |
| O-T04 | Instrument key functions | `api/src/routes/*.ts` | M |
| O-T05 | Create service map | CloudWatch Console | S |
| O-T06 | Add database query tracing | `lib/db/client.ts` | M |

#### 4.1.3 Alerting
| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| O-T07 | Create SNS topics (critical, warning) | `sst.config.ts` | S |
| O-T08 | Create CloudWatch alarms (error rate, latency, 5xx) | `sst.config.ts` | M |
| O-T09 | Create runbooks (high error rate, high latency, DB issues) | `docs/04-operations/runbooks/` | M |

**Observability Subtotal**: 9 tasks

### 4.2 Analytics Dashboard Completion (E6) - 20% remaining

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E6-T01 | Create therapist-facing analytics page | `remix-frontend/app/routes/therapist.analytics.tsx` | L |
| E6-T02 | Add CSV export for all admin dashboards | `api/src/routes/admin/analytics.ts` | M |
| E6-T03 | Add custom date range filter to all queries | `services/analytics/src/*.ts` | M |
| E6-T04 | Implement scheduled report emails | `functions/report-email-cron/handler.ts` | M |

**E6 Subtotal**: 4 tasks

### 4.3 Performance & Caching - 60% remaining

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| P-T01 | Set up ElastiCache Redis cluster | `sst.config.ts` | M |
| P-T02 | Configure security groups for Redis | AWS Console | S |
| P-T03 | Implement search result caching (5 min TTL) | `services/matching/src/cache.ts` | M |
| P-T04 | Implement cache invalidation on profile update | `services/matching/src/cache.ts` | M |
| P-T05 | Move NPI cache to Redis (30-day TTL) | `services/credentialing/src/npi-cache.ts` | M |
| P-T06 | Analyze slow queries with EXPLAIN | - | M |
| P-T07 | Add composite indexes for hot paths | `data/schema/*.ts` | M |
| P-T08 | Optimize therapist search query | `services/matching/src/therapist-matcher.ts` | L |

**Performance Subtotal**: 8 tasks

---

## Phase 5: Integration & Growth Features (Priority P2-P3)

**Goal**: External integrations, monetization foundation

### 5.1 UACC Integration (E8) - Phase 1 Only (50%)

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| E8-T01 | Add uacc_contact_id to users table | `data/schema/identity.ts` | S |
| E8-T02 | Add uacc_contact_id to therapists table | `data/schema/provider.ts` | S |
| E8-T03 | Design event envelope contract | `docs/contracts/event-envelope.schema.json` | M |
| E8-T04 | Implement event publisher service | `services/events/src/publisher.ts` | L |
| E8-T05 | Publish user.registered event | `services/events/src/handlers/user.ts` | M |
| E8-T06 | Publish therapist.created event | `services/events/src/handlers/therapist.ts` | M |
| E8-T07 | Publish appointment.scheduled event | `services/events/src/handlers/appointment.ts` | M |
| E8-T08 | Implement retry queue for failed events | `services/events/src/retry-queue.ts` | M |
| E8-T09 | Implement dead letter handling | `services/events/src/dead-letter.ts` | M |

**E8 Subtotal**: 9 tasks

### 5.2 Payment Processing (M5.2)

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| PAY-T01 | Set up Stripe account and API keys | - | S |
| PAY-T02 | Create Stripe integration client | `services/payments/src/stripe-client.ts` | L |
| PAY-T03 | Implement checkout session creation | `api/src/routes/payments/checkout.ts` | M |
| PAY-T04 | Create payment success/cancel handlers | `api/src/routes/payments/webhooks.ts` | M |
| PAY-T05 | Link payments to appointments | `services/payments/src/appointment-payment.ts` | M |
| PAY-T06 | Implement therapist payout system (Stripe Connect) | `services/payments/src/payouts.ts` | L |
| PAY-T07 | Create invoice generation | `services/payments/src/invoices.ts` | M |
| PAY-T08 | Build payment history UI | `remix-frontend/app/routes/therapist.earnings.tsx` | M |

**Payment Subtotal**: 8 tasks

### 5.3 Sponsor/Advertising Platform (E7) - Future

| Task ID | Description | Priority | Notes |
|---------|-------------|----------|-------|
| E7-T01-T25 | Full advertising platform | P3 | Deferred - requires business model validation |

**Recommendation**: Defer E7 until product-market fit is established for core marketplace. Estimated 25+ tasks for full implementation.

---

## Task Summary

| Phase | Epic/Area | Tasks | Priority |
|-------|-----------|-------|----------|
| 1 | E3 Appointments | 31 | P0 |
| 1 | E4 Credentialing | 24 | P0-P1 |
| 2 | E5 SEO/Content | 23 | P1 |
| 3 | Remix Migration | 28 | P1 |
| 4 | Observability | 9 | P2 |
| 4 | E6 Analytics | 4 | P2 |
| 4 | Performance | 8 | P2 |
| 5 | E8 UACC | 9 | P2 |
| 5 | Payments | 8 | P3 |
| 5 | E7 Sponsors | - | DEFERRED |
| **Total** | | **144** | |

### Effort Distribution

| Size | Definition | Count |
|------|------------|-------|
| S | < 2 hours | ~48 |
| M | 2-4 hours | ~74 |
| L | 4-8 hours | ~18 |
| XL | 8+ hours | ~4 |

---

## Recommended Execution Order

### Sprint 1-2: Core P0
1. E3 email notification wiring (E3-T07 to E3-T18)
2. E3 patient reschedule flow (E3-T01 to E3-T06)
3. E4 credentialing wizard completion (E4-T19 to E4-T24)

### Sprint 3-4: Core P1
1. E4 background check integration (E4-T01 to E4-T09)
2. E4 auto-suspend on expiration (E4-T10 to E4-T15)
3. E5 SEO metadata implementation (E5-T01 to E5-T09)

### Sprint 5-6: SEO & Migration Start
1. E5 sitemap generation (E5-T10 to E5-T15)
2. E5 location landing pages (E5-T16 to E5-T19)
3. Remix migration - public routes (R-T18 to R-T21)
4. Remix migration - dashboard routes (R-T01 to R-T05)

### Sprint 7-8: Migration Completion
1. Remix migration - therapist routes (R-T06 to R-T11)
2. Remix migration - patient routes (R-T12 to R-T17)
3. Remix migration - admin routes (R-T22 to R-T24)
4. Legacy cleanup (R-T25 to R-T28)

### Sprint 9-10: Platform Maturity
1. Observability stack (O-T01 to O-T09)
2. Performance & caching (P-T01 to P-T08)
3. E6 analytics completion (E6-T01 to E6-T04)

### Sprint 11-12: Integrations
1. UACC integration phase 1 (E8-T01 to E8-T09)
2. Payment processing (PAY-T01 to PAY-T08)

### Sprint 13+: Stretch Goals
1. E3 Google Calendar sync (E3-T19 to E3-T25)
2. E7 Sponsor platform (if validated)

---

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Feature Completion | 75% | 95% |
| Test Pass Rate | 78% | 95% |
| Remix Migration | 40% | 100% |
| API Latency p95 | Unknown | <500ms |
| Error Rate | Unknown | <1% |
| SEO Pages Indexed | Unknown | 100% |

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Remix migration complexity | High | Incremental migration, feature flags |
| Background check vendor delays | Medium | Multiple vendor options ready |
| Calendar OAuth complexity | Medium | Start Google-only, add Outlook later |
| Test suite instability | Medium | Continue stabilization in parallel |
| UACC dependency | Medium | Design for eventual consistency |

---

## Decisions Log

| Decision | Choice | Date | Rationale |
|----------|--------|------|-----------|
| Background check vendor | DEFERRED | 2026-01-08 | Proceed with schema/UI work, defer vendor selection |
| E7 Sponsor platform | DEFERRED | 2026-01-08 | Wait for product-market fit validation |
| Calendar sync scope | BOTH (Google + Outlook) | 2026-01-08 | Full feature parity from launch |

---

## Next Actions

1. **Immediate**: Begin E3 email notification wiring (12 tasks)
2. **This Week**: Start E4 credentialing wizard completion (6 tasks)
3. **Calendar Sync**: Plan for both Google AND Outlook OAuth flows
4. **Background Checks**: Build consent UI + status tracking, vendor integration later
5. **Plan**: Set up sprint board with Phase 1 tasks

---

**Document Owner**: Engineering Team
**Review Cycle**: Weekly
**Version**: 1.1
