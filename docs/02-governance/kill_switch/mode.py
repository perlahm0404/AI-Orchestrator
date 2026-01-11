"""
Kill Switch / Safe Mode

Global controls for AI Brain operation.

Modes:
- OFF: All agents stopped, no actions allowed
- SAFE: Read-only mode, can run tests but no writes
- NORMAL: Full operation within contracts
- PAUSED: No new work, current work can complete

Usage:
    from governance.kill_switch import mode

    current = mode.get()
    if current == Mode.OFF:
        raise SystemError("AI Brain is OFF")

    mode.set(Mode.SAFE)  # Enter safe mode

Environment variable: AI_BRAIN_MODE

Implementation: Phase 0
"""

from enum import Enum
import os


class Mode(Enum):
    """AI Brain operation modes."""
    OFF = "OFF"       # Emergency stop - nothing runs
    SAFE = "SAFE"     # Read-only - tests only, no writes
    NORMAL = "NORMAL" # Full operation
    PAUSED = "PAUSED" # No new work, finish current


ENV_VAR = "AI_BRAIN_MODE"
DEFAULT_MODE = Mode.NORMAL


def get() -> Mode:
    """
    Get current operation mode.

    Reads from AI_BRAIN_MODE environment variable.

    Returns:
        Current Mode
    """
    value = os.environ.get(ENV_VAR, DEFAULT_MODE.value)
    try:
        return Mode(value)
    except ValueError:
        return DEFAULT_MODE


def set(new_mode: Mode) -> None:
    """
    Set operation mode.

    Args:
        new_mode: Mode to set

    Note: This sets the environment variable for the current process.
    For persistent changes, update the environment externally.
    """
    os.environ[ENV_VAR] = new_mode.value


def require_normal() -> None:
    """
    Raise exception if not in NORMAL mode.

    Use at the start of write operations.
    """
    current = get()
    if current != Mode.NORMAL:
        raise RuntimeError(f"Operation blocked: AI Brain is in {current.value} mode")


def require_not_off() -> None:
    """
    Raise exception if in OFF mode.

    Use at the start of any operation.
    """
    if get() == Mode.OFF:
        raise RuntimeError("AI Brain is OFF - all operations blocked")
