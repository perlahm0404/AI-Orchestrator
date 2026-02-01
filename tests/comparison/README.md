# Kimi vs Opus 4.5 Comparative Testing

This directory contains infrastructure for comparing Kimi thinking models against Claude Opus 4.5 on complex reasoning tasks.

## Overview

**Purpose**: Validate that Kimi thinking models (kimi-k2-thinking-turbo, kimi-k2-thinking) meet or exceed Claude Opus 4.5 performance on complex reasoning tasks from the AI Orchestrator codebase.

**Success Criteria**: Kimi must achieve ≥95% of Opus 4.5 quality scores across 3 dimensions: correctness, reasoning depth, and actionability.

## Test Cases

### Tier 1: Moderate Complexity (Warmup)
1. **TC1**: Email Classification Bug Analysis
2. **TC2**: TypeScript Build Error Diagnosis
3. **TC3**: Claude CLI Environment Configuration

### Tier 2: High Complexity (Core Validation)
4. **TC4**: Profile Save 401 Authentication Error ⭐ CRITICAL
5. **TC5**: CME Rules Engine Fidelity Sync ⭐ CRITICAL
6. **TC6**: Token Optimization Trade-off Analysis

### Tier 3: Expert-Level Complexity (Stretch Goals)
7. **TC7**: Anthropic Agent SDK Adoption Decision
8. **TC8**: Documentation Architecture Consolidation
9. **TC9**: LlamaIndex Technology Assessment

## Quick Start

### 1. Setup Environment

```bash
# Ensure API keys are set
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export KIMI_API_KEY="sk-6T3FckoAlryBduPNYFd6jlnK40D0Q9evb6s8uMbgoROcYymW"

# Install dependencies (if not already installed)
pip install anthropic openai
```

### 2. Run Tests

```bash
# Run Kimi thinking-turbo comparison
python tests/comparison/test_kimi_vs_opus.py --model kimi-k2-thinking-turbo

# Optional: Run Kimi deep thinking (slower, more thorough)
python tests/comparison/test_kimi_vs_opus.py --model kimi-k2-thinking
```

**Expected Duration**: 2-3 hours per run (9 test cases × 2 models × 15-30s per response)

**Output**: `tests/comparison/results/comparison_kimi_k2_thinking_turbo_YYYYMMDD_HHMMSS.json`

### 3. Manual Scoring

Open the results JSON file and add scores for each response:

```json
{
  "opus": {
    "scores": {
      "quality": 8.5,        // 1-10 scale
      "reasoning": 7.5,      // 1-10 scale
      "actionability": 9.0   // 1-10 scale
    }
  },
  "kimi": {
    "scores": {
      "quality": 8.0,
      "reasoning": 7.0,
      "actionability": 8.5
    }
  }
}
```

**Scoring Rubrics**: See [Evaluation Rubrics](#evaluation-rubrics) below.

### 4. Analyze Results

```bash
# Run analysis script
python tests/comparison/analyze_results.py results/comparison_kimi_k2_thinking_turbo_20260129_143022.json
```

**Output**: Comprehensive report with:
- Aggregate scores (quality, reasoning, actionability)
- Per-tier performance
- Win/lose/tie breakdown
- Cost efficiency metrics
- Speed metrics
- Success criteria evaluation
- Final recommendation

### 5. Print Summary (Without Scoring)

```bash
# Print basic metrics without manual scoring
python tests/comparison/test_kimi_vs_opus.py --summary results/comparison_kimi_k2_thinking_turbo_20260129_143022.json
```

## Evaluation Rubrics

### Quality Score (1-10 scale)

- **10 (Perfect)**: Identifies root cause with 100% accuracy, comprehensive solution, anticipates edge cases
- **8-9 (Excellent)**: Identifies root cause correctly, actionable solution, covers main edge cases
- **6-7 (Good)**: Identifies likely root cause, workable solution, some edge cases missed
- **4-5 (Acceptable)**: Identifies possible causes, solution requires refinement, major edge cases missed
- **1-3 (Poor)**: Misses root cause, solution ineffective, critical gaps in reasoning

### Reasoning Depth Score (1-10 scale)

- **10 (Expert-Level)**: Explores 5+ hypotheses, systematic elimination, considers second-order effects, provides alternatives
- **8-9 (Deep)**: Explores 3-4 hypotheses, systematic elimination, considers trade-offs, multi-dimensional analysis
- **6-7 (Moderate)**: Explores 2-3 hypotheses, basic elimination, some trade-off consideration
- **4-5 (Shallow)**: Single hypothesis, jumps to conclusion, minimal trade-off analysis
- **1-3 (Surface-Level)**: No hypothesis exploration, pattern matching only, no alternatives considered

### Actionability Score (1-10 scale)

- **10 (Immediately Executable)**: Step-by-step instructions, code examples, verification steps, success criteria defined
- **8-9 (Highly Actionable)**: Clear action items, most details provided, verification mentioned
- **6-7 (Actionable with Effort)**: General direction clear, some details missing, implementation left to reader
- **4-5 (Vague)**: High-level suggestions, many details missing, significant work to implement
- **1-3 (Not Actionable)**: Abstract concepts only, no concrete steps, unable to implement

## Success Criteria

### Minimum Requirements (MUST MEET)

**Overall Performance**:
- Kimi overall quality score ≥ 95% of Opus baseline
- Kimi reasoning depth score ≥ 95% of Opus baseline
- Kimi actionability score ≥ 95% of Opus baseline

**Per-Tier Performance**:
- Tier 1 (Moderate): Kimi ≥ 90% of Opus
- Tier 2 (High): Kimi ≥ 95% of Opus ⭐ CRITICAL
- Tier 3 (Expert): Kimi ≥ 90% of Opus

**Critical Test Cases**:
- TC4 (Profile 401 Error): MUST match or exceed Opus
- TC5 (CME Rules Sync): MUST match or exceed Opus

### Stretch Goals (NICE TO HAVE)

- Kimi > Opus on ≥3 test cases
- Kimi faster than Opus on Tier 1 tasks
- Kimi ≥50% cheaper than Opus while maintaining quality

## Decision Matrix

### If Kimi Meets All Success Criteria (≥95%)
**Decision**: ADOPT Kimi thinking models for reasoning tasks

**Next Steps**:
1. Implement full KimiProvider class
2. Add to factory with intelligent routing
3. Update governance contracts
4. Start Phase 2 pilot (ProductManagerAgent)

### If Kimi Meets 90-94% Threshold
**Decision**: CONDITIONAL ADOPTION

**Next Steps**:
1. Identify specific gaps (which test cases failed?)
2. Determine if gaps are acceptable for specific use cases
3. Adopt for low-risk reasoning tasks only
4. Continue monitoring performance

### If Kimi Below 90% Threshold
**Decision**: REJECT for now, revisit later

**Next Steps**:
1. Document specific failure modes
2. Provide feedback to Moonshot AI
3. Test fallback models (kimi-k2.5, kimi-turbo)
4. Re-evaluate in 3-6 months

## File Structure

```
tests/comparison/
├── README.md                           # This file
├── test_kimi_vs_opus.py                # Main test harness
├── analyze_results.py                  # Analysis script
├── prompts/                            # Standardized test prompts
│   ├── tc1_email_classification.txt
│   ├── tc2_typescript_build_errors.txt
│   ├── tc3_claude_cli_config.txt
│   ├── tc4_profile_401_error.txt       ⭐ CRITICAL
│   ├── tc5_cme_rules_sync.txt          ⭐ CRITICAL
│   ├── tc6_token_optimization.txt
│   ├── tc7_agent_sdk_decision.txt
│   ├── tc8_documentation_architecture.txt
│   └── tc9_llamaindex_evaluation.txt
└── results/                            # Raw outputs (gitignored)
    └── comparison_*.json
```

## Pricing Assumptions

**Claude Opus 4.5**:
- Input: $15.00 / 1M tokens
- Output: $75.00 / 1M tokens

**Kimi k2-thinking-turbo** (conservative estimates):
- Input: $4.00 / 1M tokens
- Output: $12.00 / 1M tokens

**Kimi k2-thinking** (deeper, slower):
- Input: $6.00 / 1M tokens (estimated)
- Output: $18.00 / 1M tokens (estimated)

## Performance Expectations

**Latency**:
- Opus 4.5: 20-40s per response (complex reasoning)
- Kimi thinking-turbo: 15-30s per response (60-100 tokens/s)
- Kimi thinking: 30-60s per response (deeper reasoning)

**Token Usage**:
- Input: 1,000-3,000 tokens per test case (prompts)
- Output: 2,000-8,000 tokens per response (detailed analysis)

**Total Cost Estimate** (per full run):
- Opus 4.5: $3-5
- Kimi thinking-turbo: $1-2
- Savings: 50-66%

## Known Limitations

1. **Manual Scoring Required**: Quality assessment is subjective and requires human judgment
2. **Inter-Rater Reliability**: Should have 2 reviewers for objectivity (Cohen's kappa ≥ 0.70)
3. **Sample Size**: 9 test cases is small; results are indicative, not conclusive
4. **Domain Specificity**: Test cases are from AI Orchestrator codebase; may not generalize

## Troubleshooting

### API Key Issues
```bash
# Verify keys are set
echo $ANTHROPIC_API_KEY
echo $KIMI_API_KEY

# Test Anthropic API
curl https://api.anthropic.com/v1/messages -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" -H "content-type: application/json" -d '{"model":"claude-opus-4-5-20251101","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'

# Test Kimi API
curl https://api.moonshot.ai/v1/chat/completions -H "Authorization: Bearer $KIMI_API_KEY" -H "Content-Type: application/json" -d '{"model":"kimi-k2-thinking-turbo","messages":[{"role":"user","content":"test"}]}'
```

### Import Errors
```bash
# Install missing dependencies
pip install anthropic openai
```

### Timeout Errors
- Increase timeout in test harness (default: 120s)
- Kimi thinking models may take longer for complex reasoning
- Consider using `kimi-k2-thinking-turbo` (faster) instead of `kimi-k2-thinking`

## Contributing

To add new test cases:

1. Create prompt file in `prompts/tcN_description.txt`
2. Update test case list in `test_kimi_vs_opus.py`
3. Document expected output and evaluation criteria in prompt
4. Update this README with test case description

## References

- [Kimi API Documentation](https://platform.moonshot.cn/docs)
- [Claude API Documentation](https://docs.anthropic.com/en/api)
- [AI Orchestrator Documentation](../../docs/)
- [Validation Plan](../../work/plans-active/kimi-thinking-validation-plan.md)
