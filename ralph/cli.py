#!/usr/bin/env python3
"""
Ralph CLI - Command line interface for Ralph verification.

Used by git hooks and wrapper scripts to verify changes.

Usage:
    # Verify staged files (for pre-commit hook)
    python -m ralph.cli --staged --project karematch

    # Verify specific files
    python -m ralph.cli --files src/auth.ts src/login.ts --project karematch

    # Verify with custom project path
    python -m ralph.cli --staged --project karematch --project-path /path/to/project
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ralph.engine import verify, VerdictType
from adapters import get_adapter


def get_staged_files(project_path: Path) -> list[str]:
    """Get list of staged files from git."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return []

    files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    return files


def get_changed_files(project_path: Path) -> list[str]:
    """Get list of all changed files (staged + unstaged)."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return []

    files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    return files


def main():
    parser = argparse.ArgumentParser(description="Ralph verification CLI")
    parser.add_argument("--project", required=True, help="Project name (karematch, credentialmate)")
    parser.add_argument("--project-path", help="Override project path")
    parser.add_argument("--staged", action="store_true", help="Verify staged files only")
    parser.add_argument("--all-changes", action="store_true", help="Verify all changed files")
    parser.add_argument("--files", nargs="+", help="Specific files to verify")
    parser.add_argument("--session-id", default="cli-verification", help="Session ID for audit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Get adapter for project
    try:
        adapter = get_adapter(args.project)
        app_context = adapter.get_context()
    except Exception as e:
        print(f"ERROR: Failed to load adapter for '{args.project}': {e}")
        sys.exit(2)

    # Override project path if specified
    if args.project_path:
        app_context.project_path = Path(args.project_path)

    project_path = Path(app_context.project_path)

    # Determine files to verify
    if args.files:
        files = args.files
    elif args.staged:
        files = get_staged_files(project_path)
    elif args.all_changes:
        files = get_changed_files(project_path)
    else:
        print("ERROR: Must specify --staged, --all-changes, or --files")
        sys.exit(2)

    if not files:
        print("No files to verify")
        sys.exit(0)

    if args.verbose:
        print(f"Verifying {len(files)} file(s) in {project_path}:")
        for f in files:
            print(f"  - {f}")
        print()

    # Run verification
    verdict = verify(
        project=args.project,
        changes=files,
        session_id=args.session_id,
        app_context=app_context
    )

    # Output results
    print(f"{'='*60}")
    print(f"RALPH VERDICT: {verdict.type.value}")
    print(f"{'='*60}")

    for step in verdict.steps:
        status = "✅ PASS" if step.passed else "❌ FAIL"
        print(f"\n{status} - {step.step}")
        if args.verbose or not step.passed:
            # Show output for verbose or failed steps
            output_lines = step.output.strip().split("\n")
            for line in output_lines[:20]:  # Limit output
                print(f"    {line}")
            if len(output_lines) > 20:
                print(f"    ... ({len(output_lines) - 20} more lines)")

    if verdict.reason:
        print(f"\nReason: {verdict.reason}")

    print(f"\n{'='*60}")

    # Exit code based on verdict
    if verdict.type == VerdictType.PASS:
        print("✅ Verification PASSED - safe to proceed")
        sys.exit(0)
    elif verdict.type == VerdictType.BLOCKED:
        print("🚫 Verification BLOCKED - guardrail violation, cannot proceed")
        sys.exit(1)
    else:
        print("❌ Verification FAILED - fix issues and retry")
        sys.exit(1)


if __name__ == "__main__":
    main()
