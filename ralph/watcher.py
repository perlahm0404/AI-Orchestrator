#!/usr/bin/env python3
"""
Ralph File Watcher - Real-time verification daemon.

Watches for file changes and runs Ralph verification based on risk level:
- CRITICAL: Blocks immediately, reverts change, notifies
- HIGH: Verifies within seconds, auto-reverts on BLOCKED

Usage:
    # Start watcher for KareMatch
    python -m ralph.watcher --project karematch

    # Start with verbose output
    python -m ralph.watcher --project karematch --verbose

    # Run as daemon
    python -m ralph.watcher --project karematch --daemon
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from ralph.risk import classify_risk, RiskLevel, requires_immediate_verification
from ralph.engine import verify, VerdictType
from adapters import get_adapter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [RALPH] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class RalphEventHandler(FileSystemEventHandler):
    """Handles file system events and triggers Ralph verification."""

    def __init__(self, project: str, app_context, verbose: bool = False):
        super().__init__()
        self.project = project
        self.app_context = app_context
        self.project_path = Path(app_context.project_path)
        self.verbose = verbose

        # Debounce: track recently verified files
        self._recent_verifications: dict[str, float] = {}
        self._debounce_seconds = 2.0

        # Track verification stats
        self.stats = {
            "files_checked": 0,
            "verifications_run": 0,
            "blocks_issued": 0,
            "reverts_performed": 0,
        }

    def _should_verify(self, file_path: str) -> bool:
        """Check if file should be verified (debouncing)."""
        now = time.time()
        last_check = self._recent_verifications.get(file_path, 0)

        if now - last_check < self._debounce_seconds:
            return False

        self._recent_verifications[file_path] = now
        return True

    def _get_relative_path(self, absolute_path: str) -> str:
        """Convert absolute path to relative path from project root."""
        try:
            return str(Path(absolute_path).relative_to(self.project_path))
        except ValueError:
            return absolute_path

    def _is_ignored(self, path: str) -> bool:
        """Check if path should be ignored."""
        ignore_patterns = [
            ".git",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".venv",
            "venv",
            ".env",
            "*.pyc",
            "*.pyo",
            ".DS_Store",
            "*.log",
        ]

        for pattern in ignore_patterns:
            if pattern in path:
                return True
        return False

    def _revert_file(self, file_path: str) -> bool:
        """Revert a file to its git HEAD state."""
        try:
            result = subprocess.run(
                ["git", "checkout", "HEAD", "--", file_path],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to revert {file_path}: {e}")
            return False

    def _notify_block(self, file_path: str, reason: str) -> None:
        """Notify about a blocked change."""
        logger.warning(f"🚫 BLOCKED: {file_path}")
        logger.warning(f"   Reason: {reason}")

        # Could also send to a webhook, write to a file, etc.
        notification_file = self.project_path / ".ralph_notifications.log"
        with open(notification_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} | BLOCKED | {file_path} | {reason}\n")

    def _run_quick_verify(self, file_path: str) -> Optional[VerdictType]:
        """Run quick verification on a single file."""
        try:
            verdict = verify(
                project=self.project,
                changes=[file_path],
                session_id=f"watcher-{int(time.time())}",
                app_context=self.app_context
            )
            return verdict.type
        except Exception as e:
            logger.error(f"Verification error for {file_path}: {e}")
            return None

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        self._handle_file_change(event.src_path)

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        self._handle_file_change(event.src_path)

    def _handle_file_change(self, absolute_path: str):
        """Process a file change event."""
        if self._is_ignored(absolute_path):
            return

        relative_path = self._get_relative_path(absolute_path)

        if not self._should_verify(relative_path):
            return

        self.stats["files_checked"] += 1
        risk_level = classify_risk(relative_path)

        if self.verbose:
            logger.info(f"Change detected: {relative_path} (risk: {risk_level.value})")

        # CRITICAL: Always block and revert
        if risk_level == RiskLevel.CRITICAL:
            logger.warning(f"⚠️  CRITICAL file modified: {relative_path}")
            self._notify_block(relative_path, "Critical file requires human approval")
            self.stats["blocks_issued"] += 1

            # Revert the change
            if self._revert_file(relative_path):
                logger.info(f"   ↩️  Reverted to HEAD")
                self.stats["reverts_performed"] += 1
            else:
                logger.error(f"   ❌ Failed to revert!")

            return

        # HIGH: Verify immediately
        if risk_level == RiskLevel.HIGH:
            if self.verbose:
                logger.info(f"Running immediate verification for: {relative_path}")

            self.stats["verifications_run"] += 1
            verdict_type = self._run_quick_verify(relative_path)

            if verdict_type == VerdictType.BLOCKED:
                logger.warning(f"🚫 BLOCKED by guardrails: {relative_path}")
                self._notify_block(relative_path, "Guardrail violation detected")
                self.stats["blocks_issued"] += 1

                if self._revert_file(relative_path):
                    logger.info(f"   ↩️  Auto-reverted")
                    self.stats["reverts_performed"] += 1

            elif verdict_type == VerdictType.FAIL:
                logger.warning(f"⚠️  Verification failed: {relative_path}")
                # Don't auto-revert on FAIL, just warn

            elif verdict_type == VerdictType.PASS:
                if self.verbose:
                    logger.info(f"✅ Verified: {relative_path}")

        # MEDIUM/LOW: Just log, will be caught at commit time
        elif self.verbose:
            logger.debug(f"Skipping immediate verification for {risk_level.value} file: {relative_path}")


def run_watcher(project: str, verbose: bool = False):
    """Run the file watcher for a project."""
    if not WATCHDOG_AVAILABLE:
        logger.error("watchdog package not installed. Run: pip install watchdog")
        sys.exit(1)

    # Get adapter
    try:
        adapter = get_adapter(project)
        app_context = adapter.get_context()
    except Exception as e:
        logger.error(f"Failed to load adapter for '{project}': {e}")
        sys.exit(1)

    project_path = Path(app_context.project_path)

    logger.info(f"{'='*60}")
    logger.info(f"RALPH FILE WATCHER")
    logger.info(f"{'='*60}")
    logger.info(f"Project: {project}")
    logger.info(f"Path: {project_path}")
    logger.info(f"Verbose: {verbose}")
    logger.info(f"{'='*60}")
    logger.info(f"Watching for changes... (Ctrl+C to stop)")
    logger.info("")

    event_handler = RalphEventHandler(project, app_context, verbose)
    observer = Observer()
    observer.schedule(event_handler, str(project_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("")
        logger.info(f"{'='*60}")
        logger.info("WATCHER STOPPED")
        logger.info(f"{'='*60}")
        logger.info(f"Stats:")
        logger.info(f"  Files checked: {event_handler.stats['files_checked']}")
        logger.info(f"  Verifications: {event_handler.stats['verifications_run']}")
        logger.info(f"  Blocks issued: {event_handler.stats['blocks_issued']}")
        logger.info(f"  Reverts: {event_handler.stats['reverts_performed']}")

    observer.join()


def main():
    parser = argparse.ArgumentParser(description="Ralph file watcher daemon")
    parser.add_argument("--project", required=True, help="Project name (karematch, credentialmate)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon (background)")

    args = parser.parse_args()

    if args.daemon:
        # Fork to background (Unix only)
        if os.name != 'nt':
            pid = os.fork()
            if pid > 0:
                print(f"Ralph watcher started as daemon (PID: {pid})")
                sys.exit(0)

    run_watcher(args.project, args.verbose)


if __name__ == "__main__":
    main()
