#!/usr/bin/env python3
"""
Kanban Aggregation Tool - Combines objectives, ADRs, and tasks from all repos

Usage:
    python mission-control/tools/aggregate_kanban.py
"""

import json
import yaml  # type: ignore
import re
from pathlib import Path
from datetime import datetime
from typing import Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Objective:
    """Represents a project objective"""
    id: str
    repo: str
    title: str
    status: str
    completion_pct: float
    tasks_total: int
    tasks_complete: int
    adrs: List[str]
    source_file: str


@dataclass
class ADR:
    """Represents an Architecture Decision Record"""
    id: str
    repo: str
    title: str
    file_path: str
    related_tasks: List[str]


@dataclass
class Task:
    """Represents a task from work queue"""
    id: str
    repo: str
    title: str
    status: str
    priority: str
    agent_type: Optional[str]
    adr_references: List[str]


class KanbanAggregator:
    """Aggregates kanban data from all repos"""

    def __init__(self, ai_orchestrator_root: Path):
        self.root = ai_orchestrator_root
        self.mission_control = self.root / "mission-control"
        self.work_queues_dir = self.mission_control / "work-queues"
        self.vibe_kanban_dir = self.mission_control / "vibe-kanban"

        # Ensure output directory exists
        self.vibe_kanban_dir.mkdir(parents=True, exist_ok=True)

        # Repo configurations
        self.repos = {
            "karematch": {
                "path": Path("/Users/tmac/1_REPOS/karematch"),
                "decisions_dir": "docs/decisions",
                "vibe_kanban": "vibe-kanban"
            },
            "credentialmate": {
                "path": Path("/Users/tmac/1_REPOS/credentialmate"),
                "decisions_dir": "docs/decisions",
                "vibe_kanban": "vibe-kanban"
            },
            "ai-orchestrator": {
                "path": self.root,
                "decisions_dir": "docs/decisions",
                "vibe_kanban": "vibe-kanban"
            }
        }

    def extract_adr_references(self, text: str) -> List[str]:
        """Extract ADR references from text (e.g., ADR-001, ADR-KM-002-005)"""
        # Pattern matches: ADR-001 or ADR-KM-002-001 (captures full ID)
        pattern = r'ADR-(?:[A-Z]+-)?(?:\d+-)?\d+'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return matches

    def load_tasks_from_queue(self, repo_name: str) -> List[Task]:
        """Load tasks from synced work queue"""
        queue_file = self.work_queues_dir / f"{repo_name}.json"
        if not queue_file.exists():
            return []

        try:
            with open(queue_file) as f:
                data = json.load(f)
                tasks = []

                for feature in data.get("features", []):
                    task_id = feature.get("id", "unknown")
                    description = feature.get("description", "")

                    # Extract ADR references from description
                    adr_refs = self.extract_adr_references(description)

                    task = Task(
                        id=task_id,
                        repo=repo_name,
                        title=feature.get("title", "Untitled"),
                        status=feature.get("status", "pending"),
                        priority=feature.get("priority", "P2"),
                        agent_type=feature.get("assigned_agent_type"),
                        adr_references=adr_refs
                    )
                    tasks.append(task)

                return tasks
        except Exception as e:
            print(f"Warning: Failed to load tasks from {repo_name}: {e}")
            return []

    def load_adrs_from_repo(self, repo_name: str) -> List[ADR]:
        """Load ADRs from repo's decisions directory and vibe-kanban/adrs"""
        repo_config = self.repos[repo_name]
        repo_path: Path = repo_config["path"]  # type: ignore

        adrs = []

        # Load from docs/decisions/ (markdown)
        decisions_dir = repo_path / str(repo_config["decisions_dir"])
        if decisions_dir.exists():
            for adr_file in decisions_dir.glob("ADR-*.md"):
                try:
                    adr_id = adr_file.stem
                    with open(adr_file) as f:
                        content = f.read()
                        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                        title = title_match.group(1) if title_match else adr_id

                    adr = ADR(
                        id=adr_id,
                        repo=repo_name,
                        title=title,
                        file_path=str(adr_file),
                        related_tasks=[]
                    )
                    adrs.append(adr)
                except Exception as e:
                    print(f"Warning: Failed to parse {adr_file}: {e}")
                    continue

        # Load from vibe-kanban/adrs/ (yaml)
        vibe_adrs_dir = repo_path / str(repo_config["vibe_kanban"]) / "adrs"
        if vibe_adrs_dir.exists():
            for adr_file in vibe_adrs_dir.glob("ADR-*.yaml"):
                try:
                    with open(adr_file) as f:
                        data = yaml.safe_load(f)

                    adr = ADR(
                        id=data.get("id", adr_file.stem),
                        repo=repo_name,
                        title=data.get("title", "Untitled ADR"),
                        file_path=str(adr_file),
                        related_tasks=data.get("tasks", [])
                    )
                    adrs.append(adr)
                except Exception as e:
                    print(f"Warning: Failed to parse {adr_file}: {e}")
                    continue

        return adrs

    def load_objectives_from_repo(self, repo_name: str) -> List[Objective]:
        """Load objectives from repo's vibe-kanban directory"""
        repo_config = self.repos[repo_name]
        repo_path: Path = repo_config["path"]  # type: ignore
        vibe_dir = repo_path / str(repo_config["vibe_kanban"])
        objectives_dir = vibe_dir / "objectives"

        if not objectives_dir.exists():
            return []

        objectives = []
        for obj_file in objectives_dir.glob("*.yaml"):
            try:
                with open(obj_file) as f:
                    data = yaml.safe_load(f)

                    objective = Objective(
                        id=data.get("id", obj_file.stem),
                        repo=repo_name,
                        title=data.get("title", "Untitled"),
                        status=data.get("status", "active"),
                        completion_pct=data.get("completion_pct", 0.0),
                        tasks_total=data.get("tasks_total", 0),
                        tasks_complete=data.get("tasks_complete", 0),
                        adrs=data.get("adrs", []),
                        source_file=str(obj_file)
                    )
                    objectives.append(objective)
            except Exception as e:
                print(f"Warning: Failed to parse {obj_file}: {e}")
                continue

        return objectives

    def link_tasks_to_adrs(self, tasks: List[Task], adrs: List[ADR]) -> None:
        """Link tasks to ADRs based on references"""
        adr_map = {adr.id: adr for adr in adrs}

        for task in tasks:
            for adr_ref in task.adr_references:
                if adr_ref in adr_map:
                    adr_map[adr_ref].related_tasks.append(task.id)

    def calculate_objective_progress(self, objective: Objective, tasks: List[Task]) -> Objective:
        """Calculate objective progress based on linked tasks"""
        # Find tasks linked to this objective's ADRs
        linked_tasks = [
            t for t in tasks
            if any(adr in objective.adrs for adr in t.adr_references)
        ]

        if linked_tasks:
            total = len(linked_tasks)
            completed = sum(1 for t in linked_tasks if t.status == "completed")

            objective.tasks_total = total
            objective.tasks_complete = completed
            objective.completion_pct = (completed / total * 100) if total > 0 else 0.0

        return objective

    def aggregate_all(self) -> dict[str, Any]:
        """Aggregate objectives, ADRs, and tasks from all repos"""
        all_objectives = []
        all_adrs = []
        all_tasks = []

        # Collect data from all repos
        for repo_name in self.repos.keys():
            objectives = self.load_objectives_from_repo(repo_name)
            adrs = self.load_adrs_from_repo(repo_name)
            tasks = self.load_tasks_from_queue(repo_name)

            all_objectives.extend(objectives)
            all_adrs.extend(adrs)
            all_tasks.extend(tasks)

        # Link tasks to ADRs
        self.link_tasks_to_adrs(all_tasks, all_adrs)

        # Calculate objective progress
        for objective in all_objectives:
            self.calculate_objective_progress(objective, all_tasks)

        # Build aggregate structure
        aggregate = {
            "last_updated": datetime.now().isoformat(),
            "summary": {
                "total_objectives": len(all_objectives),
                "total_adrs": len(all_adrs),
                "total_tasks": len(all_tasks),
                "repos": list(self.repos.keys()),
                "tasks_by_status": {
                    "pending": sum(1 for t in all_tasks if t.status == "pending"),
                    "in_progress": sum(1 for t in all_tasks if t.status == "in_progress"),
                    "blocked": sum(1 for t in all_tasks if t.status == "blocked"),
                    "completed": sum(1 for t in all_tasks if t.status == "completed")
                }
            },
            "objectives": [asdict(obj) for obj in all_objectives],
            "adrs": [asdict(adr) for adr in all_adrs],
            "tasks": [asdict(task) for task in all_tasks]
        }

        return aggregate

    def generate_unified_board_json(self) -> Path:
        """Generate unified-board.json"""
        aggregate = self.aggregate_all()

        output_file = self.vibe_kanban_dir / "unified-board.json"
        with open(output_file, "w") as f:
            json.dump(aggregate, f, indent=2)

        return output_file

    def generate_unified_board_md(self, aggregate: dict[str, Any]) -> Path:
        """Generate human-readable unified-board.md"""
        output_file = self.vibe_kanban_dir / "unified-board.md"

        with open(output_file, "w") as f:
            f.write("# Unified Vibe Kanban Board\n\n")
            f.write(f"**Last Updated**: {aggregate['last_updated']}\n\n")

            # Summary section
            summary = aggregate["summary"]
            f.write("## Summary\n\n")
            f.write(f"- **Total Objectives**: {summary['total_objectives']}\n")
            f.write(f"- **Total ADRs**: {summary['total_adrs']}\n")
            f.write(f"- **Total Tasks**: {summary['total_tasks']}\n")
            f.write(f"- **Repos**: {', '.join(summary['repos'])}\n\n")

            # Task breakdown
            f.write("### Tasks by Status\n\n")
            status_counts = summary["tasks_by_status"]
            f.write(f"- Pending: {status_counts['pending']}\n")
            f.write(f"- In Progress: {status_counts['in_progress']}\n")
            f.write(f"- Blocked: {status_counts['blocked']}\n")
            f.write(f"- Completed: {status_counts['completed']}\n\n")

            # Objectives section
            if aggregate["objectives"]:
                f.write("## Objectives\n\n")
                f.write("| ID | Repo | Title | Status | Progress | Tasks |\n")
                f.write("|---|---|---|---|---|---|\n")

                for obj in aggregate["objectives"]:
                    progress_bar = self._generate_progress_bar(obj["completion_pct"])
                    f.write(f"| {obj['id']} | {obj['repo']} | {obj['title']} | "
                           f"{obj['status']} | {progress_bar} | "
                           f"{obj['tasks_complete']}/{obj['tasks_total']} |\n")
                f.write("\n")

            # ADRs section
            if aggregate["adrs"]:
                f.write("## Architecture Decision Records\n\n")
                f.write("| ID | Repo | Title | Related Tasks |\n")
                f.write("|---|---|---|---|\n")

                for adr in aggregate["adrs"]:
                    task_count = len(adr["related_tasks"])
                    f.write(f"| {adr['id']} | {adr['repo']} | {adr['title']} | {task_count} |\n")
                f.write("\n")

            # Tasks by repo section
            f.write("## Tasks by Repo\n\n")
            repos = set(t["repo"] for t in aggregate["tasks"])

            for repo in sorted(repos):
                repo_tasks = [t for t in aggregate["tasks"] if t["repo"] == repo]
                f.write(f"### {repo.capitalize()} ({len(repo_tasks)} tasks)\n\n")

                # Group by status
                for status in ["in_progress", "blocked", "pending", "completed"]:
                    status_tasks = [t for t in repo_tasks if t["status"] == status]
                    if status_tasks:
                        f.write(f"#### {status.replace('_', ' ').title()} ({len(status_tasks)})\n\n")
                        for task in status_tasks[:10]:  # Limit to first 10
                            priority = task["priority"]
                            f.write(f"- [{priority}] {task['title']} (`{task['id']}`)\n")
                        if len(status_tasks) > 10:
                            f.write(f"  - _(+{len(status_tasks) - 10} more)_\n")
                        f.write("\n")

        return output_file

    def _generate_progress_bar(self, percentage: float, width: int = 10) -> str:
        """Generate a text-based progress bar"""
        filled = int(percentage / 100 * width)
        empty = width - filled
        return f"{'█' * filled}{'░' * empty} {percentage:.0f}%"


def main() -> None:
    # Get AI_Orchestrator root
    ai_orch_root = Path(__file__).parent.parent.parent

    aggregator = KanbanAggregator(ai_orch_root)

    print("📊 Aggregating kanban data from all repos...")

    # Generate JSON
    json_file = aggregator.generate_unified_board_json()
    print(f"✅ Generated: {json_file}")

    # Load for MD generation
    with open(json_file) as f:
        aggregate = json.load(f)

    # Generate Markdown
    md_file = aggregator.generate_unified_board_md(aggregate)
    print(f"✅ Generated: {md_file}")

    # Print summary
    summary = aggregate["summary"]
    print(f"\n📈 Summary:")
    print(f"   Objectives: {summary['total_objectives']}")
    print(f"   ADRs: {summary['total_adrs']}")
    print(f"   Tasks: {summary['total_tasks']} ({summary['tasks_by_status']['completed']} completed)")


if __name__ == "__main__":
    main()
