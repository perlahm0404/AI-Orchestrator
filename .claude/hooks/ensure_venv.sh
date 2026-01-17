#!/bin/bash
#
# Pre-tool hook: Ensures Python commands use the .venv
#
# This hook is called before every Bash tool invocation.
# It reads the tool input from stdin and can:
# - Exit 0: Allow the command
# - Exit 2: Block the command with a message to stderr
#
# The hook receives JSON on stdin with the tool input.
#

VENV_PATH="/Users/tmac/1_REPOS/AI_Orchestrator/.venv"
ORCHESTRATOR_PATH="/Users/tmac/1_REPOS/AI_Orchestrator"
VENV_PYTHON="${VENV_PATH}/bin/python"

# Read the tool input from stdin
INPUT=$(cat)

# Extract the command from JSON
COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"command"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//' || echo "")

# Skip if no command extracted
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# Check if this is a bare python/python3 command (not already using venv)
if echo "$COMMAND" | grep -qE "^(python|python3) "; then
    # Check if it's NOT using the venv
    if [[ "$COMMAND" != *".venv/bin/python"* ]] && [[ "$COMMAND" != *"${VENV_PYTHON}"* ]]; then
        # Block and suggest using venv
        echo "BLOCKED: Python commands must use .venv" >&2
        echo "" >&2
        echo "Instead of:" >&2
        echo "  $COMMAND" >&2
        echo "" >&2
        echo "Use:" >&2
        FIXED_COMMAND=$(echo "$COMMAND" | sed -E "s|^python3? |${VENV_PYTHON} |")
        echo "  $FIXED_COMMAND" >&2
        echo "" >&2
        echo "Or activate the venv first:" >&2
        echo "  source ${VENV_PATH}/bin/activate && $COMMAND" >&2
        exit 2
    fi
fi

# Check if this is a pip command (should use venv pip)
if echo "$COMMAND" | grep -qE "^pip "; then
    if [[ "$COMMAND" != *".venv/bin/pip"* ]]; then
        echo "BLOCKED: pip commands must use .venv/bin/pip" >&2
        echo "" >&2
        echo "Instead of:" >&2
        echo "  $COMMAND" >&2
        echo "" >&2
        echo "Use:" >&2
        echo "  ${VENV_PATH}/bin/pip ${COMMAND#pip }" >&2
        exit 2
    fi
fi

# Check if this is a pytest command (should use venv pytest)
if echo "$COMMAND" | grep -qE "^pytest "; then
    if [[ "$COMMAND" != *".venv/bin/pytest"* ]]; then
        echo "BLOCKED: pytest commands must use .venv/bin/pytest" >&2
        echo "" >&2
        echo "Instead of:" >&2
        echo "  $COMMAND" >&2
        echo "" >&2
        echo "Use:" >&2
        echo "  ${VENV_PATH}/bin/pytest ${COMMAND#pytest }" >&2
        exit 2
    fi
fi

# Check for source .venv/bin/activate - this is allowed
if echo "$COMMAND" | grep -qE "source.*\.venv/bin/activate"; then
    exit 0
fi

# Team enforcement: Check AI_ORCHESTRATOR_TEAM environment variable
# This integrates with the branch enforcement system
TEAM="${AI_ORCHESTRATOR_TEAM:-}"
if [[ -n "$TEAM" ]]; then
    # Log team context for audit
    # echo "[HOOK] Team: $TEAM executing: ${COMMAND:0:50}..." >&2
    :
fi

# Allow the command
exit 0
