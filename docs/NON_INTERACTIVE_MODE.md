# Non-Interactive Mode

## Overview

Non-interactive mode enables the autonomous loop to run completely unattended by auto-reverting changes when guardrail violations (BLOCKED verdicts) are detected.

## Problem Solved

Previously, the autonomous loop would crash with `EOFError` when running in background mode and encountering a guardrail violation that required human input (R/O/A prompt). This limited autonomy to ~60% because ~40% of tasks would trigger guardrails (adding `noqa` directives, modifying guardrail exceptions, etc.).

## Solution

The `--non-interactive` flag enables fully autonomous operation:
- **On BLOCKED verdict**: Automatically reverts changes and continues with next task
- **Logs violations**: All auto-reverted changes are logged to `.aibrain/guardrail-violations/YYYY-MM-DD.jsonl`
- **No crashes**: Process continues until all tasks are complete or max iterations reached

## Usage

### Command Line

```bash
# Interactive mode (default) - prompts on guardrail violations
python autonomous_loop.py --project credentialmate --max-iterations 100

# Non-interactive mode - auto-reverts on guardrail violations
python autonomous_loop.py --project credentialmate --max-iterations 100 --non-interactive
```

### Expected Output

**Non-Interactive Mode** (when guardrail is triggered):
```
============================================================
🚫 GUARDRAIL VIOLATION DETECTED
============================================================
❌ guardrails: FAIL
Reason: 1 guardrail violation(s) detected
- Pattern 'noqa' detected in file.py:line 42
============================================================
🤖 NON-INTERACTIVE MODE
============================================================
Auto-reverting changes and continuing with next task...
Guardrail violations are logged for later review.
============================================================
```

## Audit Trail

All auto-reverted guardrail violations are logged to:
```
.aibrain/guardrail-violations/2026-01-09.jsonl
```

**Log Format** (JSONL - one JSON object per line):
```json
{
  "timestamp": "2026-01-09T23:15:42.123456",
  "session_id": "TEST-CYCLEDATE-004",
  "verdict_type": "VerdictType.BLOCKED",
  "changes": ["apps/backend-api/tests/unit/test_file.py"],
  "summary": "❌ guardrails: FAIL\nReason: 1 guardrail violation(s) detected\n...",
  "auto_action": "REVERTED"
}
```

## Review Process

After an autonomous run with `--non-interactive`:

1. **Check the log**:
   ```bash
   cat .aibrain/guardrail-violations/$(date +%Y-%m-%d).jsonl | jq
   ```

2. **Review auto-reverted changes**:
   - Examine the `changes` field to see which files were affected
   - Read the `summary` field to understand what guardrail was triggered

3. **Manually fix if needed**:
   - If a change was legitimately safe, manually apply it with proper justification
   - Update guardrail rules if too strict

## Performance Impact

**Before** (Interactive Mode):
- Success Rate: 60% (3/5 tasks - 2 blocked waiting for human input)
- Crashes: Yes (EOF when reading a line)

**After** (Non-Interactive Mode):
- Success Rate: 60% (3/5 tasks - 2 auto-reverted)
- Crashes: No (continues processing all tasks)
- Audit Trail: Yes (all decisions logged)

## When to Use Each Mode

| Mode | Use Case |
|------|----------|
| **Interactive** | Development, debugging, when you want to manually approve risky changes |
| **Non-Interactive** | CI/CD, bulk fixing, overnight runs, when you trust guardrails to auto-revert bad changes |

## Safety Guarantees

**What Gets Auto-Reverted**:
- New `noqa` directives (linter suppressions)
- New `@ts-ignore` comments (type suppressions)
- New `eslint-disable` comments
- Modified `guardrail-exception` comments
- Bypassing Ralph verification (`--no-verify`)

**What Still Requires Human Approval** (in both modes):
- Iteration budget exhausted (max retries reached)
- None - all other BLOCKED verdicts are auto-reverted in non-interactive mode

## Environment Variable Alternative

For backward compatibility, you can also use:
```bash
export AUTO_GUARDRAIL_OVERRIDE=R  # Auto-revert
python autonomous_loop.py --project credentialmate
```

However, `--non-interactive` flag is preferred as it's more explicit and adds logging.

## Integration with CI/CD

```yaml
# GitHub Actions example
- name: Run Autonomous Loop
  run: |
    python autonomous_loop.py \
      --project credentialmate \
      --max-iterations 100 \
      --non-interactive

- name: Upload Guardrail Violations
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: guardrail-violations
    path: .aibrain/guardrail-violations/
```

## FAQ

**Q: Will it skip good changes?**
A: Possibly. If a change is safe but adds a `noqa` directive, it will be reverted. Review the log and manually apply if needed.

**Q: How do I know what was reverted?**
A: Check `.aibrain/guardrail-violations/YYYY-MM-DD.jsonl` - all decisions are logged.

**Q: Can I override specific guardrails in non-interactive mode?**
A: Not yet. Currently it's all-or-nothing. This is a safety feature.

**Q: What happens to the work queue?**
A: Tasks that trigger BLOCKED verdicts are marked as `blocked` with error `"Auto-reverted in non-interactive mode"`.

## Version History

- **v5.6** (2026-01-09): Initial implementation of `--non-interactive` flag
- Autonomy: Maintains 60% (same tasks complete, but no crashes)
- Improvement: 100% uptime (no EOFError crashes in background mode)
