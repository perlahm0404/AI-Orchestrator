#!/bin/bash
# Checkpoint Reminder Hook
# Tracks tool calls and reminds Claude to checkpoint every N calls
# Auto-syncs STATE.md to other repos when modified

COUNTER_FILE="/Users/tmac/1_REPOS/AI_Orchestrator/.claude/hooks/.checkpoint_counter"
THRESHOLD=10
STATE_FILE="/Users/tmac/1_REPOS/AI_Orchestrator/STATE.md"
STATE_SYNC_SCRIPT="/Users/tmac/1_REPOS/AI_Orchestrator/utils/state_sync.py"
PYTHON_VENV="/Users/tmac/1_REPOS/AI_Orchestrator/.venv/bin/python"

# Initialize counter if not exists
if [ ! -f "$COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi

# Read current count
COUNT=$(cat "$COUNTER_FILE")
COUNT=$((COUNT + 1))

# Auto-sync STATE.md if it was modified in the last 5 seconds
if [ -f "$STATE_FILE" ] && [ -f "$STATE_SYNC_SCRIPT" ] && [ -x "$PYTHON_VENV" ]; then
    # Check if STATE.md was modified recently (within 5 seconds)
    if [ $(uname) = "Darwin" ]; then
        # macOS: use stat -f %m
        STATE_MTIME=$(stat -f %m "$STATE_FILE" 2>/dev/null || echo 0)
    else
        # Linux: use stat -c %Y
        STATE_MTIME=$(stat -c %Y "$STATE_FILE" 2>/dev/null || echo 0)
    fi
    CURRENT_TIME=$(date +%s)
    TIME_DIFF=$((CURRENT_TIME - STATE_MTIME))

    if [ $TIME_DIFF -le 5 ]; then
        echo "🔄 STATE.md modified - syncing to other repos..."
        "$PYTHON_VENV" "$STATE_SYNC_SCRIPT" sync ai_orchestrator 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ State synced to KareMatch and CredentialMate"
        fi
    fi
fi

# Check if threshold reached
if [ $COUNT -ge $THRESHOLD ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "⏰ CHECKPOINT REMINDER (${COUNT} tool calls since last checkpoint)"
    echo "═══════════════════════════════════════════════════════════════"
    echo "ACTION REQUIRED: Update 12-SESSION-PLANNING-STATE.md with:"
    echo "  - What was accomplished since last checkpoint"
    echo "  - Current working state"
    echo "  - Any decisions made"
    echo ""
    echo "After updating, run: echo 0 > $COUNTER_FILE"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
fi

# Save new count
echo "$COUNT" > "$COUNTER_FILE"
