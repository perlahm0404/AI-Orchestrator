#!/bin/bash
# Kimi vs Opus 4.5 Comparison Test Runner
# Usage: ./tests/comparison/run_comparison.sh [kimi-k2-thinking-turbo|kimi-k2-thinking]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default model
MODEL="${1:-kimi-k2-thinking-turbo}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Kimi vs Opus 4.5 Comparison Test${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}Error: ANTHROPIC_API_KEY not set${NC}"
    echo "Please export ANTHROPIC_API_KEY before running tests"
    exit 1
fi

if [ -z "$KIMI_API_KEY" ]; then
    echo -e "${RED}Error: KIMI_API_KEY not set${NC}"
    echo "Please export KIMI_API_KEY before running tests"
    exit 1
fi

echo -e "${GREEN}✓ API keys detected${NC}"
echo ""

# Check dependencies
echo "Checking dependencies..."
python -c "import anthropic" 2>/dev/null || {
    echo -e "${YELLOW}Installing anthropic...${NC}"
    pip install anthropic
}

python -c "import openai" 2>/dev/null || {
    echo -e "${YELLOW}Installing openai...${NC}"
    pip install openai
}

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Create results directory
mkdir -p tests/comparison/results

# Run tests
echo -e "${GREEN}Running comparison tests with model: $MODEL${NC}"
echo -e "${YELLOW}This will take 2-3 hours (9 test cases × 2 models × 15-30s per response)${NC}"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Starting tests..."
echo ""

# Run the test
python tests/comparison/test_kimi_vs_opus.py --model "$MODEL"

# Get the most recent results file
RESULTS_FILE=$(ls -t tests/comparison/results/comparison_*.json | head -1)

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Tests Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Results saved to: $RESULTS_FILE"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Review responses in the JSON file"
echo "2. Score each response using tests/comparison/scoring_template.md"
echo "3. Run analysis: python tests/comparison/analyze_results.py $RESULTS_FILE"
echo ""
echo -e "${GREEN}Or print basic summary now:${NC}"
echo "python tests/comparison/test_kimi_vs_opus.py --summary $RESULTS_FILE"
echo ""
