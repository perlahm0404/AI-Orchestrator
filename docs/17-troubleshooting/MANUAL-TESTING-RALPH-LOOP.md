# Manual Testing Guide: Ralph Loop Integration

## Overview

This guide covers manual testing of the Ralph-Wiggum iteration loop integration completed in Phase 1-5.

**Status**: CLI registration complete, ready for manual testing

## Prerequisites

- Python 3.9+ environment
- AI Orchestrator repo at `/Users/tmac/Vaults/AI_Orchestrator`
- KareMatch repo at `/Users/tmac/karematch` (for integration tests)

## CLI Tests

### Test 1: Help Command

```bash
cd /Users/tmac/Vaults/AI_Orchestrator
python3 -m cli --help
```

**Expected**: Shows `ralph-loop` as available command

**Status**: ✅ PASSED (verified 2026-01-06)

### Test 2: Ralph-Loop Help

```bash
python3 -m cli ralph-loop --help
```

**Expected**: Shows usage with all options (agent, project, max-iterations, promise)

**Status**: ✅ PASSED (verified 2026-01-06)

### Test 3: Missing Required Arguments

```bash
python3 -m cli ralph-loop "Fix bug"
```

**Expected**: Error message about missing --agent and --project

**Status**: Not yet tested

### Test 4: Invalid Agent Name

```bash
python3 -m cli ralph-loop "Fix bug" --agent invalid --project karematch
```

**Expected**: Error message about invalid agent choice

**Status**: Not yet tested

## Unit Tests

### Test 5: Completion Signal Detection

```bash
python3 -m pytest tests/agents/test_completion_signals.py -v
```

**Expected**: 15 tests pass
- Simple promise tags
- Multi-word promises
- Whitespace normalization
- Case sensitivity
- Missing/malformed tags
- Multiple promises
- Empty promises

**Status**: ✅ PASSED (15/15 tests passing)

### Test 6: Iteration Tracking

```bash
python3 -m pytest tests/agents/test_iteration_tracking.py -v
```

**Expected**: 15 tests pass
- Single iteration recording
- Multiple iterations
- Regression detection
- Budget exhaustion
- History preservation
- Summary statistics

**Status**: ✅ PASSED (15/15 tests passing)

### Test 7: All Tests

```bash
python3 -m pytest tests/ -v
```

**Expected**: All tests pass (30+ tests)

**Status**: ✅ PASSED (30/30 tests passing)

## Integration Tests (Future)

These tests require actual agent execution and are planned for future testing:

### Test 8: BugFix Agent Loop (Dry Run)

```bash
# This will fail because agents not fully implemented yet
python3 -m cli ralph-loop "Fix authentication bug in login.ts" \
  --agent bugfix \
  --project karematch \
  --max-iterations 15 \
  --promise "DONE"
```

**Expected**:
- Agent starts iteration loop
- Creates state file at `.aibrain/agent-loop.local.md`
- Shows iteration progress
- Fails gracefully (agents not fully implemented)

**Status**: Not yet tested (blocked on agent implementation)

### Test 9: CodeQuality Agent Loop (Dry Run)

```bash
python3 -m cli ralph-loop "Remove console.log statements" \
  --agent codequality \
  --project karematch \
  --max-iterations 20 \
  --promise "CLEANUP_COMPLETE"
```

**Expected**: Similar to Test 8

**Status**: Not yet tested (blocked on agent implementation)

### Test 10: State File Persistence

```bash
# Run ralph-loop
python3 -m cli ralph-loop "Test task" --agent bugfix --project karematch

# Check state file exists
cat .aibrain/agent-loop.local.md
```

**Expected**:
- State file created with YAML frontmatter
- Shows iteration count, agent name, task description
- Markdown body shows progress

**Status**: Not yet tested

### Test 11: Iteration Budget Exhaustion

```bash
# Run with low iteration limit
python3 -m cli ralph-loop "Complex task" \
  --agent bugfix \
  --project karematch \
  --max-iterations 2
```

**Expected**:
- Runs 2 iterations
- Stops with "iteration budget exhausted" message
- Requires human approval

**Status**: Not yet tested

### Test 12: Completion Signal Detection

```bash
# Agent outputs completion signal
# (Requires mock agent that outputs <promise>DONE</promise>)
```

**Expected**:
- Loop exits successfully
- Shows completion promise in state file
- Returns success status

**Status**: Not yet tested (blocked on mock agent)

## Manual Verification Checklist

- [x] CLI help shows ralph-loop command
- [x] ralph-loop help shows all options
- [x] Unit tests pass (30/30)
- [ ] Missing required args shows error
- [ ] Invalid agent name shows error
- [ ] State file created on loop start
- [ ] Iteration count increments
- [ ] Budget exhaustion handled
- [ ] Completion signal detected
- [ ] Ralph verification runs per iteration
- [ ] Stop hook decisions work (ALLOW/BLOCK/ASK_HUMAN)

## Next Steps

1. **Implement agent execution stubs** - Allow dry-run testing without full agent implementation
2. **Create mock agents** - Test completion signal and stop hook logic
3. **Integration testing** - Run on real KareMatch bugs
4. **Load testing** - Test with high iteration counts
5. **Error recovery** - Test crash recovery and resume

## Known Limitations

- **Agent implementation incomplete**: BugFixAgent and CodeQualityAgent still use legacy execute methods
- **Ralph integration placeholder**: `ralph/engine.py` verify() raises NotImplementedError
- **No state persistence**: State files created but not loaded on resume
- **No stop hook integration**: Stop hook exists but not called by iteration loop yet

## Testing Timeline

- **Phase 1 (Complete)**: CLI registration, unit tests
- **Phase 2 (Planned)**: Dry-run integration tests
- **Phase 3 (Planned)**: Mock agent tests
- **Phase 4 (Planned)**: Real agent integration
- **Phase 5 (Planned)**: Production testing on KareMatch

## Success Criteria

For manual testing to be considered complete:
1. All unit tests pass (30/30) ✅
2. CLI commands work without errors ✅
3. State files created correctly ⏳
4. Iteration loop executes (dry-run) ⏳
5. Completion signals detected ⏳
6. Budget exhaustion handled ⏳
7. No regressions in existing functionality ⏳

**Current Status**: 2/7 criteria met (CLI and unit tests working)
