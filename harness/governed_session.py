#!/usr/bin/env python3
"""
Governed Session Harness

Wraps Claude Code sessions with governance enforcement.

Layers of protection (defense in depth):
1. PRE-CHECK: Critical files blocked before Claude can touch them
2. REAL-TIME: File watcher catches high-risk changes immediately
3. POST-TASK: Ralph verification after each task
4. COMMIT-TIME: Git pre-commit hook as final gate

Usage:
    # Run a governed bug-fix session
    python -m harness.governed_session --project karematch --task "Fix the auth bug in login.ts"

    # Run with watcher (real-time protection)
    python -m harness.governed_session --project karematch --task "Fix bugs" --with-watcher

    # Dry run (show what would happen)
    python -m harness.governed_session --project karematch --task "Fix bugs" --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from ralph.engine import verify, VerdictType
from ralph.risk import classify_files, RiskLevel, get_highest_risk
from governance.kill_switch import mode
from governance import contract
from adapters import get_adapter


@dataclass
class SessionConfig:
    """Configuration for a governed session."""
    project: str
    task: str
    agent_type: str = "bugfix"
    max_retries: int = 3
    timeout_minutes: int = 30
    with_watcher: bool = False
    dry_run: bool = False


@dataclass
class SessionResult:
    """Result of a governed session."""
    success: bool
    verdict_type: Optional[VerdictType]
    changes: list[str]
    duration_seconds: float
    error: Optional[str] = None
    reverted: bool = False


class GovernedSession:
    """
    Manages a governed Claude Code session with tiered verification.
    """

    def __init__(self, config: SessionConfig):
        self.config = config
        self.adapter = get_adapter(config.project)
        self.app_context = self.adapter.get_context()
        self.project_path = Path(self.app_context.project_path)

        # Load contract for agent type
        self.contract = contract.load(config.agent_type)

        # Session tracking
        self.session_id = f"session-{int(time.time())}"
        self.start_time: Optional[float] = None
        self.watcher_process: Optional[subprocess.Popen] = None

        # Audit log
        self.audit_log: list[dict] = []

    def _log(self, event: str, details: dict = None):
        """Log an event to the audit trail."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event": event,
            "details": details or {}
        }
        self.audit_log.append(entry)
        print(f"[{entry['timestamp']}] {event}: {json.dumps(details or {})}")

    def _check_kill_switch(self) -> bool:
        """Check if kill switch allows operation."""
        try:
            mode.require_normal()
            return True
        except Exception as e:
            self._log("KILL_SWITCH_BLOCKED", {"error": str(e)})
            return False

    def _get_changed_files(self) -> list[str]:
        """Get list of files changed since session start."""
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

    def _check_critical_files(self, files: list[str]) -> tuple[bool, list[str]]:
        """Check if any critical files were modified (should be blocked)."""
        classified = classify_files(files)
        critical_files = classified.get(RiskLevel.CRITICAL, [])
        return len(critical_files) == 0, critical_files

    def _revert_all_changes(self) -> bool:
        """Revert all uncommitted changes."""
        try:
            subprocess.run(
                ["git", "checkout", "HEAD", "--", "."],
                cwd=self.project_path,
                check=True
            )
            subprocess.run(
                ["git", "clean", "-fd"],
                cwd=self.project_path,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _start_watcher(self):
        """Start the Ralph file watcher in background."""
        if not self.config.with_watcher:
            return

        self._log("WATCHER_STARTING", {"project": self.config.project})

        orchestrator_path = Path(__file__).parent.parent
        python_path = orchestrator_path / ".venv" / "bin" / "python"

        self.watcher_process = subprocess.Popen(
            [
                str(python_path),
                "-m", "ralph.watcher",
                "--project", self.config.project,
                "--verbose"
            ],
            cwd=str(orchestrator_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        time.sleep(1)  # Give watcher time to start
        self._log("WATCHER_STARTED", {"pid": self.watcher_process.pid})

    def _stop_watcher(self):
        """Stop the file watcher."""
        if self.watcher_process:
            self._log("WATCHER_STOPPING", {"pid": self.watcher_process.pid})
            self.watcher_process.terminate()
            self.watcher_process.wait(timeout=5)
            self.watcher_process = None

    def _run_claude_code(self, task: str) -> tuple[bool, str]:
        """Run Claude Code with the given task."""
        self._log("CLAUDE_CODE_STARTING", {"task": task[:100]})

        # Build the prompt with governance instructions
        governed_prompt = f"""
You are operating under Ralph governance. Follow these rules:

1. DO NOT modify files matching these critical patterns:
   - **/migrations/**, .github/**, **/auth/**, **/*secret*
   - docker-compose*.yml, package-lock.json, yarn.lock

2. After making changes, run Ralph verification:
   cd {Path(__file__).parent.parent} && .venv/bin/python -m ralph.cli --all-changes --project {self.config.project}

3. If Ralph returns BLOCKED, revert your changes immediately.

4. Your task: {task}

Begin work now.
"""

        if self.config.dry_run:
            self._log("DRY_RUN", {"prompt": governed_prompt[:500]})
            return True, "Dry run - no actual execution"

        # Run Claude Code
        try:
            result = subprocess.run(
                [
                    "claude",
                    "--dangerously-skip-permissions",
                    "-p", governed_prompt
                ],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=self.config.timeout_minutes * 60
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Session timed out"
        except FileNotFoundError:
            return False, "Claude CLI not found"

    def _run_final_verification(self, changed_files: list[str]) -> VerdictType:
        """Run final Ralph verification on all changes."""
        if not changed_files:
            self._log("NO_CHANGES_TO_VERIFY")
            return VerdictType.PASS

        self._log("FINAL_VERIFICATION_STARTING", {"files": changed_files})

        verdict = verify(
            project=self.config.project,
            changes=changed_files,
            session_id=self.session_id,
            app_context=self.app_context
        )

        self._log("FINAL_VERIFICATION_COMPLETE", {
            "verdict": verdict.type.value,
            "reason": verdict.reason
        })

        return verdict.type

    def run(self) -> SessionResult:
        """
        Execute the governed session.

        Returns:
            SessionResult with outcome details
        """
        self.start_time = time.time()
        self._log("SESSION_STARTING", {
            "project": self.config.project,
            "task": self.config.task[:100],
            "agent_type": self.config.agent_type
        })

        # Pre-flight checks
        if not self._check_kill_switch():
            return SessionResult(
                success=False,
                verdict_type=None,
                changes=[],
                duration_seconds=time.time() - self.start_time,
                error="Kill switch is active"
            )

        # Start watcher if requested
        self._start_watcher()

        try:
            # Run Claude Code
            success, output = self._run_claude_code(self.config.task)

            if not success:
                self._log("CLAUDE_CODE_FAILED", {"output": output[:500]})

            # Get changed files
            changed_files = self._get_changed_files()
            self._log("CHANGES_DETECTED", {"files": changed_files})

            # Check for critical file violations
            critical_ok, critical_files = self._check_critical_files(changed_files)
            if not critical_ok:
                self._log("CRITICAL_FILE_VIOLATION", {"files": critical_files})
                self._revert_all_changes()
                return SessionResult(
                    success=False,
                    verdict_type=VerdictType.BLOCKED,
                    changes=changed_files,
                    duration_seconds=time.time() - self.start_time,
                    error=f"Critical files modified: {critical_files}",
                    reverted=True
                )

            # Run final verification
            verdict_type = self._run_final_verification(changed_files)

            # Handle verdict
            if verdict_type == VerdictType.BLOCKED:
                self._log("VERDICT_BLOCKED_REVERTING")
                self._revert_all_changes()
                return SessionResult(
                    success=False,
                    verdict_type=verdict_type,
                    changes=changed_files,
                    duration_seconds=time.time() - self.start_time,
                    error="Guardrail violation - changes reverted",
                    reverted=True
                )

            elif verdict_type == VerdictType.FAIL:
                self._log("VERDICT_FAILED", {"action": "keeping changes for review"})
                return SessionResult(
                    success=False,
                    verdict_type=verdict_type,
                    changes=changed_files,
                    duration_seconds=time.time() - self.start_time,
                    error="Verification failed - changes kept for manual review"
                )

            else:  # PASS
                self._log("SESSION_SUCCESS")
                return SessionResult(
                    success=True,
                    verdict_type=verdict_type,
                    changes=changed_files,
                    duration_seconds=time.time() - self.start_time
                )

        finally:
            self._stop_watcher()
            self._save_audit_log()

    def _save_audit_log(self):
        """Save audit log to file."""
        log_dir = Path(__file__).parent.parent / "audit" / "sessions"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{self.session_id}.json"
        with open(log_file, 'w') as f:
            json.dump(self.audit_log, f, indent=2)

        print(f"\nAudit log saved to: {log_file}")


def main():
    parser = argparse.ArgumentParser(description="Run a governed Claude Code session")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--task", required=True, help="Task description")
    parser.add_argument("--agent-type", default="bugfix", help="Agent type (bugfix, codequality)")
    parser.add_argument("--with-watcher", action="store_true", help="Run file watcher")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in minutes")

    args = parser.parse_args()

    config = SessionConfig(
        project=args.project,
        task=args.task,
        agent_type=args.agent_type,
        with_watcher=args.with_watcher,
        dry_run=args.dry_run,
        timeout_minutes=args.timeout
    )

    session = GovernedSession(config)
    result = session.run()

    print("\n" + "=" * 60)
    print("SESSION RESULT")
    print("=" * 60)
    print(f"Success: {result.success}")
    print(f"Verdict: {result.verdict_type.value if result.verdict_type else 'N/A'}")
    print(f"Changes: {len(result.changes)} files")
    print(f"Duration: {result.duration_seconds:.1f}s")
    if result.error:
        print(f"Error: {result.error}")
    if result.reverted:
        print("⚠️  Changes were reverted")
    print("=" * 60)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
