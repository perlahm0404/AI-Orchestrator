"""
Resource Tracker for Cost Guardian System (ADR-004).

Monitors and limits resource consumption across sessions to prevent
runaway costs like the 1 million Lambda requests incident.

Multi-layer protection:
1. Session Budget - Hard limit on total iterations per session
2. Daily Budget - Rolling 24h limit on expensive operations
3. Cost Tracking - Monitor and log all billable operations
4. Circuit Breakers - Auto-pause when thresholds hit
5. Escalation Threshold - Register tasks when retries exceed limit
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, Any, Union
import json


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# =============================================================================
# CONFIGURATION DATACLASSES
# =============================================================================

@dataclass
class ResourceLimits:
    """
    Configurable resource limits for the Cost Guardian system.

    All limits are configurable per-project or can use defaults.
    """

    # Session limits
    max_iterations: int = 500           # Total iterations per session
    max_api_calls: int = 10_000         # Total API calls per session
    max_file_writes: int = 200          # Total file writes per session
    max_session_hours: int = 8          # Maximum session duration

    # Daily limits (rolling 24h)
    max_lambda_deploys_daily: int = 50  # Prevent deploy loops
    max_api_calls_daily: int = 100_000  # Daily API budget
    max_cost_daily_usd: float = 50.0    # Daily cost cap

    # Retry escalation (ADR-003 integration)
    retry_escalation_threshold: int = 10  # Retries before escalation to human

    # Circuit breaker thresholds (% of limit to trigger warning)
    circuit_breaker_pct: float = 0.8    # Warn at 80% of limits

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_iterations": self.max_iterations,
            "max_api_calls": self.max_api_calls,
            "max_file_writes": self.max_file_writes,
            "max_session_hours": self.max_session_hours,
            "max_lambda_deploys_daily": self.max_lambda_deploys_daily,
            "max_api_calls_daily": self.max_api_calls_daily,
            "max_cost_daily_usd": self.max_cost_daily_usd,
            "retry_escalation_threshold": self.retry_escalation_threshold,
            "circuit_breaker_pct": self.circuit_breaker_pct,
        }


@dataclass
class ResourceUsage:
    """
    Current resource usage tracking.

    Tracks both session-level and operation-specific metrics.
    """

    # Session counters
    iterations: int = 0
    api_calls: int = 0
    file_writes: int = 0
    session_start: datetime = field(default_factory=utc_now)

    # Operation counters
    lambda_deploys: int = 0
    npm_installs: int = 0

    # Cost estimate (USD)
    estimated_cost_usd: float = 0.0

    # Timestamps for rate limiting
    last_lambda_deploy: Optional[datetime] = None
    last_npm_install: Optional[datetime] = None
    last_external_api: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "iterations": self.iterations,
            "api_calls": self.api_calls,
            "file_writes": self.file_writes,
            "session_start": self.session_start.isoformat(),
            "lambda_deploys": self.lambda_deploys,
            "npm_installs": self.npm_installs,
            "estimated_cost_usd": self.estimated_cost_usd,
            "last_lambda_deploy": self.last_lambda_deploy.isoformat() if self.last_lambda_deploy else None,
            "last_npm_install": self.last_npm_install.isoformat() if self.last_npm_install else None,
            "last_external_api": self.last_external_api.isoformat() if self.last_external_api else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceUsage":
        """Create from dictionary."""
        return cls(
            iterations=data.get("iterations", 0),
            api_calls=data.get("api_calls", 0),
            file_writes=data.get("file_writes", 0),
            session_start=datetime.fromisoformat(data["session_start"]) if data.get("session_start") else utc_now(),
            lambda_deploys=data.get("lambda_deploys", 0),
            npm_installs=data.get("npm_installs", 0),
            estimated_cost_usd=data.get("estimated_cost_usd", 0.0),
            last_lambda_deploy=datetime.fromisoformat(data["last_lambda_deploy"]) if data.get("last_lambda_deploy") else None,
            last_npm_install=datetime.fromisoformat(data["last_npm_install"]) if data.get("last_npm_install") else None,
            last_external_api=datetime.fromisoformat(data["last_external_api"]) if data.get("last_external_api") else None,
        )


@dataclass
class LimitCheck:
    """
    Result of a resource limit check.

    Contains information about whether limits are exceeded,
    warnings for approaching limits, and current usage.
    """

    exceeded: bool                              # Hard limit exceeded
    reasons: list[str] = field(default_factory=list)     # Why limits exceeded
    warnings: list[str] = field(default_factory=list)    # Circuit breaker warnings
    usage: Optional[ResourceUsage] = None       # Current usage snapshot

    def should_pause(self) -> bool:
        """Check if should pause (exceeded or circuit breaker warnings)."""
        return self.exceeded or len(self.warnings) > 0

    def should_stop(self) -> bool:
        """Check if should stop completely (hard limit exceeded)."""
        return self.exceeded

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "exceeded": self.exceeded,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "should_pause": self.should_pause(),
            "should_stop": self.should_stop(),
        }


# =============================================================================
# RESOURCE TRACKER
# =============================================================================

class ResourceTracker:
    """
    Tracks and enforces resource limits for the Cost Guardian system.

    Usage:
        tracker = ResourceTracker(project="credentialmate")
        tracker.record_iteration()

        check = tracker.check_limits()
        if check.exceeded:
            print(f"LIMIT EXCEEDED: {check.reasons}")
            # Stop autonomous loop

        if check.warnings:
            print(f"WARNING: {check.warnings}")
            # Consider pausing

    State Persistence:
        - Session state: .aibrain/resources/{project}-resources.json
        - Daily state: .aibrain/resources/{project}-daily.json
    """

    def __init__(
        self,
        project: str,
        limits: Optional[ResourceLimits] = None,
        state_dir: Optional[Path] = None,
    ):
        """
        Initialize ResourceTracker.

        Args:
            project: Project name for state isolation
            limits: Custom limits (uses defaults if None)
            state_dir: Directory for state files (default: .aibrain/resources)
        """
        self.project = project
        self.limits = limits or ResourceLimits()
        self.state_dir = Path(state_dir) if state_dir else Path(".aibrain/resources")
        self.state_file = self.state_dir / f"{project}-resources.json"
        self.daily_file = self.state_dir / f"{project}-daily.json"

        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Initialize state
        self.usage: ResourceUsage = self._load_session_state()
        self.daily_usage: Dict[str, Union[str, int, float]] = self._load_daily_state()

    # -------------------------------------------------------------------------
    # Recording Methods
    # -------------------------------------------------------------------------

    def record_iteration(self) -> LimitCheck:
        """
        Record one agent iteration.

        Call this once per iteration in the autonomous loop.

        Returns:
            LimitCheck with current status
        """
        self.usage.iterations += 1
        self._persist_state()
        return self.check_limits()

    def record_api_call(self, count: int = 1) -> LimitCheck:
        """
        Record API calls (e.g., Claude API).

        Args:
            count: Number of API calls to record

        Returns:
            LimitCheck with current status
        """
        self.usage.api_calls += count
        current = int(self.daily_usage.get("api_calls", 0))
        self.daily_usage["api_calls"] = current + count
        self._persist_state()
        return self.check_limits()

    def record_file_write(self, count: int = 1) -> LimitCheck:
        """
        Record file write operations.

        Args:
            count: Number of file writes to record

        Returns:
            LimitCheck with current status
        """
        self.usage.file_writes += count
        self._persist_state()
        return self.check_limits()

    def record_lambda_deploy(self) -> LimitCheck:
        """
        Record Lambda deployment.

        Important: This is a critical operation that can cause
        runaway costs if done in a retry loop.

        Returns:
            LimitCheck with current status
        """
        self.usage.lambda_deploys += 1
        current = int(self.daily_usage.get("lambda_deploys", 0))
        self.daily_usage["lambda_deploys"] = current + 1
        self.usage.last_lambda_deploy = utc_now()
        self._persist_state()
        return self.check_limits()

    def record_npm_install(self) -> LimitCheck:
        """
        Record npm install operation.

        Returns:
            LimitCheck with current status
        """
        self.usage.npm_installs += 1
        current = int(self.daily_usage.get("npm_installs", 0))
        self.daily_usage["npm_installs"] = current + 1
        self.usage.last_npm_install = utc_now()
        self._persist_state()
        return self.check_limits()

    def record_cost(self, amount_usd: float) -> LimitCheck:
        """
        Record estimated cost.

        Args:
            amount_usd: Cost in USD to record

        Returns:
            LimitCheck with current status
        """
        self.usage.estimated_cost_usd += amount_usd
        current = float(self.daily_usage.get("cost_usd", 0.0))
        self.daily_usage["cost_usd"] = current + amount_usd
        self._persist_state()
        return self.check_limits()

    # -------------------------------------------------------------------------
    # Limit Checking
    # -------------------------------------------------------------------------

    def check_limits(self) -> LimitCheck:
        """
        Check all resource limits.

        Checks both hard limits (must stop) and circuit breaker
        thresholds (should pause/warn).

        Returns:
            LimitCheck with exceeded flag, reasons, and warnings
        """
        exceeded_reasons = []
        warnings = []
        cb_pct = self.limits.circuit_breaker_pct

        # Session limits
        if self.usage.iterations >= self.limits.max_iterations:
            exceeded_reasons.append(
                f"Session iterations: {self.usage.iterations}/{self.limits.max_iterations}"
            )
        elif self.usage.iterations >= self.limits.max_iterations * cb_pct:
            warnings.append(
                f"Approaching iteration limit: {self.usage.iterations}/{self.limits.max_iterations} "
                f"({self.usage.iterations / self.limits.max_iterations * 100:.0f}%)"
            )

        if self.usage.api_calls >= self.limits.max_api_calls:
            exceeded_reasons.append(
                f"Session API calls: {self.usage.api_calls}/{self.limits.max_api_calls}"
            )
        elif self.usage.api_calls >= self.limits.max_api_calls * cb_pct:
            warnings.append(
                f"Approaching API call limit: {self.usage.api_calls}/{self.limits.max_api_calls}"
            )

        if self.usage.file_writes >= self.limits.max_file_writes:
            exceeded_reasons.append(
                f"Session file writes: {self.usage.file_writes}/{self.limits.max_file_writes}"
            )

        # Session duration
        session_duration = utc_now() - self.usage.session_start
        max_duration = timedelta(hours=self.limits.max_session_hours)
        if session_duration >= max_duration:
            exceeded_reasons.append(
                f"Session duration: {session_duration} >= {max_duration}"
            )

        # Daily limits
        daily_deploys = int(self.daily_usage.get("lambda_deploys", 0))
        if daily_deploys >= self.limits.max_lambda_deploys_daily:
            exceeded_reasons.append(
                f"Daily Lambda deploys: {daily_deploys}/{self.limits.max_lambda_deploys_daily}"
            )
        elif daily_deploys >= self.limits.max_lambda_deploys_daily * cb_pct:
            warnings.append(
                f"Approaching daily deploy limit: {daily_deploys}/{self.limits.max_lambda_deploys_daily}"
            )

        daily_cost = float(self.daily_usage.get("cost_usd", 0.0))
        if daily_cost >= self.limits.max_cost_daily_usd:
            exceeded_reasons.append(
                f"Daily cost: ${daily_cost:.2f}/${self.limits.max_cost_daily_usd:.2f}"
            )
        elif daily_cost >= self.limits.max_cost_daily_usd * cb_pct:
            warnings.append(
                f"Approaching daily cost limit: ${daily_cost:.2f}/${self.limits.max_cost_daily_usd:.2f}"
            )

        return LimitCheck(
            exceeded=len(exceeded_reasons) > 0,
            reasons=exceeded_reasons,
            warnings=warnings,
            usage=self.usage,
        )

    def check_retry_escalation(self, attempts: int) -> bool:
        """
        Check if task should be escalated due to excessive retries.

        Args:
            attempts: Current number of attempts

        Returns:
            True if should escalate to human review
        """
        return attempts >= self.limits.retry_escalation_threshold

    # -------------------------------------------------------------------------
    # Summary and Reporting
    # -------------------------------------------------------------------------

    def get_summary(self) -> Dict[str, Any]:
        """
        Get usage summary for logging and reporting.

        Returns:
            Dictionary with session, daily, and limits information
        """
        return {
            "project": self.project,
            "session": {
                "iterations": self.usage.iterations,
                "api_calls": self.usage.api_calls,
                "file_writes": self.usage.file_writes,
                "lambda_deploys": self.usage.lambda_deploys,
                "npm_installs": self.usage.npm_installs,
                "cost_usd": round(self.usage.estimated_cost_usd, 4),
                "duration_hours": round(
                    (utc_now() - self.usage.session_start).total_seconds() / 3600, 2
                ),
            },
            "daily": {
                "lambda_deploys": int(self.daily_usage.get("lambda_deploys", 0)),
                "api_calls": int(self.daily_usage.get("api_calls", 0)),
                "npm_installs": int(self.daily_usage.get("npm_installs", 0)),
                "cost_usd": round(float(self.daily_usage.get("cost_usd", 0.0)), 4),
            },
            "limits": self.limits.to_dict(),
            "status": self.check_limits().to_dict(),
        }

    def get_usage_report(self) -> str:
        """
        Generate a human-readable usage report.

        Returns:
            Markdown-formatted usage report
        """
        summary = self.get_summary()
        check = self.check_limits()

        lines = [
            f"# Resource Usage Report - {self.project}",
            f"Generated: {utc_now().isoformat()}Z",
            "",
            "## Session Stats",
            f"- Iterations: {summary['session']['iterations']} / {self.limits.max_iterations} "
            f"({summary['session']['iterations'] / self.limits.max_iterations * 100:.0f}%)",
            f"- API Calls: {summary['session']['api_calls']} / {self.limits.max_api_calls}",
            f"- File Writes: {summary['session']['file_writes']} / {self.limits.max_file_writes}",
            f"- Lambda Deploys: {summary['session']['lambda_deploys']}",
            f"- Duration: {summary['session']['duration_hours']} hours / {self.limits.max_session_hours} hours",
            "",
            "## Daily Stats (Rolling 24h)",
            f"- Lambda Deploys: {summary['daily']['lambda_deploys']} / {self.limits.max_lambda_deploys_daily}",
            f"- API Calls: {summary['daily']['api_calls']} / {self.limits.max_api_calls_daily}",
            "",
            "## Cost Estimate",
            f"- Session: ${summary['session']['cost_usd']:.4f}",
            f"- Daily: ${summary['daily']['cost_usd']:.4f} / ${self.limits.max_cost_daily_usd:.2f}",
            "",
            "## Status",
        ]

        if check.exceeded:
            lines.append(f"**LIMIT EXCEEDED**")
            for reason in check.reasons:
                lines.append(f"- {reason}")
        elif check.warnings:
            lines.append(f"**WARNING - Approaching Limits**")
            for warning in check.warnings:
                lines.append(f"- {warning}")
        else:
            lines.append("All limits OK")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------

    def reset_session(self) -> None:
        """
        Reset session counters for a new session.

        Daily counters are NOT reset (they use rolling 24h window).
        """
        self.usage = ResourceUsage()
        self._persist_state()

    def reset_daily(self) -> None:
        """
        Reset daily counters.

        Use with caution - normally daily counters reset automatically
        when the 24h window expires.
        """
        self.daily_usage = {"window_start": utc_now().isoformat()}
        self._persist_state()

    # -------------------------------------------------------------------------
    # State Persistence
    # -------------------------------------------------------------------------

    def _load_session_state(self) -> ResourceUsage:
        """Load session state from file or create new."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                usage = ResourceUsage.from_dict(data)

                # Check if session is still valid (within max hours)
                session_age = utc_now() - usage.session_start
                if session_age < timedelta(hours=self.limits.max_session_hours):
                    return usage
                # Session expired, start new
            except Exception:
                pass

        return ResourceUsage()

    def _load_daily_state(self) -> Dict[str, Union[str, int, float]]:
        """Load rolling 24h state from file or create new."""
        if self.daily_file.exists():
            try:
                data = json.loads(self.daily_file.read_text())
                window_start = datetime.fromisoformat(data.get("window_start", ""))

                # Check if within 24h window
                if utc_now() - window_start < timedelta(hours=24):
                    return data
                # Window expired, start new
            except Exception:
                pass

        return {"window_start": utc_now().isoformat()}

    def _persist_state(self) -> None:
        """Save state to files."""
        # Ensure directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Session state
        self.state_file.write_text(
            json.dumps(self.usage.to_dict(), indent=2)
        )

        # Daily state
        self.daily_file.write_text(
            json.dumps(self.daily_usage, indent=2)
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_tracker(
    project: str,
    limits: Optional[ResourceLimits] = None,
) -> ResourceTracker:
    """
    Get a ResourceTracker instance for a project.

    Args:
        project: Project name
        limits: Custom limits (optional)

    Returns:
        Configured ResourceTracker instance
    """
    return ResourceTracker(project=project, limits=limits)


def check_project_limits(project: str) -> LimitCheck:
    """
    Quick check of current limits for a project.

    Args:
        project: Project name

    Returns:
        LimitCheck with current status
    """
    tracker = get_tracker(project)
    return tracker.check_limits()


# =============================================================================
# CLI INTERFACE (for testing)
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python resource_tracker.py <project>")
        print("       python resource_tracker.py <project> --report")
        sys.exit(1)

    project = sys.argv[1]
    tracker = ResourceTracker(project)

    if "--report" in sys.argv:
        print(tracker.get_usage_report())
    else:
        print(json.dumps(tracker.get_summary(), indent=2))
