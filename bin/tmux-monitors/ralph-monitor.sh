#!/usr/bin/env bash
# Ralph Monitor - Monitors Ralph verification verdicts
# Usage: ralph-monitor.sh

set -euo pipefail

REFRESH_INTERVAL=3

# Color codes (ANSI)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

# Ralph verdicts directory (AI_Orchestrator)
RALPH_DIR="/Users/tmac/1_REPOS/AI_Orchestrator/.ralph"
VERDICTS_DIR="$RALPH_DIR/verdicts"

# Function to get verdict stats
get_verdict_stats() {
  if [[ -d "$VERDICTS_DIR" ]]; then
    find "$VERDICTS_DIR" -name "*.json" -mtime -1 2>/dev/null | while read -r file; do
      python3 -c "
import json
try:
    with open('$file') as f:
        data = json.load(f)
    verdict = data.get('verdict', 'unknown')
    print(verdict)
except Exception:
    pass
" 2>/dev/null
    done | {
      pass=0 fail=0 blocked=0
      while read -r verdict; do
        case "$verdict" in
          PASS) ((pass++)) ;;
          FAIL) ((fail++)) ;;
          BLOCKED) ((blocked++)) ;;
        esac
      done
      echo "$pass|$fail|$blocked"
    }
  else
    echo "0|0|0"
  fi
}

# Function to get recent verdicts
get_recent_verdicts() {
  if [[ -d "$VERDICTS_DIR" ]]; then
    find "$VERDICTS_DIR" -name "*.json" -type f -print0 2>/dev/null | \
      xargs -0 ls -t 2>/dev/null | head -n 15 | while read -r file; do
        python3 -c "
import json
import os
try:
    with open('$file') as f:
        data = json.load(f)
    verdict = data.get('verdict', 'UNKNOWN')
    reason = data.get('reason', 'No reason')[:60]
    file_name = os.path.basename('$file')

    color_map = {
        'PASS': '\033[0;32m',
        'FAIL': '\033[0;31m',
        'BLOCKED': '\033[1;33m',
        'UNKNOWN': '\033[0m'
    }
    color = color_map.get(verdict, '\033[0m')
    reset = '\033[0m'
    dim = '\033[2m'

    print(f'{color}[{verdict:7s}]{reset} {dim}{file_name[:20]}{reset} {reason}')
except Exception:
    pass
" 2>/dev/null
      done
  else
    echo -e "${DIM}No verdicts directory found${NC}"
  fi
}

# Function to get active verifications
get_active_verifications() {
  if [[ -d "$RALPH_DIR/active" ]]; then
    count=$(find "$RALPH_DIR/active" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [[ $count -gt 0 ]]; then
      echo -e "${CYAN}$count active verification(s)${NC}"
    else
      echo -e "${DIM}No active verifications${NC}"
    fi
  else
    echo -e "${DIM}No active verifications${NC}"
  fi
}

# Main monitoring loop
while true; do
  clear

  # Get stats
  stats=$(get_verdict_stats)
  pass_count="${stats%%|*}"
  temp="${stats#*|}"
  fail_count="${temp%%|*}"
  blocked_count="${temp#*|}"
  total=$((pass_count + fail_count + blocked_count))

  # Calculate success rate
  success_rate=0
  if [[ $total -gt 0 ]]; then
    success_rate=$(( (pass_count * 100) / total ))
  fi

  # Header
  echo -e "${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}║  RALPH VERIFICATION MONITOR                               ║${NC}"
  echo -e "${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Stats Section
  echo -e "${BOLD}Verification Stats (Last 24h):${NC}"
  echo -e "  ${GREEN}PASS:${NC}    $pass_count"
  echo -e "  ${RED}FAIL:${NC}    $fail_count"
  echo -e "  ${YELLOW}BLOCKED:${NC} $blocked_count"
  echo -e "  ${BOLD}TOTAL:${NC}   $total"

  # Success rate with color coding
  if [[ $success_rate -ge 85 ]]; then
    echo -e "  ${GREEN}${BOLD}Success Rate: ${success_rate}%${NC}"
  elif [[ $success_rate -ge 70 ]]; then
    echo -e "  ${YELLOW}${BOLD}Success Rate: ${success_rate}%${NC}"
  else
    echo -e "  ${RED}${BOLD}Success Rate: ${success_rate}%${NC}"
  fi
  echo ""

  # Active verifications
  echo -e "${BOLD}Active Verifications:${NC}"
  echo "  $(get_active_verifications)"
  echo ""

  # Recent verdicts
  echo -e "${BOLD}Recent Verdicts (Last 15):${NC}"
  echo -e "${DIM}────────────────────────────────────────────────────────────${NC}"
  get_recent_verdicts
  echo ""

  echo -e "${BOLD}────────────────────────────────────────────────────────────${NC}"
  echo -e "Last updated: $(date '+%H:%M:%S') | Refresh: ${REFRESH_INTERVAL}s"

  sleep "$REFRESH_INTERVAL"
done
