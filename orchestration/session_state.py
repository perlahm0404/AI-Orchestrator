"""
Session State Management for Stateless Agent Execution

Enables agents to save/load work-in-progress state across context resets.
Implements markdown files with JSON frontmatter for human readability.

Author: Claude Code
Date: 2026-02-07
Version: 1.0
"""

from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class SessionState:
    """
    Manages persistent session state for agent iterations.

    Saves progress to markdown files with JSON frontmatter.
    Enables resumption across context resets.
    """

    def __init__(self, task_id: str, project: str):
        """
        Initialize session manager.

        Args:
            task_id: Unique task identifier
            project: Project name (credentialmate, karematch, etc.)
        """
        self.task_id = task_id
        self.project = project
        self.session_dir = Path(".aibrain")
        self.session_dir.mkdir(exist_ok=True)
        self.archive_dir = self.session_dir / "sessions" / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_file_path(self, checkpoint_num: int = 0) -> Path:
        """Get path to session file, optionally including checkpoint number."""
        if checkpoint_num > 0:
            return self.session_dir / f"session-{self.task_id}-{checkpoint_num}.md"
        return self.session_dir / f"session-{self.task_id}.md"

    def _get_latest_session_file(self) -> Optional[Path]:
        """Find the latest session file for this task."""
        files = list(self.session_dir.glob(f"session-{self.task_id}*.md"))
        if not files:
            return None
        # Sort by modification time, return newest
        return sorted(files, key=lambda f: f.stat().st_mtime)[-1]

    def save(self, data: Dict[str, Any]) -> None:
        """
        Save session to disk.

        Args:
            data: Dictionary with keys:
                - iteration_count: Current iteration number
                - phase: Current phase of work
                - status: "in_progress", "blocked", or "completed"
                - last_output: Summary of last agent output
                - next_steps: List of next steps
                - error: Optional error message
                - markdown_content: Optional human-readable markdown
                - context_window: Optional context window number
                - tokens_used: Optional token count
                - checkpoint_number: Optional checkpoint number

        Raises:
            ValueError: If required fields missing
        """
        # Validate required fields
        required = ["iteration_count", "phase", "status"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Get checkpoint number if provided, otherwise auto-increment
        checkpoint_num = data.get("checkpoint_number", 0)
        if checkpoint_num == 0:
            # Auto-increment if not provided
            latest = self._get_latest_session_file()
            if latest:
                try:
                    checkpoint_num = int(latest.stem.split("-")[-1])
                    # Check if it's a checkpoint number (numeric suffix)
                    if not checkpoint_num:
                        checkpoint_num = 1
                    else:
                        checkpoint_num += 1
                except (ValueError, IndexError):
                    checkpoint_num = 1
            else:
                checkpoint_num = 1

        # Create frontmatter (JSON in YAML block)
        frontmatter = {
            "id": f"SESSION-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "task_id": self.task_id,
            "project": self.project,
            "created_at": self._get_created_at(),
            "updated_at": datetime.now().isoformat(),
            "checkpoint_number": checkpoint_num,
            "iteration_count": data["iteration_count"],
            "phase": data["phase"],
            "status": data["status"],
            "last_output": data.get("last_output", ""),
            "next_steps": data.get("next_steps", []),
            "context_window": data.get("context_window", 0),
            "tokens_used": data.get("tokens_used", 0),
            "agent_type": data.get("agent_type", ""),
            "max_iterations": data.get("max_iterations", 50),
        }

        # Only include error if present
        if "error" in data and data["error"]:
            frontmatter["error"] = data["error"]

        # Get markdown content
        markdown = data.get("markdown_content", "")

        # Format file content
        yaml_block = json.dumps(frontmatter, indent=2)
        content = f"""---
{yaml_block}
---

{markdown}
"""

        # Write to disk
        file_path = self._get_session_file_path(checkpoint_num)
        try:
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"Session saved: {file_path}")
        except IOError as e:
            logger.error(f"Failed to save session {file_path}: {e}")
            raise

    @classmethod
    def load(cls, task_id: str) -> Dict[str, Any]:
        """
        Load session from disk.

        Args:
            task_id: Task identifier to load

        Returns:
            Dictionary with all session data including markdown_content

        Raises:
            FileNotFoundError: If no session file found
            json.JSONDecodeError: If frontmatter is malformed
        """
        session_dir = Path(".aibrain")

        # Find latest session file for this task
        files = list(session_dir.glob(f"session-{task_id}*.md"))
        if not files:
            raise FileNotFoundError(f"No session found for task: {task_id}")

        # Get most recently modified
        file_path = sorted(files, key=lambda f: f.stat().st_mtime)[-1]

        try:
            content = file_path.read_text(encoding="utf-8")
        except IOError as e:
            logger.error(f"Failed to read session {file_path}: {e}")
            raise

        # Parse: --- frontmatter --- markdown
        parts = content.split("---", 2)
        if len(parts) < 2:
            raise ValueError(f"Invalid session file format (missing frontmatter): {file_path}")

        try:
            frontmatter = json.loads(parts[1].strip())
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON frontmatter in {file_path}: {e}")
            raise

        markdown = parts[2].strip() if len(parts) > 2 else ""

        return {
            **frontmatter,
            "markdown_content": markdown,
            "file_path": str(file_path),
        }

    @classmethod
    def load_by_id(cls, session_id: str) -> Dict[str, Any]:
        """
        Load session by session ID (from frontmatter).

        Args:
            session_id: Session ID like "SESSION-20260207-101530"

        Returns:
            Dictionary with session data

        Raises:
            FileNotFoundError: If session not found
        """
        session_dir = Path(".aibrain")

        # Search all session files
        for file_path in session_dir.glob("session-*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                parts = content.split("---", 2)
                if len(parts) >= 2:
                    frontmatter = json.loads(parts[1].strip())
                    if frontmatter.get("id") == session_id:
                        markdown = parts[2].strip() if len(parts) > 2 else ""
                        return {
                            **frontmatter,
                            "markdown_content": markdown,
                            "file_path": str(file_path),
                        }
            except (IOError, json.JSONDecodeError):
                continue

        raise FileNotFoundError(f"Session not found: {session_id}")

    def update(self, **kwargs: Any) -> None:
        """
        Update existing session with new data.

        Loads current session, updates with provided kwargs, and saves.
        """
        try:
            session = self.load(self.task_id)
        except FileNotFoundError:
            # New session
            session = {
                "iteration_count": 0,
                "phase": "initial",
                "status": "pending",
                "markdown_content": "",
            }

        # Update with new data
        session.update(kwargs)

        # Remove file_path if present (internal use only)
        session.pop("file_path", None)
        session.pop("id", None)

        self.save(session)

    def archive(self) -> None:
        """Move completed session to archive directory."""
        file_path = self._get_latest_session_file()
        if file_path and file_path.exists():
            try:
                archive_name = file_path.name
                archive_path = self.archive_dir / archive_name
                file_path.rename(archive_path)
                logger.info(f"Session archived: {archive_path}")
            except IOError as e:
                logger.error(f"Failed to archive session: {e}")

    def get_latest(self) -> Dict[str, Any]:
        """Get the latest session data without specifying task_id."""
        return self.load(self.task_id)

    def _get_created_at(self) -> str:
        """Get created_at from existing session or now."""
        try:
            existing = self.load(self.task_id)
            created_at = existing.get("created_at")
            if created_at is None:
                return datetime.now().isoformat()
            return str(created_at)
        except FileNotFoundError:
            return datetime.now().isoformat()

    @staticmethod
    def get_all_sessions(project: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all session files.

        Args:
            project: Optional project filter

        Returns:
            List of session dictionaries
        """
        session_dir = Path(".aibrain")
        sessions = []

        for file_path in session_dir.glob("session-*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                parts = content.split("---", 2)
                if len(parts) >= 2:
                    frontmatter = json.loads(parts[1].strip())

                    # Filter by project if specified
                    if project and frontmatter.get("project") != project:
                        continue

                    markdown = parts[2].strip() if len(parts) > 2 else ""
                    sessions.append({
                        **frontmatter,
                        "markdown_content": markdown,
                        "file_path": str(file_path),
                    })
            except (IOError, json.JSONDecodeError):
                continue

        return sorted(sessions, key=lambda s: s.get("updated_at", ""), reverse=True)

    @staticmethod
    def delete_session(task_id: str) -> None:
        """Delete all session files for a task."""
        session_dir = Path(".aibrain")
        for file_path in session_dir.glob(f"session-{task_id}*.md"):
            try:
                file_path.unlink()
                logger.info(f"Session deleted: {file_path}")
            except IOError as e:
                logger.error(f"Failed to delete session {file_path}: {e}")

    # ==================== Multi-Agent Extension Methods ====================

    def _get_multi_agent_data(self) -> Dict[str, Any]:
        """
        Load multi-agent data from .aibrain/.multi-agent-{task_id}.json.

        Returns:
            Dictionary with team_lead and specialists data, or empty dict
        """
        ma_file = self.session_dir / f".multi-agent-{self.task_id}.json"
        if ma_file.exists():
            try:
                data = json.loads(ma_file.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
            except (IOError, json.JSONDecodeError):
                return {}
        return {}

    def _save_multi_agent_data(self, data: Dict[str, Any]) -> None:
        """Save multi-agent data to .aibrain/.multi-agent-{task_id}.json."""
        ma_file = self.session_dir / f".multi-agent-{self.task_id}.json"
        try:
            ma_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except IOError as e:
            logger.error(f"Failed to save multi-agent data: {e}")
            raise

    def record_team_lead_analysis(self, analysis: Dict[str, Any]) -> None:
        """
        Record team lead task analysis in session state.

        Args:
            analysis: Dictionary with keys:
                - key_challenges: List of identified challenges
                - recommended_specialists: List of specialist types
                - subtask_breakdown: List of subtask descriptions
                - risk_factors: List of risk factors
                - estimated_complexity: "low", "medium", or "high"
        """
        # Load existing multi-agent data
        ma_data = self._get_multi_agent_data()

        # Initialize team_lead section if not present
        if "team_lead" not in ma_data:
            ma_data["team_lead"] = {}

        # Record analysis
        ma_data["team_lead"]["analysis"] = {
            "timestamp": datetime.now().isoformat(),
            "key_challenges": analysis.get("key_challenges", []),
            "recommended_specialists": analysis.get("recommended_specialists", []),
            "subtask_breakdown": analysis.get("subtask_breakdown", []),
            "risk_factors": analysis.get("risk_factors", []),
            "estimated_complexity": analysis.get("estimated_complexity", "medium"),
        }

        # Save multi-agent data
        self._save_multi_agent_data(ma_data)
        logger.info(f"Team Lead analysis recorded for task {self.task_id}")

    def record_specialist_launch(self, specialist_type: str, subtask_id: str) -> None:
        """
        Record launch of a specialist agent.

        Args:
            specialist_type: Type of specialist ("bugfix", "featurebuilder", etc.)
            subtask_id: ID of the subtask being assigned
        """
        # Load existing multi-agent data
        ma_data = self._get_multi_agent_data()

        # Initialize specialists dict if not present
        if "specialists" not in ma_data:
            ma_data["specialists"] = {}

        # Initialize this specialist's tracking
        if specialist_type not in ma_data["specialists"]:
            ma_data["specialists"][specialist_type] = {
                "status": "pending",
                "iterations": 0,
                "subtask_ids": [],
                "verdict": None,
                "start_time": None,
                "end_time": None,
                "tokens_used": 0,
                "cost": 0.0,
            }

        # Record launch
        if ma_data["specialists"][specialist_type]["start_time"] is None:
            ma_data["specialists"][specialist_type]["start_time"] = datetime.now().isoformat()
        ma_data["specialists"][specialist_type]["status"] = "in_progress"
        if subtask_id not in ma_data["specialists"][specialist_type]["subtask_ids"]:
            ma_data["specialists"][specialist_type]["subtask_ids"].append(subtask_id)

        # Save multi-agent data
        self._save_multi_agent_data(ma_data)
        logger.info(f"Specialist {specialist_type} launched for subtask {subtask_id}")

    def record_specialist_iteration(
        self,
        specialist_type: str,
        iteration: int,
        output_summary: str,
        verdict_type: Optional[str] = None,
    ) -> None:
        """
        Record iteration progress for a specialist.

        Args:
            specialist_type: Type of specialist
            iteration: Current iteration number
            output_summary: Summary of iteration output
            verdict_type: Ralph verdict ("PASS", "FAIL", "BLOCKED", or None for in-progress)
        """
        # Load existing multi-agent data
        ma_data = self._get_multi_agent_data()

        # Ensure specialists structure exists
        if "specialists" not in ma_data:
            ma_data["specialists"] = {}
        if specialist_type not in ma_data["specialists"]:
            ma_data["specialists"][specialist_type] = {
                "status": "in_progress",
                "iterations": 0,
                "subtask_ids": [],
                "verdict": None,
                "tokens_used": 0,
                "cost": 0.0,
            }

        # Update iteration count
        ma_data["specialists"][specialist_type]["iterations"] = iteration

        # Store iteration history (keep last 3 for debugging)
        if "iteration_history" not in ma_data["specialists"][specialist_type]:
            ma_data["specialists"][specialist_type]["iteration_history"] = []

        ma_data["specialists"][specialist_type]["iteration_history"].append({
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "output_summary": output_summary[:200],  # Truncate for readability
            "verdict": verdict_type,
        })

        # Keep only last 3 iterations
        if len(ma_data["specialists"][specialist_type]["iteration_history"]) > 3:
            ma_data["specialists"][specialist_type]["iteration_history"] = (
                ma_data["specialists"][specialist_type]["iteration_history"][-3:]
            )

        # Update verdict if provided
        if verdict_type:
            ma_data["specialists"][specialist_type]["verdict"] = verdict_type

        # Save multi-agent data
        self._save_multi_agent_data(ma_data)
        logger.debug(f"Specialist {specialist_type} iteration {iteration} recorded")

    def record_specialist_completion(
        self,
        specialist_type: str,
        status: str,
        verdict: Dict[str, str],
        output_summary: str,
        tokens_used: int = 0,
        cost: float = 0.0,
    ) -> None:
        """
        Record completion of a specialist agent.

        Args:
            specialist_type: Type of specialist
            status: Final status ("completed", "blocked", "timeout", "failed")
            verdict: Ralph verdict dict with "type" key
            output_summary: Summary of final output
            tokens_used: Token count used
            cost: Estimated cost in USD
        """
        # Load existing multi-agent data
        ma_data = self._get_multi_agent_data()

        # Ensure specialists structure exists
        if "specialists" not in ma_data:
            ma_data["specialists"] = {}
        if specialist_type not in ma_data["specialists"]:
            ma_data["specialists"][specialist_type] = {
                "status": "pending",
                "iterations": 0,
                "subtask_ids": [],
                "verdict": None,
                "tokens_used": 0,
                "cost": 0.0,
            }

        # Record completion
        ma_data["specialists"][specialist_type].update({
            "status": status,
            "verdict": verdict.get("type", "UNKNOWN"),
            "end_time": datetime.now().isoformat(),
            "tokens_used": tokens_used,
            "cost": cost,
            "final_output": output_summary[:500],  # Store final summary
        })

        # Save multi-agent data
        self._save_multi_agent_data(ma_data)
        logger.info(f"Specialist {specialist_type} completed with status: {status}")

    def get_specialist_status(self, specialist_type: str) -> Dict[str, Any]:
        """
        Get current status of a specialist.

        Args:
            specialist_type: Type of specialist to query

        Returns:
            Dictionary with specialist status info or empty dict if not found
        """
        ma_data = self._get_multi_agent_data()
        specialists = ma_data.get("specialists", {})
        status = specialists.get(specialist_type, {})
        return status if isinstance(status, dict) else {}

    def get_all_specialists_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all specialists in this session.

        Returns:
            Dictionary mapping specialist type to status info
        """
        ma_data = self._get_multi_agent_data()
        specialists = ma_data.get("specialists", {})
        return specialists if isinstance(specialists, dict) else {}

    def all_specialists_complete(self) -> bool:
        """
        Check if all launched specialists have completed.

        Returns:
            True if all specialists are done, False otherwise
        """
        ma_data = self._get_multi_agent_data()
        specialists = ma_data.get("specialists", {})

        if not specialists:
            return True  # No specialists launched

        # Check if all have end_time (indicates completion)
        for specialist_data in specialists.values():
            if specialist_data.get("end_time") is None:
                return False  # At least one specialist still running

        return True  # All specialists have end times

    def get_team_lead_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Get recorded team lead analysis from session.

        Returns:
            Analysis dictionary or None if not recorded
        """
        ma_data = self._get_multi_agent_data()
        team_lead = ma_data.get("team_lead", {})
        analysis = team_lead.get("analysis") if isinstance(team_lead, dict) else None
        return analysis if isinstance(analysis, dict) else None


def format_session_markdown(
    session: Dict[str, Any],
    progress_sections: Optional[List[str]] = None,
    iteration_log: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Format session data into human-readable markdown.

    Args:
        session: Session dictionary
        progress_sections: List of markdown strings for each phase
        iteration_log: List of iteration details

    Returns:
        Markdown string for session body
    """
    lines = []

    # Task summary
    lines.append("## Task Summary\n")
    lines.append(f"**ID**: {session.get('task_id', 'UNKNOWN')}")
    lines.append(f"**Project**: {session.get('project', 'UNKNOWN')}")
    lines.append(f"**Status**: {_get_status_emoji(session.get('status'))} {session.get('status', 'unknown').title()}\n")

    # Objective and constraints (if provided)
    if session.get("objective"):
        lines.append("### Objective")
        lines.append(session["objective"])
        lines.append("")

    if session.get("constraints"):
        lines.append("### Constraints")
        lines.append(session["constraints"])
        lines.append("")

    # Progress sections
    if progress_sections:
        lines.append("## Progress\n")
        for section in progress_sections:
            lines.append(section)
        lines.append("")

    # Current iteration
    lines.append(f"## Current Status\n")
    lines.append(f"**Iteration**: {session.get('iteration_count', 0)} of {session.get('max_iterations', 50)}")
    lines.append(f"**Phase**: {session.get('phase', 'unknown')}")
    lines.append(f"**Context Window**: {session.get('context_window', 0)}")
    lines.append(f"**Tokens Used**: {session.get('tokens_used', 0)}\n")

    if session.get("last_output"):
        lines.append("### Latest Output\n")
        lines.append(session["last_output"])
        lines.append("")

    # Iteration log
    if iteration_log:
        lines.append("## Iteration Log\n")
        for iter_entry in iteration_log:
            lines.append(f"### Iteration {iter_entry.get('num', '?')}")
            lines.append(f"**Task**: {iter_entry.get('task', '?')}")
            lines.append(f"**Result**: {iter_entry.get('result', '?')}")
            if iter_entry.get("notes"):
                lines.append(f"**Notes**: {iter_entry['notes']}")
            lines.append("")

    # Next steps
    if session.get("next_steps"):
        lines.append("## Next Steps\n")
        for i, step in enumerate(session["next_steps"], 1):
            lines.append(f"{i}. {step}")
        lines.append("")

    # Blockers
    if session.get("error"):
        lines.append("## Current Blockers\n")
        lines.append(f"**Error**: {session['error']}\n")

    return "\n".join(lines)


def _get_status_emoji(status: Optional[str]) -> str:
    """Get emoji for status."""
    emojis: Dict[str, str] = {
        "in_progress": "🔄",
        "blocked": "🚫",
        "completed": "✅",
        "pending": "⏳",
    }
    if status is None:
        return "❓"
    return emojis.get(status, "❓")
