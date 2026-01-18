#!/usr/bin/env bash
# tmux-launch.sh - Launch AI Orchestrator tmux session with monitoring layout
#
# Usage:
#   ./bin/tmux-launch.sh [project]
#
# Arguments:
#   project - Optional project name (karematch, credentialmate, etc.)
#             If omitted, creates generic "ai-brain" session
#
# Examples:
#   ./bin/tmux-launch.sh                  # Generic session: ai-brain
#   ./bin/tmux-launch.sh karematch        # Project session: ai-brain-karematch
#   ./bin/tmux-launch.sh credentialmate   # Project session: ai-brain-credentialmate

set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================
PROJECT="${1:-}"
if [[ -n "$PROJECT" ]]; then
    SESSION_NAME="ai-brain-${PROJECT}"
else
    SESSION_NAME="ai-brain"
fi

REPO_ROOT="/Users/tmac/1_REPOS/AI_Orchestrator"
TMUX_CONFIG="${REPO_ROOT}/.tmux.conf.ai-brain"
LOG_DIR="${REPO_ROOT}/.aibrain/tmux-logs"

# ==============================================================================
# SETUP
# ==============================================================================
# Create log directory for tmux capture
mkdir -p "$LOG_DIR"

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "✅ Session '$SESSION_NAME' already exists. Attaching..."
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

# ==============================================================================
# SESSION CREATION
# ==============================================================================
echo "🚀 Creating tmux session: $SESSION_NAME"

# Create new detached session with tmux config
tmux -f "$TMUX_CONFIG" new-session -d -s "$SESSION_NAME" -c "$REPO_ROOT"

# ==============================================================================
# WINDOW 0: ORCHESTRATOR (Main Execution)
# ==============================================================================
tmux rename-window -t "${SESSION_NAME}:0" "orchestrator"

# Split window horizontally (top: main loop, bottom: logs)
tmux split-window -h -t "${SESSION_NAME}:0" -c "$REPO_ROOT"

# Resize panes (70% left for main, 30% right for logs)
tmux resize-pane -t "${SESSION_NAME}:0.0" -x 70%

# Pane 0 (left): Main autonomous loop (ready for command)
tmux send-keys -t "${SESSION_NAME}:0.0" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "source .venv/bin/activate" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo '⚡ AI Orchestrator - Main Loop'" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo ''" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo 'Run autonomous loop:'" C-m
if [[ -n "$PROJECT" ]]; then
    tmux send-keys -t "${SESSION_NAME}:0.0" "echo '  python parallel_autonomous_loop.py --project ${PROJECT} --max-parallel 3'" C-m
else
    tmux send-keys -t "${SESSION_NAME}:0.0" "echo '  python parallel_autonomous_loop.py --project <PROJECT> --max-parallel 3'" C-m
fi
tmux send-keys -t "${SESSION_NAME}:0.0" "echo ''" C-m

# Pane 1 (right): Real-time log viewer
tmux send-keys -t "${SESSION_NAME}:0.1" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:0.1" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:0.1" "echo '📋 Agent Logs'" C-m
tmux send-keys -t "${SESSION_NAME}:0.1" "echo 'Waiting for autonomous loop to start...'" C-m

# ==============================================================================
# WINDOW 1: PARALLEL WORKERS (3 panes for monitoring)
# ==============================================================================
tmux new-window -t "$SESSION_NAME" -n "parallel" -c "$REPO_ROOT"

# Split into 3 vertical panes
tmux split-window -v -t "${SESSION_NAME}:1" -c "$REPO_ROOT"
tmux split-window -v -t "${SESSION_NAME}:1" -c "$REPO_ROOT"

# Evenly distribute panes
tmux select-layout -t "${SESSION_NAME}:1" even-vertical

# Pane 0: Worker 0 monitoring
tmux send-keys -t "${SESSION_NAME}:1.0" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:1.0" "echo '🔧 Worker 0 Monitor'" C-m
tmux send-keys -t "${SESSION_NAME}:1.0" "echo 'Watching: .aibrain/worker-0/'" C-m

# Pane 1: Worker 1 monitoring
tmux send-keys -t "${SESSION_NAME}:1.1" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:1.1" "echo '🔧 Worker 1 Monitor'" C-m
tmux send-keys -t "${SESSION_NAME}:1.1" "echo 'Watching: .aibrain/worker-1/'" C-m

# Pane 2: Worker 2 monitoring
tmux send-keys -t "${SESSION_NAME}:1.2" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:1.2" "echo '🔧 Worker 2 Monitor'" C-m
tmux send-keys -t "${SESSION_NAME}:1.2" "echo 'Watching: .aibrain/worker-2/'" C-m

# ==============================================================================
# WINDOW 2: MONITORING (Ralph, Git, Queue Stats)
# ==============================================================================
tmux new-window -t "$SESSION_NAME" -n "monitor" -c "$REPO_ROOT"

# Split into 3 horizontal panes
tmux split-window -h -t "${SESSION_NAME}:2" -c "$REPO_ROOT"
tmux split-window -h -t "${SESSION_NAME}:2" -c "$REPO_ROOT"

# Evenly distribute panes
tmux select-layout -t "${SESSION_NAME}:2" even-horizontal

# Pane 0: Ralph verification log
tmux send-keys -t "${SESSION_NAME}:2.0" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:2.0" "echo '⚖️  Ralph Verification Monitor'" C-m
tmux send-keys -t "${SESSION_NAME}:2.0" "echo ''" C-m
tmux send-keys -t "${SESSION_NAME}:2.0" "echo 'Watching for verdicts...'" C-m
tmux send-keys -t "${SESSION_NAME}:2.0" "echo 'Log: .ralph/verdicts/'" C-m

# Pane 1: Git status (watch mode)
tmux send-keys -t "${SESSION_NAME}:2.1" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:2.1" "echo '🔀 Git Status Monitor'" C-m
if [[ -n "$PROJECT" ]]; then
    if [[ "$PROJECT" == "karematch" ]]; then
        PROJECT_PATH="/Users/tmac/1_REPOS/karematch"
    elif [[ "$PROJECT" == "credentialmate" ]]; then
        PROJECT_PATH="/Users/tmac/1_REPOS/credentialmate"
    else
        PROJECT_PATH="$REPO_ROOT"
    fi
    tmux send-keys -t "${SESSION_NAME}:2.1" "cd ${PROJECT_PATH}" C-m
    tmux send-keys -t "${SESSION_NAME}:2.1" "watch -n 5 'git status --short'" C-m
else
    tmux send-keys -t "${SESSION_NAME}:2.1" "echo 'Run: watch -n 5 git status --short'" C-m
fi

# Pane 2: Work queue stats
tmux send-keys -t "${SESSION_NAME}:2.2" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:2.2" "echo '📊 Work Queue Stats'" C-m
tmux send-keys -t "${SESSION_NAME}:2.2" "echo ''" C-m
if [[ -n "$PROJECT" ]]; then
    tmux send-keys -t "${SESSION_NAME}:2.2" "cd ${REPO_ROOT}" C-m
    tmux send-keys -t "${SESSION_NAME}:2.2" "watch -n 5 'cat tasks/work_queue_${PROJECT}.json 2>/dev/null | jq \".features | group_by(.status) | map({status: .[0].status, count: length})\" || echo \"Queue not yet created\"'" C-m
else
    tmux send-keys -t "${SESSION_NAME}:2.2" "echo 'Project-specific work queue will appear here'" C-m
fi

# ==============================================================================
# FINALIZATION
# ==============================================================================
# Select the orchestrator window (window 0, pane 0) as default
tmux select-window -t "${SESSION_NAME}:0"
tmux select-pane -t "${SESSION_NAME}:0.0"

# Attach to the session
echo "✅ Session created successfully!"
echo ""
echo "Session Layout:"
echo "  Window 0: orchestrator (main loop + logs)"
echo "  Window 1: parallel (3 worker monitors)"
echo "  Window 2: monitor (Ralph + Git + Queue)"
echo ""
echo "Ghostty Tips:"
echo "  - Tab Overview: Cmd+Shift+T (see all sessions)"
echo "  - New Tab: Cmd+T"
echo "  - Split Pane: Cmd+D (right) or Cmd+Shift+D (down)"
echo ""
echo "tmux Shortcuts:"
echo "  - Detach: Ctrl+B, D"
echo "  - Switch window: Ctrl+B, 0-2"
echo "  - Resize pane: Ctrl+B, arrow keys"
echo "  - Capture pane: Ctrl+B, Ctrl+L (custom keybind)"
echo ""
echo "Attaching to session: $SESSION_NAME"
tmux attach-session -t "$SESSION_NAME"
