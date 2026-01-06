"""
@require_harness Decorator

Prevents code from running outside of a governed harness session.
This is a critical safeguard against accidental bypass of governance.

Usage:
    from governance.require_harness import require_harness, HarnessContext

    @require_harness
    def dangerous_operation():
        # This will raise if not running inside a harness
        pass

    # To run inside harness:
    with HarnessContext():
        dangerous_operation()  # Works

    dangerous_operation()  # Raises HarnessRequiredError
"""

import functools
import os
import threading
from contextlib import contextmanager
from typing import Callable, TypeVar, Any

# Thread-local storage for harness context
_harness_context = threading.local()

# Environment variable that can also signal harness mode
HARNESS_ENV_VAR = "AI_ORCHESTRATOR_HARNESS_ACTIVE"


class HarnessRequiredError(Exception):
    """Raised when code requires harness but isn't running inside one."""

    def __init__(self, func_name: str):
        self.func_name = func_name
        super().__init__(
            f"Function '{func_name}' requires harness context.\n"
            f"This function must be called within a GovernedSession or HarnessContext.\n"
            f"Running outside harness bypasses governance - this is not allowed."
        )


def is_harness_active() -> bool:
    """Check if code is running inside a harness context."""
    # Check thread-local context
    if getattr(_harness_context, "active", False):
        return True

    # Check environment variable (for subprocess scenarios)
    if os.environ.get(HARNESS_ENV_VAR, "").lower() in ("1", "true", "yes"):
        return True

    return False


def set_harness_active(active: bool = True) -> None:
    """Set the harness context state (used by GovernedSession)."""
    _harness_context.active = active
    if active:
        os.environ[HARNESS_ENV_VAR] = "1"
    else:
        os.environ.pop(HARNESS_ENV_VAR, None)


@contextmanager
def HarnessContext():
    """
    Context manager for harness-protected code blocks.

    Usage:
        with HarnessContext():
            # Code here can call @require_harness functions
            pass
    """
    previous = getattr(_harness_context, "active", False)
    previous_env = os.environ.get(HARNESS_ENV_VAR)

    try:
        set_harness_active(True)
        yield
    finally:
        _harness_context.active = previous
        if previous_env is not None:
            os.environ[HARNESS_ENV_VAR] = previous_env
        else:
            os.environ.pop(HARNESS_ENV_VAR, None)


def require_harness(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that enforces function execution within a harness context.

    Use this on any function that:
    - Makes changes to target repositories
    - Runs verification steps
    - Should never be called outside of governance

    Example:
        @require_harness
        def apply_fix(file_path: str, content: str):
            # This will raise HarnessRequiredError if called outside harness
            with open(file_path, 'w') as f:
                f.write(content)
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not is_harness_active():
            raise HarnessRequiredError(func.__name__)
        return func(*args, **kwargs)

    # Mark the function as requiring harness (for introspection)
    wrapper._requires_harness = True  # type: ignore
    return wrapper


def require_harness_async(func: Callable[..., Any]) -> Callable[..., Any]:
    """Async version of require_harness decorator."""
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not is_harness_active():
            raise HarnessRequiredError(func.__name__)
        return await func(*args, **kwargs)

    wrapper._requires_harness = True  # type: ignore
    return wrapper


# Convenience exports
__all__ = [
    "require_harness",
    "require_harness_async",
    "HarnessContext",
    "HarnessRequiredError",
    "is_harness_active",
    "set_harness_active",
    "HARNESS_ENV_VAR",
]
