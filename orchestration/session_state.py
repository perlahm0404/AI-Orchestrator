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
