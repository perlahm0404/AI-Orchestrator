"""
PM (Project Manager) Meta-Agent

Cross-repository coordination and prioritization agent.

Responsibilities:
1. Cross-repo prioritization - Order work across all managed repos
2. Evidence-driven queue ordering - Prioritize based on impact/urgency
3. Resource allocation - Assign tasks to appropriate agents

Usage:
    from agents.coordinator.pm_agent import PMAgent

    pm = PMAgent()
    prioritized_tasks = pm.prioritize_work_queues()
    allocation = pm.allocate_resources(prioritized_tasks)

Integration: Phase 2 of Governance Harmonization
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Paths
ADAPTERS_PATH = Path("/Users/tmac/1_REPOS/AI_Orchestrator/adapters")
WORK_QUEUE_PATH = Path("/Users/tmac/1_REPOS/AI_Orchestrator/tasks")
MISSION_CONTROL_PATH = Path("/Users/tmac/1_REPOS/MissionControl")


class Priority(Enum):
    """Task priority levels."""
    P0_CRITICAL = 0     # Production down, data loss risk
    P1_HIGH = 1         # User-facing bugs, security issues
    P2_MEDIUM = 2       # Feature work, improvements
    P3_LOW = 3          # Tech debt, cleanup
    P4_BACKLOG = 4      # Nice to have


class TaskType(Enum):
    """Types of tasks for routing."""
    BUGFIX = "bugfix"
    FEATURE = "feature"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    DOCUMENTATION = "documentation"
    REFACTOR = "refactor"


@dataclass
class Task:
    """A task from any work queue."""
    id: str
    description: str
    repo: str
    priority: Priority
    task_type: TaskType
    file_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    evidence: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "description": self.description,
            "repo": self.repo,
            "priority": self.priority.name,
            "task_type": self.task_type.value,
            "file_path": self.file_path,
            "created_at": self.created_at,
            "evidence": self.evidence,
            "dependencies": self.dependencies,
            "estimated_complexity": self.estimated_complexity,
        }


@dataclass
class ResourceAllocation:
    """Assignment of tasks to agents."""
    task: Task
    assigned_agent: str
    assigned_lane: str
    repo_path: str
    estimated_start: Optional[str] = None


class PMAgent:
    """
    Project Manager Meta-Agent.

    Coordinates work across all managed repositories by:
    1. Loading work queues from all repos
    2. Prioritizing tasks based on evidence
    3. Allocating resources to avoid conflicts
    """

    def __init__(self):
        self.repos: Dict[str, Dict[str, Any]] = {}
        self.work_queues: Dict[str, List[Task]] = {}
        self._load_repos()

    def _load_repos(self) -> None:
        """Load all configured repositories from adapters."""
        if not ADAPTERS_PATH.exists():
            return

        for adapter_dir in ADAPTERS_PATH.iterdir():
            if not adapter_dir.is_dir():
                continue

            config_file = adapter_dir / "config.yaml"
            if not config_file.exists():
                continue

            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)

                repo_name = config.get('project', {}).get('name', adapter_dir.name)
                self.repos[repo_name] = {
                    'config': config,
                    'path': config.get('project', {}).get('path'),
                    'autonomy_level': config.get('autonomy_level', 'L2'),
                    'hipaa': config.get('hipaa', {}).get('enabled', False),
                }
            except Exception:
                continue

    def load_work_queues(self) -> Dict[str, List[Task]]:
        """
        Load work queues from all repositories.

        Returns:
            Dict mapping repo name to list of tasks
        """
        self.work_queues = {}

        # Load from central task directory
        if WORK_QUEUE_PATH.exists():
            for queue_file in WORK_QUEUE_PATH.glob("work_queue_*.json"):
                try:
                    with open(queue_file, 'r') as f:
                        data = json.load(f)

                    repo_name = data.get('project', queue_file.stem.replace('work_queue_', ''))
                    tasks = []

                    for feature in data.get('features', []):
                        task = self._parse_task(feature, repo_name)
                        if task:
                            tasks.append(task)

                    if tasks:
                        self.work_queues[repo_name] = tasks

                except Exception:
                    continue

        return self.work_queues

    def _parse_task(self, feature: Dict[str, Any], repo_name: str) -> Optional[Task]:
        """Parse a feature dict into a Task object."""
        try:
            # Determine priority from feature data
            priority = self._infer_priority(feature)

            # Determine task type
            task_type = self._infer_task_type(feature)

            return Task(
                id=feature.get('id', f"{repo_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                description=feature.get('description', ''),
                repo=repo_name,
                priority=priority,
                task_type=task_type,
                file_path=feature.get('file'),
                evidence={
                    'tests': feature.get('tests', []),
                    'status': feature.get('status', 'pending'),
                },
                dependencies=feature.get('dependencies', []),
                estimated_complexity=feature.get('complexity', 'medium'),
            )
        except Exception:
            return None

    def _infer_priority(self, feature: Dict[str, Any]) -> Priority:
        """Infer priority from feature data."""
        description = feature.get('description', '').lower()
        feature_id = feature.get('id', '').upper()

        # P0: Critical indicators
        if any(kw in description for kw in ['production', 'outage', 'data loss', 'critical']):
            return Priority.P0_CRITICAL

        # P1: High priority indicators
        if any(kw in description for kw in ['security', 'bug', 'error', 'fix']):
            return Priority.P1_HIGH

        # Check ID prefix
        if feature_id.startswith('BUG-') or feature_id.startswith('SEC-'):
            return Priority.P1_HIGH

        if feature_id.startswith('FEAT-'):
            return Priority.P2_MEDIUM

        return Priority.P2_MEDIUM

    def _infer_task_type(self, feature: Dict[str, Any]) -> TaskType:
        """Infer task type from feature data."""
        description = feature.get('description', '').lower()
        feature_id = feature.get('id', '').upper()

        if 'security' in description or feature_id.startswith('SEC-'):
            return TaskType.SECURITY

        if any(kw in description for kw in ['bug', 'fix', 'error', 'broken']):
            return TaskType.BUGFIX

        if any(kw in description for kw in ['deploy', 'release']):
            return TaskType.DEPLOYMENT

        if any(kw in description for kw in ['doc', 'readme']):
            return TaskType.DOCUMENTATION

        if any(kw in description for kw in ['refactor', 'cleanup', 'optimize']):
            return TaskType.REFACTOR

        return TaskType.FEATURE

    def prioritize_work_queues(self) -> List[Task]:
        """
        Prioritize all tasks across repositories.

        Priority order:
        1. P0 Critical (production issues)
        2. P1 High (security, bugs)
        3. P2 Medium (features)
        4. P3 Low (tech debt)
        5. P4 Backlog

        Within same priority:
        - HIPAA repos get slight boost (compliance)
        - Security tasks come first
        - Bugfixes before features

        Returns:
            Sorted list of all tasks by priority
        """
        if not self.work_queues:
            self.load_work_queues()

        all_tasks = []
        for repo, tasks in self.work_queues.items():
            for task in tasks:
                all_tasks.append(task)

        # Sort by priority score
        def priority_score(task: Task) -> tuple:
            # Base priority
            base = task.priority.value

            # Type adjustments within priority
            type_order = {
                TaskType.SECURITY: 0,
                TaskType.BUGFIX: 1,
                TaskType.DEPLOYMENT: 2,
                TaskType.FEATURE: 3,
                TaskType.REFACTOR: 4,
                TaskType.DOCUMENTATION: 5,
            }

            # HIPAA boost
            hipaa_boost = 0
            if task.repo in self.repos:
                if self.repos[task.repo].get('hipaa', False):
                    hipaa_boost = -0.5  # Lower score = higher priority

            return (base + hipaa_boost, type_order.get(task.task_type, 5), task.created_at)

        all_tasks.sort(key=priority_score)
        return all_tasks

    def allocate_resources(
        self,
        tasks: List[Task],
        available_agents: int = 3
    ) -> List[ResourceAllocation]:
        """
        Allocate tasks to agents, avoiding conflicts.

        Args:
            tasks: Prioritized list of tasks
            available_agents: Number of agents available

        Returns:
            List of resource allocations
        """
        allocations = []
        active_files: Dict[str, str] = {}  # file -> agent
        active_repos: Dict[str, str] = {}  # repo -> primary agent

        agent_names = [f"agent-{i+1}" for i in range(available_agents)]
        agent_index = 0

        for task in tasks:
            # Check for conflicts
            if task.file_path and task.file_path in active_files:
                # Skip - file already being worked on
                continue

            # Assign agent
            agent = agent_names[agent_index % len(agent_names)]

            # Determine lane based on task type
            lane = self._determine_lane(task)

            # Get repo path
            repo_path = ""
            if task.repo in self.repos:
                repo_path = self.repos[task.repo].get('path', '')

            allocation = ResourceAllocation(
                task=task,
                assigned_agent=agent,
                assigned_lane=lane,
                repo_path=repo_path,
            )
            allocations.append(allocation)

            # Track active files
            if task.file_path:
                active_files[task.file_path] = agent

            # Track active repos
            if task.repo not in active_repos:
                active_repos[task.repo] = agent

            agent_index += 1

        return allocations

    def _determine_lane(self, task: Task) -> str:
        """Determine the appropriate branch lane for a task."""
        if task.task_type == TaskType.BUGFIX:
            return f"fix/{task.id.lower()}"
        elif task.task_type == TaskType.FEATURE:
            return f"feature/{task.id.lower()}"
        elif task.task_type == TaskType.SECURITY:
            return f"security/{task.id.lower()}"
        elif task.task_type == TaskType.DEPLOYMENT:
            return f"deploy/{task.id.lower()}"
        elif task.task_type == TaskType.DOCUMENTATION:
            return f"docs/{task.id.lower()}"
        else:
            return f"task/{task.id.lower()}"

    def get_cross_repo_status(self) -> Dict[str, Any]:
        """
        Get status summary across all repositories.

        Returns:
            Status dict with task counts, blockers, etc.
        """
        if not self.work_queues:
            self.load_work_queues()

        status = {
            "repos": {},
            "total_tasks": 0,
            "by_priority": {p.name: 0 for p in Priority},
            "by_type": {t.value: 0 for t in TaskType},
            "generated_at": datetime.now().isoformat(),
        }

        for repo, tasks in self.work_queues.items():
            repo_status = {
                "task_count": len(tasks),
                "hipaa": self.repos.get(repo, {}).get('hipaa', False),
                "autonomy_level": self.repos.get(repo, {}).get('autonomy_level', 'L2'),
            }
            status["repos"][repo] = repo_status
            status["total_tasks"] += len(tasks)

            for task in tasks:
                status["by_priority"][task.priority.name] += 1
                status["by_type"][task.task_type.value] += 1

        return status

    def export_prioritized_queue(self, output_path: Optional[Path] = None) -> str:
        """
        Export prioritized queue to JSON.

        Args:
            output_path: Path to write JSON file

        Returns:
            JSON string of prioritized tasks
        """
        prioritized = self.prioritize_work_queues()

        data = {
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(prioritized),
            "tasks": [t.to_dict() for t in prioritized],
        }

        json_str = json.dumps(data, indent=2)

        if output_path:
            output_path.write_text(json_str)

        return json_str


# CLI interface
def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="PM Meta-Agent")
    parser.add_argument('command', choices=['status', 'prioritize', 'allocate'])
    parser.add_argument('--output', '-o', help='Output file path')
    args = parser.parse_args()

    pm = PMAgent()

    if args.command == 'status':
        status = pm.get_cross_repo_status()
        print(json.dumps(status, indent=2))

    elif args.command == 'prioritize':
        prioritized = pm.prioritize_work_queues()
        for i, task in enumerate(prioritized[:20], 1):  # Top 20
            print(f"{i}. [{task.priority.name}] {task.repo}: {task.description[:50]}...")

    elif args.command == 'allocate':
        prioritized = pm.prioritize_work_queues()
        allocations = pm.allocate_resources(prioritized)
        for alloc in allocations[:10]:  # Top 10
            print(f"{alloc.assigned_agent} -> {alloc.task.repo}/{alloc.assigned_lane}")


if __name__ == "__main__":
    main()
