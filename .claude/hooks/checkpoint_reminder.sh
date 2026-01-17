#!/bin/bash
# Checkpoint Reminder Hook
# Tracks tool calls and reminds Claude to checkpoint every N calls

COUNTER_FILE="/Users/tmac/1_REPOS/AI_Orchestrator/.claude/hooks/.checkpoint_counter"
THRESHOLD=10

# Initialize counter if not exists
if [ ! -f "$COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi

# Read current count
COUNT=$(cat "$COUNTER_FILE")
COUNT=$((COUNT + 1))

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
