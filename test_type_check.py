"""Test file to verify mypy pre-commit hook (ADR-013)."""


def add_numbers(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b


def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    result = add_numbers(1, 2)
    print(result)
    print(greet("World"))
