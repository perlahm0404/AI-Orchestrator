"""
Baseline Recording for Pre-Existing Failures

Records the state of lint/typecheck/tests BEFORE changes are made,
so we can distinguish between:
- Pre-existing failures (repo was already broken)
- Regressions (this change broke something)
- Net improvements (this change fixed something)

Usage:
    from ralph.baseline import BaselineRecorder, BaselineComparison

    # At session start, record baseline
    recorder = BaselineRecorder(project_path, app_context)
    baseline = recorder.record()

    # ... agent makes changes ...

    # After changes, compare
    comparison = recorder.compare_to_current()

    if comparison.has_regressions:
        # This change made things worse
        revert()
    elif comparison.has_improvements:
        # This change fixed something!
        celebrate()
    else:
        # Same state as before (including any pre-existing failures)
        pass
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class StepStatus(Enum):
    """Status of a verification step."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"  # Step not configured


@dataclass
class StepBaseline:
    """Baseline for a single verification step."""
    step_name: str
    status: StepStatus
    error_count: int = 0
    error_hashes: list[str] = field(default_factory=list)  # Hashed errors for comparison
    raw_output: str = ""
    duration_ms: int = 0


@dataclass
class Baseline:
    """Complete baseline snapshot of project state."""
    project: str
    recorded_at: str
    commit_hash: str
    steps: dict[str, StepBaseline]

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "project": self.project,
            "recorded_at": self.recorded_at,
            "commit_hash": self.commit_hash,
            "steps": {
                name: {
                    "step_name": step.step_name,
                    "status": step.status.value,
                    "error_count": step.error_count,
                    "error_hashes": step.error_hashes,
                    "duration_ms": step.duration_ms,
                }
                for name, step in self.steps.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Baseline":
        """Load from dict."""
        steps = {}
        for name, step_data in data.get("steps", {}).items():
            steps[name] = StepBaseline(
                step_name=step_data["step_name"],
                status=StepStatus(step_data["status"]),
                error_count=step_data.get("error_count", 0),
                error_hashes=step_data.get("error_hashes", []),
                duration_ms=step_data.get("duration_ms", 0),
            )
        return cls(
            project=data["project"],
            recorded_at=data["recorded_at"],
            commit_hash=data["commit_hash"],
            steps=steps,
        )


@dataclass
class StepComparison:
    """Comparison of a step between baseline and current."""
    step_name: str
    baseline_status: StepStatus
    current_status: StepStatus
    baseline_errors: int
    current_errors: int
    new_errors: list[str]  # Errors that didn't exist in baseline
    fixed_errors: list[str]  # Errors that were in baseline but not current

    @property
    def is_regression(self) -> bool:
        """True if this change made things worse."""
        # Was passing, now failing
        if self.baseline_status == StepStatus.PASS and self.current_status == StepStatus.FAIL:
            return True
        # More errors than before
        if self.current_errors > self.baseline_errors:
            return True
        return False

    @property
    def is_improvement(self) -> bool:
        """True if this change made things better."""
        # Was failing, now passing
        if self.baseline_status == StepStatus.FAIL and self.current_status == StepStatus.PASS:
            return True
        # Fewer errors than before
        if self.current_errors < self.baseline_errors:
            return True
        return False

    @property
    def is_unchanged(self) -> bool:
        """True if state is the same."""
        return not self.is_regression and not self.is_improvement


@dataclass
class BaselineComparison:
    """Complete comparison between baseline and current state."""
    baseline: Baseline
    current: Baseline
    step_comparisons: dict[str, StepComparison]

    @property
    def has_regressions(self) -> bool:
        """True if any step regressed."""
        return any(c.is_regression for c in self.step_comparisons.values())

    @property
    def has_improvements(self) -> bool:
        """True if any step improved."""
        return any(c.is_improvement for c in self.step_comparisons.values())

    @property
    def regression_steps(self) -> list[str]:
        """Names of steps that regressed."""
        return [name for name, c in self.step_comparisons.items() if c.is_regression]

    @property
    def improvement_steps(self) -> list[str]:
        """Names of steps that improved."""
        return [name for name, c in self.step_comparisons.items() if c.is_improvement]

    @property
    def net_error_change(self) -> int:
        """Net change in error count (negative = improvement)."""
        return sum(
            c.current_errors - c.baseline_errors
            for c in self.step_comparisons.values()
        )

    def summary(self) -> str:
        """Human-readable summary."""
        lines = []
        lines.append("=" * 60)
        lines.append("BASELINE COMPARISON")
        lines.append("=" * 60)

        for name, comp in self.step_comparisons.items():
            status_icon = "✅" if comp.current_status == StepStatus.PASS else "❌"
            change_icon = ""
            if comp.is_regression:
                change_icon = "📉 REGRESSION"
            elif comp.is_improvement:
                change_icon = "📈 IMPROVEMENT"

            lines.append(f"\n{status_icon} {name.upper()}")
            lines.append(f"   Baseline: {comp.baseline_status.value} ({comp.baseline_errors} errors)")
            lines.append(f"   Current:  {comp.current_status.value} ({comp.current_errors} errors)")
            if change_icon:
                lines.append(f"   {change_icon}")

            if comp.new_errors:
                lines.append(f"   New errors: {len(comp.new_errors)}")
            if comp.fixed_errors:
                lines.append(f"   Fixed errors: {len(comp.fixed_errors)}")

        lines.append("\n" + "=" * 60)
        if self.has_regressions:
            lines.append("⚠️  REGRESSIONS DETECTED - This change made things worse")
        elif self.has_improvements:
            lines.append("✅ NET IMPROVEMENT - This change fixed issues")
        else:
            lines.append("➡️  NO CHANGE - Same state as baseline")
        lines.append("=" * 60)

        return "\n".join(lines)


class BaselineRecorder:
    """Records and compares project baselines."""

    def __init__(self, project_path: Path, app_context):
        self.project_path = Path(project_path)
        self.app_context = app_context
        self._baseline: Optional[Baseline] = None

    def _get_commit_hash(self) -> str:
        """Get current HEAD commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _run_command(self, command: str) -> tuple[bool, str, int]:
        """Run a command and return (passed, output, duration_ms)."""
        import time
        start = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            duration_ms = int((time.time() - start) * 1000)
            output = result.stdout + result.stderr
            passed = result.returncode == 0
            return passed, output, duration_ms
        except subprocess.TimeoutExpired:
            return False, "Command timed out", 300000
        except Exception as e:
            return False, str(e), 0

    def _hash_errors(self, output: str) -> list[str]:
        """Extract and hash individual errors from output for comparison."""
        import hashlib

        # Simple line-based hashing - each non-empty line gets hashed
        # This is a simplistic approach; project-specific parsers could be added
        hashes = []
        for line in output.split("\n"):
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in ["error", "fail", "❌", "✗"]):
                # Hash the line to enable comparison without storing full output
                hash_val = hashlib.md5(line.encode()).hexdigest()[:12]
                hashes.append(hash_val)
        return sorted(set(hashes))

    def _count_errors(self, output: str) -> int:
        """Count errors in output."""
        return len(self._hash_errors(output))

    def record(self) -> Baseline:
        """Record current project state as baseline."""
        steps = {}

        # Lint
        if self.app_context.lint_command:
            passed, output, duration = self._run_command(self.app_context.lint_command)
            steps["lint"] = StepBaseline(
                step_name="lint",
                status=StepStatus.PASS if passed else StepStatus.FAIL,
                error_count=0 if passed else self._count_errors(output),
                error_hashes=[] if passed else self._hash_errors(output),
                raw_output=output[:5000],  # Truncate
                duration_ms=duration,
            )
        else:
            steps["lint"] = StepBaseline("lint", StepStatus.SKIP)

        # Typecheck
        if self.app_context.typecheck_command:
            passed, output, duration = self._run_command(self.app_context.typecheck_command)
            steps["typecheck"] = StepBaseline(
                step_name="typecheck",
                status=StepStatus.PASS if passed else StepStatus.FAIL,
                error_count=0 if passed else self._count_errors(output),
                error_hashes=[] if passed else self._hash_errors(output),
                raw_output=output[:5000],
                duration_ms=duration,
            )
        else:
            steps["typecheck"] = StepBaseline("typecheck", StepStatus.SKIP)

        # Tests
        if self.app_context.test_command:
            passed, output, duration = self._run_command(self.app_context.test_command)
            steps["test"] = StepBaseline(
                step_name="test",
                status=StepStatus.PASS if passed else StepStatus.FAIL,
                error_count=0 if passed else self._count_errors(output),
                error_hashes=[] if passed else self._hash_errors(output),
                raw_output=output[:10000],
                duration_ms=duration,
            )
        else:
            steps["test"] = StepBaseline("test", StepStatus.SKIP)

        self._baseline = Baseline(
            project=self.app_context.project_name,
            recorded_at=datetime.now().isoformat(),
            commit_hash=self._get_commit_hash(),
            steps=steps,
        )

        return self._baseline

    def compare_to_current(self) -> BaselineComparison:
        """Compare stored baseline to current project state."""
        if not self._baseline:
            raise ValueError("No baseline recorded. Call record() first.")

        # Record current state
        current = self.record()

        # Build comparisons
        step_comparisons = {}
        for step_name in self._baseline.steps:
            baseline_step = self._baseline.steps[step_name]
            current_step = current.steps.get(step_name)

            if not current_step:
                continue

            # Find new and fixed errors by comparing hashes
            baseline_hashes = set(baseline_step.error_hashes)
            current_hashes = set(current_step.error_hashes)

            new_errors = list(current_hashes - baseline_hashes)
            fixed_errors = list(baseline_hashes - current_hashes)

            step_comparisons[step_name] = StepComparison(
                step_name=step_name,
                baseline_status=baseline_step.status,
                current_status=current_step.status,
                baseline_errors=baseline_step.error_count,
                current_errors=current_step.error_count,
                new_errors=new_errors,
                fixed_errors=fixed_errors,
            )

        return BaselineComparison(
            baseline=self._baseline,
            current=current,
            step_comparisons=step_comparisons,
        )

    def save(self, path: Path) -> None:
        """Save baseline to file."""
        if not self._baseline:
            raise ValueError("No baseline to save")
        with open(path, "w") as f:
            json.dump(self._baseline.to_dict(), f, indent=2)

    def load(self, path: Path) -> Baseline:
        """Load baseline from file."""
        with open(path) as f:
            data = json.load(f)
        self._baseline = Baseline.from_dict(data)
        return self._baseline


# Convenience functions
def record_baseline(project_path: Path, app_context) -> Baseline:
    """Quick function to record a baseline."""
    recorder = BaselineRecorder(project_path, app_context)
    return recorder.record()


def compare_baseline(baseline_path: Path, project_path: Path, app_context) -> BaselineComparison:
    """Quick function to compare against a saved baseline."""
    recorder = BaselineRecorder(project_path, app_context)
    recorder.load(baseline_path)
    return recorder.compare_to_current()
