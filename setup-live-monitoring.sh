#!/bin/bash
# Setup live monitoring in current tmux session

KAREMATCH_PATH="/Users/tmac/1_REPOS/karematch"
AGENT_PIDS="67608 92540"

echo "Setting up live monitoring panes..."

# Split current pane horizontally (left/right)
tmux split-window -h

# Split left pane vertically (top/bottom)
tmux select-pane -t 0
tmux split-window -v

# Split right pane vertically (top/bottom)
tmux select-pane -t 2
tmux split-window -v

echo "Created 4-pane layout"

# Pane 0 (top-left): Agent process tree
tmux select-pane -t 0
tmux send-keys "clear" C-m
tmux send-keys "echo '🌳 AGENT PROCESS TREE - Live Subagents'" C-m
tmux send-keys "echo ''" C-m
tmux send-keys "watch -n 2 -c 'for pid in $AGENT_PIDS; do echo \"═══ Agent PID \$pid ═══\"; ps -p \$pid -o pid,state,etime,command 2>/dev/null | tail -n +2; echo \"\"; children=\$(pgrep -P \$pid 2>/dev/null); if [ -n \"\$children\" ]; then echo \"  Subprocesses:\"; for child in \$children; do ps -p \$child -o pid,state,etime,command 2>/dev/null | tail -n +2 | sed \"s/^/    /\"; grandchildren=\$(pgrep -P \$child 2>/dev/null); if [ -n \"\$grandchildren\" ]; then echo \"      Workers:\"; for gc in \$grandchildren; do ps -p \$gc -o pid,state,command 2>/dev/null | tail -n +2 | sed \"s/^/        → /\"; done; fi; done; fi; echo \"\"; done'" C-m

# Pane 1 (bottom-left): Agent state + progress
tmux select-pane -t 1
tmux send-keys "clear" C-m
tmux send-keys "echo '📝 AGENT STATE + PROGRESS'" C-m
tmux send-keys "echo ''" C-m
tmux send-keys "watch -n 3 -c 'echo \"Current Task:\"; tail -20 $KAREMATCH_PATH/claude-progress.txt 2>/dev/null | grep -A 3 \"Status:\" | tail -8 || echo \"No progress\"; echo \"\"; echo \"Agent Loop State:\"; tail -10 $KAREMATCH_PATH/.aibrain/agent-loop.local.md 2>/dev/null || echo \"No state file\"'" C-m

# Pane 2 (top-right): Test output monitoring
tmux select-pane -t 2
tmux send-keys "clear" C-m
tmux send-keys "echo '🧪 TEST EXECUTION MONITOR'" C-m
tmux send-keys "echo ''" C-m
tmux send-keys "cd $KAREMATCH_PATH && while true; do clear; date; echo \"\"; if pgrep -f 'vitest' > /dev/null; then echo \"✅ Vitest is running\"; echo \"\"; ps aux | grep -E 'vitest|npm test' | grep -v grep | awk '{print \"  PID: \" \$2 \"  CPU: \" \$3 \"%  MEM: \" \$4 \"%  Elapsed: \" \$10}'; echo \"\"; echo \"Test workers:\"; pgrep -f 'vitest.*forks' | while read pid; do ps -p \$pid -o pid,pcpu,command | tail -n +2; done; echo \"\"; echo \"Checking for test output...\"; if [ -f .vitest/test-results.json ]; then echo \"Found test results\"; jq -r '.numTotalTests, .numPassedTests' .vitest/test-results.json 2>/dev/null; fi; else echo \"⏸️  No tests running\"; echo \"\"; echo \"Last test run:\"; find . -name '*.test.ts' -o -name '*.test.tsx' 2>/dev/null | head -3; fi; sleep 3; done" C-m

# Pane 3 (bottom-right): Work queue + commits
tmux select-pane -t 3
tmux send-keys "clear" C-m
tmux send-keys "echo '📊 WORK QUEUE + GIT ACTIVITY'" C-m
tmux send-keys "echo ''" C-m
tmux send-keys "watch -n 5 -c 'echo \"🎯 Features Queue:\"; /Users/tmac/1_REPOS/AI_Orchestrator/.venv/bin/python -c \"import json; data=json.load(open(\\\"/Users/tmac/1_REPOS/AI_Orchestrator/tasks/work_queue_karematch_features.json\\\")); tasks=data.get(\\\"features\\\",[]); print(f\\\"  Complete: {len([t for t in tasks if t[\\\\\\\"status\\\\\\\"]==\\\\\\\"complete\\\\\\\"])}/{len(tasks)}\\\"); ip=[t for t in tasks if t[\\\"status\\\"]==\\\"in_progress\\\"]; [print(f\\\"  🔄 {t[\\\\\\\"id\\\\\\\"]}\\\") for t in ip]\" 2>/dev/null; echo \"\"; echo \"🔄 Recent Commits (last hour):\"; cd $KAREMATCH_PATH && git log --oneline --since=\"1 hour ago\" --color=always | head -5 || echo \"  none\"; echo \"\"; echo \"💻 CPU Usage:\"; ps -p $AGENT_PIDS -o pid,%cpu,%mem,etime 2>/dev/null'" C-m

# Select top-left pane as default
tmux select-pane -t 0

echo ""
echo "✅ Live monitoring setup complete!"
echo ""
echo "📺 Pane Layout:"
echo "  TOP-LEFT:    Agent process tree with subprocesses"
echo "  BOTTOM-LEFT: Agent state + progress logs"
echo "  TOP-RIGHT:   Test execution monitor"
echo "  BOTTOM-RIGHT: Work queue + git commits"
echo ""
echo "Navigate with: Ctrl+b then arrow keys"
echo "Zoom a pane: Ctrl+b then z"
