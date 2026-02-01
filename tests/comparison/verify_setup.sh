#!/bin/bash
# Verify Kimi vs Opus comparison test setup
# Usage: ./tests/comparison/verify_setup.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Kimi vs Opus Setup Verification${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Track overall status
ERRORS=0

# 1. Check Python version
echo -n "Checking Python version... "
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
if python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3.8+ required (found $PYTHON_VERSION)${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 2. Check API keys
echo -n "Checking ANTHROPIC_API_KEY... "
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo -e "${GREEN}✓ Set${NC}"
else
    echo -e "${RED}✗ Not set${NC}"
    echo -e "${YELLOW}  Run: export ANTHROPIC_API_KEY='sk-ant-api03-...'${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo -n "Checking KIMI_API_KEY... "
if [ -n "$KIMI_API_KEY" ]; then
    echo -e "${GREEN}✓ Set${NC}"
else
    echo -e "${RED}✗ Not set${NC}"
    echo -e "${YELLOW}  Run: export KIMI_API_KEY='sk-...'${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 3. Check dependencies
echo -n "Checking anthropic package... "
if python -c "import anthropic" 2>/dev/null; then
    echo -e "${GREEN}✓ Installed${NC}"
else
    echo -e "${RED}✗ Not installed${NC}"
    echo -e "${YELLOW}  Run: pip install anthropic${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo -n "Checking openai package... "
if python -c "import openai" 2>/dev/null; then
    echo -e "${GREEN}✓ Installed${NC}"
else
    echo -e "${RED}✗ Not installed${NC}"
    echo -e "${YELLOW}  Run: pip install openai${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 4. Check test files
echo -n "Checking test harness... "
if [ -f "tests/comparison/test_kimi_vs_opus.py" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Missing${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo -n "Checking analysis script... "
if [ -f "tests/comparison/analyze_results.py" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Missing${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo -n "Checking prompts directory... "
PROMPT_COUNT=$(ls tests/comparison/prompts/*.txt 2>/dev/null | wc -l)
if [ "$PROMPT_COUNT" -eq 9 ]; then
    echo -e "${GREEN}✓ All 9 prompts found${NC}"
else
    echo -e "${RED}✗ Expected 9 prompts, found $PROMPT_COUNT${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 5. Check directory structure
echo -n "Checking results directory... "
if [ -d "tests/comparison/results" ]; then
    echo -e "${GREEN}✓ Exists${NC}"
else
    echo -e "${YELLOW}⚠ Creating results directory...${NC}"
    mkdir -p tests/comparison/results
    echo -e "${GREEN}✓ Created${NC}"
fi

# 6. Test API connectivity (optional, requires keys)
if [ -n "$ANTHROPIC_API_KEY" ] && [ -n "$KIMI_API_KEY" ]; then
    echo ""
    echo -e "${YELLOW}Testing API connectivity (optional)...${NC}"

    echo -n "Testing Anthropic API... "
    if curl -s -f -X POST https://api.anthropic.com/v1/messages \
        -H "x-api-key: $ANTHROPIC_API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d '{"model":"claude-opus-4-5-20251101","max_tokens":10,"messages":[{"role":"user","content":"test"}]}' \
        > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Connected${NC}"
    else
        echo -e "${RED}✗ Connection failed${NC}"
        echo -e "${YELLOW}  Check API key or network connection${NC}"
        ERRORS=$((ERRORS + 1))
    fi

    echo -n "Testing Kimi API... "
    if curl -s -f -X POST https://api.moonshot.ai/v1/chat/completions \
        -H "Authorization: Bearer $KIMI_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"model":"kimi-k2-thinking-turbo","messages":[{"role":"user","content":"test"}]}' \
        > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Connected${NC}"
    else
        echo -e "${RED}✗ Connection failed${NC}"
        echo -e "${YELLOW}  Check API key or network connection${NC}"
        ERRORS=$((ERRORS + 1))
    fi
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Setup verification passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Ready to run tests:"
    echo "  ./tests/comparison/run_comparison.sh"
    echo ""
    echo "Or manually:"
    echo "  python tests/comparison/test_kimi_vs_opus.py --model kimi-k2-thinking-turbo"
    exit 0
else
    echo -e "${RED}✗ Setup verification failed ($ERRORS errors)${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Please fix the errors above before running tests."
    exit 1
fi
