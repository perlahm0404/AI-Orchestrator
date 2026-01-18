"""
Objective Sync Module

Syncs objectives from MissionControl to vibe-kanban.

MissionControl holds high-level objectives in governance/objectives/.
This module imports them into vibe-kanban/objectives/ for decomposition
into ADRs and tasks.

Usage:
    from vibe_kanban.objective_sync import sync_objectives

    # Sync all objectives
    sync_objectives()

    # Sync and decompose
    objectives = sync_objectives()
    for obj in objectives:
        adrs = decompose_to_adrs(obj)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml  # type: ignore[import-untyped]


# Paths
MISSION_CONTROL_OBJECTIVES = Path("/Users/tmac/1_REPOS/MissionControl/governance/objectives")
VIBE_KANBAN_OBJECTIVES = Path("/Users/tmac/1_REPOS/AI_Orchestrator/vibe-kanban/objectives")
VIBE_KANBAN_ADRS = Path("/Users/tmac/1_REPOS/AI_Orchestrator/vibe-kanban/adrs")
BOARD_STATE_PATH = Path("/Users/tmac/1_REPOS/AI_Orchestrator/vibe-kanban/board-state.json")


@dataclass
class Objective:
    """A high-level objective from MissionControl."""
    id: str
    title: str
    description: str
    priority: str  # P0-P4
    status: str  # draft, active, completed
    repos: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    imported_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "repos": self.repos,
            "success_criteria": self.success_criteria,
            "source_file": self.source_file,
            "imported_at": self.imported_at,
        }


@dataclass
class ADR:
    """An Architecture Decision Record decomposed from an objective."""
    id: str
    objective_id: str
    title: str
    context: str
    decision: str
    consequences: List[str] = field(default_factory=list)
    status: str = "proposed"  # proposed, accepted, superseded
    tasks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "objective_id": self.objective_id,
            "title": self.title,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "status": self.status,
            "tasks": self.tasks,
        }


def sync_objectives() -> List[Objective]:
    """
    Sync objectives from MissionControl to vibe-kanban.

    Returns:
        List of imported objectives
    """
    objectives: List[Objective] = []

    # Ensure directories exist
    VIBE_KANBAN_OBJECTIVES.mkdir(parents=True, exist_ok=True)
    VIBE_KANBAN_ADRS.mkdir(parents=True, exist_ok=True)

    # Check if MissionControl objectives exist
    if not MISSION_CONTROL_OBJECTIVES.exists():
        print(f"MissionControl objectives directory not found: {MISSION_CONTROL_OBJECTIVES}")
        return objectives

    # Scan for objective files
    for obj_file in MISSION_CONTROL_OBJECTIVES.glob("*.yaml"):
        try:
            obj = _parse_objective_file(obj_file)
            if obj:
                objectives.append(obj)
                _write_local_objective(obj)
        except Exception as e:
            print(f"Error parsing {obj_file}: {e}")
            continue

    # Also check for markdown objectives
    for obj_file in MISSION_CONTROL_OBJECTIVES.glob("*.md"):
        try:
            obj = _parse_objective_markdown(obj_file)
            if obj:
                objectives.append(obj)
                _write_local_objective(obj)
        except Exception as e:
            print(f"Error parsing {obj_file}: {e}")
            continue

    # Update board state
    _update_board_state(objectives)

    return objectives


def _parse_objective_file(file_path: Path) -> Optional[Objective]:
    """Parse a YAML objective file."""
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        return Objective(
            id=data.get('id', file_path.stem),
            title=data.get('title', ''),
            description=data.get('description', ''),
            priority=data.get('priority', 'P2'),
            status=data.get('status', 'draft'),
            repos=data.get('repos', []),
            success_criteria=data.get('success_criteria', []),
            source_file=str(file_path),
        )
    except Exception:
        return None


def _parse_objective_markdown(file_path: Path) -> Optional[Objective]:
    """Parse a markdown objective file (extract from frontmatter if present)."""
    try:
        content = file_path.read_text()

        # Extract YAML frontmatter if present
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                if frontmatter:
                    return Objective(
                        id=frontmatter.get('id', file_path.stem),
                        title=frontmatter.get('title', file_path.stem),
                        description=parts[2].strip()[:500],  # First 500 chars of body
                        priority=frontmatter.get('priority', 'P2'),
                        status=frontmatter.get('status', 'draft'),
                        repos=frontmatter.get('repos', []),
                        success_criteria=frontmatter.get('success_criteria', []),
                        source_file=str(file_path),
                    )

        # No frontmatter - create basic objective from filename
        return Objective(
            id=file_path.stem,
            title=file_path.stem.replace('-', ' ').title(),
            description=content[:500] if content else '',
            priority='P2',
            status='draft',
            source_file=str(file_path),
        )
    except Exception:
        return None


def _write_local_objective(obj: Objective) -> None:
    """Write objective to local vibe-kanban directory."""
    output_file = VIBE_KANBAN_OBJECTIVES / f"{obj.id}.yaml"

    with open(output_file, 'w') as f:
        yaml.dump(obj.to_dict(), f, default_flow_style=False, sort_keys=False)


def _update_board_state(objectives: List[Objective]) -> None:
    """Update the board-state.json with new objectives."""
    try:
        if BOARD_STATE_PATH.exists():
            with open(BOARD_STATE_PATH, 'r') as f:
                state = json.load(f)
        else:
            state = {
                "version": "1.0",
                "objectives": [],
                "adrs": [],
                "tasks": [],
                "agents_active": [],
            }

        # Update objectives
        state["objectives"] = [obj.to_dict() for obj in objectives]
        state["last_updated"] = datetime.now().isoformat()

        with open(BOARD_STATE_PATH, 'w') as f:
            json.dump(state, f, indent=2)

    except Exception as e:
        print(f"Error updating board state: {e}")


def decompose_to_adrs(objective: Objective) -> List[ADR]:
    """
    Decompose an objective into ADRs.

    This is a template - actual decomposition requires understanding
    the objective context. Returns placeholder ADRs for manual refinement.

    Args:
        objective: The objective to decompose

    Returns:
        List of ADRs (templates for refinement)
    """
    adrs = []

    # Create a default ADR for the objective
    adr = ADR(
        id=f"ADR-{objective.id}-001",
        objective_id=objective.id,
        title=f"Implement: {objective.title}",
        context=objective.description,
        decision="[TO BE DEFINED]",
        consequences=["[TO BE DEFINED]"],
        status="proposed",
        tasks=[],
    )
    adrs.append(adr)

    # Write ADR to file
    adr_file = VIBE_KANBAN_ADRS / f"{adr.id}.yaml"
    with open(adr_file, 'w') as f:
        yaml.dump(adr.to_dict(), f, default_flow_style=False, sort_keys=False)

    return adrs


def get_board_status() -> Dict[str, Any]:
    """Get current board status."""
    if BOARD_STATE_PATH.exists():
        with open(BOARD_STATE_PATH, 'r') as f:
            result: Dict[str, Any] = json.load(f)
            return result
    return {}


# CLI interface
def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Objective Sync")
    parser.add_argument('command', choices=['sync', 'status', 'decompose'])
    parser.add_argument('--objective', '-o', help='Objective ID for decompose')
    args = parser.parse_args()

    if args.command == 'sync':
        objectives = sync_objectives()
        print(f"Synced {len(objectives)} objectives")
        for obj in objectives:
            print(f"  - [{obj.priority}] {obj.id}: {obj.title}")

    elif args.command == 'status':
        status = get_board_status()
        print(json.dumps(status, indent=2))

    elif args.command == 'decompose':
        if not args.objective:
            print("--objective required for decompose command")
            return

        # Load objective and decompose
        obj_file = VIBE_KANBAN_OBJECTIVES / f"{args.objective}.yaml"
        if obj_file.exists():
            with open(obj_file, 'r') as f:
                data = yaml.safe_load(f)
            obj = Objective(**data)
            adrs = decompose_to_adrs(obj)
            print(f"Created {len(adrs)} ADRs for {obj.id}")
        else:
            print(f"Objective not found: {args.objective}")


if __name__ == "__main__":
    main()
