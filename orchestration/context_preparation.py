"""
Context Preparation for Agent Sessions

Generates startup protocol instructions to prepend to agent prompts.
Ensures agents load key context files before beginning work.

This implements the 10-step startup protocol for cross-repo memory continuity.
"""

from pathlib import Path
from typing import Optional


def get_startup_protocol_prompt(
    project_path: Path,
    repo_name: str,
    include_cross_repo: bool = True,
    task_type: Optional[str] = None
) -> str:
    """
    Generate startup protocol instructions for agent session.

    This creates a prompt section that instructs Claude to read key
    context files before beginning work, ensuring session continuity
    and cross-repo awareness.

    Args:
        project_path: Path to project directory
        repo_name: Name of repository (ai_orchestrator, karematch, credentialmate)
        include_cross_repo: Whether to include cross-repo state cache
        task_type: Optional task type for conditional loading (bugfix, feature, test, etc.)

    Returns:
        Formatted startup protocol instructions
    """
    protocol_steps = []

    # Core memory files
    if (project_path / "CATALOG.md").exists():
        protocol_steps.append("1. Read CATALOG.md for documentation structure")

    if (project_path / "STATE.md").exists():
        protocol_steps.append("2. Read STATE.md for current state of this repo")

    # Conditional DECISIONS.md loading (Phase 2C optimization)
    # Only load for feature/architecture/planning tasks to save tokens
    if (project_path / "DECISIONS.md").exists():
        needs_decisions = (
            task_type is None or  # Load by default if task_type not specified
            task_type.lower() in {
                "feature", "architecture", "planning", "design",
                "refactor", "migration", "strategic"
            }
        )
        if needs_decisions:
            protocol_steps.append("3. Read DECISIONS.md for past decisions in this repo")
        else:
            protocol_steps.append("3. Skip DECISIONS.md (not needed for bugfix/test/quality tasks)")

    # Session handoff
    sessions_dir = project_path / "sessions"
    if sessions_dir.exists():
        latest_session = _find_latest_session(sessions_dir)
        if latest_session:
            protocol_steps.append(f"4. Read {latest_session} for last session handoff")
        else:
            protocol_steps.append("4. No recent session file found (skip)")

    # Cross-repo state cache (NEW in v6.0)
    if include_cross_repo and (project_path / ".aibrain" / "global-state-cache.md").exists():
        protocol_steps.append("5. Read .aibrain/global-state-cache.md for cross-repo state ⭐")

    # Recent progress
    if (project_path / "claude-progress.txt").exists():
        protocol_steps.append("6. Read claude-progress.txt for recent accomplishments")

    # Known issues
    hot_patterns = project_path / ".claude" / "memory" / "hot-patterns.md"
    if hot_patterns.exists():
        protocol_steps.append("7. Read .claude/memory/hot-patterns.md for known issues")

    # Git status
    protocol_steps.append("8. Check git status for uncommitted work")

    # Work queue
    work_queue = project_path / "tasks" / f"work_queue_{repo_name}.json"
    if work_queue.exists():
        protocol_steps.append(f"9. Review tasks/work_queue_{repo_name}.json for pending tasks")

    if not protocol_steps:
        return ""  # No context files found

    # Generate prompt
    prompt = """
═══════════════════════════════════════════════════════════
SESSION STARTUP PROTOCOL
═══════════════════════════════════════════════════════════

Before beginning work, please complete the following startup steps
to load context and ensure session continuity:

"""

    for step in protocol_steps:
        prompt += f"{step}\n"

    prompt += """
After completing these steps, proceed with your assigned task.

═══════════════════════════════════════════════════════════

"""

    return prompt


def _find_latest_session(sessions_dir: Path) -> Optional[str]:
    """
    Find the most recent session file in sessions/active/ or sessions/{repo}/active/.

    Returns:
        Relative path to latest session file, or None if not found
    """
    # Try sessions/{repo}/active/ first (new structure)
    for repo in ["karematch", "credentialmate", "ai-orchestrator", "cross-repo"]:
        active_dir = sessions_dir / repo / "active"
        if active_dir.exists():
            session_files = list(active_dir.glob("*.md"))
            if session_files:
                # Sort by modification time, get most recent
                latest = max(session_files, key=lambda p: p.stat().st_mtime)
                return str(latest.relative_to(sessions_dir.parent))

    # Try sessions/active/ (old structure)
    active_dir = sessions_dir / "active"
    if active_dir.exists():
        session_files = list(active_dir.glob("*.md"))
        if session_files:
            latest = max(session_files, key=lambda p: p.stat().st_mtime)
            return str(latest.relative_to(sessions_dir.parent))

    return None


def should_include_startup_protocol(task_type: str) -> bool:
    """
    Determine if startup protocol should be included for this task type.

    Some task types (like simple linting) don't need full context loading.

    Args:
        task_type: Type of task (bugfix, feature, test, etc.)

    Returns:
        True if startup protocol should be included
    """
    # Skip protocol for simple automated tasks
    skip_for = {
        "lint-fix",
        "format-fix",
        "simple-test-fix"
    }

    return task_type.lower() not in skip_for
