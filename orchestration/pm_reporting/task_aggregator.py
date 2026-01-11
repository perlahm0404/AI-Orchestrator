"""
Task Aggregator - Roll up tasks by ADR/project with drill-down capability.

Uses existing task queues instead of creating new PRD system.
ADRs already function as "PRDs" - tasks link to them via `source` field.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import json
import os
import glob
from collections import defaultdict


@dataclass
class ADRStatus:
    """ADR = 'PRD' in this system"""
    adr_id: str  # "ADR-006"
    title: str  # "CME Gap Calculation"
    project: str  # "credentialmate"
    status: str  # "active" | "complete" | "blocked"

    # Task rollup
    total_tasks: int
    tasks_pending: int
    tasks_in_progress: int
    tasks_completed: int
    tasks_blocked: int
    tasks_failed: int

    # Evidence linkage
    evidence_refs: List[str]  # ["EVIDENCE-001"]

    # Calculated
    progress_pct: int  # 0-100


@dataclass
class ProjectRollup:
    """Project-level aggregation"""
    project: str  # "credentialmate" | "karematch" | "orchestrator"
    adrs: List[ADRStatus]

    # Totals
    total_tasks: int
    tasks_open: int  # pending + in_progress
    tasks_completed: int
    tasks_blocked: int

    # Evidence
    evidence_coverage_pct: int

    # Risk
    high_risk_count: int


class TaskAggregator:
    """Aggregate tasks from existing work queues by project/ADR"""

    def __init__(self) -> None:
        self.queue_dir = "tasks/queues-active/"
        self.feature_queue_dir = "tasks/queues-feature/"
        self.adr_index_path = "AI-Team-Plans/ADR-INDEX.md"
        self.evidence_dir = "evidence/"

    def load_all_queues(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load all task queues for a project"""
        all_tasks = []

        # Load from active queues
        if os.path.exists(self.queue_dir):
            for queue_file in glob.glob(f"{self.queue_dir}*.json"):
                try:
                    with open(queue_file, 'r') as f:
                        queue_data = json.load(f)

                        # Filter by project if specified
                        if project and queue_data.get("project") != project:
                            continue

                        all_tasks.extend(queue_data.get("features", []))
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"Warning: Could not load {queue_file}: {e}")
                    continue

        # Load from feature-specific queues
        if os.path.exists(self.feature_queue_dir):
            for queue_file in glob.glob(f"{self.feature_queue_dir}*.json"):
                try:
                    with open(queue_file, 'r') as f:
                        queue_data = json.load(f)

                        # Filter by project if specified
                        if project and queue_data.get("project") != project:
                            continue

                        all_tasks.extend(queue_data.get("features", []))
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"Warning: Could not load {queue_file}: {e}")
                    continue

        return all_tasks

    def get_adr_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Parse ADR-INDEX.md to get metadata for each ADR"""
        adr_map: Dict[str, Dict[str, Any]] = {}

        if not os.path.exists(self.adr_index_path):
            return adr_map

        try:
            with open(self.adr_index_path, 'r') as f:
                content = f.read()

            # Parse ADR table (only main registry table, not "By Project" sections)
            # Main table has 6 columns: ADR | Title | Project | Status | Date | Advisor
            in_main_table = False
            for line in content.split('\n'):
                # Detect main table header
                if '## ADR Registry' in line:
                    in_main_table = True
                    continue
                # Stop at next section
                if in_main_table and line.startswith('##'):
                    in_main_table = False
                    continue

                # Only parse ADR lines in main table
                if in_main_table and '| ADR-' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    # Main table has 6 parts, "By Project" has only 3
                    if len(parts) >= 6:
                        adr_id = parts[0]
                        title = parts[1].split('](')[0].strip('[').strip()
                        project = parts[2]

                        adr_map[adr_id] = {
                            "title": title,
                            "project": project
                        }
        except Exception as e:
            print(f"Warning: Could not parse ADR-INDEX.md: {e}")

        return adr_map

    def count_evidence_items(self) -> int:
        """Count total evidence files"""
        if not os.path.exists(self.evidence_dir):
            return 0

        evidence_files = glob.glob(f"{self.evidence_dir}EVIDENCE-*.md")
        return len(evidence_files)

    def get_evidence_mappings(self) -> Dict[str, List[str]]:
        """Build mapping of task_id → [evidence_ids] from evidence files"""
        task_to_evidence: Dict[str, List[str]] = defaultdict(list)

        if not os.path.exists(self.evidence_dir):
            return task_to_evidence

        evidence_files = glob.glob(f"{self.evidence_dir}EVIDENCE-*.md")

        for evidence_file in evidence_files:
            try:
                with open(evidence_file, 'r') as f:
                    content = f.read()

                # Extract evidence ID from filename
                evidence_id = os.path.basename(evidence_file).replace('.md', '').split('-')[0] + '-' + os.path.basename(evidence_file).replace('.md', '').split('-')[1]

                # Parse frontmatter for linked_tasks
                if '---' in content:
                    parts = content.split('---', 2)
                    if len(parts) >= 2:
                        frontmatter = parts[1]

                        # Extract linked_tasks (simple parsing)
                        for line in frontmatter.split('\n'):
                            if 'linked_tasks:' in line:
                                # Extract list: linked_tasks: [TASK-1, TASK-2]
                                tasks_str = line.split('linked_tasks:', 1)[1].strip()
                                if '[' in tasks_str and ']' in tasks_str:
                                    tasks_str = tasks_str.strip('[]').strip()
                                    task_ids = [t.strip() for t in tasks_str.split(',')]
                                    for task_id in task_ids:
                                        if task_id:  # Skip empty strings
                                            task_to_evidence[task_id].append(evidence_id)

            except Exception as e:
                print(f"Warning: Could not parse evidence file {evidence_file}: {e}")
                continue

        return dict(task_to_evidence)

    def aggregate_by_adr(self, adr_id: str, tasks: List[Dict[str, Any]], adr_metadata: Dict[str, Dict[str, Any]]) -> ADRStatus:
        """Aggregate all tasks linked to an ADR"""

        # Get evidence mappings
        task_to_evidence = self.get_evidence_mappings()

        # Filter tasks by ADR (check multiple source fields)
        adr_tasks = []
        for task in tasks:
            source = task.get("source", "")
            source_adr = task.get("source_adr", "")
            adr_context = task.get("adr_context", {})

            if (adr_id in source or
                adr_id == source_adr or
                adr_id in str(adr_context)):
                adr_tasks.append(task)

        # Count by status
        pending = sum(1 for t in adr_tasks if t.get("status") == "pending")
        in_progress = sum(1 for t in adr_tasks if t.get("status") == "in_progress")
        completed = sum(1 for t in adr_tasks if t.get("status") == "complete")
        blocked = sum(1 for t in adr_tasks if t.get("status") == "blocked")
        failed = sum(1 for t in adr_tasks if t.get("verification_verdict") == "BLOCKED")

        total = len(adr_tasks)
        progress_pct = int((completed / total * 100)) if total > 0 else 0

        # Get ADR metadata
        meta = adr_metadata.get(adr_id, {"title": "Unknown", "project": "unknown"})

        # Check for evidence references (from tasks OR from evidence files)
        evidence_refs = []
        for task in adr_tasks:
            # Check task's evidence_linked field
            evidence_linked = task.get("evidence_linked", [])
            if isinstance(evidence_linked, list):
                evidence_refs.extend(evidence_linked)

            # Check task's evidence_refs field
            task_evidence = task.get("evidence_refs", [])
            if isinstance(task_evidence, list):
                evidence_refs.extend(task_evidence)

            # Check evidence files that reference this task
            task_id = task.get("id", "")
            if task_id in task_to_evidence:
                evidence_refs.extend(task_to_evidence[task_id])

        return ADRStatus(
            adr_id=adr_id,
            title=meta["title"],
            project=meta["project"],
            status="complete" if progress_pct == 100 else "active",
            total_tasks=total,
            tasks_pending=pending,
            tasks_in_progress=in_progress,
            tasks_completed=completed,
            tasks_blocked=blocked,
            tasks_failed=failed,
            evidence_refs=list(set(evidence_refs)),
            progress_pct=progress_pct
        )

    def aggregate_by_project(self, project: str) -> ProjectRollup:
        """Aggregate all ADRs/tasks for a project"""

        # Load tasks for project
        tasks = self.load_all_queues(project=project)

        # Get ADR metadata
        adr_metadata = self.get_adr_metadata()

        # Find all ADRs mentioned in tasks
        adr_ids = set()
        for task in tasks:
            source = task.get("source", "")
            source_adr = task.get("source_adr", "")

            # Extract ADR ID from source field
            if "ADR-" in source:
                # Find ADR-XXX pattern
                import re
                matches = re.findall(r'ADR-\d+', source)
                adr_ids.update(matches)

            if source_adr:
                adr_ids.add(source_adr)

        # Also include ADRs from index for this project
        for adr_id, meta in adr_metadata.items():
            if meta["project"].lower() == project.lower():
                adr_ids.add(adr_id)

        # Aggregate each ADR
        adrs = []
        for adr_id in sorted(adr_ids):
            adr_status = self.aggregate_by_adr(adr_id, tasks, adr_metadata)
            # Include ALL ADRs from index, even without tasks (for roadmap visibility)
            adrs.append(adr_status)

        # Calculate project totals
        total_tasks = sum(adr.total_tasks for adr in adrs)
        tasks_open = sum(adr.tasks_pending + adr.tasks_in_progress for adr in adrs)
        tasks_completed = sum(adr.tasks_completed for adr in adrs)
        tasks_blocked = sum(adr.tasks_blocked for adr in adrs)

        # Evidence coverage
        adrs_with_evidence = sum(1 for adr in adrs if adr.evidence_refs)
        evidence_coverage_pct = int((adrs_with_evidence / len(adrs) * 100)) if len(adrs) > 0 else 0

        # Risk count (HIGH risk tasks)
        high_risk_count = 0  # Placeholder for when Governance agent deploys

        return ProjectRollup(
            project=project,
            adrs=adrs,
            total_tasks=total_tasks,
            tasks_open=tasks_open,
            tasks_completed=tasks_completed,
            tasks_blocked=tasks_blocked,
            evidence_coverage_pct=evidence_coverage_pct,
            high_risk_count=high_risk_count
        )

    def get_all_projects(self) -> List[ProjectRollup]:
        """Get rollup for all projects"""
        projects = []

        # Scan all queue files to find projects
        project_names = set()

        if os.path.exists(self.queue_dir):
            for queue_file in glob.glob(f"{self.queue_dir}*.json"):
                try:
                    with open(queue_file, 'r') as f:
                        queue_data = json.load(f)
                        project_names.add(queue_data.get("project", "unknown"))
                except Exception:
                    continue

        # Aggregate each project
        for project in sorted(project_names):
            if project != "unknown":
                projects.append(self.aggregate_by_project(project))

        return projects
