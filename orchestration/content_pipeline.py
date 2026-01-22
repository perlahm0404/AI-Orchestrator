"""
Content Pipeline - 7-stage workflow orchestrator for editorial automation

Implements multi-stage workflow with approval gates:
PREPARATION → RESEARCH → GENERATION → VALIDATION → REVIEW → PUBLICATION → COMPLETE

Features:
- State persistence to .aibrain/pipeline-{content_id}.md (Markdown + YAML)
- Resume capability after interruptions
- Decision tree: SUCCESS→PROCEED, FAIL→RETRY, BLOCKED→ASK_HUMAN
- Integration with IterationLoop, ContentValidator, BrowserAutomation, ApprovalGate

Usage:
    from orchestration.content_pipeline import ContentPipeline
    from agents.editorial.editorial_agent import EditorialTask

    pipeline = ContentPipeline(adapter, keyword_strategy)
    result = pipeline.run(editorial_task, resume=False, non_interactive=False)

Implementation: Phase 5 - Editorial Automation
"""

from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import yaml
import shutil
import time

from agents.editorial.editorial_agent import EditorialTask


class PipelineStage(Enum):
    """Pipeline execution stages"""
    PREPARATION = "preparation"
    RESEARCH = "research"
    GENERATION = "generation"
    VALIDATION = "validation"
    REVIEW = "review"
    PUBLICATION = "publication"
    COMPLETE = "complete"


class StageDecision(Enum):
    """Decision after stage execution"""
    PROCEED = "proceed"      # Advance to next stage
    RETRY = "retry"          # Retry current stage
    ASK_HUMAN = "ask_human"  # Requires human decision
    ABORT = "abort"          # Fatal error, cannot continue


@dataclass
class StageResult:
    """Result of a pipeline stage execution"""
    stage: PipelineStage
    status: str  # "success" | "failed" | "blocked"
    artifacts: Dict[str, Any] = field(default_factory=dict)  # Stage outputs
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration: float = 0.0  # seconds


@dataclass
class PipelineState:
    """Persistent state for content pipeline"""
    content_id: str
    current_stage: PipelineStage
    iteration: int
    max_iterations: int
    started_at: str
    task: EditorialTask
    draft_path: Optional[str] = None
    seo_score: Optional[int] = None
    validation_issues: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    research_data: Optional[Dict[str, Any]] = None


@dataclass
class PipelineResult:
    """Final result of content pipeline execution"""
    content_id: str
    status: str  # "completed" | "failed" | "blocked" | "aborted"
    iterations: int
    draft_path: Optional[str] = None
    published_path: Optional[str] = None
    verdict: Any = None
    reason: str = ""
    seo_score: Optional[int] = None


class ContentPipeline:
    """
    7-stage workflow orchestrator for editorial automation.

    Extends (not replaces) IterationLoop pattern with stage management,
    approval gates, and browser automation orchestration.
    """

    # Stage progression map
    STAGE_PROGRESSION = {
        PipelineStage.PREPARATION: PipelineStage.RESEARCH,
        PipelineStage.RESEARCH: PipelineStage.GENERATION,
        PipelineStage.GENERATION: PipelineStage.VALIDATION,
        PipelineStage.VALIDATION: PipelineStage.REVIEW,
        PipelineStage.REVIEW: PipelineStage.PUBLICATION,
        PipelineStage.PUBLICATION: PipelineStage.COMPLETE,
        PipelineStage.COMPLETE: None
    }

    # Iteration budgets per stage
    STAGE_BUDGETS = {
        PipelineStage.RESEARCH: 5,
        PipelineStage.GENERATION: 10,
        PipelineStage.VALIDATION: 5,
        PipelineStage.PUBLICATION: 3
    }

    def __init__(self, adapter: Any, keyword_strategy: Optional[Dict[str, Any]] = None):
        """
        Initialize content pipeline.

        Args:
            adapter: Application adapter (e.g., CredentialMate adapter)
            keyword_strategy: Optional keyword strategy dict (from YAML)
        """
        self.adapter = adapter
        self.app_context = adapter.get_context()
        self.keyword_strategy = keyword_strategy or {}

        # State tracking
        self.state: Optional[PipelineState] = None
        self.state_dir = Path(".aibrain")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Paths
        self.drafts_dir = Path.cwd() / "blog" / self.app_context.project_name / "drafts"
        self.published_dir = Path.cwd() / "blog" / self.app_context.project_name / "published"
        self.rejected_dir = self.state_dir / "rejected"

        # Ensure directories exist
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.published_dir.mkdir(parents=True, exist_ok=True)
        self.rejected_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        task: EditorialTask,
        resume: bool = False,
        non_interactive: bool = False,
        max_iterations: int = 20
    ) -> PipelineResult:
        """
        Run 7-stage content pipeline.

        Args:
            task: Editorial task to execute
            resume: Resume from saved state if True
            non_interactive: Skip approval gates if True (auto-approve)
            max_iterations: Global iteration budget

        Returns:
            PipelineResult with final status
        """
        # Load or create state
        if resume:
            self.state = self._load_state(task.task_id)
            if self.state:
                print(f"♻️ Resuming from stage {self.state.current_stage.value} (iteration {self.state.iteration})")

        if not self.state:
            self.state = PipelineState(
                content_id=task.task_id,
                current_stage=PipelineStage.PREPARATION,
                iteration=0,
                max_iterations=max_iterations,
                started_at=datetime.now().isoformat(),
                task=task
            )

        # Main execution loop
        while self.state.current_stage != PipelineStage.COMPLETE:
            # Check global iteration budget
            if self.state.iteration >= self.state.max_iterations:
                print(f"⚠️  Max iterations ({self.state.max_iterations}) reached")
                return PipelineResult(
                    content_id=task.task_id,
                    status="failed",
                    iterations=self.state.iteration,
                    reason="Max iterations reached"
                )

            # Execute current stage
            print(f"\n--- Stage: {self.state.current_stage.value.upper()} (iteration {self.state.iteration + 1}) ---")
            stage_result = self._execute_stage(self.state.current_stage, non_interactive)

            # Record stage in history
            self.state.stage_history.append({
                "stage": self.state.current_stage.value,
                "status": stage_result.status,
                "iteration": self.state.iteration,
                "duration": stage_result.duration,
                "errors": stage_result.errors,
                "warnings": stage_result.warnings
            })

            # Make decision based on result
            decision = self._make_decision(stage_result)

            # Handle decision
            if decision == StageDecision.PROCEED:
                # Advance to next stage
                next_stage = self.STAGE_PROGRESSION[self.state.current_stage]
                if next_stage:
                    self.state.current_stage = next_stage
                    self.state.iteration += 1
                else:
                    # Reached COMPLETE
                    self.state.current_stage = PipelineStage.COMPLETE

                # Save state
                self._save_state()

            elif decision == StageDecision.RETRY:
                # Retry current stage
                self.state.iteration += 1
                self._save_state()
                print(f"🔄 Retrying {self.state.current_stage.value}...")
                continue

            elif decision == StageDecision.ASK_HUMAN:
                # Blocked - requires human intervention
                self._save_state()
                return PipelineResult(
                    content_id=task.task_id,
                    status="blocked",
                    iterations=self.state.iteration,
                    draft_path=self.state.draft_path,
                    seo_score=self.state.seo_score,
                    reason=f"Blocked at {self.state.current_stage.value}: {', '.join(stage_result.errors)}"
                )

            else:  # ABORT
                # Fatal error
                self._save_state()
                return PipelineResult(
                    content_id=task.task_id,
                    status="aborted",
                    iterations=self.state.iteration,
                    reason=f"Aborted at {self.state.current_stage.value}: {', '.join(stage_result.errors)}"
                )

        # Pipeline complete
        self._cleanup_state()
        return PipelineResult(
            content_id=task.task_id,
            status="completed",
            iterations=self.state.iteration,
            draft_path=self.state.draft_path,
            published_path=str(self.published_dir / Path(self.state.draft_path).name) if self.state.draft_path else None,
            seo_score=self.state.seo_score,
            reason="Pipeline completed successfully"
        )

    def _execute_stage(self, stage: PipelineStage, non_interactive: bool = False) -> StageResult:
        """
        Execute a pipeline stage.

        Args:
            stage: Stage to execute
            non_interactive: Skip approval gates if True

        Returns:
            StageResult with status and artifacts
        """
        start_time = time.time()

        # Dispatch to stage handler
        if stage == PipelineStage.PREPARATION:
            result = self._stage_preparation()
        elif stage == PipelineStage.RESEARCH:
            result = self._stage_research()
        elif stage == PipelineStage.GENERATION:
            result = self._stage_generation()
        elif stage == PipelineStage.VALIDATION:
            result = self._stage_validation()
        elif stage == PipelineStage.REVIEW:
            result = self._stage_review(non_interactive)
        elif stage == PipelineStage.PUBLICATION:
            result = self._stage_publication()
        else:
            result = StageResult(
                stage=stage,
                status="failed",
                errors=[f"Unknown stage: {stage}"]
            )

        result.duration = time.time() - start_time
        return result

    def _stage_preparation(self) -> StageResult:
        """
        PREPARATION stage: Parse and validate task specification.

        Returns:
            StageResult with validation outcome
        """
        assert self.state is not None, "Pipeline state must be initialized"
        errors = []

        # Validate task fields
        if not self.state.task.task_id:
            errors.append("Missing task_id")
        if not self.state.task.topic:
            errors.append("Missing topic")
        if not self.state.task.keywords:
            errors.append("Missing keywords")

        if errors:
            return StageResult(
                stage=PipelineStage.PREPARATION,
                status="failed",
                errors=errors
            )

        print(f"✅ Task validated: {self.state.task.topic}")
        return StageResult(
            stage=PipelineStage.PREPARATION,
            status="success",
            artifacts={"task": self.state.task}
        )

    def _stage_research(self) -> StageResult:
        """
        RESEARCH stage: Browser automation scraping.

        Returns:
            StageResult with research data
        """
        assert self.state is not None, "Pipeline state must be initialized"
        from adapters.browser_automation import BrowserAutomationClient

        # If research already done (retry scenario), reuse it
        if self.state.research_data:
            print("♻️ Reusing existing research data")
            return StageResult(
                stage=PipelineStage.RESEARCH,
                status="success",
                artifacts={"research_data": self.state.research_data}
            )

        client = BrowserAutomationClient()
        session_id = f"{self.state.content_id}-research"

        research_data = {
            "regulatory_updates": [],
            "competitor_analysis": [],
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Create browser session
            client.create_session({
                "sessionId": session_id,
                "headless": True,
                "auditLogPath": str(self.state_dir / f"browser-audit-{session_id}.jsonl")
            })

            # Separate sources by type
            regulatory_sources = [
                s for s in self.state.task.research_sources
                if ".gov" in s or "state" in s.lower()
            ]
            competitor_sources = [
                s for s in self.state.task.research_sources
                if s not in regulatory_sources
            ]

            # Scrape regulatory sources
            for source in regulatory_sources:
                try:
                    state_name = self._extract_state_from_url(source)
                    updates = client.scrape_regulatory_updates(
                        session_id=session_id,
                        board_url=source,
                        state=state_name,
                        max_pages=5
                    )
                    research_data["regulatory_updates"].extend(updates)
                    print(f"✅ Scraped {len(updates)} updates from {source}")
                except Exception as e:
                    print(f"⚠️  Failed to scrape {source}: {e}")

            # Analyze competitor content
            for source in competitor_sources:
                try:
                    analysis = client.analyze_competitor_blog(
                        session_id=session_id,
                        url=source
                    )
                    research_data["competitor_analysis"].append(analysis)
                    print(f"✅ Analyzed competitor: {source}")
                except Exception as e:
                    print(f"⚠️  Failed to analyze {source}: {e}")

        except Exception as e:
            return StageResult(
                stage=PipelineStage.RESEARCH,
                status="failed",
                errors=[f"Browser automation failed: {e}"]
            )

        finally:
            # Always cleanup browser session
            try:
                client.cleanup_session(session_id)
            except:
                pass

        # Store research data in state
        self.state.research_data = research_data

        print(f"✅ Research complete: {len(research_data['regulatory_updates'])} regulatory, {len(research_data['competitor_analysis'])} competitor")
        return StageResult(
            stage=PipelineStage.RESEARCH,
            status="success",
            artifacts={"research_data": research_data}
        )

    def _stage_generation(self) -> StageResult:
        """
        GENERATION stage: Claude CLI content generation via IterationLoop.

        Returns:
            StageResult with draft path
        """
        assert self.state is not None, "Pipeline state must be initialized"
        from orchestration.iteration_loop import IterationLoop
        from agents.factory import create_agent

        # Create editorial agent
        agent = create_agent("editorial", self.app_context.project_name)

        # Build generation prompt
        prompt = self._build_generation_prompt()

        # Run with IterationLoop (Wiggum self-correction)
        loop = IterationLoop(agent, self.app_context)
        result = loop.run(
            task_id=self.state.content_id,
            task_description=prompt,
            max_iterations=self.STAGE_BUDGETS[PipelineStage.GENERATION]
        )

        if result.status != "completed":
            return StageResult(
                stage=PipelineStage.GENERATION,
                status="failed",
                errors=[result.reason]
            )

        # Find generated draft (should be in drafts_dir)
        draft_files = list(self.drafts_dir.glob("*.md"))
        if not draft_files:
            return StageResult(
                stage=PipelineStage.GENERATION,
                status="failed",
                errors=["No draft file generated"]
            )

        # Use most recent draft
        draft_path = max(draft_files, key=lambda p: p.stat().st_mtime)
        self.state.draft_path = str(draft_path)

        print(f"✅ Draft generated: {draft_path.name}")
        return StageResult(
            stage=PipelineStage.GENERATION,
            status="success",
            artifacts={"draft_path": str(draft_path)}
        )

    def _stage_validation(self) -> StageResult:
        """
        VALIDATION stage: ContentValidator (Ralph-style SEO + frontmatter + citations).

        Returns:
            StageResult with validation verdict
        """
        assert self.state is not None, "Pipeline state must be initialized"
        from ralph.checkers.content_checker import ContentValidator
        from ralph.engine import VerdictType

        if not self.state.draft_path or not Path(self.state.draft_path).exists():
            return StageResult(
                stage=PipelineStage.VALIDATION,
                status="failed",
                errors=["Draft file not found"]
            )

        # Run ContentValidator
        validator = ContentValidator(self.keyword_strategy)
        verdict = validator.validate(
            Path(self.state.draft_path),
            min_seo_score=self.state.task.min_seo_score
        )

        # Extract issues and warnings from verdict
        issues = []
        warnings = []
        seo_score = 0

        for step in verdict.steps:
            if not step.passed:
                if "seo" in step.step.lower():
                    # Extract SEO score from output
                    import re
                    match = re.search(r'SEO score: (\d+)', step.output)
                    if match:
                        seo_score = int(match.group(1))
                issues.append(f"{step.step}: {step.output}")
            else:
                if step.output and "warning" in step.output.lower():
                    warnings.append(f"{step.step}: {step.output}")

        # Store in state
        self.state.seo_score = seo_score
        self.state.validation_issues = issues
        self.state.validation_warnings = warnings

        # Map verdict to stage status
        if verdict.type == VerdictType.PASS:
            print(f"✅ Validation PASSED (SEO: {seo_score}/100)")
            return StageResult(
                stage=PipelineStage.VALIDATION,
                status="success",
                artifacts={"verdict": verdict, "seo_score": seo_score}
            )
        elif verdict.type == VerdictType.BLOCKED:
            print(f"🚫 Validation BLOCKED: {verdict.reason}")
            return StageResult(
                stage=PipelineStage.VALIDATION,
                status="blocked",
                errors=[verdict.reason],
                artifacts={"verdict": verdict}
            )
        else:  # FAIL
            print(f"❌ Validation FAILED (SEO: {seo_score}/100)")
            return StageResult(
                stage=PipelineStage.VALIDATION,
                status="failed",
                errors=issues,
                warnings=warnings,
                artifacts={"verdict": verdict, "seo_score": seo_score}
            )

    def _stage_review(self, non_interactive: bool = False) -> StageResult:
        """
        REVIEW stage: Human approval gate.

        Args:
            non_interactive: Auto-approve if True

        Returns:
            StageResult with approval decision
        """
        assert self.state is not None, "Pipeline state must be initialized"
        from orchestration.content_approval import ContentApprovalGate, ApprovalRequest, ApprovalDecision

        if non_interactive:
            # Auto-approve in non-interactive mode
            print("✅ Auto-approved (non-interactive mode)")
            return StageResult(
                stage=PipelineStage.REVIEW,
                status="success",
                artifacts={"approved": True}
            )

        # Create approval request
        request = ApprovalRequest(
            content_id=self.state.content_id,
            draft_path=Path(self.state.draft_path),
            seo_score=self.state.seo_score or 0,
            validation_issues=self.state.validation_issues,
            validation_warnings=self.state.validation_warnings,
            stage=self.state.current_stage.value
        )

        # Request human approval
        gate = ContentApprovalGate()
        result = gate.request_approval(request)

        # Handle decision
        if result.decision == ApprovalDecision.APPROVE:
            print("✅ Approved for publication")
            return StageResult(
                stage=PipelineStage.REVIEW,
                status="success",
                artifacts={"approval_result": result}
            )
        elif result.decision == ApprovalDecision.REJECT:
            # Move draft to rejected/
            rejected_path = self.rejected_dir / Path(self.state.draft_path).name
            shutil.move(self.state.draft_path, rejected_path)
            print(f"❌ Rejected, moved to {rejected_path}")
            return StageResult(
                stage=PipelineStage.REVIEW,
                status="blocked",
                errors=["Content rejected by human reviewer"],
                artifacts={"approval_result": result}
            )
        else:  # MODIFY
            print("🔄 Modifications requested, returning to GENERATION")
            # Will trigger retry logic to go back to GENERATION
            return StageResult(
                stage=PipelineStage.REVIEW,
                status="failed",
                errors=["Modifications requested"],
                warnings=[result.notes] if result.notes else [],
                artifacts={"approval_result": result}
            )

    def _stage_publication(self) -> StageResult:
        """
        PUBLICATION stage: Copy draft to published directory.

        Returns:
            StageResult with publication outcome
        """
        assert self.state is not None, "Pipeline state must be initialized"
        if not self.state.draft_path or not Path(self.state.draft_path).exists():
            return StageResult(
                stage=PipelineStage.PUBLICATION,
                status="failed",
                errors=["Draft file not found"]
            )

        try:
            # Copy to published directory
            draft_path = Path(self.state.draft_path)
            published_path = self.published_dir / draft_path.name

            shutil.copy2(draft_path, published_path)

            print(f"✅ Published: {published_path}")
            return StageResult(
                stage=PipelineStage.PUBLICATION,
                status="success",
                artifacts={"published_path": str(published_path)}
            )

        except Exception as e:
            return StageResult(
                stage=PipelineStage.PUBLICATION,
                status="failed",
                errors=[f"Publication failed: {e}"]
            )

    def _make_decision(self, stage_result: StageResult) -> StageDecision:
        """
        Make decision based on stage result.

        Decision tree (matches stop_hook.py pattern):
        - success → PROCEED
        - blocked → ASK_HUMAN
        - failed + budget remaining → RETRY
        - failed + budget exhausted → ASK_HUMAN

        Args:
            stage_result: Result from stage execution

        Returns:
            StageDecision for next action
        """
        if stage_result.status == "success":
            return StageDecision.PROCEED

        elif stage_result.status == "blocked":
            # Critical violation, requires human decision
            return StageDecision.ASK_HUMAN

        else:  # "failed"
            # Check if stage has retry budget
            stage = stage_result.stage
            if stage in self.STAGE_BUDGETS:
                # Count retries for this stage
                stage_retries = sum(
                    1 for h in self.state.stage_history
                    if h["stage"] == stage.value and h["status"] == "failed"
                )

                if stage_retries < self.STAGE_BUDGETS[stage]:
                    # Budget available, retry
                    return StageDecision.RETRY

            # Budget exhausted or no budget defined
            return StageDecision.ASK_HUMAN

    def _build_generation_prompt(self) -> str:
        """
        Build generation prompt for Claude CLI.

        Returns:
            Formatted prompt with task details and research data
        """
        assert self.state is not None, "Pipeline state must be initialized"
        prompt_parts = [
            f"# Editorial Task: {self.state.task.topic}",
            f"\n## Target Audience: {self.state.task.target_audience}",
            f"## Keywords: {', '.join(self.state.task.keywords)}",
            f"## Target Word Count: {self.state.task.target_word_count}",
            f"## Minimum SEO Score: {self.state.task.min_seo_score}",
        ]

        # Add research data if available
        if self.state.research_data:
            prompt_parts.append("\n## Research Data")

            if self.state.research_data.get("regulatory_updates"):
                prompt_parts.append("\n### Regulatory Updates:")
                for update in self.state.research_data["regulatory_updates"][:5]:
                    prompt_parts.append(f"- {update.get('title', 'Unknown')}")

            if self.state.research_data.get("competitor_analysis"):
                prompt_parts.append("\n### Competitor Analysis:")
                for analysis in self.state.research_data["competitor_analysis"]:
                    prompt_parts.append(f"- {analysis.get('title', 'Unknown')} (SEO: {analysis.get('seo_score', 'N/A')})")

        prompt_parts.append("\n## Instructions")
        prompt_parts.append("Write a comprehensive, SEO-optimized blog post with:")
        prompt_parts.append("1. Frontmatter (YAML) with title, date, author, keywords, description")
        prompt_parts.append("2. Proper heading hierarchy (H1, H2, H3)")
        prompt_parts.append("3. Keyword integration (natural, not stuffed)")
        prompt_parts.append("4. Citations for factual claims")
        prompt_parts.append("5. Readability score >= 60")
        prompt_parts.append("\nSave to blog/credentialmate/drafts/")
        prompt_parts.append("\n<promise>EDITORIAL_COMPLETE</promise> when done.")

        return "\n".join(prompt_parts)

    def _extract_state_from_url(self, url: str) -> str:
        """
        Extract state name from regulatory board URL.

        Args:
            url: Board URL

        Returns:
            State name (full, not abbreviation)
        """
        state_mapping = {
            "ca.gov": "California",
            "ct.gov": "Connecticut",
            "ny.gov": "New York",
            "tx.gov": "Texas",
            "fl.gov": "Florida",
        }

        for pattern, state in state_mapping.items():
            if pattern in url.lower():
                return state

        # Fallback: try to extract from path
        import re
        match = re.search(r'/([a-z]+)-nursing', url.lower())
        if match:
            return match.group(1).capitalize()

        return "Unknown"

    def _save_state(self) -> None:
        """Save pipeline state to Markdown file."""
        assert self.state is not None, "Pipeline state must be initialized"
        state_file = self.state_dir / f"pipeline-{self.state.content_id}.md"

        # Build frontmatter
        frontmatter = {
            "content_id": self.state.content_id,
            "current_stage": self.state.current_stage.value,
            "iteration": self.state.iteration,
            "max_iterations": self.state.max_iterations,
            "started_at": self.state.started_at,
        }

        if self.state.draft_path:
            frontmatter["draft_path"] = self.state.draft_path
        if self.state.seo_score is not None:
            frontmatter["seo_score"] = self.state.seo_score

        # Build content
        content = "---\n"
        content += yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        content += "---\n\n"
        content += f"# Pipeline State: {self.state.task.topic}\n\n"
        content += "## Stage History\n\n"

        for entry in self.state.stage_history:
            content += f"### {entry['stage'].upper()} ({entry['status']}, {entry['duration']:.1f}s)\n"
            if entry['errors']:
                content += "Errors:\n"
                for error in entry['errors']:
                    content += f"- {error}\n"
            if entry['warnings']:
                content += "Warnings:\n"
                for warning in entry['warnings']:
                    content += f"- {warning}\n"
            content += "\n"

        state_file.write_text(content)

    def _load_state(self, content_id: str) -> Optional[PipelineState]:
        """
        Load pipeline state from file.

        Args:
            content_id: Content ID to load

        Returns:
            PipelineState if file exists, None otherwise
        """
        state_file = self.state_dir / f"pipeline-{content_id}.md"

        if not state_file.exists():
            return None

        try:
            content = state_file.read_text()

            # Extract frontmatter
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter = yaml.safe_load(parts[1])

            # Reconstruct state (simplified - task reconstruction needed)
            state = PipelineState(
                content_id=frontmatter["content_id"],
                current_stage=PipelineStage(frontmatter["current_stage"]),
                iteration=frontmatter["iteration"],
                max_iterations=frontmatter["max_iterations"],
                started_at=frontmatter["started_at"],
                task=self.state.task if self.state else None,  # Reuse current task
                draft_path=frontmatter.get("draft_path"),
                seo_score=frontmatter.get("seo_score")
            )

            return state

        except Exception as e:
            print(f"⚠️  Failed to load state: {e}")
            return None

    def _cleanup_state(self) -> None:
        """Remove state file after pipeline completion."""
        assert self.state is not None, "Pipeline state must be initialized"
        state_file = self.state_dir / f"pipeline-{self.state.content_id}.md"
        if state_file.exists():
            state_file.unlink()
