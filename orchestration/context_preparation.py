"""
Context Preparation for Agent Sessions

Generates startup protocol instructions to prepend to agent prompts.
Ensures agents load key context files before beginning work.

This implements the 10-step startup protocol for cross-repo memory continuity.

v6 Enhancement: Budget-aware context selection
- Prioritizes context files based on task type
- Skips DECISIONS.md for simple tasks (lint-fix, format-fix)
- Compresses context to fit within token budget
"""

from pathlib import Path
from typing import Dict, List, Optional


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


# ═══════════════════════════════════════════════════════════════════════════════
# BUDGET-AWARE CONTEXT PREPARATION (v6)
# ═══════════════════════════════════════════════════════════════════════════════


def get_budget_aware_context(
    project_path: Path,
    task_type: Optional[str] = None,
    max_governance_tokens: int = 2000
) -> Dict[str, str]:
    """
    Load context files with budget awareness.

    Prioritizes files and skips low-priority content to stay within
    token budget.

    Args:
        project_path: Path to project directory
        task_type: Type of task for prioritization
        max_governance_tokens: Maximum tokens for governance context

    Returns:
        Dictionary of filename -> content for selected files
    """
    try:
        from governance.token_budget import TokenBudgetEnforcer, TokenBudget
    except ImportError:
        # Fallback if module not available
        return _load_all_context_files(project_path, task_type)

    # Create budget enforcer
    budget = TokenBudget(governance_limit=max_governance_tokens)
    enforcer = TokenBudgetEnforcer(budget)

    # Collect available context files
    available_files = _load_all_context_files(project_path, task_type)

    # Select files based on priority and budget
    selected_filenames = enforcer.select_priority_context(
        available_files=available_files,
        task_type=task_type
    )

    # Return selected files
    return {f: available_files[f] for f in selected_filenames if f in available_files}


def _load_all_context_files(
    project_path: Path,
    task_type: Optional[str] = None
) -> Dict[str, str]:
    """
    Load all available context files.

    Args:
        project_path: Path to project directory
        task_type: Type of task for conditional loading

    Returns:
        Dictionary of filename -> content
    """
    files = {}

    # Core files
    core_files = ["CATALOG.md", "STATE.md", "DECISIONS.md"]
    for filename in core_files:
        file_path = project_path / filename
        if file_path.exists():
            # Skip DECISIONS.md for simple tasks
            if filename == "DECISIONS.md" and task_type in {"lint-fix", "format-fix", "simple-test-fix"}:
                continue
            try:
                files[filename] = file_path.read_text()
            except Exception:
                pass

    # Session handoff
    sessions_dir = project_path / "sessions"
    if sessions_dir.exists():
        latest = _find_latest_session(sessions_dir)
        if latest:
            try:
                session_path = project_path / latest
                files["session_handoff"] = session_path.read_text()
            except Exception:
                pass

    # Hot patterns
    hot_patterns = project_path / ".claude" / "memory" / "hot-patterns.md"
    if hot_patterns.exists():
        try:
            files["hot_patterns"] = hot_patterns.read_text()
        except Exception:
            pass

    # Cross-repo state
    global_state = project_path / ".aibrain" / "global-state-cache.md"
    if global_state.exists():
        try:
            files["global_state"] = global_state.read_text()
        except Exception:
            pass

    return files


def estimate_context_tokens(
    context_files: Dict[str, str]
) -> Dict[str, int]:
    """
    Estimate token count for each context file.

    Args:
        context_files: Dictionary of filename -> content

    Returns:
        Dictionary of filename -> estimated tokens
    """
    try:
        from governance.token_estimator import TokenEstimator
        estimator = TokenEstimator()
    except ImportError:
        # Fallback: rough estimate
        return {f: len(c) // 4 for f, c in context_files.items()}

    return {
        filename: estimator.estimate(content)
        for filename, content in context_files.items()
    }


def compress_context_to_budget(
    context_files: Dict[str, str],
    max_tokens: int = 2000
) -> Dict[str, str]:
    """
    Compress context files to fit within token budget.

    Strategies:
    1. Remove low-priority files first
    2. Truncate large files
    3. Summarize if compression module available

    Args:
        context_files: Context files to compress
        max_tokens: Maximum total tokens

    Returns:
        Compressed context files
    """
    token_counts = estimate_context_tokens(context_files)
    total_tokens = sum(token_counts.values())

    if total_tokens <= max_tokens:
        return context_files

    # Priority order (higher = keep)
    priority = {
        "STATE.md": 5,
        "CATALOG.md": 4,
        "session_handoff": 3,
        "global_state": 2,
        "DECISIONS.md": 1,
        "hot_patterns": 1,
    }

    # Sort by priority
    sorted_files = sorted(
        context_files.keys(),
        key=lambda f: priority.get(f, 0),
        reverse=True
    )

    # Select files until budget exhausted
    result = {}
    remaining = max_tokens

    for filename in sorted_files:
        content = context_files[filename]
        tokens = token_counts.get(filename, 0)

        if tokens <= remaining:
            result[filename] = content
            remaining -= tokens
        elif remaining > 500:
            # Truncate file to fit remaining budget
            ratio = remaining / tokens
            truncated_len = int(len(content) * ratio * 0.9)
            result[filename] = content[:truncated_len] + "\n[...truncated...]"
            break

    return result
