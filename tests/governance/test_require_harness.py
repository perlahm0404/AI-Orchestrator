"""
Tests for @require_harness decorator.

This ensures that protected functions cannot be called outside a harness context.
"""

import pytest
import os
from governance.require_harness import (
    require_harness,
    require_harness_async,
    HarnessContext,
    HarnessRequiredError,
    is_harness_active,
    set_harness_active,
    HARNESS_ENV_VAR,
)


class TestRequireHarnessDecorator:
    """Test the @require_harness decorator behavior."""

    def setup_method(self):
        """Ensure clean state before each test."""
        set_harness_active(False)
        os.environ.pop(HARNESS_ENV_VAR, None)

    def teardown_method(self):
        """Clean up after each test."""
        set_harness_active(False)
        os.environ.pop(HARNESS_ENV_VAR, None)

    def test_raises_outside_harness(self):
        """Function decorated with @require_harness should raise outside harness."""
        @require_harness
        def protected_function():
            return "should not reach here"

        with pytest.raises(HarnessRequiredError) as exc_info:
            protected_function()

        assert "protected_function" in str(exc_info.value)
        assert "requires harness context" in str(exc_info.value)

    def test_works_inside_harness_context(self):
        """Function should work when called inside HarnessContext."""
        @require_harness
        def protected_function():
            return "success"

        with HarnessContext():
            result = protected_function()

        assert result == "success"

    def test_works_with_set_harness_active(self):
        """Function should work when harness is activated via set_harness_active."""
        @require_harness
        def protected_function():
            return "success"

        set_harness_active(True)
        try:
            result = protected_function()
            assert result == "success"
        finally:
            set_harness_active(False)

    def test_works_with_env_var(self):
        """Function should work when harness env var is set."""
        @require_harness
        def protected_function():
            return "success"

        os.environ[HARNESS_ENV_VAR] = "1"
        try:
            result = protected_function()
            assert result == "success"
        finally:
            del os.environ[HARNESS_ENV_VAR]

    def test_nested_harness_context(self):
        """Nested HarnessContext should work correctly."""
        @require_harness
        def protected_function():
            return "success"

        with HarnessContext():
            with HarnessContext():
                result = protected_function()
                assert result == "success"
            # Should still work after inner context exits
            result = protected_function()
            assert result == "success"

        # Should fail after outer context exits
        with pytest.raises(HarnessRequiredError):
            protected_function()

    def test_preserves_function_metadata(self):
        """Decorator should preserve function name and docstring."""
        @require_harness
        def my_function():
            """This is the docstring."""
            pass

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "This is the docstring."

    def test_marks_function_as_requiring_harness(self):
        """Decorated function should have _requires_harness attribute."""
        @require_harness
        def my_function():
            pass

        assert hasattr(my_function, "_requires_harness")
        assert my_function._requires_harness is True

    def test_passes_arguments_correctly(self):
        """Arguments should be passed through correctly."""
        @require_harness
        def add(a, b, multiplier=1):
            return (a + b) * multiplier

        with HarnessContext():
            assert add(2, 3) == 5
            assert add(2, 3, multiplier=2) == 10

    def test_returns_value_correctly(self):
        """Return values should be passed through correctly."""
        @require_harness
        def get_dict():
            return {"key": "value", "count": 42}

        with HarnessContext():
            result = get_dict()
            assert result == {"key": "value", "count": 42}


# NOTE: Async tests removed - require pytest-asyncio which is not installed
# The async decorator (require_harness_async) exists but is not tested here


class TestIsHarnessActive:
    """Test the is_harness_active() function."""

    def setup_method(self):
        set_harness_active(False)
        os.environ.pop(HARNESS_ENV_VAR, None)

    def teardown_method(self):
        set_harness_active(False)
        os.environ.pop(HARNESS_ENV_VAR, None)

    def test_false_by_default(self):
        """Should return False when no harness is active."""
        assert is_harness_active() is False

    def test_true_in_context(self):
        """Should return True inside HarnessContext."""
        assert is_harness_active() is False
        with HarnessContext():
            assert is_harness_active() is True
        assert is_harness_active() is False

    def test_true_with_env_var(self):
        """Should return True when env var is set."""
        os.environ[HARNESS_ENV_VAR] = "true"
        assert is_harness_active() is True

    def test_env_var_case_insensitive(self):
        """Env var check should be case insensitive."""
        for value in ["1", "true", "TRUE", "True", "yes", "YES"]:
            os.environ[HARNESS_ENV_VAR] = value
            assert is_harness_active() is True
            del os.environ[HARNESS_ENV_VAR]


class TestHarnessErrorMessage:
    """Test that error messages are helpful."""

    def test_error_includes_function_name(self):
        """Error message should include the function name."""
        @require_harness
        def very_specific_function_name():
            pass

        try:
            very_specific_function_name()
            assert False, "Should have raised"
        except HarnessRequiredError as e:
            assert "very_specific_function_name" in str(e)

    def test_error_explains_solution(self):
        """Error message should explain how to fix the issue."""
        @require_harness
        def my_func():
            pass

        try:
            my_func()
        except HarnessRequiredError as e:
            message = str(e)
            assert "GovernedSession" in message or "HarnessContext" in message
