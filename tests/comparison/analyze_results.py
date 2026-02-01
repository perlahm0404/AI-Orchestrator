"""
Analyze Kimi vs Opus 4.5 comparison results.

Usage:
    python tests/comparison/analyze_results.py results/comparison_kimi_k2_thinking_turbo_20260129_143022.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import statistics


def load_results(path: str) -> Dict[str, Any]:
    """Load results from JSON file."""
    return json.loads(Path(path).read_text())


def validate_scoring(results: List[Dict[str, Any]]) -> bool:
    """Check if all results have been manually scored."""
    for result in results:
        opus_scores = result['opus']['scores']
        kimi_scores = result['kimi']['scores']

        if None in [opus_scores['quality'], opus_scores['reasoning'], opus_scores['actionability']]:
            return False
        if None in [kimi_scores['quality'], kimi_scores['reasoning'], kimi_scores['actionability']]:
            return False

    return True


def calculate_aggregate_scores(results: List[Dict[str, Any]], model: str) -> Dict[str, float]:
    """Calculate aggregate scores for a model."""
    quality_scores = [r[model]['scores']['quality'] for r in results]
    reasoning_scores = [r[model]['scores']['reasoning'] for r in results]
    actionability_scores = [r[model]['scores']['actionability'] for r in results]

    return {
        'quality_avg': statistics.mean(quality_scores),
        'quality_stdev': statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
        'reasoning_avg': statistics.mean(reasoning_scores),
        'reasoning_stdev': statistics.stdev(reasoning_scores) if len(reasoning_scores) > 1 else 0,
        'actionability_avg': statistics.mean(actionability_scores),
        'actionability_stdev': statistics.stdev(actionability_scores) if len(actionability_scores) > 1 else 0,
        'overall_avg': statistics.mean(quality_scores + reasoning_scores + actionability_scores),
    }


def calculate_tier_scores(results: List[Dict[str, Any]], tier: int, model: str) -> Dict[str, float]:
    """Calculate scores for a specific tier."""
    tier_results = [r for r in results if r['tier'] == tier]

    if not tier_results:
        return {}

    quality_scores = [r[model]['scores']['quality'] for r in tier_results]
    reasoning_scores = [r[model]['scores']['reasoning'] for r in tier_results]
    actionability_scores = [r[model]['scores']['actionability'] for r in tier_results]

    return {
        'quality_avg': statistics.mean(quality_scores),
        'reasoning_avg': statistics.mean(reasoning_scores),
        'actionability_avg': statistics.mean(actionability_scores),
        'overall_avg': statistics.mean(quality_scores + reasoning_scores + actionability_scores),
    }


def calculate_comparison_ratios(opus_scores: Dict[str, float], kimi_scores: Dict[str, float]) -> Dict[str, float]:
    """Calculate Kimi/Opus ratios."""
    return {
        'quality_ratio': kimi_scores['quality_avg'] / opus_scores['quality_avg'],
        'reasoning_ratio': kimi_scores['reasoning_avg'] / opus_scores['reasoning_avg'],
        'actionability_ratio': kimi_scores['actionability_avg'] / opus_scores['actionability_avg'],
        'overall_ratio': kimi_scores['overall_avg'] / opus_scores['overall_avg'],
    }


def calculate_cost_efficiency(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate cost per quality point."""
    # Pricing (conservative estimates)
    OPUS_INPUT_PRICE = 15.00 / 1_000_000  # $15/MTok
    OPUS_OUTPUT_PRICE = 75.00 / 1_000_000  # $75/MTok
    KIMI_THINKING_TURBO_INPUT = 4.00 / 1_000_000  # $4/MTok (estimated)
    KIMI_THINKING_TURBO_OUTPUT = 12.00 / 1_000_000  # $12/MTok (estimated)

    opus_cost = 0
    kimi_cost = 0
    opus_quality_sum = 0
    kimi_quality_sum = 0

    for result in results:
        opus_tokens = result['opus']['tokens']
        kimi_tokens = result['kimi']['tokens']

        opus_cost += (opus_tokens['input'] * OPUS_INPUT_PRICE +
                      opus_tokens['output'] * OPUS_OUTPUT_PRICE)
        kimi_cost += (kimi_tokens['input'] * KIMI_THINKING_TURBO_INPUT +
                      kimi_tokens['output'] * KIMI_THINKING_TURBO_OUTPUT)

        opus_quality_sum += result['opus']['scores']['quality']
        kimi_quality_sum += result['kimi']['scores']['quality']

    return {
        'opus_total_cost': opus_cost,
        'kimi_total_cost': kimi_cost,
        'opus_cost_per_quality': opus_cost / opus_quality_sum if opus_quality_sum > 0 else 0,
        'kimi_cost_per_quality': kimi_cost / kimi_quality_sum if kimi_quality_sum > 0 else 0,
        'cost_savings_ratio': opus_cost / kimi_cost if kimi_cost > 0 else 0,
    }


def calculate_speed_efficiency(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate speed metrics."""
    opus_times = [r['opus']['time_seconds'] for r in results]
    kimi_times = [r['kimi']['time_seconds'] for r in results]

    opus_quality_sum = sum(r['opus']['scores']['quality'] for r in results)
    kimi_quality_sum = sum(r['kimi']['scores']['quality'] for r in results)

    return {
        'opus_avg_time': statistics.mean(opus_times),
        'kimi_avg_time': statistics.mean(kimi_times),
        'opus_quality_per_second': opus_quality_sum / sum(opus_times) if sum(opus_times) > 0 else 0,
        'kimi_quality_per_second': kimi_quality_sum / sum(kimi_times) if sum(kimi_times) > 0 else 0,
        'speed_ratio': statistics.mean(opus_times) / statistics.mean(kimi_times) if statistics.mean(kimi_times) > 0 else 0,
    }


def calculate_win_lose_tie(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate win/lose/tie breakdown."""
    wins = 0
    losses = 0
    ties = 0

    for result in results:
        opus_overall = (result['opus']['scores']['quality'] +
                        result['opus']['scores']['reasoning'] +
                        result['opus']['scores']['actionability']) / 3
        kimi_overall = (result['kimi']['scores']['quality'] +
                        result['kimi']['scores']['reasoning'] +
                        result['kimi']['scores']['actionability']) / 3

        diff = kimi_overall - opus_overall

        if diff > 0.5:
            wins += 1
        elif diff < -0.5:
            losses += 1
        else:
            ties += 1

    return {
        'wins': wins,
        'losses': losses,
        'ties': ties,
    }


def check_success_criteria(opus_scores: Dict[str, float], kimi_scores: Dict[str, float],
                            tier_results: Dict[int, Dict[str, float]]) -> Dict[str, bool]:
    """Check if success criteria are met."""
    ratios = calculate_comparison_ratios(opus_scores, kimi_scores)

    # Overall performance (must be ≥95%)
    overall_pass = ratios['overall_ratio'] >= 0.95

    # Per-dimension (must be ≥95%)
    quality_pass = ratios['quality_ratio'] >= 0.95
    reasoning_pass = ratios['reasoning_ratio'] >= 0.95
    actionability_pass = ratios['actionability_ratio'] >= 0.95

    # Tier-specific (Tier 1: ≥90%, Tier 2: ≥95%, Tier 3: ≥90%)
    tier1_pass = tier_results.get(1, {}).get('kimi_ratio', 0) >= 0.90 if 1 in tier_results else True
    tier2_pass = tier_results.get(2, {}).get('kimi_ratio', 0) >= 0.95 if 2 in tier_results else True
    tier3_pass = tier_results.get(3, {}).get('kimi_ratio', 0) >= 0.90 if 3 in tier_results else True

    return {
        'overall_performance': overall_pass,
        'quality_dimension': quality_pass,
        'reasoning_dimension': reasoning_pass,
        'actionability_dimension': actionability_pass,
        'tier1_performance': tier1_pass,
        'tier2_performance': tier2_pass,
        'tier3_performance': tier3_pass,
        'all_criteria_met': all([overall_pass, quality_pass, reasoning_pass,
                                  actionability_pass, tier1_pass, tier2_pass, tier3_pass]),
    }


def print_report(data: Dict[str, Any]):
    """Print comprehensive analysis report."""
    results = data['results']
    metadata = data['metadata']

    print(f"\n{'='*100}")
    print("KIMI VS OPUS 4.5 COMPARISON REPORT")
    print(f"{'='*100}\n")

    print(f"Timestamp: {metadata['timestamp']}")
    print(f"Kimi Model: {metadata['kimi_model']}")
    print(f"Opus Model: {metadata['opus_model']}")
    print(f"Test Count: {metadata['test_count']}")

    # Check if scoring is complete
    if not validate_scoring(results):
        print("\n⚠ WARNING: Not all results have been manually scored!")
        print("Please score all responses before running analysis.")
        return

    # Aggregate scores
    opus_scores = calculate_aggregate_scores(results, 'opus')
    kimi_scores = calculate_aggregate_scores(results, 'kimi')
    ratios = calculate_comparison_ratios(opus_scores, kimi_scores)

    print(f"\n{'='*100}")
    print("AGGREGATE SCORES")
    print(f"{'='*100}\n")

    print(f"{'Dimension':<20} {'Opus':<15} {'Kimi':<15} {'Ratio':<15} {'Status':<15}")
    print("-" * 100)

    print(f"{'Quality':<20} {opus_scores['quality_avg']:<15.2f} {kimi_scores['quality_avg']:<15.2f} "
          f"{ratios['quality_ratio']:<15.2%} {'✓ PASS' if ratios['quality_ratio'] >= 0.95 else '✗ FAIL'}")

    print(f"{'Reasoning':<20} {opus_scores['reasoning_avg']:<15.2f} {kimi_scores['reasoning_avg']:<15.2f} "
          f"{ratios['reasoning_ratio']:<15.2%} {'✓ PASS' if ratios['reasoning_ratio'] >= 0.95 else '✗ FAIL'}")

    print(f"{'Actionability':<20} {opus_scores['actionability_avg']:<15.2f} {kimi_scores['actionability_avg']:<15.2f} "
          f"{ratios['actionability_ratio']:<15.2%} {'✓ PASS' if ratios['actionability_ratio'] >= 0.95 else '✗ FAIL'}")

    print("-" * 100)
    print(f"{'OVERALL':<20} {opus_scores['overall_avg']:<15.2f} {kimi_scores['overall_avg']:<15.2f} "
          f"{ratios['overall_ratio']:<15.2%} {'✓ PASS' if ratios['overall_ratio'] >= 0.95 else '✗ FAIL'}")

    # Per-tier performance
    print(f"\n{'='*100}")
    print("PER-TIER PERFORMANCE")
    print(f"{'='*100}\n")

    tier_results = {}
    for tier in [1, 2, 3]:
        opus_tier = calculate_tier_scores(results, tier, 'opus')
        kimi_tier = calculate_tier_scores(results, tier, 'kimi')

        if opus_tier and kimi_tier:
            tier_ratio = kimi_tier['overall_avg'] / opus_tier['overall_avg']
            tier_results[tier] = {'kimi_ratio': tier_ratio}

            threshold = 0.90 if tier in [1, 3] else 0.95
            status = '✓ PASS' if tier_ratio >= threshold else '✗ FAIL'

            print(f"Tier {tier}: Opus={opus_tier['overall_avg']:.2f}, Kimi={kimi_tier['overall_avg']:.2f}, "
                  f"Ratio={tier_ratio:.2%} (threshold: {threshold:.0%}) {status}")

    # Critical test cases
    print(f"\n{'='*100}")
    print("CRITICAL TEST CASES")
    print(f"{'='*100}\n")

    critical_cases = ['TC4', 'TC5']
    for result in results:
        if result['test_case_id'] in critical_cases:
            opus_avg = (result['opus']['scores']['quality'] +
                        result['opus']['scores']['reasoning'] +
                        result['opus']['scores']['actionability']) / 3
            kimi_avg = (result['kimi']['scores']['quality'] +
                        result['kimi']['scores']['reasoning'] +
                        result['kimi']['scores']['actionability']) / 3

            ratio = kimi_avg / opus_avg
            status = '✓ PASS' if ratio >= 0.95 else '✗ FAIL'

            print(f"{result['test_case_id']} ({result['test_case_name']}): "
                  f"Opus={opus_avg:.2f}, Kimi={kimi_avg:.2f}, Ratio={ratio:.2%} {status}")

    # Win/Lose/Tie
    wlt = calculate_win_lose_tie(results)
    print(f"\n{'='*100}")
    print("WIN/LOSE/TIE BREAKDOWN")
    print(f"{'='*100}\n")
    print(f"Kimi Wins: {wlt['wins']} ({wlt['wins']/len(results):.1%})")
    print(f"Ties: {wlt['ties']} ({wlt['ties']/len(results):.1%})")
    print(f"Kimi Losses: {wlt['losses']} ({wlt['losses']/len(results):.1%})")

    # Cost efficiency
    cost_metrics = calculate_cost_efficiency(results)
    print(f"\n{'='*100}")
    print("COST EFFICIENCY")
    print(f"{'='*100}\n")
    print(f"Opus Total Cost: ${cost_metrics['opus_total_cost']:.4f}")
    print(f"Kimi Total Cost: ${cost_metrics['kimi_total_cost']:.4f}")
    print(f"Cost Savings: {(1 - cost_metrics['kimi_total_cost']/cost_metrics['opus_total_cost'])*100:.1f}%")
    print(f"Opus Cost per Quality Point: ${cost_metrics['opus_cost_per_quality']:.6f}")
    print(f"Kimi Cost per Quality Point: ${cost_metrics['kimi_cost_per_quality']:.6f}")

    # Speed efficiency
    speed_metrics = calculate_speed_efficiency(results)
    print(f"\n{'='*100}")
    print("SPEED EFFICIENCY")
    print(f"{'='*100}\n")
    print(f"Opus Avg Time: {speed_metrics['opus_avg_time']:.1f}s")
    print(f"Kimi Avg Time: {speed_metrics['kimi_avg_time']:.1f}s")
    print(f"Speed Ratio: {speed_metrics['speed_ratio']:.2f}x {'(Kimi faster)' if speed_metrics['speed_ratio'] > 1 else '(Opus faster)'}")

    # Success criteria
    success = check_success_criteria(opus_scores, kimi_scores, tier_results)
    print(f"\n{'='*100}")
    print("SUCCESS CRITERIA")
    print(f"{'='*100}\n")

    for criterion, passed in success.items():
        if criterion == 'all_criteria_met':
            continue
        status = '✓ PASS' if passed else '✗ FAIL'
        print(f"{criterion.replace('_', ' ').title():<30} {status}")

    print("-" * 100)
    print(f"{'ALL CRITERIA MET':<30} {'✓ PASS' if success['all_criteria_met'] else '✗ FAIL'}")

    # Final recommendation
    print(f"\n{'='*100}")
    print("RECOMMENDATION")
    print(f"{'='*100}\n")

    if success['all_criteria_met']:
        print("✓ ADOPT Kimi thinking models for reasoning tasks")
        print("\nNext Steps:")
        print("1. Implement full KimiProvider class")
        print("2. Add to factory with intelligent routing")
        print("3. Update governance contracts")
        print("4. Start Phase 2 pilot (ProductManagerAgent)")
    elif ratios['overall_ratio'] >= 0.90:
        print("⚠ CONDITIONAL ADOPTION")
        print("\nNext Steps:")
        print("1. Identify specific gaps (review failed test cases)")
        print("2. Determine if gaps are acceptable for specific use cases")
        print("3. Adopt for low-risk reasoning tasks only")
        print("4. Continue monitoring performance")
    else:
        print("✗ REJECT for now, revisit later")
        print("\nNext Steps:")
        print("1. Document specific failure modes")
        print("2. Provide feedback to Moonshot AI")
        print("3. Test fallback models (kimi-k2.5, kimi-turbo)")
        print("4. Re-evaluate in 3-6 months")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <results_file.json>")
        sys.exit(1)

    results_file = sys.argv[1]

    if not Path(results_file).exists():
        print(f"Error: File not found: {results_file}")
        sys.exit(1)

    data = load_results(results_file)
    print_report(data)
