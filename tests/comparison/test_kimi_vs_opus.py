"""
Kimi vs Opus 4.5 Comparative Testing Framework

Tests Kimi thinking models against Claude Opus 4.5 on complex reasoning tasks.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    from anthropic import AsyncAnthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    raise

try:
    from openai import AsyncOpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    raise


@dataclass
class ModelResponse:
    """Response from a model with metadata."""
    content: str
    time_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    timestamp: str


@dataclass
class TestCaseResult:
    """Results for a single test case."""
    test_case_id: str
    test_case_name: str
    tier: int
    opus_response: ModelResponse
    kimi_response: ModelResponse

    # Manual scoring (to be filled in later)
    opus_quality: Optional[float] = None
    opus_reasoning: Optional[float] = None
    opus_actionability: Optional[float] = None

    kimi_quality: Optional[float] = None
    kimi_reasoning: Optional[float] = None
    kimi_actionability: Optional[float] = None

    notes: str = ""


class OpusProvider:
    """Claude Opus 4.5 provider."""

    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-opus-4-5-20251101"
        self.last_usage = None

    async def execute_task(self, prompt: str) -> ModelResponse:
        """Execute task and return response with metadata."""
        start = datetime.now()

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}]
        )

        elapsed = (datetime.now() - start).total_seconds()

        self.last_usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }

        return ModelResponse(
            content=response.content[0].text,
            time_seconds=elapsed,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            model=self.model,
            timestamp=datetime.now().isoformat()
        )


class KimiProvider:
    """Kimi thinking model provider."""

    def __init__(self, model: str = "kimi-k2-thinking-turbo"):
        self.client = AsyncOpenAI(
            api_key=os.getenv("KIMI_API_KEY"),
            base_url="https://api.moonshot.ai/v1"
        )
        self.model = model
        self.last_usage = None

    async def execute_task(self, prompt: str) -> ModelResponse:
        """Execute task and return response with metadata."""
        start = datetime.now()

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0  # Recommended for thinking models
        )

        elapsed = (datetime.now() - start).total_seconds()

        self.last_usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

        return ModelResponse(
            content=response.choices[0].message.content,
            time_seconds=elapsed,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            model=self.model,
            timestamp=datetime.now().isoformat()
        )


class ModelComparison:
    """Orchestrates model comparison testing."""

    def __init__(self, kimi_model: str = "kimi-k2-thinking-turbo"):
        self.opus_provider = OpusProvider()
        self.kimi_provider = KimiProvider(kimi_model)
        self.results: List[TestCaseResult] = []

    async def run_test_case(
        self,
        test_case_id: str,
        test_case_name: str,
        tier: int,
        prompt: str
    ) -> TestCaseResult:
        """Run both models on a single test case."""
        print(f"\n{'='*80}")
        print(f"Running Test Case: {test_case_id} - {test_case_name}")
        print(f"Tier: {tier}")
        print(f"{'='*80}\n")

        # Run Opus
        print(f"[1/2] Running Opus 4.5...")
        opus_response = await self.opus_provider.execute_task(prompt)
        print(f"✓ Opus completed in {opus_response.time_seconds:.1f}s "
              f"({opus_response.total_tokens:,} tokens)")

        # Run Kimi
        print(f"[2/2] Running Kimi ({self.kimi_provider.model})...")
        kimi_response = await self.kimi_provider.execute_task(prompt)
        print(f"✓ Kimi completed in {kimi_response.time_seconds:.1f}s "
              f"({kimi_response.total_tokens:,} tokens)")

        result = TestCaseResult(
            test_case_id=test_case_id,
            test_case_name=test_case_name,
            tier=tier,
            opus_response=opus_response,
            kimi_response=kimi_response
        )

        self.results.append(result)
        return result

    def save_results(self, output_path: str):
        """Save results to JSON file."""
        results_dict = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "kimi_model": self.kimi_provider.model,
                "opus_model": self.opus_provider.model,
                "test_count": len(self.results)
            },
            "results": [self._result_to_dict(r) for r in self.results]
        }

        Path(output_path).write_text(json.dumps(results_dict, indent=2))
        print(f"\n✓ Results saved to: {output_path}")

    def _result_to_dict(self, result: TestCaseResult) -> Dict[str, Any]:
        """Convert TestCaseResult to dictionary."""
        return {
            "test_case_id": result.test_case_id,
            "test_case_name": result.test_case_name,
            "tier": result.tier,
            "opus": {
                "content": result.opus_response.content,
                "time_seconds": result.opus_response.time_seconds,
                "tokens": {
                    "input": result.opus_response.input_tokens,
                    "output": result.opus_response.output_tokens,
                    "total": result.opus_response.total_tokens
                },
                "scores": {
                    "quality": result.opus_quality,
                    "reasoning": result.opus_reasoning,
                    "actionability": result.opus_actionability
                }
            },
            "kimi": {
                "content": result.kimi_response.content,
                "time_seconds": result.kimi_response.time_seconds,
                "tokens": {
                    "input": result.kimi_response.input_tokens,
                    "output": result.kimi_response.output_tokens,
                    "total": result.kimi_response.total_tokens
                },
                "scores": {
                    "quality": result.kimi_quality,
                    "reasoning": result.kimi_reasoning,
                    "actionability": result.kimi_actionability
                }
            },
            "notes": result.notes
        }


async def run_all_tests(kimi_model: str = "kimi-k2-thinking-turbo"):
    """Run all test cases."""
    comparison = ModelComparison(kimi_model)

    test_cases = [
        # Tier 1: Moderate Complexity
        ("TC1", "Email Classification Bug Analysis", 1, "tc1_email_classification.txt"),
        ("TC2", "TypeScript Build Error Diagnosis", 1, "tc2_typescript_build_errors.txt"),
        ("TC3", "Claude CLI Environment Configuration", 1, "tc3_claude_cli_config.txt"),

        # Tier 2: High Complexity
        ("TC4", "Profile Save 401 Authentication Error", 2, "tc4_profile_401_error.txt"),
        ("TC5", "CME Rules Engine Fidelity Sync", 2, "tc5_cme_rules_sync.txt"),
        ("TC6", "Token Optimization Trade-off Analysis", 2, "tc6_token_optimization.txt"),

        # Tier 3: Expert-Level Complexity
        ("TC7", "Anthropic Agent SDK Adoption Decision", 3, "tc7_agent_sdk_decision.txt"),
        ("TC8", "Documentation Architecture Consolidation", 3, "tc8_documentation_architecture.txt"),
        ("TC9", "LlamaIndex Technology Assessment", 3, "tc9_llamaindex_evaluation.txt"),
    ]

    prompts_dir = Path(__file__).parent / "prompts"

    for test_id, test_name, tier, prompt_file in test_cases:
        prompt_path = prompts_dir / prompt_file

        if not prompt_path.exists():
            print(f"⚠ Warning: Prompt file not found: {prompt_path}")
            print(f"   Skipping {test_id}")
            continue

        prompt = prompt_path.read_text()
        await comparison.run_test_case(test_id, test_name, tier, prompt)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = kimi_model.replace("-", "_")
    output_file = f"tests/comparison/results/comparison_{model_name}_{timestamp}.json"
    comparison.save_results(output_file)

    return comparison


def print_summary(results_file: str):
    """Print summary of test results."""
    data = json.loads(Path(results_file).read_text())

    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}\n")

    print(f"Timestamp: {data['metadata']['timestamp']}")
    print(f"Kimi Model: {data['metadata']['kimi_model']}")
    print(f"Opus Model: {data['metadata']['opus_model']}")
    print(f"Test Count: {data['metadata']['test_count']}")

    print(f"\n{'Test Case':<10} {'Name':<40} {'Tier':<6} {'Opus (s)':<12} {'Kimi (s)':<12} {'Opus Tok':<12} {'Kimi Tok':<12}")
    print("-" * 120)

    total_opus_time = 0
    total_kimi_time = 0
    total_opus_tokens = 0
    total_kimi_tokens = 0

    for result in data['results']:
        opus_time = result['opus']['time_seconds']
        kimi_time = result['kimi']['time_seconds']
        opus_tokens = result['opus']['tokens']['total']
        kimi_tokens = result['kimi']['tokens']['total']

        total_opus_time += opus_time
        total_kimi_time += kimi_time
        total_opus_tokens += opus_tokens
        total_kimi_tokens += kimi_tokens

        print(f"{result['test_case_id']:<10} {result['test_case_name']:<40} {result['tier']:<6} "
              f"{opus_time:<12.1f} {kimi_time:<12.1f} {opus_tokens:<12,} {kimi_tokens:<12,}")

    print("-" * 120)
    print(f"{'TOTALS':<10} {'':<40} {'':<6} {total_opus_time:<12.1f} {total_kimi_time:<12.1f} "
          f"{total_opus_tokens:<12,} {total_kimi_tokens:<12,}")

    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print(f"{'='*80}\n")
    print("1. Review responses in the JSON file")
    print("2. Score each response using the rubrics (quality, reasoning, actionability)")
    print("3. Run analysis script: python tests/comparison/analyze_results.py")
    print(f"\nResults file: {results_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Kimi vs Opus 4.5 comparison tests")
    parser.add_argument(
        "--model",
        default="kimi-k2-thinking-turbo",
        choices=["kimi-k2-thinking-turbo", "kimi-k2-thinking"],
        help="Kimi model to test"
    )
    parser.add_argument(
        "--summary",
        help="Path to results file to print summary"
    )

    args = parser.parse_args()

    if args.summary:
        print_summary(args.summary)
    else:
        comparison = asyncio.run(run_all_tests(args.model))
        # Summary is printed automatically by save_results
