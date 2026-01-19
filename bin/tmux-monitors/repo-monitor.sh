#!/usr/bin/env bash
# Repo Monitor - Monitors work queue and git status for a repository
# Usage: repo-monitor.sh <repo_name>

set -euo pipefail

REPO_NAME="${1:-unknown}"
REFRESH_INTERVAL=5

# Color codes (ANSI)
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Assign colors based on repo
case "$REPO_NAME" in
  karematch)
    REPO_COLOR="$CYAN"
    REPO_PATH="/Users/tmac/1_REPOS/karematch"
    QUEUE_FILE="$REPO_PATH/tasks/work_queue_karematch.json"
    ;;
  credentialmate)
    REPO_COLOR="$YELLOW"
    REPO_PATH="/Users/tmac/1_REPOS/credentialmate"
    QUEUE_FILE="$REPO_PATH/tasks/work_queue_credentialmate.json"
    ;;
  ai-orchestrator)
    REPO_COLOR="$GREEN"
    REPO_PATH="/Users/tmac/1_REPOS/AI_Orchestrator"
    QUEUE_FILE="$REPO_PATH/tasks/work_queue_ai-orchestrator.json"
    ;;
  *)
    REPO_COLOR="$NC"
    REPO_PATH="."
    QUEUE_FILE=""
    ;;
esac

# Function to get work queue stats
get_queue_stats() {
  if [[ -f "$QUEUE_FILE" ]]; then
    python3 -c "
import json
import sys
try:
    with open('$QUEUE_FILE') as f:
        data = json.load(f)
    tasks = data.get('features', [])
    total = len(tasks)
    pending = sum(1 for t in tasks if t.get('status') == 'pending')
    in_progress = sum(1 for t in tasks if t.get('status') == 'in_progress')
    blocked = sum(1 for t in tasks if t.get('status') == 'blocked')
    completed = sum(1 for t in tasks if t.get('status') == 'completed')
    print(f'Total: {total} | Pending: {pending} | In Progress: {in_progress} | Blocked: {blocked} | Completed: {completed}')
except Exception as e:
    print(f'Error reading queue: {e}')
" 2>/dev/null || echo "No queue file found"
  else
    echo "No queue file at: $QUEUE_FILE"
  fi
}

# Function to get git status
get_git_status() {
  if [[ -d "$REPO_PATH/.git" ]]; then
    cd "$REPO_PATH" || return

    # Get current branch
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

    # Get status
    STATUS=$(git status --short 2>/dev/null | wc -l | tr -d ' ')

    # Get ahead/behind
    UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")
    if [[ -n "$UPSTREAM" ]]; then
      AHEAD=$(git rev-list --count HEAD..@{u} 2>/dev/null || echo "0")
      BEHIND=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
      echo "Branch: $BRANCH | Changes: $STATUS | ↑$BEHIND ↓$AHEAD"
    else
      echo "Branch: $BRANCH | Changes: $STATUS | (no upstream)"
    fi
  else
    echo "Not a git repository"
  fi
}

# Main monitoring loop
while true; do
  clear

  # Header
  echo -e "${BOLD}${REPO_COLOR}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${REPO_COLOR}║  REPO MONITOR: $(printf '%-42s' "$REPO_NAME" | tr '[:lower:]' '[:upper:]')  ║${NC}"
  echo -e "${BOLD}${REPO_COLOR}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Work Queue Section
  echo -e "${BOLD}Work Queue Status:${NC}"
  echo -e "${REPO_COLOR}$(get_queue_stats)${NC}"
  echo ""

  # Git Status Section
  echo -e "${BOLD}Git Status:${NC}"
  echo -e "${REPO_COLOR}$(get_git_status)${NC}"
  echo ""

  # Recent Activity (last 5 tasks from queue)
  if [[ -f "$QUEUE_FILE" ]]; then
    echo -e "${BOLD}Recent Tasks:${NC}"
    python3 -c "
import json
try:
    with open('$QUEUE_FILE') as f:
        data = json.load(f)
    tasks = data.get('features', [])
    recent = sorted(tasks, key=lambda t: t.get('updated_at', ''), reverse=True)[:5]
    for task in recent:
        status = task.get('status', 'unknown')
        title = task.get('title', 'Untitled')[:50]
        status_color = {
            'pending': '\033[0;37m',      # White
            'in_progress': '\033[0;34m',  # Blue
            'blocked': '\033[1;33m',      # Yellow
            'completed': '\033[0;32m',    # Green
        }.get(status, '\033[0m')
        print(f'{status_color}  [{status:12s}] {title}\033[0m')
except Exception:
    pass
" 2>/dev/null
  fi

  echo ""
  echo -e "${BOLD}${REPO_COLOR}────────────────────────────────────────────────────────────${NC}"
  echo -e "Last updated: $(date '+%H:%M:%S') | Refresh: ${REFRESH_INTERVAL}s"

  sleep "$REFRESH_INTERVAL"
done
