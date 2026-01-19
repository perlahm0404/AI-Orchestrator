#!/usr/bin/env bash
# parallel-multi-repo.sh - Launch parallel autonomous loops for karematch + credentialmate
#
# Usage:
#   ./bin/parallel-multi-repo.sh [options]
#
# Options:
#   --max-parallel N    Max parallel workers per repo (default: 3)
#   --max-iterations N  Max iterations before stopping (default: 100)
#   --non-interactive   Auto-revert guardrails, auto-approve prompts
#
# Examples:
#   ./bin/parallel-multi-repo.sh
#   ./bin/parallel-multi-repo.sh --max-parallel 5 --max-iterations 200
#   ./bin/parallel-multi-repo.sh --non-interactive

set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================
REPO_ROOT="/Users/tmac/1_REPOS/AI_Orchestrator"
LOG_DIR="$REPO_ROOT/.aibrain/tmux-logs"

# Default options
MAX_PARALLEL=3
MAX_ITERATIONS=100
NON_INTERACTIVE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --max-parallel)
      MAX_PARALLEL="$2"
      shift 2
      ;;
    --max-iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --non-interactive)
      NON_INTERACTIVE="--non-interactive"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--max-parallel N] [--max-iterations N] [--non-interactive]"
      exit 1
      ;;
  esac
done

# ==============================================================================
# SETUP
# ==============================================================================
# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Change to AI_Orchestrator directory
cd "$REPO_ROOT" || exit 1

# Activate virtual environment
if [[ -d ".venv" ]]; then
  source .venv/bin/activate
else
  echo "❌ ERROR: Virtual environment not found at .venv/"
  echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# ==============================================================================
# LAUNCH PARALLEL AUTONOMOUS LOOPS
# ==============================================================================
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  AI ORCHESTRATOR - MULTI-REPO PARALLEL EXECUTION              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  - Max Parallel Workers: $MAX_PARALLEL"
echo "  - Max Iterations: $MAX_ITERATIONS"
echo "  - Non-Interactive: ${NON_INTERACTIVE:-false}"
echo ""
echo "Launching autonomous loops..."
echo ""

# Launch KareMatch
echo "🚀 Starting KareMatch autonomous loop..."
python parallel_autonomous_loop.py \
  --project karematch \
  --max-parallel "$MAX_PARALLEL" \
  --max-iterations "$MAX_ITERATIONS" \
  $NON_INTERACTIVE \
  > "$LOG_DIR/karematch-parallel.log" 2>&1 &

KM_PID=$!
echo "   ✅ KareMatch launched (PID: $KM_PID)"
echo "   📋 Logs: $LOG_DIR/karematch-parallel.log"
echo ""

# Launch CredentialMate
echo "🚀 Starting CredentialMate autonomous loop..."
python parallel_autonomous_loop.py \
  --project credentialmate \
  --max-parallel "$MAX_PARALLEL" \
  --max-iterations "$MAX_ITERATIONS" \
  $NON_INTERACTIVE \
  > "$LOG_DIR/credentialmate-parallel.log" 2>&1 &

CM_PID=$!
echo "   ✅ CredentialMate launched (PID: $CM_PID)"
echo "   📋 Logs: $LOG_DIR/credentialmate-parallel.log"
echo ""

# ==============================================================================
# MONITORING
# ==============================================================================
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  MONITORING                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Background processes running:"
echo "  - KareMatch: PID $KM_PID"
echo "  - CredentialMate: PID $CM_PID"
echo ""
echo "To view real-time logs:"
echo "  tail -f $LOG_DIR/karematch-parallel.log"
echo "  tail -f $LOG_DIR/credentialmate-parallel.log"
echo ""
echo "To stop processes:"
echo "  kill $KM_PID $CM_PID"
echo ""
echo "tmux Navigation:"
echo "  Alt+R - Switch to Repos window (see work queue status)"
echo "  Alt+A - Switch to Agents window (see worker activity)"
echo "  Alt+M - Switch to Metrics window (see performance)"
echo ""

# ==============================================================================
# WAIT FOR COMPLETION
# ==============================================================================
# Store PIDs in a file for cleanup
echo "$KM_PID" > "$LOG_DIR/.karematch.pid"
echo "$CM_PID" > "$LOG_DIR/.credentialmate.pid"

# Wait for both processes to complete
echo "⏳ Waiting for autonomous loops to complete..."
echo "   (Press Ctrl+C to stop all processes and exit)"
echo ""

# Trap Ctrl+C to clean up
trap "echo ''; echo '🛑 Stopping all processes...'; kill $KM_PID $CM_PID 2>/dev/null; rm -f $LOG_DIR/.karematch.pid $LOG_DIR/.credentialmate.pid; echo '✅ Stopped'; exit 0" INT TERM

# Wait for both processes
wait $KM_PID $CM_PID

# Clean up PID files
rm -f "$LOG_DIR/.karematch.pid" "$LOG_DIR/.credentialmate.pid"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  COMPLETED                                                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Both autonomous loops have completed."
echo ""
echo "Review logs:"
echo "  $LOG_DIR/karematch-parallel.log"
echo "  $LOG_DIR/credentialmate-parallel.log"
echo ""
