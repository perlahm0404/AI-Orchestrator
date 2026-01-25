"""
Token Budget Enforcement

Tracks and enforces token budgets for agent sessions.
Prevents context overflow and optimizes token usage.

Key Features:
- Hard limits with early warning
- Per-component tracking (governance, context, response)
- Automatic compression triggers
- Real-time budget monitoring

Target from existing metrics:
- Governance context: 2000 tokens
- Total session: 50000 tokens

Usage:
    from governance.token_budget import TokenBudget, TokenBudgetEnforcer

    # Create budget
    budget = TokenBudget(
        governance_limit=2000,
        total_limit=50000
    )

    # Create enforcer
    enforcer = TokenBudgetEnforcer(budget)

    # Check if context fits
    if enforcer.can_add_context(context_tokens=500):
        # Add context
        enforcer.add_context(500)
    else:
        # Compress or skip
        compressed = enforcer.compress_context(original_context)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import json


@dataclass
class TokenBudget:
    """
    Token budget for an agent session.

    Defines limits and tracks current usage.
    """
    # Limits
    governance_limit: int = 2000  # Target from existing metrics
    context_limit: int = 10000   # Additional context (files, KOs)
    response_limit: int = 8000   # Max expected response
    total_limit: int = 50000     # Total session budget

    # Current usage
    current_governance: int = 0
    current_context: int = 0
    current_response: int = 0
    current_total: int = 0

    # Warning thresholds (percentage of limit)
    warning_threshold: float = 0.8

    @property
    def governance_remaining(self) -> int:
        """Remaining governance tokens."""
        return max(0, self.governance_limit - self.current_governance)

    @property
    def context_remaining(self) -> int:
        """Remaining context tokens."""
        return max(0, self.context_limit - self.current_context)

    @property
    def total_remaining(self) -> int:
        """Remaining total tokens."""
        return max(0, self.total_limit - self.current_total)

    @property
    def is_over_budget(self) -> bool:
        """Check if any budget is exceeded."""
        return (
            self.current_governance > self.governance_limit or
            self.current_context > self.context_limit or
            self.current_total > self.total_limit
        )

    @property
    def is_warning(self) -> bool:
        """Check if approaching budget limits."""
        return (
            self.current_governance > self.governance_limit * self.warning_threshold or
            self.current_total > self.total_limit * self.warning_threshold
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "limits": {
                "governance": self.governance_limit,
                "context": self.context_limit,
                "response": self.response_limit,
                "total": self.total_limit,
            },
            "current": {
                "governance": self.current_governance,
                "context": self.current_context,
                "response": self.current_response,
                "total": self.current_total,
            },
            "remaining": {
                "governance": self.governance_remaining,
                "context": self.context_remaining,
                "total": self.total_remaining,
            },
            "status": {
                "over_budget": self.is_over_budget,
                "warning": self.is_warning,
            },
        }


@dataclass
class BudgetEvent:
    """Event logged when budget changes."""
    timestamp: str
    event_type: str  # "add", "release", "warning", "exceeded"
    component: str   # "governance", "context", "response"
    tokens: int
    budget_after: Dict[str, int]


class TokenBudgetEnforcer:
    """
    Enforces token budgets with compression and prioritization.

    Features:
    - Real-time tracking
    - Automatic compression triggers
    - Priority-based context loading
    - Event logging for debugging
    """

    # Default priorities for governance context
    GOVERNANCE_PRIORITY = {
        "STATE.md": 1.0,        # Always load
        "CATALOG.md": 0.9,      # Usually load
        "DECISIONS.md": 0.7,    # Load for complex tasks
        "session_handoff": 0.8, # Load for continuity
        "hot_patterns": 0.6,    # Load if budget allows
    }

    def __init__(
        self,
        budget: Optional[TokenBudget] = None,
        estimator: Optional[Any] = None,  # TokenEstimator
    ):
        """
        Initialize enforcer.

        Args:
            budget: Token budget (uses defaults if None)
            estimator: Token estimator (creates default if None)
        """
        self.budget = budget or TokenBudget()
        self._events: List[BudgetEvent] = []

        if estimator is None:
            from .token_estimator import TokenEstimator
            self._estimator = TokenEstimator()
        else:
            self._estimator = estimator

    def can_add_governance(self, tokens: int) -> bool:
        """Check if governance tokens can be added within budget."""
        return self.budget.current_governance + tokens <= self.budget.governance_limit

    def can_add_context(self, tokens: int) -> bool:
        """Check if context tokens can be added within budget."""
        return (
            self.budget.current_context + tokens <= self.budget.context_limit and
            self.budget.current_total + tokens <= self.budget.total_limit
        )

    def add_governance(self, tokens: int, source: str = "unknown") -> bool:
        """
        Add governance tokens to budget.

        Args:
            tokens: Number of tokens
            source: Source of tokens (for logging)

        Returns:
            True if added successfully, False if would exceed budget
        """
        if not self.can_add_governance(tokens):
            self._log_event("exceeded", "governance", tokens)
            return False

        self.budget.current_governance += tokens
        self.budget.current_total += tokens
        self._log_event("add", "governance", tokens)

        if self.budget.is_warning:
            self._log_event("warning", "governance", tokens)

        return True

    def add_context(self, tokens: int, source: str = "unknown") -> bool:
        """
        Add context tokens to budget.

        Args:
            tokens: Number of tokens
            source: Source of tokens (for logging)

        Returns:
            True if added successfully
        """
        if not self.can_add_context(tokens):
            self._log_event("exceeded", "context", tokens)
            return False

        self.budget.current_context += tokens
        self.budget.current_total += tokens
        self._log_event("add", "context", tokens)

        return True

    def estimate_and_check_governance(self, content: str) -> bool:
        """
        Estimate tokens and check if content fits in governance budget.

        Args:
            content: Content to check

        Returns:
            True if content fits
        """
        tokens = self._estimator.estimate(content)
        return self.can_add_governance(tokens)

    def select_priority_context(
        self,
        available_files: Dict[str, str],
        task_type: Optional[str] = None
    ) -> List[str]:
        """
        Select context files based on priority and budget.

        Args:
            available_files: Map of filename -> content
            task_type: Optional task type for prioritization

        Returns:
            List of filenames to include, in priority order
        """
        # Calculate token cost for each file
        file_costs = {}
        for filename, content in available_files.items():
            file_costs[filename] = self._estimator.estimate(content)

        # Adjust priorities based on task type
        priorities = self.GOVERNANCE_PRIORITY.copy()
        if task_type in {"lint-fix", "format-fix", "simple-test-fix"}:
            # Skip DECISIONS.md for simple tasks
            priorities["DECISIONS.md"] = 0.0

        # Sort by priority
        sorted_files = sorted(
            available_files.keys(),
            key=lambda f: priorities.get(f, 0.5),
            reverse=True
        )

        # Select files that fit in budget
        selected = []
        remaining_budget = self.budget.governance_remaining

        for filename in sorted_files:
            cost = file_costs[filename]
            priority = priorities.get(filename, 0.5)

            # Skip low-priority files if budget is tight
            if priority < 0.5 and remaining_budget < self.budget.governance_limit * 0.3:
                continue

            if cost <= remaining_budget:
                selected.append(filename)
                remaining_budget -= cost

        return selected

    def compress_context(
        self,
        content: str,
        target_tokens: int,
        compressor: Optional[Callable[[str, int], str]] = None
    ) -> str:
        """
        Compress context to fit within target token count.

        Args:
            content: Content to compress
            target_tokens: Target token count
            compressor: Optional custom compressor function

        Returns:
            Compressed content
        """
        current_tokens = self._estimator.estimate(content)

        if current_tokens <= target_tokens:
            return content

        if compressor:
            return compressor(content, target_tokens)

        # Default compression: truncate with ellipsis
        ratio = target_tokens / current_tokens
        target_chars = int(len(content) * ratio * 0.9)  # 10% buffer

        return content[:target_chars] + "\n\n[...content truncated for token budget...]"

    def release_context(self, tokens: int) -> None:
        """Release context tokens (e.g., after response received)."""
        self.budget.current_context = max(0, self.budget.current_context - tokens)
        self.budget.current_total = max(0, self.budget.current_total - tokens)
        self._log_event("release", "context", tokens)

    def _log_event(self, event_type: str, component: str, tokens: int) -> None:
        """Log a budget event."""
        event = BudgetEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            component=component,
            tokens=tokens,
            budget_after={
                "governance": self.budget.current_governance,
                "context": self.budget.current_context,
                "total": self.budget.current_total,
            }
        )
        self._events.append(event)

    def get_events(self) -> List[BudgetEvent]:
        """Get all logged events."""
        return self._events.copy()

    def get_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        return {
            "budget": self.budget.to_dict(),
            "event_count": len(self._events),
            "last_event": self._events[-1].__dict__ if self._events else None,
        }


# Singleton instance
_enforcer: Optional[TokenBudgetEnforcer] = None


def get_enforcer() -> TokenBudgetEnforcer:
    """Get default enforcer instance."""
    global _enforcer
    if _enforcer is None:
        _enforcer = TokenBudgetEnforcer()
    return _enforcer


def reset_budget() -> None:
    """Reset the global budget (for new session)."""
    global _enforcer
    _enforcer = TokenBudgetEnforcer()
