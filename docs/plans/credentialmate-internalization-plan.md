# CredentialMate AI Orchestrator Internalization Plan

## Executive Summary

**Goal**: Internalize AI Orchestrator governance into CredentialMate for standalone operation while maintaining sync capability with AI Orchestrator improvements.

**Strategy**: Merge both governance systems through layering (not replacement), copy Knowledge Objects locally, harmonize on AUTONOMOUS_MODE, and create sync mechanism for future updates.

**Timeline**: 5-7 days with comprehensive testing

---

## User Requirements

- **Gov Strategy**: Keep both, merge capabilities (best of both worlds)
- **KO Storage**: Copy locally, fully independent
- **Env Vars**: Harmonize on AUTONOMOUS_MODE
- **Update Path**: Maintain sync capability with AI Orchestrator

---

## Current State Analysis

### CredentialMate Native Governance (Pre-Existing)
**Location**: `/Users/tmac/credentialmate/`

**Strengths**:
- 11 blocking PreToolUse hooks (database-deletion-guardian, golden-path-guard-v3, TDD-enforcer, etc.)
- HIPAA-focused safety (5-layer database deletion policy, PHI detection)
- Trust registry with graduated autonomy (L0-L4)
- Golden pathway protection (upload→process→view workflow)
- Service contract validation (SSOT for docker-compose.yml)
- Uses `AUTONOMOUS_MODE` environment variable

**Hook Registration**: `.claude/settings.local.json`
- 11 PreToolUse hooks (execute BEFORE tool runs)
- 2 PostToolUse hooks (execute AFTER tool runs)

### AI Orchestrator Governance (Replicated)
**Location**: `/Users/tmac/credentialmate/` (replicated from AI_Orchestrator)

**Strengths**:
- Wiggum iteration control (completion signals, retry budgets 15-50)
- Ralph verification (PASS/FAIL/BLOCKED verdicts with HIPAA checks)
- Knowledge Object system (approved/drafts, 10.5x ROI)
- Bug discovery (Ruff, MyPy, Pytest, Guardrails)
- Multi-agent orchestration
- Session resume capability

**Current Status**:
- ✅ ralph/, governance/, orchestration/, agents/, discovery/ - WORKING
- ✅ autonomous_loop.py, cli.py - WORKING
- ⚠️ knowledge/ - Symlinked (needs internalization)
- ❌ ralph/watcher.py, orchestration/parallel_agents.py - Broken (adapter imports)

---

## Critical Conflicts Identified

1. **Stop Hook Duplication**
   - Both have `governance/hooks/stop_hook.py` with different logic
   - CredentialMate: R/O/A prompt for HIPAA guardrails
   - AI Orchestrator: Wiggum completion signals + iteration budgets
   - **Solution**: Already merged! Current stop_hook.py has both (lines 1-100)

2. **Knowledge Symlink**
   - `knowledge/` → `/Users/tmac/Vaults/AI_Orchestrator/knowledge`
   - Creates cross-repo dependency
   - **Solution**: Copy directory locally, remove symlink

3. **Adapter Import Errors**
   - `ralph/watcher.py` (line 42): `from adapters import get_adapter`
   - `orchestration/parallel_agents.py` (line 24): `from adapters import get_adapter`
   - **Solution**: Use LocalAdapter pattern (already working in agents/factory.py lines 84-93)

4. **Environment Variables**
   - Both use different variable names
   - **Solution**: Harmonize on `AUTONOMOUS_MODE` (already in CredentialMate)

---

## Implementation Architecture

### Layered Governance Model

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: PreToolUse Hooks (HIPAA Safety - FIRST)      │
│ • database-deletion-guardian.py                        │
│ • golden-path-guard-v3.py                             │
│ • TDD-enforcer.py                                      │
│ • 8 other native hooks                                 │
│ Priority: HIGHEST (blocks before action executes)      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Action Executes (Write, Edit, Bash, etc.)             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: PostToolUse Hooks (Iteration Control - AFTER)│
│ • governance/hooks/stop_hook.py (ALREADY MERGED)      │
│   - Wiggum completion signals                          │
│   - Iteration budgets                                  │
│   - Ralph verification (includes HIPAA)                │
│   - R/O/A prompt on BLOCKED                           │
│ Priority: SECONDARY (quality + iteration after safety) │
└─────────────────────────────────────────────────────────┘
```

**Key Insight**: PreToolUse hooks prevent bad actions. PostToolUse hooks enforce quality AFTER action succeeds. Sequential layering preserves HIPAA safety while adding Wiggum iteration control.

---

## Implementation Steps

### Step 1: Knowledge Object Internalization

**Goal**: Remove symlink, copy directory locally

**Script**: `scripts/internalize_knowledge.sh`

```bash
#!/bin/bash
# Remove symlink
rm /Users/tmac/credentialmate/knowledge

# Copy entire directory
cp -R /Users/tmac/Vaults/AI_Orchestrator/knowledge /Users/tmac/credentialmate/

# Create CredentialMate-specific config
cat > /Users/tmac/credentialmate/knowledge/config/credentialmate.json << 'EOF'
{
  "project": "credentialmate",
  "auto_approval": {
    "enabled": true,
    "thresholds": {"min_iterations": 2, "max_iterations": 10}
  },
  "tag_aliases": {
    "hipaa": ["phi", "protected-health-information", "compliance"]
  }
}
EOF

echo "✓ Knowledge Objects internalized"
```

**Metrics Decision**: Start fresh (don't copy metrics.json). CredentialMate-specific metrics will build quickly.

---

### Step 2: Adapter Import Fixes

**Goal**: Fix broken adapter imports in 2 files

#### Fix 1: ralph/watcher.py (line 42)

**Problem**: `from adapters import get_adapter`

**Solution**: Use LocalAdapter pattern from agents/factory.py

```python
# Add at top of ralph/watcher.py after imports
class LocalAdapter:
    def __init__(self, app_ctx):
        self.app_context = app_ctx
    def get_context(self):
        return self.app_context

# Replace line 42
# OLD: from adapters import get_adapter
# NEW: from ralph.config import APP_CONTEXT

# Update main() function
def main():
    # Use APP_CONTEXT directly
    adapter = LocalAdapter(APP_CONTEXT)
    # ... rest of watcher logic
```

#### Fix 2: orchestration/parallel_agents.py

**Problem**: `from adapters import get_adapter` (line 24)

**Solution**: **REMOVE FILE ENTIRELY**

Parallel agents require cross-repo adapter registry. For CredentialMate standalone:
- Single-agent iteration loop is sufficient
- `orchestration/iteration_loop.py` already handles sequential execution
- No need for parallel orchestration in standalone mode

```bash
rm /Users/tmac/credentialmate/orchestration/parallel_agents.py
```

---

### Step 3: Environment Variable Harmonization

**Goal**: Use AUTONOMOUS_MODE everywhere

**Files to Check**:
- `governance/kill_switch.py` - Already uses AUTONOMOUS_MODE ✅
- `autonomous_loop.py` - Already uses AUTONOMOUS_MODE ✅
- `autonomy-toggle.sh` - Already uses AUTONOMOUS_MODE ✅

**No changes needed!** CredentialMate already standardized on AUTONOMOUS_MODE.

---

### Step 4: Sync Mechanism Implementation

**Goal**: Create sync script for future AI Orchestrator updates

#### File 1: `.aibrain/sync-manifest.yaml`

Defines sync rules:
- **syncable_files**: Core logic (ralph/engine.py, orchestration/iteration_loop.py, agents/*.py)
- **protected_files**: CredentialMate-specific (ralph/config.py, ralph/hipaa_config.yaml, governance/contracts/*.yaml)
- **merge_strategy_files**: Require manual review (agents/factory.py)

#### File 2: `scripts/sync-from-orchestrator.sh`

Main sync script with:
- Dry-run mode (`--dry-run`)
- Auto-approve mode (`--yes`)
- Verbose mode (`--verbose`)
- Backup before sync
- Test validation after sync
- Auto-rollback on test failure

**Usage**:
```bash
# Preview changes
./scripts/sync-from-orchestrator.sh --dry-run --verbose

# Interactive sync
./scripts/sync-from-orchestrator.sh

# Auto-sync all
./scripts/sync-from-orchestrator.sh --yes
```

#### File 3: `sync_tools/filter_changed_files.py`

Python helper to categorize files based on manifest rules.

#### File 4: `docs/sync-from-orchestrator.md`

User documentation:
- When to sync (weekly, on-demand)
- How to sync (commands)
- What gets synced (categories)
- Troubleshooting (rollback, conflicts)

---

## Testing Strategy

### Unit Tests (`tests/test_governance_merge.py`)

Create comprehensive tests:

```python
def test_native_hooks_still_work():
    """Verify all 11 PreToolUse hooks registered and functional."""
    # Test database-deletion-guardian blocks production deletions
    # Test golden-path-guard asks for docker-compose changes
    # Test TDD-enforcer blocks production code without tests
    pass

def test_ai_orchestrator_systems_work():
    """Verify AI Orchestrator components functional."""
    # Test Ralph runs without adapter errors
    # Test agents/factory uses LocalAdapter correctly
    # Test autonomous_loop.py starts without crashes
    pass

def test_knowledge_objects_local():
    """Verify Knowledge Objects fully local."""
    # Test knowledge/ is real directory (not symlink)
    # Test KO search works
    # Test CredentialMate config exists
    pass

def test_stop_hook_merged():
    """Verify stop hook has both Wiggum + HIPAA logic."""
    # Test completion signal detection
    # Test iteration budget enforcement
    # Test Ralph verification runs
    # Test HIPAA-specific R/O/A prompt
    pass
```

### HIPAA Compliance Tests (`tests/test_hipaa_compliance.py`)

**CRITICAL**: These tests MUST pass before deployment.

```python
def test_hipaa_violations_blocked():
    """Verify HIPAA violations escalate to BLOCKED verdict."""
    # Test PHI logging blocked by Ralph
    # Test production DB deletions permanently blocked
    pass

def test_golden_pathway_protected():
    """Verify golden pathway workflow always works."""
    # Test upload→S3→worker→Bedrock→review flow
    # Test S3 bucket config validation
    pass
```

### Manual Smoke Tests

Checklist:
- [ ] Native hooks work (11/11 pass)
- [ ] AI Orchestrator systems work (Ralph, bug discovery, KO search, autonomous loop)
- [ ] Stop hook merge works (completion signals, R/O/A prompts)
- [ ] HIPAA compliance maintained (database guardian, PHI detection)
- [ ] Autonomous mode toggle works (`./autonomy-toggle.sh on/off/status`)
- [ ] Knowledge Objects accessible (no symlink, local directory)
- [ ] Sync script works (`--dry-run` mode)

---

## Rollback Plan

### Backup Script

`scripts/backup_before_merge.sh`:
```bash
#!/bin/bash
BACKUP_DIR=".aibrain/backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup critical files
cp -R governance/ "$BACKUP_DIR/"
cp -R knowledge/ "$BACKUP_DIR/"
cp ralph/watcher.py "$BACKUP_DIR/"
cp orchestration/parallel_agents.py "$BACKUP_DIR/" 2>/dev/null || true

echo "✓ Backup created: $BACKUP_DIR"
```

### Rollback Script

`scripts/rollback_merge.sh`:
```bash
#!/bin/bash
BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: ./rollback_merge.sh /path/to/backup"
    exit 1
fi

# Restore all files
cp -R "$BACKUP_DIR"/* .

echo "✓ Rollback complete from: $BACKUP_DIR"
```

### Decision Matrix

| Test Failure | Action |
|--------------|--------|
| HIPAA tests fail | **ROLLBACK IMMEDIATELY** (CRITICAL) |
| Stop hook broken | Rollback (High severity) |
| Unit tests fail | Fix first, then retry (High severity) |
| Adapter import errors | Fix imports, no rollback needed (Medium) |
| KO search broken | Fix service.py, no rollback (Low) |

---

## Migration Timeline

| Day | Task | Hours |
|-----|------|-------|
| **Day 1** | Preparation & Backup | 2h |
| | • Create backup script | 0.5h |
| | • Run backup | 0.5h |
| | • Run baseline tests | 1h |
| **Day 2** | Adapter Import Fixes | 3h |
| | • Fix ralph/watcher.py | 1h |
| | • Remove parallel_agents.py | 0.5h |
| | • Test no adapter errors | 1.5h |
| **Day 3** | Knowledge Internalization | 2h |
| | • Run internalization script | 0.5h |
| | • Verify directory structure | 0.5h |
| | • Test KO search works | 1h |
| **Day 4** | Sync Script Creation | 4h |
| | • Create sync manifest | 1h |
| | • Create sync script | 2h |
| | • Test dry-run mode | 1h |
| **Day 5** | Testing & Validation | 6h |
| | • Run unit tests | 2h |
| | • Run HIPAA compliance tests | 2h |
| | • Manual smoke tests | 2h |
| **Day 6** | Documentation | 2h |
| | • Update CLAUDE.md | 0.5h |
| | • Create sync docs | 1h |
| | • Write migration guide | 0.5h |
| **Day 7** | Final Commit | 1h |
| | • Git commit all changes | 0.5h |
| | • Update STATE.md | 0.5h |
| **TOTAL** | | **20h** |

---

## Critical Files for Implementation

### New Files to Create

#### CredentialMate Files

1. **scripts/internalize_knowledge.sh** (80 lines)
   - Removes symlink
   - Copies knowledge directory
   - Creates CredentialMate config

2. **scripts/backup_before_merge.sh** (20 lines)
   - Creates timestamped backup
   - Backs up critical files

3. **scripts/rollback_merge.sh** (15 lines)
   - Restores from backup directory

4. **.aibrain/sync-manifest.yaml** (380 lines)
   - Defines syncable/protected/merge files
   - Tracks sync version

5. **scripts/sync-from-orchestrator.sh** (350 lines)
   - Main sync script
   - Dry-run, auto-yes, verbose modes
   - Backup + test + rollback

6. **sync_tools/filter_changed_files.py** (80 lines)
   - Categorizes files based on manifest

7. **sync_tools/create_initial_manifest.py** (120 lines)
   - Generates initial sync manifest

8. **docs/sync-from-orchestrator.md** (200 lines)
   - User documentation for sync process

#### AI Orchestrator Files

9. **/Users/tmac/Vaults/AI_Orchestrator/docs/plans/credentialmate-internalization-plan.md**
   - Complete copy of this plan for reference
   - Serves as template for future project internalizations
   - Institutional memory in framework source
   - Easy access for KareMatch or other projects

10. **/Users/tmac/Vaults/AI_Orchestrator/docs/internalization-guide.md** (NEW)
    - Generic guide extracted from CredentialMate experience
    - Step-by-step process for any project
    - Decision matrix for agent placement
    - Sync mechanism setup instructions

### Files to Modify

1. **ralph/watcher.py** (30 lines modified)
   - Add LocalAdapter class
   - Replace adapter import with ralph.config

2. **tests/test_governance_merge.py** (NEW - 200 lines)
   - Unit tests for merge verification

3. **tests/test_hipaa_compliance.py** (NEW - 150 lines)
   - HIPAA-specific compliance tests

### Files to Delete

1. **orchestration/parallel_agents.py**
   - Remove entirely (not needed for standalone)

2. **knowledge/** (symlink)
   - Remove symlink, replace with real directory

---

## Success Metrics

**Must achieve ALL before marking merge complete:**
- [ ] Adapter imports: 0
- [ ] Unit test pass rate: 100%
- [ ] HIPAA test pass rate: 100%
- [ ] Knowledge Objects accessible: Yes
- [ ] Autonomous loop starts: Yes
- [ ] Bug discovery works: Yes
- [ ] Native hooks work: 11/11 pass
- [ ] Ralph verification: No crashes
- [ ] Sync script works: Yes (dry-run tested)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| HIPAA compliance broken | Low | CRITICAL | HIPAA tests mandatory. Rollback immediately if fail. |
| Stop hook logic error | Medium | High | Extensive unit tests. Preserve both logic paths. Current version already merged. |
| Knowledge Objects broken | Low | Medium | Test KO search early. Copy approved/ AND drafts/. |
| Adapter imports persist | Medium | Medium | LocalAdapter everywhere. Grep for remaining imports. |
| Sync script errors | Low | Medium | Dry-run mode available. Test before real sync. |

---

## Verification Checklist

After implementation, verify:

### Standalone Operation
- [ ] Can run without `/Users/tmac/Vaults/AI_Orchestrator/` present
- [ ] No symlinks to AI_Orchestrator
- [ ] No adapter imports
- [ ] Knowledge Objects fully local

### Governance Integration
- [ ] All 11 PreToolUse hooks registered in `.claude/settings.local.json`
- [ ] Stop hook runs after Write/Edit/Bash tools
- [ ] Ralph verification includes HIPAA checks
- [ ] AUTONOMOUS_MODE environment variable works

### Autonomous Systems
- [ ] `python cli.py discover-bugs` works
- [ ] `python cli.py autonomous --max-iterations 50` works
- [ ] `./autonomy-toggle.sh on/off/status` works
- [ ] Work queue processing completes

### Sync Capability
- [ ] `./scripts/sync-from-orchestrator.sh --dry-run` works
- [ ] Manifest categorizes files correctly
- [ ] Backup created before sync
- [ ] Tests run after sync
- [ ] Rollback works if tests fail

---

## Agent Architecture Strategy

### Current Agent Status

**Already Replicated in CredentialMate** ✅:
- BugFixAgent (bugfix.py)
- CodeQualityAgent (codequality.py)
- FeatureBuilderAgent (featurebuilder.py)
- TestWriterAgent (testwriter.py)
- BaseAgent protocol (base.py)
- Agent factory with LocalAdapter (factory.py)

**Verdict**: All core agentic capabilities ARE already in CredentialMate!

### Recommended Architecture: Hybrid (Core vs Specialized)

```
AI Orchestrator = Framework Source
├─ Core Agents (Universal, Proven)
│  ├─ BugFixAgent ────────► sync to projects
│  ├─ CodeQualityAgent ───► sync to projects
│  ├─ FeatureBuilderAgent ► sync to projects
│  └─ TestWriterAgent ────► sync to projects
│
└─ Base Abstractions (New agents)
   ├─ BaseProjectManager ─► projects extend
   └─ BaseProgramManager ─► projects extend

CredentialMate = Standalone + Specialized
├─ Synced Core Agents (From AI Orch) ✅
│  └─ All 4 agents working with LocalAdapter
│
└─ Native Specialized Agents (NEW)
   ├─ program_manager.py (HIPAA-aware coordination)
   ├─ project_manager.py (PHI-safe task management)
   └─ compliance_validator.py (HIPAA-specific)
```

### Decision Matrix: Where to Build New Agents

**Score each factor 1-5, total determines placement:**
- **13-20 points** → AI Orchestrator (universal, sync to projects)
- **6-12 points** → Hybrid (base in AI Orch, impl in project)
- **0-5 points** → Native to project

**Factors**:
1. Generality (works for all projects?)
2. Stability (pattern proven?)
3. Customization (how much project-specific logic?)
4. HIPAA Sensitivity (handles PHI/compliance?)
5. Reusability (3+ projects benefit?)

### New Agent Placement Decisions

#### Program Manager Agent
**Score**: 11 → **HYBRID**

**Build**:
- Framework: `AI_Orchestrator/agents/base_program_manager.py`
- Implementation: `credentialmate/agents/program_manager.py`

**Rationale**:
- Sprint planning differs per project (HIPAA for CM, feature flags for KM)
- Base protocol captures common coordination patterns
- Projects customize for domain-specific needs

**Capabilities**:
- Multi-project sprint planning
- Resource allocation across teams
- HIPAA-aware user story management (for CredentialMate)
- Cross-project dependency tracking

#### Project Manager Agent
**Score**: 12 → **HYBRID (leaning AI Orch)**

**Build**:
- Framework: `AI_Orchestrator/agents/base_project_manager.py` (80% of logic)
- Extension: `credentialmate/agents/project_manager.py` (HIPAA validation layer)

**Rationale**:
- Task breakdown is 80% universal
- CredentialMate adds HIPAA validation (tasks don't expose PHI)
- High reusability across projects

**Capabilities**:
- Epic → Feature → Task decomposition
- Work queue generation
- Agent selection (route to BugFix vs Feature vs Quality)
- Dependency graph management

### AI Orchestrator's New Role

**Post-Internalization Identity**: Framework Source + Research Vault

**PRIMARY**: Governance Framework Source of Truth
- Core agents (proven patterns)
- Ralph verification engine
- Governance contracts
- Orchestration patterns (Wiggum)

**SECONDARY**: Multi-Project Learning Repository
- Knowledge Objects (cross-project patterns)
- Session reflections
- Metrics aggregation

**RESEARCH**: Agent Experimentation Lab
- Test new agents before production
- A/B test governance policies
- Validate on AI_Brain vault (30+ repos)

**NOT IN SCOPE**:
- ✗ Direct execution on projects (standalone operation)
- ✗ Project-specific business logic
- ✗ HIPAA/domain compliance

### Migration Impact

**Additional Steps for Manager Agents** (+6 days):

1. **Knowledge Internalization** (1 day) - Copy knowledge/ directory
2. **Base Manager Agents** (2 days) - Create in AI Orch
3. **CredentialMate Implementations** (3 days) - Extend base agents

**Updated Timeline**: 13 days (was 7 days)

---

## Expected Outcome

After implementation:

### CredentialMate
- **Standalone**: Operates fully independently (no cross-repo dependencies)
- **All Core Agents**: BugFix, CodeQuality, Feature, Test working ✅
- **New Manager Agents**: Program Manager + Project Manager (HIPAA-aware)
- **Merged Governance**: All 11 native hooks + AI Orchestrator governance
- **Zero Dependencies**: No cross-repo imports, no symlinks
- **HIPAA Compliant**: All safety guards maintained
- **Sync Ready**: Can pull AI Orchestrator improvements with single command
- **Production Ready**: Tested, documented, rollback plan in place

### AI Orchestrator
- **Plan Reference**: Complete internalization plan stored in `docs/plans/`
- **Internalization Guide**: Generic guide for future projects
- **Base Manager Agents**: BaseProjectManager, BaseProgramManager ready for reuse
- **Template**: KareMatch or future projects can follow same pattern
- **Institutional Memory**: Decisions and learnings documented in DECISIONS.md

---

## Next Steps After Approval

1. **Copy plan to AI Orchestrator** (0.5h)
   - Copy this plan to `/Users/tmac/Vaults/AI_Orchestrator/docs/plans/credentialmate-internalization-plan.md`
   - Create generic internalization guide at `AI_Orchestrator/docs/internalization-guide.md`
   - Serves as reference for future projects (KareMatch, others)

2. Run `scripts/backup_before_merge.sh` (0.5h)

3. Execute migration steps - Days 1-13 (48h)
   - **Days 1-7**: Core internalization (20h)
     - Day 1: Preparation & Backup (2h)
     - Day 2: Adapter Import Fixes (3h)
     - Day 3: Knowledge Internalization (2h)
     - Day 4: Sync Script Creation (4h)
     - Day 5: Testing & Validation (6h)
     - Day 6: Documentation (2h)
     - Day 7: Final Commit (1h)
   - **Days 8-10**: Base manager agents in AI Orch (16h)
     - Day 8: BaseProjectManager design + implementation (8h)
     - Day 9: BaseProgramManager design + implementation (8h)
     - Day 10: Testing base agents on AI_Brain vault (Buffer day)
   - **Days 11-13**: CredentialMate manager implementations (12h)
     - Day 11: CredentialMateProjectManager (6h)
     - Day 12: CredentialMateProgramManager (6h)
     - Day 13: Integration testing (Buffer day)

4. Run all tests (unit, HIPAA, smoke) (included in Day 5)

5. Verify success metrics checklist (included in Day 5)

6. Commit changes with detailed message (Day 7)

7. Update STATE.md and DECISIONS.md in both repos (1h)
   - AI_Orchestrator/STATE.md - Document internalization completion
   - AI_Orchestrator/DECISIONS.md - Record architecture decisions
   - CredentialMate/STATE.md - Document standalone status

**Estimated Total Effort**: 52 hours over 13 days

**Risk Level**: Medium (mitigated by backup + rollback + extensive testing)

**Confidence**: HIGH - Plans validated against actual codebase, rollback available, HIPAA tests mandatory
