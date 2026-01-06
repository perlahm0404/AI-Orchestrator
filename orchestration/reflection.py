"""
Session Reflection System

Generates handoff documents at the end of agent sessions to provide
continuity between sessions. Captures:
- What was accomplished
- What was NOT done
- Blockers and open questions
- Files modified
- Ralph verdicts
- Handoff notes for next session

Usage:
    from orchestration.reflection import SessionReflection, SessionResult

    # At end of agent execution
    reflection = SessionReflection(
        session_id="session-123",
        agent_name="bugfix",
        result=result
    )

    handoff_path = reflection.generate()
    # → Writes sessions/{date}-{task}.md
    # → Updates sessions/latest.md
    # → Updates STATE.md

Implementation: v5.0 - Session Reflection
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import subprocess
from enum import Enum

from ralph.engine import Verdict, VerdictType


class SessionStatus(Enum):
    """Session outcome status."""
    COMPLETED = "COMPLETED"     # Task fully done
    BLOCKED = "BLOCKED"         # Cannot proceed due to blocker
    FAILED = "FAILED"           # Execution failed
    PARTIAL = "PARTIAL"         # Some work done, more remains


@dataclass
class FileChange:
    """Represents a file change in the session."""
    file: str
    action: str  # "Created" | "Modified" | "Deleted"
    lines_added: int = 0
    lines_removed: int = 0


@dataclass
class SessionTestSummary:
    """Test execution status summary for a session."""
    total: int
    passed: int
    failed: int
    skipped: int = 0
    added: int = 0
    removed: int = 0
    modified: int = 0


@dataclass
class SessionResult:
    """
    Complete result of an agent session.

    This is what agents return from execute() and what
    gets passed to SessionReflection.
    """
    task_id: str
    status: SessionStatus

    # What was accomplished
    accomplished: List[str] = field(default_factory=list)

    # What was NOT done
    incomplete: List[str] = field(default_factory=list)

    # Blockers encountered
    blockers: List[str] = field(default_factory=list)

    # Files changed
    file_changes: List[FileChange] = field(default_factory=list)

    # Test status
    tests: Optional[SessionTestSummary] = None

    # Ralph verdict
    verdict: Optional[Verdict] = None

    # Free-form handoff notes
    handoff_notes: str = ""

    # Next steps (if incomplete)
    next_steps: List[str] = field(default_factory=list)

    # Risk assessment
    regression_risk: str = "LOW"  # LOW | MEDIUM | HIGH
    merge_confidence: str = "HIGH"  # HIGH | MEDIUM | LOW
    requires_review: bool = False


class SessionReflection:
    """
    Generates session handoff documents.

    Responsibilities:
    1. Write handoff markdown to sessions/{date}-{task}.md
    2. Update sessions/latest.md symlink
    3. Update STATE.md with new status
    4. Generate narrative handoff notes (optional LLM)
    """

    def __init__(
        self,
        session_id: str,
        agent_name: str,
        result: SessionResult,
        project_root: Optional[Path] = None
    ):
        """
        Initialize session reflection.

        Args:
            session_id: Unique session identifier
            agent_name: Name of agent (bugfix, codequality, etc.)
            result: SessionResult from agent execution
            project_root: Root of AI Orchestrator project (defaults to CWD)
        """
        self.session_id = session_id
        self.agent_name = agent_name
        self.result = result
        self.project_root = project_root or Path.cwd()
        self.sessions_dir = self.project_root / "sessions"

        # Ensure sessions directory exists
        self.sessions_dir.mkdir(exist_ok=True)

        # Timestamps
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def set_timing(self, start: datetime, end: datetime) -> None:
        """Set session start and end times."""
        self.start_time = start
        self.end_time = end

    def generate(self) -> Path:
        """
        Generate handoff document and update all artifacts.

        Returns:
            Path to generated handoff document
        """
        # 1. Generate handoff markdown
        handoff_path = self._write_handoff_doc()

        # 2. Update latest.md symlink
        self._update_latest_symlink(handoff_path)

        # 3. Update STATE.md (optional, if exists)
        self._update_state_file()

        return handoff_path

    def _write_handoff_doc(self) -> Path:
        """
        Write handoff markdown document.

        Returns:
            Path to written document
        """
        # Generate filename: {date}-{task_id}.md
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}-{self.result.task_id}.md"
        filepath = self.sessions_dir / filename

        # Generate content
        content = self._generate_handoff_content()

        # Write to file
        filepath.write_text(content)

        return filepath

    def _generate_handoff_content(self) -> str:
        """Generate the markdown content for handoff document."""
        lines = []

        # Header
        lines.append(f"# Session: {datetime.now().strftime('%Y-%m-%d')} - {self.result.task_id}")
        lines.append("")
        lines.append(f"**Session ID**: {self.session_id}")
        lines.append(f"**Task ID**: {self.result.task_id}")
        lines.append(f"**Agent**: {self.agent_name}")
        lines.append(f"**Outcome**: {self.result.status.value}")

        # Timing (if available)
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            lines.append(f"**Duration**: {duration:.1f}s")
            lines.append(f"**Time**: {self.start_time.strftime('%H:%M:%S')} - {self.end_time.strftime('%H:%M:%S')}")

        lines.append("")

        # What Was Accomplished
        lines.append("## What Was Accomplished")
        lines.append("")
        if self.result.accomplished:
            for item in self.result.accomplished:
                lines.append(f"- {item}")
        else:
            lines.append("- *(No items completed)*")
        lines.append("")

        # What Was NOT Done
        lines.append("## What Was NOT Done")
        lines.append("")
        if self.result.incomplete:
            for item in self.result.incomplete:
                lines.append(f"- {item}")
        else:
            lines.append("- *(All planned items completed)*")
        lines.append("")

        # Blockers / Open Questions
        lines.append("## Blockers / Open Questions")
        lines.append("")
        if self.result.blockers:
            for i, blocker in enumerate(self.result.blockers, 1):
                lines.append(f"{i}. {blocker}")
        else:
            lines.append("- *(No blockers)*")
        lines.append("")

        # Ralph Verdict
        if self.result.verdict:
            lines.append("## Ralph Verdict")
            lines.append("")
            lines.append(f"- **Status**: {self.result.verdict.type.value}")
            lines.append(f"- **Safe to Merge**: {'✅ YES' if self.result.verdict.safe_to_merge else '❌ NO'}")

            if self.result.tests:
                lines.append(f"- **Tests**: {self.result.tests.passed}/{self.result.tests.total} passing")

            if self.result.verdict.regression_detected:
                lines.append(f"- **⚠️  Regression Detected**: YES")

            if self.result.verdict.pre_existing_failures:
                lines.append(f"- **Pre-existing Failures**: {', '.join(self.result.verdict.pre_existing_failures)}")

            # Step details
            lines.append("")
            lines.append("### Verification Steps")
            lines.append("")
            for step in self.result.verdict.steps:
                icon = "✅" if step.passed else "❌"
                status = "PASS" if step.passed else "FAIL"
                lines.append(f"- {icon} **{step.step}**: {status} ({step.duration_ms}ms)")

            lines.append("")

        # Files Modified
        lines.append("## Files Modified")
        lines.append("")
        if self.result.file_changes:
            lines.append("| File | Action | Lines Changed |")
            lines.append("|------|--------|---------------|")
            for change in self.result.file_changes:
                delta = f"+{change.lines_added}/-{change.lines_removed}"
                lines.append(f"| {change.file} | {change.action} | {delta} |")
        else:
            lines.append("- *(No files modified)*")
        lines.append("")

        # Tests Changed
        if self.result.tests and (self.result.tests.added or self.result.tests.removed or self.result.tests.modified):
            lines.append("## Tests Changed")
            lines.append("")
            if self.result.tests.added:
                lines.append(f"- Tests added: {self.result.tests.added}")
            if self.result.tests.removed:
                lines.append(f"- Tests removed: {self.result.tests.removed}")
            if self.result.tests.modified:
                lines.append(f"- Tests modified: {self.result.tests.modified}")
            lines.append("")

        # Handoff Notes
        lines.append("## Handoff Notes")
        lines.append("")
        if self.result.handoff_notes:
            lines.append(self.result.handoff_notes)
        else:
            lines.append("*(No additional notes)*")
        lines.append("")

        # Next Steps (if incomplete)
        if self.result.next_steps:
            lines.append("## Next Steps")
            lines.append("")
            for i, step in enumerate(self.result.next_steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        # Risk Assessment
        lines.append("## Risk Assessment")
        lines.append("")
        lines.append(f"- **Regression risk**: {self.result.regression_risk}")
        lines.append(f"- **Merge confidence**: {self.result.merge_confidence}")
        lines.append(f"- **Requires human review**: {'YES' if self.result.requires_review else 'NO'}")
        lines.append("")

        return "\n".join(lines)

    def _update_latest_symlink(self, handoff_path: Path) -> None:
        """
        Update sessions/latest.md symlink to point to new handoff.

        Args:
            handoff_path: Path to the new handoff document
        """
        latest_link = self.sessions_dir / "latest.md"

        # Remove existing symlink if present
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()

        # Create new symlink (relative path)
        latest_link.symlink_to(handoff_path.name)

    def _update_state_file(self) -> None:
        """
        Update STATE.md with session outcome.

        This is optional - only updates if STATE.md exists and
        contains a section for the task.
        """
        state_file = self.project_root / "STATE.md"

        if not state_file.exists():
            return

        # For now, just append a note to STATE.md
        # In production, would parse and update specific sections
        try:
            content = state_file.read_text()

            # Add a session note at the end
            note = f"\n\n---\n\n**Session {self.session_id}** ({datetime.now().strftime('%Y-%m-%d %H:%M')}): {self.result.status.value} - {self.result.task_id}\n"

            # Only append if not already present
            if self.session_id not in content:
                state_file.write_text(content + note)
        except Exception:
            # Silently fail - STATE.md update is optional
            pass

    def _get_git_changes(self) -> List[FileChange]:
        """
        Extract file changes from git diff.

        Returns:
            List of FileChange objects
        """
        try:
            # Run git diff --stat
            result = subprocess.run(
                ["git", "diff", "--stat", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return []

            # Parse output
            changes = []
            for line in result.stdout.split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        filename = parts[0].strip()
                        stats = parts[1].strip()

                        # Parse +/- stats
                        lines_added = stats.count("+")
                        lines_removed = stats.count("-")

                        changes.append(FileChange(
                            file=filename,
                            action="Modified",
                            lines_added=lines_added,
                            lines_removed=lines_removed
                        ))

            return changes
        except Exception:
            return []


def create_session_handoff(
    session_id: str,
    agent_name: str,
    result: SessionResult,
    project_root: Optional[Path] = None
) -> Path:
    """
    Convenience function to create a session handoff.

    Args:
        session_id: Unique session identifier
        agent_name: Name of agent
        result: SessionResult from agent execution
        project_root: Root of AI Orchestrator project

    Returns:
        Path to generated handoff document

    Example:
        result = SessionResult(
            task_id="BUG-001",
            status=SessionStatus.COMPLETED,
            accomplished=["Fixed authentication bug"],
            verdict=verdict
        )

        handoff = create_session_handoff("session-123", "bugfix", result)
    """
    reflection = SessionReflection(session_id, agent_name, result, project_root)
    return reflection.generate()
