"""
Vibe Kanban Integration for Coordinator

Integrates the vibe-kanban objective system with the Coordinator agent.

This module provides:
1. Read objectives from vibe-kanban/objectives/
2. Decompose objectives to ADRs with context-aware generation
3. Decompose ADRs to tasks using Coordinator patterns
4. Route tasks to appropriate repo/team via PM Agent

Integration: Phase 3 of Governance Harmonization
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Import from sibling modules
from .pm_agent import PMAgent, Task as PMTask, Priority, TaskType


# Paths
VIBE_KANBAN_ROOT = Path("/Users/tmac/1_REPOS/AI_Orchestrator/vibe-kanban")
VIBE_KANBAN_OBJECTIVES = VIBE_KANBAN_ROOT / "objectives"
VIBE_KANBAN_ADRS = VIBE_KANBAN_ROOT / "adrs"
BOARD_STATE_PATH = VIBE_KANBAN_ROOT / "board-state.json"


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class Objective:
    """A high-level objective from vibe-kanban."""
    id: str
    title: str
    description: str
    priority: str  # P0-P4
    status: str  # draft, active, completed
    repos: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    source_file: Optional[str] = None

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
        }


@dataclass
class ADR:
    """An Architecture Decision Record derived from an objective."""
    id: str
    objective_id: str
    title: str
    context: str
    decision: str
    consequences: List[str] = field(default_factory=list)
    status: str = "proposed"  # proposed, accepted, implemented, superseded
    tasks: List[str] = field(default_factory=list)
    target_repos: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"  # low, medium, high
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

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
            "target_repos": self.target_repos,
            "estimated_complexity": self.estimated_complexity,
            "created_at": self.created_at,
        }


@dataclass
class VibeTask:
    """A task derived from an ADR for execution."""
    id: str
    adr_id: str
    objective_id: str
    title: str
    description: str
    repo: str
    task_type: str  # bugfix, feature, migration, test, documentation
    priority: str  # P0-P4
    status: str = "pending"  # pending, in_progress, completed, blocked
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    branch_lane: Optional[str] = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "adr_id": self.adr_id,
            "objective_id": self.objective_id,
            "title": self.title,
            "description": self.description,
            "repo": self.repo,
            "task_type": self.task_type,
            "priority": self.priority,
            "status": self.status,
            "dependencies": self.dependencies,
            "assigned_agent": self.assigned_agent,
            "branch_lane": self.branch_lane,
            "created_at": self.created_at,
        }


class VibeKanbanIntegration:
    """
    Integrates vibe-kanban objectives with Coordinator task management.

    Flow: Objective → ADR(s) → Task(s) → Agent Assignment

    This creates the traceability chain:
    - Objectives define WHAT to achieve
    - ADRs define HOW to achieve it (architecture decisions)
    - Tasks define WHO does WHAT work
    """

    def __init__(self):
        self.pm_agent = PMAgent()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure vibe-kanban directories exist."""
        VIBE_KANBAN_OBJECTIVES.mkdir(parents=True, exist_ok=True)
        VIBE_KANBAN_ADRS.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # OBJECTIVE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def load_objectives(self) -> List[Objective]:
        """
        Load all objectives from vibe-kanban/objectives/.

        Returns:
            List of Objective instances
        """
        objectives = []

        if not VIBE_KANBAN_OBJECTIVES.exists():
            return objectives

        for obj_file in VIBE_KANBAN_OBJECTIVES.glob("*.yaml"):
            try:
                with open(obj_file, 'r') as f:
                    data = yaml.safe_load(f)
                if data:
                    objectives.append(Objective(
                        id=data.get('id', obj_file.stem),
                        title=data.get('title', ''),
                        description=data.get('description', ''),
                        priority=data.get('priority', 'P2'),
                        status=data.get('status', 'draft'),
                        repos=data.get('repos', []),
                        success_criteria=data.get('success_criteria', []),
                        source_file=str(obj_file),
                    ))
            except Exception as e:
                print(f"Error loading objective {obj_file}: {e}")

        return objectives

    def get_active_objectives(self) -> List[Objective]:
        """Get only active (non-draft, non-completed) objectives."""
        return [obj for obj in self.load_objectives() if obj.status == 'active']

    def activate_objective(self, objective_id: str) -> bool:
        """
        Activate a draft objective.

        Args:
            objective_id: ID of objective to activate

        Returns:
            True if activated, False if not found
        """
        obj_file = VIBE_KANBAN_OBJECTIVES / f"{objective_id}.yaml"
        if not obj_file.exists():
            return False

        with open(obj_file, 'r') as f:
            data = yaml.safe_load(f)

        data['status'] = 'active'

        with open(obj_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

        self._update_board_state()
        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # ADR DECOMPOSITION
    # ═══════════════════════════════════════════════════════════════════════════

    def decompose_objective_to_adrs(self, objective: Objective) -> List[ADR]:
        """
        Decompose an objective into ADRs.

        Uses context-aware decomposition based on:
        - Objective description analysis
        - Target repos and their characteristics
        - Success criteria

        Args:
            objective: Objective to decompose

        Returns:
            List of generated ADRs
        """
        adrs = []
        adr_seq = 1

        # Analyze objective to determine ADR structure
        analysis = self._analyze_objective(objective)

        # Create ADRs based on analysis
        for component in analysis['components']:
            adr = ADR(
                id=f"ADR-{objective.id}-{adr_seq:03d}",
                objective_id=objective.id,
                title=component['title'],
                context=f"Part of objective: {objective.title}\n\n{component['context']}",
                decision=component['decision'],
                consequences=component['consequences'],
                status="proposed",
                target_repos=component.get('repos', objective.repos),
                estimated_complexity=component.get('complexity', 'medium'),
            )
            adrs.append(adr)
            self._write_adr(adr)
            adr_seq += 1

        # Update board state
        self._update_board_state()

        return adrs

    def _analyze_objective(self, objective: Objective) -> Dict[str, Any]:
        """
        Analyze an objective to determine how to decompose it.

        Returns a structure describing the components needed.
        """
        components = []
        description_lower = objective.description.lower()

        # Check for common patterns and generate appropriate ADRs

        # Database/schema changes
        if any(kw in description_lower for kw in ['database', 'schema', 'migration', 'table', 'model']):
            components.append({
                'title': f"Schema Design: {objective.title}",
                'context': "Database schema changes required for this objective.",
                'decision': self._generate_schema_decision(objective),
                'consequences': [
                    "Requires database migration",
                    "Backward compatibility must be considered",
                    "May require data backfill",
                ],
                'complexity': 'high',
                'repos': [r for r in objective.repos if 'backend' in r.lower() or 'api' in r.lower()] or objective.repos,
            })

        # API changes
        if any(kw in description_lower for kw in ['api', 'endpoint', 'rest', 'graphql', 'route']):
            components.append({
                'title': f"API Design: {objective.title}",
                'context': "API changes or new endpoints required.",
                'decision': self._generate_api_decision(objective),
                'consequences': [
                    "API versioning may be needed",
                    "Documentation must be updated",
                    "Client code may need updates",
                ],
                'complexity': 'medium',
                'repos': [r for r in objective.repos if 'backend' in r.lower() or 'api' in r.lower()] or objective.repos,
            })

        # UI changes
        if any(kw in description_lower for kw in ['ui', 'frontend', 'component', 'page', 'screen', 'interface']):
            components.append({
                'title': f"UI Implementation: {objective.title}",
                'context': "User interface changes required.",
                'decision': self._generate_ui_decision(objective),
                'consequences': [
                    "Visual testing may be needed",
                    "Accessibility must be verified",
                    "Responsive design considered",
                ],
                'complexity': 'medium',
                'repos': [r for r in objective.repos if 'frontend' in r.lower() or 'web' in r.lower() or 'app' in r.lower()] or objective.repos,
            })

        # Integration/orchestration
        if any(kw in description_lower for kw in ['integration', 'orchestrat', 'coordinat', 'workflow', 'pipeline']):
            components.append({
                'title': f"Integration Architecture: {objective.title}",
                'context': "System integration or orchestration changes.",
                'decision': self._generate_integration_decision(objective),
                'consequences': [
                    "Cross-repo coordination needed",
                    "Testing across boundaries required",
                    "Deployment coordination may be needed",
                ],
                'complexity': 'high',
                'repos': objective.repos,
            })

        # Security changes
        if any(kw in description_lower for kw in ['security', 'auth', 'permission', 'access', 'encrypt']):
            components.append({
                'title': f"Security Design: {objective.title}",
                'context': "Security-related changes required.",
                'decision': self._generate_security_decision(objective),
                'consequences': [
                    "Security review required",
                    "May affect existing auth flows",
                    "Compliance verification needed",
                ],
                'complexity': 'high',
                'repos': objective.repos,
            })

        # If no specific patterns matched, create a generic implementation ADR
        if not components:
            components.append({
                'title': f"Implementation: {objective.title}",
                'context': objective.description,
                'decision': f"Implement the objective as described, following existing patterns in the codebase.",
                'consequences': [
                    "Implementation follows existing architecture",
                    "Tests must be added for new functionality",
                ],
                'complexity': 'medium',
                'repos': objective.repos,
            })

        return {'components': components}

    def _generate_schema_decision(self, objective: Objective) -> str:
        """Generate schema decision text based on objective."""
        return (
            f"Design database schema changes to support: {objective.title}\n\n"
            "Consider:\n"
            "- Table structure and relationships\n"
            "- Index requirements for query performance\n"
            "- Migration strategy (additive first, then modifications)\n"
            "- Backward compatibility with existing data"
        )

    def _generate_api_decision(self, objective: Objective) -> str:
        """Generate API decision text based on objective."""
        return (
            f"Design API changes to support: {objective.title}\n\n"
            "Consider:\n"
            "- RESTful design principles\n"
            "- Request/response schema\n"
            "- Error handling patterns\n"
            "- Authentication/authorization requirements"
        )

    def _generate_ui_decision(self, objective: Objective) -> str:
        """Generate UI decision text based on objective."""
        return (
            f"Design UI implementation for: {objective.title}\n\n"
            "Consider:\n"
            "- Component hierarchy and reusability\n"
            "- State management approach\n"
            "- User interaction patterns\n"
            "- Accessibility requirements"
        )

    def _generate_integration_decision(self, objective: Objective) -> str:
        """Generate integration decision text based on objective."""
        return (
            f"Design integration architecture for: {objective.title}\n\n"
            "Consider:\n"
            "- Service boundaries and interfaces\n"
            "- Data flow between components\n"
            "- Error handling and resilience\n"
            "- Testing strategy across boundaries"
        )

    def _generate_security_decision(self, objective: Objective) -> str:
        """Generate security decision text based on objective."""
        return (
            f"Design security implementation for: {objective.title}\n\n"
            "Consider:\n"
            "- Authentication mechanism\n"
            "- Authorization model\n"
            "- Data protection requirements\n"
            "- Audit logging needs"
        )

    def _write_adr(self, adr: ADR) -> None:
        """Write ADR to vibe-kanban/adrs/."""
        adr_file = VIBE_KANBAN_ADRS / f"{adr.id}.yaml"
        with open(adr_file, 'w') as f:
            yaml.dump(adr.to_dict(), f, default_flow_style=False, sort_keys=False)

    # ═══════════════════════════════════════════════════════════════════════════
    # TASK DECOMPOSITION
    # ═══════════════════════════════════════════════════════════════════════════

    def decompose_adr_to_tasks(self, adr: ADR) -> List[VibeTask]:
        """
        Decompose an ADR into executable tasks.

        Creates tasks for each target repo with appropriate types
        and dependencies.

        Args:
            adr: ADR to decompose

        Returns:
            List of generated tasks
        """
        tasks = []
        task_seq = 1
        title_lower = adr.title.lower()

        # Determine task types needed based on ADR title/context
        for repo in adr.target_repos or ['default']:
            # Schema ADRs get migration tasks
            if 'schema' in title_lower:
                tasks.append(VibeTask(
                    id=f"TASK-{adr.id}-{task_seq:03d}",
                    adr_id=adr.id,
                    objective_id=adr.objective_id,
                    title=f"Create migration: {adr.title}",
                    description=f"Create database migration for: {adr.decision[:200]}",
                    repo=repo,
                    task_type='migration',
                    priority=self._adr_to_task_priority(adr),
                ))
                task_seq += 1

            # API ADRs get implementation + test tasks
            if 'api' in title_lower:
                impl_task = VibeTask(
                    id=f"TASK-{adr.id}-{task_seq:03d}",
                    adr_id=adr.id,
                    objective_id=adr.objective_id,
                    title=f"Implement API: {adr.title}",
                    description=f"Implement API endpoints for: {adr.decision[:200]}",
                    repo=repo,
                    task_type='feature',
                    priority=self._adr_to_task_priority(adr),
                )
                tasks.append(impl_task)
                task_seq += 1

                # Test task depends on implementation
                tasks.append(VibeTask(
                    id=f"TASK-{adr.id}-{task_seq:03d}",
                    adr_id=adr.id,
                    objective_id=adr.objective_id,
                    title=f"Write API tests: {adr.title}",
                    description=f"Write tests for API implementation",
                    repo=repo,
                    task_type='test',
                    priority='P3',
                    dependencies=[impl_task.id],
                ))
                task_seq += 1

            # UI ADRs get component + test tasks
            if 'ui' in title_lower:
                impl_task = VibeTask(
                    id=f"TASK-{adr.id}-{task_seq:03d}",
                    adr_id=adr.id,
                    objective_id=adr.objective_id,
                    title=f"Implement UI: {adr.title}",
                    description=f"Implement UI components for: {adr.decision[:200]}",
                    repo=repo,
                    task_type='feature',
                    priority=self._adr_to_task_priority(adr),
                )
                tasks.append(impl_task)
                task_seq += 1

                tasks.append(VibeTask(
                    id=f"TASK-{adr.id}-{task_seq:03d}",
                    adr_id=adr.id,
                    objective_id=adr.objective_id,
                    title=f"Write UI tests: {adr.title}",
                    description=f"Write tests for UI components",
                    repo=repo,
                    task_type='test',
                    priority='P3',
                    dependencies=[impl_task.id],
                ))
                task_seq += 1

            # Security ADRs get implementation + security review tasks
            if 'security' in title_lower:
                impl_task = VibeTask(
                    id=f"TASK-{adr.id}-{task_seq:03d}",
                    adr_id=adr.id,
                    objective_id=adr.objective_id,
                    title=f"Implement security: {adr.title}",
                    description=f"Implement security changes for: {adr.decision[:200]}",
                    repo=repo,
                    task_type='feature',
                    priority='P1',  # Security is always high priority
                )
                tasks.append(impl_task)
                task_seq += 1

            # Integration ADRs get coordination tasks
            if 'integration' in title_lower:
                tasks.append(VibeTask(
                    id=f"TASK-{adr.id}-{task_seq:03d}",
                    adr_id=adr.id,
                    objective_id=adr.objective_id,
                    title=f"Implement integration: {adr.title}",
                    description=f"Implement integration for: {adr.decision[:200]}",
                    repo=repo,
                    task_type='feature',
                    priority=self._adr_to_task_priority(adr),
                ))
                task_seq += 1

            # Generic implementation ADR
            if 'implementation' in title_lower and not tasks:
                tasks.append(VibeTask(
                    id=f"TASK-{adr.id}-{task_seq:03d}",
                    adr_id=adr.id,
                    objective_id=adr.objective_id,
                    title=f"Implement: {adr.title}",
                    description=f"Implement: {adr.decision[:200]}",
                    repo=repo,
                    task_type='feature',
                    priority=self._adr_to_task_priority(adr),
                ))
                task_seq += 1

        # Update ADR with task IDs
        adr.tasks = [t.id for t in tasks]
        self._write_adr(adr)

        # Write tasks to board state
        self._update_board_state()

        return tasks

    def _adr_to_task_priority(self, adr: ADR) -> str:
        """Convert ADR complexity to task priority."""
        if adr.estimated_complexity == 'high':
            return 'P1'
        elif adr.estimated_complexity == 'low':
            return 'P3'
        return 'P2'

    # ═══════════════════════════════════════════════════════════════════════════
    # TASK ROUTING
    # ═══════════════════════════════════════════════════════════════════════════

    def route_tasks(self, tasks: List[VibeTask]) -> List[Tuple[VibeTask, str, str]]:
        """
        Route tasks to appropriate agents using PM Agent.

        Args:
            tasks: Tasks to route

        Returns:
            List of (task, agent, lane) tuples
        """
        # Convert VibeTask to PMTask format for PM Agent
        pm_tasks = []
        for task in tasks:
            pm_task = PMTask(
                id=task.id,
                description=task.description,
                repo=task.repo,
                priority=self._str_to_priority(task.priority),
                task_type=self._str_to_task_type(task.task_type),
            )
            pm_tasks.append(pm_task)

        # Get allocations from PM Agent
        allocations = self.pm_agent.allocate_resources(pm_tasks)

        # Map back to VibeTask with assignments
        routed = []
        for alloc in allocations:
            # Find matching VibeTask
            for task in tasks:
                if task.id == alloc.task.id:
                    task.assigned_agent = alloc.assigned_agent
                    task.branch_lane = alloc.assigned_lane
                    routed.append((task, alloc.assigned_agent, alloc.assigned_lane))
                    break

        return routed

    def _str_to_priority(self, priority_str: str) -> Priority:
        """Convert string priority to Priority enum."""
        mapping = {
            'P0': Priority.P0_CRITICAL,
            'P1': Priority.P1_HIGH,
            'P2': Priority.P2_MEDIUM,
            'P3': Priority.P3_LOW,
            'P4': Priority.P4_BACKLOG,
        }
        return mapping.get(priority_str, Priority.P2_MEDIUM)

    def _str_to_task_type(self, type_str: str) -> TaskType:
        """Convert string task type to TaskType enum."""
        mapping = {
            'bugfix': TaskType.BUGFIX,
            'feature': TaskType.FEATURE,
            'security': TaskType.SECURITY,
            'deployment': TaskType.DEPLOYMENT,
            'documentation': TaskType.DOCUMENTATION,
            'refactor': TaskType.REFACTOR,
            'migration': TaskType.FEATURE,  # Map to feature for now
            'test': TaskType.FEATURE,  # Map to feature for now
        }
        return mapping.get(type_str, TaskType.FEATURE)

    # ═══════════════════════════════════════════════════════════════════════════
    # FULL PIPELINE
    # ═══════════════════════════════════════════════════════════════════════════

    def process_objective(self, objective_id: str) -> Dict[str, Any]:
        """
        Process a full objective through the pipeline.

        Objective → ADRs → Tasks → Routing

        Args:
            objective_id: ID of objective to process

        Returns:
            Processing result with all generated artifacts
        """
        result = {
            'objective_id': objective_id,
            'adrs': [],
            'tasks': [],
            'routing': [],
            'status': 'pending',
        }

        # Load objective
        objectives = self.load_objectives()
        objective = next((o for o in objectives if o.id == objective_id), None)

        if not objective:
            result['status'] = 'error'
            result['error'] = f"Objective not found: {objective_id}"
            return result

        # Activate if draft
        if objective.status == 'draft':
            self.activate_objective(objective_id)
            objective.status = 'active'

        # Decompose to ADRs
        adrs = self.decompose_objective_to_adrs(objective)
        result['adrs'] = [adr.to_dict() for adr in adrs]

        # Decompose ADRs to tasks
        all_tasks = []
        for adr in adrs:
            tasks = self.decompose_adr_to_tasks(adr)
            all_tasks.extend(tasks)
        result['tasks'] = [t.to_dict() for t in all_tasks]

        # Route tasks
        routing = self.route_tasks(all_tasks)
        result['routing'] = [
            {'task_id': t.id, 'agent': agent, 'lane': lane}
            for t, agent, lane in routing
        ]

        result['status'] = 'processed'
        result['processed_at'] = utc_now().isoformat()

        # Update board state with full result
        self._update_board_state()

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # BOARD STATE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def _update_board_state(self) -> None:
        """Update the board-state.json with current state."""
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
            objectives = self.load_objectives()
            state["objectives"] = [obj.to_dict() for obj in objectives]

            # Update ADRs
            adrs = self._load_all_adrs()
            state["adrs"] = [adr.to_dict() for adr in adrs]

            # Update tasks from ADRs
            all_tasks = []
            for adr in adrs:
                for task_id in adr.tasks:
                    # Tasks are stored in ADR references
                    all_tasks.append({"id": task_id, "adr_id": adr.id})
            state["tasks"] = all_tasks

            state["last_updated"] = utc_now().isoformat()
            state["notes"] = {
                "description": "Vibe Kanban board state for AI_Orchestrator",
                "objectives_source": "MissionControl/governance/objectives/",
                "phase": "Phase 3 - Vibe Kanban Integration",
            }

            with open(BOARD_STATE_PATH, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            print(f"Error updating board state: {e}")

    def _load_all_adrs(self) -> List[ADR]:
        """Load all ADRs from vibe-kanban/adrs/."""
        adrs = []

        if not VIBE_KANBAN_ADRS.exists():
            return adrs

        for adr_file in VIBE_KANBAN_ADRS.glob("*.yaml"):
            try:
                with open(adr_file, 'r') as f:
                    data = yaml.safe_load(f)
                if data:
                    adrs.append(ADR(
                        id=data.get('id', adr_file.stem),
                        objective_id=data.get('objective_id', ''),
                        title=data.get('title', ''),
                        context=data.get('context', ''),
                        decision=data.get('decision', ''),
                        consequences=data.get('consequences', []),
                        status=data.get('status', 'proposed'),
                        tasks=data.get('tasks', []),
                        target_repos=data.get('target_repos', []),
                        estimated_complexity=data.get('estimated_complexity', 'medium'),
                        created_at=data.get('created_at', ''),
                    ))
            except Exception as e:
                print(f"Error loading ADR {adr_file}: {e}")

        return adrs

    def get_traceability(self, task_id: str) -> Dict[str, Any]:
        """
        Get full traceability chain for a task.

        Returns: Objective → ADR → Task → Agent chain
        """
        adrs = self._load_all_adrs()
        objectives = self.load_objectives()

        # Find ADR containing this task
        for adr in adrs:
            if task_id in adr.tasks:
                # Find objective for this ADR
                objective = next(
                    (o for o in objectives if o.id == adr.objective_id),
                    None
                )
                return {
                    'task_id': task_id,
                    'adr': adr.to_dict(),
                    'objective': objective.to_dict() if objective else None,
                    'chain': f"{objective.id if objective else 'unknown'} → {adr.id} → {task_id}",
                }

        return {
            'task_id': task_id,
            'adr': None,
            'objective': None,
            'chain': f"unknown → unknown → {task_id}",
        }


# CLI interface
def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Vibe Kanban Integration")
    parser.add_argument('command', choices=[
        'list-objectives',
        'process-objective',
        'list-adrs',
        'traceability',
        'status',
    ])
    parser.add_argument('--objective', '-o', help='Objective ID')
    parser.add_argument('--task', '-t', help='Task ID')
    args = parser.parse_args()

    integration = VibeKanbanIntegration()

    if args.command == 'list-objectives':
        objectives = integration.load_objectives()
        print(f"Found {len(objectives)} objectives:")
        for obj in objectives:
            print(f"  [{obj.priority}] {obj.id}: {obj.title} ({obj.status})")

    elif args.command == 'process-objective':
        if not args.objective:
            print("--objective required")
            return
        result = integration.process_objective(args.objective)
        print(json.dumps(result, indent=2))

    elif args.command == 'list-adrs':
        adrs = integration._load_all_adrs()
        print(f"Found {len(adrs)} ADRs:")
        for adr in adrs:
            print(f"  [{adr.status}] {adr.id}: {adr.title}")
            if adr.tasks:
                print(f"    Tasks: {', '.join(adr.tasks)}")

    elif args.command == 'traceability':
        if not args.task:
            print("--task required")
            return
        trace = integration.get_traceability(args.task)
        print(json.dumps(trace, indent=2))

    elif args.command == 'status':
        objectives = integration.load_objectives()
        adrs = integration._load_all_adrs()
        print(f"Vibe Kanban Status:")
        print(f"  Objectives: {len(objectives)} ({len([o for o in objectives if o.status == 'active'])} active)")
        print(f"  ADRs: {len(adrs)} ({len([a for a in adrs if a.status == 'accepted'])} accepted)")
        total_tasks = sum(len(a.tasks) for a in adrs)
        print(f"  Tasks: {total_tasks}")


if __name__ == "__main__":
    main()
