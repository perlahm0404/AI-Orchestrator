#!/usr/bin/env python3
"""
Quick test to verify streaming output works

This test demonstrates that Claude CLI output is now streamed
in real-time rather than buffered until completion.
"""

from claude.cli_wrapper import ClaudeCliWrapper
from pathlib import Path

def test_streaming():
    """Test that streaming output works"""
    wrapper = ClaudeCliWrapper(Path('/Users/tmac/karematch'))

    print("="*60)
    print("Testing streaming output...")
    print("="*60)
    print("\nYou should see output appear line-by-line as Claude works:\n")

    # Simple task to verify streaming
    result = wrapper.execute_task(
        prompt="List the files in the current directory and tell me what you see",
        timeout=30
    )

    print("\n" + "="*60)
    print("Streaming test complete!")
    print("="*60)
    print(f"\nSuccess: {result.success}")
    print(f"Duration: {result.duration_ms}ms")

    return result.success

if __name__ == "__main__":
    success = test_streaming()
    exit(0 if success else 1)
