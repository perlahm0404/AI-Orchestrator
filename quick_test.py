#!/usr/bin/env python3
"""Quick test of Claude CLI integration"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, '/Users/tmac/Vaults/AI_Orchestrator')

from claude.cli_wrapper import ClaudeCliWrapper
from claude.prompts import generate_smart_prompt

print("=" * 80)
print("AUTONOMOUS AGENT V2 - QUICK TEST")
print("=" * 80)

# Test 1: CLI Wrapper
print("\n[Test 1] CLI Wrapper Test")
print("-" * 80)

wrapper = ClaudeCliWrapper(Path("/Users/tmac/karematch"))

try:
    print("Executing: List TypeScript files in services/auth/src...")
    result = wrapper.execute_task(
        prompt="List the TypeScript files in the services/auth/src directory. Just show filenames, no other work.",
        files=[],
        timeout=30
    )

    print(f"\n✓ Execution: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"✓ Duration: {result.duration_ms}ms ({result.duration_ms/1000:.1f}s)")
    print(f"✓ Files changed: {len(result.files_changed)}")
    if result.error:
        print(f"✗ Error: {result.error}")
    else:
        print(f"✓ Output (first 300 chars):")
        print("  " + result.output[:300].replace("\n", "\n  "))
        if len(result.output) > 300:
            print("  ...")

except Exception as e:
    print(f"✗ Exception: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Smart Prompt Generation
print("\n\n[Test 2] Smart Prompt Generation")
print("-" * 80)

test_cases = [
    {
        "id": "BUG-TEST-001",
        "desc": "Fix undefined variable error in authentication",
        "file": "services/auth/src/session.ts",
        "tests": ["services/auth/tests/session.test.ts"]
    },
    {
        "id": "QUALITY-TEST-001",
        "desc": "Remove console.error from logging module",
        "file": "services/logging/src/logger.ts",
        "tests": []
    },
    {
        "id": "TEST-TEST-001",
        "desc": "Create unit test for validateEmail function",
        "file": "services/validation/tests/email.test.ts",
        "tests": []
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. Task Type: {test['id'].split('-')[0]}")
    prompt = generate_smart_prompt(
        task_id=test["id"],
        description=test["desc"],
        file_path=test["file"],
        test_files=test["tests"] if test["tests"] else None
    )

    print(f"   Description: {test['desc']}")
    print(f"   Prompt (first 200 chars):")
    print("   " + prompt[:200].replace("\n", "\n   "))
    print("   ...")

print("\n" + "=" * 80)
print("✅ TESTS COMPLETE")
print("=" * 80)

print("\nNext Steps:")
print("1. If CLI test succeeded → System is working!")
print("2. If CLI test failed → Check Claude CLI authentication")
print("3. Ready to run: python3 autonomous_loop.py --project karematch")
