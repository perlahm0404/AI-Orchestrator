#!/usr/bin/env bash
# Resource Dashboard - Shows system resource usage
# Usage: resource-dashboard.sh

set -euo pipefail

REFRESH_INTERVAL=5

# Color codes (ANSI)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

# Function to format resource bar
format_resource_bar() {
  value=$1
  width=30
  # Convert float to int, handle empty values
  value_int=$(echo "$value" | cut -d'.' -f1)
  value_int=${value_int:-0}

  filled=$(( (value_int * width) / 100 ))
  empty=$(( width - filled ))

  # Color based on value
  if (( value_int >= 90 )); then
    color="$RED"
  elif (( value_int >= 75 )); then
    color="$YELLOW"
  else
    color="$GREEN"
  fi

  echo -ne "${color}"
  printf '█%.0s' $(seq 1 $filled) 2>/dev/null
  echo -ne "${DIM}"
  printf '░%.0s' $(seq 1 $empty) 2>/dev/null
  echo -ne "${NC}"
}

# Function to get system resources using standard tools
get_system_resources() {
  # CPU usage (last 1 second average)
  cpu=$(ps -A -o %cpu | awk '{s+=$1} END {print s}')
  cpu=${cpu:-0}

  # Memory usage
  mem=$(ps -A -o %mem | awk '{s+=$1} END {print s}')
  mem=${mem:-0}

  # Disk usage for root
  disk=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
  disk=${disk:-0}

  echo "$cpu|$mem|$disk"
}

# Function to get AI Brain process stats
get_process_stats() {
  # Count Python processes related to AI Brain
  python_procs=$(ps aux | grep -E "autonomous_loop|parallel_autonomous" | grep -v grep | wc -l | tr -d ' ')

  # Get total memory used by AI Brain processes (in MB)
  mem_kb=$(ps aux | grep -E "autonomous_loop|parallel_autonomous" | grep -v grep | awk '{sum+=$6} END {print sum}')
  mem_mb=$((${mem_kb:-0} / 1024))

  echo "$python_procs|$mem_mb"
}

# Main monitoring loop
while true; do
  clear

  # Header
  echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${CYAN}║  RESOURCE USAGE DASHBOARD                                 ║${NC}"
  echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Get resource data
  resources=$(get_system_resources)
  cpu=$(echo "$resources" | cut -d'|' -f1 | cut -d'.' -f1)
  memory=$(echo "$resources" | cut -d'|' -f2 | cut -d'.' -f1)
  disk=$(echo "$resources" | cut -d'|' -f3)

  # Display system resources
  echo -e "${BOLD}System Resources:${NC}"
  echo -e "  ${BOLD}CPU Usage:${NC}"
  echo -e "    ${cpu}% $(format_resource_bar "$cpu")"
  echo ""
  echo -e "  ${BOLD}Memory Usage:${NC}"
  echo -e "    ${memory}% $(format_resource_bar "$memory")"
  echo ""
  echo -e "  ${BOLD}Disk Usage:${NC}"
  echo -e "    ${disk}% $(format_resource_bar "$disk")"
  echo ""

  # Worker stats (from tmux monitors)
  active_workers=$(ps aux | grep "bin/tmux-monitors/agent-monitor" | grep -v grep | wc -l | tr -d ' ')
  echo -e "${BOLD}Worker Status:${NC}"
  echo -e "  ${BOLD}Active Monitors:${NC} ${GREEN}${active_workers}${NC} agent monitors running"

  # Process stats
  proc_stats=$(get_process_stats)
  proc_count=$(echo "$proc_stats" | cut -d'|' -f1)
  proc_mem=$(echo "$proc_stats" | cut -d'|' -f2)

  echo -e "  ${BOLD}AI Brain Processes:${NC} ${proc_count}"
  echo -e "  ${BOLD}Memory Usage (AI Brain):${NC} ${proc_mem} MB"

  echo ""

  # System info
  echo -e "${BOLD}System Info:${NC}"
  echo -e "  ${DIM}Hostname:${NC} $(hostname -s)"
  echo -e "  ${DIM}Load Average:${NC} $(uptime | awk -F'load averages:' '{print $2}' | xargs)"

  echo ""
  echo -e "${BOLD}${CYAN}────────────────────────────────────────────────────────────${NC}"
  echo -e "Last updated: $(date '+%H:%M:%S') | Refresh: ${REFRESH_INTERVAL}s"

  sleep "$REFRESH_INTERVAL"
done
