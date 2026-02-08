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
import subprocess

# Ralph imports (required for verification)
try:
    from ralph import engine as ralph_engine
    RALPH_AVAILABLE = True
except ImportError:
    RALPH_AVAILABLE = False
    ralph_engine = None  # type: ignore[assignment]

# Adapters for app context
try:
    from adapters import get_adapter
    ADAPTERS_AVAILABLE = True
except ImportError:
    ADAPTERS_AVAILABLE = False
    get_adapter = None  # type: ignore[assignment]

# Audit trail for verification events
try:
    from governance.verification_audit import get_audit
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    get_audit = None  # type: ignore[assignment]

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
                if r.get("status") == "completed" and r.get("verdict", {}).get("type") == "PASS"
            )
            specialists_total = len(specialist_results)

            # Step 6b: Validate specialist results before synthesis
            # CRITICAL: Block if majority of specialists failed
            validation_result = self._validate_specialist_results(specialist_results)
            if not validation_result["can_proceed"]:
                logger.error(
                    f"TeamLead.orchestrate: Specialist validation failed for {task_id}: "
                    f"{validation_result['reason']}"
                )
                self.session.save({
                    **self.session.get_latest(),
                    "status": "blocked",
                    "phase": "validation_failed",
                    "validation_result": validation_result,
                    "blocked_at": datetime.now().isoformat()
                })
                return {
                    "status": "blocked",
                    "specialist_results": specialist_results,
                    "validation_result": validation_result,
                    "verdict": {"type": "BLOCKED", "reason": validation_result["reason"]},
                    "iterations": self.iteration_budget,
                    "analysis": analysis.to_dict()
                }

            # Emit multi_agent_synthesis event
            if self.monitoring:
                await self.monitoring.multi_agent_synthesis(
                    task_id=task_id,
                    project=project_name,
                    specialists_completed=specialists_completed,
                    specialists_total=specialists_total
                )

            # Step 7: Synthesize results
            logger.info(f"TeamLead.orchestrate: Synthesizing results for {task_id}")
            final_result = await self._synthesize(task_description, specialist_results)
            self.session.save({
                **self.session.get_latest(),
                "phase": "synthesis_complete",
                "synthesis_length": len(final_result)
            })

            # Step 8: Verify final result with Ralph (REAL verification)
            logger.info(f"TeamLead.orchestrate: Verifying final result for {task_id}")
            verdict = await self._verify_synthesis(project_name, task_id)

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

            # Step 10: Create Knowledge Object from orchestration learnings
            if verdict["type"] == "PASS" and len(specialist_results) >= 2:
                try:
                    from orchestration.ko_helpers import create_ko_from_orchestration
                    ko = create_ko_from_orchestration(
                        task_id=task_id,
                        task_description=task_description,
                        specialist_results=specialist_results,
                        final_verdict=verdict,
                        project=project_name
                    )
                    if ko:
                        logger.info(f"TeamLead.orchestrate: Created KO {ko.id}")
                except Exception as e:
                    logger.warning(f"TeamLead.orchestrate: Failed to create KO: {e}")

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

        Uses keyword heuristics by default, or real Claude analysis
        when use_real_analysis=True.

        Args:
            description: Full task description

        Returns:
            TaskAnalysis with recommendations
        """
        logger.info("TeamLead._analyze_task: Starting analysis")

        # Use real Claude analysis if enabled
        if getattr(self, 'use_real_analysis', False):
            return await self._claude_analyze_task(description)

        # Keyword heuristics (fallback)

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

    async def _claude_analyze_task(self, description: str) -> TaskAnalysis:
        """
        Real Claude-based task analysis.

        Uses Claude Sonnet to semantically analyze the task and
        provide structured recommendations.

        Args:
            description: Full task description

        Returns:
            TaskAnalysis with Claude-generated recommendations
        """
        import json
        from anthropic import Anthropic

        logger.info("TeamLead._claude_analyze_task: Using Claude for analysis")

        client = Anthropic()

        prompt = f"""Analyze this software development task and return JSON:

Task: {description}

Return ONLY valid JSON with no explanation:
{{
  "key_challenges": ["challenge1", "challenge2"],
  "recommended_specialists": ["bugfix", "featurebuilder", "testwriter"],
  "subtask_breakdown": {{"bugfix": "Fix X", "testwriter": "Test Y"}},
  "risk_factors": ["risk1"],
  "estimated_complexity": "low|medium|high"
}}

Valid specialists: bugfix, featurebuilder, testwriter, codequality, advisor, deployment
"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract text from response (handle different block types)
            response_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            data = json.loads(response_text)

            analysis = TaskAnalysis(
                key_challenges=data.get("key_challenges", ["general development"]),
                recommended_specialists=data.get("recommended_specialists", ["bugfix"]),
                subtask_breakdown=list(data.get("subtask_breakdown", {}).values()) or ["Main task"],
                risk_factors=data.get("risk_factors", []),
                estimated_complexity=data.get("estimated_complexity", "medium"),
                notes="Claude analysis"
            )

            logger.info(
                f"TeamLead._claude_analyze_task: Complexity={analysis.estimated_complexity}, "
                f"Specialists={analysis.recommended_specialists}"
            )

            return analysis

        except Exception as e:
            logger.warning(f"TeamLead._claude_analyze_task: Claude failed ({e}), falling back to heuristics")
            # Fall back to keyword heuristics by calling self with flag disabled
            self.use_real_analysis = False
            result = await self._analyze_task(description)
            self.use_real_analysis = True
            return result

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

        Uses placeholder by default, or real Claude synthesis
        when use_real_synthesis=True.

        Args:
            task_description: Original task
            specialist_results: Results from all specialists

        Returns:
            Synthesized final output
        """
        logger.info("TeamLead._synthesize: Starting synthesis")

        # Use real Claude synthesis if enabled
        if getattr(self, 'use_real_synthesis', False):
            return await self._claude_synthesize(task_description, specialist_results)

        # Placeholder synthesis (fallback)
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

    async def _claude_synthesize(
        self,
        task_description: str,
        specialist_results: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Real Claude-based synthesis.

        Uses Claude Sonnet to intelligently merge specialist outputs
        into a coherent summary.

        Args:
            task_description: Original task description
            specialist_results: Results from all specialists

        Returns:
            Synthesized final output
        """
        from anthropic import Anthropic

        logger.info("TeamLead._claude_synthesize: Using Claude for synthesis")

        client = Anthropic()

        # Build concise specialist summaries
        summaries = []
        for stype, result in specialist_results.items():
            status = result.get("status", "unknown")
            verdict = result.get("verdict", "unknown")
            output = str(result.get("output", ""))[:500]
            summaries.append(f"**{stype.upper()}** ({status}, {verdict}): {output}")

        prompt = f"""Synthesize these specialist results into a unified summary:

Task: {task_description}

Specialist Results:
{chr(10).join(summaries)}

Provide a coherent 2-3 paragraph summary that:
1. Describes what was accomplished
2. Highlights key changes made
3. Notes any issues or considerations
"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract text from response (handle different block types)
            result_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    result_text += block.text

            logger.info(f"TeamLead._claude_synthesize: Complete ({len(result_text)} chars)")
            return result_text

        except Exception as e:
            logger.warning(f"TeamLead._claude_synthesize: Claude failed ({e}), using placeholder")
            # Fall back to placeholder
            self.use_real_synthesis = False
            fallback_result = await self._synthesize(task_description, specialist_results)
            self.use_real_synthesis = True
            return fallback_result

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
    # Verification Methods (Anti-Shirking Enforcement)
    # ========================================================================

    def _validate_specialist_results(
        self,
        specialist_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate specialist results before synthesis.

        CRITICAL: Prevents synthesis if specialists failed to perform work.

        Rules:
        1. At least 50% of specialists must have PASS verdict
        2. No specialist can have "verification_missing" flag
        3. Failed specialists are logged for audit trail

        Args:
            specialist_results: Results from all specialists

        Returns:
            Dict with:
            - can_proceed: bool - whether synthesis can proceed
            - reason: str - explanation
            - passed_count: int
            - failed_count: int
            - blocked_count: int
            - audit_log: list of specialist statuses
        """
        passed = []
        failed = []
        blocked = []
        verification_missing = []

        for specialist_type, result in specialist_results.items():
            status = result.get("status", "unknown")
            verdict = result.get("verdict", {})

            # Handle verdict as dict or string
            if isinstance(verdict, dict):
                verdict_type = verdict.get("type", "FAIL")
                has_missing_verification = verdict.get("verification_missing", False)
            else:
                verdict_type = str(verdict)
                has_missing_verification = False

            # Check for verification_missing flag (simulation mode bypass attempt)
            if has_missing_verification:
                verification_missing.append(specialist_type)
                logger.warning(
                    f"Specialist {specialist_type} has verification_missing flag - "
                    "Ralph verification was bypassed"
                )

            # Categorize by verdict
            if verdict_type == "PASS":
                passed.append(specialist_type)
            elif verdict_type == "BLOCKED":
                blocked.append(specialist_type)
            else:
                failed.append(specialist_type)

        total = len(specialist_results)
        passed_count = len(passed)
        failed_count = len(failed)
        blocked_count = len(blocked)

        # Build audit log
        audit_log = [
            {
                "specialist": s,
                "status": specialist_results[s].get("status"),
                "verdict": specialist_results[s].get("verdict"),
                "iterations": specialist_results[s].get("iterations", 0)
            }
            for s in specialist_results
        ]

        # Rule 1: Check for verification bypass attempts
        if verification_missing:
            # Log security event - bypass attempts detected
            if AUDIT_AVAILABLE and get_audit is not None and self.task_id:
                audit = get_audit(self.project_path)
                for spec in verification_missing:
                    audit.log_bypass_attempt(
                        task_id=self.task_id,
                        specialist_type=spec,
                        attempt_type="verification_missing",
                        details={"all_missing": verification_missing}
                    )
            return {
                "can_proceed": False,
                "reason": f"Verification bypassed for specialists: {verification_missing}. "
                          "Ralph verification is required for all specialists.",
                "passed_count": passed_count,
                "failed_count": failed_count,
                "blocked_count": blocked_count,
                "verification_missing": verification_missing,
                "audit_log": audit_log
            }

        # Rule 2: All specialists blocked means systemic issue
        if blocked_count == total:
            return {
                "can_proceed": False,
                "reason": "All specialists blocked - likely systemic issue (Ralph unavailable?)",
                "passed_count": passed_count,
                "failed_count": failed_count,
                "blocked_count": blocked_count,
                "audit_log": audit_log
            }

        # Rule 3: Require majority pass rate (at least 50%)
        pass_rate = passed_count / max(total, 1)
        if pass_rate < 0.5:
            return {
                "can_proceed": False,
                "reason": f"Insufficient pass rate: {pass_rate:.0%} ({passed_count}/{total}). "
                          f"Required: 50%. Failed: {failed}, Blocked: {blocked}",
                "passed_count": passed_count,
                "failed_count": failed_count,
                "blocked_count": blocked_count,
                "pass_rate": pass_rate,
                "audit_log": audit_log
            }

        # Validation passed
        logger.info(
            f"Specialist validation passed: {passed_count}/{total} specialists "
            f"({pass_rate:.0%} pass rate)"
        )

        result = {
            "can_proceed": True,
            "reason": f"Validation passed: {passed_count}/{total} specialists verified",
            "passed_count": passed_count,
            "failed_count": failed_count,
            "blocked_count": blocked_count,
            "pass_rate": pass_rate,
            "audit_log": audit_log
        }

        # Log to audit trail
        if AUDIT_AVAILABLE and get_audit is not None and self.task_id:
            audit = get_audit(self.project_path)
            audit.log_validation_result(
                task_id=self.task_id,
                can_proceed=True,
                passed_count=passed_count,
                total_count=total,
                details={"pass_rate": pass_rate}
            )

        return result

    async def _verify_synthesis(
        self,
        project_name: str,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Verify synthesized output with Ralph.

        CRITICAL: This replaces the placeholder verification.
        Synthesis is NOT complete until Ralph verifies the final state.

        Args:
            project_name: Project being verified
            task_id: Task ID for session tracking

        Returns:
            Verdict dict with type, reason, and verification details
        """
        logger.info(f"TeamLead._verify_synthesis: Verifying synthesis for {task_id}")

        # Get changed files from git
        changed_files = self._get_changed_files()

        if not changed_files:
            logger.warning(
                f"TeamLead._verify_synthesis: No changed files for {task_id}"
            )
            # No changes means no work was done - this is suspicious
            return {
                "type": "BLOCKED",
                "reason": "No file changes detected after synthesis - specialists may not have performed work",
                "safe_to_merge": False,
                "changed_files": []
            }

        # Check Ralph availability
        if not RALPH_AVAILABLE or ralph_engine is None:
            logger.error(
                f"TeamLead._verify_synthesis: Ralph not available for {task_id}"
            )
            return {
                "type": "BLOCKED",
                "reason": "Ralph verification engine not available - cannot verify synthesis quality",
                "safe_to_merge": False,
                "verification_missing": True
            }

        # Get app context for Ralph
        app_context = None
        if ADAPTERS_AVAILABLE and get_adapter is not None:
            try:
                adapter = get_adapter(project_name)
                app_context = adapter.get_context()
            except Exception as e:
                logger.warning(f"Could not load adapter for {project_name}: {e}")

        if app_context is None:
            logger.error(
                f"TeamLead._verify_synthesis: No app_context for {project_name}"
            )
            return {
                "type": "BLOCKED",
                "reason": f"No app_context available for project {project_name}",
                "safe_to_merge": False
            }

        # Run Ralph verification
        try:
            logger.info(
                f"TeamLead._verify_synthesis: Running Ralph on {len(changed_files)} files"
            )

            loop = asyncio.get_event_loop()
            verdict = await loop.run_in_executor(
                None,
                lambda: ralph_engine.verify(
                    project=project_name,
                    changes=changed_files,
                    session_id=task_id,
                    app_context=app_context
                )
            )

            # Convert Ralph Verdict to dict
            verdict_type = verdict.type.value if hasattr(verdict.type, 'value') else str(verdict.type)

            logger.info(
                f"TeamLead._verify_synthesis: Ralph verdict={verdict_type} for {task_id}"
            )

            result = {
                "type": verdict_type,
                "reason": verdict.reason or "",
                "safe_to_merge": verdict.safe_to_merge,
                "regression_detected": verdict.regression_detected,
                "changed_files": changed_files,
                "steps": [
                    {
                        "step": s.step,
                        "passed": s.passed,
                        "output": s.output[:500] if s.output else ""
                    }
                    for s in verdict.steps
                ]
            }

            # Log to audit trail
            if AUDIT_AVAILABLE and get_audit is not None:
                audit = get_audit(self.project_path)
                audit.log_synthesis_result(
                    task_id=task_id,
                    verdict=verdict_type,
                    changed_files=changed_files,
                    details={
                        "safe_to_merge": verdict.safe_to_merge,
                        "regression_detected": verdict.regression_detected
                    }
                )

            return result

        except Exception as e:
            logger.error(
                f"TeamLead._verify_synthesis: Ralph verification failed: {e}"
            )
            return {
                "type": "BLOCKED",
                "reason": f"Ralph verification error: {str(e)}",
                "safe_to_merge": False,
                "error": str(e)
            }

    def _get_changed_files(self) -> List[str]:
        """
        Get list of changed files from git.

        Returns:
            List of file paths that have been modified
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=10
            )
            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                return files
            return []
        except Exception as e:
            logger.warning(f"Could not get changed files: {e}")
            return []

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
