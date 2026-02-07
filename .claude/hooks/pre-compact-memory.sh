#!/bin/bash
# Pre-Compact Memory Hook
# Saves session state BEFORE context compaction to prevent memory loss
# This hook fires when Claude Code is about to compact context

set -e

# Read hook input from stdin
INPUT=$(cat)

# Extract key fields
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""')
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')
TRIGGER=$(echo "$INPUT" | jq -r '.trigger // "auto"')

# Determine project directory
PROJECT_DIR="$CWD"
if [ -f "$PROJECT_DIR/.claude/settings.json" ] || [ -f "$PROJECT_DIR/CLAUDE.md" ]; then
    PROJECT_DIR="$CWD"
elif [ -n "$CLAUDE_PROJECT_DIR" ]; then
    PROJECT_DIR="$CLAUDE_PROJECT_DIR"
fi

# Create .aibrain directory if needed
AIBRAIN_DIR="$PROJECT_DIR/.aibrain"
mkdir -p "$AIBRAIN_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Save pre-compaction state
STATE_FILE="$AIBRAIN_DIR/pre-compact-state-$TIMESTAMP.json"

# Extract recent context from transcript if available
RECENT_CONTEXT=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    # Get last 50 lines of transcript for context
    RECENT_CONTEXT=$(tail -50 "$TRANSCRIPT_PATH" 2>/dev/null | jq -s '.' 2>/dev/null || echo "[]")
fi

# Build state object
cat > "$STATE_FILE" << EOF
{
  "saved_at": "$(date -Iseconds)",
  "session_id": "$SESSION_ID",
  "trigger": "$TRIGGER",
  "project_dir": "$PROJECT_DIR",
  "transcript_path": "$TRANSCRIPT_PATH",
  "pre_compact_context": $RECENT_CONTEXT
}
EOF

# Also update the main session state using Python if available
if command -v python3 &> /dev/null; then
    python3 << PYTHON_SCRIPT
import sys
sys.path.insert(0, "$PROJECT_DIR")
try:
    from orchestration.session_state import SessionState

    # Try to find current task from environment or use default
    import os
    task_id = os.environ.get('CURRENT_TASK_ID', 'CLAUDE-SESSION')
    project = os.path.basename("$PROJECT_DIR")

    session = SessionState(task_id=task_id, project=project)
    session.save({
        "iteration_count": 0,
        "phase": "pre_compact",
        "status": "compacting",
        "last_output": "Context compaction triggered ($TRIGGER). State preserved.",
        "next_steps": ["Resume from pre-compaction state", "Check $STATE_FILE for context"],
        "agent_type": "Claude-Code",
        "max_iterations": 100,
        "context_window": 1,
        "tokens_used": 0,
    })
    print("SessionState saved before compaction", file=sys.stderr)
except Exception as e:
    print(f"Warning: Could not save SessionState: {e}", file=sys.stderr)
PYTHON_SCRIPT
fi

# Output success message (shown in verbose mode)
echo "Pre-compact state saved to $STATE_FILE" >&2

# Return empty JSON (no blocking needed)
exit 0
