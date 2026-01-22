"""
Editorial Agent - Autonomous SEO/AEO-optimized content creation

Workflow:
1. Research state board updates via browser automation
2. Analyze competitor content for SEO gaps
3. Generate content drafts with citations
4. Validate against keyword strategy and factual accuracy
5. Save draft for human approval and publishing

Autonomy Level: L1.5 (between Dev L1 and QA L2)
Approval Gate: Ralph-style validation → Human review → Publish
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json
from datetime import datetime

from governance.kill_switch import mode
from governance import contract
from governance.require_harness import require_harness
from agents.base import BaseAgent, AgentConfig


@dataclass
class EditorialTask:
    """An editorial content creation task."""
    task_id: str
    category: str  # e.g., "state-board-updates", "CE-requirements", "compliance-guides"
    topic: str  # e.g., "California-nursing-CE-2026"
    keywords: List[str]  # Primary and secondary keywords
    research_sources: List[str]  # URLs to scrape (state boards, competitors)
    target_audience: str  # e.g., "nurses", "doctors", "allied-health"
    target_word_count: int = 2000
    min_seo_score: int = 50  # Minimum SEO score to pass validation


class EditorialAgent(BaseAgent):
    """
    Autonomous editorial agent for SEO/AEO-optimized content creation.

    Features:
    - Browser automation for research (state boards, competitors)
    - SEO-driven content generation with keyword optimization
    - Citation verification for factual accuracy
    - Ralph-style validation before human approval
    - Multi-stage workflow: Draft → Validate → Review → Publish
    """

    def __init__(self, app_adapter: Any, config: Optional[AgentConfig] = None) -> None:
        """
        Initialize Editorial agent.

        Args:
            app_adapter: Application adapter (typically CredentialMate)
            config: Optional AgentConfig (will be created from contract if not provided)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract
        self.contract = contract.load("editorial")

        # Create or use provided config
        if config is None:
            self.config = AgentConfig(
                project_name=self.app_context.project_name,
                agent_name="editorial",
                expected_completion_signal=None,  # Can be set by caller
                max_iterations=self.contract.limits.get("max_iterations", 20),
                max_retries=self.contract.limits.get("max_retries", 3)
            )
        else:
            self.config = config

        # Backward compatibility
        self.max_retries = self.config.max_retries

        # Iteration tracking
        self.current_iteration = 0
        self.iteration_history: List[Dict[str, Any]] = []

        # Editorial-specific paths
        self.drafts_dir = Path.cwd() / "blog" / self.app_context.project_name / "drafts"
        self.published_dir = Path.cwd() / "blog" / self.app_context.project_name / "published"

        # Ensure directories exist
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.published_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, task_id: str) -> Dict[str, Any]:
        """
        Execute editorial workflow using Claude CLI.

        Workflow:
        1. Parse task specification
        2. Execute via Claude CLI with editorial prompt
        3. Check for completion signal
        4. Return result for validation

        Args:
            task_id: The task ID to work on (e.g., "EDITORIAL-STATE-CA-NURSING-001")

        Returns:
            Result dict with:
            - status: "completed" | "blocked" | "failed"
            - draft_path: Path to generated draft
            - output: Agent output text (for completion signal checking)
            - validation: Validation results (if run)
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract: can we execute this action?
        contract.require_allowed(self.contract, "write_file")
        contract.require_allowed(self.contract, "browser_automation")

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

        # Get task description (set by IterationLoop.run())
        task_description = getattr(self, 'task_description', task_id)

        # Execute via Claude CLI
        from claude.cli_wrapper import ClaudeCliWrapper

        project_dir = Path(self.app_context.project_path)
        wrapper = ClaudeCliWrapper(project_dir)

        print(f"✍️  Executing editorial task via Claude CLI...")
        print(f"   Task: {task_id}")
        print(f"   Prompt: {task_description}")

        result = wrapper.execute_task(
            prompt=task_description,
            files=None,  # Let Claude decide which files to examine
            timeout=600  # 10 minutes for research + content generation
        )

        if not result.success:
            return {
                "task_id": task_id,
                "status": "failed",
                "reason": f"Claude CLI execution failed: {result.error}",
                "iterations": self.current_iteration,
                "output": result.error or "Execution failed"
            }

        print(f"✅ Editorial task complete ({result.duration_ms}ms)")
        if result.files_changed:
            print(f"   Changed files: {', '.join(result.files_changed)}")

        # Use Claude's output for completion signal checking
        output = result.output

        # Check for completion signal if configured
        if self.config.expected_completion_signal:
            promise = self.check_completion_signal(output)
            if promise == self.config.expected_completion_signal:
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "signal": "promise",
                    "promise_text": promise,
                    "output": output,
                    "iterations": self.current_iteration,
                    "files_changed": result.files_changed
                }

        # Return success
        return {
            "task_id": task_id,
            "status": "completed",
            "output": output,
            "iterations": self.current_iteration,
            "files_changed": result.files_changed
        }

    def execute_editorial_task(self, task: EditorialTask) -> Dict[str, Any]:
        """
        Execute editorial workflow (legacy method for backward compatibility).

        This method provides a more structured interface for editorial tasks
        with explicit research, generation, and validation phases.

        Args:
            task: EditorialTask with specification

        Returns:
            Result dict with status, draft_path, and validation
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract
        contract.require_allowed(self.contract, "write_file")
        contract.require_allowed(self.contract, "browser_automation")

        # Track iteration
        self.current_iteration += 1

        # Phase 1: Research
        print(f"📚 Phase 1: Research for {task.topic}...")
        research_data = self._conduct_research(task)

        # Phase 2: Generate content
        print(f"✍️  Phase 2: Generating content...")
        draft_path = self._generate_content(task, research_data)

        # Phase 3: Validate
        print(f"✅ Phase 3: Validating content...")
        validation = self._validate_content(draft_path, task)

        output = f"Editorial task complete. Draft saved to {draft_path}"

        # Check for completion signal if configured
        if self.config.expected_completion_signal:
            promise = self.check_completion_signal(output)
            if promise == self.config.expected_completion_signal:
                return {
                    "task_id": task.task_id,
                    "status": "completed",
                    "signal": "promise",
                    "promise_text": promise,
                    "draft_path": str(draft_path),
                    "validation": validation,
                    "output": output
                }

        return {
            "task_id": task.task_id,
            "status": "completed" if validation.get("passed", False) else "failed",
            "draft_path": str(draft_path),
            "validation": validation,
            "output": output
        }

    @require_harness
    def _conduct_research(self, task: EditorialTask) -> Dict[str, Any]:
        """
        Conduct research via browser automation.

        Integrates Phase 3-4 browser automation extensions:
        - Scrapes state board regulatory updates
        - Analyzes competitor blog content
        - Gathers keyword research data

        Args:
            task: EditorialTask with research sources

        Returns:
            research_data: Dict with regulatory_updates, competitor_analysis
        """
        # Check contract
        contract.require_allowed(self.contract, "browser_automation")

        # Import browser automation client
        try:
            from adapters.browser_automation import BrowserAutomationClient
        except ImportError:
            print("   ⚠️  Browser automation not available, skipping research phase")
            return {
                "regulatory_updates": [],
                "competitor_analysis": [],
                "timestamp": datetime.now().isoformat()
            }

        client = BrowserAutomationClient()
        session_id = f"editorial-{task.task_id}"

        # Create browser session
        try:
            client.create_session({
                "sessionId": session_id,
                "headless": True,
                "auditLogPath": str(Path(".aibrain") / f"browser-audit-{session_id}.jsonl")
            })
        except Exception as e:
            print(f"   ⚠️  Failed to create browser session: {e}")
            return {
                "regulatory_updates": [],
                "competitor_analysis": [],
                "timestamp": datetime.now().isoformat()
            }

        research_data = {
            "regulatory_updates": [],
            "competitor_analysis": [],
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Separate sources by type
            regulatory_sources = [
                s for s in task.research_sources
                if ".gov" in s or "state" in s.lower()
            ]
            competitor_sources = [
                s for s in task.research_sources
                if s not in regulatory_sources
            ]

            # Scrape regulatory sources
            for source in regulatory_sources:
                try:
                    state = self._extract_state_from_url(source)
                    print(f"   Scraping {state} regulatory board: {source}")
                    updates = client.scrape_regulatory_updates(
                        session_id=session_id,
                        board_url=source,
                        state=state,
                        max_pages=5
                    )
                    research_data["regulatory_updates"].extend(updates)
                    print(f"   ✅ Scraped {len(updates)} updates")
                except Exception as e:
                    print(f"   ⚠️  Failed to scrape {source}: {e}")
                    research_data["regulatory_updates"].append({
                        "source": source,
                        "error": str(e),
                        "status": "failed"
                    })

            # Analyze competitor content
            for source in competitor_sources:
                try:
                    print(f"   Analyzing competitor: {source}")
                    analysis = client.analyze_competitor_blog(
                        session_id=session_id,
                        url=source
                    )
                    research_data["competitor_analysis"].append(analysis)
                    print(f"   ✅ Analyzed (SEO: {analysis.get('seo_score', 'N/A')})")
                except Exception as e:
                    print(f"   ⚠️  Failed to analyze {source}: {e}")
                    research_data["competitor_analysis"].append({
                        "source": source,
                        "error": str(e),
                        "status": "failed"
                    })

        finally:
            # Always cleanup browser session
            try:
                client.cleanup_session(session_id)
            except Exception as e:
                print(f"   ⚠️  Failed to cleanup session: {e}")

        print(f"   Research complete: {len(research_data['regulatory_updates'])} regulatory, {len(research_data['competitor_analysis'])} competitor")
        return research_data

    @require_harness
    def _generate_content(self, task: EditorialTask, research_data: Dict[str, Any]) -> Path:
        """
        Generate content draft with citations.

        Args:
            task: EditorialTask with specifications
            research_data: Research data from _conduct_research()

        Returns:
            Path to generated draft file
        """
        # Check contract
        contract.require_allowed(self.contract, "write_file")

        # Generate filename
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}-{task.topic.lower().replace(' ', '-')}.md"
        draft_path = self.drafts_dir / filename

        # Create frontmatter
        frontmatter: Dict[str, Any] = {
            "title": task.topic.replace('-', ' ').title(),
            "category": task.category,
            "keywords": task.keywords,
            "target_audience": task.target_audience,
            "created": datetime.now().isoformat(),
            "status": "draft",
            "seo_score": None,  # Will be filled by validation
            "citations_verified": False
        }

        # Generate content (MVP: simple template)
        # In production, this would use Claude CLI to generate full content
        content = f"""---
{json.dumps(frontmatter, indent=2)}
---

# {frontmatter['title']}

## Introduction

[Content to be generated by Claude CLI based on research data]

## Key Points

- Point 1
- Point 2
- Point 3

## Conclusion

[Conclusion]

## References

{json.dumps(research_data, indent=2)}
"""

        # Write draft
        with open(draft_path, 'w') as f:
            f.write(content)

        print(f"   Draft saved: {draft_path}")
        return draft_path

    @require_harness
    def _validate_content(self, draft_path: Path, task: EditorialTask) -> Dict[str, Any]:
        """
        Validate content against SEO and quality standards.

        Args:
            draft_path: Path to draft file
            task: EditorialTask with validation criteria

        Returns:
            Validation result dict
        """
        validation: Dict[str, Any] = {
            "passed": False,
            "seo_score": 0,
            "issues": [],
            "warnings": []
        }

        # Read draft
        if not draft_path.exists():
            validation["issues"].append(f"Draft file not found: {draft_path}")
            return validation

        with open(draft_path, 'r') as f:
            content = f.read()

        # Basic validations
        if len(content) < 500:
            validation["issues"].append("Content too short (< 500 chars)")

        # Check for frontmatter
        if not content.startswith("---"):
            validation["issues"].append("Missing frontmatter")

        # Check for keywords (simple check)
        keyword_found = any(kw.lower() in content.lower() for kw in task.keywords[:3])
        if not keyword_found:
            validation["warnings"].append("Primary keywords not found in content")

        # MVP: Simple SEO score based on length and keyword presence
        score = 0
        if len(content) > 1000:
            score += 30
        if keyword_found:
            score += 40
        if "##" in content:  # Has headings
            score += 20
        if "[" in content and "]" in content:  # Has links/citations
            score += 10

        validation["seo_score"] = score
        validation["passed"] = score >= task.min_seo_score and len(validation["issues"]) == 0

        print(f"   SEO Score: {score}/100")
        print(f"   Status: {'✅ PASS' if validation['passed'] else '❌ FAIL'}")

        return validation

    def checkpoint(self) -> Dict[str, Any]:
        """Capture current state for resume."""
        return {
            "agent": "editorial",
            "project": self.app_context.project_name,
            "iteration": self.current_iteration
        }

    def halt(self, reason: str) -> None:
        """Gracefully stop execution."""
        print(f"🛑 Editorial agent halted: {reason}")
        # Log halt reason (would go to audit log in production)
        pass

    def run_with_loop(self, task_id: str, task_description: str = "", max_iterations: Optional[int] = None, resume: bool = False) -> Any:
        """
        Run editorial workflow with Wiggum iteration loop.

        This is a convenience method that creates an IterationLoop and runs the agent.
        Use this for Wiggum iteration mode with stop hooks (uses ContentValidator).

        Args:
            task_id: Task identifier
            task_description: Description of the task
            max_iterations: Override max_iterations from config
            resume: Resume from saved state if available

        Returns:
            IterationResult with final status

        Example:
            agent = EditorialAgent(app_adapter, config=AgentConfig(
                project_name="credentialmate",
                agent_name="editorial",
                expected_completion_signal="EDITORIAL_COMPLETE",
                max_iterations=20
            ))
            result = agent.run_with_loop("EDITORIAL-STATE-CA-001", "Write blog post about CA nursing CE requirements")
        """
        from orchestration.iteration_loop import IterationLoop

        loop = IterationLoop(self, self.app_context)
        return loop.run(
            task_id=task_id,
            task_description=task_description,
            max_iterations=max_iterations or self.config.max_iterations,
            resume=resume
        )

    def _extract_state_from_url(self, url: str) -> str:
        """
        Extract state name from regulatory board URL.

        Examples:
            "https://www.rn.ca.gov/" -> "California"
            "https://portal.ct.gov/DPH" -> "Connecticut"

        Args:
            url: Board URL

        Returns:
            State name (full, not abbreviation)
        """
        import re

        # Common state domain patterns
        state_mapping = {
            "ca.gov": "California",
            "ct.gov": "Connecticut",
            "ny.gov": "New York",
            "tx.gov": "Texas",
            "fl.gov": "Florida",
            "il.gov": "Illinois",
            "pa.gov": "Pennsylvania",
            "oh.gov": "Ohio",
            "ga.gov": "Georgia",
            "nc.gov": "North Carolina",
            "mi.gov": "Michigan",
            "nj.gov": "New Jersey",
            "va.gov": "Virginia",
            "wa.gov": "Washington",
            "az.gov": "Arizona",
            "ma.gov": "Massachusetts",
            "tn.gov": "Tennessee",
            "in.gov": "Indiana",
            "mo.gov": "Missouri",
            "md.gov": "Maryland"
        }

        # Check domain patterns
        for pattern, state in state_mapping.items():
            if pattern in url.lower():
                return state

        # Fallback: try to extract from path
        # e.g., /california-nursing-board/ -> California
        match = re.search(r'/([a-z]+)-nursing', url.lower())
        if match:
            return match.group(1).capitalize()

        # Fallback: try state abbreviations in URL
        state_abbrev_map = {
            "CA": "California", "CT": "Connecticut", "NY": "New York",
            "TX": "Texas", "FL": "Florida", "IL": "Illinois",
            "PA": "Pennsylvania", "OH": "Ohio", "GA": "Georgia",
            "NC": "North Carolina", "MI": "Michigan", "NJ": "New Jersey",
            "VA": "Virginia", "WA": "Washington", "AZ": "Arizona",
            "MA": "Massachusetts", "TN": "Tennessee", "IN": "Indiana",
            "MO": "Missouri", "MD": "Maryland"
        }

        for abbrev, state in state_abbrev_map.items():
            if f"/{abbrev}/" in url or f"-{abbrev}-" in url:
                return state

        # Last resort: return "Unknown"
        return "Unknown"
