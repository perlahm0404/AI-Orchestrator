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
# WINDOW 0: ORCHESTRATOR (Main Execution & CITO Status)
# ==============================================================================
tmux rename-window -t "${SESSION_NAME}:0" "orchestrator"

# Split window horizontally (50/50: main loop | CITO status)
tmux split-window -h -t "${SESSION_NAME}:0" -c "$REPO_ROOT"

# Resize panes equally
tmux resize-pane -t "${SESSION_NAME}:0.0" -x 50%

# Pane 0 (left): Main autonomous loop (ready for command)
tmux send-keys -t "${SESSION_NAME}:0.0" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "source .venv/bin/activate" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo '⚡ AI Orchestrator - Multi-Repo Launch'" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo ''" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo 'Launch parallel autonomous loops for all repos:'" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo '  ./bin/parallel-multi-repo.sh'" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo ''" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo 'Or single repo:'" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo '  python parallel_autonomous_loop.py --project karematch --max-parallel 3'" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo '  python parallel_autonomous_loop.py --project credentialmate --max-parallel 3'" C-m
tmux send-keys -t "${SESSION_NAME}:0.0" "echo ''" C-m

# Pane 1 (right): CITO coordination status (board-state.json live view)
tmux send-keys -t "${SESSION_NAME}:0.1" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:0.1" "clear" C-m
tmux send-keys -t "${SESSION_NAME}:0.1" "echo '🎯 CITO Coordination Status'" C-m
tmux send-keys -t "${SESSION_NAME}:0.1" "echo ''" C-m
tmux send-keys -t "${SESSION_NAME}:0.1" "echo 'Watching: vibe-kanban/board-state.json'" C-m
tmux send-keys -t "${SESSION_NAME}:0.1" "echo ''" C-m
tmux send-keys -t "${SESSION_NAME}:0.1" "watch -n 5 'cat vibe-kanban/board-state.json 2>/dev/null | jq \".[] | {id: .id, status: .status, agent: .assigned_agent}\" || echo \"No active board state\"'" C-m

# ==============================================================================
# WINDOW 1: REPOS (KareMatch, CredentialMate, AI_Orchestrator Status)
# ==============================================================================
tmux new-window -t "$SESSION_NAME" -n "repos" -c "$REPO_ROOT"

# Split into 3 vertical panes
tmux split-window -v -t "${SESSION_NAME}:1" -c "$REPO_ROOT"
tmux split-window -v -t "${SESSION_NAME}:1" -c "$REPO_ROOT"

# Evenly distribute panes
tmux select-layout -t "${SESSION_NAME}:1" even-vertical

# Pane 0: KareMatch status
tmux send-keys -t "${SESSION_NAME}:1.0" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:1.0" "./bin/tmux-monitors/repo-monitor.sh karematch" C-m

# Pane 1: CredentialMate status
tmux send-keys -t "${SESSION_NAME}:1.1" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:1.1" "./bin/tmux-monitors/repo-monitor.sh credentialmate" C-m

# Pane 2: AI_Orchestrator status
tmux send-keys -t "${SESSION_NAME}:1.2" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:1.2" "./bin/tmux-monitors/repo-monitor.sh ai-orchestrator" C-m

# ==============================================================================
# WINDOW 2: AGENTS (4 Worker Activity Monitors in 2x2 Grid)
# ==============================================================================
tmux new-window -t "$SESSION_NAME" -n "agents" -c "$REPO_ROOT"

# Create 2x2 grid layout
# First split vertically to create top and bottom halves
tmux split-window -v -t "${SESSION_NAME}:2" -c "$REPO_ROOT"

# Split each half horizontally to create 4 panes total
tmux split-window -h -t "${SESSION_NAME}:2.0" -c "$REPO_ROOT"
tmux split-window -h -t "${SESSION_NAME}:2.2" -c "$REPO_ROOT"

# Balance the panes
tmux select-layout -t "${SESSION_NAME}:2" tiled

# Pane 0 (top-left): Worker 0
tmux send-keys -t "${SESSION_NAME}:2.0" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:2.0" "./bin/tmux-monitors/agent-monitor.sh 0" C-m

# Pane 1 (top-right): Worker 1
tmux send-keys -t "${SESSION_NAME}:2.1" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:2.1" "./bin/tmux-monitors/agent-monitor.sh 1" C-m

# Pane 2 (bottom-left): Worker 2
tmux send-keys -t "${SESSION_NAME}:2.2" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:2.2" "./bin/tmux-monitors/agent-monitor.sh 2" C-m

# Pane 3 (bottom-right): Ralph verification stream
tmux send-keys -t "${SESSION_NAME}:2.3" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:2.3" "./bin/tmux-monitors/ralph-monitor.sh" C-m

# ==============================================================================
# WINDOW 3: METRICS (Performance, Resources, Governance)
# ==============================================================================
tmux new-window -t "$SESSION_NAME" -n "metrics" -c "$REPO_ROOT"

# Split into 3 horizontal panes
tmux split-window -h -t "${SESSION_NAME}:3" -c "$REPO_ROOT"
tmux split-window -h -t "${SESSION_NAME}:3" -c "$REPO_ROOT"

# Evenly distribute panes
tmux select-layout -t "${SESSION_NAME}:3" even-horizontal

# Pane 0: Agent performance dashboard
tmux send-keys -t "${SESSION_NAME}:3.0" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:3.0" "./bin/tmux-monitors/metrics-dashboard.sh" C-m

# Pane 1: Resource usage
tmux send-keys -t "${SESSION_NAME}:3.1" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:3.1" "./bin/tmux-monitors/resource-dashboard.sh" C-m

# Pane 2: Governance dashboard
tmux send-keys -t "${SESSION_NAME}:3.2" "cd ${REPO_ROOT}" C-m
tmux send-keys -t "${SESSION_NAME}:3.2" "./bin/tmux-monitors/governance-dashboard.sh" C-m

# ==============================================================================
# FINALIZATION
# ==============================================================================
# Select the orchestrator window (window 0, pane 0) as default
tmux select-window -t "${SESSION_NAME}:0"
tmux select-pane -t "${SESSION_NAME}:0.0"

# Attach to the session
echo "✅ Mission Control Session Created Successfully!"
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  AI ORCHESTRATOR - MISSION CONTROL v6.0                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Session Layout (4 Windows):"
echo "  Window 0: ORCHESTRATOR - Multi-repo launcher + CITO coordination"
echo "  Window 1: REPOS - KareMatch, CredentialMate, AI_Orchestrator status"
echo "  Window 2: AGENTS - 4 worker monitors + Ralph verification"
echo "  Window 3: METRICS - Performance, Resources, Governance dashboards"
echo ""
echo "Navigation Shortcuts:"
echo "  Alt+O - Jump to Orchestrator window"
echo "  Alt+R - Jump to Repos window"
echo "  Alt+A - Jump to Agents window"
echo "  Alt+M - Jump to Metrics window"
echo "  Alt+1/2/3/4 - Jump to pane within window"
echo ""
echo "Ghostty Tips:"
echo "  Cmd+Shift+T - Tab overview (see all sessions)"
echo "  Cmd+T       - New tab"
echo "  Cmd+D       - Split pane (right)"
echo ""
echo "tmux Shortcuts:"
echo "  Ctrl+B, D   - Detach session"
echo "  Ctrl+B, 0-3 - Switch window (0=Orch, 1=Repos, 2=Agents, 3=Metrics)"
echo "  Ctrl+B, ←/→ - Resize pane"
echo ""
echo "Quick Start:"
echo "  1. Launch multi-repo execution: ./bin/parallel-multi-repo.sh"
echo "  2. Switch to Repos window (Alt+R) to watch progress"
echo "  3. Switch to Agents window (Alt+A) to see worker activity"
echo "  4. Switch to Metrics window (Alt+M) to monitor performance"
echo ""
echo "Attaching to session: $SESSION_NAME"
echo ""
tmux attach-session -t "$SESSION_NAME"
