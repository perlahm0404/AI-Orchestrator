"""
Content Approval Gate - Interactive human review for editorial content

Implements approval gate following stop_hook.py pattern:
- Display validation summary (SEO score, issues, warnings)
- Show content preview (first 30 lines)
- Interactive prompt: [A]pprove / [R]eject / [M]odify
- Audit logging to .aibrain/content-approvals.jsonl

Usage:
    from orchestration.content_approval import ContentApprovalGate, ApprovalRequest

    gate = ContentApprovalGate()
    request = ApprovalRequest(
        content_id="EDITORIAL-001",
        draft_path=Path("blog/draft.md"),
        seo_score=75,
        validation_issues=[],
        validation_warnings=["Minor keyword placement issue"],
        stage="review"
    )
    result = gate.request_approval(request)

    if result.decision == ApprovalDecision.APPROVE:
        # Proceed to publication
    elif result.decision == ApprovalDecision.REJECT:
        # Move to rejected/
    else:  # MODIFY
        # Return to generation with notes

Implementation: Phase 5 - Editorial Automation
"""

from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class ApprovalDecision(Enum):
    """Human approval decisions"""
    APPROVE = "approve"  # Publish content
    REJECT = "reject"    # Discard draft
    MODIFY = "modify"    # Request modifications


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    content_id: str
    draft_path: Path
    seo_score: int
    validation_issues: List[str]
    validation_warnings: List[str]
    stage: str  # Current pipeline stage


@dataclass
class ApprovalResult:
    """Result of approval gate"""
    decision: ApprovalDecision
    approved_by: str  # Username or "human"
    timestamp: str
    notes: Optional[str] = None


class ContentApprovalGate:
    """
    Interactive approval gate for editorial content.

    Follows stop_hook.py interactive pattern (lines 220-265):
    - Display summary with validation details
    - Show content preview
    - Prompt for decision (A/R/M)
    - Log decision to audit trail
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize approval gate.

        Args:
            log_dir: Directory for audit logs (default: .aibrain)
        """
        self.log_dir = log_dir or Path(".aibrain")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "content-approvals.jsonl"

    def request_approval(self, request: ApprovalRequest) -> ApprovalResult:
        """
        Request human approval for content (interactive gate).

        Displays:
        - SEO score and validation summary
        - Content preview (first 30 lines)
        - Decision prompt: [A]pprove / [R]eject / [M]odify

        Args:
            request: ApprovalRequest with content details

        Returns:
            ApprovalResult with decision
        """
        # Display header
        print("\n" + "="*60)
        print("📝 CONTENT READY FOR REVIEW")
        print("="*60)

        # Display validation summary
        self._display_validation_summary(request)

        # Display content preview
        self._display_content_preview(request.draft_path)

        # Prompt for decision
        decision = self._prompt_for_decision()

        # Collect optional notes
        notes = None
        if decision in [ApprovalDecision.REJECT, ApprovalDecision.MODIFY]:
            notes_input = input("\nNotes (optional): ").strip()
            notes = notes_input if notes_input else None

        # Create result
        result = ApprovalResult(
            decision=decision,
            approved_by="human",  # Could be enhanced to get actual username
            timestamp=datetime.now().isoformat(),
            notes=notes
        )

        # Log decision to audit trail
        self._log_approval(request, result)

        # Display confirmation
        self._display_confirmation(result)

        return result

    def _display_validation_summary(self, request: ApprovalRequest) -> None:
        """
        Display validation summary.

        Args:
            request: ApprovalRequest with validation details
        """
        print(f"\n📊 SEO Score: {request.seo_score}/100")

        if request.validation_issues:
            print("\n⚠️  Issues:")
            for issue in request.validation_issues:
                print(f"  - {issue}")

        if request.validation_warnings:
            print("\n⚡ Warnings:")
            for warning in request.validation_warnings:
                print(f"  - {warning}")

        if not request.validation_issues and not request.validation_warnings:
            print("\n✅ No issues or warnings")

    def _display_content_preview(self, draft_path: Path) -> None:
        """
        Display content preview (first 30 lines).

        Args:
            draft_path: Path to draft file
        """
        print(f"\n📄 Preview ({draft_path.name}):")
        print("-" * 60)

        try:
            with open(draft_path, 'r') as f:
                lines = f.readlines()[:30]
                print("".join(lines), end="")

            if len(lines) >= 30:
                print("\n... (truncated)")

        except Exception as e:
            print(f"⚠️  Error reading draft: {e}")

        print("-" * 60)

    def _prompt_for_decision(self) -> ApprovalDecision:
        """
        Prompt user for approval decision.

        Returns:
            ApprovalDecision (APPROVE, REJECT, or MODIFY)
        """
        print("\n" + "="*60)
        print("OPTIONS:")
        print("  [A] Approve and publish")
        print("  [R] Reject (move to rejected/)")
        print("  [M] Modify (request changes)")
        print("="*60)

        decision_map = {
            'A': ApprovalDecision.APPROVE,
            'R': ApprovalDecision.REJECT,
            'M': ApprovalDecision.MODIFY
        }

        while True:
            try:
                response = input("\nYour choice [A/R/M]: ").strip().upper()

                if response in decision_map:
                    return decision_map[response]
                else:
                    print("Invalid choice. Please enter A, R, or M.")

            except (EOFError, KeyboardInterrupt):
                print("\n\n⚠️  Interrupted. Defaulting to REJECT.")
                return ApprovalDecision.REJECT

    def _display_confirmation(self, result: ApprovalResult) -> None:
        """
        Display confirmation message.

        Args:
            result: ApprovalResult
        """
        print()

        if result.decision == ApprovalDecision.APPROVE:
            print("✅ Content approved for publication")
        elif result.decision == ApprovalDecision.REJECT:
            print("❌ Content rejected")
            if result.notes:
                print(f"   Reason: {result.notes}")
        else:  # MODIFY
            print("🔄 Modifications requested")
            if result.notes:
                print(f"   Notes: {result.notes}")

    def _log_approval(self, request: ApprovalRequest, result: ApprovalResult) -> None:
        """
        Log approval decision to audit trail.

        Appends to .aibrain/content-approvals.jsonl in JSONL format:
        Each line is a JSON object with approval metadata.

        Args:
            request: ApprovalRequest
            result: ApprovalResult
        """
        log_entry = {
            "timestamp": result.timestamp,
            "content_id": request.content_id,
            "draft_path": str(request.draft_path),
            "seo_score": request.seo_score,
            "decision": result.decision.value,
            "approved_by": result.approved_by,
            "notes": result.notes,
            "validation_issues": request.validation_issues,
            "validation_warnings": request.validation_warnings
        }

        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"⚠️  Failed to log approval: {e}")

    def get_approval_history(
        self,
        content_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get approval history from audit log.

        Args:
            content_id: Filter by content ID (optional)
            limit: Maximum number of entries to return

        Returns:
            List of approval entries (most recent first)
        """
        if not self.log_file.exists():
            return []

        entries = []

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())

                    # Filter by content_id if specified
                    if content_id and entry.get("content_id") != content_id:
                        continue

                    entries.append(entry)

        except Exception as e:
            print(f"⚠️  Failed to read approval log: {e}")

        # Return most recent first
        return list(reversed(entries))[-limit:]

    def get_approval_stats(self) -> Dict[str, int]:
        """
        Get approval statistics.

        Returns:
            Dict with counts by decision type
        """
        stats = {
            "approved": 0,
            "rejected": 0,
            "modified": 0,
            "total": 0
        }

        if not self.log_file.exists():
            return stats

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    decision = entry.get("decision", "")

                    if decision == "approve":
                        stats["approved"] += 1
                    elif decision == "reject":
                        stats["rejected"] += 1
                    elif decision == "modify":
                        stats["modified"] += 1

                    stats["total"] += 1

        except Exception as e:
            print(f"⚠️  Failed to compute approval stats: {e}")

        return stats
