"""
Traceability Module

Provides end-to-end traceability linking:
    Objective → ADR → Task → RIS Resolution

This enables:
1. Impact analysis (what objectives does this task serve?)
2. Progress tracking (what % of objective is complete?)
3. Audit trail (how did we get here?)
4. RIS correlation (what guardrail patterns were triggered?)

Integration: Phase 3 of Governance Harmonization
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Paths
VIBE_KANBAN_ROOT = Path("/Users/tmac/1_REPOS/AI_Orchestrator/vibe-kanban")
VIBE_KANBAN_OBJECTIVES = VIBE_KANBAN_ROOT / "objectives"
VIBE_KANBAN_ADRS = VIBE_KANBAN_ROOT / "adrs"
BOARD_STATE_PATH = VIBE_KANBAN_ROOT / "board-state.json"
MISSION_CONTROL_RIS = Path("/Users/tmac/1_REPOS/MissionControl/governance/ris")
TRACEABILITY_LOG = VIBE_KANBAN_ROOT / "traceability-log.json"


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class TraceLink:
    """A link in the traceability chain."""
    source_type: str  # objective, adr, task, ris
    source_id: str
    target_type: str
    target_id: str
    relationship: str  # decomposed_to, implements, triggered, resolved_by
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "relationship": self.relationship,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class TraceChain:
    """A complete traceability chain from objective to RIS."""
    objective_id: Optional[str] = None
    objective_title: Optional[str] = None
    adr_id: Optional[str] = None
    adr_title: Optional[str] = None
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    ris_resolutions: List[str] = field(default_factory=list)
    links: List[TraceLink] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "objective_title": self.objective_title,
            "adr_id": self.adr_id,
            "adr_title": self.adr_title,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "ris_resolutions": self.ris_resolutions,
            "chain_string": self.to_chain_string(),
            "links": [l.to_dict() for l in self.links],
        }

    def to_chain_string(self) -> str:
        """Generate a human-readable chain string."""
        parts = []
        if self.objective_id:
            parts.append(f"OBJ:{self.objective_id}")
        if self.adr_id:
            parts.append(f"ADR:{self.adr_id}")
        if self.task_id:
            parts.append(f"TASK:{self.task_id}")
        if self.ris_resolutions:
            parts.append(f"RIS:[{','.join(self.ris_resolutions)}]")
        return " → ".join(parts) if parts else "empty"


@dataclass
class RISResolution:
    """A Resolution from the RIS (Resolution Information Store)."""
    id: str
    type: str  # bugfix, feature, security, deployment
    description: str
    task_id: Optional[str] = None
    repo: Optional[str] = None
    files_affected: List[str] = field(default_factory=list)
    patterns_triggered: List[str] = field(default_factory=list)
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "task_id": self.task_id,
            "repo": self.repo,
            "files_affected": self.files_affected,
            "patterns_triggered": self.patterns_triggered,
            "resolved_at": self.resolved_at,
        }


class TraceabilityEngine:
    """
    Engine for managing end-to-end traceability.

    Features:
    1. Link Management - Create and query trace links
    2. Chain Building - Construct full chains from any node
    3. Impact Analysis - What objectives does a task serve?
    4. Progress Tracking - What % of objective is complete?
    5. RIS Correlation - What patterns were triggered?
    """

    def __init__(self):
        self.links: List[TraceLink] = []
        self._ensure_directories()
        self._load_state()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        VIBE_KANBAN_ROOT.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> None:
        """Load traceability state."""
        if TRACEABILITY_LOG.exists():
            try:
                with open(TRACEABILITY_LOG, 'r') as f:
                    data = json.load(f)
                for link_data in data.get("links", []):
                    self.links.append(TraceLink(**link_data))
            except Exception as e:
                print(f"Error loading traceability state: {e}")

    def _save_state(self) -> None:
        """Save traceability state."""
        try:
            data = {
                "version": "1.0",
                "last_updated": utc_now().isoformat(),
                "links": [l.to_dict() for l in self.links],
            }
            with open(TRACEABILITY_LOG, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving traceability state: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # LINK MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def add_link(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        relationship: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TraceLink:
        """
        Add a traceability link.

        Args:
            source_type: Type of source (objective, adr, task, ris)
            source_id: ID of source
            target_type: Type of target
            target_id: ID of target
            relationship: Type of relationship
            metadata: Additional metadata

        Returns:
            Created TraceLink
        """
        link = TraceLink(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            relationship=relationship,
            metadata=metadata or {},
        )

        # Check for duplicate
        existing = self._find_link(source_type, source_id, target_type, target_id)
        if existing:
            return existing

        self.links.append(link)
        self._save_state()

        return link

    def _find_link(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
    ) -> Optional[TraceLink]:
        """Find an existing link."""
        for link in self.links:
            if (link.source_type == source_type and
                link.source_id == source_id and
                link.target_type == target_type and
                link.target_id == target_id):
                return link
        return None

    def get_links_from(self, source_type: str, source_id: str) -> List[TraceLink]:
        """Get all links from a source."""
        return [
            l for l in self.links
            if l.source_type == source_type and l.source_id == source_id
        ]

    def get_links_to(self, target_type: str, target_id: str) -> List[TraceLink]:
        """Get all links to a target."""
        return [
            l for l in self.links
            if l.target_type == target_type and l.target_id == target_id
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # CHAIN BUILDING
    # ═══════════════════════════════════════════════════════════════════════════

    def build_chain_from_task(self, task_id: str) -> TraceChain:
        """
        Build a complete traceability chain starting from a task.

        Traces up to ADR and Objective, and down to RIS resolutions.

        Args:
            task_id: Task ID to trace from

        Returns:
            Complete TraceChain
        """
        chain = TraceChain(task_id=task_id)
        collected_links = []

        # Trace up: Task → ADR
        adr_links = self.get_links_to("task", task_id)
        for link in adr_links:
            if link.source_type == "adr":
                chain.adr_id = link.source_id
                chain.adr_title = link.metadata.get("adr_title")
                collected_links.append(link)

                # Continue up: ADR → Objective
                obj_links = self.get_links_to("adr", link.source_id)
                for obj_link in obj_links:
                    if obj_link.source_type == "objective":
                        chain.objective_id = obj_link.source_id
                        chain.objective_title = obj_link.metadata.get("objective_title")
                        collected_links.append(obj_link)
                        break
                break

        # Trace down: Task → RIS
        ris_links = self.get_links_from("task", task_id)
        for link in ris_links:
            if link.target_type == "ris":
                chain.ris_resolutions.append(link.target_id)
                collected_links.append(link)

        # Try to load task title from board state
        chain.task_title = self._get_task_title(task_id)

        chain.links = collected_links
        return chain

    def build_chain_from_objective(self, objective_id: str) -> List[TraceChain]:
        """
        Build all traceability chains for an objective.

        Returns chains for all tasks under this objective.

        Args:
            objective_id: Objective ID

        Returns:
            List of TraceChains (one per task)
        """
        chains = []
        objective_title = self._get_objective_title(objective_id)

        # Get ADRs for this objective
        adr_links = self.get_links_from("objective", objective_id)
        for adr_link in adr_links:
            if adr_link.target_type == "adr":
                adr_id = adr_link.target_id
                adr_title = adr_link.metadata.get("adr_title")

                # Get tasks for this ADR
                task_links = self.get_links_from("adr", adr_id)
                for task_link in task_links:
                    if task_link.target_type == "task":
                        task_id = task_link.target_id
                        chain = self.build_chain_from_task(task_id)
                        chain.objective_id = objective_id
                        chain.objective_title = objective_title
                        chain.adr_id = adr_id
                        chain.adr_title = adr_title
                        chains.append(chain)

        return chains

    def _get_task_title(self, task_id: str) -> Optional[str]:
        """Try to get task title from board state."""
        try:
            if BOARD_STATE_PATH.exists():
                with open(BOARD_STATE_PATH, 'r') as f:
                    state = json.load(f)
                for task in state.get("tasks", []):
                    if task.get("id") == task_id:
                        return task.get("title")
        except Exception:
            pass
        return None

    def _get_objective_title(self, objective_id: str) -> Optional[str]:
        """Try to get objective title."""
        obj_file = VIBE_KANBAN_OBJECTIVES / f"{objective_id}.yaml"
        if obj_file.exists():
            try:
                with open(obj_file, 'r') as f:
                    data = yaml.safe_load(f)
                return data.get("title")
            except Exception:
                pass
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # RIS CORRELATION
    # ═══════════════════════════════════════════════════════════════════════════

    def link_task_to_ris(
        self,
        task_id: str,
        ris_id: str,
        patterns_triggered: Optional[List[str]] = None,
    ) -> TraceLink:
        """
        Link a task to its RIS resolution.

        Args:
            task_id: Task ID
            ris_id: RIS resolution ID
            patterns_triggered: Guardrail patterns that were triggered

        Returns:
            Created TraceLink
        """
        return self.add_link(
            source_type="task",
            source_id=task_id,
            target_type="ris",
            target_id=ris_id,
            relationship="resolved_by",
            metadata={
                "patterns_triggered": patterns_triggered or [],
                "resolved_at": utc_now().isoformat(),
            },
        )

    def get_ris_resolutions_for_objective(
        self,
        objective_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all RIS resolutions for an objective.

        Args:
            objective_id: Objective ID

        Returns:
            List of RIS resolution summaries
        """
        chains = self.build_chain_from_objective(objective_id)
        resolutions = []

        for chain in chains:
            for ris_id in chain.ris_resolutions:
                resolutions.append({
                    "ris_id": ris_id,
                    "task_id": chain.task_id,
                    "adr_id": chain.adr_id,
                })

        return resolutions

    def load_ris_resolutions(self) -> List[RISResolution]:
        """
        Load RIS resolutions from MissionControl.

        Returns:
            List of RISResolution objects
        """
        resolutions = []

        if not MISSION_CONTROL_RIS.exists():
            return resolutions

        # Look for resolution files
        for res_file in MISSION_CONTROL_RIS.glob("**/*.yaml"):
            try:
                with open(res_file, 'r') as f:
                    data = yaml.safe_load(f)
                if data:
                    resolutions.append(RISResolution(
                        id=data.get('id', res_file.stem),
                        type=data.get('type', 'unknown'),
                        description=data.get('description', ''),
                        task_id=data.get('task_id'),
                        repo=data.get('repo'),
                        files_affected=data.get('files_affected', []),
                        patterns_triggered=data.get('patterns_triggered', []),
                        resolved_at=data.get('resolved_at'),
                    ))
            except Exception as e:
                print(f"Error loading RIS {res_file}: {e}")

        return resolutions

    # ═══════════════════════════════════════════════════════════════════════════
    # PROGRESS TRACKING
    # ═══════════════════════════════════════════════════════════════════════════

    def get_objective_progress(self, objective_id: str) -> Dict[str, Any]:
        """
        Calculate progress for an objective.

        Args:
            objective_id: Objective ID

        Returns:
            Progress summary with percentages
        """
        chains = self.build_chain_from_objective(objective_id)

        if not chains:
            return {
                "objective_id": objective_id,
                "total_tasks": 0,
                "completed_tasks": 0,
                "progress_pct": 0,
                "status": "no_tasks",
            }

        # Load board state to get task statuses
        task_statuses = {}
        if BOARD_STATE_PATH.exists():
            try:
                with open(BOARD_STATE_PATH, 'r') as f:
                    state = json.load(f)
                for task in state.get("tasks", []):
                    task_statuses[task.get("id")] = task.get("status", "pending")
            except Exception:
                pass

        total = len(chains)
        completed = sum(
            1 for chain in chains
            if task_statuses.get(chain.task_id) == "completed"
        )

        return {
            "objective_id": objective_id,
            "objective_title": chains[0].objective_title if chains else None,
            "total_tasks": total,
            "completed_tasks": completed,
            "progress_pct": round(completed / total * 100, 1) if total > 0 else 0,
            "status": "completed" if completed == total else "in_progress",
            "task_breakdown": {
                "completed": [c.task_id for c in chains if task_statuses.get(c.task_id) == "completed"],
                "pending": [c.task_id for c in chains if task_statuses.get(c.task_id) in ("pending", None)],
                "in_progress": [c.task_id for c in chains if task_statuses.get(c.task_id) == "in_progress"],
                "blocked": [c.task_id for c in chains if task_statuses.get(c.task_id) == "blocked"],
            },
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # IMPACT ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def analyze_task_impact(self, task_id: str) -> Dict[str, Any]:
        """
        Analyze the impact of a task.

        Shows what objectives this task serves and its position in the chain.

        Args:
            task_id: Task ID

        Returns:
            Impact analysis
        """
        chain = self.build_chain_from_task(task_id)

        return {
            "task_id": task_id,
            "serves_objective": chain.objective_id,
            "objective_title": chain.objective_title,
            "implements_adr": chain.adr_id,
            "adr_title": chain.adr_title,
            "has_ris_resolutions": len(chain.ris_resolutions) > 0,
            "ris_resolutions": chain.ris_resolutions,
            "chain": chain.to_chain_string(),
        }

    def analyze_adr_impact(self, adr_id: str) -> Dict[str, Any]:
        """
        Analyze the impact of an ADR.

        Shows what objectives this ADR serves and its tasks.

        Args:
            adr_id: ADR ID

        Returns:
            Impact analysis
        """
        # Get objective for this ADR
        obj_links = self.get_links_to("adr", adr_id)
        objective_id = None
        objective_title = None
        for link in obj_links:
            if link.source_type == "objective":
                objective_id = link.source_id
                objective_title = link.metadata.get("objective_title")
                break

        # Get tasks for this ADR
        task_links = self.get_links_from("adr", adr_id)
        task_ids = [
            link.target_id
            for link in task_links
            if link.target_type == "task"
        ]

        return {
            "adr_id": adr_id,
            "serves_objective": objective_id,
            "objective_title": objective_title,
            "task_count": len(task_ids),
            "task_ids": task_ids,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # BULK OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def record_decomposition(
        self,
        objective_id: str,
        adrs: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Record a complete decomposition operation.

        Creates all links for Objective → ADRs → Tasks.

        Args:
            objective_id: Source objective
            adrs: List of ADR dicts with 'id' and 'title'
            tasks: List of task dicts with 'id', 'title', 'adr_id'

        Returns:
            Summary of created links
        """
        links_created = []
        objective_title = self._get_objective_title(objective_id)

        # Objective → ADR links
        for adr in adrs:
            adr_id = adr.get("id")
            if not adr_id:
                continue
            link = self.add_link(
                source_type="objective",
                source_id=objective_id,
                target_type="adr",
                target_id=adr_id,
                relationship="decomposed_to",
                metadata={
                    "objective_title": objective_title,
                    "adr_title": adr.get("title"),
                },
            )
            links_created.append(link.to_dict())

        # ADR → Task links
        for task in tasks:
            adr_id = task.get("adr_id")
            task_id = task.get("id")
            if not adr_id or not task_id:
                continue
            adr_title = next(
                (a.get("title") for a in adrs if a.get("id") == adr_id),
                None
            )
            link = self.add_link(
                source_type="adr",
                source_id=adr_id,
                target_type="task",
                target_id=task_id,
                relationship="implements",
                metadata={
                    "adr_title": adr_title,
                    "task_title": task.get("title"),
                },
            )
            links_created.append(link.to_dict())

        return {
            "objective_id": objective_id,
            "adrs_linked": len(adrs),
            "tasks_linked": len(tasks),
            "total_links": len(links_created),
        }

    def get_full_traceability_report(self) -> Dict[str, Any]:
        """
        Generate a full traceability report.

        Returns:
            Complete report with all objectives, ADRs, tasks, and chains
        """
        # Load all objectives
        objectives = []
        if VIBE_KANBAN_OBJECTIVES.exists():
            for obj_file in VIBE_KANBAN_OBJECTIVES.glob("*.yaml"):
                try:
                    with open(obj_file, 'r') as f:
                        data = yaml.safe_load(f)
                    if data:
                        objectives.append({
                            "id": data.get("id", obj_file.stem),
                            "title": data.get("title"),
                            "status": data.get("status"),
                        })
                except Exception:
                    pass

        # Build progress for each objective
        objective_progress = []
        for obj in objectives:
            progress = self.get_objective_progress(obj["id"])
            objective_progress.append(progress)

        return {
            "generated_at": utc_now().isoformat(),
            "total_objectives": len(objectives),
            "total_links": len(self.links),
            "objectives": objective_progress,
            "link_summary": {
                "objective_to_adr": len([l for l in self.links if l.source_type == "objective"]),
                "adr_to_task": len([l for l in self.links if l.source_type == "adr"]),
                "task_to_ris": len([l for l in self.links if l.target_type == "ris"]),
            },
        }


# CLI interface
def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Traceability Engine")
    parser.add_argument('command', choices=[
        'chain',
        'progress',
        'impact',
        'report',
        'links',
    ])
    parser.add_argument('--task', '-t', help='Task ID')
    parser.add_argument('--objective', '-o', help='Objective ID')
    parser.add_argument('--adr', '-a', help='ADR ID')
    args = parser.parse_args()

    engine = TraceabilityEngine()

    if args.command == 'chain':
        if args.task:
            chain = engine.build_chain_from_task(args.task)
            print(json.dumps(chain.to_dict(), indent=2))
        elif args.objective:
            chains = engine.build_chain_from_objective(args.objective)
            print(f"Found {len(chains)} chains:")
            for chain in chains:
                print(f"  {chain.to_chain_string()}")
        else:
            print("--task or --objective required")

    elif args.command == 'progress':
        if not args.objective:
            print("--objective required")
            return
        progress = engine.get_objective_progress(args.objective)
        print(json.dumps(progress, indent=2))

    elif args.command == 'impact':
        if args.task:
            impact = engine.analyze_task_impact(args.task)
        elif args.adr:
            impact = engine.analyze_adr_impact(args.adr)
        else:
            print("--task or --adr required")
            return
        print(json.dumps(impact, indent=2))

    elif args.command == 'report':
        report = engine.get_full_traceability_report()
        print(json.dumps(report, indent=2))

    elif args.command == 'links':
        print(f"Total links: {len(engine.links)}")
        for link in engine.links:
            print(f"  {link.source_type}:{link.source_id} "
                  f"--[{link.relationship}]--> "
                  f"{link.target_type}:{link.target_id}")


if __name__ == "__main__":
    main()
