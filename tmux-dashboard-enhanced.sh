#!/bin/bash
# Enhanced Tmux Dashboard - Shows actual agent subprocess activity

set -e

DASHBOARD_SESSION="agent-dashboard"
KAREMATCH_PATH="/Users/tmac/1_REPOS/karematch"

echo "=== ENHANCED STREAMING DASHBOARD ==="
echo ""

# Kill existing dashboard
if tmux has-session -t "$DASHBOARD_SESSION" 2>/dev/null; then
    echo "🗑️  Rebuilding dashboard..."
    tmux kill-session -t "$DASHBOARD_SESSION"
fi

# Find agents
AGENT_PIDS=$(ps aux | grep -E "autonomous_loop.*karematch" | grep -v grep | awk '{print $2}')
echo "🔍 Found agents: $AGENT_PIDS"

# Create session
tmux new-session -d -s "$DASHBOARD_SESSION" -n "Live"

# === PANE 1: Live Agent Process Tree ===
tmux send-keys -t "$DASHBOARD_SESSION:0.0" "clear" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.0" "echo '🌳 AGENT PROCESS TREE - Live View'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.0" "echo ''" C-m

# Show full process tree of agents with auto-refresh
tmux send-keys -t "$DASHBOARD_SESSION:0.0" "watch -n 2 -c 'for pid in $AGENT_PIDS; do echo \"═══ Agent PID \$pid ═══\"; ps -p \$pid -o pid,ppid,state,etime,command 2>/dev/null; echo \"\"; children=\$(pgrep -P \$pid); if [ -n \"\$children\" ]; then echo \"  Children:\"; for child in \$children; do ps -p \$child -o pid,ppid,state,etime,command 2>/dev/null | tail -n +2 | sed \"s/^/    /\"; grandchildren=\$(pgrep -P \$child); if [ -n \"\$grandchildren\" ]; then for gc in \$grandchildren; do ps -p \$gc -o pid,state,etime,command 2>/dev/null | tail -n +2 | sed \"s/^/      → /\"; done; fi; done; fi; echo \"\"; done'" C-m

# === PANE 2: Test Output (if running) ===
tmux split-window -t "$DASHBOARD_SESSION:0" -h
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "clear" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "echo '🧪 TEST EXECUTION OUTPUT'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "echo ''" C-m

# Monitor test output from karematch directory
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "cd $KAREMATCH_PATH && while true; do if pgrep -f 'vitest' > /dev/null; then echo \"[$(date '+%H:%M:%S')] Vitest is running...\"; echo \"\"; ps aux | grep vitest | grep -v grep | awk '{print \"PID: \" \$2 \"  Elapsed: \" \$10}'  ; echo \"\"; echo \"Checking for test output...\"; find . -name \"*.log\" -o -name \"test-results*\" 2>/dev/null | head -5 | xargs tail -20 2>/dev/null || echo \"No test logs found\"; else echo \"[$(date '+%H:%M:%S')] No tests running\"; fi; sleep 5; done" C-m

# === PANE 3: Work Queue + Agent State ===
tmux split-window -t "$DASHBOARD_SESSION:0.0" -v -p 40
tmux send-keys -t "$DASHBOARD_SESSION:0.2" "clear" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.2" "echo '📋 WORK QUEUES + AGENT STATE'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.2" "echo ''" C-m

tmux send-keys -t "$DASHBOARD_SESSION:0.2" "watch -n 3 -c 'echo \"🎯 ACTIVE TASKS:\"; jq -r \".tasks[] | select(.status == \\\"in_progress\\\") | \\\"  [\(.status | ascii_upcase)] \(.id): \(.title)\\\"\" /Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_karematch_features.json 2>/dev/null || echo \"  none\"; echo \"\"; tail -15 $KAREMATCH_PATH/claude-progress.txt 2>/dev/null | tail -10 || echo \"No progress file\"'" C-m

# === PANE 4: System Monitor ===
tmux split-window -t "$DASHBOARD_SESSION:0.1" -v -p 40
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "clear" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "echo '💻 SYSTEM RESOURCES'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "echo ''" C-m

# Monitor CPU/Memory for all agent-related processes
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "watch -n 2 'echo \"Agent Processes:\"; ps -p $AGENT_PIDS -o pid,etime,%cpu,%mem,command 2>/dev/null; echo \"\"; echo \"Test Runners:\"; ps aux | grep -E \"vitest|npm test\" | grep -v grep | awk \"{printf \\\"PID: %-6s CPU: %-4s MEM: %-4s TIME: %-8s CMD: %s\\\\n\\\", \\\$2, \\\$3\\\"%\\\", \\\$4\\\"%\\\", \\\$10, \\\$11}\" | head -5; echo \"\"; echo \"Recent Commits:\"; cd $KAREMATCH_PATH && git log --oneline -3 --color=always 2>/dev/null'" C-m

echo ""
echo "════════════════════════════════════════════════"
echo "✅ ENHANCED DASHBOARD READY"
echo "════════════════════════════════════════════════"
echo ""
echo "📺 PANES:"
echo "  TOP-LEFT:  Full agent process tree (live)"
echo "  TOP-RIGHT: Test execution monitoring"
echo "  BOT-LEFT:  Active tasks + progress log"
echo "  BOT-RIGHT: System resources + recent commits"
echo ""
echo "💡 You'll now see:"
echo "  • Actual subprocesses (npm test, vitest workers)"
echo "  • How long tests have been running"
echo "  • Real-time process states"
echo ""
echo "════════════════════════════════════════════════"
echo "🚀 Attaching to dashboard in 2 seconds..."
echo "════════════════════════════════════════════════"

sleep 2
tmux attach-session -t "$DASHBOARD_SESSION"
