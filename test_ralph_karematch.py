"""
Test Ralph verification on real KareMatch changes.

This demonstrates the full governance workflow:
1. Agent fixes bugs
2. Ralph verifies changes
3. Human approves (simulated)
"""

from adapters.karematch import KareMatchAdapter
from ralph import engine

# Create adapter
adapter = KareMatchAdapter()
context = adapter.get_context()

# Files we changed
changed_files = [
    "web/src/App.tsx",
    "web/src/pages/therapist-dashboard/schedule.tsx"
]

# Run Ralph verification
print("Running Ralph verification on KareMatch bug fixes...")
print(f"Project: {context.project_name}")
print(f"Changed files: {changed_files}")
print()

verdict = engine.verify(
    project=context.project_name,
    changes=changed_files,
    session_id="phase-1-bugfix-test",
    app_context=context
)

print(f"Verdict: {verdict.type.value}")
print(f"Reason: {verdict.reason}")
print()
print("Steps:")
for step in verdict.steps:
    status = "✅ PASS" if step.passed else "❌ FAIL"
    print(f"  {status} {step.step} ({step.duration_ms}ms)")

print()
if verdict.type.value == "PASS":
    print("✅ All checks passed! Agent work ready for human approval.")
elif verdict.type.value == "BLOCKED":
    print("⛔ BLOCKED! Guardrail violations detected. Must fix before proceeding.")
    print(f"Violations: {verdict.evidence.get('violations', [])}")
else:
    print("❌ FAIL! Some checks failed. Agent should retry.")
