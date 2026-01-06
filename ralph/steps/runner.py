"""
Step Runner

Executes verification steps and returns results.

Implementation: Phase 0 MVP
"""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ralph.engine import StepResult


@dataclass
class StepConfig:
    """Configuration for a verification step."""
    name: str
    command: str
    cwd: Path
    timeout_seconds: int = 300  # 5 minutes default


def run_step(config: StepConfig) -> StepResult:
    """
    Run a verification step and return result.

    Args:
        config: Step configuration

    Returns:
        StepResult with pass/fail status and output
    """
    start_time = time.time()

    try:
        # Run command in project directory
        result = subprocess.run(
            config.command,
            shell=True,
            cwd=config.cwd,
            capture_output=True,
            text=True,
            timeout=config.timeout_seconds
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Combine stdout and stderr
        output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

        # Step passes if exit code is 0
        passed = (result.returncode == 0)

        return StepResult(
            step=config.name,
            passed=passed,
            output=output,
            duration_ms=duration_ms
        )

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        return StepResult(
            step=config.name,
            passed=False,
            output=f"Command timed out after {config.timeout_seconds} seconds",
            duration_ms=duration_ms
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return StepResult(
            step=config.name,
            passed=False,
            output=f"Error running step: {str(e)}",
            duration_ms=duration_ms
        )
