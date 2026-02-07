#!/bin/bash
# Session Start Memory Hook
# Loads and injects session state at the start of every session
# This hook fires on startup, resume, clear, and after compaction

set -e

# Read hook input from stdin
INPUT=$(cat)

# Extract key fields
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
SOURCE=$(echo "$INPUT" | jq -r '.source // "startup"')
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')

# Determine project directory
PROJECT_DIR="$CWD"
if [ -n "$CLAUDE_PROJECT_DIR" ]; then
    PROJECT_DIR="$CLAUDE_PROJECT_DIR"
fi

AIBRAIN_DIR="$PROJECT_DIR/.aibrain"

# Build context to inject
CONTEXT=""

# 1. Load most recent session state using Python
if command -v python3 &> /dev/null; then
    SESSION_CONTEXT=$(python3 << PYTHON_SCRIPT 2>/dev/null || echo ""
import sys
import json
sys.path.insert(0, "$PROJECT_DIR")
try:
    from orchestration.session_state import SessionState
    import os

    # Check for any active sessions
    sessions = SessionState.get_all_sessions(project=os.path.basename("$PROJECT_DIR"))

    if sessions:
        # Get the most recent session
        latest = sessions[0]
        task_id = latest.get('task_id', '')

        if task_id:
            session = SessionState(task_id=task_id, project=os.path.basename("$PROJECT_DIR"))
            try:
                data = session.get_latest()
                if data:
                    output = {
                        "task_id": task_id,
                        "phase": data.get('phase', 'unknown'),
                        "status": data.get('status', 'unknown'),
                        "iteration": data.get('iteration_count', 0),
                        "next_steps": data.get('next_steps', [])[:3],
                        "last_output": (data.get('last_output', '')[:200] + '...') if len(data.get('last_output', '')) > 200 else data.get('last_output', '')
                    }
                    print(json.dumps(output))
            except:
                pass
except Exception as e:
    pass
PYTHON_SCRIPT
)

    # Validate SESSION_CONTEXT is valid JSON before parsing
    if [ -n "$SESSION_CONTEXT" ] && echo "$SESSION_CONTEXT" | jq -e . >/dev/null 2>&1; then
        TASK_ID=$(echo "$SESSION_CONTEXT" | jq -r '.task_id // ""' 2>/dev/null)
        PHASE=$(echo "$SESSION_CONTEXT" | jq -r '.phase // ""' 2>/dev/null)
        STATUS=$(echo "$SESSION_CONTEXT" | jq -r '.status // ""' 2>/dev/null)
        ITERATION=$(echo "$SESSION_CONTEXT" | jq -r '.iteration // 0' 2>/dev/null)
        NEXT_STEPS=$(echo "$SESSION_CONTEXT" | jq -r '.next_steps | join(", ")' 2>/dev/null || echo "")

        CONTEXT="## Resumed Session State\n"
        CONTEXT+="- **Task**: $TASK_ID\n"
        CONTEXT+="- **Phase**: $PHASE\n"
        CONTEXT+="- **Status**: $STATUS\n"
        CONTEXT+="- **Iteration**: $ITERATION\n"
        if [ -n "$NEXT_STEPS" ]; then
            CONTEXT+="- **Next Steps**: $NEXT_STEPS\n"
        fi
        CONTEXT+="\n"
    fi
fi

# 2. Check for pre-compact state files (if resuming after compaction)
if [ "$SOURCE" = "compact" ] && [ -d "$AIBRAIN_DIR" ]; then
    LATEST_PRECOMPACT=$(ls -t "$AIBRAIN_DIR"/pre-compact-state-*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_PRECOMPACT" ] && [ -f "$LATEST_PRECOMPACT" ]; then
        CONTEXT+="## Pre-Compaction Context Available\n"
        CONTEXT+="State was saved before compaction. See: $LATEST_PRECOMPACT\n\n"
    fi
fi

# 3. Check STATE.md for current project state
if [ -f "$PROJECT_DIR/STATE.md" ]; then
    # Extract first 30 lines of STATE.md for quick context
    STATE_SUMMARY=$(head -30 "$PROJECT_DIR/STATE.md" | grep -E "^#|^\*\*|^-" | head -10)
    if [ -n "$STATE_SUMMARY" ]; then
        CONTEXT+="## Project State Summary (from STATE.md)\n"
        CONTEXT+="$STATE_SUMMARY\n\n"
    fi
fi

# If we have context to inject, return it
if [ -n "$CONTEXT" ]; then
    # Return as additionalContext in hookSpecificOutput
    jq -n --arg ctx "$CONTEXT" '{
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": $ctx
        }
    }'
else
    # No context to inject
    exit 0
fi
