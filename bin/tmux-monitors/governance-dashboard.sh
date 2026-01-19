#!/usr/bin/env bash
# Governance Dashboard - Shows governance metrics and compliance status
# Usage: governance-dashboard.sh

set -euo pipefail

REFRESH_INTERVAL=10

# Color codes (ANSI)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

# AI_Orchestrator path
AI_BRAIN_DIR="/Users/tmac/1_REPOS/AI_Orchestrator"

# Function to get kill switch status (from config or default)
get_kill_switch() {
  # Default to NORMAL if no config found
  if [[ -f "$AI_BRAIN_DIR/governance/kill-switch.txt" ]]; then
    cat "$AI_BRAIN_DIR/governance/kill-switch.txt"
  else
    echo "NORMAL"
  fi
}

# Function to get autonomy level (from config or default)
get_autonomy_level() {
  # Default to L2 if no config found
  if [[ -f "$AI_BRAIN_DIR/governance/autonomy-level.txt" ]]; then
    cat "$AI_BRAIN_DIR/governance/autonomy-level.txt"
  else
    echo "L2"
  fi
}

# Function to count policy violations
get_violations() {
  if [[ -d "$AI_BRAIN_DIR/.ralph/violations" ]]; then
    total=$(find "$AI_BRAIN_DIR/.ralph/violations" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    critical=$(find "$AI_BRAIN_DIR/.ralph/violations" -name "*CRITICAL*.json" 2>/dev/null | wc -l | tr -d ' ')
    echo "$total|$critical"
  else
    echo "0|0"
  fi
}

# Function to get Ralph stats
get_ralph_stats() {
  if [[ -d "$AI_BRAIN_DIR/.ralph/verdicts" ]]; then
    total=$(find "$AI_BRAIN_DIR/.ralph/verdicts" -name "*.json" -mtime -7 2>/dev/null | wc -l | tr -d ' ')

    # Count PASS verdicts
    pass_count=0
    if [[ $total -gt 0 ]]; then
      pass_count=$(find "$AI_BRAIN_DIR/.ralph/verdicts" -name "*.json" -mtime -7 -exec grep -l '"verdict": "PASS"' {} \; 2>/dev/null | wc -l | tr -d ' ')
    fi

    # Calculate pass rate
    pass_rate=0
    if [[ $total -gt 0 ]]; then
      pass_rate=$(( (pass_count * 100) / total ))
    fi

    echo "$total|$pass_rate"
  else
    echo "0|0"
  fi
}

# Function to format kill switch status
format_kill_switch() {
  status=$1
  case "$status" in
    OFF)
      echo -e "${RED}${BOLD}OFF (All agents stopped)${NC}"
      ;;
    SAFE)
      echo -e "${YELLOW}${BOLD}SAFE MODE (Limited operations)${NC}"
      ;;
    NORMAL)
      echo -e "${GREEN}${BOLD}NORMAL (Full autonomy)${NC}"
      ;;
    PAUSED)
      echo -e "${CYAN}${BOLD}PAUSED (Temporary hold)${NC}"
      ;;
    *)
      echo -e "${DIM}UNKNOWN${NC}"
      ;;
  esac
}

# Function to format autonomy level
format_autonomy_level() {
  level=$1
  case "$level" in
    L0.5)
      echo -e "${RED}L0.5${NC} (Strictest - Operator Team)"
      ;;
    L1)
      echo -e "${YELLOW}L1${NC} (Stricter - Dev Team / HIPAA)"
      ;;
    L2)
      echo -e "${GREEN}L2${NC} (Higher - QA Team)"
      ;;
    *)
      echo -e "${DIM}${level}${NC}"
      ;;
  esac
}

# Main monitoring loop
while true; do
  clear

  # Header
  echo -e "${BOLD}${MAGENTA}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${MAGENTA}║  GOVERNANCE & COMPLIANCE DASHBOARD                        ║${NC}"
  echo -e "${BOLD}${MAGENTA}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Get kill switch status
  kill_switch=$(get_kill_switch)
  echo -e "${BOLD}Kill Switch Status:${NC}"
  echo -e "  $(format_kill_switch "$kill_switch")"
  echo ""

  # Get autonomy level
  autonomy=$(get_autonomy_level)
  echo -e "${BOLD}Autonomy Level:${NC}"
  echo -e "  $(format_autonomy_level "$autonomy")"
  echo ""

  # Get violations
  violations=$(get_violations)
  total_violations=$(echo "$violations" | cut -d'|' -f1)
  critical_violations=$(echo "$violations" | cut -d'|' -f2)

  echo -e "${BOLD}Policy Violations:${NC}"
  if [[ $critical_violations -gt 0 ]]; then
    echo -e "  ${RED}${BOLD}Critical: ${critical_violations}${NC}"
  else
    echo -e "  ${GREEN}Critical: 0${NC}"
  fi
  echo -e "  ${DIM}Total: ${total_violations}${NC}"
  echo ""

  # Get Ralph stats
  ralph_stats=$(get_ralph_stats)
  ralph_total=$(echo "$ralph_stats" | cut -d'|' -f1)
  ralph_pass_rate=$(echo "$ralph_stats" | cut -d'|' -f2)

  echo -e "${BOLD}Ralph Verification (Last 7 days):${NC}"
  echo -e "  ${BOLD}Total Verdicts:${NC} ${ralph_total}"

  # Color code pass rate
  if [[ $ralph_pass_rate -ge 85 ]]; then
    echo -e "  ${GREEN}${BOLD}Pass Rate: ${ralph_pass_rate}%${NC}"
  elif [[ $ralph_pass_rate -ge 70 ]]; then
    echo -e "  ${YELLOW}${BOLD}Pass Rate: ${ralph_pass_rate}%${NC}"
  else
    echo -e "  ${RED}${BOLD}Pass Rate: ${ralph_pass_rate}%${NC}"
  fi
  echo ""

  # Team compliance (simplified - count active workers by team)
  echo -e "${BOLD}Active Teams:${NC}"
  qa_agents=$(ps aux | grep -E "bugfix|codequality|testfixer" | grep -v grep | wc -l | tr -d ' ')
  dev_agents=$(ps aux | grep -E "featurebuilder|testwriter" | grep -v grep | wc -l | tr -d ' ')
  echo -e "  ${BOLD}QA Team:${NC}  ${qa_agents} agents active"
  echo -e "  ${BOLD}Dev Team:${NC} ${dev_agents} agents active"
  echo ""

  # Compliance summary
  echo -e "${BOLD}Compliance Summary:${NC}"
  if [[ $critical_violations -eq 0 ]]; then
    echo -e "  ${GREEN}●${NC} No critical violations detected"
  else
    echo -e "  ${RED}●${NC} ${critical_violations} critical violations require attention"
  fi
  echo -e "  ${GREEN}●${NC} Kill switch: $kill_switch"
  echo -e "  ${GREEN}●${NC} Autonomy level: $autonomy"

  echo ""
  echo -e "${BOLD}${MAGENTA}────────────────────────────────────────────────────────────${NC}"
  echo -e "Last updated: $(date '+%H:%M:%S') | Refresh: ${REFRESH_INTERVAL}s"

  sleep "$REFRESH_INTERVAL"
done
