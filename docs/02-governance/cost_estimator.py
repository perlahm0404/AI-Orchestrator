"""
Cost Estimator for AI Team Orchestration
Version: 1.0
Part of: ADR-004 Resource Protection / Cost Guardian System

Provides rough cost estimates for cloud operations and AI API usage.
All costs are conservative estimates in USD.
"""

from dataclasses import dataclass
from typing import Dict, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# COST CONSTANTS (USD)
# ═══════════════════════════════════════════════════════════════════════════════

# AWS Lambda costs (us-east-1 pricing)
LAMBDA_INVOKE_COST = 0.0000002      # Per invocation (first 1M free)
LAMBDA_DURATION_COST = 0.0000166667 # Per GB-second
LAMBDA_DEPLOY_COST = 0.01           # Rough estimate per deployment

# AWS API Gateway
API_GATEWAY_COST = 0.0000035        # Per request

# AWS S3
S3_PUT_COST = 0.000005              # Per PUT request
S3_GET_COST = 0.0000004             # Per GET request
S3_STORAGE_COST = 0.023             # Per GB-month

# Claude API (Anthropic pricing as of 2024)
CLAUDE_SONNET_INPUT = 0.000003      # Per token (input)
CLAUDE_SONNET_OUTPUT = 0.000015     # Per token (output)
CLAUDE_HAIKU_INPUT = 0.00000025     # Per token (input)
CLAUDE_HAIKU_OUTPUT = 0.00000125    # Per token (output)
CLAUDE_OPUS_INPUT = 0.000015        # Per token (input)
CLAUDE_OPUS_OUTPUT = 0.000075       # Per token (output)

# Git operations (GitHub API)
GITHUB_API_COST = 0.0               # Free tier typically sufficient

# NPM operations
NPM_INSTALL_COST = 0.0              # Free but costs compute time


# ═══════════════════════════════════════════════════════════════════════════════
# COST PROFILES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IterationProfile:
    """Typical resource usage for one agent iteration."""
    input_tokens: int = 2000        # Prompt + context
    output_tokens: int = 500        # Response
    api_calls: int = 1              # Claude API calls
    file_reads: int = 3             # Files read
    file_writes: int = 1            # Files written
    bash_commands: int = 2          # Shell commands


@dataclass
class DeployProfile:
    """Typical resource usage for one Lambda deployment."""
    s3_puts: int = 10               # Upload artifacts
    lambda_updates: int = 1         # Lambda update
    api_gateway_updates: int = 1    # API Gateway config


# ═══════════════════════════════════════════════════════════════════════════════
# COST ESTIMATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def estimate_iteration_cost(
    model: str = "sonnet",
    profile: Optional[IterationProfile] = None,
) -> float:
    """
    Estimate cost of one agent iteration.

    Args:
        model: Claude model ("sonnet", "haiku", "opus")
        profile: Custom iteration profile (uses default if None)

    Returns:
        Estimated cost in USD

    Example:
        >>> estimate_iteration_cost()
        0.0135  # ~$0.01-0.02 per iteration with Sonnet
    """
    if profile is None:
        profile = IterationProfile()

    # Select model pricing
    if model == "haiku":
        input_cost = CLAUDE_HAIKU_INPUT
        output_cost = CLAUDE_HAIKU_OUTPUT
    elif model == "opus":
        input_cost = CLAUDE_OPUS_INPUT
        output_cost = CLAUDE_OPUS_OUTPUT
    else:  # sonnet (default)
        input_cost = CLAUDE_SONNET_INPUT
        output_cost = CLAUDE_SONNET_OUTPUT

    # Calculate costs
    token_cost = (
        profile.input_tokens * input_cost +
        profile.output_tokens * output_cost
    )

    return token_cost


def estimate_deploy_cost(
    profile: Optional[DeployProfile] = None,
) -> float:
    """
    Estimate cost of one Lambda deployment.

    Args:
        profile: Custom deploy profile (uses default if None)

    Returns:
        Estimated cost in USD

    Example:
        >>> estimate_deploy_cost()
        0.01005  # ~$0.01 per deployment
    """
    if profile is None:
        profile = DeployProfile()

    cost = (
        LAMBDA_DEPLOY_COST +
        profile.s3_puts * S3_PUT_COST +
        profile.api_gateway_updates * API_GATEWAY_COST
    )

    return cost


def estimate_session_cost(
    iterations: int,
    deploys: int = 0,
    model: str = "sonnet",
) -> float:
    """
    Estimate total cost for a session.

    Args:
        iterations: Number of agent iterations
        deploys: Number of Lambda deployments
        model: Claude model used

    Returns:
        Estimated total cost in USD

    Example:
        >>> estimate_session_cost(iterations=100, deploys=5)
        1.40  # 100 iterations + 5 deploys
    """
    iteration_cost = estimate_iteration_cost(model=model) * iterations
    deploy_cost = estimate_deploy_cost() * deploys

    return iteration_cost + deploy_cost


def estimate_daily_budget(
    max_cost_usd: float = 50.0,
    model: str = "sonnet",
) -> Dict[str, int]:
    """
    Calculate how many operations fit within a daily budget.

    Args:
        max_cost_usd: Maximum daily budget in USD
        model: Claude model used

    Returns:
        Dictionary with operation counts

    Example:
        >>> estimate_daily_budget(max_cost_usd=50.0)
        {'iterations': 3703, 'deploys': 4975}
    """
    iteration_cost = estimate_iteration_cost(model=model)
    deploy_cost = estimate_deploy_cost()

    return {
        "iterations": int(max_cost_usd / iteration_cost) if iteration_cost > 0 else 999999,
        "deploys": int(max_cost_usd / deploy_cost) if deploy_cost > 0 else 999999,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COST TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

class CostTracker:
    """
    Tracks accumulated costs during a session.

    Usage:
        tracker = CostTracker(budget_usd=50.0)
        tracker.record_iteration()
        if tracker.is_over_budget():
            # Stop operations
    """

    def __init__(
        self,
        budget_usd: float = 50.0,
        model: str = "sonnet",
    ):
        self.budget_usd = budget_usd
        self.model = model
        self.total_cost = 0.0
        self.iterations = 0
        self.deploys = 0
        self.custom_costs: Dict[str, float] = {}

    def record_iteration(self, count: int = 1) -> float:
        """Record iteration(s) and return new total cost."""
        cost = estimate_iteration_cost(model=self.model) * count
        self.total_cost += cost
        self.iterations += count
        return self.total_cost

    def record_deploy(self, count: int = 1) -> float:
        """Record deployment(s) and return new total cost."""
        cost = estimate_deploy_cost() * count
        self.total_cost += cost
        self.deploys += count
        return self.total_cost

    def record_custom(self, operation: str, cost: float) -> float:
        """Record custom operation cost."""
        self.total_cost += cost
        self.custom_costs[operation] = self.custom_costs.get(operation, 0) + cost
        return self.total_cost

    def is_over_budget(self) -> bool:
        """Check if over budget."""
        return self.total_cost >= self.budget_usd

    def budget_remaining(self) -> float:
        """Get remaining budget."""
        return max(0, self.budget_usd - self.total_cost)

    def budget_used_pct(self) -> float:
        """Get percentage of budget used."""
        if self.budget_usd <= 0:
            return 100.0
        return (self.total_cost / self.budget_usd) * 100

    def get_summary(self) -> Dict:
        """Get cost tracking summary."""
        return {
            "total_cost_usd": round(self.total_cost, 4),
            "budget_usd": self.budget_usd,
            "budget_remaining_usd": round(self.budget_remaining(), 4),
            "budget_used_pct": round(self.budget_used_pct(), 1),
            "iterations": self.iterations,
            "deploys": self.deploys,
            "custom_costs": self.custom_costs,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COST FORMATTERS
# ═══════════════════════════════════════════════════════════════════════════════

def format_cost(cost_usd: float) -> str:
    """Format cost for display."""
    if cost_usd < 0.01:
        return f"${cost_usd:.4f}"
    elif cost_usd < 1.0:
        return f"${cost_usd:.3f}"
    else:
        return f"${cost_usd:.2f}"


def format_cost_summary(tracker: CostTracker) -> str:
    """Format cost tracker summary for display."""
    summary = tracker.get_summary()
    lines = [
        f"Cost Summary:",
        f"  Total: {format_cost(summary['total_cost_usd'])} / {format_cost(summary['budget_usd'])}",
        f"  Budget Used: {summary['budget_used_pct']}%",
        f"  Remaining: {format_cost(summary['budget_remaining_usd'])}",
        f"  Iterations: {summary['iterations']}",
        f"  Deploys: {summary['deploys']}",
    ]

    if summary['custom_costs']:
        lines.append("  Custom Costs:")
        for op, cost in summary['custom_costs'].items():
            lines.append(f"    {op}: {format_cost(cost)}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Cost Estimation Examples:")
    print("=" * 50)

    # Per-operation costs
    print(f"\nPer-Operation Costs:")
    print(f"  Iteration (Sonnet): {format_cost(estimate_iteration_cost('sonnet'))}")
    print(f"  Iteration (Haiku):  {format_cost(estimate_iteration_cost('haiku'))}")
    print(f"  Iteration (Opus):   {format_cost(estimate_iteration_cost('opus'))}")
    print(f"  Lambda Deploy:      {format_cost(estimate_deploy_cost())}")

    # Session estimates
    print(f"\nSession Estimates:")
    print(f"  100 iterations:     {format_cost(estimate_session_cost(100))}")
    print(f"  500 iterations:     {format_cost(estimate_session_cost(500))}")
    print(f"  100 iter + 5 deploy:{format_cost(estimate_session_cost(100, 5))}")

    # Budget calculations
    print(f"\nDaily Budget ($50):")
    budget = estimate_daily_budget(50.0)
    print(f"  Max iterations: {budget['iterations']:,}")
    print(f"  Max deploys:    {budget['deploys']:,}")

    # Tracker demo
    print(f"\nCostTracker Demo:")
    tracker = CostTracker(budget_usd=10.0)
    tracker.record_iteration(50)
    tracker.record_deploy(2)
    print(format_cost_summary(tracker))
