# Test Prompt for Claude Chat UI

Copy and paste this into Claude to test the autonomous agent system:

---

## Test Prompt

```
I want to test the autonomous agent v2 system we just built.

Please run a simple test of the Claude CLI integration:

1. Test the CLI wrapper directly:
   - Use the ClaudeCliWrapper to execute a simple prompt
   - Prompt: "Create a TypeScript file called hello.ts that exports a function sayHello() which returns 'Hello, World!'"
   - Project directory: /Users/tmac/karematch
   - Timeout: 60 seconds

2. Show me:
   - Whether the execution succeeded
   - How long it took
   - What files were changed
   - Any errors encountered

3. Then test the smart prompt generation:
   - Task ID: "BUG-TEST-001"
   - Description: "Fix undefined variable error in authentication"
   - File: "services/auth/src/session.ts"
   - Test files: ["services/auth/tests/session.test.ts"]

   Show me what prompt gets generated.

Please execute these tests and report the results.
```

---

## Alternative: Direct Python Test

Or run this Python code directly:

```python
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
    result = wrapper.execute_task(
        prompt="List the TypeScript files in the services/auth/src directory. Just show filenames, no other work.",
        files=[],
        timeout=30
    )

    print(f"✓ Execution: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"✓ Duration: {result.duration_ms}ms")
    print(f"✓ Files changed: {len(result.files_changed)}")
    if result.error:
        print(f"✗ Error: {result.error}")
    print(f"✓ Output (first 200 chars): {result.output[:200]}...")

except Exception as e:
    print(f"✗ Exception: {e}")

# Test 2: Smart Prompt Generation
print("\n[Test 2] Smart Prompt Generation")
print("-" * 80)

prompt = generate_smart_prompt(
    task_id="BUG-TEST-001",
    description="Fix undefined variable error in authentication",
    file_path="services/auth/src/session.ts",
    test_files=["services/auth/tests/session.test.ts"]
)

print("✓ Generated Prompt:")
print("-" * 80)
print(prompt[:400])
print("...")
print("-" * 80)

print("\n" + "=" * 80)
print("✅ TESTS COMPLETE")
print("=" * 80)
```

Save as `quick_test.py` and run:
```bash
cd /Users/tmac/Vaults/AI_Orchestrator
python3 quick_test.py
```

---

## Expected Output

### Test 1: CLI Wrapper
```
✓ Execution: SUCCESS
✓ Duration: 12500ms
✓ Files changed: 0
✓ Output (first 200 chars): The services/auth/src directory contains:
- session.ts
- middleware.ts
- tokens.ts
...
```

### Test 2: Smart Prompt
```
✓ Generated Prompt:
Fix this bug: Fix undefined variable error in authentication

**File to fix**: services/auth/src/session.ts

**Test files**: services/auth/tests/session.test.ts

**Requirements**:
1. Read the file and understand the current implementation
2. Fix the bug described above
3. Ensure all existing tests still pass
...
```

---

## What This Tests

✅ **CLI Wrapper**: Subprocess execution, timeout handling, output parsing
✅ **Smart Prompts**: Task type detection, context-aware generation
✅ **Integration**: Both components working together
✅ **Error Handling**: Graceful failure if Claude CLI has issues

---

## Troubleshooting

**Error: "Claude CLI not found"**
```bash
which claude  # Should show path
claude --version  # Should show 2.0.76+
```

**Error: "Not authenticated"**
```bash
claude auth status
claude auth login  # If needed
```

**Error: "Project directory not found"**
```bash
ls -la /Users/tmac/karematch  # Verify exists
```

---

## Next Steps After Test

If tests pass:
1. ✅ System is working!
2. Ready to run full autonomous loop
3. Can process work queue tasks

If tests fail:
1. Check error messages
2. Verify Claude CLI setup
3. Check project path
4. Review logs

---

**Quick Start Command**:
```bash
cd /Users/tmac/Vaults/AI_Orchestrator
python3 quick_test.py
```
