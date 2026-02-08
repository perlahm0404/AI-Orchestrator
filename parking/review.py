"""
Icebox Review Workflows

Provides:
- Interactive CLI review of raw ideas
- Auto-archive rules (>90 days without review)
- Dependency health checks
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from parking.icebox import IceboxIdea
from parking.service import (
    list_ideas,
    get_idea,
    update_idea,
    archive_idea,
    get_stale_ideas,
    promote_to_parked_task,
    promote_to_pending_task,
)


class IceboxReviewer:
    """Workflow for reviewing and promoting ideas."""

    def __init__(self, project: Optional[str] = None):
        """
        Initialize reviewer.

        Args:
            project: Optional project filter
        """
        self.project = project

    def interactive_review(self) -> Dict[str, int]:
        """
        Interactive CLI review of raw ideas.

        Returns:
            Summary of review actions taken
        """
        ideas = list_ideas(project=self.project, status="raw")

        if not ideas:
            print(f"\n✨ No raw ideas to review")
            if self.project:
                print(f"   (project: {self.project})")
            return {"reviewed": 0, "promoted": 0, "archived": 0, "skipped": 0}

        summary = {"reviewed": 0, "promoted": 0, "archived": 0, "skipped": 0}

        print(f"\n{'='*60}")
        print(f"📋 INTERACTIVE ICEBOX REVIEW")
        print(f"   {len(ideas)} ideas to review")
        if self.project:
            print(f"   Project: {self.project}")
        print(f"{'='*60}\n")

        for i, idea in enumerate(ideas, 1):
            self._display_idea(idea, i, len(ideas))

            action = self._prompt_action()
            summary["reviewed"] += 1

            if action == "p":
                # Promote
                status = self._prompt_status()
                project = self.project or idea.project

                if status == "pending":
                    task_id = promote_to_pending_task(idea.id, project)
                else:
                    task_id = promote_to_parked_task(idea.id, project)

                if task_id:
                    print(f"   ✅ Promoted to {task_id}")
                    summary["promoted"] += 1
                else:
                    print(f"   ❌ Failed to promote")

            elif action == "a":
                # Archive
                reason = input("   Archive reason: ").strip()
                if not reason:
                    reason = "Reviewed and archived"

                if archive_idea(idea.id, reason):
                    print(f"   📦 Archived")
                    summary["archived"] += 1
                else:
                    print(f"   ❌ Failed to archive")

            elif action == "e":
                # Edit
                self._edit_idea(idea)
                print(f"   ✏️ Updated")

            elif action == "s":
                # Skip
                # Mark as reviewed but leave in raw
                idea.last_reviewed = datetime.now(timezone.utc).isoformat()
                update_idea(idea)
                print(f"   ⏭️ Skipped (marked as reviewed)")
                summary["skipped"] += 1

            elif action == "q":
                # Quit
                print(f"\n   Stopping review. {summary['reviewed']-1} ideas reviewed.")
                summary["reviewed"] -= 1  # Don't count the quit action
                break

            print()

        print(f"\n{'='*60}")
        print(f"📊 REVIEW SUMMARY")
        print(f"   Reviewed: {summary['reviewed']}")
        print(f"   Promoted: {summary['promoted']}")
        print(f"   Archived: {summary['archived']}")
        print(f"   Skipped: {summary['skipped']}")
        print(f"{'='*60}\n")

        return summary

    def _display_idea(self, idea: IceboxIdea, current: int, total: int) -> None:
        """Display an idea for review."""
        priority_emoji = ["🔴", "🟠", "🟡", "⚪"][min(idea.priority, 3)]

        print(f"[{current}/{total}] {idea.id} {priority_emoji} P{idea.priority}")
        print(f"Title: {idea.title}")
        print(f"Category: {idea.category} | Effort: {idea.effort_estimate}")
        print(f"Project: {idea.project}")
        if idea.tags:
            print(f"Tags: {', '.join(idea.tags)}")
        print(f"Created: {idea.created_at}")
        print()
        print(f"Description:")
        print(f"  {idea.description[:200]}{'...' if len(idea.description) > 200 else ''}")
        print()

    def _prompt_action(self) -> str:
        """Prompt for review action."""
        while True:
            action = input("[P]romote / [A]rchive / [E]dit / [S]kip / [Q]uit: ").strip().lower()
            if action in ["p", "a", "e", "s", "q"]:
                return action
            print("   Invalid choice. Try again.")

    def _prompt_status(self) -> str:
        """Prompt for target status."""
        while True:
            status = input("   Promote to [parked] or [pending]: ").strip().lower()
            if status in ["parked", "pending"]:
                return status
            print("   Invalid choice. Enter 'parked' or 'pending'.")

    def _edit_idea(self, idea: IceboxIdea) -> None:
        """Edit an idea's fields."""
        print("   Edit fields (press Enter to keep current):")

        # Title
        new_title = input(f"   Title [{idea.title}]: ").strip()
        if new_title:
            idea.title = new_title

        # Priority
        new_priority = input(f"   Priority (0-3) [{idea.priority}]: ").strip()
        if new_priority and new_priority.isdigit():
            idea.priority = min(int(new_priority), 3)

        # Effort
        new_effort = input(f"   Effort (XS/S/M/L/XL) [{idea.effort_estimate}]: ").strip().upper()
        if new_effort in ["XS", "S", "M", "L", "XL"]:
            idea.effort_estimate = new_effort  # type: ignore[assignment]

        # Tags
        new_tags = input(f"   Tags (comma-sep) [{','.join(idea.tags)}]: ").strip()
        if new_tags:
            idea.tags = [t.strip() for t in new_tags.split(",") if t.strip()]

        idea.last_reviewed = datetime.now(timezone.utc).isoformat()
        update_idea(idea)

    def auto_review(self) -> Dict[str, Any]:
        """
        Automated review based on rules.

        Rules:
        - Ideas > 90 days with no review -> archive
        - Ideas with resolved dependencies -> suggest promotion

        Returns:
            Summary of automated actions
        """
        summary: Dict[str, Any] = {"archived": 0, "suggested_promotions": []}

        # Auto-archive very old ideas
        ancient = get_stale_ideas(days=90)
        for idea in ancient:
            if idea.status == "raw":
                reason = "Auto-archived: no activity for 90+ days"
                if archive_idea(idea.id, reason):
                    summary["archived"] += 1

        # Find ideas that might be ready for promotion
        # (e.g., dependencies resolved)
        for idea in list_ideas(project=self.project, status="raw"):
            if self._check_dependencies_resolved(idea):
                summary["suggested_promotions"].append(idea.id)

        return summary

    def _check_dependencies_resolved(self, idea: IceboxIdea) -> bool:
        """Check if idea's dependencies are resolved."""
        if not idea.dependencies:
            return True

        # Check each dependency
        for dep in idea.dependencies:
            if dep.startswith("IDEA-"):
                # Check if dependent idea is promoted
                dep_idea = get_idea(dep)
                if not dep_idea or dep_idea.status != "promoted":
                    return False
            # TODO: Check task dependencies (TASK-xxx, FEAT-xxx)

        return True


def daily_icebox_maintenance() -> Dict[str, Any]:
    """
    Run daily maintenance on icebox.

    Actions:
    1. Find stale ideas (> 30 days without review) -> notify
    2. Auto-archive ancient ideas (> 90 days, raw status)
    3. Check for orphaned dependencies

    Returns:
        Maintenance summary
    """
    summary: Dict[str, Any] = {
        "stale_count": 0,
        "archived_count": 0,
        "orphaned_deps": [],
    }

    # Find stale ideas for notification
    stale = get_stale_ideas(days=30)
    summary["stale_count"] = len(stale)

    if stale:
        print(f"⏰ {len(stale)} stale ideas need review")
        print(f"   Run: aibrain icebox stale --days 30")

    # Auto-archive very old ideas
    ancient = get_stale_ideas(days=90)
    for idea in ancient:
        if idea.status == "raw":
            reason = "Auto-archived: no activity for 90 days"
            if archive_idea(idea.id, reason):
                summary["archived_count"] += 1
                print(f"   📦 Archived: {idea.id}")

    # Check for orphaned dependencies
    all_ideas = list_ideas(include_archived=True)
    idea_ids = {i.id for i in all_ideas}

    for idea in list_ideas():
        for dep in idea.dependencies:
            if dep.startswith("IDEA-") and dep not in idea_ids:
                summary["orphaned_deps"].append((idea.id, dep))
                print(f"   ⚠️ Orphaned dependency: {idea.id} -> {dep}")

    return summary
