# Dev Team Implementation - Autonomous Work Plan

**Goal**: Implement complete Dev Team architecture (FeatureBuilder + TestWriter agents + integration)

**Priority**: P0 - Critical Foundation
**Estimated Time**: 8-10 hours (agent execution time)
**Dependencies**: None (all prerequisites met)

---

## Context

The AI Orchestrator currently has a fully operational QA Team (BugFix, CodeQuality agents) achieving 89% autonomy. However, the Dev Team architecture planned in v5 has never been implemented. This blocks feature development capability.

**Current State**:
- ✅ QA Team operational (BugFix, CodeQuality)
- ✅ Autonomous loop works for bugfix tasks
- ✅ Wiggum iteration control (15-50 retries)
- ✅ Dev Team contract exists (`governance/contracts/dev-team.yaml`)
- ❌ No Dev Team agents (FeatureBuilder, TestWriter)
- ❌ No feature work queue format
- ❌ No feature workflow in autonomous loop

**Target State**:
- ✅ FeatureBuilder agent implemented
- ✅ TestWriter agent implemented
- ✅ Feature work queue format defined
- ✅ Autonomous loop handles features
- ✅ First feature task ready to run

---

## Implementation Tasks

### Task 1: Create FeatureBuilder Agent

**File**: `agents/featurebuilder.py`
**Template**: Use `agents/bugfix.py` as reference
**Contract**: `governance/contracts/dev-team.yaml`

**Requirements**:
1. Inherits from `BaseAgent`
2. Uses `ClaudeCliWrapper` for execution (like BugFix/CodeQuality)
3. Loads `dev-team` contract
4. Configuration:
   - `agent_name: "featurebuilder"`
   - `max_iterations: 50` (from contract)
   - `expected_completion_signal: "FEATURE_COMPLETE"`
5. Branch validation: Only works on `feature/*` branches
6. No per-commit Ralph verification (only at PR)
7. Can create new files (unlike BugFix)
8. Higher limits: 500 lines, 20 files, 10 new files

**Key Differences from BugFix**:
- BugFix: Modifies existing code only
- FeatureBuilder: Creates new code, new files, new components
- BugFix: 15 iterations, strict limits
- FeatureBuilder: 50 iterations, liberal limits
- BugFix: Ralph every commit
- FeatureBuilder: Ralph only at PR

**Implementation Notes**:
```python
class FeatureBuilderAgent(BaseAgent):
    def __init__(self, app_adapter, config=None):
        self.contract = contract.load("dev-team")  # Not "featurebuilder"
        self.config = AgentConfig(
            agent_name="featurebuilder",
            max_iterations=50,
            expected_completion_signal="FEATURE_COMPLETE"
        )

    def execute(self, task_id: str) -> Dict[str, Any]:
        # Validate branch (must be feature/*)
        current_branch = get_current_branch()
        if not current_branch.startswith("feature/"):
            return {"status": "blocked", "reason": "Must be on feature/* branch"}

        # Use Claude CLI (same as BugFix)
        wrapper = ClaudeCliWrapper(project_dir)
        result = wrapper.execute_task(
            prompt=task_description,
            timeout=600  # 10 minutes (features take longer)
        )

        # No per-commit Ralph (contract says verify_on_commit: false)
        return {
            "status": "completed" if result.success else "failed",
            "output": result.output
        }
```

---

### Task 2: Create TestWriter Agent

**File**: `agents/testwriter.py`
**Template**: Use `agents/bugfix.py` as reference
**Contract**: `governance/contracts/dev-team.yaml`

**Requirements**:
1. Specializes in writing Vitest/Playwright tests
2. Uses Claude CLI
3. Configuration:
   - `agent_name: "testwriter"`
   - `max_iterations: 15`
   - `expected_completion_signal: "TESTS_COMPLETE"`
4. Can use `.todo` for WIP tests (contract allows)
5. Must achieve 80%+ coverage (from contract)
6. Cannot delete existing tests (contract forbids)

**Prompt Engineering**:
The TestWriter should receive enhanced prompts like:
```
Write comprehensive tests for [feature].

Requirements:
- Use Vitest for unit tests
- Use Playwright for E2E tests (if needed)
- Follow existing test patterns in tests/unit/ and tests/e2e/
- Achieve 80%+ coverage
- Test happy paths AND edge cases
- Use .todo() for tests you can't complete yet

Signal completion with: <promise>TESTS_COMPLETE</promise>
```

---

### Task 3: Update Work Queue Format

**File**: `tasks/work_queue.py`

**Add Fields**:
```python
@dataclass
class Task:
    # Existing fields
    id: str
    description: str
    file: str
    status: str
    tests: List[str]

    # NEW fields for feature tasks
    type: str = "bugfix"  # "bugfix" | "feature" | "test"
    branch: Optional[str] = None  # "feature/matching-algorithm"
    agent: Optional[str] = None  # "BugFix" | "FeatureBuilder" | "TestWriter"
    completion_promise: Optional[str] = None  # Override default
    max_iterations: Optional[int] = None  # Override default
    requires_approval: List[str] = field(default_factory=list)  # ["new_api_endpoint"]
```

**Validation**:
- If `type="feature"`, branch must start with `feature/`
- If `type="bugfix"`, branch must be `main` or `fix/*`
- Agent must match task type

---

### Task 4: Create Feature Work Queue Generator

**File**: `cli/commands/generate_features.py`

**Functionality**:
```bash
aibrain generate-features --project karematch

# Reads: docs/planning/v5-Planning.md
# Outputs: tasks/work_queue_karematch_features.json
```

**Parsing Logic**:
1. Parse markdown sections (Priority 0, Priority 1, etc.)
2. Extract tasks from tables
3. Determine branch name from heading
4. Assign agent type (FeatureBuilder or TestWriter)
5. Set completion promise based on task type
6. Generate task IDs (FEAT-001, TEST-001, etc.)

**Output Example**:
```json
{
  "project": "karematch",
  "features": [
    {
      "id": "FEAT-001",
      "type": "feature",
      "description": "Implement deterministic matching logic",
      "file": "services/matching/src/routes.ts",
      "branch": "feature/matching-algorithm",
      "agent": "FeatureBuilder",
      "status": "pending",
      "tests": ["tests/unit/matching/routes.test.ts"],
      "completion_promise": "FEATURE_COMPLETE",
      "max_iterations": 50,
      "requires_approval": []
    },
    {
      "id": "TEST-001",
      "type": "test",
      "description": "Write matching tests with 90%+ coverage",
      "file": "tests/unit/matching/",
      "branch": "feature/matching-algorithm",
      "agent": "TestWriter",
      "status": "pending",
      "tests": [],
      "completion_promise": "TESTS_COMPLETE",
      "max_iterations": 15,
      "requires_approval": []
    }
  ]
}
```

---

### Task 5: Integrate into Factory

**File**: `agents/factory.py`

**Add to `create_agent()`**:
```python
def create_agent(task_type: str, project_name: str, ...):
    if task_type in ["BUG", "BUGFIX", "FIX"]:
        return BugFixAgent(adapter, config)
    elif task_type in ["LINT", "TYPE", "QUALITY", "CODEQUALITY"]:
        return CodeQualityAgent(adapter, config)
    elif task_type in ["FEAT", "FEATURE"]:
        from agents.featurebuilder import FeatureBuilderAgent
        return FeatureBuilderAgent(adapter, config)
    elif task_type in ["TEST", "TESTS"]:
        from agents.testwriter import TestWriterAgent
        return TestWriterAgent(adapter, config)
    else:
        raise ValueError(f"Unknown task type: {task_type}")

def infer_agent_type(task_id: str) -> str:
    """Infer agent type from task ID prefix"""
    prefix = task_id.split('-')[0].upper()
    if prefix in ["BUG", "BUGFIX", "FIX"]:
        return "BugFix"
    elif prefix in ["LINT", "TYPE", "QUALITY"]:
        return "CodeQuality"
    elif prefix in ["FEAT", "FEATURE"]:
        return "FeatureBuilder"
    elif prefix in ["TEST", "TESTS"]:
        return "TestWriter"
    else:
        return "BugFix"  # Default
```

---

### Task 6: Update Autonomous Loop

**File**: `autonomous_loop.py`

**Add Feature Support**:
```python
async def run_autonomous_loop(...):
    # Load work queue
    queue_path = Path(__file__).parent / "tasks" / f"work_queue_{project_name}.json"

    # NEW: Support feature queue
    if queue_type == "features":
        queue_path = Path(__file__).parent / "tasks" / f"work_queue_{project_name}_features.json"

    for iteration in range(max_iterations):
        task = queue.get_next_pending()

        # NEW: Handle feature tasks
        if task.type == "feature":
            # Create/checkout feature branch
            if task.branch and not branch_exists(task.branch):
                create_branch(task.branch, from_branch="main")
                checkout_branch(task.branch)

            # Check requires_approval items
            if task.requires_approval:
                print(f"⚠️  Task requires approval for: {task.requires_approval}")
                # Pause and ask human
                approval = input("Approve? [y/N]: ")
                if approval.lower() != 'y':
                    queue.mark_blocked(task.id, "Human rejected approval")
                    continue

        # Create agent (factory handles feature vs bugfix)
        agent = create_agent(
            task_type=infer_agent_type(task.id),
            project_name=project_name,
            ...
        )

        # Run iteration loop
        result = loop.run(task_id, task_description, ...)

        # Handle result (same as before)
```

---

### Task 7: Create First Feature Task

**File**: `tasks/work_queue_karematch_features.json`

**Manually create first task** (before generator exists):
```json
{
  "project": "karematch",
  "features": [
    {
      "id": "FEAT-MATCH-001",
      "type": "feature",
      "description": "Implement deterministic matching logic in /api/matching/find endpoint. The endpoint currently returns null. It should return an array of scored therapist matches based on client preferences (insurance, specialties, availability). Use the existing TherapistMatcher class.",
      "file": "services/matching/src/routes.ts",
      "branch": "feature/matching-algorithm",
      "agent": "FeatureBuilder",
      "status": "pending",
      "tests": ["services/matching/tests/routes.test.ts"],
      "completion_promise": "FEATURE_COMPLETE",
      "max_iterations": 50,
      "requires_approval": []
    }
  ]
}
```

---

## Testing Strategy

After implementation:

1. **Unit Test**: Instantiate agents and verify config
   ```python
   agent = FeatureBuilderAgent(karematch_adapter)
   assert agent.config.max_iterations == 50
   assert agent.config.agent_name == "featurebuilder"
   ```

2. **Integration Test**: Run first feature task
   ```bash
   python autonomous_loop.py --project karematch --queue features --max-iterations 10
   ```

3. **Validation**: Check branch created and code works
   ```bash
   cd /Users/tmac/karematch
   git checkout feature/matching-algorithm
   npm run test services/matching
   ```

---

## Success Criteria

- [ ] `agents/featurebuilder.py` exists and follows contract
- [ ] `agents/testwriter.py` exists and follows contract
- [ ] Work queue format supports `type`, `branch`, `agent` fields
- [ ] Factory can instantiate FeatureBuilder and TestWriter
- [ ] Autonomous loop handles feature tasks
- [ ] First feature task completes successfully
- [ ] All existing tests still pass (no regressions)

---

## Documentation Updates

After completion:

1. Update `STATE.md` to v5.4
2. Create session handoff: `sessions/2026-01-06-dev-team-implementation.md`
3. Update `DECISIONS.md` with implementation choices
4. Update `CLAUDE.md` with Dev Team usage instructions

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Feature too complex for single task | Break into sub-tasks (FEAT-001-a, FEAT-001-b) |
| Agent creates broken code | Wiggum will retry up to 50 times |
| Conflicts with QA Team | Work on feature branch only (isolated) |
| Long execution time | Set realistic expectations (10+ hours) |

---

## Reference Files

**Templates**:
- `agents/bugfix.py` - Agent structure
- `agents/codequality.py` - Claude CLI integration
- `governance/contracts/dev-team.yaml` - Contract to enforce

**Documentation**:
- `docs/planning/v5-Planning.md` - Full v5 architecture
- `STATE.md` - Current system state
- `CLAUDE.md` - Usage instructions

---

**Ready to Execute**: ✅
**Blockers**: None
**Next Step**: Run autonomous loop with this plan
