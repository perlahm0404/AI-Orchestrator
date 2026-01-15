#!/bin/bash
#
# ralph.sh - Real Ralph Loop (Fresh Session Per Iteration)
#
# This script implements the "Real Ralph" pattern: a bash while-loop that
# spawns a NEW Claude Code session for each iteration, ensuring fresh context
# windows and preventing context pollution across attempts.
#
# KEY DIFFERENCE FROM PLUGIN RALPH:
# - Plugin Ralph: Runs in a single long-lived session with auto-compaction.
#                 Context accumulates and may cause drift or confusion.
# - Real Ralph:   Each iteration starts a BRAND NEW Claude Code process.
#                 The only shared context is PRD.md + progress.md files.
#                 This ensures clean, predictable behavior on every attempt.
#
# HOW FRESH SESSIONS WORK:
# 1. This script runs in a bash loop OUTSIDE of Claude Code.
# 2. Each iteration invokes `claude` CLI as a subprocess with --print and -p.
# 3. The subprocess receives PRD.md + progress.md as context, works on ONE task.
# 4. The subprocess terminates, its context is discarded.
# 5. Only file-system artifacts (PRD.md, progress.md, code changes) persist.
# 6. Next iteration starts with zero in-memory context from previous attempts.
#
# Usage:
#   ./ralph.sh                  # Default: 10 iterations
#   ./ralph.sh 50               # Custom: 50 iterations
#   ./ralph.sh 100 --verbose    # Verbose mode with full Claude output
#
# Requirements:
#   - `claude` CLI must be installed and in PATH
#   - .ralph/PRD.md must exist
#   - .ralph/progress.md will be created if it doesn't exist
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RALPH_DIR="${SCRIPT_DIR}/.ralph"
PRD_FILE="${RALPH_DIR}/PRD.md"
PROGRESS_FILE="${RALPH_DIR}/progress.md"
MAX_ITERATIONS="${1:-10}"
VERBOSE="${2:-}"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Header
echo ""
echo "=============================================="
echo "  Real Ralph Loop - Fresh Session Controller"
echo "=============================================="
echo ""
log_info "Max iterations: ${MAX_ITERATIONS}"
log_info "PRD file: ${PRD_FILE}"
log_info "Progress file: ${PROGRESS_FILE}"
echo ""

# Validate prerequisites
if ! command -v claude &> /dev/null; then
    log_error "Claude CLI not found. Please install it first."
    log_info "Visit: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

if [ ! -f "${PRD_FILE}" ]; then
    log_error "PRD.md not found at ${PRD_FILE}"
    log_info "Create a PRD.md file with tasks and acceptance criteria."
    log_info "See RALPH.md for the expected format."
    exit 1
fi

# Initialize progress file if it doesn't exist
if [ ! -f "${PROGRESS_FILE}" ]; then
    log_info "Creating initial progress.md..."
    cat > "${PROGRESS_FILE}" << 'EOF'
# Ralph Progress Log

This file tracks iteration attempts, failures, and patterns across Real Ralph sessions.

---

## Session Started

**Timestamp**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Max Iterations**: $(echo $MAX_ITERATIONS)

---

## Iteration Log

EOF
    # Replace placeholders with actual values
    sed -i.bak "s/\$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")/$(date -u +"%Y-%m-%dT%H:%M:%SZ")/" "${PROGRESS_FILE}"
    sed -i.bak "s/\$(echo \$MAX_ITERATIONS)/${MAX_ITERATIONS}/" "${PROGRESS_FILE}"
    rm -f "${PROGRESS_FILE}.bak"
fi

# Count incomplete tasks in PRD.md
count_incomplete_tasks() {
    # Count lines that have unchecked checkboxes: - [ ]
    grep -c '^\s*- \[ \]' "${PRD_FILE}" 2>/dev/null || echo "0"
}

# Get the first incomplete task
get_first_incomplete_task() {
    # Extract the first line with an unchecked checkbox
    grep -m 1 '^\s*- \[ \]' "${PRD_FILE}" 2>/dev/null | sed 's/^\s*- \[ \] //' || echo ""
}

# Build the prompt for Claude
build_prompt() {
    local iteration=$1
    local task="$2"

    cat << EOF
You are working on iteration ${iteration} of a Real Ralph loop.

## Your Mission

Complete the following task from PRD.md:
**${task}**

## Context Files

Read these files for full context:
1. PRD.md - Contains all tasks and acceptance criteria
2. progress.md - Contains history of previous attempts

## Instructions

1. Read PRD.md and progress.md to understand the task and any previous attempts.
2. Implement the solution for the task described above.
3. When the task is complete:
   - Mark the checkbox as done in PRD.md: change "- [ ]" to "- [x]"
   - Add an entry to progress.md documenting what you did
4. If you cannot complete the task:
   - Do NOT mark it as complete
   - Add a detailed entry to progress.md explaining:
     - What you attempted
     - What errors or blockers you encountered
     - Any hypotheses for the next attempt

## Critical Rules

- Focus ONLY on the task specified above
- Do NOT skip ahead to other tasks
- Do NOT mark tasks complete unless they actually work
- Be honest in progress.md about failures

## Output Format

When done, output a single line summary:
RALPH_RESULT: [COMPLETED|FAILED] - <brief description>
EOF
}

# Main loop
log_info "Starting Ralph loop..."
echo ""

ITERATION=0
while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))

    # Check remaining tasks
    INCOMPLETE=$(count_incomplete_tasks)

    if [ "$INCOMPLETE" -eq 0 ]; then
        echo ""
        log_success "All tasks in PRD.md are complete!"
        echo ""
        echo "=============================================="
        echo "  Ralph Loop Finished - All Tasks Complete"
        echo "=============================================="
        exit 0
    fi

    # Get the current task
    TASK=$(get_first_incomplete_task)

    if [ -z "$TASK" ]; then
        log_warn "No incomplete tasks found, but count was ${INCOMPLETE}. Check PRD.md format."
        break
    fi

    echo "----------------------------------------------"
    log_info "Iteration ${ITERATION}/${MAX_ITERATIONS}"
    log_info "Remaining tasks: ${INCOMPLETE}"
    log_info "Current task: ${TASK}"
    echo "----------------------------------------------"

    # Build prompt
    PROMPT=$(build_prompt "$ITERATION" "$TASK")

    # Record attempt in progress file
    echo "" >> "${PROGRESS_FILE}"
    echo "### Iteration ${ITERATION}" >> "${PROGRESS_FILE}"
    echo "**Timestamp**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "${PROGRESS_FILE}"
    echo "**Task**: ${TASK}" >> "${PROGRESS_FILE}"
    echo "" >> "${PROGRESS_FILE}"

    # Run Claude in a NEW session
    # --print: Output to stdout (don't open interactive mode)
    # -p: Pass the prompt directly
    # This spawns a FRESH Claude Code process with no prior context
    log_info "Spawning fresh Claude Code session..."

    if [ "$VERBOSE" = "--verbose" ]; then
        # Show full output
        if claude --print -p "$PROMPT" 2>&1; then
            CLAUDE_EXIT=$?
        else
            CLAUDE_EXIT=$?
        fi
    else
        # Capture output, show only result line
        OUTPUT=$(claude --print -p "$PROMPT" 2>&1) || true
        CLAUDE_EXIT=$?

        # Extract and display result line
        RESULT_LINE=$(echo "$OUTPUT" | grep "RALPH_RESULT:" | tail -1 || echo "")
        if [ -n "$RESULT_LINE" ]; then
            echo "$RESULT_LINE"
        fi
    fi

    # Log result
    if [ $CLAUDE_EXIT -eq 0 ]; then
        echo "**Status**: Session completed (exit 0)" >> "${PROGRESS_FILE}"
    else
        echo "**Status**: Session error (exit ${CLAUDE_EXIT})" >> "${PROGRESS_FILE}"
    fi

    # Check if task was completed
    NEW_INCOMPLETE=$(count_incomplete_tasks)
    if [ "$NEW_INCOMPLETE" -lt "$INCOMPLETE" ]; then
        log_success "Task completed! Remaining: ${NEW_INCOMPLETE}"
        echo "**Result**: COMPLETED" >> "${PROGRESS_FILE}"
    else
        log_warn "Task not completed. Will retry on next iteration."
        echo "**Result**: INCOMPLETE - will retry" >> "${PROGRESS_FILE}"
    fi

    echo ""
done

# Final status
echo ""
echo "=============================================="
FINAL_INCOMPLETE=$(count_incomplete_tasks)
if [ "$FINAL_INCOMPLETE" -eq 0 ]; then
    log_success "All tasks completed!"
else
    log_warn "Iteration budget exhausted."
    log_warn "Remaining incomplete tasks: ${FINAL_INCOMPLETE}"
    echo ""
    echo "Incomplete tasks:"
    grep '^\s*- \[ \]' "${PRD_FILE}" | head -10
fi
echo "=============================================="
echo ""
log_info "See progress.md for detailed iteration history."
