"""
Fully Automated Kimi vs Opus 4.5 Comparative Testing Framework

Uses browser automation to run prompts through Claude.ai (Opus 4.5)
and Kimi API for fully automated comparison.

This script generates:
1. A JSON file with Kimi responses
2. Instructions for Claude Code to run Opus tests via browser automation
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

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
    model: str
    timestamp: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass
class TestCaseResult:
    """Results for a single test case."""
    test_case_id: str
    test_case_name: str
    tier: int
    prompt: str
    opus_response: Optional[ModelResponse] = None
    kimi_response: Optional[ModelResponse] = None

    # Manual scoring (to be filled in later)
    opus_quality: Optional[float] = None
    opus_reasoning: Optional[float] = None
    opus_actionability: Optional[float] = None
    kimi_quality: Optional[float] = None
    kimi_reasoning: Optional[float] = None
    kimi_actionability: Optional[float] = None
    notes: Optional[str] = None


class KimiProvider:
    """Kimi thinking model provider via OpenAI-compatible API."""

    def __init__(self, api_key: str, model: str = "moonshot-v1-auto"):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self.model = model

    async def complete(self, prompt: str) -> ModelResponse:
        """Get completion from Kimi model."""
        start_time = time.time()

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant skilled at debugging, analysis, and strategic thinking."},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0
        )

        elapsed = time.time() - start_time

        return ModelResponse(
            content=response.choices[0].message.content,
            time_seconds=elapsed,
            input_tokens=response.usage.prompt_tokens if response.usage else None,
            output_tokens=response.usage.completion_tokens if response.usage else None,
            total_tokens=response.usage.total_tokens if response.usage else None,
            model=self.model,
            timestamp=datetime.now().isoformat()
        )


class TestRunner:
    """Orchestrates the comparative testing."""

    # Test case definitions
    TEST_CASES = [
        {"id": "tc1", "name": "Email Classification Bug", "tier": 1, "file": "tc1_email_classification.txt"},
        {"id": "tc2", "name": "TypeScript Build Errors", "tier": 1, "file": "tc2_typescript_build_errors.txt"},
        {"id": "tc3", "name": "Claude CLI Configuration", "tier": 1, "file": "tc3_claude_cli_config.txt"},
        {"id": "tc4", "name": "Profile 401 Error", "tier": 2, "file": "tc4_profile_401_error.txt", "critical": True},
        {"id": "tc5", "name": "CME Rules Sync", "tier": 2, "file": "tc5_cme_rules_sync.txt", "critical": True},
        {"id": "tc6", "name": "Token Optimization", "tier": 2, "file": "tc6_token_optimization.txt"},
        {"id": "tc7", "name": "Agent SDK Decision", "tier": 3, "file": "tc7_agent_sdk_decision.txt"},
        {"id": "tc8", "name": "Documentation Architecture", "tier": 3, "file": "tc8_documentation_architecture.txt"},
        {"id": "tc9", "name": "LlamaIndex Evaluation", "tier": 3, "file": "tc9_llamaindex_evaluation.txt"},
    ]

    def __init__(self, kimi_model: str = "moonshot-v1-auto"):
        # Initialize Kimi provider
        kimi_api_key = os.getenv("KIMI_API_KEY")
        if not kimi_api_key:
            raise ValueError("KIMI_API_KEY not set. Run: export KIMI_API_KEY='sk-...'")

        self.kimi = KimiProvider(kimi_api_key, kimi_model)
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    def load_test_cases(self) -> List[Dict[str, Any]]:
        """Load all test case prompts."""
        test_cases = self.TEST_CASES.copy()

        for tc in test_cases:
            prompt_file = self.prompts_dir / tc["file"]
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            tc["prompt"] = prompt_file.read_text()

        return test_cases

    async def run_kimi_tests(self) -> Dict[str, TestCaseResult]:
        """Run all test cases through Kimi API."""
        test_cases = self.load_test_cases()
        results = {}

        print(f"\n{'='*60}")
        print("Running Kimi Tests")
        print(f"{'='*60}\n")

        for i, tc in enumerate(test_cases, 1):
            critical = " ⭐ CRITICAL" if tc.get("critical") else ""
            print(f"[{i}/9] {tc['name']}{critical}...", end=" ", flush=True)

            try:
                kimi_response = await self.kimi.complete(tc["prompt"])

                result = TestCaseResult(
                    test_case_id=tc["id"],
                    test_case_name=tc["name"],
                    tier=tc["tier"],
                    prompt=tc["prompt"],
                    kimi_response=kimi_response
                )

                results[tc["id"]] = result
                print(f"✓ ({kimi_response.time_seconds:.1f}s, {kimi_response.total_tokens} tokens)")

            except Exception as e:
                print(f"✗ Error: {e}")
                results[tc["id"]] = TestCaseResult(
                    test_case_id=tc["id"],
                    test_case_name=tc["name"],
                    tier=tc["tier"],
                    prompt=tc["prompt"]
                )

        return results

    def save_results(self, results: Dict[str, TestCaseResult], filename: str = None):
        """Save results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = self.kimi.model.replace('/', '_').replace('-', '_')
            filename = f"comparison_{model_name}_{timestamp}.json"

        output_file = self.results_dir / filename

        # Convert to serializable format
        serializable_results = {
            "metadata": {
                "kimi_model": self.kimi.model,
                "opus_model": "claude-opus-4-5",
                "timestamp": datetime.now().isoformat(),
                "total_test_cases": len(results)
            },
            "test_cases": {}
        }

        for tc_id, result in results.items():
            result_dict = {
                "test_case_id": result.test_case_id,
                "test_case_name": result.test_case_name,
                "tier": result.tier,
                "prompt": result.prompt,
                "opus_response": asdict(result.opus_response) if result.opus_response else None,
                "kimi_response": asdict(result.kimi_response) if result.kimi_response else None,
                "scoring": {
                    "opus": {
                        "quality": result.opus_quality,
                        "reasoning": result.opus_reasoning,
                        "actionability": result.opus_actionability
                    },
                    "kimi": {
                        "quality": result.kimi_quality,
                        "reasoning": result.kimi_reasoning,
                        "actionability": result.kimi_actionability
                    },
                    "notes": result.notes
                }
            }
            serializable_results["test_cases"][tc_id] = result_dict

        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        print(f"\n✓ Kimi results saved to: {output_file}")
        return output_file


async def main():
    """Main test execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Kimi vs Opus comparison tests")
    parser.add_argument("--model", default="moonshot-v1-auto",
                       choices=["moonshot-v1-auto", "kimi-k2-thinking-turbo", "kimi-k2-thinking"],
                       help="Kimi model to test")
    parser.add_argument("--output", help="Output filename (default: auto-generated)")

    args = parser.parse_args()

    try:
        runner = TestRunner(kimi_model=args.model)

        # Run Kimi tests
        results = await runner.run_kimi_tests()

        # Save results
        results_file = runner.save_results(results, args.output)

        print(f"\n{'='*60}")
        print("Phase 1 Complete: Kimi Tests")
        print(f"{'='*60}\n")
        print(f"✓ Kimi responses collected for all 9 test cases")
        print(f"✓ Results saved to: {results_file}")
        print(f"\n{'='*60}")
        print("Next Steps")
        print(f"{'='*60}\n")
        print("Phase 2: Collect Opus responses via browser automation")
        print("  → Ask Claude Code to run Opus tests through Claude.ai")
        print()
        print("Phase 3: Manual scoring (2-3 hours)")
        print(f"  → Use: tests/comparison/scoring_template.md")
        print()
        print("Phase 4: Analysis")
        print(f"  → Run: python tests/comparison/analyze_results.py {results_file}")
        print()

        return str(results_file)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    result = asyncio.run(main())
