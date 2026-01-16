---
# Document Metadata
doc-id: "g-plan-product-epics"
title: "Product Epics - KareMatch & CredentialMate Strategic Initiatives"
created: "2026-01-16"
updated: "2026-01-16"
author: "AI Orchestrator"
status: "active"

# Compliance Metadata
compliance:
  soc2:
    controls: ["CC7.3", "CC8.1"]
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.12.1.1", "A.14.2.2"]
    classification: "confidential"
    review-frequency: "quarterly"

# Project Context
project: "global"
domain: "product"
relates-to: ["g-plan-product-prd"]
---

# Product Epics
## KareMatch & CredentialMate Strategic Initiatives

**Document Version**: 1.0
**Date**: 2026-01-16
**Owner**: Product & Engineering
**Status**: Draft

---

## Epic Index

### KareMatch Epics
- [KM-E0: Patient Safety & Identity Foundation](#km-e0-patient-safety--identity-foundation)
- [KM-E1: Therapist Discovery & Matching](#km-e1-therapist-discovery--matching)
- [KM-E2: Credentialing Automation](#km-e2-credentialing-automation)
- [KM-E3: Frontend Migration to Remix](#km-e3-frontend-migration-to-remix)
- [KM-E4: Patient Analytics & Engagement](#km-e4-patient-analytics--engagement)
- [KM-E5: Calendar Integration & Scheduling](#km-e5-calendar-integration--scheduling)
- [KM-E6: Payment Processing & Revenue](#km-e6-payment-processing--revenue)
- [KM-E7: Telehealth & Video Consultations](#km-e7-telehealth--video-consultations)

### CredentialMate Epics
- [CM-E1: Multi-Provider Support (Phase 2)](#cm-e1-multi-provider-support-phase-2)
- [CM-E2: Collaboration System (Phase 3)](#cm-e2-collaboration-system-phase-3)
- [CM-E3: Enterprise Features & API Platform](#cm-e3-enterprise-features--api-platform)
- [CM-E4: State Board Integration](#cm-e4-state-board-integration)
- [CM-E5: AI Processing Pipeline Optimization](#cm-e5-ai-processing-pipeline-optimization)
- [CM-E6: Revenue & Subscription Management (Phase 4)](#cm-e6-revenue--subscription-management-phase-4)

### Shared Infrastructure Epics
- [SI-E1: HIPAA Compliance & Security Hardening](#si-e1-hipaa-compliance--security-hardening)
- [SI-E2: Performance & Scalability](#si-e2-performance--scalability)
- [SI-E3: Observability & Alerting](#si-e3-observability--alerting)
- [SI-E4: Multi-Region Disaster Recovery](#si-e4-multi-region-disaster-recovery)

---

## KareMatch Epics

### KM-E0: Patient Safety & Identity Foundation
**Epic ID**: KM-E0
**Priority**: P0 (Critical)
**Status**: 60% Complete

#### Description
Complete the patient safety foundation including crisis intercept, identity verification, rate limiting, and CAPTCHA to prevent bot abuse and ensure patient protection before therapist contact.

#### Business Value
- Reduce liability risk by intercepting crisis situations
- Prevent bot abuse and spam (security)
- Build trust with patients (safety-first approach)
- Regulatory compliance (duty to warn, crisis protocols)

#### Acceptance Criteria
- [ ] Fix event type enum mismatch (`crisis_intercept_displayed` added to database)
- [ ] Fix consent logging FK violation (allow anonymous users to log consent)
- [ ] Wire crisis intercept UI to all patient entry points
- [ ] Implement rate limiting (1000 req/min per user, 100 req/min per IP)
- [ ] Implement CAPTCHA on registration and search forms
- [ ] Wire identity gate UI to onboarding routes
- [ ] All safety tests passing (E2E crisis flow)

#### Dependencies
- Database migration (add event type)
- Frontend routing (wire identity gate)

#### Estimated Effort
- Engineering: 2 weeks (1 backend, 1 frontend)
- QA: 1 week (E2E safety testing)
- Legal review: 1 week (crisis protocol validation)

---

### KM-E1: Therapist Discovery & Matching
**Epic ID**: KM-E1
**Priority**: P0 (Critical)
**Status**: 75% Complete

#### Description
Fix proximity matching SQL bug, wire matching explainability UI, and optimize search performance to deliver deterministic, transparent therapist matching.

#### Business Value
- Improve patient-therapist fit (reduce drop-off)
- Increase trust through explainability (show why match scored highest)
- Reduce search-to-contact friction (proximity filtering works)
- SEO advantage (better match quality = better retention)

#### Acceptance Criteria
- [ ] Fix proximity matching SQL distance calculation (returns valid results)
- [ ] Wire matching explainability UI (show match score breakdown)
- [ ] Add Redis caching for directory queries (<100ms P95)
- [ ] Implement search result ranking (relevance + proximity + availability)
- [ ] All matching tests passing (unit + integration)

#### Dependencies
- Database query optimization
- Frontend matching UI components

#### Estimated Effort
- Engineering: 2 weeks (1 backend, 0.5 frontend, 0.5 DevOps)
- QA: 1 week (matching algorithm validation)

---

### KM-E2: Credentialing Automation
**Epic ID**: KM-E2
**Priority**: P1 (High)
**Status**: 95% Complete

#### Description
Complete credentialing automation by integrating background check vendors (Checkr/Sterling) and automating license expiration tracking with suspension workflows.

#### Business Value
- Achieve 100% credentialing automation (currently 95%)
- Reduce therapist onboarding time (7 days → 3 days)
- Eliminate compliance risk (no un-credentialed therapists visible)
- Competitive advantage (fastest onboarding in industry)

#### Acceptance Criteria
- [ ] Integrate Checkr or Sterling API for background checks
- [ ] Automate license expiration suspension workflow
- [ ] Add expiration alert notifications (60/30/14/7 days)
- [ ] Implement bulk credential verification tools
- [ ] Admin dashboard shows credential status in real-time
- [ ] All credentialing tests passing (E2E)

#### Dependencies
- Checkr/Sterling API access and credentials
- Email notification system (already exists)

#### Estimated Effort
- Engineering: 3 weeks (2 backend, 0.5 frontend, 0.5 DevOps)
- QA: 1 week (credentialing workflow validation)
- Vendor onboarding: 1 week (Checkr/Sterling setup)

---

### KM-E3: Frontend Migration to Remix
**Epic ID**: KM-E3
**Priority**: P1 (High)
**Status**: 40% Complete

#### Description
Complete migration from React SPA to Remix (React Router v7 SSR) to improve SEO, page load performance, and developer experience.

#### Business Value
- Improve SEO rankings (SSR for all pages)
- Faster page loads (server rendering)
- Reduce JavaScript bundle size (code splitting)
- Better developer experience (file-based routing)

#### Acceptance Criteria
- [ ] Migrate all pages from React SPA to Remix App Router
- [ ] Implement SSR for all public pages (SEO)
- [ ] Migrate all API routes to Remix loaders/actions
- [ ] Remove legacy React SPA build artifacts
- [ ] All frontend tests passing (E2E + unit)
- [ ] Lighthouse score >90 for all pages

#### Dependencies
- None (isolated frontend work)

#### Estimated Effort
- Engineering: 6 weeks (2 frontend engineers)
- QA: 2 weeks (E2E regression testing)

---

### KM-E4: Patient Analytics & Engagement
**Epic ID**: KM-E4
**Priority**: P2 (Medium)
**Status**: 40% Complete

#### Description
Build patient engagement analytics including funnel visualization, retention metrics, and therapist booking rate dashboards to drive product decisions.

#### Business Value
- Data-driven product decisions (identify drop-off points)
- Measure marketing effectiveness (funnel attribution)
- Optimize therapist matching (booking rate by specialty)
- Investor reporting (engagement metrics)

#### Acceptance Criteria
- [ ] Implement patient funnel visualization (search → profile → contact → booking)
- [ ] Build retention cohort analysis (6-month retention)
- [ ] Add therapist booking rate metrics
- [ ] Implement A/B testing framework (for matching algorithm)
- [ ] Build admin analytics dashboard (patient metrics)

#### Dependencies
- Event logging system (already exists)
- Analytics database (consider separate read replica)

#### Estimated Effort
- Engineering: 3 weeks (1 backend, 1 frontend, 0.5 data analyst)
- QA: 1 week (analytics validation)

---

### KM-E5: Calendar Integration & Scheduling
**Epic ID**: KM-E5
**Priority**: P2 (Medium)
**Status**: 10% Complete

#### Description
Implement Google Calendar OAuth/sync to enable therapists to sync availability and automatically block booked appointments.

#### Business Value
- Reduce therapist double-booking (manual sync eliminated)
- Improve therapist satisfaction (automation)
- Increase booking conversion (real-time availability)
- Competitive parity (Psychology Today has this)

#### Acceptance Criteria
- [ ] Implement Google Calendar OAuth flow
- [ ] Sync therapist availability to/from Google Calendar
- [ ] Auto-block booked appointments in KareMatch
- [ ] Handle cancellations and reschedules bidirectionally
- [ ] Support recurring availability templates
- [ ] All calendar tests passing (E2E)

#### Dependencies
- Google Calendar API access and credentials
- OAuth consent screen approval

#### Estimated Effort
- Engineering: 4 weeks (2 backend, 1 frontend)
- QA: 1 week (calendar sync validation)

---

### KM-E6: Payment Processing & Revenue
**Epic ID**: KM-E6
**Priority**: P3 (Future)
**Status**: 0% Complete

#### Description
Implement Stripe payment processing to enable therapist subscription billing or commission-per-booking revenue model.

#### Business Value
- Enable revenue generation (currently no monetization)
- Support therapist payouts (commission model)
- Enable subscription management (SaaS model)
- Investor milestone (revenue-generating product)

#### Acceptance Criteria
- [ ] Integrate Stripe Connect for therapist payouts
- [ ] Implement subscription management (monthly/annual plans)
- [ ] Build billing dashboard for therapists
- [ ] Support commission-per-booking model (10-20%)
- [ ] Implement refund workflows
- [ ] All payment tests passing (E2E)

#### Dependencies
- Business model decision (subscription vs. commission)
- Stripe account and API keys
- Tax/legal consultation (1099 reporting)

#### Estimated Effort
- Engineering: 5 weeks (2 backend, 1 frontend, 1 DevOps)
- QA: 1 week (payment workflow validation)
- Legal/tax review: 2 weeks

---

### KM-E7: Telehealth & Video Consultations
**Epic ID**: KM-E7
**Priority**: P3 (Future)
**Status**: 0% Complete

#### Description
Implement HIPAA-compliant video consultations to enable remote therapy sessions (expand from in-person only).

#### Business Value
- Expand addressable market (remote therapy)
- Increase booking conversion (no geographic constraints)
- Competitive advantage (end-to-end platform)
- COVID-era expectations (patients expect telehealth)

#### Acceptance Criteria
- [ ] Integrate HIPAA-compliant video platform (Twilio, Zoom Healthcare, or Daily.co)
- [ ] Build video consultation UI (waiting room, in-session controls)
- [ ] Implement session recording (with consent)
- [ ] Support screen sharing (for therapy worksheets)
- [ ] Add teletherapy licensing validation (cross-state rules)
- [ ] All video tests passing (E2E)

#### Dependencies
- HIPAA-compliant video vendor selection
- Legal review (teletherapy licensing across states)
- BAA (Business Associate Agreement) with vendor

#### Estimated Effort
- Engineering: 6 weeks (2 backend, 2 frontend, 1 DevOps)
- QA: 2 weeks (video workflow validation)
- Legal review: 2 weeks

---

## CredentialMate Epics

### CM-E1: Multi-Provider Support (Phase 2)
**Epic ID**: CM-E1
**Priority**: P0 (Critical)
**Status**: 20% Complete

#### Description
Expand platform to support Nurse Practitioners (NP) and Physician Assistants (PA) with state-specific CME rules, credential tracking, and compliance dashboards.

#### Business Value
- 4x addressable market (MD/DO → all provider types)
- Competitive advantage (most competitors MD-only)
- Revenue growth (expand TAM from 1M to 4M providers)
- Customer demand (50+ customer requests)

#### Acceptance Criteria
- [ ] Implement NP credential tracking (50-state CME rules)
- [ ] Implement PA credential tracking (50-state CME rules)
- [ ] Add CRNA, CNM, CNS credential types
- [ ] Build provider-specific compliance dashboards
- [ ] Update AI document classification for NP/PA credentials
- [ ] All multi-provider tests passing (E2E)

#### Dependencies
- NP/PA CME rules research (50 states)
- Database migrations (add credential types)

#### Estimated Effort
- Engineering: 4 weeks (2 backend, 1 frontend, 0.5 data analyst)
- QA: 1 week (multi-provider validation)
- Research: 1 week (CME rules compilation)

---

### CM-E2: Collaboration System (Phase 3)
**Epic ID**: CM-E2
**Priority**: P1 (High)
**Status**: 0% Complete

#### Description
Build NP-physician collaboration tracking system including supervised practice hours, state-specific oversight requirements, and progression-to-independence workflows.

#### Business Value
- Unlock NP market (cannot work independently in 20+ states)
- Competitive moat (no competitor has this)
- Revenue opportunity (oversight payment routing)
- Legal compliance (state-mandated collaboration agreements)

#### Acceptance Criteria
- [ ] Implement NP-physician collaboration agreements
- [ ] Track supervised practice hours (state-specific requirements)
- [ ] Build oversight requirement dashboards
- [ ] Implement progression-to-independence workflows
- [ ] Generate audit packages for state boards
- [ ] Support oversight payment routing (revenue share)
- [ ] All collaboration tests passing (E2E)

#### Dependencies
- Legal research (50-state collaboration requirements)
- Payment processing (Stripe integration)

#### Estimated Effort
- Engineering: 6 weeks (3 backend, 2 frontend)
- QA: 2 weeks (collaboration workflow validation)
- Legal research: 2 weeks (state requirement compilation)

---

### CM-E3: Enterprise Features & API Platform
**Epic ID**: CM-E3
**Priority**: P1 (High)
**Status**: 5% Complete

#### Description
Build enterprise features including API rate limiting, webhook integrations, advanced search, and analytics dashboards to enable enterprise sales motion.

#### Business Value
- Enable enterprise sales (100+ provider organizations)
- Increase ARPU (API access premium feature)
- Competitive parity (larger competitors have APIs)
- Developer ecosystem (third-party integrations)

#### Acceptance Criteria
- [ ] Implement API rate limiting (1000 req/min per org)
- [ ] Build webhook system (credential expiration, compliance events)
- [ ] Add advanced search (Elasticsearch or Algolia)
- [ ] Build enterprise analytics dashboards
- [ ] Implement API key management
- [ ] Create developer documentation and sandbox
- [ ] All API tests passing (contract tests)

#### Dependencies
- Elasticsearch infrastructure (or Algolia account)
- Webhook delivery infrastructure (retries, DLQ)

#### Estimated Effort
- Engineering: 6 weeks (3 backend, 1 frontend, 1 DevOps)
- Technical writing: 2 weeks (API documentation)

---

### CM-E4: State Board Integration
**Epic ID**: CM-E4
**Priority**: P2 (Medium)
**Status**: 0% Complete

#### Description
Integrate with state medical board APIs for automated license verification, expiration tracking, and compliance reconciliation (pilot with 10 states, expand to 50).

#### Business Value
- Eliminate manual data entry (80% time savings)
- Real-time compliance (no lag from manual updates)
- Competitive moat (exclusive board integrations)
- Data quality improvement (source of truth)

#### Acceptance Criteria
- [ ] Pilot integration with 10 state boards (CA, TX, FL, NY, IL, PA, OH, GA, NC, MI)
- [ ] Automate license verification (API polling)
- [ ] Implement expiration tracking (real-time sync)
- [ ] Build reconciliation workflows (detect discrepancies)
- [ ] Expand to all 50 states + DC
- [ ] All board integration tests passing (E2E)

#### Dependencies
- State board API access (varies by state)
- Legal agreements (data sharing, BAAs)

#### Estimated Effort
- Engineering: 8 weeks (3 backend, 1 DevOps)
- Legal/compliance: 4 weeks (board negotiations, BAAs)
- Ongoing maintenance: 1 engineer (integration monitoring)

---

### CM-E5: AI Processing Pipeline Optimization
**Epic ID**: CM-E5
**Priority**: P2 (Medium)
**Status**: 30% Complete

#### Description
Optimize AI document processing pipeline including chunked uploads, confidence threshold auto-approval, extraction accuracy monitoring, and cost reduction.

#### Business Value
- Reduce manual review burden (80% → 95% auto-approval)
- Support large file uploads (>100MB PDFs)
- Reduce AI costs (optimize prompts, model selection)
- Improve extraction accuracy (95% → 98%)

#### Acceptance Criteria
- [ ] Implement chunked/resumable file uploads (support >100MB files)
- [ ] Add confidence threshold auto-approval (>95% confidence = auto-approve)
- [ ] Build extraction accuracy dashboards (track drift)
- [ ] Optimize AI prompts (reduce token usage by 30%)
- [ ] Evaluate alternative AI models (Claude, Gemini vs. GPT-4)
- [ ] All AI pipeline tests passing (accuracy benchmarks)

#### Dependencies
- S3 multipart upload support
- AI model evaluation (benchmark dataset)

#### Estimated Effort
- Engineering: 4 weeks (2 backend, 1 ML engineer, 0.5 frontend)
- QA: 2 weeks (accuracy validation, benchmarking)

---

### CM-E6: Revenue & Subscription Management (Phase 4)
**Epic ID**: CM-E6
**Priority**: P3 (Future)
**Status**: 0% Complete

#### Description
Implement Stripe subscription management, oversight payment routing, enterprise licensing, and revenue dashboards to enable sustainable business model.

#### Business Value
- Enable revenue generation (currently no monetization)
- Support oversight payment routing (10-20% take rate)
- Enterprise licensing (seat-based pricing)
- Investor milestone (revenue-generating product)

#### Acceptance Criteria
- [ ] Integrate Stripe subscription management
- [ ] Implement oversight payment routing (NP-physician revenue share)
- [ ] Build enterprise licensing (seat-based pricing)
- [ ] Create billing dashboards for customers
- [ ] Implement usage-based pricing (per-provider tiers)
- [ ] All payment tests passing (E2E)

#### Dependencies
- Business model decision (pricing tiers)
- Stripe account and API keys
- Tax/legal consultation (revenue recognition)

#### Estimated Effort
- Engineering: 6 weeks (3 backend, 1 frontend, 1 DevOps)
- QA: 2 weeks (payment workflow validation)
- Legal/tax review: 2 weeks

---

## Shared Infrastructure Epics

### SI-E1: HIPAA Compliance & Security Hardening
**Epic ID**: SI-E1
**Priority**: P0 (Critical)
**Status**: 60% Complete

#### Description
Complete HIPAA compliance requirements including field-level encryption, MFA, penetration testing, audit log retention, and BAA documentation.

#### Business Value
- Regulatory compliance (HIPAA, HITECH)
- Risk mitigation (avoid $50K-$1.5M fines)
- Customer trust (enterprise requirement)
- Competitive advantage (SOC 2 Type II certification)

#### Acceptance Criteria
- [ ] Implement field-level encryption for PII (SSN, NPI, DEA)
- [ ] Add MFA requirement for all users
- [ ] Implement automated penetration testing in CI/CD
- [ ] Add audit log retention automation (7-year window, auto-archive)
- [ ] Create HIPAA BAA documentation
- [ ] Conduct third-party HIPAA audit
- [ ] All security tests passing (penetration test findings remediated)

#### Dependencies
- Security tools (OWASP ZAP, Burp Suite)
- Third-party audit firm (engagement)

#### Estimated Effort
- Engineering: 4 weeks (2 backend, 1 DevOps, 1 security engineer)
- Security audit: 2 weeks (third-party firm)
- Legal review: 1 week (BAA documentation)

---

### SI-E2: Performance & Scalability
**Epic ID**: SI-E2
**Priority**: P1 (High)
**Status**: 30% Complete

#### Description
Optimize system performance including Lambda cold start reduction, query optimization, Redis caching, CDN caching headers, and database indexing.

#### Business Value
- Improve user experience (faster page loads)
- Reduce infrastructure costs (optimize Lambda usage)
- Support scale (10,000+ concurrent users)
- Competitive advantage (fastest platform)

#### Acceptance Criteria
- [ ] Optimize Lambda cold start (<2s, target <1s)
- [ ] Implement Redis caching layer (directory queries, compliance checks)
- [ ] Add database query optimization (materialized views, indexes)
- [ ] Implement CDN caching headers (static assets, API responses)
- [ ] Add database read replicas (separate analytics queries)
- [ ] All performance tests passing (load testing, P95 <500ms)

#### Dependencies
- Redis ElastiCache infrastructure
- Load testing tools (k6, Locust)

#### Estimated Effort
- Engineering: 6 weeks (2 backend, 1 database engineer, 1 DevOps)
- QA: 2 weeks (load testing, benchmarking)

---

### SI-E3: Observability & Alerting
**Epic ID**: SI-E3
**Priority**: P1 (High)
**Status**: 40% Complete

#### Description
Build comprehensive observability including error tracking, performance monitoring, proactive alerting, and automated incident response.

#### Business Value
- Reduce MTTR (mean time to resolution)
- Proactive issue detection (before customers report)
- Improve reliability (SLA monitoring)
- Customer trust (uptime transparency)

#### Acceptance Criteria
- [ ] Integrate PagerDuty for alerting
- [ ] Build CloudWatch dashboards (API latency, error rates, Lambda metrics)
- [ ] Implement automated error alerting (error rate spikes)
- [ ] Add custom metrics (business KPIs, queue depth)
- [ ] Create runbooks for common incidents
- [ ] All monitoring tests passing (alerting validation)

#### Dependencies
- PagerDuty account and integration
- CloudWatch Logs Insights queries

#### Estimated Effort
- Engineering: 3 weeks (1 backend, 1 DevOps, 0.5 frontend)
- Documentation: 1 week (runbooks)

---

### SI-E4: Multi-Region Disaster Recovery
**Epic ID**: SI-E4
**Priority**: P3 (Future)
**Status**: 0% Complete

#### Description
Implement multi-region disaster recovery architecture including cross-region database replication, failover automation, and RTO/RPO validation.

#### Business Value
- Business continuity (survive regional outages)
- SLA improvement (99.9% → 99.99% uptime)
- Customer requirement (enterprise contracts)
- Competitive advantage (HA architecture)

#### Acceptance Criteria
- [ ] Implement cross-region RDS replication (us-east-1 → us-west-2)
- [ ] Add Route53 health checks and failover
- [ ] Build automated failover workflows (Lambda, Step Functions)
- [ ] Validate RTO/RPO targets (RTO <30 min, RPO <5 min)
- [ ] Create disaster recovery runbook
- [ ] All DR tests passing (quarterly failover drills)

#### Dependencies
- AWS multi-region architecture design
- Cost approval (2x infrastructure)

#### Estimated Effort
- Engineering: 6 weeks (2 backend, 2 DevOps)
- Documentation: 2 weeks (DR runbook)
- Ongoing: Quarterly DR drills

---

## Epic Prioritization Matrix

| Epic ID | Epic Name | Priority | Effort | Business Impact |
|---------|-----------|----------|--------|-----------------|
| KM-E0 | Patient Safety | P0 | 4 weeks | Critical (liability) |
| KM-E1 | Matching | P0 | 3 weeks | Critical (core UX) |
| SI-E1 | HIPAA Compliance | P0 | 6 weeks | Critical (legal) |
| KM-E2 | Credentialing | P1 | 4 weeks | High (competitive) |
| CM-E1 | Multi-Provider | P0 | 6 weeks | Critical (TAM) |
| KM-E3 | Remix Migration | P1 | 8 weeks | High (SEO) |
| SI-E2 | Performance | P1 | 8 weeks | High (UX) |
| CM-E3 | Enterprise API | P1 | 8 weeks | High (revenue) |
| SI-E3 | Observability | P1 | 4 weeks | High (reliability) |
| CM-E2 | Collaboration | P1 | 8 weeks | High (NP market) |
| KM-E4 | Analytics | P2 | 4 weeks | Medium (product) |
| KM-E5 | Calendar | P2 | 5 weeks | Medium (UX) |
| CM-E4 | State Boards | P2 | 12 weeks | Medium (moat) |
| CM-E5 | AI Pipeline | P2 | 6 weeks | Medium (cost) |
| KM-E6 | Payments | P3 | 6 weeks | Future (revenue) |
| CM-E6 | Revenue | P3 | 8 weeks | Future (revenue) |
| KM-E7 | Telehealth | P3 | 8 weeks | Future (TAM) |
| SI-E4 | Multi-Region | P3 | 8 weeks | Future (enterprise) |

---

## Success Metrics by Epic

| Epic ID | Key Metric | Target | Measurement |
|---------|------------|--------|-------------|
| KM-E0 | Crisis intercept rate | >95% | Event logging |
| KM-E1 | Match satisfaction | >80% | Patient survey |
| KM-E2 | Time-to-credential | <3 days | Admin dashboard |
| KM-E3 | Lighthouse score | >90 | Automated testing |
| KM-E4 | Conversion rate improvement | +10% | A/B testing |
| KM-E5 | Double-booking incidents | 0 | Error logs |
| KM-E6 | Revenue per therapist | $50/month | Billing dashboard |
| KM-E7 | Telehealth adoption | 30% | Usage analytics |
| CM-E1 | NP/PA credential count | 10,000 | Database query |
| CM-E2 | Oversight agreement count | 5,000 | Database query |
| CM-E3 | API adoption rate | 20% | Usage metrics |
| CM-E4 | State board coverage | 50 states | Integration status |
| CM-E5 | AI accuracy | >98% | Accuracy dashboard |
| CM-E6 | Revenue per org | $1,000/month | Billing dashboard |
| SI-E1 | Security audit score | 100% | Third-party audit |
| SI-E2 | Lambda cold start | <1s | CloudWatch metrics |
| SI-E3 | MTTR | <30 min | PagerDuty metrics |
| SI-E4 | Failover time | <30 min | DR drill results |

---

**Document Status**: Draft - Awaiting Review
**Next Steps**:
1. Review with product and engineering teams
2. Prioritize Q1 epics and create sprint plans
3. Assign epic owners and DRIs (Directly Responsible Individuals)
4. Create detailed user stories for each epic
5. Schedule kickoff meetings for Q1 epics

**Contact**: For questions or epic assignment, contact the product team.
