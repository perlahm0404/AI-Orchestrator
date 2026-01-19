#!/usr/bin/env bash
# Agent Monitor - Monitors agent activity from worker logs
# Usage: agent-monitor.sh <worker_id>

set -euo pipefail

WORKER_ID="${1:-0}"
REFRESH_INTERVAL=3

# Color codes (ANSI)
RED='\033[0;31m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

# AI_Orchestrator paths
AI_BRAIN_DIR="/Users/tmac/1_REPOS/AI_Orchestrator/.aibrain"
WORKER_DIR="$AI_BRAIN_DIR/worker-$WORKER_ID"
LOG_FILE="$WORKER_DIR/agent.log"

# Agent type color mapping
get_agent_color() {
  case "$1" in
    bugfix|BugFix)
      echo "$RED"
      ;;
    codequality|CodeQuality)
      echo "$BLUE"
      ;;
    featurebuilder|FeatureBuilder)
      echo "$MAGENTA"
      ;;
    testwriter|TestWriter)
      echo "$CYAN"
      ;;
    testfixer|TestFixer)
      echo "$YELLOW"
      ;;
    *)
      echo "$NC"
      ;;
  esac
}

# Function to get current agent type from worker state
get_current_agent() {
  if [[ -f "$WORKER_DIR/state.json" ]]; then
    python3 -c "
import json
try:
    with open('$WORKER_DIR/state.json') as f:
        data = json.load(f)
    agent = data.get('agent_type', 'unknown')
    task = data.get('current_task', {}).get('title', 'No active task')
    print(f'{agent}|{task}')
except Exception:
    print('unknown|No state file')
" 2>/dev/null || echo "unknown|Error reading state"
  else
    echo "unknown|No state file"
  fi
}

# Function to get worker status
get_worker_status() {
  if [[ -d "$WORKER_DIR" ]]; then
   agent_info
    agent_info=$(get_current_agent)
   agent_type="${agent_info%%|*}"
   current_task="${agent_info##*|}"

    # Check if worker is active (log file modified in last 60 seconds)
    if [[ -f "$LOG_FILE" ]]; then
     last_modified
      last_modified=$(stat -f %m "$LOG_FILE" 2>/dev/null || echo "0")
     now
      now=$(date +%s)
     age=$((now - last_modified))

      if [[ $age -lt 60 ]]; then
        echo -e "${GREEN}ACTIVE${NC}"
      else
        echo -e "${DIM}IDLE (${age}s ago)${NC}"
      fi
    else
      echo -e "${DIM}NO LOGS${NC}"
    fi

    echo "$agent_type|$current_task"
  else
    echo -e "${DIM}NOT INITIALIZED${NC}"
    echo "unknown|No worker directory"
  fi
}

# Function to get recent log entries
get_recent_logs() {
  if [[ -f "$LOG_FILE" ]]; then
    # Get last 20 lines with color coding
    tail -n 20 "$LOG_FILE" | while IFS= read -r line; do
      # Color code based on log level or keywords
      if [[ "$line" =~ ERROR|FAILED|BLOCKED ]]; then
        echo -e "${RED}$line${NC}"
      elif [[ "$line" =~ WARNING|WARN ]]; then
        echo -e "${YELLOW}$line${NC}"
      elif [[ "$line" =~ SUCCESS|PASS|COMPLETED ]]; then
        echo -e "${GREEN}$line${NC}"
      elif [[ "$line" =~ INFO ]]; then
        echo -e "${CYAN}$line${NC}"
      else
        echo -e "${DIM}$line${NC}"
      fi
    done
  else
    echo -e "${DIM}No log file found at: $LOG_FILE${NC}"
  fi
}

# Main monitoring loop
while true; do
  clear

  # Get status
  status_info=$(get_worker_status)
  status_line=$(echo "$status_info" | head -n 1)
  agent_info=$(echo "$status_info" | tail -n 1)
 agent_type="${agent_info%%|*}"
 current_task="${agent_info##*|}"
  agent_color=$(get_agent_color "$agent_type")

  # Header
  echo -e "${BOLD}${agent_color}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${agent_color}║  AGENT MONITOR: WORKER-${WORKER_ID}                                 ║${NC}"
  echo -e "${BOLD}${agent_color}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Status Section
  echo -e "${BOLD}Status:${NC} $status_line"
  echo -e "${BOLD}Agent Type:${NC} ${agent_color}${agent_type}${NC}"
  echo -e "${BOLD}Current Task:${NC} ${DIM}${current_task}${NC}"
  echo ""

  # Iteration info (if available)
  if [[ -f "$WORKER_DIR/iteration.json" ]]; then
    echo -e "${BOLD}Iteration Info:${NC}"
    python3 -c "
import json
try:
    with open('$WORKER_DIR/iteration.json') as f:
        data = json.load(f)
    iteration = data.get('current_iteration', 0)
    max_iterations = data.get('max_iterations', 0)
    progress = int((iteration / max_iterations) * 100) if max_iterations > 0 else 0
    print(f'  Iteration: {iteration}/{max_iterations} ({progress}%)')
    verdict = data.get('last_verdict', 'N/A')
    print(f'  Last Verdict: {verdict}')
except Exception:
    pass
" 2>/dev/null
    echo ""
  fi

  # Recent Activity
  echo -e "${BOLD}Recent Activity (last 20 lines):${NC}"
  echo -e "${DIM}────────────────────────────────────────────────────────────${NC}"
  get_recent_logs
  echo ""

  echo -e "${BOLD}${agent_color}────────────────────────────────────────────────────────────${NC}"
  echo -e "Last updated: $(date '+%H:%M:%S') | Refresh: ${REFRESH_INTERVAL}s"

  sleep "$REFRESH_INTERVAL"
done
