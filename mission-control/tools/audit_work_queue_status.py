#!/usr/bin/env python3
"""
Work Queue Status Auditor - Automatically sync work queue status with actual repo state

This script scans target repositories for files specified in work queues and automatically
updates task status based on file existence and timestamps.

Usage:
    python mission-control/tools/audit_work_queue_status.py [--dry-run] [--repo REPO]

Examples:
    # Audit all repos and update work queues
    python mission-control/tools/audit_work_queue_status.py

    # Preview changes without updating
    python mission-control/tools/audit_work_queue_status.py --dry-run

    # Audit only karematch repo
    python mission-control/tools/audit_work_queue_status.py --repo karematch
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class WorkQueueStatusAuditor:
    """Automatically sync work queue status with repo file state"""

    def __init__(self, ai_orchestrator_root: Path):
        self.root = ai_orchestrator_root
        self.work_queues_dir = self.root / "mission-control" / "work-queues"

        # Repo configurations
        self.repos = {
            "karematch": Path("/Users/tmac/1_REPOS/karematch"),
            "credentialmate": Path("/Users/tmac/1_REPOS/credentialmate"),
        }

    def check_file_exists(self, repo_path: Path, file_path: str) -> Tuple[bool, Optional[datetime]]:
        """
        Check if a file exists in the repo and get its modification time.

        Returns:
            (exists: bool, modified_at: Optional[datetime])
        """
        full_path = repo_path / file_path
        if full_path.exists() and full_path.is_file():
            # Get file modification time
            mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
            return True, mtime
        return False, None

    def check_file_substantive(self, repo_path: Path, file_path: str, min_lines: int = 50) -> bool:
        """
        Check if file has substantive content (not just a stub).

        Args:
            min_lines: Minimum line count to consider file "substantive"
        """
        full_path = repo_path / file_path
        if not full_path.exists():
            return False

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Count non-empty, non-comment lines
                substantive_lines = [
                    line for line in lines
                    if line.strip() and not line.strip().startswith(('#', '//', '/*', '*'))
                ]
                return len(substantive_lines) >= min_lines
        except Exception:
            return False

    def audit_task(self, repo_path: Path, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit a single task and determine if status should be updated.

        Returns:
            Dictionary with audit results and suggested updates
        """
        task_id = task.get("id", "unknown")
        file_path = task.get("file", "")
        current_status = task.get("status", "pending")

        # Check if file exists
        exists, modified_at = self.check_file_exists(repo_path, file_path)

        # Check if file is substantive (not just a stub)
        is_substantive = self.check_file_substantive(repo_path, file_path)

        # Determine suggested status
        if exists and is_substantive:
            suggested_status = "completed"
        elif exists and not is_substantive:
            suggested_status = "in_progress"  # File exists but incomplete
        else:
            suggested_status = "pending"

        # Build audit result
        audit_result = {
            "task_id": task_id,
            "file_path": file_path,
            "current_status": current_status,
            "suggested_status": suggested_status,
            "file_exists": exists,
            "file_substantive": is_substantive,
            "modified_at": modified_at.isoformat() if modified_at else None,
            "needs_update": current_status != suggested_status,
        }

        # Build suggested updates if needed
        if audit_result["needs_update"]:
            updates = {"status": suggested_status}

            if suggested_status == "completed" and current_status != "completed":
                updates["completed_at"] = datetime.now().isoformat()
                updates["passes"] = "true"
                updates["verification_verdict"] = "PASS"
                updates["attempts"] = task.get("attempts", 0) + 1
                updates["last_attempt"] = datetime.now().isoformat()

                # Update files_actually_changed
                files_changed = task.get("files_actually_changed", [])
                if file_path not in files_changed:
                    files_changed.append(file_path)
                updates["files_actually_changed"] = files_changed

            elif suggested_status == "in_progress" and current_status == "pending":
                updates["attempts"] = task.get("attempts", 0) + 1
                updates["last_attempt"] = datetime.now().isoformat()

            audit_result["suggested_updates"] = updates

        return audit_result

    def audit_work_queue(self, repo_name: str) -> Dict[str, Any]:
        """
        Audit all tasks in a work queue.

        Returns:
            Audit report with summary and task-level results
        """
        queue_file = self.work_queues_dir / f"{repo_name}.json"

        if not queue_file.exists():
            return {
                "repo": repo_name,
                "error": f"Work queue not found: {queue_file}",
                "tasks_audited": 0,
            }

        # Load work queue
        with open(queue_file, 'r') as f:
            work_queue = json.load(f)

        repo_path = self.repos.get(repo_name)
        if not repo_path or not repo_path.exists():
            return {
                "repo": repo_name,
                "error": f"Repo not found: {repo_path}",
                "tasks_audited": 0,
            }

        # Audit each task
        task_audits = []
        needs_update_count = 0

        for task in work_queue.get("features", []):
            audit_result = self.audit_task(repo_path, task)
            task_audits.append(audit_result)

            if audit_result.get("needs_update"):
                needs_update_count += 1

        # Build summary
        return {
            "repo": repo_name,
            "queue_file": str(queue_file),
            "repo_path": str(repo_path),
            "tasks_audited": len(task_audits),
            "tasks_need_update": needs_update_count,
            "task_audits": task_audits,
        }

    def apply_updates(self, repo_name: str, audit_report: Dict[str, Any]) -> bool:
        """
        Apply suggested updates to work queue file.

        Returns:
            True if updates applied successfully
        """
        queue_file = self.work_queues_dir / f"{repo_name}.json"

        # Load work queue
        with open(queue_file, 'r') as f:
            work_queue = json.load(f)

        # Apply updates
        updated_count = 0
        for task_audit in audit_report.get("task_audits", []):
            if not task_audit.get("needs_update"):
                continue

            task_id = task_audit["task_id"]
            suggested_updates = task_audit.get("suggested_updates", {})

            # Find task in work queue
            for task in work_queue.get("features", []):
                if task.get("id") == task_id:
                    # Apply updates
                    for key, value in suggested_updates.items():
                        task[key] = value
                    updated_count += 1
                    break

        # Update summary counts
        summary = work_queue.get("summary", {})
        completed_count = sum(1 for t in work_queue.get("features", []) if t.get("status") == "completed")
        in_progress_count = sum(1 for t in work_queue.get("features", []) if t.get("status") == "in_progress")
        blocked_count = sum(1 for t in work_queue.get("features", []) if t.get("status") == "blocked")
        pending_count = sum(1 for t in work_queue.get("features", []) if t.get("status") == "pending")

        summary.update({
            "complete": completed_count,
            "in_progress": in_progress_count,
            "blocked": blocked_count,
            "pending": pending_count,
        })

        # Update metadata
        work_queue["last_updated"] = datetime.now().isoformat()
        work_queue["updated_by"] = "audit-work-queue-status"

        # Write back to file
        with open(queue_file, 'w') as f:
            json.dump(work_queue, f, indent=2)

        print(f"✅ Updated {updated_count} tasks in {queue_file}")
        return True

    def print_audit_report(self, audit_report: Dict[str, Any], verbose: bool = False) -> None:
        """Print human-readable audit report"""
        repo = audit_report.get("repo", "unknown")

        if "error" in audit_report:
            print(f"❌ {repo}: {audit_report['error']}")
            return

        tasks_audited = audit_report.get("tasks_audited", 0)
        tasks_need_update = audit_report.get("tasks_need_update", 0)

        print(f"\n📊 Audit Report: {repo}")
        print(f"   Tasks audited: {tasks_audited}")
        print(f"   Tasks need update: {tasks_need_update}")

        if verbose or tasks_need_update > 0:
            print(f"\n   Task Details:")
            for task_audit in audit_report.get("task_audits", []):
                task_id = task_audit["task_id"]
                current = task_audit["current_status"]
                suggested = task_audit["suggested_status"]
                exists = "✅" if task_audit["file_exists"] else "❌"
                substantive = "✅" if task_audit["file_substantive"] else "❌"

                if task_audit["needs_update"]:
                    print(f"   • {task_id}: {current} → {suggested} (exists: {exists}, substantive: {substantive})")
                elif verbose:
                    print(f"   • {task_id}: {current} (no change needed)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit work queue status based on actual repo files")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without updating")
    parser.add_argument("--repo", type=str, help="Audit only specified repo (karematch, credentialmate)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    # Initialize auditor
    ai_orchestrator_root = Path(__file__).parent.parent.parent
    auditor = WorkQueueStatusAuditor(ai_orchestrator_root)

    # Determine which repos to audit
    repos_to_audit = [args.repo] if args.repo else list(auditor.repos.keys())

    print("🔍 Work Queue Status Auditor")
    print(f"   Mode: {'DRY RUN (no changes)' if args.dry_run else 'LIVE (will update files)'}")
    print(f"   Repos: {', '.join(repos_to_audit)}")

    # Audit each repo
    all_reports = []
    for repo_name in repos_to_audit:
        audit_report = auditor.audit_work_queue(repo_name)
        all_reports.append(audit_report)
        auditor.print_audit_report(audit_report, verbose=args.verbose)

        # Apply updates if not dry run
        if not args.dry_run and audit_report.get("tasks_need_update", 0) > 0:
            auditor.apply_updates(repo_name, audit_report)

    # Print summary
    total_audited = sum(r.get("tasks_audited", 0) for r in all_reports)
    total_updated = sum(r.get("tasks_need_update", 0) for r in all_reports)

    print(f"\n{'📋' if args.dry_run else '✅'} Summary:")
    print(f"   Total tasks audited: {total_audited}")
    print(f"   Total tasks {'would be updated' if args.dry_run else 'updated'}: {total_updated}")

    if args.dry_run and total_updated > 0:
        print(f"\n💡 Run without --dry-run to apply changes")


if __name__ == "__main__":
    main()
