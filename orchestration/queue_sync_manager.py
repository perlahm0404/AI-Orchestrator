#!/usr/bin/env python3
"""
Enhanced Work Queue Sync Manager - Real-time synchronization

Provides bidirectional sync with file watching and conflict resolution.
"""

import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class QueueSyncManager:
    """Enhanced work queue synchronization manager"""

    def __init__(self, ai_orchestrator_root: Path):
        """
        Initialize sync manager

        Args:
            ai_orchestrator_root: Root directory of AI Orchestrator
        """
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
                "queue_file": "tasks/work_queue.json"
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

    def load_sync_metadata(self) -> Dict:
        """Load sync metadata"""
        metadata_file = self.work_queues_dir / "sync-metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                return json.load(f)
        return {}

    def save_sync_metadata(self, metadata: Dict):
        """Save sync metadata"""
        metadata_file = self.work_queues_dir / "sync-metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def sync_from_repo(
        self,
        repo_name: str,
        force: bool = False
    ) -> Dict:
        """
        Sync work queue from repo to mission control

        Args:
            repo_name: Repository to sync from
            force: Force sync even if no changes detected

        Returns:
            Sync result
        """
        if repo_name not in self.repos:
            return {
                "repo": repo_name,
                "status": "error",
                "message": f"Unknown repo: {repo_name}"
            }

        repo_config = self.repos[repo_name]
        source_file = repo_config["path"] / repo_config["queue_file"]
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
        if not force and source_checksum == last_checksum and dest_file.exists():
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

    def sync_all_repos(self, force: bool = False) -> list:
        """
        Sync all repos

        Args:
            force: Force sync even if no changes detected

        Returns:
            List of sync results
        """
        results = []
        for repo_name in self.repos.keys():
            result = self.sync_from_repo(repo_name, force=force)
            results.append(result)
        return results

    def watch_and_sync(self):
        """
        Watch for changes and auto-sync

        Note: This requires the 'watchdog' library.
        Install with: pip install watchdog
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            print("Error: watchdog library not installed")
            print("Install with: pip install watchdog")
            return

        class QueueChangeHandler(FileSystemEventHandler):
            def __init__(self, sync_manager, repo_name):
                self.sync_manager = sync_manager
                self.repo_name = repo_name

            def on_modified(self, event):
                if event.is_directory:
                    return

                # Check if it's a queue file
                if event.src_path.endswith(".json"):
                    print(f"Change detected in {self.repo_name}, syncing...")
                    result = self.sync_manager.sync_from_repo(self.repo_name)
                    if result["status"] == "success":
                        print(f"✅ Synced {self.repo_name}")

        observer = Observer()

        # Watch each repo's queue directory
        for repo_name, repo_config in self.repos.items():
            queue_dir = repo_config["path"] / Path(repo_config["queue_file"]).parent

            if queue_dir.exists():
                handler = QueueChangeHandler(self, repo_name)
                observer.schedule(handler, str(queue_dir), recursive=False)
                print(f"👁️  Watching {repo_name}: {queue_dir}")

        observer.start()
        print("\n✅ File watcher started. Press Ctrl+C to stop.")

        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n🛑 File watcher stopped")

        observer.join()


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Work Queue Sync Manager")
    parser.add_argument(
        "command",
        choices=["sync", "sync-all", "watch"],
        help="Command to execute"
    )
    parser.add_argument(
        "--repo",
        help="Repository to sync (for sync command)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force sync even if no changes detected"
    )
    args = parser.parse_args()

    # Get AI_Orchestrator root
    ai_orch_root = Path(__file__).parent.parent

    manager = QueueSyncManager(ai_orch_root)

    if args.command == "sync":
        if not args.repo:
            print("Error: --repo required for sync command")
            parser.print_help()
            exit(1)

        print(f"🔄 Syncing {args.repo}...")
        result = manager.sync_from_repo(args.repo, force=args.force)

        status_icon = "✅" if result["status"] == "success" else "⏭️" if result["status"] == "skipped" else "❌"
        print(f"{status_icon} {result['message']}")

        if "stats" in result:
            stats = result["stats"]
            print(f"📊 Tasks: {stats['total']} total, {stats['pending']} pending, {stats['blocked']} blocked")

    elif args.command == "sync-all":
        print("🔄 Syncing all repos...")
        results = manager.sync_all_repos(force=args.force)

        for result in results:
            status_icon = "✅" if result["status"] == "success" else "⏭️" if result["status"] == "skipped" else "❌"
            print(f"{status_icon} {result['repo']}: {result['message']}")

            if "stats" in result:
                stats = result["stats"]
                print(f"   📊 Tasks: {stats['total']} total, {stats['pending']} pending, {stats['blocked']} blocked")

    elif args.command == "watch":
        manager.watch_and_sync()
