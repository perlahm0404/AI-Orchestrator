---
id: EVIDENCE-001
date: 2026-01-10
type: bug-report
source: pilot-user
project: credentialmate
tags: [cme, california, np, ancc-certification]
priority: p0-blocks-user
linked_tasks: []
linked_adrs: []
status: captured
---

## Evidence Summary
California NPs with ANCC certification are shown incorrect CME hour requirements (system shows 30 hours, actual requirement is 40 hours every 2 years).

## Context
- User persona: NP (Nurse Practitioner)
- State: California
- Specialty: Family Medicine
- Current behavior: System shows "30 CME hours required for renewal"
- Expected behavior: System should show "40 CME hours required every 2 years" for ANCC-certified NPs

## Raw Data
- User quote: "I just checked my license renewal requirements on the CA BRN website and it says I need 40 hours, but CredentialMate is showing 30. I'm worried I'm going to miss my deadline."
- Source: California Board of Registered Nursing (BRN) - [https://www.rn.ca.gov/applicants/lic-np.shtml](https://www.rn.ca.gov/applicants/lic-np.shtml)
- Relevant regulation: California requires 40 CME hours every 2 years for NPs with ANCC certification (Business and Professions Code Section 2836.1)

## Impact Assessment
- How many users affected? **All California NP users with ANCC certification** (estimated 20-30% of CA NP market)
- Urgency: **Immediate** - users relying on incorrect data risk missing renewal deadlines
- Business value: **High-retention** - accurate CME tracking is core value prop, errors erode trust

## Linked Items
- Tasks: *(To be created)*
- ADRs: *(None yet)*
- KOs: *(None yet)*

## Resolution (if implemented)
- Date resolved: *(Not yet resolved)*
- Implementation: *(Pending)*
- Validation: *(Pending)*
