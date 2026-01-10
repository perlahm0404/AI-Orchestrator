# Autonomous KareMatch

**Command**: `/autonomous-karematch`

**Description**: Run autonomous bug-fixing loop for KareMatch with full Wiggum iteration control

## What This Does

Launches the AI Orchestrator autonomous loop for the KareMatch project:

1. **Auto-discovers bugs** (optional, via flag)
2. **Processes work queue** autonomously
3. **Fixes bugs** with 15-50 retry iterations per task
4. **Auto-commits** when Ralph verification passes
5. **Only interrupts** for guardrail violations (R/O/A prompt)

## Usage

The skill accepts optional arguments:

- `--discover` - Run bug discovery before processing queue
- `--max-iterations N` - Set max global iterations (default: 100)
- `--queue bugs|features` - Process bug queue or feature queue (default: bugs)

### Examples

```bash
# Standard autonomous mode (process existing queue)
/autonomous-karematch

# Discover bugs first, then process
/autonomous-karematch --discover

# Process feature queue instead of bug queue
/autonomous-karematch --queue features

# Limit to 50 global iterations
/autonomous-karematch --max-iterations 50
```

## Behavior

**Fully Autonomous**:
- Fixes lint, type, and test errors without asking
- Self-corrects up to 15-50 times per task (agent-specific)
- Auto-commits on success

**Human Interaction Only For**:
- Guardrail violations (e.g., `--no-verify` detected)
- Iteration budget exhausted

## Implementation

```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator

# Optional: Discover bugs first
if [[ "$@" == *"--discover"* ]]; then
    echo "🔍 Discovering bugs in KareMatch..."
    python3 -m cli.main discover-bugs --project karematch
    echo ""
fi

# Extract max-iterations argument
MAX_ITER=100
QUEUE_TYPE="bugs"

if [[ "$@" =~ --max-iterations[[:space:]]+([0-9]+) ]]; then
    MAX_ITER="${BASH_REMATCH[1]}"
fi

if [[ "$@" =~ --queue[[:space:]]+(bugs|features) ]]; then
    QUEUE_TYPE="${BASH_REMATCH[1]}"
fi

# Run autonomous loop
echo "🤖 Starting autonomous loop for KareMatch..."
echo "   Max iterations: $MAX_ITER"
echo "   Queue type: $QUEUE_TYPE"
echo ""

python3 autonomous_loop.py \
    --project karematch \
    --max-iterations "$MAX_ITER" \
    --queue "$QUEUE_TYPE"
```

## Session Resume

If interrupted (Ctrl+C or crash), simply run the same command again - it automatically resumes from the last state.

## Work Queue Location

Tasks are loaded from: `tasks/work_queue_karematch.json`

## Autonomy Level

- **KareMatch**: L2 autonomy (higher, stable codebase)
- **Autonomy Rate**: 89%
- **Tasks per session**: 30-50
- **Retry budget**: 15-50 per task

## Related Commands

- `/autonomous-credentialmate` - Same for CredentialMate project
- `aibrain discover-bugs --project karematch` - Manual bug discovery
- `aibrain status` - Check current task status
