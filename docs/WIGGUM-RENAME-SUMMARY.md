# Wiggum Rename Summary

**Date**: 2026-01-06

## What Changed

Renamed the iteration control system from "Ralph-Wiggum" to "Wiggum" to eliminate confusion with the Ralph verification system.

## Rationale

**Problem**: Having two systems both using "Ralph" in their names was confusing:
- Ralph Verification Engine (`ralph/engine.py`) - Code quality verification
- Ralph-Wiggum Pattern (`orchestration/iteration_loop.py`) - Iteration control

**Solution**: Clear separation of concerns:
- **Ralph** = Verification system (PASS/FAIL/BLOCKED verdicts)
- **Wiggum** = Iteration control system (manages loops, calls Ralph for verification)

## Changes Made

### Files Renamed
- `cli/commands/ralph_loop.py` → `cli/commands/wiggum.py`
- `tests/integration/test_ralph_loop.py` → `tests/integration/test_wiggum.py`

### CLI Command Renamed
```bash
# OLD
aibrain ralph-loop "Fix bug" --agent bugfix --project karematch

# NEW
aibrain wiggum "Fix bug" --agent bugfix --project karematch
```

### Session IDs Changed
- OLD: `ralph-20260106-111414`
- NEW: `wiggum-20260106-111414`

### Documentation Updated
- ✅ [CLAUDE.md](../CLAUDE.md) - Updated all references
- ✅ [STATE.md](../STATE.md) - Updated status section
- ✅ [cli/__main__.py](../cli/__main__.py) - Updated imports and help text
- ✅ [cli/commands/wiggum.py](../cli/commands/wiggum.py) - Updated docstrings
- ✅ [orchestration/iteration_loop.py](../orchestration/iteration_loop.py) - Updated comments
- ✅ [agents/bugfix.py](../agents/bugfix.py) - Updated method docs
- ✅ [agents/codequality.py](../agents/codequality.py) - Updated method docs
- ✅ [tests/integration/test_wiggum.py](../tests/integration/test_wiggum.py) - Updated comments

### Code Comments Updated
All references to "Ralph-Wiggum" or "Ralph loop" updated to "Wiggum" with clarification that Wiggum uses Ralph for verification.

## Architecture Clarity

```
┌─────────────────────────────────────────────────────────────┐
│                    Ralph System (Verification)              │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │  Full Ralph          │    │  Fast Verify         │      │
│  │  (ralph/engine.py)   │    │  (ralph/fast_verify) │      │
│  │  - 5 min verification│    │  - 30s verification  │      │
│  │  - Baseline compare  │    │  - Lint + Type + Test│      │
│  │  - Guardrails        │    │  - No guardrails     │      │
│  └──────────────────────┘    └──────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ called by
                              │
┌─────────────────────────────────────────────────────────────┐
│              Wiggum System (Iteration Control)              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  orchestration/iteration_loop.py                   │     │
│  │  - Iteration budgets                               │     │
│  │  - Stop hook (calls Ralph/Fast Verify)            │     │
│  │  - Completion signals (<promise>)                  │     │
│  │  - State persistence                               │     │
│  │  - Claude CLI integration                          │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Testing

All tests updated and passing:
- ✅ 42/42 tests passing
- ✅ `python3 -m cli wiggum --help` working
- ✅ CLI command functional
- ✅ Claude CLI integration verified

## Backward Compatibility

**Breaking Change**: The CLI command name changed from `ralph-loop` to `wiggum`.

Users must update any scripts or aliases:
```bash
# Update this
python3 -m cli ralph-loop "task"

# To this
python3 -m cli wiggum "task"
```

**Non-Breaking**: All internal APIs remain the same. Agent methods and classes unchanged.

## References

- Ralph = Verification (checks code quality)
- Wiggum = Iteration control (manages loops, uses Ralph)
- Fast Verify = Quick verification subset (part of Ralph system)

**Historical Note**: The name "Wiggum" comes from anthropics/claude-code's Ralph-Wiggum plugin, which inspired this iteration pattern. We split the name to clarify the two distinct systems.
