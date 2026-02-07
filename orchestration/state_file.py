"""
DEPRECATED: This module is deprecated in favor of session_state.py

Use orchestration.session_state.SessionState instead:

    from orchestration.session_state import SessionState

    session = SessionState(task_id="TASK-001", project="myproject")
    session.save({"iteration_count": 5, "phase": "testing", ...})
    data = session.get_latest()

Migration: session_state.py uses JSON frontmatter instead of YAML,
provides automatic checkpointing, and integrates with Claude Code hooks
for true stateless memory that survives context compaction.

---
ORIGINAL DOCSTRING (state_file.py - DEPRECATED):

State file management for persistent agent loops.

Format: Markdown with YAML frontmatter (Ralph-Wiggum pattern)

This allows agent loops to be resumed across sessions by persisting
loop state to disk in a human-readable format.

Usage:
    from orchestration.state_file import write_state_file, read_state_file, LoopState

    # Write state
    state = LoopState(
        iteration=1,
        max_iterations=10,
        completion_promise="DONE",
        task_description="Fix bug in login.ts",
        agent_name="bugfix",
        session_id="session-123",
        started_at="2026-01-06T10:00:00"
    )
    state_file = write_state_file(state, state_dir=Path(".aibrain"))

    # Read state
    state = read_state_file(state_file)

Implementation: Phase 4 - Ralph-Wiggum Integration
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class LoopState:
    """State of an agent iteration loop."""
    iteration: int
    max_iterations: int
    completion_promise: Optional[str]
    task_description: str
    agent_name: str
    session_id: str
    started_at: str
    project_name: Optional[str] = None
    task_id: Optional[str] = None


def write_state_file(state: LoopState, state_dir: Path) -> Path:
    """
    Write agent loop state to markdown file.

    Format:
    ---
    iteration: 1
    max_iterations: 10
    completion_promise: "COMPLETE"
    agent_name: "bugfix"
    session_id: "abc-123"
    started_at: "2026-01-06T10:00:00"
    project_name: "karematch"
    task_id: "TASK-123"
    ---

    # Task Description

    Fix the authentication bug in login.ts that causes users to be
    logged out after 5 minutes.

    ## Context

    This is a critical bug affecting all users...

    Args:
        state: LoopState to persist
        state_dir: Directory to write state file

    Returns:
        Path to created state file
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "agent-loop.local.md"

    frontmatter = {
        "iteration": state.iteration,
        "max_iterations": state.max_iterations,
        "completion_promise": state.completion_promise,
        "agent_name": state.agent_name,
        "session_id": state.session_id,
        "started_at": state.started_at
    }

    # Optional fields
    if state.project_name:
        frontmatter["project_name"] = state.project_name
    if state.task_id:
        frontmatter["task_id"] = state.task_id

    content = "---\n"
    content += yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    content += "---\n\n"
    content += "# Task Description\n\n"
    content += state.task_description

    state_file.write_text(content)
    return state_file


def read_state_file(state_file: Path) -> Optional[LoopState]:
    """
    Parse state file and return LoopState.

    Args:
        state_file: Path to state file

    Returns:
        LoopState if file exists and is valid, None otherwise
    """
    if not state_file.exists():
        return None

    content = state_file.read_text()

    # Extract frontmatter
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None

    # Extract task description (everything after second ---)
    task_description_section = parts[2].strip()

    # Remove "# Task Description" header if present
    if task_description_section.startswith("# Task Description"):
        lines = task_description_section.split("\n", 1)
        task_description = lines[1].strip() if len(lines) > 1 else ""
    else:
        task_description = task_description_section

    return LoopState(
        iteration=frontmatter["iteration"],
        max_iterations=frontmatter["max_iterations"],
        completion_promise=frontmatter.get("completion_promise"),
        task_description=task_description,
        agent_name=frontmatter["agent_name"],
        session_id=frontmatter["session_id"],
        started_at=frontmatter["started_at"],
        project_name=frontmatter.get("project_name"),
        task_id=frontmatter.get("task_id")
    )


def cleanup_state_file(state_dir: Path) -> bool:
    """
    Remove state file after loop completion.

    Args:
        state_dir: Directory containing state file

    Returns:
        True if file was removed, False if not found
    """
    state_file = state_dir / "agent-loop.local.md"
    if state_file.exists():
        state_file.unlink()
        return True
    return False
