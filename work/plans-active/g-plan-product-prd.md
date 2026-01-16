---
# Document Metadata
doc-id: "g-plan-product-prd"
title: "Product Requirements Document - Healthcare Compliance Platform"
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
relates-to: ["g-plan-product-epics"]
---

# Product Requirements Document (PRD)
## Healthcare Compliance Platform - KareMatch & CredentialMate

**Document Version**: 1.0
**Date**: 2026-01-16
**Owner**: Product Team
**Status**: Draft

---

## Executive Summary

This PRD outlines the strategic direction for two healthcare SaaS applications: **KareMatch** (patient-therapist marketplace) and **CredentialMate** (provider credential management). Both applications serve the healthcare compliance and access market with complementary value propositions:

- **KareMatch**: Connects patients with vetted mental health therapists through intelligent matching, HIPAA-compliant booking, and comprehensive credentialing workflows
- **CredentialMate**: Eliminates credentialing chaos through AI-powered document processing, multi-state license tracking, and automated compliance monitoring

### Key Metrics
- **KareMatch**: 75% feature complete, 95% credentialing automation, 80% test coverage
- **CredentialMate**: 95% Phase 1 (MD/DO) complete, 457x query performance improvement, HIPAA-compliant

---

## 1. Product Vision

### Mission Statement
**Simplify healthcare access and compliance through intelligent automation, reducing administrative burden while maintaining the highest standards of patient safety and regulatory compliance.**

### Strategic Goals
1. **Reduce Time-to-Care**: Connect patients with therapists in <48 hours (vs. industry average 2-3 weeks)
2. **Eliminate Compliance Risk**: Automate 95%+ of credentialing workflows with AI-powered validation
3. **Scale Healthcare Access**: Support 10,000+ providers managing credentials across all 50 states
4. **Ensure Patient Safety**: 100% provider verification before patient contact

---

## 2. Target Users & Personas

### KareMatch Personas

#### Patient (Primary User)
- **Demographics**: Adults 18-65, 60% female, urban/suburban
- **Pain Points**: Long wait times, difficulty finding in-network therapists, opaque pricing
- **Goals**: Find qualified therapist matching preferences (specialty, gender, insurance, location)
- **Success Metrics**: Time-to-first-appointment, therapist match satisfaction

#### Therapist (Secondary User)
- **Demographics**: Licensed therapists (LCSW, PsyD, PhD, MD), 70% private practice
- **Pain Points**: Client acquisition costs, credentialing burden, scheduling overhead
- **Goals**: Fill practice with ideal-fit clients, reduce administrative work
- **Success Metrics**: Client acquisition cost, booking conversion rate, schedule utilization

#### Credentialing Coordinator (Tertiary User)
- **Demographics**: Healthcare administrators managing therapist verification
- **Pain Points**: Manual document review, license expiration tracking, multi-state compliance
- **Goals**: Fast therapist onboarding, zero compliance violations
- **Success Metrics**: Time-to-credential, verification accuracy, compliance rate

---

### CredentialMate Personas

#### Credentialing Coordinator (Primary User)
- **Demographics**: Healthcare administrators at hospitals, group practices, medical staffing agencies
- **Pain Points**: Spreadsheet chaos, missed expiration deadlines, manual data entry
- **Goals**: Automate credential tracking, prevent license lapses, reduce administrative overhead
- **Success Metrics**: Time saved per credential, compliance rate, error reduction

#### Healthcare Provider (Secondary User)
- **Demographics**: MDs, DOs, NPs, PAs managing multi-state licenses
- **Pain Points**: CME tracking complexity, license renewal deadlines, multi-state compliance rules
- **Goals**: Stay compliant without spreadsheets, receive proactive expiration alerts
- **Success Metrics**: Zero license lapses, CME gap visibility, renewal on-time rate

#### Compliance Officer (Tertiary User)
- **Demographics**: Legal/compliance teams ensuring regulatory adherence
- **Pain Points**: Audit preparation, HIPAA documentation, multi-site coordination
- **Goals**: Real-time compliance dashboards, audit trail generation
- **Success Metrics**: Audit readiness, zero regulatory violations, documentation completeness

---

## 3. Problem Statement

### KareMatch: The Therapist Access Crisis
- **Industry Problem**: 50% of patients wait 3+ weeks for first appointment; 30% give up entirely
- **Root Causes**:
  - Fragmented directory listings (Psychology Today, insurance networks, word-of-mouth)
  - Opaque therapist availability and insurance acceptance
  - No intelligent matching (patients guess compatibility)
  - Manual scheduling overhead (phone tag, 24h response times)
- **Market Gap**: No HIPAA-compliant, end-to-end platform for discovery → booking → credentialing

### CredentialMate: The Credentialing Crisis
- **Industry Problem**: 70% of medical groups track credentials in spreadsheets; 15% experience license lapses
- **Root Causes**:
  - Manual data entry from 50+ state board formats
  - No centralized CME tracking (rules vary by state × credential type)
  - Reactive compliance (discover expirations after they lapse)
  - HIPAA audit burden (7-year retention, event logging)
- **Market Gap**: No AI-powered, multi-state credentialing platform with HIPAA compliance

---

## 4. Product Overview

### 4.1 KareMatch

#### Current State (v1.0 - 75% Complete)
**Live Features**:
- Therapist directory with search/filtering (specialty, location, insurance)
- Therapist profile pages with credentials, availability, contact
- Appointment booking workflow (request-based and instant)
- Multi-step therapist onboarding wizard
- Credentialing system with NPI/DEA/OIG verification (95% automated)
- Admin dashboard for therapist approval workflows
- Blog/SEO platform with city/state landing pages
- Analytics dashboard (admin traffic, profile views)

**Architecture**:
- **Frontend**: React 18 + Vite (SPA), Remix experimental (40% migrated)
- **Backend**: Express.js on AWS Lambda, PostgreSQL 15, Drizzle ORM
- **Infrastructure**: Lambda + CloudFront, Turborepo monorepo
- **Compliance**: HIPAA audit logging, soft-delete-only, consent tracking

**Test Suite**: 884 passing tests, 826 skipped, 1 flaky (70% coverage)

---

#### Feature Gaps & Roadmap

##### P0: Critical (Q1 2026)
1. **Event Type Enum Mismatch** - `crisis_intercept_displayed` not in database enum (blocks E0 safety features)
2. **Consent Logging FK Violation** - Cannot log consent for anonymous users (blocks caregiver flows)
3. **Proximity Matching Broken** - SQL distance calculation returns NULL (blocks deterministic matching)
4. **Health Endpoint Parity** - Production returns HTML instead of JSON

##### P1: High Priority (Q1-Q2 2026)
5. **Matching Explainability UI** - Algorithm exists but UI not wired to show why therapist scored highest
6. **Background Check Integration** - Checkr/Sterling APIs (30% done)
7. **Rate Limiting/CAPTCHA** - Security features for E0 not implemented
8. **Terraform IaC** - Infrastructure manual; should be codified for HIPAA compliance
9. **Integration Tests** - Missing middle layer (only unit + E2E)

##### P2: Medium Priority (Q2 2026)
10. **Patient Analytics** - Funnel visualization, engagement metrics sparse (40% complete)
11. **Calendar OAuth** - Google Calendar sync not implemented
12. **Featured Images** - Blog articles can't have featured images
13. **Performance Optimization** - No Redis caching layer, query optimization
14. **Mobile Responsiveness** - Audit needed

##### P3: Future (Q3+ 2026)
15. **Payment Processing** - Stripe integration for therapist payouts
16. **UACC Integration** - Cross-repo identity linking
17. **Sponsor/Advertising Platform** - Revenue model
18. **Video Consultations** - Telehealth
19. **In-App Messaging** - HIPAA-compliant chat
20. **Mobile Apps** - iOS/Android native

---

### 4.2 CredentialMate

#### Current State (v1.0 - Phase 1 Complete)
**Live Features**:
- AI document processing pipeline (classify → extract → review → link)
- Medical license tracking (50 US states + DC)
- DEA registration management
- Controlled Substance Registration (CSR) tracking
- CME compliance engine with 67 rule packs (50 states × MD/DO split boards)
- Admin license matrix for bulk credential management
- Accuracy dashboard showing AI extraction confidence
- HIPAA-compliant audit logging
- Email campaign system for credential reminders
- Async report generation (PDF/CSV)

**Architecture**:
- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind, shadcn/ui
- **Backend**: FastAPI + Python 3.11, PostgreSQL 15 with RLS, Celery workers
- **Infrastructure**: AWS Lambda (Docker containers), RDS, S3 + KMS, CloudFront
- **AI Processing**: OpenAI GPT-4 for document classification and field extraction
- **Compliance**: Row-level security, audit logging, encryption at rest (S3 + RDS)

**Test Suite**: Unit tests for auth/compliance/CME, E2E Playwright tests, contract tests

---

#### Feature Gaps & Roadmap

##### Phase 2: Multi-Provider Expansion (Q1 2026 - 20% Complete)
- Nurse Practitioner (NP) support with 50-state CME rules
- Physician Assistant (PA) support with 50-state CME rules
- CRNA, CNM, CNS credential tracking
- Provider-specific compliance rules

##### Phase 3: Collaboration System (Q1-Q2 2026 - Planned)
- NP-physician collaboration tracking
- Supervised practice hour logging
- State-specific oversight requirements
- Progression-to-independence workflows
- Audit package generation

##### Phase 4: Revenue & Enterprise (Q2-Q3 2026 - Future)
- Subscription management (Stripe integration)
- Oversight payment routing
- Enterprise licenses and dashboards
- Board/payer integrations

---

#### Critical Gaps Requiring Immediate Attention

##### Security & Compliance (P0)
1. **API Rate Limiting**: Not enforced in production (target: 1000 req/min/user)
2. **Field-Level Encryption**: Only S3 documents encrypted; DB fields not encrypted
3. **MFA**: Not required for user authentication
4. **Audit Log Retention**: No automatic purge after 7 years (HIPAA requirement)
5. **Penetration Testing**: Not automated in CI/CD pipeline

##### Performance (P1)
6. **Lambda Cold Start**: 5-10s on first request (impacts UX)
7. **Large File Uploads**: No chunked/resumable uploads (single-part only)
8. **Query Performance**: No optimization for large datasets (1M+ credentials)
9. **Caching Strategy**: Limited Redis usage; no CDN caching headers
10. **Database Indexes**: Basic indexes; no materialized views for dashboards

##### Operational (P1)
11. **Alerting**: Logging exists; no proactive alerting on error spikes
12. **Runbooks**: Operational procedures not documented
13. **Capacity Planning**: No metrics on resource utilization vs. limits
14. **Security Updates**: No automated dependency vulnerability scanning
15. **Multi-Region**: Single region (us-east-1); no disaster recovery region

##### Data Quality (P2)
16. **Duplicate Detection**: No deduplication of providers/credentials
17. **Data Validation**: AI extraction confidence scores stored; no rejection workflow
18. **Reconciliation**: No audit/reconciliation against state boards
19. **Historic Data**: No version history for credential changes
20. **ETL Monitoring**: Task queue failures logged but not alerted

---

## 5. Success Metrics & KPIs

### KareMatch Metrics

#### Patient Acquisition & Engagement
- **Primary**: Time-to-first-appointment (target: <48 hours)
- **Secondary**: Search-to-contact conversion rate (target: >15%)
- **Tertiary**: Patient retention rate at 6 months (target: >70%)

#### Therapist Growth & Satisfaction
- **Primary**: Active therapist count (target: 5,000 by EOY 2026)
- **Secondary**: Credentialing completion rate (target: >90%)
- **Tertiary**: Average time-to-credential (target: <7 days)

#### Platform Health
- **Primary**: Appointment booking conversion rate (target: >25%)
- **Secondary**: API response time P95 (target: <500ms)
- **Tertiary**: Test pass rate (target: >95%)

---

### CredentialMate Metrics

#### Efficiency Gains
- **Primary**: Time saved per credential (target: 80% reduction vs. spreadsheets)
- **Secondary**: AI extraction accuracy (target: >95%)
- **Tertiary**: Bulk operation completion time (target: <5 minutes for 100 credentials)

#### Compliance & Risk Reduction
- **Primary**: Zero license lapses (target: 100% compliance)
- **Secondary**: Expiration alert delivery rate (target: 100% at 60/30/14/7 days)
- **Tertiary**: Audit log completeness (target: 100% event coverage)

#### Customer Growth
- **Primary**: Active organizations (target: 500 by EOY 2026)
- **Secondary**: Providers per organization (target: 50 average)
- **Tertiary**: Net Promoter Score (NPS) (target: >50)

---

## 6. Technical Requirements

### Shared Infrastructure Requirements

#### Security & Compliance (HIPAA)
- ✅ Encryption at rest (S3, RDS)
- ✅ Encryption in transit (TLS 1.2+)
- ✅ Audit logging (WHO, WHEN, WHAT)
- ❌ Field-level encryption for PII (SSN, NPI, DEA) - **REQUIRED**
- ❌ MFA for all users - **REQUIRED**
- ❌ Automated penetration testing in CI/CD - **REQUIRED**
- ❌ HIPAA BAA documentation - **REQUIRED**

#### Performance
- API response time P95: <500ms
- Frontend load time P95: <3s
- Database query time P95: <200ms
- Lambda cold start: <2s (target: <1s)
- Bulk operations: Support 1000+ records

#### Scalability
- Support 10,000+ concurrent users
- Handle 1M+ credentials per organization
- Process 10,000+ documents per day
- Support multi-tenancy with RLS

#### Observability
- Structured logging (JSON, CloudWatch)
- Error tracking and alerting (PagerDuty integration)
- Performance monitoring (CloudWatch dashboards)
- Automated health checks and smoke tests

---

### KareMatch-Specific Requirements

#### Frontend Migration
- **Goal**: Complete Remix migration by Q2 2026 (currently 40%)
- **Impact**: Improved SEO, faster page loads, better UX
- **Risk**: Dual frontend complexity during transition

#### Matching Algorithm
- **Goal**: Fix proximity matching (SQL distance calculation broken)
- **Goal**: Wire matching explainability UI (show why therapist scored highest)
- **Impact**: Better patient-therapist fit, reduced drop-off

#### Credentialing Automation
- **Goal**: Integrate background check vendors (Checkr/Sterling)
- **Goal**: Automate license expiration tracking with suspension
- **Impact**: 100% credentialing automation (currently 95%)

---

### CredentialMate-Specific Requirements

#### AI Processing Pipeline
- **Goal**: Maintain >95% extraction accuracy
- **Goal**: Add chunked/resumable uploads for large files (>100MB)
- **Goal**: Implement confidence threshold auto-approval
- **Impact**: Reduce manual review burden, faster onboarding

#### Multi-Provider Support
- **Goal**: Support NP/PA/CRNA/CNM credential types
- **Goal**: Implement provider-specific CME rules
- **Goal**: Support state-specific collaboration tracking
- **Impact**: 4x addressable market (MD/DO → all provider types)

#### Enterprise Features
- **Goal**: Implement API rate limiting and quotas
- **Goal**: Add webhook integrations for third-party systems
- **Goal**: Build advanced search and analytics
- **Impact**: Enable enterprise sales motion

---

## 7. Integration Points

### KareMatch Integrations

#### Current
- **AWS Services**: Lambda, CloudFront, RDS, S3, SSM Parameter Store
- **Payment Gateway**: None (Stripe planned for Q2 2026)
- **Email**: Transactional emails via Bull queues
- **External APIs**: NPI Registry (NPPES), OIG Exclusion List, DEA validation

#### Planned
- **Calendar**: Google Calendar OAuth/sync (Q2 2026)
- **Background Checks**: Checkr or Sterling (Q1 2026)
- **Video Conferencing**: Telehealth platform TBD (Q3 2026)
- **EMR/EHR**: Epic/Cerner integration (Q4 2026)

---

### CredentialMate Integrations

#### Current
- **AWS Services**: Lambda, RDS, S3 + KMS, CloudFront, ElastiCache Redis
- **AI Services**: OpenAI GPT-4 for document processing
- **Email**: SES for notifications
- **Message Queue**: Celery with Redis broker

#### Planned
- **State Boards**: Automated license verification APIs (50 states)
- **Payment Gateway**: Stripe for subscriptions (Q2 2026)
- **EMR/EHR**: Epic/Cerner for credential export (Q3 2026)
- **Payer Systems**: Insurance credentialing (Q4 2026)
- **Webhooks**: Third-party integrations (Q2 2026)

---

## 8. Risk Assessment & Mitigation

### Technical Risks

#### KareMatch
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Proximity matching broken | High | High | Fix SQL distance calculation (P0) |
| Dual frontend complexity | Medium | High | Accelerate Remix migration, freeze React SPA |
| Lambda cold start latency | Medium | Medium | Implement provisioned concurrency |
| Test suite flakiness | Low | Medium | Investigate and fix flaky test |

#### CredentialMate
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Lambda cold start (5-10s) | High | High | Implement provisioned concurrency, optimize container |
| AI extraction accuracy drift | High | Low | Continuous monitoring, accuracy dashboards, retraining |
| Field-level encryption gap | High | Medium | Implement before enterprise sales |
| Single-region dependency | Medium | Low | Plan multi-region DR architecture |

---

### Business Risks

#### KareMatch
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Therapist supply constraints | High | Medium | Aggressive therapist acquisition campaigns |
| Insurance integration complexity | High | Medium | Partner with clearinghouse (Availity) |
| Regulatory changes (HIPAA) | Medium | Low | Legal review, compliance monitoring |
| Competitive pressure (BetterHelp) | High | High | Differentiate on matching quality, in-person care |

#### CredentialMate
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| State board API unavailability | High | High | Fallback to manual verification, scraping |
| AI vendor dependency (OpenAI) | Medium | Low | Abstract AI layer, evaluate alternatives (Claude, Gemini) |
| HIPAA compliance violation | Critical | Low | Third-party audit, penetration testing |
| Market education required | Medium | High | Content marketing, webinars, case studies |

---

## 9. Open Questions & Decisions Needed

### KareMatch
1. **Payment Model**: Should therapists pay subscription or commission per booking?
2. **Insurance Strategy**: Direct payer integrations or clearinghouse partner?
3. **Telehealth Strategy**: Build in-house or partner with existing platform?
4. **Mobile Strategy**: Native apps or progressive web app (PWA)?
5. **Marketing Budget**: What's the customer acquisition cost (CAC) target?

### CredentialMate
1. **Pricing Model**: Per-provider or per-organization subscription?
2. **AI Vendor**: Stay with OpenAI GPT-4 or evaluate alternatives (Claude, Gemini)?
3. **State Board Integrations**: Build direct integrations or partner with existing vendor?
4. **Enterprise Sales**: Direct sales or channel partnerships?
5. **Compliance Certification**: When to pursue SOC 2 Type II vs. HITRUST?

### Shared
1. **Go-to-Market Strategy**: Focus on one product or dual-product sales?
2. **Sales Motion**: Product-led growth (PLG) or enterprise sales?
3. **Customer Support**: In-house or outsourced support team?
4. **Infrastructure**: Stay with Lambda-First or migrate to Kubernetes?
5. **Data Residency**: Multi-region for compliance or stay single-region?

---

## 10. Success Criteria

### Launch Readiness (Both Products)
- ✅ Zero P0 bugs in production
- ✅ >95% test pass rate
- ✅ API response time P95 <500ms
- ✅ HIPAA compliance audit complete
- ✅ Penetration test findings remediated
- ✅ Runbooks and incident response documented
- ✅ Customer support team trained

### Adoption Metrics (6 Months Post-Launch)

#### KareMatch
- 5,000+ active therapists
- 50,000+ registered patients
- 10,000+ appointments booked
- <48 hour average time-to-first-appointment
- >15% search-to-contact conversion
- NPS >50

#### CredentialMate
- 500+ active organizations
- 25,000+ providers tracked
- 100,000+ credentials managed
- 95%+ AI extraction accuracy
- Zero license lapses
- NPS >50

---

## 11. Appendices

### A. Glossary
- **CME**: Continuing Medical Education (required for license renewal)
- **CSR**: Controlled Substance Registration (state-level drug prescribing license)
- **DEA**: Drug Enforcement Administration (federal drug prescribing license)
- **HIPAA**: Health Insurance Portability and Accountability Act (US healthcare privacy law)
- **NPI**: National Provider Identifier (unique healthcare provider ID)
- **OIG**: Office of Inspector General (federal exclusion list)
- **RLS**: Row-Level Security (database access control)
- **BAA**: Business Associate Agreement (HIPAA subprocessor contract)

### B. References
- KareMatch Codebase: `/Users/tmac/1_REPOS/karematch`
- CredentialMate Codebase: `/Users/tmac/1_REPOS/credentialmate`
- AI Orchestrator Documentation: `/Users/tmac/1_REPOS/AI_Orchestrator/docs/`
- HIPAA Compliance Guide: [HHS.gov](https://www.hhs.gov/hipaa)
- State Medical Board Directory: [FSMB.org](https://www.fsmb.org)

### C. Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-16 | AI Orchestrator | Initial draft based on codebase exploration |

---

**Document Status**: Draft - Awaiting Review
**Next Steps**:
1. Review with product team
2. Prioritize epics for Q1 2026
3. Create detailed feature specs for P0 items
4. Schedule kickoff meeting with engineering

**Contact**: For questions or feedback, contact the product team.
