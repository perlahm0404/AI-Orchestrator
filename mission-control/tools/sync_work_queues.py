#!/usr/bin/env python3
"""
Work Queue Sync Tool - Syncs work queues from target repos to mission-control

Usage:
    python mission-control/tools/sync_work_queues.py --all
    python mission-control/tools/sync_work_queues.py --project karematch
"""

import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, List, Optional
import argparse


class WorkQueueSync:
    """Syncs work queues from target repos to mission-control"""

    def __init__(self, ai_orchestrator_root: Path):
        self.root = ai_orchestrator_root
        self.mission_control = self.root / "mission-control"
        self.work_queues_dir = self.mission_control / "work-queues"

        # Ensure directories exist
        self.work_queues_dir.mkdir(parents=True, exist_ok=True)

        # Repo configurations
        self.repos = {
            "karematch": {
                "path": Path("/Users/tmac/1_REPOS/karematch"),
                "queue_file": "tasks/work_queue_karematch.json"
            },
            "credentialmate": {
                "path": Path("/Users/tmac/1_REPOS/credentialmate"),
                "queue_file": "tasks/work_queue.json"  # Note: different naming
            },
            "ai-orchestrator": {
                "path": self.root,
                "queue_file": "tasks/work_queue_ai-orchestrator.json"
            }
        }

    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        if not file_path.exists():
            return ""

        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def load_sync_metadata(self) -> dict[str, Any]:
        """Load sync metadata (last sync times, checksums)"""
        metadata_file = self.work_queues_dir / "sync-metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        return {}

    def save_sync_metadata(self, metadata: dict[str, Any]) -> None:
        """Save sync metadata"""
        metadata_file = self.work_queues_dir / "sync-metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def sync_repo(self, repo_name: str) -> dict[str, Any]:
        """Sync work queue from a specific repo"""
        if repo_name not in self.repos:
            return {
                "repo": repo_name,
                "status": "error",
                "message": f"Unknown repo: {repo_name}"
            }

        repo_config = self.repos[repo_name]
        repo_path: Path = repo_config["path"]  # type: ignore
        source_file = repo_path / str(repo_config["queue_file"])
        dest_file = self.work_queues_dir / f"{repo_name}.json"

        # Check if source exists
        if not source_file.exists():
            return {
                "repo": repo_name,
                "status": "error",
                "message": f"Source file not found: {source_file}"
            }

        # Calculate checksums
        source_checksum = self.calculate_checksum(source_file)

        # Load metadata to check if sync needed
        metadata = self.load_sync_metadata()
        repo_metadata = metadata.get(repo_name, {})
        last_checksum = repo_metadata.get("checksum", "")

        # Check if changed
        if source_checksum == last_checksum and dest_file.exists():
            return {
                "repo": repo_name,
                "status": "skipped",
                "message": "No changes detected",
                "checksum": source_checksum
            }

        # Copy file
        try:
            shutil.copy2(source_file, dest_file)

            # Verify copy
            dest_checksum = self.calculate_checksum(dest_file)
            if dest_checksum != source_checksum:
                return {
                    "repo": repo_name,
                    "status": "error",
                    "message": "Checksum mismatch after copy"
                }

            # Update metadata
            metadata[repo_name] = {
                "source_path": str(source_file),
                "last_sync": datetime.now().isoformat(),
                "checksum": source_checksum,
                "status": "success"
            }
            self.save_sync_metadata(metadata)

            # Parse queue to get stats
            with open(dest_file) as f:
                queue_data = json.load(f)
                tasks = queue_data.get("features", [])
                stats = {
                    "total": len(tasks),
                    "pending": sum(1 for t in tasks if t.get("status") == "pending"),
                    "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
                    "blocked": sum(1 for t in tasks if t.get("status") == "blocked"),
                    "completed": sum(1 for t in tasks if t.get("status") == "completed")
                }

            return {
                "repo": repo_name,
                "status": "success",
                "message": "Synced successfully",
                "checksum": source_checksum,
                "stats": stats
            }

        except Exception as e:
            return {
                "repo": repo_name,
                "status": "error",
                "message": f"Failed to copy: {str(e)}"
            }

    def sync_all(self) -> list[dict[str, Any]]:
        """Sync all repos"""
        results = []
        for repo_name in self.repos.keys():
            result = self.sync_repo(repo_name)
            results.append(result)
        return results

    def generate_aggregate_view(self) -> dict[str, Any]:
        """Generate aggregate view of all work queues"""
        aggregate: dict[str, Any] = {
            "last_sync": datetime.now().isoformat(),
            "repos": {},
            "summary": {
                "total_tasks": 0,
                "pending": 0,
                "in_progress": 0,
                "blocked": 0,
                "completed": 0
            },
            "alerts": []
        }

        # Load each repo's queue
        for repo_name in self.repos.keys():
            queue_file = self.work_queues_dir / f"{repo_name}.json"
            if not queue_file.exists():
                continue

            try:
                with open(queue_file) as f:
                    queue_data = json.load(f)
                    tasks = queue_data.get("features", [])

                    stats = {
                        "total": len(tasks),
                        "pending": sum(1 for t in tasks if t.get("status") == "pending"),
                        "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
                        "blocked": sum(1 for t in tasks if t.get("status") == "blocked"),
                        "completed": sum(1 for t in tasks if t.get("status") == "completed"),
                        "last_updated": datetime.now().isoformat()
                    }

                    aggregate["repos"][repo_name] = stats

                    # Update summary
                    aggregate["summary"]["total_tasks"] += stats["total"]
                    aggregate["summary"]["pending"] += stats["pending"]
                    aggregate["summary"]["in_progress"] += stats["in_progress"]
                    aggregate["summary"]["blocked"] += stats["blocked"]
                    aggregate["summary"]["completed"] += stats["completed"]

                    # Check for alerts (tasks blocked >3 days)
                    for task in tasks:
                        if task.get("status") == "blocked":
                            # Calculate duration if timestamp available
                            if "updated_at" in task:
                                # Simplified: just flag all blocked tasks
                                aggregate["alerts"].append({
                                    "type": "blocked_task",
                                    "task_id": task.get("id", "unknown"),
                                    "repo": repo_name,
                                    "title": task.get("title", "Untitled")
                                })

            except Exception as e:
                print(f"Warning: Failed to process {repo_name}: {e}")
                continue

        # Save aggregate view
        aggregate_file = self.work_queues_dir / "aggregate-view.json"
        with open(aggregate_file, "w") as f:
            json.dump(aggregate, f, indent=2)

        return aggregate


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync work queues from target repos")
    parser.add_argument("--all", action="store_true", help="Sync all repos")
    parser.add_argument("--project", type=str, help="Sync specific project (karematch, credentialmate, ai-orchestrator)")
    args = parser.parse_args()

    # Get AI_Orchestrator root
    ai_orch_root = Path(__file__).parent.parent.parent

    syncer = WorkQueueSync(ai_orch_root)

    if args.all:
        print("🔄 Syncing all repos...")
        results = syncer.sync_all()
        for result in results:
            status_icon = "✅" if result["status"] == "success" else "⏭️" if result["status"] == "skipped" else "❌"
            print(f"{status_icon} {result['repo']}: {result['message']}")
            if "stats" in result:
                stats = result["stats"]
                print(f"   📊 Tasks: {stats['total']} total, {stats['pending']} pending, {stats['blocked']} blocked")

        # Generate aggregate view
        print("\n📊 Generating aggregate view...")
        aggregate = syncer.generate_aggregate_view()
        print(f"✅ Aggregate view updated:")
        print(f"   Total tasks across all repos: {aggregate['summary']['total_tasks']}")
        print(f"   Pending: {aggregate['summary']['pending']}, In Progress: {aggregate['summary']['in_progress']}")
        print(f"   Blocked: {aggregate['summary']['blocked']}, Completed: {aggregate['summary']['completed']}")

        if aggregate["alerts"]:
            print(f"\n⚠️  {len(aggregate['alerts'])} alert(s) detected")

    elif args.project:
        print(f"🔄 Syncing {args.project}...")
        result = syncer.sync_repo(args.project)
        status_icon = "✅" if result["status"] == "success" else "⏭️" if result["status"] == "skipped" else "❌"
        print(f"{status_icon} {result['message']}")
        if "stats" in result:
            stats = result["stats"]
            print(f"📊 Tasks: {stats['total']} total, {stats['pending']} pending, {stats['blocked']} blocked")

        # Regenerate aggregate view
        syncer.generate_aggregate_view()
        print("✅ Aggregate view updated")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
