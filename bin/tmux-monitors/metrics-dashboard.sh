#!/usr/bin/env bash
# Metrics Dashboard - Shows agent performance metrics
# Usage: metrics-dashboard.sh

set -euo pipefail

REFRESH_INTERVAL=10

# Color codes (ANSI)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

# AI_Orchestrator path
AI_BRAIN_DIR="/Users/tmac/1_REPOS/AI_Orchestrator"

# Function to get agent performance data
get_agent_performance() {
  cd "$AI_BRAIN_DIR" || return

  python3 -c '
import sys
sys.path.insert(0, "/Users/tmac/1_REPOS/AI_Orchestrator")

try:
    from agents.coordinator.metrics import AIHRDashboard

    dashboard = AIHRDashboard()
    data = dashboard.get_performance_dashboard()

    # Print agent stats
    print("AGENT_STATS_START")
    for agent_id, stats in data.get("agents", {}).items():
        success_rate = stats.get("success_rate", 0) * 100
        total_tasks = stats.get("total_tasks", 0)
        avg_iterations = stats.get("avg_iterations", 0)
        escalation_rate = stats.get("escalation_rate", 0) * 100

        print(f"{agent_id}|{success_rate:.1f}|{total_tasks}|{avg_iterations:.1f}|{escalation_rate:.1f}")
    print("AGENT_STATS_END")

    # Print overall stats
    overall = data.get("overall", {})
    print(f"OVERALL|{overall.get(\"autonomy_pct\", 0):.1f}|{overall.get(\"total_tasks\", 0)}|{overall.get(\"avg_iterations\", 0):.1f}")

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    print("AGENT_STATS_START")
    print("AGENT_STATS_END")
    print("OVERALL|0.0|0|0.0")
' 2>/dev/null || {
    echo "AGENT_STATS_START"
    echo "AGENT_STATS_END"
    echo "OVERALL|0.0|0|0.0"
  }
}

# Function to format performance bar
format_bar() {
 value=$1
 max=100
 width=20
 # Convert float to int by removing decimal
 value_int=${value%.*}
 filled=$(( (value_int * width) / max ))
 empty=$(( width - filled ))

  # Color based on value
  if (( $(echo "$value >= 85" | bc -l) )); then
    color="$GREEN"
  elif (( $(echo "$value >= 70" | bc -l) )); then
    color="$YELLOW"
  else
    color="$RED"
  fi

  echo -ne "${color}"
  printf '█%.0s' $(seq 1 $filled)
  echo -ne "${DIM}"
  printf '░%.0s' $(seq 1 $empty)
  echo -ne "${NC}"
}

# Main monitoring loop
while true; do
  clear

  # Header
  echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${CYAN}║  AGENT PERFORMANCE DASHBOARD                              ║${NC}"
  echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Get performance data
  perf_data=$(get_agent_performance)

  # Parse and display agent stats
  echo -e "${BOLD}Agent Performance:${NC}"
  echo -e "${DIM}Agent          Success%   Tasks   Avg Iter   Esc%${NC}"
  echo -e "${DIM}──────────────────────────────────────────────────────────${NC}"

 in_stats=false
  while IFS='|' read -r agent success tasks iterations escalation; do
    if [[ "$agent" == "AGENT_STATS_START" ]]; then
      in_stats=true
      continue
    elif [[ "$agent" == "AGENT_STATS_END" ]]; then
      in_stats=false
      continue
    elif [[ "$in_stats" == true && -n "$agent" ]]; then
      # Format agent name
     agent_name
      agent_name=$(printf '%-14s' "$agent")

      # Color code success rate
     success_color
      if (( $(echo "$success >= 85" | bc -l) )); then
        success_color="$GREEN"
      elif (( $(echo "$success >= 70" | bc -l) )); then
        success_color="$YELLOW"
      else
        success_color="$RED"
      fi

      # Color code escalation rate
     esc_color
      if (( $(echo "$escalation < 10" | bc -l) )); then
        esc_color="$GREEN"
      elif (( $(echo "$escalation < 20" | bc -l) )); then
        esc_color="$YELLOW"
      else
        esc_color="$RED"
      fi

      echo -e "$agent_name ${success_color}${success}%${NC}     ${tasks}     ${iterations}        ${esc_color}${escalation}%${NC}"
    fi
  done <<< "$perf_data"

  echo ""

  # Overall stats
  echo -e "${BOLD}Overall System Performance:${NC}"
  overall_line=$(echo "$perf_data" | grep "^OVERALL|" || echo "OVERALL|0.0|0|0.0")
  IFS='|' read -r _ autonomy total_tasks avg_iter <<< "$overall_line"

  echo -e "  ${BOLD}Autonomy:${NC}      ${autonomy}% $(format_bar "${autonomy}")"
  echo -e "  ${BOLD}Total Tasks:${NC}   $total_tasks"
  echo -e "  ${BOLD}Avg Iterations:${NC} $avg_iter"

  echo ""

  # Performance thresholds legend
  echo -e "${BOLD}Performance Thresholds:${NC}"
  echo -e "  ${GREEN}■${NC} Excellent: ≥85%    ${YELLOW}■${NC} Good: 70-85%    ${RED}■${NC} Needs Review: <70%"

  echo ""
  echo -e "${BOLD}${CYAN}────────────────────────────────────────────────────────────${NC}"
  echo -e "Last updated: $(date '+%H:%M:%S') | Refresh: ${REFRESH_INTERVAL}s"

  sleep "$REFRESH_INTERVAL"
done
