#!/bin/bash
# Context Monitor Hook (Stop event)
# Detects when context is getting large and saves state before compaction can waste tokens
# Prompts user to start fresh session instead of compacting

set -e

# Read hook input from stdin
INPUT=$(cat)

# Extract fields
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""')
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')

# Don't run if already in a stop hook loop
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
    exit 0
fi

# Determine project directory
PROJECT_DIR="$CWD"
if [ -n "$CLAUDE_PROJECT_DIR" ]; then
    PROJECT_DIR="$CLAUDE_PROJECT_DIR"
fi

# Check transcript size as proxy for context usage
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    # Get file size in KB
    TRANSCRIPT_SIZE=$(du -k "$TRANSCRIPT_PATH" | cut -f1)

    # Threshold: 500KB transcript ≈ approaching context limit
    # Adjust based on experience
    THRESHOLD_KB=500

    if [ "$TRANSCRIPT_SIZE" -gt "$THRESHOLD_KB" ]; then
        # Save state before suggesting reset
        TIMESTAMP=$(date +%Y%m%d-%H%M%S)
        AIBRAIN_DIR="$PROJECT_DIR/.aibrain"
        mkdir -p "$AIBRAIN_DIR"

        # Save pre-reset state using Python
        if command -v python3 &> /dev/null; then
            python3 << PYTHON_SCRIPT 2>/dev/null || true
import sys
sys.path.insert(0, "$PROJECT_DIR")
try:
    from orchestration.session_state import SessionState
    import os

    task_id = os.environ.get('CURRENT_TASK_ID', 'CLAUDE-SESSION')
    project = os.path.basename("$PROJECT_DIR")

    session = SessionState(task_id=task_id, project=project)
    session.save({
        "iteration_count": 0,
        "phase": "context_full",
        "status": "needs_reset",
        "last_output": "Context approaching limit. State saved. Ready for fresh session.",
        "next_steps": ["Start fresh session with /clear or new conversation", "State will be auto-loaded on SessionStart"],
        "agent_type": "Claude-Code",
        "max_iterations": 100,
        "context_window": 1,
        "tokens_used": 0,
    })
    print("State saved before context reset", file=sys.stderr)
except Exception as e:
    print(f"Warning: {e}", file=sys.stderr)
PYTHON_SCRIPT
        fi

        # Return warning to user (shown as system message)
        jq -n --arg size "$TRANSCRIPT_SIZE" '{
            "systemMessage": "Context is getting large (\($size)KB). Consider running /clear to start fresh - your state has been saved and will auto-reload."
        }'
        exit 0
    fi
fi

# Context is fine, allow stop
exit 0
