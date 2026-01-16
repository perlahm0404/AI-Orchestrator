# CredentialMate Campaign Management UI Test Report

**Date:** 2026-01-15
**Tester:** Claude (Browser Automation)
**Test User:** c1@test.com (Coordinator One)
**Environments Tested:**
- localhost:3000 (Local Dev)
- credentialmate.com (Production)

---

## Executive Summary

Local dev authentication issues that caused 401s across campaign actions are now **resolved** after a container restart. Retest confirms tokens persisted in localStorage and campaign list/preview/save are working. Two UI/UX items remain open (campaign detail view and action menu). Production was not revalidated in the retest.

---

## Retest Update (Local Dev)

- **Tokens present:** `credmate_access_token` + `credmate_refresh_token` stored as valid JWTs
- **Campaign list:** `GET /api/v1/campaigns` → 200 OK
- **Audience preview:** `POST /api/v1/campaigns/preview-audience` → 200 OK
- **Save draft:** `POST /api/v1/campaigns` → 201 Created

---

## Critical Issues

### 🔴 CRITICAL: Backend API Failures (P0)

**Bug ID:** CME-CAMP-SAVE-001
**Severity:** Critical (P0) - Cannot save campaigns
**Status:** Local dev resolved; production not revalidated

**Description:**
Campaign save operations failed previously in both environments, but local dev is now fixed. Production was not revalidated after the local fix.

**Local Dev (localhost:3000):**
- ✅ Tokens persisted in localStorage
- ✅ Authenticated requests returning 200/201

**Production (credentialmate.com):**
- Previously reported "Failed to fetch" errors
- Needs revalidation after the local auth fix

**Affected Endpoints (Local Dev):**
- `GET /api/v1/campaigns?status_filter=draft` → 401
- `GET /api/v1/campaigns?status_filter=failed` → 401
- `GET /api/v1/campaigns?page=1&page_size=20` → 401
- `POST /api/v1/campaigns/preview-audience` → 401
- `POST /api/v1/campaigns` (save draft) → 401
- `POST /api/v1/auth/refresh` → 401

**Impact (Latest):**
- Local dev: campaign list, preview, and save are working
- Production: status unknown pending retest

**Console Errors:**

Local Dev:
```
Failed to save draft: ApiError
    at ApiClient.request (api.ts:163:19)
    at async handleSaveDraft (CampaignWizard.tsx:99:30)
```

Production:
```
Failed to send campaign: TypeError: Failed to fetch
    at Object.request (https://credentialmate.com/_next/static/chunks/5210-765f5ecf1c9ffe42.js:1:3339)
    at Object.createCampaign
```

**Reproduction (Local Dev - Resolved):**
1. Log in as c1@test.com on localhost:3000
2. Navigate to /dashboard/campaigns
3. Create campaign, preview audience, save draft
4. All requests return 200/201

**Reproduction (Production):**
1. Log in as c1@test.com on credentialmate.com
2. Navigate to /dashboard/campaigns
3. Create new campaign through wizard
4. Click "Save as Draft" → "Failed to save campaign"

**Recommended Fixes:**

**Local Dev:**
- Investigate session token storage/validation on backend
- Check if JWT tokens are expired or misconfigured
- Verify auth middleware is correctly validating tokens
- Add better error handling for auth failures (show re-login prompt)

**Production:**
- Check backend API server status (may be down or unreachable)
- Verify CORS configuration for credentialmate.com → api.credentialmate.com
- Check network connectivity between frontend and backend
- Verify backend deployment is healthy and responding
- Review load balancer/proxy configurations

---

## High Priority Issues

### 🟠 HIGH: Campaign Status Filters Not Working (P1)

**Bug ID:** CME-CAMP-001
**Severity:** High (P1) - Core feature broken
**Status:** Resolved (local dev)

**Description:**
Clicking status filter tabs (Drafts, Failed, Scheduled, etc.) does not filter the campaign list. All campaigns remain visible regardless of selected filter.

**Steps to Reproduce:**
1. Navigate to /dashboard/campaigns
2. Click "Drafts" tab
3. Observe: Failed campaigns still visible
4. Click "Failed" tab
5. Observe: Draft campaigns still visible

**Expected:** Only campaigns matching the selected status should display
**Actual:** All campaigns display regardless of filter selection

**Root Cause:** Backend API returned 401 due to missing refresh token (resolved)
**Location:** `CampaignList.tsx` calling `/api/v1/campaigns?status_filter=X`

---

### 🟠 HIGH: Audience Preview Not Updating (P1)

**Bug ID:** CME-CAMP-002
**Severity:** High (P1) - Critical workflow feedback missing
**Status:** Resolved (local dev)

**Description:**
When selecting audience filters (states, specialties), the "Audience Preview" section never updates. It continues showing "Add filters to see matching providers" even after filters are applied.

**Steps to Reproduce:**
1. Click "New Campaign"
2. Complete Step 1 (Campaign Name)
3. Click "Continue" to Step 2 (Audience)
4. Select "CA" state
5. Select "MD" specialty
6. Observe "Audience Preview" section

**Expected:** Preview should show count of matching providers (e.g., "142 providers match your criteria")
**Actual:** Shows "Add filters to see matching providers" despite filters being selected

**Root Cause:** Backend API returned 401 due to missing refresh token (resolved)
**Location:** `CampaignWizard.tsx` calling `POST /api/v1/campaigns/preview-audience`

**Impact:** Users have no feedback on audience size before sending campaigns

---

### 🟠 HIGH: Campaign Save Failing (P1)

**Bug ID:** CME-CAMP-003
**Severity:** High (P1) - Cannot complete campaign creation
**Status:** Resolved (local dev)

**Description:**
Attempting to save a campaign as draft fails with error: "Failed to save campaign. Please try again."

**Steps to Reproduce:**
1. Click "New Campaign"
2. Complete all wizard steps:
   - Campaign Name: "UI Test - New Campaign Creation"
   - Audience: CA + MD filters
   - Content: Subject + body with template variables
3. Click "Save as Draft"
4. Observe error banner

**Expected:** Campaign saved as draft and added to campaign list
**Actual:** Error message displayed, campaign not saved

**Root Cause:** Backend API returned 401 due to missing refresh token (resolved)
**Location:** `CampaignWizard.tsx` calling `POST /api/v1/campaigns`

---

## Medium Priority Issues

### 🟡 MEDIUM: Campaign Detail View Missing/Broken (P2)

**Bug ID:** CME-CAMP-004
**Severity:** Medium (P2) - Expected feature missing
**Status:** Needs implementation

**Description:**
Clicking on a campaign name in the list does nothing. No detail view or edit screen opens.

**Steps to Reproduce:**
1. Navigate to /dashboard/campaigns
2. Click on any campaign name (e.g., "UI Test Campaign")
3. Observe: Nothing happens

**Expected:** Campaign detail/edit view opens
**Actual:** No response to click

**Notes:** Code confirms the selection state is set, but no detail view is rendered yet.

---

### 🟡 MEDIUM: Campaign Action Menu Not Responding (P2)

**Bug ID:** CME-CAMP-005
**Severity:** Medium (P2) - Expected feature missing
**Status:** Needs implementation

**Description:**
The 3-dot action menu icon on campaigns does not respond to clicks. No context menu appears.

**Steps to Reproduce:**
1. Navigate to /dashboard/campaigns
2. Click the 3-dot icon on any campaign row
3. Observe: Nothing happens

**Expected:** Context menu with actions (Edit, Delete, Duplicate, etc.)
**Actual:** No response to click

**Notes:** Code confirms no click handler is attached to the action icon.

---

## What Works Well ✅

### Campaign Creation Wizard
- ✅ Multi-step wizard UI is clean and intuitive
- ✅ Progress indicators show completed steps clearly
- ✅ Step 1: Campaign Name - works perfectly
- ✅ Step 2: Audience filters render correctly (states, specialties, expiration)
- ✅ Step 3: Rich text editor works with formatting toolbar
- ✅ Template variables display correctly (`{{first_name}}`, etc.)
- ✅ Step 4: Review summary displays all campaign details
- ✅ Visual/HTML/Preview tabs work
- ✅ Subject line character counter works (42/100 displayed correctly)

### Layout & Design
- ✅ Responsive layout
- ✅ Clean visual design
- ✅ Status badges (Failed, Draft) are clear
- ✅ Navigation sidebar works
- ✅ User profile display in sidebar

---

## Recommendations

### Completed
1. **Fix Authentication Issue (CME-AUTH-001)** - ✅ Verified resolved in local dev
2. **Retest Core Campaign Workflow** - ✅ List, preview, and save confirmed

### Short-term Improvements (Next Sprint)
3. **Add Campaign Detail View (CME-CAMP-004)**
4. **Implement Action Menu (CME-CAMP-005)**
5. **Add Loading States for audience preview + save**

---

## Test Coverage (Post-Fix Retest)

| Feature | Tested | Status |
|---------|--------|--------|
| Campaign list display | ✅ | Working |
| Status filters | ✅ | Working |
| New campaign wizard | ✅ | Working |
| Campaign name entry | ✅ | Working |
| Audience filtering | ✅ | Working |
| Content editor | ✅ | Working |
| Template variables | ✅ | Working |
| Save as draft | ✅ | Working |
| Send campaign | ⏸️ | Not tested |
| Campaign detail view | ✅ | Missing (needs implementation) |
| Action menu | ✅ | Missing (needs implementation) |
| Schedule for later | ⏸️ | Not tested |

---

## Next Steps

1. **Development Team:** Implement campaign detail view + action menu
2. **QA Team:** Validate send/schedule flows once implemented
3. **Product Team:** Decide UX for detail view (modal vs. route)

---

## Appendix A: Environment Comparison

| Aspect | Local Dev | Production |
|--------|-----------|------------|
| **URL** | localhost:3000 | credentialmate.com |
| **Backend API** | localhost:3000/api/v1 | api.credentialmate.com/api/v1 |
| **Test Account** | c1@test.com | c1@test.com |
| **Campaign List** | ✅ Working | Not revalidated |
| **Status Filters** | ✅ Working | Not revalidated |
| **New Campaign Wizard** | ✅ Loads | ✅ Loads |
| **Audience Filters** | ✅ Renders | ✅ Renders |
| **Audience Preview** | ✅ Working | Not revalidated |
| **Content Editor** | ✅ Works | ✅ Works |
| **Save as Draft** | ❌ 401 error | ❌ Failed to fetch |
| **Error Type** | Authentication (401) | Network/CORS |

**Key Differences:**
1. **Local has auth issues**, production has network/backend issues
2. **Production filters work** (shows appropriate empty states), local filters broken
3. **Both fail to save campaigns** but for different reasons

---

## Appendix B: Test Environment Details

**Test Configuration:**
- **Browser:** Chrome (via Claude in Chrome extension)
- **Test Account:** c1@test.com / Test1234
- **Session Duration:** ~20 minutes total (10 min per environment)

**Local Dev Environment:**
- **Frontend URL:** http://localhost:3000
- **Backend API:** http://localhost:3000/api/v1
- **Network:** Loopback (127.0.0.1)

**Production Environment:**
- **Frontend URL:** https://credentialmate.com
- **Backend API:** https://api.credentialmate.com/api/v1
- **Network:** Public internet

**API Response Samples:**

Local Dev (401 Error):
```
Status: 401 Unauthorized
Request: POST /api/v1/campaigns
Response: { "detail": "Unauthorized" }
```

Production (Network Error):
```
TypeError: Failed to fetch
(Network request failed - CORS/connectivity issue)
```

**Console Error Samples:**

Local Dev:
```
Failed to save draft: ApiError
    at ApiClient.request (webpack-internal:///(app-pages-browser)/./src/lib/api.ts:163:19)
    at async handleSaveDraft (webpack-internal:///(app-pages-browser)/./src/components/campaigns/CampaignWizard.tsx:99:30)
```

Production:
```
Failed to send campaign: TypeError: Failed to fetch
    at Object.request (https://credentialmate.com/_next/static/chunks/5210-765f5ecf1c9ffe42.js:1:3339)
    at Object.createCampaign
Failed to load preview: TypeError: Failed to fetch
    at Object.request
    at Object.previewAudience
```
