---
id: EVIDENCE-001
date: 2026-01-10
type: bug-report
source: pilot-user
project: credentialmate
tags: [cme, california, np, ancc-certification]
priority: p0-blocks-user
linked_tasks: [TEST-META-001, BUG-CME-002]
linked_adrs: []
status: captured
---

## Evidence Summary

California NPs with ANCC certification are shown incorrect CME hour requirements (system shows 30 hours, actual requirement is 40 hours every 2 years).

## Context

- **User persona**: NP (Nurse Practitioner)
- **State**: California
- **Specialty**: Family Medicine
- **Certification**: ANCC (American Nurses Credentialing Center)
- **Impact**: User relies on system for compliance tracking and risked missing renewal deadline

## User Quote

> "I almost missed my ANCC renewal because CredentialMate told me I only needed 30 CME hours. I found out from a colleague that California NPs with ANCC actually need 40 hours every 2 years. This is a critical bug - I could have lost my license!"

## Root Cause Analysis

**Current behavior**:
- System queries CA NP base requirements (30 hours/2 years)
- Does NOT account for ANCC certification overlay (+10 hours)
- Result: Displays 30 hours instead of 40 hours

**Expected behavior**:
- System should check for certifications (ANCC, AANP, specialty boards)
- Apply certification-specific requirements on top of state base requirements
- CA NP + ANCC = 30 (base) + 10 (ANCC) = 40 hours/2 years

**Affected users**:
- All California NPs with ANCC certification (~15% of CA NP user base)
- Potentially affects other states with certification overlays

## Impact Assessment

- **How many users affected?** Approximately 15% of California NP users (ANCC-certified)
- **Urgency**: IMMEDIATE - users risk license non-renewal
- **Business value**: HIGH-RETENTION - accurate CME tracking is core value prop
- **Trust impact**: CRITICAL - compliance errors destroy trust in healthcare

## Reproduction Steps

1. Create user profile: CA NP with ANCC certification
2. Navigate to CME tracking dashboard
3. Observe: System shows "30 hours required every 2 years"
4. Expected: Should show "40 hours required every 2 years"

## Evidence Chain

1. **User interview**: CA NP pilot user (2026-01-08)
2. **CA Board of Nursing verification**: Confirmed 30 hour base requirement
3. **ANCC documentation**: Confirmed 10 hour certification overlay
4. **Database query**: Confirmed system missing certification overlay logic

## Proposed Solution

1. **Data model**: Add `certifications` array to user profile
2. **Calculation logic**: `total_cme = state_base + sum(certification_overlays)`
3. **Test coverage**: Add test cases for CA NP + ANCC, CA NP + AANP, etc.
4. **Validation**: Cross-reference with official state/certification body requirements

## Related Evidence

- Future: Create EVIDENCE-002 for similar issue in Texas (different certification rules)
- Future: Create EVIDENCE-003 for multi-specialty board requirements

## Follow-up Tasks

- [x] Create bug fix task: BUG-CME-002
- [ ] Add ANCC overlay to CME calculator
- [ ] Add regression tests for certification overlays
- [ ] Audit all states for certification-specific requirements
- [ ] Create user notification for affected users (data correction)

## Outcome Metrics

**Success criteria**:
- All CA NP + ANCC users see correct 40 hour requirement
- Zero compliance errors for certification overlays
- User trust restored (measured via NPS)

**Measurement**:
- CME accuracy test suite: 100% pass rate
- User-reported compliance errors: 0 (down from 1)
- Time to detect similar issues: <24 hours (via monitoring)
