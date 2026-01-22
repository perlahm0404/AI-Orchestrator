# Editorial Automation - Manual Verification Guide

**Version**: 1.0
**Date**: 2026-01-22
**Status**: Ready for Execution
**System**: Editorial Automation v6.1 (Phase 5-7)

---

## Overview

This guide provides step-by-step instructions for manually verifying the editorial automation system end-to-end. Execute these tests in order to validate the complete workflow from task creation to content publication.

### Prerequisites

**Before starting:**
- [ ] Browser automation package built: `cd packages/browser-automation && npm run build`
- [ ] Work queue has editorial tasks: `cat tasks/work_queue_credentialmate_editorial.json | jq 'length'` (should be 50)
- [ ] Blog directories exist: `ls blog/credentialmate/drafts` and `ls blog/credentialmate/published`
- [ ] Ralph ContentValidator tested: `pytest tests/ralph/checkers/test_content_checker.py -v`
- [ ] All unit tests passing: `pytest tests/orchestration/ tests/agents/editorial/ -v`
- [ ] All integration tests passing: `pytest tests/integration/test_editorial*.py tests/integration/test_browser*.py tests/integration/test_autonomous*.py -v`

---

## Test 1: Happy Path (APPROVE)

**Purpose**: Verify complete successful workflow from task to publication

**Expected Duration**: 5-10 minutes

### Steps

1. **Start autonomous loop**:
   ```bash
   python autonomous_loop.py --project credentialmate --max-iterations 1
   ```

2. **Verify PREPARATION stage**:
   - [ ] Console shows "📋 PREPARATION stage starting"
   - [ ] Task parsed successfully (task_id, category, topic, keywords visible)
   - [ ] No errors in parsing

3. **Verify RESEARCH stage**:
   - [ ] Console shows "🔍 RESEARCH stage starting"
   - [ ] Browser session created (session ID visible)
   - [ ] Regulatory sources scraped (2+ sources, check console output)
   - [ ] Competitor analysis completed (1+ sources)
   - [ ] Research data shows `regulatory_updates` and `competitor_analysis` arrays
   - [ ] Browser session cleaned up

4. **Verify GENERATION stage**:
   - [ ] Console shows "✍️ GENERATION stage starting"
   - [ ] IterationLoop started (max 10 iterations)
   - [ ] Draft file created in `blog/credentialmate/drafts/`
   - [ ] Filename format: `YYYY-MM-DD-{topic}.md`
   - [ ] Draft contains YAML frontmatter (title, keywords, date)
   - [ ] Draft contains markdown content (headings, paragraphs)

5. **Verify VALIDATION stage**:
   - [ ] Console shows "✅ VALIDATION stage starting"
   - [ ] ContentValidator invoked
   - [ ] SEO score calculated and displayed (0-100)
   - [ ] SEO score >= 60 (min_seo_score threshold)
   - [ ] Frontmatter validated (title, keywords present)
   - [ ] Citations validated (if applicable)
   - [ ] Verdict type: PASS

6. **Verify REVIEW stage (Approval Gate)**:
   - [ ] Console shows approval gate UI:
     ```
     ========================================
     📝 CONTENT READY FOR REVIEW
     ========================================
     ```
   - [ ] SEO score displayed: `📊 SEO Score: XX/100`
   - [ ] Validation issues displayed (if any): `⚠️ Issues:`
   - [ ] Validation warnings displayed (if any): `⚡ Warnings:`
   - [ ] Content preview shown (first 30 lines)
   - [ ] Options displayed: `[A] Approve and publish`, `[R] Reject`, `[M] Modify`

7. **Approve the draft**:
   - [ ] Press `A` when prompted
   - [ ] Approval logged to `.aibrain/content-approvals.jsonl`

8. **Verify PUBLICATION stage**:
   - [ ] Console shows "🚀 PUBLICATION stage starting"
   - [ ] Draft copied to `blog/credentialmate/published/`
   - [ ] Published filename matches draft filename
   - [ ] Git commit created (check `git log --oneline -1`)
   - [ ] Commit message format: `feat: publish editorial content - {title}`

9. **Verify COMPLETE stage**:
   - [ ] Console shows "🎉 COMPLETE stage"
   - [ ] State file cleaned up: `ls .aibrain/pipeline-*.md` (should be empty)
   - [ ] Task marked complete in work queue
   - [ ] Autonomous loop continues to next task (or exits if max iterations reached)

### Expected Results

**Files Created:**
- `blog/credentialmate/drafts/{date}-{topic}.md` (draft)
- `blog/credentialmate/published/{date}-{topic}.md` (published copy)
- `.aibrain/content-approvals.jsonl` (approval log entry)

**Git History:**
- New commit with message `feat: publish editorial content - {title}`

**Console Output:**
- All 7 stages completed successfully
- No errors or warnings (except validation warnings if applicable)

---

## Test 2: Rejection Path (REJECT)

**Purpose**: Verify rejection workflow moves draft to rejected directory

**Expected Duration**: 5-10 minutes

### Steps

1. **Start autonomous loop**:
   ```bash
   python autonomous_loop.py --project credentialmate --max-iterations 1
   ```

2. **Follow steps 1-6 from Test 1** (PREPARATION through REVIEW)

3. **Reject the draft**:
   - [ ] Press `R` when prompted
   - [ ] Enter rejection notes when prompted (e.g., "Not aligned with brand voice")
   - [ ] Notes captured: verify console shows "Notes: {your notes}"

4. **Verify rejection handling**:
   - [ ] Draft moved to `.aibrain/rejected/`
   - [ ] Rejection logged to `.aibrain/content-approvals.jsonl`
   - [ ] Task status updated to "rejected" in work queue
   - [ ] No files in `blog/credentialmate/published/`

5. **Verify log entry**:
   ```bash
   cat .aibrain/content-approvals.jsonl | tail -1 | jq
   ```
   - [ ] `decision: "reject"`
   - [ ] `notes: "{your notes}"`
   - [ ] `approved_by: "human"`

### Expected Results

**Files Created:**
- `.aibrain/rejected/{date}-{topic}.md` (rejected draft)
- `.aibrain/content-approvals.jsonl` (rejection log entry)

**Git History:**
- No new commits (rejected content not published)

**Console Output:**
- REVIEW stage returns `blocked` status
- Pipeline aborts after REVIEW stage

---

## Test 3: Modification Path (MODIFY)

**Purpose**: Verify modification request triggers retry to GENERATION stage

**Expected Duration**: 10-15 minutes

### Steps

1. **Start autonomous loop**:
   ```bash
   python autonomous_loop.py --project credentialmate --max-iterations 1
   ```

2. **Follow steps 1-6 from Test 1** (PREPARATION through REVIEW)

3. **Request modifications**:
   - [ ] Press `M` when prompted
   - [ ] Enter modification notes (e.g., "Needs more examples of CE requirements")
   - [ ] Notes captured: verify console shows "Notes: {your notes}"

4. **Verify retry to GENERATION**:
   - [ ] Pipeline returns to GENERATION stage
   - [ ] IterationLoop starts again with feedback context
   - [ ] Modification notes passed to agent as context
   - [ ] New draft iteration created (existing draft updated)
   - [ ] Iteration count incremented in state file

5. **Verify state persistence**:
   ```bash
   cat .aibrain/pipeline-*.md
   ```
   - [ ] `current_stage: "generation"` (or later if progressed)
   - [ ] `iteration: 4` (or higher, incremented from previous)
   - [ ] Stage history shows REVIEW → GENERATION retry

6. **Verify second approval gate**:
   - [ ] After regeneration, VALIDATION stage runs again
   - [ ] SEO score recalculated
   - [ ] Second approval gate appears
   - [ ] Content reflects requested modifications

7. **Approve the revised draft**:
   - [ ] Press `A` at second approval gate
   - [ ] Verify publication completes as in Test 1

### Expected Results

**Files Created:**
- `blog/credentialmate/published/{date}-{topic}.md` (final published version)
- `.aibrain/content-approvals.jsonl` (2 entries: MODIFY, then APPROVE)

**Console Output:**
- First approval gate: MODIFY decision
- Return to GENERATION stage
- Second approval gate: APPROVE decision
- Complete publication workflow

---

## Test 4: Resume from Interruption

**Purpose**: Verify pipeline resumes from saved state after crash/interrupt

**Expected Duration**: 5-10 minutes

### Steps

1. **Start autonomous loop**:
   ```bash
   python autonomous_loop.py --project credentialmate --max-iterations 1
   ```

2. **Interrupt mid-pipeline**:
   - [ ] Wait for GENERATION stage to start (console shows "✍️ GENERATION stage starting")
   - [ ] Press `Ctrl+C` to kill the process
   - [ ] Verify process terminated

3. **Verify state file exists**:
   ```bash
   ls .aibrain/pipeline-*.md
   cat .aibrain/pipeline-*.md
   ```
   - [ ] State file present
   - [ ] Contains YAML frontmatter with:
     - `content_id`
     - `current_stage: "generation"`
     - `iteration: 3` (or similar)
     - `draft_path` (if draft was created)

4. **Resume pipeline**:
   ```bash
   python autonomous_loop.py --project credentialmate --max-iterations 1
   ```

5. **Verify resume behavior**:
   - [ ] Console shows "🔄 Resuming from saved state"
   - [ ] State loaded from file
   - [ ] Pipeline resumes from GENERATION stage (not PREPARATION)
   - [ ] Iteration count preserved
   - [ ] Draft path preserved (existing draft updated, not recreated)

6. **Complete the workflow**:
   - [ ] Let pipeline complete all remaining stages
   - [ ] Approve at REVIEW gate
   - [ ] Verify publication completes

7. **Verify state cleanup**:
   ```bash
   ls .aibrain/pipeline-*.md
   ```
   - [ ] State file deleted after successful completion

### Expected Results

**Console Output:**
- First run: Shows PREPARATION → RESEARCH → GENERATION (interrupted)
- Second run: Shows "Resuming from saved state" → GENERATION → VALIDATION → REVIEW → PUBLICATION → COMPLETE

**State File:**
- Present after interruption
- Deleted after successful completion

---

## Test 5: Validation Failure → Retry

**Purpose**: Verify pipeline retries GENERATION when validation fails

**Expected Duration**: 10-15 minutes

### Prerequisites for This Test

**Manually create a low-quality draft** to force validation failure:

```bash
# Create a draft with low keyword density to fail SEO validation
cat > blog/credentialmate/drafts/2026-01-22-test-validation-fail.md << 'EOF'
---
title: "Test Article"
keywords: ["nursing", "license"]
---

# Test Article

This is a short article with very little content.

It does not contain the required keywords.
EOF
```

### Steps

1. **Modify work queue** to use the pre-created low-quality draft:
   - Edit `tasks/work_queue_credentialmate_editorial.json`
   - Add task with `draft_path: "blog/credentialmate/drafts/2026-01-22-test-validation-fail.md"`

2. **Start autonomous loop**:
   ```bash
   python autonomous_loop.py --project credentialmate --max-iterations 1
   ```

3. **Verify VALIDATION stage fails**:
   - [ ] Console shows "✅ VALIDATION stage starting"
   - [ ] SEO score calculated: < 60 (below min_seo_score)
   - [ ] Verdict type: FAIL
   - [ ] Validation issues listed (e.g., "Keyword density too low", "Content too short")

4. **Verify retry decision**:
   - [ ] Decision tree chooses RETRY (not ASK_HUMAN)
   - [ ] Pipeline returns to GENERATION stage
   - [ ] Iteration count incremented

5. **Verify agent receives feedback**:
   - [ ] Validation issues passed to agent as context
   - [ ] Agent regenerates content with improvements
   - [ ] New draft has higher keyword density

6. **Verify second validation**:
   - [ ] VALIDATION stage runs again
   - [ ] SEO score improved (>= 60)
   - [ ] Verdict type: PASS
   - [ ] Pipeline proceeds to REVIEW

7. **Check state file during retry**:
   ```bash
   cat .aibrain/pipeline-*.md
   ```
   - [ ] Stage history shows: VALIDATION (failed) → GENERATION (retry) → VALIDATION (passed)
   - [ ] Iteration count incremented each retry

### Expected Results

**Console Output:**
- First VALIDATION: FAIL (SEO < 60)
- Return to GENERATION
- Agent improves content
- Second VALIDATION: PASS (SEO >= 60)
- Proceed to REVIEW

**Iteration Count:**
- Incremented by at least 2 (failed validation + retry generation)

---

## Test 6: Browser Automation

**Purpose**: Verify browser automation scrapes regulatory and competitor data

**Expected Duration**: 10-15 minutes

### Steps

1. **Prepare editorial task** with specific research sources:
   - Edit `tasks/work_queue_credentialmate_editorial.json`
   - Ensure task has:
     ```json
     {
       "research_sources": [
         "https://www.rn.ca.gov/regulations/",
         "https://www.example.com/blog/nursing-ce"
       ]
     }
     ```

2. **Start autonomous loop**:
   ```bash
   python autonomous_loop.py --project credentialmate --max-iterations 1
   ```

3. **Verify browser session creation**:
   - [ ] Console shows "Creating browser session: editorial-{task_id}"
   - [ ] Session config logged:
     - `sessionId: editorial-{task_id}`
     - `headless: true`
     - `auditLogPath: .aibrain/browser-audit-editorial-{task_id}.jsonl`

4. **Verify regulatory scraping**:
   - [ ] Console shows "Scraping regulatory updates from: https://www.rn.ca.gov/regulations/"
   - [ ] State extraction: "State: California" (extracted from ca.gov URL)
   - [ ] Max pages: 5
   - [ ] Regulatory updates returned (check console output for array length)

5. **Verify competitor analysis**:
   - [ ] Console shows "Analyzing competitor blog: https://www.example.com/blog/nursing-ce"
   - [ ] Competitor analysis returned with metadata:
     - `title`
     - `seo_score`
     - `keywords`
     - `word_count`
     - `structure` (h1_count, h2_count, h3_count)

6. **Verify research data structure**:
   ```bash
   # Research data should be visible in console output
   ```
   - [ ] `regulatory_updates: [...]` (array of objects)
   - [ ] `competitor_analysis: [...]` (array of objects)
   - [ ] `timestamp` (ISO 8601 format)

7. **Verify session cleanup**:
   - [ ] Console shows "Cleaning up browser session: editorial-{task_id}"
   - [ ] No orphaned Chrome processes: `ps aux | grep chrome` (should be empty or only user Chrome instances)

8. **Check browser audit log**:
   ```bash
   cat .aibrain/browser-audit-editorial-*.jsonl | jq
   ```
   - [ ] Log file exists
   - [ ] Contains session creation event
   - [ ] Contains scraping events (regulatory + competitor)
   - [ ] Contains session cleanup event
   - [ ] All events timestamped (ISO 8601)

9. **Verify error handling** (optional, if scraping fails):
   - [ ] If network error occurs, error captured in research data
   - [ ] Session still cleaned up despite errors
   - [ ] Pipeline continues (does not abort on scraping failure)

### Expected Results

**Browser Audit Log:**
- `.aibrain/browser-audit-editorial-{task_id}.jsonl` created
- Contains session lifecycle events

**Research Data:**
- Regulatory updates from .gov sources
- Competitor analysis from blog sources
- Both integrated into draft content (visible in GENERATION stage output)

**Console Output:**
- All scraping operations logged
- No orphaned browser sessions
- Clean session lifecycle

---

## Post-Testing Checklist

After completing all 6 tests:

### Cleanup

- [ ] Remove test drafts: `rm blog/credentialmate/drafts/2026-01-22-test-*.md`
- [ ] Remove rejected drafts: `rm .aibrain/rejected/*.md`
- [ ] Archive approval logs: `mv .aibrain/content-approvals.jsonl .aibrain/content-approvals-$(date +%Y%m%d).jsonl.bak`
- [ ] Archive browser audit logs: `mv .aibrain/browser-audit-*.jsonl .aibrain/archive/`

### Verification Summary

- [ ] All 6 tests passed
- [ ] No critical errors encountered
- [ ] State persistence working correctly
- [ ] Browser automation functional
- [ ] Approval workflow intuitive and functional
- [ ] Git commits created appropriately

### Known Issues

**Document any issues encountered:**

| Test | Issue | Severity | Workaround |
|------|-------|----------|------------|
| (e.g., Test 3) | (e.g., Modification notes not passed to agent) | (e.g., Medium) | (e.g., Manually edit draft) |

---

## Troubleshooting

### Common Issues

**Issue**: Browser automation fails with "Module not found"
- **Solution**: Build browser automation package: `cd packages/browser-automation && npm run build`

**Issue**: State file not found on resume
- **Solution**: Check `.aibrain/` directory exists and has write permissions

**Issue**: SEO score always fails
- **Solution**: Check `knowledge/seo/keyword-strategy.yaml` is properly configured

**Issue**: Approval gate not showing
- **Solution**: Ensure not running with `--non-interactive` flag

**Issue**: Git commit fails
- **Solution**: Check git user configured: `git config --global user.name` and `git config --global user.email`

### Debug Commands

```bash
# View all state files
ls -la .aibrain/pipeline-*.md

# View approval history
cat .aibrain/content-approvals.jsonl | jq

# View browser audit logs
cat .aibrain/browser-audit-*.jsonl | jq

# Check test coverage
pytest tests/integration/test_editorial*.py -v --cov=orchestration --cov=agents/editorial

# Run only editorial tests
pytest tests/ -k editorial -v
```

---

## Success Criteria

**All tests must:**
- ✅ Complete without fatal errors
- ✅ Produce expected artifacts (drafts, published files, logs)
- ✅ Follow decision tree logic correctly
- ✅ Resume from interruption
- ✅ Clean up state files on completion
- ✅ Log decisions to audit trail

**System is production-ready when:**
- All 6 tests pass
- Approval workflow is intuitive
- Browser automation is reliable (>90% success rate)
- State persistence works across interruptions
- Git integration is seamless

---

**Verification Date**: _____________ (YYYY-MM-DD)
**Verified By**: _____________
**Result**: ⬜ PASS  ⬜ FAIL  ⬜ PARTIAL
**Notes**:


---

**Document Version**: 1.0
**Last Updated**: 2026-01-22
**Maintainer**: tmac
