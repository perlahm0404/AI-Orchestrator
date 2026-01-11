#!/usr/bin/env python3
"""Test script to verify guardrail scanner fix."""

from pathlib import Path
from ralph.guardrails.patterns import scan_for_violations, parse_git_diff

# Test with KareMatch project
project = Path("/Users/tmac/karematch")

print("=" * 60)
print("Testing Guardrail Scanner Fix")
print("=" * 60)

# Show what lines were actually changed
print("\n1. Parsing git diff to find changed lines...")
changed = parse_git_diff(project, staged=True)
if changed:
    print("\nChanged lines (staged):")
    for file, lines in changed.items():
        print(f"  {file}: {sorted(lines)}")
else:
    print("\nNo staged changes found. Checking unstaged...")
    changed = parse_git_diff(project, staged=False)
    if changed:
        print("\nChanged lines (unstaged):")
        for file, lines in changed.items():
            print(f"  {file}: {sorted(lines)}")
    else:
        print("\nNo changes found in git diff")

# Run scanner with OLD behavior (check all lines)
print("\n2. Running scanner with check_only_changed_lines=False (OLD behavior)...")
violations_old = scan_for_violations(
    project,
    changed_files=["tests/appointments-routes.test.ts"],
    check_only_changed_lines=False
)
print(f"\nViolations found (scanning all lines): {len(violations_old)}")
for v in violations_old:
    print(f"  {v.file_path}:{v.line_number} - {v.pattern} - {v.reason}")
    print(f"    Line: {v.line_content}")

# Run scanner with NEW behavior (check only changed lines)
print("\n3. Running scanner with check_only_changed_lines=True (NEW behavior)...")
violations_new = scan_for_violations(
    project,
    changed_files=["tests/appointments-routes.test.ts"],
    check_only_changed_lines=True
)
print(f"\nViolations found (scanning only changed lines): {len(violations_new)}")
for v in violations_new:
    print(f"  {v.file_path}:{v.line_number} - {v.pattern} - {v.reason}")
    print(f"    Line: {v.line_content}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"OLD behavior violations: {len(violations_old)}")
print(f"NEW behavior violations: {len(violations_new)}")
print(f"False positives eliminated: {len(violations_old) - len(violations_new)}")

if len(violations_new) == 0:
    print("\n✅ SUCCESS: No violations in changed lines!")
    print("✅ Pre-existing code patterns are now ignored!")
else:
    print(f"\n⚠️ WARNING: {len(violations_new)} violation(s) found in changed lines")
    print("These are real violations that should be fixed.")

print("=" * 60)
