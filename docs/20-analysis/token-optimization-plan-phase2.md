# Token Optimization Plan - Phase 2

**Date**: 2026-01-18
**Author**: Claude (Session Analysis)
**Context**: Follow-up to Phase 1 optimization (saved 9,703 tokens)

---

## Executive Summary

Phase 1 saved **9,703 tokens** (50% reduction in AI_Orchestrator startup cost). Phase 2 targets **8,000+ additional tokens** by pruning STATE.md bloat and optimizing DECISIONS.md loading.

**Key Finding**: KareMatch STATE.md (80 lines) is the gold standard - lean, current, no historical bloat. AI_Orchestrator (849 lines) and CredentialMate (538 lines) have massive duplication.

---

## Current Token Costs (Post Phase 1)

| Repository | File | Lines | Tokens | % of Startup |
|------------|------|-------|--------|--------------|
| **AI_Orchestrator** | STATE.md | 849 | 5,861 | 54% |
| | DECISIONS.md | N/A | 0 | 0% (ADRs in vault) |
| | CATALOG.md | 219 | 1,511 | 14% |
| | CLAUDE.md | 333 | 1,948 | 18% |
| | Session file | ~300 | 2,070 | 19% |
| | Contracts | 374 | 3,253 | 30% |
| | **Total** | | **10,856** | |
| **KareMatch** | STATE.md | 80 | 552 | 11% |
| | DECISIONS.md | 176 | 1,214 | 24% |
| | CLAUDE.md | ~200 | 1,380 | 27% |
| | Session file | ~150 | 1,035 | 20% |
| | **Total** | | **5,031** | |
| **CredentialMate** | STATE.md | 538 | 3,712 | 67% |
| | DECISIONS.md | 578 | 3,988 | 72% |
| | CLAUDE.md | ~200 | 1,380 | 25% |
| | Session file | ~150 | 1,035 | 19% |
| | **Total** | | **5,534** | |

**Biggest Issue**: STATE.md dominates AI_Orchestrator (54%) and CredentialMate (67%) startup costs.

---

## Problem Analysis

### AI_Orchestrator STATE.md (849 lines, 5,861 tokens)

| Section | Lines | Tokens | Critical? | Issue |
|---------|-------|--------|-----------|-------|
| **Active Work** | **604** | **4,160** | ❌ | **Duplicates sessions/cross-repo/active/20260118-1130-3-repo-memory-unification.md** |
| Current Status | 30 | 210 | ✅ | Essential |
| Recent Milestones | 35 | 245 | ⚠️ | Can compress to 5 lines |
| KareMatch Status | 24 | 168 | ❌ | Duplicates .aibrain/global-state-cache.md |
| CredentialMate Status | 24 | 168 | ❌ | Duplicates .aibrain/global-state-cache.md |
| Architecture Overview | 28 | 196 | ❌ | Duplicates CATALOG.md |
| Directory Status | 6 | 42 | ❌ | Use `ls` or `tree` |
| Blockers | 6 | 42 | ✅ | Essential |
| Next Steps | 24 | 168 | ✅ | Essential |
| Success Metrics | 13 | 91 | ⚠️ | Can compress to 3 lines |
| v4 Summary | 50+ | 350+ | ❌ | Historical - archive to vault |

**Total Waste**: ~5,255 tokens (90% of STATE.md)

### CredentialMate STATE.md (538 lines, 3,712 tokens)

| Section | Lines | Tokens | Critical? | Issue |
|---------|-------|--------|-----------|-------|
| **All Systems Status** | **144** | **993** | ❌ | **Duplicates .aibrain/global-state-cache.md** |
| **CME Reporting Discoveries** | **103** | **710** | ❌ | **Historical - should be in session file** |
| Current Implementation Status | 93 | 641 | ⚠️ | Partially historical |
| Decision Points Made | 29 | 200 | ❌ | Duplicates DECISIONS.md |
| Verification Checklist | 33 | 228 | ⚠️ | Reference task completion |
| Risk Assessment | 23 | 159 | ⚠️ | Can compress |
| Other | 113 | 781 | Mixed | |

**Total Waste**: ~2,700 tokens (73% of STATE.md)

### KareMatch STATE.md (80 lines, 552 tokens) ✅

**This is the gold standard!**
- Current status only
- No historical bloat
- Links to other resources (Knowledge Vault, MissionControl, AI_Orchestrator)
- Essential metrics and blockers

---

## Optimization Recommendations

### Option A: Conservative Pruning (~3,500 token savings)

**AI_Orchestrator STATE.md** (849 → 300 lines):
- ✅ **Delete Active Work** (604 lines) → Replace with link to session file → **4,160 tokens saved**
- ✅ **Delete other repo status** (48 lines) → Link to global-state-cache.md → **336 tokens saved**
- ✅ **Delete Architecture Overview** (28 lines) → Link to CATALOG.md → **196 tokens saved**
- ✅ **Delete Directory Status** (6 lines) → Use `ls` → **42 tokens saved**
- ⚠️ Keep v4 Summary (historical reference)

**CredentialMate STATE.md** (538 → 450 lines):
- ✅ **Delete All Systems Status** (144 lines) → Link to global-state-cache.md → **993 tokens saved**
- ⚠️ Keep CME Reporting Discoveries (learning value)
- ⚠️ Keep Decision Points Made (context)

**Total Savings**: ~5,727 tokens (conservative)

### Option B: Aggressive Pruning (~8,000 token savings)

**AI_Orchestrator STATE.md** (849 → 100 lines):
- ✅ **Delete Active Work** (604 lines) → **4,160 tokens saved**
- ✅ **Delete other repo status** (48 lines) → **336 tokens saved**
- ✅ **Delete Architecture Overview** (28 lines) → **196 tokens saved**
- ✅ **Delete Directory Status** (6 lines) → **42 tokens saved**
- ✅ **Delete v4 Summary** (50+ lines) → Archive to vault → **350 tokens saved**
- ✅ **Compress Recent Milestones** (35 → 5 lines) → **210 tokens saved**
- ✅ **Compress Success Metrics** (13 → 3 lines) → **70 tokens saved**

**CredentialMate STATE.md** (538 → 200 lines):
- ✅ **Delete All Systems Status** (144 lines) → **993 tokens saved**
- ✅ **Delete CME Reporting Discoveries** (103 lines) → Move to session file → **710 tokens saved**
- ✅ **Delete Decision Points Made** (29 lines) → Link to DECISIONS.md → **200 tokens saved**
- ✅ **Compress Current Implementation Status** (93 → 30 lines) → **434 tokens saved**
- ✅ **Compress Verification Checklist** (33 → 10 lines) → **159 tokens saved**

**Total Savings**: ~7,860 tokens (aggressive)

### Option C: Maximum Pruning + Conditional Loading (~10,000 token savings)

**Same as Option B, PLUS:**

#### Conditional DECISIONS.md Loading

Currently DECISIONS.md is loaded on EVERY session (step 3 of startup protocol). This is wasteful for task execution sessions.

**Proposal**: Only load DECISIONS.md when:
- Starting strategic planning sessions
- Building new features
- Making architectural decisions
- Explicitly requested by user

**Implementation**:
```python
# orchestration/context_preparation.py
def get_startup_protocol_prompt(
    project_path: Path,
    repo_name: str,
    include_cross_repo: bool = True,
    task_type: Optional[str] = None  # NEW parameter
) -> str:
    # ... existing code ...

    # Conditional DECISIONS.md loading
    if (project_path / "DECISIONS.md").exists():
        if task_type in ["feature", "architecture", "planning", None]:
            protocol_steps.append("3. Read DECISIONS.md for past decisions")
        else:
            protocol_steps.append("3. Skip DECISIONS.md (not needed for bugfix/test/quality tasks)")
```

**Token Savings**:
- KareMatch: 1,214 tokens (skip for 80% of bugfix/test sessions)
- CredentialMate: 3,988 tokens (skip for 80% of bugfix/test sessions)
- Average savings across repos: ~2,100 tokens

**Total with Conditional Loading**: ~9,960 tokens saved

---

## Risks and Mitigations

### Risk 1: Loss of Historical Context
**Concern**: Deleting Active Work section loses detailed session history

**Mitigation**:
- ✅ Session files contain full context (already loaded at step 4)
- ✅ claude-progress.txt tracks accomplishments (loaded at step 6)
- ✅ Keep Recent Milestones section (compressed to 5 lines)
- ✅ Archive detailed history to Knowledge Vault

**Verdict**: LOW RISK - session files are better source of truth

### Risk 2: Missing Cross-Repo Status
**Concern**: Deleting other repo status loses awareness of other projects

**Mitigation**:
- ✅ global-state-cache.md already contains this (loaded at step 5)
- ✅ Link from STATE.md to global-state-cache.md for easy reference

**Verdict**: NO RISK - this is pure duplication

### Risk 3: Architecture Amnesia
**Concern**: Deleting Architecture Overview loses system understanding

**Mitigation**:
- ✅ CATALOG.md contains complete architecture docs (loaded at step 1)
- ✅ Link from STATE.md to CATALOG.md for reference

**Verdict**: NO RISK - this is pure duplication

### Risk 4: Decision Context Loss
**Concern**: Skipping DECISIONS.md loses decision context for bugfixes

**Mitigation**:
- ✅ Agents can explicitly read DECISIONS.md if needed (not deleted, just not auto-loaded)
- ✅ Load DECISIONS.md for feature/architecture tasks where it matters
- ✅ Keep critical decisions in compressed format in STATE.md

**Verdict**: LOW RISK - most bugfixes don't need full decision history

---

## Session Files vs STATE.md: What Goes Where?

### STATE.md (Current Snapshot)
**Purpose**: Quick status check - "Where are we RIGHT NOW?"

**Should contain**:
- ✅ Current version, branch, last deploy
- ✅ Active blockers (things preventing progress)
- ✅ Next 3-5 steps
- ✅ Critical metrics (test coverage, bug count)
- ✅ Links to detailed resources

**Should NOT contain**:
- ❌ Detailed work logs (use session files)
- ❌ Historical decisions (use DECISIONS.md)
- ❌ Complete system status (use global-state-cache.md)
- ❌ Architecture diagrams (use CATALOG.md)

**Target Size**: 80-150 lines (like KareMatch) = 500-1,000 tokens

### Session Files (Detailed Work Logs)
**Purpose**: Complete record of what happened in a session

**Should contain**:
- ✅ Objective and context
- ✅ Detailed progress log with phases
- ✅ All findings and discoveries
- ✅ Complete files changed list
- ✅ Issues encountered and resolutions
- ✅ Full session reflection

**Loading**: Conditional (step 4) - only latest session loaded

---

## DECISIONS.md Optimization

### Current State
- **AI_Orchestrator**: No DECISIONS.md (ADRs in Knowledge Vault)
- **KareMatch**: 176 lines (1,214 tokens) - well-structured
- **CredentialMate**: 578 lines (3,988 tokens) - could be pruned

### Recommendation for CredentialMate DECISIONS.md

**Option 1**: Keep all decisions, but conditional loading (Option C above)
- Pro: No loss of context
- Con: Still high token cost when loaded

**Option 2**: Summarize old decisions, keep recent ones
- Pro: Reduces token cost
- Con: Requires maintenance

**Option 3**: Link to Knowledge Vault ADRs (like AI_Orchestrator)
- Pro: Single source of truth
- Con: Vault not always accessible (iOS)

**Recommendation**: **Option 1** (conditional loading) - simplest with good ROI

---

## Link Opportunities Across Documentation

### Current Duplication Issues

1. **Architecture duplicated** (CATALOG.md vs STATE.md)
   - Fix: Delete from STATE.md, link to CATALOG.md

2. **Other repo status duplicated** (STATE.md vs global-state-cache.md)
   - Fix: Delete from STATE.md, link to global-state-cache.md

3. **Decisions duplicated** (STATE.md vs DECISIONS.md)
   - Fix: Delete from STATE.md, link to DECISIONS.md

4. **Session details duplicated** (STATE.md Active Work vs session files)
   - Fix: Delete from STATE.md, link to latest session file

### Proposed Link Standard

**In STATE.md**:
```markdown
## Architecture Overview

See [CATALOG.md](./CATALOG.md) for complete documentation structure.

## Other Repositories

See [.aibrain/global-state-cache.md](./.aibrain/global-state-cache.md) for KareMatch and CredentialMate status.

## Recent Work

See [sessions/cross-repo/active/20260118-1130-3-repo-memory-unification.md](./sessions/cross-repo/active/20260118-1130-3-repo-memory-unification.md) for latest session details.

## Past Decisions

See [DECISIONS.md](./DECISIONS.md) for architectural decisions and rationale.
```

**Benefits**:
- Single source of truth (no sync issues)
- Reduced token costs
- Easier maintenance
- Clear navigation path

---

## Implementation Plan

### Phase 2A: AI_Orchestrator STATE.md Pruning (5,255 token savings)

1. **Backup current STATE.md** to `archive/2026-01/STATE-pre-phase2.md`

2. **Delete sections**:
   - Active Work (604 lines) → Replace with link to session file
   - Other repo status (48 lines) → Link to global-state-cache.md
   - Architecture Overview (28 lines) → Link to CATALOG.md
   - Directory Status (6 lines) → Delete
   - v4 Summary (50+ lines) → Archive to vault

3. **Compress sections**:
   - Recent Milestones (35 → 5 lines)
   - Success Metrics (13 → 3 lines)

4. **Add links section** at top:
   ```markdown
   ## Quick Navigation
   - 📋 Latest Session: [sessions/cross-repo/active/20260118-1130-3-repo-memory-unification.md]
   - 🗺️ Architecture: [CATALOG.md]
   - 🌐 Other Repos: [.aibrain/global-state-cache.md]
   - 📚 Decisions: Knowledge Vault ADRs
   ```

5. **Verify**: Run startup protocol and confirm token reduction

**Result**: 849 lines → ~100 lines (88% reduction), 5,861 → ~690 tokens

### Phase 2B: CredentialMate STATE.md Pruning (2,700 token savings)

1. **Backup current STATE.md** to `archive/2026-01/STATE-pre-phase2.md`

2. **Delete sections**:
   - All Systems Status (144 lines) → Link to global-state-cache.md
   - CME Reporting Discoveries (103 lines) → Move to session file
   - Decision Points Made (29 lines) → Link to DECISIONS.md

3. **Compress sections**:
   - Current Implementation Status (93 → 30 lines)
   - Verification Checklist (33 → 10 lines)

4. **Add links section** at top

5. **Move CME discoveries** to proper session file: `sessions/credentialmate/archive/20260109-cme-reporting-discoveries.md`

**Result**: 538 lines → ~200 lines (63% reduction), 3,712 → ~1,380 tokens

### Phase 2C: Conditional DECISIONS.md Loading (2,100 token savings)

1. **Update `context_preparation.py`**:
   - Add `task_type` parameter
   - Conditional DECISIONS.md loading logic

2. **Update `claude/cli_wrapper.py`**:
   - Pass `task_type` to `get_startup_protocol_prompt()`

3. **Test**:
   - Bugfix task: DECISIONS.md should be skipped
   - Feature task: DECISIONS.md should be loaded

**Result**: Average 2,100 tokens saved per bugfix/test session (80% of sessions)

### Phase 2D: Verification

1. **Token count verification**:
   ```bash
   # Before
   wc -w STATE.md DECISIONS.md CATALOG.md CLAUDE.md | tail -1

   # After
   wc -w STATE.md DECISIONS.md CATALOG.md CLAUDE.md | tail -1
   ```

2. **Startup test**:
   - Run autonomous loop with `--dry-run`
   - Verify protocol loads correctly
   - Check no missing context errors

3. **Commit**:
   ```bash
   git commit -m "perf(phase2): prune STATE.md and conditional DECISIONS.md loading

   Token savings:
   - AI_Orchestrator STATE.md: 5,255 tokens (88% reduction)
   - CredentialMate STATE.md: 2,700 tokens (63% reduction)
   - Conditional DECISIONS.md: ~2,100 tokens (avg per session)
   - Total: ~10,055 tokens saved

   BREAKING: STATE.md now links to session files instead of duplicating content

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

---

## Expected Impact

### Token Cost Reduction

| Phase | Savings | Cumulative | Total Reduction |
|-------|---------|------------|-----------------|
| Phase 1 | 9,703 | 9,703 | 45% |
| Phase 2A | 5,255 | 14,958 | 69% |
| Phase 2B | 2,700 | 17,658 | 82% |
| Phase 2C | 2,100 | 19,758 | 92% |

**Final Startup Cost**: 21,532 → 1,774 tokens (92% reduction!)

### Operational Impact

**Before Phase 1**:
- Startup: 21,532 tokens
- Tasks per session: 8-10
- Autonomy: 89%

**After Phase 1**:
- Startup: 10,856 tokens
- Tasks per session: 15-18
- Autonomy: 89%

**After Phase 2 (projected)**:
- Startup: 1,774 tokens
- Tasks per session: 30-40 (4x improvement!)
- Autonomy: 91%+ (more tokens for actual work)

### Quality Impact

- ✅ Less duplication = easier maintenance
- ✅ Single source of truth = fewer sync issues
- ✅ Clearer navigation = faster context loading
- ✅ More tokens for work = higher quality outputs

---

## Recommendation

**Proceed with Option C (Maximum Pruning + Conditional Loading)**

**Why**:
1. **Massive ROI**: 10,000 tokens saved (~92% reduction)
2. **Low Risk**: All pruned content preserved in proper locations
3. **Better Architecture**: Single source of truth, clear separation of concerns
4. **KareMatch Validation**: 80-line STATE.md works great in production
5. **Operational Win**: 30-40 tasks per session (4x current capacity)

**Risks are mitigated**:
- Session files preserve history
- Links maintain navigation
- Conditional loading preserves context when needed
- All deleted content archived

**Next Steps**:
1. Get user approval for Option C
2. Execute Phase 2A (AI_Orchestrator)
3. Execute Phase 2B (CredentialMate)
4. Execute Phase 2C (Conditional loading)
5. Verify token savings
6. Update ROADMAP.md (91%+ autonomy achieved)
