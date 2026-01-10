#!/bin/bash
# Autonomous CredentialMate Runner
# Usage: ./autonomous-credentialmate.sh [--discover] [--max-iterations N] [--queue bugs|features]

set -e

# Navigate to AI_Orchestrator root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Parse arguments
DISCOVER=false
MAX_ITER=100
QUEUE_TYPE="bugs"

while [[ $# -gt 0 ]]; do
    case $1 in
        --discover)
            DISCOVER=true
            shift
            ;;
        --max-iterations)
            MAX_ITER="$2"
            shift 2
            ;;
        --queue)
            QUEUE_TYPE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--discover] [--max-iterations N] [--queue bugs|features]"
            exit 1
            ;;
    esac
done

echo "🤖 AI Orchestrator - Autonomous CredentialMate Mode"
echo "=================================================="
echo ""

# Optional: Discover bugs first
if [ "$DISCOVER" = true ]; then
    echo "🔍 Discovering bugs in CredentialMate..."
    python3 -m cli.main discover-bugs --project credentialmate
    echo ""
fi

# Run autonomous loop
echo "🚀 Starting autonomous loop..."
echo "   Project: credentialmate"
echo "   Max iterations: $MAX_ITER"
echo "   Queue type: $QUEUE_TYPE"
echo ""

python3 autonomous_loop.py \
    --project credentialmate \
    --max-iterations "$MAX_ITER" \
    --queue "$QUEUE_TYPE"
