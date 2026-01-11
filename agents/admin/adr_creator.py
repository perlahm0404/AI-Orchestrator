"""
ADR Creator Agent

Admin agent that creates ADR drafts from advisor consultation context.

Workflow:
1. Read task.adr_context from work queue
2. Reserve ADR number (atomic file locking)
3. Generate ADR draft using template
4. Write ADR file to correct location
5. Extract tasks from Implementation Notes
6. Register tasks with work queue
7. Update ADR registry
8. Log completion with <promise>ADR_CREATE_COMPLETE</promise>

Implementation: Phase 4 - ADR Automation System
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from governance.kill_switch import mode
from governance import contract
from agents.base import BaseAgent, AgentConfig
from orchestration.adr_registry import ADRRegistry
from orchestration.adr_generator import ADRGenerator, ADRContext
from orchestration.adr_to_tasks import extract_tasks_from_adr, register_tasks_with_queue
from tasks.work_queue import WorkQueue

logger = logging.getLogger(__name__)


class ADRCreatorAgent(BaseAgent):
    """
    Admin agent that creates ADR drafts from advisor consultation context.

    Enhanced with Ralph-Wiggum iteration patterns.
    """

    def __init__(self, app_adapter, config: Optional[AgentConfig] = None):
        """
        Initialize ADR Creator agent.

        Args:
            app_adapter: Application adapter (provides project context)
            config: Optional AgentConfig (will be created from contract if not provided)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract
        self.contract = contract.load("admin-team")

        # Create or use provided config
        if config is None:
            self.config = AgentConfig(
                project_name=self.app_context.project_name,
                agent_name="adr-creator",
                expected_completion_signal="ADR_CREATE_COMPLETE",
                max_iterations=self.contract.limits.get("max_iterations", 3),
                max_retries=self.contract.limits.get("max_retries", 2)
            )
        else:
            self.config = config

        # Backward compatibility
        self.max_retries = self.config.max_retries

        # Iteration tracking
        self.current_iteration = 0
        self.iteration_history: List[Dict[str, Any]] = []

        # AI Orchestrator repo root (where ADRs are stored)
        self.orchestrator_root = Path(__file__).parent.parent.parent

    def execute(self, task_id: str) -> Dict[str, Any]:
        """
        Execute ADR creation workflow.

        Args:
            task_id: The task ID to work on (e.g., "TASK-ADR-001")

        Returns:
            Result dict with:
            - status: "completed" | "blocked" | "failed"
            - adr_number: Created ADR number (e.g., "ADR-006")
            - adr_path: Path to created ADR file
            - tasks_created: Number of tasks extracted and registered
            - output: Agent output text (for completion signal checking)
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract: can we execute this action?
        contract.require_allowed(self.contract, "write_file")
        contract.require_allowed(self.contract, "update_adr_registry")
        contract.require_allowed(self.contract, "register_tasks")

        # Track iteration
        self.current_iteration += 1

        # Check iteration budget
        if self.current_iteration > self.config.max_iterations:
            return {
                "task_id": task_id,
                "status": "failed",
                "reason": f"Max iterations ({self.config.max_iterations}) reached",
                "iterations": self.current_iteration,
                "output": f"Failed: Max iterations ({self.config.max_iterations}) reached"
            }

        logger.info(f"🚀 ADR Creator Agent starting (iteration {self.current_iteration}/{self.config.max_iterations})")

        try:
            # Step 1: Load work queue and get task
            queue_path = self._find_work_queue()
            if not queue_path:
                error_msg = "No work queue found for this project"
                logger.error(error_msg)
                return {
                    "task_id": task_id,
                    "status": "blocked",
                    "reason": error_msg,
                    "iterations": self.current_iteration,
                    "output": f"BLOCKED: {error_msg}"
                }

            queue = WorkQueue.load(queue_path)
            task = self._find_task_by_id(queue, task_id)

            if not task:
                error_msg = f"Task {task_id} not found in work queue"
                logger.error(error_msg)
                return {
                    "task_id": task_id,
                    "status": "blocked",
                    "reason": error_msg,
                    "iterations": self.current_iteration,
                    "output": f"BLOCKED: {error_msg}"
                }

            # Step 2: Extract ADR context from task
            if not hasattr(task, 'adr_context') or not task.adr_context:
                error_msg = f"Task {task_id} missing adr_context field"
                logger.error(error_msg)
                return {
                    "task_id": task_id,
                    "status": "blocked",
                    "reason": error_msg,
                    "iterations": self.current_iteration,
                    "output": f"BLOCKED: {error_msg}"
                }

            # Convert dict to ADRContext
            context = self._dict_to_adr_context(task.adr_context)
            project = task.adr_context.get("project", self.config.project_name)

            logger.info(f"📋 Creating ADR for: {context.description}")

            # Step 3: Reserve ADR number
            registry = ADRRegistry(self.orchestrator_root)
            adr_number = registry.reserve_adr_number()
            adr_id = f"ADR-{adr_number:03d}"

            logger.info(f"🔢 Reserved ADR number: {adr_id}")

            # Step 4: Generate ADR draft
            template_path = self.orchestrator_root / "AI-Team-Plans" / "decisions" / "ADR-TEMPLATE.md"
            generator = ADRGenerator(template_path)

            adr_markdown = generator.generate_adr_draft(adr_number, context, project)

            # Step 5: Write ADR file
            decisions_dir = self.orchestrator_root / "AI-Team-Plans" / "decisions"
            decisions_dir.mkdir(parents=True, exist_ok=True)

            adr_filename = f"{adr_id}-{self._slugify(context.description)}.md"
            adr_path = decisions_dir / adr_filename

            adr_path.write_text(adr_markdown)
            logger.info(f"✅ ADR draft written: {adr_path}")

            # Step 6: Extract tasks from ADR
            tasks = extract_tasks_from_adr(adr_path, adr_id, project)
            logger.info(f"📝 Extracted {len(tasks)} tasks from ADR")

            # Step 7: Register tasks with work queue
            task_ids = register_tasks_with_queue(
                tasks=tasks,
                adr_number=adr_id,
                queue=queue,
                queue_path=queue_path
            )
            logger.info(f"✅ Registered {len(task_ids)} tasks: {', '.join(task_ids)}")

            # Step 8: Update ADR registry
            from orchestration.adr_registry import ADREntry

            entry = ADREntry(
                number=adr_id,
                title=generator._extract_title(context.description),
                project=project,
                status="draft",
                date=context.task_id.split('-')[1] if '-' in context.task_id else "",
                advisor=f"{context.advisor_type}-advisor",
                file_path=f"AI-Team-Plans/decisions/{adr_filename}",
                tags=context.domain_tags,
                domains=[context.decision_type]
            )

            registry.register_adr(entry)
            registry.add_fingerprint(context.fingerprint, adr_id, context.description, context.domain_tags)
            logger.info(f"✅ ADR registry updated")

            # Success output
            output = f"""ADR draft created successfully.

ADR ID: {adr_id}
Title: {entry.title}
File: {adr_path}
Tasks created: {len(task_ids)}

Next steps:
- Review ADR draft: {adr_path}
- Approve with: aibrain adr approve {adr_id}
- Or view pending: aibrain adr pending

<promise>ADR_CREATE_COMPLETE</promise>"""

            logger.info(f"✅ ADR creation complete: {adr_id}")

            return {
                "task_id": task_id,
                "status": "completed",
                "adr_number": adr_id,
                "adr_path": str(adr_path),
                "tasks_created": len(task_ids),
                "task_ids": task_ids,
                "iterations": self.current_iteration,
                "output": output
            }

        except Exception as e:
            error_msg = f"ADR creation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "task_id": task_id,
                "status": "failed",
                "reason": error_msg,
                "iterations": self.current_iteration,
                "output": f"Failed: {error_msg}"
            }

    def checkpoint(self) -> Dict[str, Any]:
        """
        Capture current state for session resume.

        Returns:
            Checkpoint dict that can reconstruct agent state
        """
        return {
            "agent_name": self.config.agent_name,
            "project_name": self.config.project_name,
            "current_iteration": self.current_iteration,
            "iteration_history": self.iteration_history,
            "max_iterations": self.config.max_iterations,
            "expected_completion_signal": self.config.expected_completion_signal
        }

    def halt(self, reason: str) -> None:
        """
        Gracefully stop execution.

        Args:
            reason: Why the agent is halting
        """
        logger.warning(f"ADR Creator Agent halting: {reason}")
        logger.info(f"Completed {self.current_iteration} iterations")
        logger.info(f"Iteration history: {len(self.iteration_history)} records")

    def _find_work_queue(self) -> Optional[Path]:
        """Find work queue for current project."""
        tasks_dir = self.orchestrator_root / "tasks"

        # Try project-specific queue first
        project_queue = tasks_dir / f"work_queue_{self.config.project_name}.json"
        if project_queue.exists():
            return project_queue

        # Try generic work_queue.json
        generic_queue = tasks_dir / "work_queue.json"
        if generic_queue.exists():
            return generic_queue

        return None

    def _find_task_by_id(self, queue: WorkQueue, task_id: str) -> Optional[Any]:
        """Find task in queue by ID."""
        for task in queue.features:
            if task.id == task_id:
                return task
        return None

    def _dict_to_adr_context(self, data: Dict[str, Any]) -> ADRContext:
        """Convert dict to ADRContext dataclass."""
        return ADRContext(
            task_id=data.get("task_id", ""),
            description=data.get("description", ""),
            decision_type=data.get("decision_type", "tactical"),
            advisor_type=data.get("advisor_type", "app"),
            confidence=data.get("confidence", 0.75),
            domain_tags=data.get("domain_tags", []),
            aligned_adrs=data.get("aligned_adrs", []),
            conflicting_adrs=data.get("conflicting_adrs", []),
            recommendation=data.get("recommendation", ""),
            iterations=data.get("iterations", 1),
            files_changed=data.get("files_changed", []),
            escalated=data.get("escalated", False),
            escalation_reason=data.get("escalation_reason"),
            fingerprint=data.get("fingerprint", "")
        )

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        import re
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        # Truncate to 50 chars
        return slug[:50].strip('-')
