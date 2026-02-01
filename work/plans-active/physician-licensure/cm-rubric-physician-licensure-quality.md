---
title: Physician Licensure Content Quality Rubric
scope: cm
type: rubric
status: active
created: 2026-01-22
version: "1.0"
compliance:
  soc2:
    controls:
      - CC6.1
      - CC7.2
  iso27001:
    controls:
      - A.8.1
      - A.14.2
---

# Physician Licensure Content Quality Rubric

## Overview

This rubric defines the quality standards for all physician licensure articles. Content must score a minimum of **70/100** to pass validation.

**Validation Checkpoints**:
1. Pre-draft: Keyword research and outline approved
2. First draft: Basic structure and content complete
3. Final: All rubric criteria met, citations verified

---

## Scoring Categories (100 Points Total)

### 1. Medical Accuracy (25 points)

| Score | Criteria |
|-------|----------|
| 25 | All facts verified against primary sources; no errors in fees, deadlines, or requirements |
| 20 | Minor discrepancies in secondary details (e.g., outdated website URL); core facts accurate |
| 15 | Contains one factual error in non-critical area; correctable without major rewrite |
| 10 | Contains errors in fees, CME hours, or deadlines; requires fact-checking pass |
| 0 | Multiple significant errors; article cannot be published without major revision |

**Mandatory Accuracy Checks**:
- [ ] License renewal fees match current state medical board fee schedule
- [ ] CME hour requirements match current state regulations
- [ ] Renewal cycle (biennial/triennial) is correct
- [ ] Grace period information is accurate (or explicitly noted as "no grace period")
- [ ] Late fees and penalty amounts are verified
- [ ] IMLC membership status is current (especially Michigan withdrawal March 2026)
- [ ] MD vs DO requirements differentiated where applicable

**Red Flags (automatic score of 0)**:
- Nursing board references in physician article
- Conflating MD and DO requirements without clarification
- Outdated IMLC state list
- Incorrect penalty amounts
- Wrong state board URL

---

### 2. Source Citations (20 points)

| Score | Criteria |
|-------|----------|
| 20 | 5+ citations from required sources; all links verified working; proper citation format |
| 16 | 4 citations from required sources; links verified |
| 12 | 3 citations; at least one from each required category |
| 8 | 2 citations; missing required source category |
| 0 | Fewer than 2 citations or no .gov sources |

**Required Source Categories** (at least one from each):

#### Category A: State Medical Board (.gov or official board site)
Examples:
- mbc.ca.gov (California)
- tmb.state.tx.us (Texas)
- flboardofmedicine.gov (Florida)
- op.nysed.gov (New York)
- med.ohio.gov (Ohio)

#### Category B: FSMB or FCVS
- fsmb.org
- fcvs.fsmb.org
- docinfo.org

#### Category C: Fee/Regulation Documentation
- Official fee schedule page
- State statute or regulation (CCR, TAC, FAC, etc.)

#### Category D: Supporting Authority (one or more)
- ACCME (accme.org)
- AMA (ama-assn.org)
- IMLC (imlcc.org)
- State legislature (.gov)
- NPDB (npdb.hrsa.gov) - for disciplinary content

**Citation Format Standard**:
```markdown
## References

[1]: California Medical Board - License Renewal
     https://mbc.ca.gov/licensees/license-renewal/

[2]: FSMB - State Medical Board Contacts
     https://www.fsmb.org/contact-a-state-medical-board/

[3]: California Code of Regulations, Title 16, Section 1338 - CME Requirements
     https://govt.westlaw.com/calregs/...

[4]: AMA PRA Credit System
     https://www.ama-assn.org/education/ama-pra-credit-system

[5]: Interstate Medical Licensure Compact - Participating States
     https://www.imlcc.org/participating-states/
```

---

### 3. Regulatory Reference Format (15 points)

| Score | Criteria |
|-------|----------|
| 15 | All regulatory references properly formatted with statute/regulation numbers |
| 12 | Most references formatted; minor inconsistencies |
| 8 | Some references present but inconsistent format |
| 4 | Vague references ("according to state law") without specifics |
| 0 | No regulatory references or incorrect statute citations |

**Proper Regulatory Reference Examples**:

#### California
```markdown
**Authority**: Business and Professions Code Section 2420-2428
**CME Regulation**: California Code of Regulations, Title 16, Division 13.8, Article 10
**Late Fee Regulation**: CCR Section 1365 (10% delinquency fee)
**Unprofessional Conduct**: CCR Section 1338
```

#### Texas
```markdown
**Authority**: Texas Occupations Code, Chapter 155
**CME Regulation**: Texas Administrative Code, Title 22, Part 9, Chapter 166
**Fees**: TMB Fee Schedule per SB104
  - SB104 Fee: $80
  - PMP Fee: $11.48
  - NPDB: $21
  - PHP: $7
  - OPP: $2
  - TMB: $370
```

#### Florida
```markdown
**Authority**: Florida Statutes, Chapter 458
**Administrative Rules**: Florida Administrative Code, Chapter 64B8
**Mandatory CME Topics**: FAC 64B8-13.005
```

#### Federal
```markdown
**NPDB Reporting**: 45 CFR Part 60
**IMLC**: Interstate Medical Licensure Compact (42 states + DC + Guam as of Jan 2026)
**ACCME Standards**: ACCME Accreditation Requirements
```

**Required Elements**:
- Statute or code section number
- Regulatory citation (CFR, CCR, TAC, FAC, etc.)
- Last verified date for fee amounts

---

### 4. Fee and Deadline Accuracy (15 points)

| Score | Criteria |
|-------|----------|
| 15 | All fees verified against current official schedule; "as of [date]" notation included |
| 12 | Fees accurate but missing verification date |
| 8 | One fee amount outdated by <$25 |
| 4 | Multiple outdated fee amounts |
| 0 | Fees significantly wrong or fabricated |

**Fee Presentation Standard**:

```markdown
## California License Renewal Fees (as of January 2026)

| Fee Type | Amount | Authority |
|----------|--------|-----------|
| Biennial Renewal | $1,206 | B&P Code Section 2435 |
| Delinquency (0-30 days) | +10% ($120.60) | CCR Section 1365 |
| Delinquency (90+ days) | +50% ($603) | CCR Section 1365 |
| Late CME Penalty | Disciplinary action | CCR Section 1338 |

*Source: [Medical Board of California Fee Schedule](https://mbc.ca.gov/licensees/license-fees/)*
*Last verified: January 22, 2026*
```

**State Fee Reference Quick Check**:

| State | Renewal Fee | CME Hours | Grace Period | Source |
|-------|-------------|-----------|--------------|--------|
| California | $1,206 | 50 | None | mbc.ca.gov |
| Texas | ~$491 | 24 | 30 days | tmb.state.tx.us |
| Florida | $360 | 40 | 30 days | flboardofmedicine.gov |
| New York | $736 | 0 | Triennial | op.nysed.gov |
| Pennsylvania | Varies | 100 | Varies | dos.pa.gov |
| Ohio | $305 | 100 | Varies | med.ohio.gov |
| Oregon | +$195 late | Varies | None | oregon.gov/omb |
| Wisconsin | $60 | Varies | Varies | dsps.wi.gov |

---

### 5. SEO Compliance (10 points)

| Score | Criteria |
|-------|----------|
| 10 | SEO score ≥70; all required placements met |
| 8 | SEO score 60-69; minor placement issues |
| 6 | SEO score 50-59; keyword density off-target |
| 4 | SEO score 40-49; multiple issues |
| 0 | SEO score <40 or missing primary keyword in title |

**SEO Requirements Checklist**:
- [ ] Primary keyword in title (exact match)
- [ ] Primary keyword in H1
- [ ] Primary keyword in first 100 words
- [ ] Primary keyword in conclusion
- [ ] Keyword density 1-3%
- [ ] At least 2 internal links to related articles
- [ ] At least 4 external links to authoritative sources
- [ ] Meta description includes primary keyword (under 160 chars)
- [ ] URL slug contains primary keyword

**SEO Score Calculation** (automated by ContentValidator):
```
Base Score: 50
+ Primary keyword in title: +10
+ Primary keyword in H1: +5
+ Primary keyword in first paragraph: +5
+ Keyword density 1-2%: +10
+ Internal links ≥2: +5
+ External links ≥4: +5
+ Proper heading hierarchy: +5
+ Meta description present: +5
= Maximum: 100
```

---

### 6. Structure and Readability (10 points)

| Score | Criteria |
|-------|----------|
| 10 | Perfect structure: 1 H1, 4+ H2, 2+ H3; Flesch-Kincaid ≤14 |
| 8 | Good structure; readability 14-16 |
| 6 | Acceptable structure; missing 1 heading level |
| 4 | Poor structure; readability >16 |
| 0 | No heading structure or unreadable |

**Required Structure**:
```markdown
# [Article Title - H1 with Primary Keyword]

## Introduction
[Hook, context, preview - 100-150 words]

## [Main Section 1 - H2]
[Content with secondary keywords]

### [Subsection - H3]
[Supporting details]

## [Main Section 2 - H2]
[Content]

## [Main Section 3 - H2]
[Content]

## Key Takeaways
- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]

## Conclusion
[Summary, call to action - 100-150 words]

## Frequently Asked Questions

### [Question 1 - long-tail keyword]?
[Answer]

### [Question 2]?
[Answer]

### [Question 3]?
[Answer]

## References
[Citations]
```

**Readability Targets**:
- Flesch-Kincaid Grade Level: ≤14 (physician audience)
- Average sentence length: <25 words
- Average paragraph length: <150 words
- Use bullet points for lists of 3+ items
- Use tables for fee/requirement comparisons

---

### 7. Completeness (5 points)

| Score | Criteria |
|-------|----------|
| 5 | All required sections present; 1000+ words; no placeholder text |
| 4 | Minor section missing (e.g., one FAQ) |
| 3 | Missing FAQ or Key Takeaways |
| 2 | Missing multiple sections |
| 0 | Incomplete draft with placeholders |

**Required Sections Checklist**:
- [ ] Frontmatter (title, category, keywords, created, status)
- [ ] H1 title with primary keyword
- [ ] Introduction (hook, context, preview)
- [ ] Main body (4+ H2 sections for physician content)
- [ ] Key Takeaways (3-5 bullet points)
- [ ] Conclusion with call to action
- [ ] FAQ section (3-5 questions using long-tail keywords)
- [ ] References section (5+ citations)

**Word Count Requirements**:
- Minimum: 1,000 words
- Target: 1,800 words
- Maximum: 3,000 words

---

## Validation Workflow

### Automated Checks (Ralph-style ContentValidator)

```python
ContentValidator runs 8 checks:
1. markdown_syntax       - Valid markdown, no broken formatting
2. frontmatter_metadata  - All required fields present
3. seo_score            - ≥50 minimum, target ≥70
4. keyword_density      - 1-3% for primary keyword
5. link_validity        - All links return 200/301
6. spelling_grammar     - <5 errors per 1000 words
7. citation_verification - Primary sources accessible
8. readability_score    - Flesch-Kincaid ≤14
```

### Manual Verification Checklist

Before publishing, human reviewer must verify:

1. **Fee Accuracy**: Open state medical board fee schedule, confirm all amounts
2. **CME Hours**: Verify against current state regulations
3. **IMLC Status**: Confirm state membership (especially Michigan March 2026)
4. **Deadline Accuracy**: Verify renewal cycles and grace periods
5. **Link Testing**: Click all external links, confirm they reach correct pages
6. **Competitor Check**: Ensure content is differentiated from top 3 SERP results
7. **Nursing Contamination**: Confirm no nursing-specific terms slipped in

---

## Passing Thresholds

| Status | Score | Action |
|--------|-------|--------|
| **PASS** | 70-100 | Ready for human review and publication |
| **NEEDS_REVISION** | 50-69 | Return to agent for improvements |
| **FAIL** | 0-49 | Major rewrite required; escalate if 3+ failures |

---

## Quality Examples

### High-Quality Example (Score: 92/100)

```markdown
---
title: "California Medical License Renewal 2026: Fees, CME, and Deadlines"
category: state-specific
keywords:
  - California medical license renewal
  - MBC license renewal
  - California CME requirements
target_audience: physicians
created: "2026-01-22"
status: draft
seo_score: 78
citations_verified: true
---

# California Medical License Renewal 2026: Fees, CME, and Deadlines

## Introduction

California physicians must renew their medical license biennially through the
Medical Board of California (MBC). Understanding the exact requirements, fees,
and deadlines is essential to avoid practicing with an expired license—a
violation that can result in disciplinary action, civil liability, and
criminal charges under Business and Professions Code Section 2052.

This guide covers everything you need to know about California medical license
renewal in 2026, including current fees, CME requirements, and what happens
if you miss your deadline.

## License Renewal Fees (as of January 2026)

| Fee Type | Amount | Authority |
|----------|--------|-----------|
| Biennial Renewal | $1,206 | B&P Code Section 2435 |
| Delinquency (0-30 days) | +10% ($120.60) | CCR Section 1365 |
| Delinquency (90+ days) | +50% ($603) | CCR Section 1365 |

The renewal fee includes mandatory contributions:
- Steven M. Thompson Physician Corps Loan Repayment Program: $25
- CURES (Controlled Substance Utilization Review): $30

*Source: [MBC Fee Schedule](https://mbc.ca.gov/licensees/license-fees/)*
*Last verified: January 22, 2026*

## CME Requirements

California requires **50 hours of Category 1 CME** per biennial renewal
period. Under California Code of Regulations, Title 16, Section 1338,
misrepresenting CME compliance constitutes unprofessional conduct.

### Mandatory CME Topics

California does not mandate specific CME topics beyond the 50-hour
requirement. However, physicians should maintain documentation per
CCR Section 1339 for at least four years.

## What Happens If You Miss the Deadline

**California has no grace period.** Your license expires at 11:59 PM on the
expiration date. Practicing medicine with an expired license violates B&P
Code Section 2052 and may result in:

- Disciplinary action by the Medical Board
- Civil liability for unlicensed practice
- Criminal misdemeanor charges
- NPDB reporting under 45 CFR Part 60

## Key Takeaways

- Biennial renewal fee is $1,206 (includes mandatory program fees)
- 50 hours of Category 1 CME required per renewal period
- **No grace period**—license expires at midnight on expiration date
- Late renewal incurs 10% fee (0-30 days) or 50% fee (90+ days)
- Maintain CME documentation for 4 years

## Conclusion

California medical license renewal requires planning ahead. With no grace
period and steep delinquency fees, physicians should complete CME requirements
and submit renewal applications well before the expiration date. Use
CredentialMate to track your CME hours and receive renewal reminders.

## Frequently Asked Questions

### How much does it cost to renew a medical license in California?

The biennial renewal fee is $1,206, which includes mandatory fees for the
Steven M. Thompson Physician Corps Loan Repayment Program ($25) and CURES
($30). Late renewals incur additional delinquency fees of 10% to 50%.

### Does California have a grace period for medical license renewal?

No. California has no grace period. Your license expires at 11:59 PM on
the expiration date, and practicing with an expired license is illegal.

### How many CME hours are required for California medical license renewal?

California requires 50 hours of AMA PRA Category 1 CME credits per biennial
(two-year) renewal period.

## References

[1]: Medical Board of California - License Renewal
     https://mbc.ca.gov/licensees/license-renewal/

[2]: Medical Board of California - Fee Schedule
     https://mbc.ca.gov/licensees/license-fees/

[3]: California Code of Regulations, Title 16, Section 1338 - CME Requirements
     https://govt.westlaw.com/calregs/

[4]: FSMB - California Medical Board Contact
     https://www.fsmb.org/contact-a-state-medical-board/

[5]: California Business and Professions Code, Section 2052 - Unlicensed Practice
     https://leginfo.legislature.ca.gov/
```

### Low-Quality Example (Score: 35/100 - FAIL)

```markdown
---
title: "How to Renew Your Doctor License"
...
---

# Renewing Your Doctor License

Doctors need to renew their license every few years. The fee varies by state.

You need to complete CME hours. Check your state board website for details.

If you don't renew on time, you might face penalties.

## References

[1]: Google search results
```

**Issues**:
- Generic title without state or primary keyword (-10 SEO)
- Vague information ("every few years", "varies by state") (-25 accuracy)
- No specific fees, regulations, or deadlines (-15 fees)
- No regulatory references (-15 regulatory)
- No authoritative sources cited (-20 citations)
- Missing required sections (-5 completeness)

---

## Appendix: Physician-Specific Validation Rules

### Differentiation from Nursing Content

| Check | Requirement |
|-------|-------------|
| Title | Must include "physician", "medical license", "MD", or "DO" |
| Keywords | No "nursing", "RN", "LPN", "nurse" in primary keywords |
| Sources | State Medical Board (not Board of Nursing) |
| Regulations | Medical practice acts (not Nurse Practice Acts) |
| CME Terms | "CME" and "Category 1" (not "CEU" or "contact hours") |

### MD vs DO Awareness

For states with separate boards (e.g., Pennsylvania):
- Clearly label which board governs which license type
- Note any differences in CME requirements
- Provide links to both boards when applicable

### IMLC Critical Update

For all IMLC-related content:
- Note current member count: 42 states + DC + Guam
- **Prominently display**: Michigan withdrawal effective March 28, 2026
- Clarify: IMLC provides expedited licensure, not a multistate license
