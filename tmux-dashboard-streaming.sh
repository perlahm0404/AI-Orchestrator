#!/bin/bash
# Tmux Dashboard Orchestrator - Streaming Edition (Compact)
# Shows live thought process and agent streaming output

set -e

DASHBOARD_SESSION="agent-dashboard"
KAREMATCH_PATH="/Users/tmac/1_REPOS/karematch"
TASK_OUTPUT_PATH="/tmp/claude/-Users-tmac-1-REPOS-AI-Orchestrator/tasks"

echo "=== TMUX STREAMING DASHBOARD ORCHESTRATOR ==="
echo ""

# Kill existing dashboard if it exists
if tmux has-session -t "$DASHBOARD_SESSION" 2>/dev/null; then
    echo "🗑️  Rebuilding existing dashboard..."
    tmux kill-session -t "$DASHBOARD_SESSION"
fi

# Find running autonomous loops
echo "🔍 Detecting autonomous agents..."
PIDS=$(ps aux | grep -E "autonomous_loop.*karematch" | grep -v grep | awk '{print $2}')
PID_ARRAY=($PIDS)
AGENT_COUNT=${#PID_ARRAY[@]}

echo "   Found $AGENT_COUNT autonomous agent(s)"
for pid in "${PID_ARRAY[@]}"; do
    CMD=$(ps -p $pid -o args= | head -c 80)
    echo "   └─ PID $pid: $CMD"
done
echo ""

# Create dashboard session
echo "🏗️  Building streaming dashboard..."
tmux new-session -d -s "$DASHBOARD_SESSION" -n "Agents"

# === PANE 1: Agent State Stream (Features Queue) ===
tmux rename-window -t "$DASHBOARD_SESSION:0" "Agent-Streams"
tmux send-keys -t "$DASHBOARD_SESSION:0.0" "clear" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.0" "echo '════════════════════════════════════════════════════════════════'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.0" "echo '🧠 AGENT THOUGHT PROCESS - Live State Stream'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.0" "echo '════════════════════════════════════════════════════════════════'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.0" "echo ''" C-m

# Tail the agent loop state file with color
if [ -f "$KAREMATCH_PATH/.aibrain/agent-loop.local.md" ]; then
    tmux send-keys -t "$DASHBOARD_SESSION:0.0" "tail -n 50 -f '$KAREMATCH_PATH/.aibrain/agent-loop.local.md' | while IFS= read -r line; do echo \"\$(date '+%H:%M:%S') | \$line\"; done" C-m
else
    tmux send-keys -t "$DASHBOARD_SESSION:0.0" "echo '⚠️  State file not found: $KAREMATCH_PATH/.aibrain/agent-loop.local.md'" C-m
fi

# === PANE 2: Latest Task Output Stream ===
tmux split-window -t "$DASHBOARD_SESSION:0" -h
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "clear" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "echo '════════════════════════════════════════════════════════════════'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "echo '📝 TASK OUTPUT - Real-time Stream'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "echo '════════════════════════════════════════════════════════════════'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "echo ''" C-m

# Auto-follow latest task output file
tmux send-keys -t "$DASHBOARD_SESSION:0.1" "while true; do LATEST=\$(ls -t $TASK_OUTPUT_PATH/*.output 2>/dev/null | head -1); if [ -n \"\$LATEST\" ] && [ -s \"\$LATEST\" ]; then echo \"📄 Tailing: \$(basename \$LATEST) (\$(date '+%H:%M:%S'))\"; echo ''; timeout 15 tail -n 30 -f \$LATEST 2>/dev/null || true; sleep 1; else echo \"⏳ Waiting for task output... (\$(date '+%H:%M:%S'))\"; sleep 3; fi; done" C-m

# === PANE 3: Work Queue Status (Bottom Split) ===
tmux split-window -t "$DASHBOARD_SESSION:0.0" -v -p 30
tmux send-keys -t "$DASHBOARD_SESSION:0.2" "clear" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.2" "echo '════════════════════════════════════════════════════════════════'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.2" "echo '📋 ACTIVE WORK QUEUES'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.2" "echo '════════════════════════════════════════════════════════════════'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.2" "echo ''" C-m

# Combined work queue status
tmux send-keys -t "$DASHBOARD_SESSION:0.2" "watch -n 3 -c 'echo \"🎯 FEATURES QUEUE:\"; jq -r \".tasks[] | select(.status == \\\"in_progress\\\" or .status == \\\"pending\\\") | \\\"  [\(.status | ascii_upcase)] \(.id): \(.title)\\\"\" /Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_karematch_features.json 2>/dev/null | head -5 || echo \"  (empty)\"; echo \"\"; echo \"⚙️  MAIN QUEUE:\"; jq -r \".tasks[] | select(.status == \\\"in_progress\\\" or .status == \\\"pending\\\") | \\\"  [\(.status | ascii_upcase)] \(.id): \(.title)\\\"\" /Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_karematch.json 2>/dev/null | head -5 || echo \"  (empty)\"; echo \"\"; echo \"💻 AGENTS:\"; ps -p ${PID_ARRAY[*]} -o pid,etime,%cpu,%mem 2>/dev/null || echo \"  No agents running\"'" C-m

# === PANE 4: Recent Agent Activity (Bottom Right) ===
tmux split-window -t "$DASHBOARD_SESSION:0.1" -v -p 30
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "clear" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "echo '════════════════════════════════════════════════════════════════'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "echo '🔄 RECENT AGENT COMMITS'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "echo '════════════════════════════════════════════════════════════════'" C-m
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "echo ''" C-m

# Watch for new commits
tmux send-keys -t "$DASHBOARD_SESSION:0.3" "cd $KAREMATCH_PATH && watch -n 5 -c 'git log --oneline --decorate --color=always -8'" C-m

# Print summary
echo ""
echo "════════════════════════════════════════════════"
echo "✅ STREAMING DASHBOARD READY"
echo "════════════════════════════════════════════════"
echo ""
echo "📺 PANE LAYOUT (4 panes):"
echo "  TOP-LEFT:  Agent Thought Process (live state)"
echo "  TOP-RIGHT: Task Output Stream (auto-rotating)"
echo "  BOT-LEFT:  Work Queue Status + Agent Stats"
echo "  BOT-RIGHT: Recent Commits (agent activity)"
echo ""
echo "🎯 STREAMING SOURCES:"
echo "  • Agent state: $KAREMATCH_PATH/.aibrain/agent-loop.local.md"
echo "  • Task output: $TASK_OUTPUT_PATH/*.output (auto-follows latest)"
echo "  • Work queues: tasks/work_queue_karematch*.json"
echo "  • Git commits: $KAREMATCH_PATH/.git"
echo ""
echo "💡 NAVIGATION:"
echo "  • Ctrl+b then arrow keys - Switch panes"
echo "  • Ctrl+b then z - Zoom current pane"
echo "  • Ctrl+b then d - Detach"
echo ""
echo "════════════════════════════════════════════════"
echo "🚀 Attaching to dashboard in 2 seconds..."
echo "════════════════════════════════════════════════"

sleep 2

# Attach to dashboard
tmux attach-session -t "$DASHBOARD_SESSION"
