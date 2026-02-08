"""
Verification Audit Trail - Anti-Shirking Enforcement

Logs all verification events for audit and compliance:
- Specialist verification attempts
- Ralph availability checks
- Bypass attempts detected
- Synthesis validation results
- Final task verdicts

All events are logged to:
1. Standard Python logger (INFO+)
2. Structured JSON file (.aibrain/audit/verification.jsonl)

This provides evidence trail for:
- Why tasks were marked complete
- When verification was bypassed (and why it was blocked)
- Specialist performance metrics

Author: Claude Code (Anti-Shirking Implementation)
Date: 2026-02-08
Version: 1.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum


class VerificationEvent(str, Enum):
    """Types of verification events for audit trail."""
    SPECIALIST_START = "specialist_start"
    SPECIALIST_COMPLETE = "specialist_complete"
    RALPH_AVAILABLE = "ralph_available"
    RALPH_UNAVAILABLE = "ralph_unavailable"
    VERIFICATION_PASS = "verification_pass"
    VERIFICATION_FAIL = "verification_fail"
    VERIFICATION_BLOCKED = "verification_blocked"
    BYPASS_ATTEMPT = "bypass_attempt"  # Critical security event
    VALIDATION_PASS = "validation_pass"
    VALIDATION_FAIL = "validation_fail"
    SYNTHESIS_VERIFIED = "synthesis_verified"
    SYNTHESIS_BLOCKED = "synthesis_blocked"
    TASK_COMPLETE = "task_complete"
    TASK_BLOCKED = "task_blocked"


logger = logging.getLogger(__name__)


class VerificationAudit:
    """
    Audit trail for all verification events.

    Provides tamper-evident logging of:
    - All verification attempts
    - All bypass attempts (blocked by new enforcement)
    - Specialist and synthesis verdicts
    - Human-readable summaries

    Logs are append-only JSONL for forensic analysis.
    """

    def __init__(self, project_path: Optional[Path] = None):
        """
        Initialize audit trail.

        Args:
            project_path: Project root (for audit file location)
        """
        self.project_path = project_path or Path.cwd()
        self.audit_dir = self.project_path / ".aibrain" / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.audit_dir / "verification.jsonl"

        # Session ID for correlation
        self._session_id = datetime.now().strftime("%Y%m%d-%H%M%S")

        logger.info(
            f"VerificationAudit initialized: session={self._session_id}, "
            f"audit_file={self.audit_file}"
        )

    def log_event(
        self,
        event_type: VerificationEvent,
        task_id: str,
        details: Dict[str, Any],
        specialist_type: Optional[str] = None,
        verdict: Optional[str] = None,
        is_security_event: bool = False
    ) -> None:
        """
        Log a verification event.

        Args:
            event_type: Type of event
            task_id: Task identifier
            details: Event details (serializable)
            specialist_type: Which specialist (if applicable)
            verdict: Verdict value (if applicable)
            is_security_event: If True, also log to security log
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self._session_id,
            "event_type": event_type.value,
            "task_id": task_id,
            "specialist_type": specialist_type,
            "verdict": verdict,
            "details": details
        }

        # Log to Python logger
        log_level = logging.WARNING if is_security_event else logging.INFO
        logger.log(
            log_level,
            f"AUDIT [{event_type.value}] task={task_id} "
            f"specialist={specialist_type} verdict={verdict}"
        )

        # Append to JSONL file
        try:
            with open(self.audit_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")

        # Security events get extra logging
        if is_security_event:
            self._log_security_event(event)

    def _log_security_event(self, event: Dict[str, Any]) -> None:
        """Log security-sensitive events to separate file."""
        security_file = self.audit_dir / "security.jsonl"
        try:
            with open(security_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write security event: {e}")

    # ========================================================================
    # Convenience Methods for Common Events
    # ========================================================================

    def log_specialist_start(
        self,
        task_id: str,
        specialist_type: str,
        iteration_budget: int
    ) -> None:
        """Log specialist execution start."""
        self.log_event(
            VerificationEvent.SPECIALIST_START,
            task_id,
            {"iteration_budget": iteration_budget},
            specialist_type=specialist_type
        )

    def log_specialist_complete(
        self,
        task_id: str,
        specialist_type: str,
        status: str,
        verdict: str,
        iterations_used: int
    ) -> None:
        """Log specialist execution complete."""
        self.log_event(
            VerificationEvent.SPECIALIST_COMPLETE,
            task_id,
            {
                "status": status,
                "iterations_used": iterations_used
            },
            specialist_type=specialist_type,
            verdict=verdict
        )

    def log_ralph_check(
        self,
        task_id: str,
        is_available: bool,
        reason: Optional[str] = None
    ) -> None:
        """Log Ralph availability check."""
        event_type = (
            VerificationEvent.RALPH_AVAILABLE
            if is_available
            else VerificationEvent.RALPH_UNAVAILABLE
        )
        self.log_event(
            event_type,
            task_id,
            {"reason": reason or ""},
            is_security_event=not is_available  # Unavailable is security concern
        )

    def log_bypass_attempt(
        self,
        task_id: str,
        specialist_type: str,
        attempt_type: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Log a detected bypass attempt.

        CRITICAL: This is a security event - verification was not performed
        but completion was claimed.

        Args:
            task_id: Task identifier
            specialist_type: Which specialist attempted bypass
            attempt_type: Type of bypass (simulation_mode, fake_signal, etc.)
            details: Additional details for forensics
        """
        self.log_event(
            VerificationEvent.BYPASS_ATTEMPT,
            task_id,
            {
                "attempt_type": attempt_type,
                **details
            },
            specialist_type=specialist_type,
            is_security_event=True  # Always a security event
        )
        logger.warning(
            f"SECURITY: Bypass attempt detected for {task_id} "
            f"specialist={specialist_type} type={attempt_type}"
        )

    def log_verification_result(
        self,
        task_id: str,
        specialist_type: Optional[str],
        verdict: str,
        details: Dict[str, Any]
    ) -> None:
        """Log verification result (PASS/FAIL/BLOCKED)."""
        if verdict == "PASS":
            event_type = VerificationEvent.VERIFICATION_PASS
        elif verdict == "BLOCKED":
            event_type = VerificationEvent.VERIFICATION_BLOCKED
        else:
            event_type = VerificationEvent.VERIFICATION_FAIL

        self.log_event(
            event_type,
            task_id,
            details,
            specialist_type=specialist_type,
            verdict=verdict
        )

    def log_validation_result(
        self,
        task_id: str,
        can_proceed: bool,
        passed_count: int,
        total_count: int,
        details: Dict[str, Any]
    ) -> None:
        """Log specialist validation result."""
        event_type = (
            VerificationEvent.VALIDATION_PASS
            if can_proceed
            else VerificationEvent.VALIDATION_FAIL
        )
        self.log_event(
            event_type,
            task_id,
            {
                "passed_count": passed_count,
                "total_count": total_count,
                "pass_rate": passed_count / max(total_count, 1),
                **details
            }
        )

    def log_synthesis_result(
        self,
        task_id: str,
        verdict: str,
        changed_files: List[str],
        details: Dict[str, Any]
    ) -> None:
        """Log synthesis verification result."""
        event_type = (
            VerificationEvent.SYNTHESIS_VERIFIED
            if verdict == "PASS"
            else VerificationEvent.SYNTHESIS_BLOCKED
        )
        self.log_event(
            event_type,
            task_id,
            {
                "changed_files_count": len(changed_files),
                **details
            },
            verdict=verdict
        )

    def log_task_complete(
        self,
        task_id: str,
        status: str,
        verdict: str,
        summary: Dict[str, Any]
    ) -> None:
        """Log final task completion."""
        event_type = (
            VerificationEvent.TASK_COMPLETE
            if verdict == "PASS"
            else VerificationEvent.TASK_BLOCKED
        )
        self.log_event(
            event_type,
            task_id,
            summary,
            verdict=verdict
        )

    # ========================================================================
    # Analysis Methods
    # ========================================================================

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session's verification events.

        Returns:
            Dict with counts of each event type and key metrics
        """
        events = self._read_session_events()

        summary = {
            "session_id": self._session_id,
            "total_events": len(events),
            "specialists_started": 0,
            "specialists_completed": 0,
            "verification_passes": 0,
            "verification_fails": 0,
            "verification_blocks": 0,
            "bypass_attempts": 0,
            "tasks_completed": 0,
            "tasks_blocked": 0
        }

        # Count events by type
        specialists_started = 0
        specialists_completed = 0
        verification_passes = 0
        verification_fails = 0
        verification_blocks = 0
        bypass_attempts = 0
        tasks_completed = 0
        tasks_blocked = 0

        for event in events:
            event_type = event.get("event_type", "")
            if event_type == "specialist_start":
                specialists_started += 1
            elif event_type == "specialist_complete":
                specialists_completed += 1
            elif event_type == "verification_pass":
                verification_passes += 1
            elif event_type == "verification_fail":
                verification_fails += 1
            elif event_type == "verification_blocked":
                verification_blocks += 1
            elif event_type == "bypass_attempt":
                bypass_attempts += 1
            elif event_type == "task_complete":
                tasks_completed += 1
            elif event_type == "task_blocked":
                tasks_blocked += 1

        # Update summary with counts
        summary["specialists_started"] = specialists_started
        summary["specialists_completed"] = specialists_completed
        summary["verification_passes"] = verification_passes
        summary["verification_fails"] = verification_fails
        summary["verification_blocks"] = verification_blocks
        summary["bypass_attempts"] = bypass_attempts
        summary["tasks_completed"] = tasks_completed
        summary["tasks_blocked"] = tasks_blocked

        return summary

    def _read_session_events(self) -> List[Dict[str, Any]]:
        """Read all events from current session."""
        events = []
        try:
            if self.audit_file.exists():
                with open(self.audit_file, "r") as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            if event.get("session_id") == self._session_id:
                                events.append(event)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Could not read audit file: {e}")
        return events


# Global audit instance (lazy initialization)
_audit_instance: Optional[VerificationAudit] = None


def get_audit(project_path: Optional[Path] = None) -> VerificationAudit:
    """
    Get or create the global audit instance.

    Args:
        project_path: Project root (only used on first call)

    Returns:
        VerificationAudit instance
    """
    global _audit_instance
    if _audit_instance is None:
        _audit_instance = VerificationAudit(project_path)
    return _audit_instance
