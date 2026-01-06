#!/bin/bash
#
# Run an AI Orchestrator agent within the governed harness.
# This script ensures the .venv is always activated.
#
# Usage:
#   ./run_agent.sh --project karematch --task "Fix the auth bug"
#   ./run_agent.sh --project karematch --task "Fix bugs" --agent-type codequality
#   ./run_agent.sh --project karematch --task "Fix bugs" --dry-run
#
# Options:
#   --project       Target project (karematch, credentialmate)
#   --task          Task description for the agent
#   --agent-type    Agent type: bugfix (default), codequality, qa-team, dev-team
#   --with-watcher  Enable real-time file monitoring
#   --dry-run       Show what would happen without executing
#   --timeout       Timeout in minutes (default: 30)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/.venv"

# Check venv exists
if [ ! -d "${VENV_PATH}" ]; then
    echo "Error: Virtual environment not found at ${VENV_PATH}"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv and run
source "${VENV_PATH}/bin/activate"

# Set PYTHONPATH to include the orchestrator
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Set harness environment variable (signals we're in governed mode)
export AI_ORCHESTRATOR_HARNESS_ACTIVE=1

# Run the governed session
exec python -m harness.governed_session "$@"
