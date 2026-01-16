---
# Document Metadata
doc-id: "cm-plan-campaign-auth-403"
title: "Campaign Creation 403 Investigation Plan"
created: "2026-01-15"
updated: "2026-01-15"
author: "Codex CLI"
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
project: "credentialmate"
domain: "operator"
relates-to: ["2026-01-15_campaign-deployment-database-fixes"]

# Change Control
version: "1.0"
---

# Campaign Creation 403 Investigation Plan

**Objective:** Resolve HTTP 403 errors when creating campaigns in production.
**Status:** Planning Phase

---

## Phase 1: Reproduce and Collect Evidence (P0)

1. Capture a failed request from the browser Network tab and save:
   - request URL, method, headers (Authorization), and response body.
2. Tail Lambda logs for the failed request window and collect:
   - auth middleware output, user identification, and role evaluation.
3. Confirm the client is targeting `https://api.credentialmate.com` and not the API Gateway default domain.

## Phase 2: Validate Auth and Role Resolution (P0)

1. Decode the JWT token and verify:
   - subject/user id, org id, role claims, and expiration.
2. Confirm `get_current_user` resolves the same user id as the token.
3. Verify `require_campaign_manager_role` compares the role in the same format as stored in the DB.

## Phase 3: Isolate Root Cause (P0)

1. If token is valid but role check fails:
   - add temporary logging for role value and comparison inputs.
2. If token is missing or invalid:
   - verify frontend auth storage and request interceptor behavior.
3. If user resolution fails:
   - inspect user lookup query for org scoping or soft-delete conditions.

## Phase 4: Fix and Verify (P0)

1. Implement the minimal fix (role mapping, token refresh, or auth middleware change).
2. Redeploy backend Lambda and re-run a campaign creation test.
3. Confirm campaign row exists and UI list updates without console errors.

## Phase 5: Prevent Recurrence (P1)

1. Add a lightweight auth diagnostic log toggle for production troubleshooting.
2. Add a regression test covering campaign creation with credentialing coordinator role.

---

## Exit Criteria

- Campaign creation returns HTTP 201 in production.
- UI shows the new campaign in the list.
- No 403 errors in Lambda logs for the test user.
