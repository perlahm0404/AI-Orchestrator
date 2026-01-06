#!/usr/bin/env python3
"""
Agent Harness - Run agents with full governance enforcement

This script is the ONLY way agents should execute. All file writes,
Ralph verifications, and governance checks happen here.

Usage:
    python run_agent.py bugfix --bug-id BUG-001 --file path/to/file.ts --old "old code" --new "new code"
    python run_agent.py codequality --project karematch --target-count 10
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import uuid

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from governance.kill_switch import mode
from governance import contract
from ralph import engine
from adapters.karematch import KareMatchAdapter
from adapters.credentialmate import CredentialMateAdapter
from agents.bugfix import BugFixAgent, BugTask, fix_bug_simple
from agents.codequality import CodeQualityAgent
from orchestration.reflection import (
    SessionReflection,
    SessionResult,
    SessionStatus,
    FileChange,
    create_session_handoff
)


# Verdict log directory
VERDICT_LOG_DIR = Path(__file__).parent / "logs" / "verdicts"
VERDICT_LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_verdict(bug_id: str, verdict: Any, agent: str) -> Path:
    """
    Log Ralph verdict to file for evidence.

    Args:
        bug_id: Bug identifier
        verdict: Ralph Verdict object
        agent: Agent name (bugfix, codequality, etc.)

    Returns:
        Path to verdict log file
    """
    timestamp = datetime.now().isoformat()
    log_file = VERDICT_LOG_DIR / f"{bug_id}_{timestamp}.json"

    # Convert verdict to dict
    verdict_data = {
        "bug_id": bug_id,
        "agent": agent,
        "timestamp": timestamp,
        "verdict_type": verdict.type.value,
        "reason": verdict.reason,
        "steps": [
            {
                "step": step.step,
                "passed": step.passed,
                "duration_ms": step.duration_ms,
                "output": step.output[:500] if step.output else ""  # Truncate for logs
            }
            for step in verdict.steps
        ]
    }

    # Write to file
    log_file.write_text(json.dumps(verdict_data, indent=2))

    print(f"\n✅ Verdict logged: {log_file}")

    return log_file


def run_bugfix(args: argparse.Namespace) -> int:
    """
    Run BugFix agent with full governance.

    Returns:
        0 if successful, 1 if failed
    """
    print(f"\n{'='*80}")
    print(f"🤖 Running BugFix Agent")
    print(f"{'='*80}\n")

    # 1. Check kill-switch
    print("📋 Step 1: Checking kill-switch...")
    try:
        mode.require_normal()
        print("   ✅ Kill-switch: NORMAL (operations allowed)\n")
    except Exception as e:
        print(f"   ❌ Kill-switch: {e}")
        print("   🛑 Operation BLOCKED by kill-switch\n")
        return 1

    # 2. Load adapter
    print("📋 Step 2: Loading project adapter...")
    if args.project == "karematch":
        adapter = KareMatchAdapter()
    elif args.project == "credentialmate":
        adapter = CredentialMateAdapter()
    else:
        print(f"   ❌ Unknown project: {args.project}\n")
        return 1
    print(f"   ✅ Loaded adapter: {args.project}\n")

    # 3. Initialize agent
    print("📋 Step 3: Initializing BugFix agent...")
    agent = BugFixAgent(adapter)
    print(f"   ✅ Agent initialized with contract: bugfix.yaml\n")

    # 4. Check contract permissions
    print("📋 Step 4: Checking autonomy contract...")
    try:
        contract.require_allowed(agent.contract, "write_file")
        print("   ✅ Contract allows: write_file\n")
    except Exception as e:
        print(f"   ❌ Contract violation: {e}")
        print("   🛑 Operation BLOCKED by contract\n")
        return 1

    # 5. Apply fix
    print("📋 Step 5: Applying bug fix...")
    print(f"   Bug ID: {args.bug_id}")
    print(f"   File: {args.file}")
    print(f"   Old code: {args.old_code[:50]}...")
    print(f"   New code: {args.new_code[:50]}...\n")

    project_path = Path(adapter.get_context().project_path)
    success = fix_bug_simple(
        project_path=project_path,
        file_path=args.file,
        old_code=args.old_code,
        new_code=args.new_code
    )

    if not success:
        print("   ❌ Failed to apply fix\n")
        return 1

    print("   ✅ Fix applied successfully\n")

    # 6. Run Ralph verification
    print("📋 Step 6: Running Ralph verification...")
    print("   This will run: lint, typecheck, tests, guardrails...\n")

    app_context = adapter.get_context()
    verdict = engine.verify(
        project=app_context.project_name,
        changes=[args.file],
        session_id=args.bug_id,
        app_context=app_context
    )

    # 7. Display verdict
    print(f"\n{'='*80}")
    print(f"📊 RALPH VERDICT")
    print(f"{'='*80}\n")
    print(f"Verdict: {verdict.type.value}")
    if verdict.reason:
        print(f"Reason: {verdict.reason}\n")

    print("Steps executed:")
    for step in verdict.steps:
        status_symbol = "✅" if step.passed else "❌"
        status_text = "PASS" if step.passed else "FAIL"
        print(f"  {status_symbol} {step.step}: {status_text} ({step.duration_ms}ms)")

    print()

    # 8. Log verdict
    log_file = log_verdict(args.bug_id, verdict, "bugfix")

    # 9. Return based on verdict
    exit_code = 0
    final_status = SessionStatus.COMPLETED

    if verdict.type.value == "PASS":
        print("✅ Bug fix APPROVED by Ralph - ready for commit\n")
        exit_code = 0
        final_status = SessionStatus.COMPLETED
    elif verdict.type.value == "BLOCKED":
        print("🛑 Bug fix BLOCKED by guardrails - fix violates governance rules\n")
        exit_code = 1
        final_status = SessionStatus.BLOCKED
    else:  # FAIL
        print("❌ Bug fix FAILED verification - tests or checks failed\n")
        exit_code = 1
        final_status = SessionStatus.FAILED

    # 10. Generate session handoff
    print("📋 Step 7: Generating session handoff...")
    session_id = str(uuid.uuid4())[:8]

    # Build SessionResult
    accomplished = []
    incomplete = []
    blockers = []

    if verdict.type.value == "PASS":
        accomplished.append(f"Applied fix to {args.file}")
        accomplished.append(f"All Ralph verification steps passed")
    else:
        incomplete.append(f"Fix applied but verification failed")
        if verdict.type.value == "BLOCKED":
            blockers.append(f"Guardrail violation: {verdict.reason}")
        else:
            blockers.append(f"Verification failure: {verdict.reason}")

    session_result = SessionResult(
        task_id=args.bug_id,
        status=final_status,
        accomplished=accomplished,
        incomplete=incomplete,
        blockers=blockers,
        file_changes=[FileChange(file=args.file, action="Modified", lines_added=len(args.new_code.split('\n')), lines_removed=len(args.old_code.split('\n')))],
        verdict=verdict,
        handoff_notes=f"Fixed bug {args.bug_id} in {args.file}. {'Ready for merge.' if verdict.type.value == 'PASS' else 'Needs attention before merge.'}",
        regression_risk="LOW" if verdict.type.value == "PASS" else "HIGH",
        merge_confidence="HIGH" if verdict.type.value == "PASS" else "LOW",
        requires_review=True
    )

    handoff_path = create_session_handoff(session_id, "bugfix", session_result)
    print(f"   ✅ Session handoff created: {handoff_path}\n")

    return exit_code


def run_codequality(args: argparse.Namespace) -> int:
    """
    Run CodeQuality agent with full governance.

    Returns:
        0 if successful, 1 if failed
    """
    print(f"\n{'='*80}")
    print(f"🤖 Running CodeQuality Agent")
    print(f"{'='*80}\n")

    # Similar governance checks as bugfix...
    print("📋 Step 1: Checking kill-switch...")
    try:
        mode.require_normal()
        print("   ✅ Kill-switch: NORMAL\n")
    except Exception as e:
        print(f"   ❌ Kill-switch: {e}\n")
        return 1

    # Load adapter
    if args.project == "karematch":
        adapter = KareMatchAdapter()
    elif args.project == "credentialmate":
        adapter = CredentialMateAdapter()
    else:
        print(f"❌ Unknown project: {args.project}\n")
        return 1

    # Initialize agent
    agent = CodeQualityAgent(adapter)

    # Execute
    result = agent.execute(target_count=args.target_count)

    print(f"\n📊 CodeQuality Result:")
    print(f"   Status: {result['status']}")
    print(f"   Fixes applied: {result.get('fixes_applied', 0)}")
    print(f"   Batches processed: {result.get('batches_processed', 0)}\n")

    return 0 if result['status'] == 'completed' else 1


def main():
    parser = argparse.ArgumentParser(description="Run AI agents with governance")
    subparsers = parser.add_subparsers(dest="agent", required=True)

    # BugFix agent
    bugfix_parser = subparsers.add_parser("bugfix", help="Run BugFix agent")
    bugfix_parser.add_argument("--bug-id", required=True, help="Bug identifier")
    bugfix_parser.add_argument("--project", default="karematch", help="Project name")
    bugfix_parser.add_argument("--file", required=True, help="File to fix")
    bugfix_parser.add_argument("--old-code", required=True, help="Code to replace")
    bugfix_parser.add_argument("--new-code", required=True, help="New code")

    # CodeQuality agent
    quality_parser = subparsers.add_parser("codequality", help="Run CodeQuality agent")
    quality_parser.add_argument("--project", default="karematch", help="Project name")
    quality_parser.add_argument("--target-count", type=int, default=10, help="Number of issues to fix")

    args = parser.parse_args()

    # Route to appropriate agent
    if args.agent == "bugfix":
        return run_bugfix(args)
    elif args.agent == "codequality":
        return run_codequality(args)
    else:
        print(f"Unknown agent: {args.agent}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
