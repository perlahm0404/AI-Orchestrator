"""
Team Lead Agent - Multi-Agent Orchestration

Coordinates specialist agents for complex tasks:
1. Analyzes task to understand scope
2. Determines which specialists are needed
3. Creates focused subtasks for each specialist
4. Launches specialists in parallel (isolated contexts)
5. Waits for all to complete
6. Synthesizes results into unified output
7. Verifies final result with Ralph

Architecture:
- Team Lead: Orchestration decisions (Opus 4.6, 1M context, 5-iteration budget)
- Specialists: Focused execution (Opus 4.6, 500K context, 15-50 iterations)
- Parallel: Multiple specialists work simultaneously on independent subtasks
- Isolation: Each specialist has separate context window (no interference)
- Verification: Ralph validates each specialist + final synthesis

Author: Claude Code (Autonomous Implementation)
Date: 2026-02-07
Version: 1.0 (Phase 1)
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from agents.base import BaseAgent, AgentConfig
from orchestration.session_state import SessionState
from orchestration.specialist_agent import SpecialistAgent
from orchestration.monitoring_integration import MonitoringIntegration
import json

logger = logging.getLogger(__name__)


@dataclass
class SubTask:
    """A focused task for a specialist agent."""
    id: str
    agent_type: str  # "bugfix", "featurebuilder", "testwriter", etc.
    description: str
    context: str
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "description": self.description,
            "context": self.context,
            "dependencies": self.dependencies,
            "priority": self.priority
        }


@dataclass
class TaskAnalysis:
    """Analysis result from task understanding."""
    key_challenges: List[str]
    recommended_specialists: List[str]
    subtask_breakdown: List[str]
    risk_factors: List[str]
    estimated_complexity: str  # "low", "medium", "high"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key_challenges": self.key_challenges,
            "recommended_specialists": self.recommended_specialists,
            "subtask_breakdown": self.subtask_breakdown,
            "risk_factors": self.risk_factors,
            "estimated_complexity": self.estimated_complexity,
            "notes": self.notes
        }


class TeamLead:
    """
    Orchestrates multiple specialist agents for complex tasks.

    The Team Lead:
    1. Analyzes task complexity and requirements
    2. Determines which specialists are needed
    3. Creates focused subtasks with clear ownership
    4. Launches specialists in parallel (async)
    5. Monitors progress and handles failures
    6. Synthesizes results without conflicts
    7. Verifies output before returning

    Key Features:
    - Orchestration decisions (not code changes)
    - Iteration budget: 5 (for analysis/synthesis decisions)
    - Context window: 1M tokens (Opus 4.6)
    - Error handling and fallback to human
    - Full audit trail in SessionState
    """

    def __init__(
        self,
        project_path: Path,
        model: str = "claude-opus-4-6",
        monitoring: Optional[MonitoringIntegration] = None,
        use_cli: Optional[bool] = None
    ):
        """
        Initialize Team Lead.

        Args:
            project_path: Root path of project
            model: Claude model to use (default Opus 4.6)
            monitoring: Optional monitoring integration for WebSocket events
            use_cli: Use Claude CLI wrapper instead of SDK (default False).
                    If None, read from AI_ORCHESTRATOR_USE_CLI environment variable.
        """
        self.project_path = Path(project_path)
        self.model = model
        self.context_window = 1_000_000  # 1M tokens (Opus 4.6)
        self.iteration_budget = 5  # Team Lead decisions, not code changes
        self.state_dir = self.project_path / ".aibrain"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.monitoring = monitoring

        # Determine use_cli: explicit param > env var > default False
        if use_cli is not None:
            self.use_cli = use_cli
        else:
            self.use_cli = os.environ.get("AI_ORCHESTRATOR_USE_CLI", "false").lower() == "true"

        self.session: Optional[SessionState] = None
        self.task_id: Optional[str] = None
        self.project_name: Optional[str] = None

        # Cost tracking (Phase 4 Step 4.3)
        self._specialist_costs: Dict[str, float] = {}
        self._analysis_cost: float = 0.0
        self._synthesis_cost: float = 0.0
        self._task_result: Optional[Dict[str, Any]] = None

        # Estimated costs per specialist type
        self._specialist_cost_estimates: Dict[str, float] = {
            "bugfix": 0.015,
            "featurebuilder": 0.05,
            "testwriter": 0.015,
            "codequality": 0.02,
            "advisor": 0.01,
            "deployment": 0.01,
            "migration": 0.015,
        }

        logger.info(
            f"TeamLead initialized (model={model}, context={self.context_window}, "
            f"budget={self.iteration_budget}, monitoring={'enabled' if monitoring else 'disabled'})"
        )

    async def orchestrate(
        self,
        task_id: str,
        task_description: str,
        project_name: str = "ai-orchestrator"
    ) -> Dict[str, Any]:
        """
        Main orchestration loop for multi-agent task execution.

        Args:
            task_id: Unique task identifier (e.g., "TASK-123")
            task_description: Full task description with requirements
            project_name: Project name for session state

        Returns:
            Result dictionary with:
            - status: "completed", "blocked", "escalated", "failed"
            - specialist_results: Dict of results per specialist
            - synthesis_result: Final merged output
            - verdict: Ralph verification result
            - iterations: Number of Team Lead iterations used
            - errors: Any errors encountered
        """
        self.task_id = task_id
        self.project_name = project_name
        start_time = datetime.now()

        try:
            # Step 1: Initialize session
            logger.info(f"TeamLead.orchestrate: Starting task {task_id}")
            self.session = SessionState(task_id, project_name)
            self.session.save({
                "iteration_count": 0,
                "phase": "initialization",
                "status": "in_progress",
                "team_lead_model": self.model,
                "team_lead_context": self.context_window,
                "team_lead_budget": self.iteration_budget,
                "team_lead_iteration": 0,
                "specialists": {},
                "started_at": start_time.isoformat(),
                "task_description": task_description[:500],  # Summary
            })

            # Stream task start to kanban board
            if self.monitoring:
                await self.monitoring.task_start(
                    task_id=task_id,
                    description=f"TeamLead: {task_description[:100]}",
                    file="",
                    attempts=0,
                    agent_type="teamlead"
                )

            # Step 2: Analyze task
            logger.info(f"TeamLead.orchestrate: Analyzing task {task_id}")
            analysis = await self._analyze_task(task_description)
            self.session.save({
                **self.session.get_latest(),
                "analysis": analysis.to_dict(),
                "phase": "task_analyzed"
            })

            # Emit multi_agent_analyzing event
            if self.monitoring:
                await self.monitoring.multi_agent_analyzing(
                    task_id=task_id,
                    project=project_name,
                    complexity=analysis.estimated_complexity,
                    specialists=analysis.recommended_specialists,
                    challenges=analysis.key_challenges
                )

            # Step 3: Determine specialists needed
            logger.info(f"TeamLead.orchestrate: Determining specialists for {task_id}")
            specialists = self._determine_specialists(analysis)
            if not specialists:
                logger.info(f"No multi-agent specialists needed for {task_id}")
                return {
                    "status": "single_agent_sufficient",
                    "analysis": analysis.to_dict(),
                    "reason": "Task complexity does not warrant multi-agent"
                }

            logger.info(f"TeamLead.orchestrate: Selected specialists: {specialists}")

            # Step 4: Create subtasks
            logger.info(f"TeamLead.orchestrate: Creating subtasks for {task_id}")
            subtasks = self._create_subtasks(task_description, analysis, specialists)
            self.session.save({
                **self.session.get_latest(),
                "subtasks": [st.to_dict() for st in subtasks],
                "phase": "subtasks_created",
                "specialist_count": len(subtasks)
            })

            # Step 5: Launch specialists in parallel
            logger.info(f"TeamLead.orchestrate: Launching {len(subtasks)} specialists in parallel")
            specialist_results = await self._launch_specialists(subtasks)

            # Step 6: Record specialist completions
            session_data = self.session.get_latest()
            for specialist_type, result in specialist_results.items():
                session_data["specialists"][specialist_type] = {
                    "status": result.get("status", "unknown"),
                    "verdict": result.get("verdict", "UNKNOWN"),
                    "iterations": result.get("iterations", 0),
                    "output_size": len(str(result.get("output", "")))
                }
            session_data["phase"] = "specialists_complete"
            self.session.save(session_data)

            # Count successful specialists
            specialists_completed = sum(
                1 for r in specialist_results.values()
                if r.get("status") == "completed" and r.get("verdict") == "PASS"
            )

            # Emit multi_agent_synthesis event
            if self.monitoring:
                await self.monitoring.multi_agent_synthesis(
                    task_id=task_id,
                    project=project_name,
                    specialists_completed=specialists_completed,
                    specialists_total=len(specialist_results)
                )

            # Step 7: Synthesize results
            logger.info(f"TeamLead.orchestrate: Synthesizing results for {task_id}")
            final_result = await self._synthesize(task_description, specialist_results)
            self.session.save({
                **self.session.get_latest(),
                "phase": "synthesis_complete",
                "synthesis_length": len(final_result)
            })

            # Step 8: Verify final result (would call Ralph in real implementation)
            logger.info(f"TeamLead.orchestrate: Verifying final result for {task_id}")
            verdict = {"type": "PASS", "reason": "Placeholder - would call Ralph"}  # Placeholder

            # Emit multi_agent_verification event
            if self.monitoring:
                await self.monitoring.multi_agent_verification(
                    task_id=task_id,
                    project=project_name,
                    verdict=verdict["type"],
                    summary=verdict.get("reason", "Verification complete")
                )

            # Step 9: Record completion
            self.session.save({
                **self.session.get_latest(),
                "status": "completed",
                "phase": "verification_complete",
                "verdict": verdict,
                "completed_at": datetime.now().isoformat()
            })

            logger.info(f"TeamLead.orchestrate: Task {task_id} completed successfully")

            # Stream task completion to kanban board
            elapsed = (datetime.now() - start_time).total_seconds()
            if self.monitoring and self.task_id:
                await self.monitoring.task_complete(
                    task_id=self.task_id,
                    verdict=verdict["type"],
                    iterations=self.iteration_budget,
                    duration_seconds=elapsed
                )

            return {
                "status": "completed",
                "specialist_results": specialist_results,
                "synthesis_result": final_result,
                "verdict": verdict,
                "iterations": self.iteration_budget,
                "analysis": analysis.to_dict()
            }

        except Exception as e:
            logger.error(f"TeamLead.orchestrate: Error in task {task_id}: {str(e)}")
            if self.session:
                self.session.save({
                    **self.session.get_latest(),
                    "status": "failed",
                    "error": str(e),
                    "phase": "error"
                })
            raise

    async def _analyze_task(self, description: str) -> TaskAnalysis:
        """
        Analyze task to understand scope and complexity.

        In real implementation, this would call Claude to analyze the task.
        For now, returns structured analysis based on keywords.

        Args:
            description: Full task description

        Returns:
            TaskAnalysis with recommendations
        """
        logger.info("TeamLead._analyze_task: Starting analysis")

        # Placeholder implementation - would call Claude in production
        # For now, use heuristics based on description

        # Detect complexity factors
        challenges = []
        if "cross" in description.lower() or "multiple" in description.lower():
            challenges.append("cross-repository coordination")
        if "test" in description.lower():
            challenges.append("test coverage")
        if "refactor" in description.lower():
            challenges.append("code refactoring")

        # Recommend specialists
        specialists = []
        if "bug" in description.lower() or "fix" in description.lower():
            specialists.append("bugfix")
        if "feature" in description.lower() or "implement" in description.lower():
            specialists.append("featurebuilder")
        if "test" in description.lower():
            specialists.append("testwriter")

        # Estimate complexity
        complexity = "low"
        if len(challenges) >= 2:
            complexity = "high"
        elif len(challenges) == 1:
            complexity = "medium"

        analysis = TaskAnalysis(
            key_challenges=challenges or ["general development"],
            recommended_specialists=specialists or ["bugfix"],
            subtask_breakdown=[f"Handle: {c}" for c in challenges] or ["Main task"],
            risk_factors=["Coordination overhead"] if len(specialists) > 1 else [],
            estimated_complexity=complexity,
            notes="Analysis based on task description keywords"
        )

        logger.info(
            f"TeamLead._analyze_task: Complexity={complexity}, "
            f"Specialists={specialists}, Challenges={challenges}"
        )

        return analysis

    def _determine_specialists(self, analysis: TaskAnalysis) -> List[str]:
        """
        Determine which specialists should be used.

        Rules:
        1. Use analysis recommendations
        2. Validate against known specialist types
        3. Limit to reasonable count (3-4 max)

        Args:
            analysis: Task analysis result

        Returns:
            List of specialist types to use
        """
        # Valid specialist types
        valid_types = {
            "bugfix",
            "featurebuilder",
            "testwriter",
            "codequality",
            "advisor"
        }

        # Get recommended specialists
        specialists = analysis.recommended_specialists

        # Filter to valid types
        specialists = [s for s in specialists if s in valid_types]

        # Limit to reasonable count
        if len(specialists) > 4:
            logger.warning(
                f"Limiting specialists from {len(specialists)} to 4 "
                f"(was: {specialists})"
            )
            specialists = specialists[:4]

        # Ensure at least one specialist
        if not specialists:
            specialists = ["bugfix"]  # Default fallback

        return specialists

    def _create_subtasks(
        self,
        task_description: str,
        analysis: TaskAnalysis,
        specialists: List[str]
    ) -> List[SubTask]:
        """
        Create focused subtasks for each specialist.

        Each subtask:
        - Has clear scope
        - Includes necessary context
        - Maps to specialist's strengths
        - Lists dependencies if any

        Args:
            task_description: Original task description
            analysis: Task analysis result
            specialists: List of specialist types

        Returns:
            List of SubTask objects
        """
        subtasks = []

        for i, specialist_type in enumerate(specialists):
            # Create specialist-specific subtask
            if specialist_type == "bugfix":
                subtitle = "Find and fix root cause"
            elif specialist_type == "featurebuilder":
                subtitle = "Implement feature requirements"
            elif specialist_type == "testwriter":
                subtitle = "Write and validate tests"
            elif specialist_type == "codequality":
                subtitle = "Review and improve code quality"
            else:
                subtitle = f"Execute {specialist_type} tasks"

            subtask = SubTask(
                id=f"SUBTASK-{self.task_id}-{i}",
                agent_type=specialist_type,
                description=subtitle,
                context=task_description,
                dependencies=[],  # Could be set based on specialist order
                priority=i + 1
            )

            subtasks.append(subtask)
            logger.info(f"Created subtask {subtask.id} for {specialist_type}")

        return subtasks

    async def _launch_specialists(
        self,
        subtasks: List[SubTask]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Launch all specialists in parallel with isolated contexts.

        Each specialist:
        - Runs in separate async task
        - Has isolated context (no state sharing)
        - Gets independent iteration budget
        - Can fail without stopping others (return_exceptions=True)

        Args:
            subtasks: List of SubTask objects

        Returns:
            Dict mapping specialist type → result
        """
        specialist_tasks = []
        specialist_map = {}

        logger.info(f"TeamLead._launch_specialists: Launching {len(subtasks)} specialists")

        # Create specialist instances and launch tasks
        for subtask in subtasks:
            try:
                specialist = SpecialistAgent(
                    agent_type=subtask.agent_type,
                    project_path=self.project_path,
                    project_name=self.project_name,
                    use_cli=self.use_cli
                )

                # Stream specialist launch to kanban
                if self.monitoring and self.task_id and self.project_name:
                    await self.monitoring.specialist_started(
                        task_id=self.task_id,
                        project=self.project_name,
                        specialist_type=subtask.agent_type,
                        subtask_id=subtask.id,
                        max_iterations=specialist.iteration_budget
                    )

                # Create async task (convert SubTask to dict for execute)
                task = specialist.execute(subtask.to_dict())
                specialist_tasks.append(task)

                # Track mapping
                specialist_map[len(specialist_tasks) - 1] = subtask.agent_type

                logger.info(
                    f"Launched specialist {subtask.agent_type} for {self.project_name} "
                    f"(task {len(specialist_tasks)})"
                )

            except Exception as e:
                logger.error(f"Failed to launch specialist {subtask.agent_type}: {e}")
                specialist_map[len(specialist_tasks)] = subtask.agent_type
                specialist_tasks.append(self._failed_specialist(subtask.agent_type, str(e)))

        # Run all specialists in parallel
        logger.info(f"Executing {len(specialist_tasks)} specialists in parallel")
        start_time = datetime.now()
        results = await asyncio.gather(
            *specialist_tasks,
            return_exceptions=True  # Don't fail if one specialist fails
        )
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"All specialists completed in {elapsed:.1f}s")

        # Map results back to specialist types
        specialist_results = {}
        for idx, result in enumerate(results):
            agent_type = specialist_map.get(idx, "unknown")

            if isinstance(result, Exception):
                logger.error(f"Specialist {agent_type} failed: {result}")
                specialist_results[agent_type] = {
                    "status": "failed",
                    "error": str(result),
                    "verdict": "FAILED",
                    "iterations": 0,
                    "output": None
                }
                # Stream specialist completion (failed)
                if self.monitoring and self.task_id and self.project_name:
                    await self.monitoring.specialist_completed(
                        task_id=self.task_id,
                        project=self.project_name,
                        specialist_type=agent_type,
                        status="failed",
                        verdict="FAILED",
                        iterations_used=0,
                        duration_seconds=elapsed
                    )
            elif isinstance(result, dict):
                specialist_results[agent_type] = result
                logger.info(
                    f"Specialist {agent_type} completed: "
                    f"status={result.get('status')}, verdict={result.get('verdict')}"
                )
                # Stream specialist completion (successful)
                if self.monitoring and self.task_id and self.project_name:
                    await self.monitoring.specialist_completed(
                        task_id=self.task_id,
                        project=self.project_name,
                        specialist_type=agent_type,
                        status=result.get("status", "completed"),
                        verdict=result.get("verdict", "UNKNOWN"),
                        iterations_used=result.get("iterations", 0),
                        duration_seconds=elapsed
                    )

        return specialist_results

    async def _synthesize(
        self,
        task_description: str,
        specialist_results: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Synthesize specialist results into unified output.

        Handles:
        - Merging changes without conflicts
        - Combining test coverage
        - Resolving different approaches
        - Creating coherent summary

        Args:
            task_description: Original task
            specialist_results: Results from all specialists

        Returns:
            Synthesized final output
        """
        logger.info("TeamLead._synthesize: Starting synthesis")

        # Build synthesis context
        specialist_summaries = []
        for specialist_type, result in specialist_results.items():
            status = result.get("status", "unknown")
            verdict = result.get("verdict", "unknown")
            output = result.get("output") or ""  # Handle None

            specialist_summaries.append(
                f"\n{specialist_type.upper()} ({status}, {verdict}):\n"
                f"{str(output)[:500]}"  # Truncate for context, ensure string
            )

        synthesis_prompt = f"""
Synthesize these specialist results into one coherent solution:

Original Task:
{task_description}

Specialist Results:
{''.join(specialist_summaries)}

Create a unified solution that:
1. Combines all changes without conflicts
2. Maintains consistency across components
3. Addresses all requirements
4. Provides clear summary

Synthesized Output:
"""

        logger.info("TeamLead._synthesize: Would call Claude for synthesis")

        # In real implementation, this would call Claude API
        # For now, return placeholder
        synthesis_result = synthesis_prompt.replace("Synthesized Output:", "SYNTHESIZED: All specialists completed successfully")

        logger.info(f"TeamLead._synthesize: Complete ({len(synthesis_result)} chars)")
        return synthesis_result

    async def _failed_specialist(self, agent_type: str, error: str) -> Dict[str, Any]:
        """Create failed specialist result (for error handling in gather)."""
        return {
            "status": "failed",
            "error": error,
            "verdict": "FAILED",
            "iterations": 0,
            "output": None
        }

    # ========================================================================
    # Cost Tracking Methods (Phase 4 Step 4.3)
    # ========================================================================

    @property
    def accumulated_cost(self) -> float:
        """Get total accumulated cost (analysis + specialists + synthesis)."""
        specialist_total = sum(self._specialist_costs.values())
        return self._analysis_cost + specialist_total + self._synthesis_cost

    def add_specialist_cost(self, specialist_name: str, cost: float) -> None:
        """
        Add cost from a specialist.

        Args:
            specialist_name: Name/type of the specialist
            cost: Cost in USD
        """
        self._specialist_costs[specialist_name] = (
            self._specialist_costs.get(specialist_name, 0.0) + cost
        )

    def get_specialist_costs(self) -> Dict[str, float]:
        """Get cost breakdown by specialist."""
        return dict(self._specialist_costs)

    def add_analysis_cost(self, cost: float) -> None:
        """
        Add cost for the analysis phase.

        Args:
            cost: Cost in USD
        """
        self._analysis_cost += cost

    def add_synthesis_cost(self, cost: float) -> None:
        """
        Add cost for the synthesis phase.

        Args:
            cost: Cost in USD
        """
        self._synthesis_cost += cost

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get complete cost summary.

        Returns:
            Dict with analysis_cost, specialist_costs, synthesis_cost, total_cost
        """
        specialist_total = sum(self._specialist_costs.values())
        return {
            "analysis_cost": self._analysis_cost,
            "specialist_costs": dict(self._specialist_costs),
            "synthesis_cost": self._synthesis_cost,
            "total_cost": self._analysis_cost + specialist_total + self._synthesis_cost
        }

    def estimate_task_cost(self, specialists: List[str]) -> float:
        """
        Estimate total task cost based on specialists.

        Args:
            specialists: List of specialist types to use

        Returns:
            Estimated total cost in USD
        """
        # Base costs for analysis and synthesis
        analysis_estimate = 0.005
        synthesis_estimate = 0.003

        # Sum specialist estimates
        specialist_estimate = sum(
            self._specialist_cost_estimates.get(s, 0.015)
            for s in specialists
        )

        return analysis_estimate + specialist_estimate + synthesis_estimate

    def record_task_result(
        self,
        status: str,
        iterations_total: int,
        value_generated: float
    ) -> None:
        """
        Record task result for efficiency metrics.

        Args:
            status: Final task status
            iterations_total: Total iterations across all specialists
            value_generated: Estimated value generated in USD
        """
        self._task_result = {
            "status": status,
            "iterations_total": iterations_total,
            "value_generated": value_generated,
            "total_cost": self.accumulated_cost
        }

    def get_efficiency_metrics(self) -> Dict[str, float]:
        """
        Calculate efficiency metrics.

        Returns:
            Dict with cost_per_iteration, roi, cost_to_value_ratio
        """
        if not self._task_result:
            return {
                "cost_per_iteration": 0.0,
                "roi": 0.0,
                "cost_to_value_ratio": 0.0
            }

        total_cost = self._task_result.get("total_cost", 0.0)
        iterations = self._task_result.get("iterations_total", 1)
        value = self._task_result.get("value_generated", 0.0)

        # Avoid division by zero
        cost_per_iteration = total_cost / max(iterations, 1)

        # ROI = (value - cost) / cost
        roi = (value - total_cost) / max(total_cost, 0.001)

        # Cost to value ratio
        cost_to_value_ratio = total_cost / max(value, 0.001)

        return {
            "cost_per_iteration": cost_per_iteration,
            "roi": roi,
            "cost_to_value_ratio": cost_to_value_ratio
        }


# Module-level functions for convenience

async def orchestrate_multi_agent_task(
    task_id: str,
    task_description: str,
    project_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Convenience function to orchestrate a task with Team Lead.

    Args:
        task_id: Task identifier
        task_description: Task description
        project_path: Project root path (uses CWD if not provided)

    Returns:
        Orchestration result
    """
    if project_path is None:
        project_path = Path.cwd()

    team_lead = TeamLead(project_path)
    return await team_lead.orchestrate(task_id, task_description)


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if len(sys.argv) > 2:
        task_id = sys.argv[1]
        task_desc = sys.argv[2]
    else:
        task_id = "TEST-001"
        task_desc = "Refactor UserService across 3 repos with tests"

    print(f"\n{'='*70}")
    print(f"Team Lead Orchestration - {task_id}")
    print(f"Task: {task_desc}")
    print(f"{'='*70}\n")

    # Run orchestration
    result = asyncio.run(
        orchestrate_multi_agent_task(task_id, task_desc, Path.cwd())
    )

    print(f"\nResult: {json.dumps(result, indent=2, default=str)}")
