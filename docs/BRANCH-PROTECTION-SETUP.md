# Branch Protection Rules Setup

This document describes how to configure GitHub branch protection rules to enforce Ralph governance at the server level.

## Why Branch Protection?

Even with local pre-commit hooks, users can bypass them using `git commit --no-verify`. Branch protection rules provide a **server-side enforcement** that cannot be bypassed.

## Setup Instructions

### 1. Navigate to Repository Settings

1. Go to your GitHub repository (e.g., `github.com/your-org/karematch`)
2. Click **Settings** tab
3. In the left sidebar, click **Branches** under "Code and automation"

### 2. Add Branch Protection Rule

Click **Add branch protection rule** (or edit existing rule for `main`).

### 3. Configure Rule for `main` Branch

**Branch name pattern**: `main`

#### Required Settings

| Setting | Value | Why |
|---------|-------|-----|
| **Require a pull request before merging** | ✅ Enabled | Prevents direct pushes |
| **Require approvals** | 1+ | Human must approve |
| **Dismiss stale PR approvals** | ✅ Enabled | New commits need re-review |
| **Require status checks to pass** | ✅ Enabled | Enforces CI |
| **Require branches to be up to date** | ✅ Enabled | No stale merges |
| **Status checks that are required** | See below | Ralph must pass |

#### Required Status Checks

Add these status checks (they must have run at least once first):

```
✅ Ralph Verification / Ralph Governance Check
✅ Ralph Verification / Risk Classification
```

#### Additional Recommended Settings

| Setting | Value | Why |
|---------|-------|-----|
| **Require conversation resolution** | ✅ Enabled | All comments addressed |
| **Require signed commits** | Optional | Extra security |
| **Include administrators** | ✅ Enabled | No one can bypass |
| **Restrict who can push** | Optional | Limit direct push access |
| **Allow force pushes** | ❌ Disabled | Prevents history rewrite |
| **Allow deletions** | ❌ Disabled | Protects branch |

### 4. Save Changes

Click **Create** or **Save changes**.

## Verification

After setup, verify by:

1. Create a test branch
2. Make a change that violates guardrails (e.g., add `eslint-disable`)
3. Push and open PR
4. Confirm Ralph CI check fails
5. Confirm merge is blocked

## What This Enforces

```
Developer makes change
         ↓
    git commit
         ↓
Pre-commit hook (can bypass with --no-verify)
         ↓
    git push
         ↓
GitHub Actions runs Ralph CI ← SERVER-SIDE (cannot bypass)
         ↓
Branch protection checks status
         ↓
❌ BLOCKED if Ralph fails
✅ Merge allowed if Ralph passes + human approves
```

## Troubleshooting

### "Status check not found"

Status checks only appear after they've run at least once. Push a commit to trigger the workflow first.

### "Admin bypassed protection"

Enable "Include administrators" to prevent this.

### CI passes but still can't merge

Check that all required status checks are listed and have passed. Sometimes checks have slightly different names.

## For AI Orchestrator Repo

Apply similar rules to the AI Orchestrator repository:

**Branch name pattern**: `main`

Required status checks:
```
✅ tests (or whatever your pytest CI job is named)
```

## Emergency Override

In true emergencies, a repository admin can:
1. Temporarily disable branch protection
2. Make the emergency fix
3. Re-enable branch protection
4. Document the emergency in the commit message

**This should be extremely rare** and requires explicit justification.

---

## Quick Reference

### GitHub CLI Setup (Optional)

You can also configure branch protection via `gh` CLI:

```bash
gh api repos/{owner}/{repo}/branches/main/protection \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  -f required_status_checks='{"strict":true,"contexts":["Ralph Verification / Ralph Governance Check"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":1}' \
  -f restrictions=null
```

### Checking Current Protection

```bash
gh api repos/{owner}/{repo}/branches/main/protection
```

---

**Last Updated**: 2026-01-06
**Applies To**: KareMatch, CredentialMate, AI Orchestrator
