#!/bin/bash
# Tmux Dashboard Orchestrator
# Builds a vertical pane dashboard mirroring all windows and sub-agents

set -e

DASHBOARD_SESSION="agent-dashboard"
CURRENT_SESSION=$(tmux display-message -p '#S')

echo "=== TMUX DASHBOARD ORCHESTRATOR ==="
echo "Current session: $CURRENT_SESSION"
echo ""

# Step 1: Kill existing dashboard if it exists
if tmux has-session -t "$DASHBOARD_SESSION" 2>/dev/null; then
    echo "🗑️  Killing existing dashboard session..."
    tmux kill-session -t "$DASHBOARD_SESSION"
fi

# Step 2: Gather window and pane information
echo "🔍 Discovering windows and panes..."
WINDOWS=$(tmux list-windows -t "$CURRENT_SESSION" -F "#{window_index}:#{window_name}")
WINDOW_COUNT=$(echo "$WINDOWS" | wc -l | xargs)

echo "📊 Found $WINDOW_COUNT windows"
echo ""

# Arrays to store summary data
declare -a WINDOW_NAMES
declare -a WINDOW_PANE_COUNTS
declare -a RUNNING_COMMANDS

# Step 3: Create dashboard session
echo "🏗️  Creating dashboard session..."
tmux new-session -d -s "$DASHBOARD_SESSION" -n "Dashboard"

FIRST_WINDOW=true
WINDOW_INDEX=0

# Step 4: Process each window
while IFS=: read -r WIN_IDX WIN_NAME; do
    echo "Processing window: $WIN_NAME (index: $WIN_IDX)"

    WINDOW_NAMES[$WINDOW_INDEX]="$WIN_NAME"

    # Get panes for this window
    PANES=$(tmux list-panes -t "$CURRENT_SESSION:$WIN_IDX" -F "#{pane_index}:#{pane_current_command}:#{pane_pid}")
    PANE_COUNT=$(echo "$PANES" | wc -l | xargs)
    WINDOW_PANE_COUNTS[$WINDOW_INDEX]=$PANE_COUNT

    echo "  └─ Found $PANE_COUNT pane(s)"

    # Create vertical split for this window (except first)
    if [ "$FIRST_WINDOW" = true ]; then
        FIRST_WINDOW=false
        TARGET_PANE="$DASHBOARD_SESSION:0.0"
    else
        tmux split-window -t "$DASHBOARD_SESSION:0" -h
        TARGET_PANE="$DASHBOARD_SESSION:0.{last}"
    fi

    # Add window header
    tmux send-keys -t "$TARGET_PANE" "clear" C-m
    tmux send-keys -t "$TARGET_PANE" "echo '════════════════════════════════'" C-m
    tmux send-keys -t "$TARGET_PANE" "echo '📁 WINDOW: $WIN_NAME'" C-m
    tmux send-keys -t "$TARGET_PANE" "echo '════════════════════════════════'" C-m
    tmux send-keys -t "$TARGET_PANE" "echo ''" C-m

    PANE_INDEX=0
    FIRST_PANE=true

    # Process each pane in this window
    while IFS=: read -r PANE_IDX PANE_CMD PANE_PID; do
        echo "    └─ Pane $PANE_IDX: $PANE_CMD (PID: $PANE_PID)"

        # Create horizontal split for additional panes (stack vertically within column)
        if [ "$FIRST_PANE" = false ]; then
            tmux split-window -t "$TARGET_PANE" -v
            TARGET_PANE="$DASHBOARD_SESSION:0.{last}"
        fi
        FIRST_PANE=false

        # Determine if this is an active process
        if [ "$PANE_CMD" = "bash" ] || [ "$PANE_CMD" = "zsh" ] || [ "$PANE_CMD" = "sh" ]; then
            # Shell is idle - show placeholder
            tmux send-keys -t "$TARGET_PANE" "echo '🔵 Pane $PANE_IDX: Idle Shell'" C-m
            tmux send-keys -t "$TARGET_PANE" "echo '   No active sub-agent running'" C-m
            tmux send-keys -t "$TARGET_PANE" "echo ''" C-m
        else
            # Active process - show live info
            RUNNING_COMMANDS+=("$WIN_NAME:Pane$PANE_IDX:$PANE_CMD")

            # Check if this is a Python autonomous loop
            if [[ "$PANE_CMD" == *"Python"* ]] || [[ "$PANE_CMD" == "python"* ]]; then
                # Try to find log file or output
                LOG_PATTERN="/tmp/claude/-Users-tmac-1-REPOS-AI-Orchestrator/tasks/*.output"

                tmux send-keys -t "$TARGET_PANE" "echo '🟢 Pane $PANE_IDX: Active Agent'" C-m
                tmux send-keys -t "$TARGET_PANE" "echo '   Process: $PANE_CMD'" C-m
                tmux send-keys -t "$TARGET_PANE" "echo '   PID: $PANE_PID'" C-m
                tmux send-keys -t "$TARGET_PANE" "echo ''" C-m
                tmux send-keys -t "$TARGET_PANE" "echo '   Monitoring agent activity...'" C-m

                # Try to tail recent task output
                LATEST_OUTPUT=$(ls -t $LOG_PATTERN 2>/dev/null | head -1 || echo "")
                if [ -n "$LATEST_OUTPUT" ]; then
                    tmux send-keys -t "$TARGET_PANE" "tail -f '$LATEST_OUTPUT'" C-m
                else
                    tmux send-keys -t "$TARGET_PANE" "ps -p $PANE_PID -o etime,args | tail -1" C-m
                fi
            else
                # Other active process
                tmux send-keys -t "$TARGET_PANE" "echo '🟢 Pane $PANE_IDX: Active Process'" C-m
                tmux send-keys -t "$TARGET_PANE" "echo '   Command: $PANE_CMD'" C-m
                tmux send-keys -t "$TARGET_PANE" "echo '   PID: $PANE_PID'" C-m
                tmux send-keys -t "$TARGET_PANE" "echo ''" C-m
                tmux send-keys -t "$TARGET_PANE" "watch -n 2 'ps -p $PANE_PID -o etime,pcpu,pmem,args 2>/dev/null || echo \"Process ended\"'" C-m
            fi
        fi

        ((PANE_INDEX++))
    done <<< "$PANES"

    ((WINDOW_INDEX++))
    echo ""
done <<< "$WINDOWS"

# Step 5: Apply even layout
echo "📐 Applying even vertical layout..."
tmux select-layout -t "$DASHBOARD_SESSION:0" even-horizontal

# Step 6: Print summary
echo ""
echo "════════════════════════════════════════════════"
echo "✅ DASHBOARD BUILD COMPLETE"
echo "════════════════════════════════════════════════"
echo ""
echo "📊 SUMMARY:"
echo "  Session: $DASHBOARD_SESSION"
echo "  Windows discovered: $WINDOW_COUNT"
echo ""

for i in "${!WINDOW_NAMES[@]}"; do
    echo "  📁 ${WINDOW_NAMES[$i]}: ${WINDOW_PANE_COUNTS[$i]} pane(s)"
done

echo ""
echo "🟢 RUNNING SUB-AGENTS:"
if [ ${#RUNNING_COMMANDS[@]} -eq 0 ]; then
    echo "  (none detected)"
else
    for cmd in "${RUNNING_COMMANDS[@]}"; do
        echo "  └─ $cmd"
    done
fi

echo ""
echo "════════════════════════════════════════════════"
echo "🚀 Attaching to dashboard in 2 seconds..."
echo "   Press Ctrl+b then d to detach"
echo "════════════════════════════════════════════════"

sleep 2

# Step 7: Attach to dashboard
tmux attach-session -t "$DASHBOARD_SESSION"
