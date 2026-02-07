"""
Tests for Decision Audit Trail (Phase 4)
"""

import json
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from orchestration.decision_audit import (
    DecisionAudit,
    DecisionEntry,
    DecisionType,
    get_audit,
    log_decision,
)


@pytest.fixture
def temp_audit_dir():
    """Create a temporary directory for audit files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def audit(temp_audit_dir):
    """Create a DecisionAudit instance with temp directory."""
    return DecisionAudit(project="test-project", audit_dir=temp_audit_dir)


class TestDecisionEntry:
    """Tests for DecisionEntry dataclass."""

    def test_to_json_includes_checksum(self):
        """Test that to_json includes a checksum."""
        entry = DecisionEntry(
            id="DEC-001",
            timestamp="2026-02-07T14:30:52.123456",
            type="task_started",
            project="test",
            task_id="TASK-001",
            decision="start_bugfix",
            reason="Test reason",
        )
        json_str = entry.to_json()
        data = json.loads(json_str)

        assert "checksum" in data
        assert len(data["checksum"]) == 16  # SHA256 truncated to 16 chars

    def test_from_json_roundtrip(self):
        """Test that entries can be serialized and deserialized."""
        entry = DecisionEntry(
            id="DEC-001",
            timestamp="2026-02-07T14:30:52.123456",
            type="task_started",
            project="test",
            task_id="TASK-001",
            decision="start_bugfix",
            reason="Test reason",
            metadata={"key": "value"},
        )
        json_str = entry.to_json()
        restored = DecisionEntry.from_json(json_str)

        assert restored.id == entry.id
        assert restored.type == entry.type
        assert restored.decision == entry.decision
        assert restored.metadata == entry.metadata


class TestDecisionAuditBasics:
    """Basic functionality tests."""

    def test_log_decision_returns_id(self, audit):
        """Test that log_decision returns a decision ID."""
        decision_id = audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start_bugfix",
            reason="Test task",
            task_id="TASK-001",
        )

        assert decision_id.startswith("DEC-")
        assert len(decision_id) > 10

    def test_log_decision_creates_file(self, audit, temp_audit_dir):
        """Test that logging creates a JSONL file."""
        audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start_bugfix",
            reason="Test task",
        )

        files = list(temp_audit_dir.glob("*.jsonl"))
        assert len(files) == 1
        assert "test-project" in files[0].name

    def test_log_decision_appends_to_file(self, audit, temp_audit_dir):
        """Test that multiple logs append to the same file."""
        audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start_1",
            reason="Task 1",
        )
        audit.log_decision(
            decision_type=DecisionType.TASK_COMPLETED,
            decision="complete_1",
            reason="Task 1 done",
        )

        files = list(temp_audit_dir.glob("*.jsonl"))
        assert len(files) == 1

        with open(files[0], 'r') as f:
            lines = [l for l in f.readlines() if l.strip()]
        assert len(lines) == 2

    def test_log_decision_with_enum(self, audit):
        """Test logging with DecisionType enum."""
        decision_id = audit.log_decision(
            decision_type=DecisionType.RALPH_PASS,
            decision="verified",
            reason="All tests pass",
        )

        assert decision_id is not None

    def test_log_decision_with_string(self, audit):
        """Test logging with string type."""
        decision_id = audit.log_decision(
            decision_type="custom_decision",
            decision="something",
            reason="Custom reason",
        )

        assert decision_id is not None


class TestDecisionAuditRetrieval:
    """Tests for retrieving decisions."""

    def test_get_decisions_for_task(self, audit):
        """Test retrieving decisions for a specific task."""
        audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start",
            reason="Starting",
            task_id="TASK-001",
        )
        audit.log_decision(
            decision_type=DecisionType.TASK_ITERATION,
            decision="iterate",
            reason="Working",
            task_id="TASK-001",
        )
        audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start",
            reason="Different task",
            task_id="TASK-002",
        )

        decisions = audit.get_decisions_for_task("TASK-001")

        assert len(decisions) == 2
        assert all(d.task_id == "TASK-001" for d in decisions)

    def test_get_decisions_for_date(self, audit):
        """Test retrieving decisions for today."""
        audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start",
            reason="Test",
        )

        decisions = list(audit.get_decisions_for_date(date.today()))

        assert len(decisions) == 1

    def test_get_decisions_for_empty_date(self, audit):
        """Test retrieving decisions for a date with no entries."""
        decisions = list(audit.get_decisions_for_date(date(2020, 1, 1)))

        assert len(decisions) == 0


class TestDecisionTree:
    """Tests for decision tree building."""

    def test_build_decision_tree_basic(self, audit):
        """Test building a basic decision tree."""
        parent_id = audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start",
            reason="Starting task",
            task_id="TASK-001",
        )

        audit.log_decision(
            decision_type=DecisionType.TASK_ITERATION,
            decision="iterate_1",
            reason="First iteration",
            task_id="TASK-001",
            parent_id=parent_id,
        )

        tree = audit.build_decision_tree("TASK-001")

        assert tree["task_id"] == "TASK-001"
        assert tree["decision_count"] == 2
        assert len(tree["tree"]) == 1  # One root
        assert len(tree["tree"][0]["children"]) == 1  # One child

    def test_build_decision_tree_with_parent_stack(self, audit):
        """Test decision tree with automatic parent tracking."""
        # Start task (pushes to parent stack)
        audit.log_task_started(
            task_id="TASK-001",
            agent="bugfix",
            description="Fix authentication bug",
        )

        # Log iteration (should auto-link to parent)
        audit.log_iteration(
            task_id="TASK-001",
            iteration=1,
            action="analyze",
            result="Found root cause",
        )

        # Complete task (pops from parent stack)
        audit.log_task_completed(
            task_id="TASK-001",
            verdict="PASS",
            iterations=1,
        )

        tree = audit.build_decision_tree("TASK-001")

        assert tree["decision_count"] == 3
        # The iteration should be a child of task_started
        assert len(tree["tree"][0]["children"]) == 1


class TestHelperMethods:
    """Tests for convenience helper methods."""

    def test_log_task_started(self, audit):
        """Test the log_task_started helper."""
        decision_id = audit.log_task_started(
            task_id="TASK-001",
            agent="bugfix",
            description="Fix bug",
        )

        decisions = audit.get_decisions_for_task("TASK-001")
        assert len(decisions) == 1
        assert decisions[0].type == "task_started"
        assert decisions[0].agent == "bugfix"

    def test_log_task_completed(self, audit):
        """Test the log_task_completed helper."""
        audit.log_task_started(
            task_id="TASK-001",
            agent="bugfix",
            description="Fix bug",
        )
        audit.log_task_completed(
            task_id="TASK-001",
            verdict="PASS",
            iterations=3,
            cost_usd=0.05,
        )

        decisions = audit.get_decisions_for_task("TASK-001")
        assert len(decisions) == 2
        assert decisions[1].type == "task_completed"
        assert decisions[1].iteration == 3
        assert decisions[1].cost_usd == 0.05

    def test_log_iteration(self, audit):
        """Test the log_iteration helper."""
        audit.log_iteration(
            task_id="TASK-001",
            iteration=5,
            action="fix_code",
            result="Applied patch to auth.py",
            agent="bugfix",
            tokens_used=1500,
        )

        decisions = audit.get_decisions_for_task("TASK-001")
        assert len(decisions) == 1
        assert decisions[0].iteration == 5
        assert decisions[0].tokens_used == 1500

    def test_log_ralph_verdict(self, audit):
        """Test the log_ralph_verdict helper."""
        audit.log_ralph_verdict(
            task_id="TASK-001",
            verdict="PASS",
            reason="All tests passing",
            files_changed=["auth.py", "test_auth.py"],
        )

        decisions = audit.get_decisions_for_task("TASK-001")
        assert len(decisions) == 1
        assert decisions[0].type == "ralph_pass"
        assert "files_changed" in decisions[0].metadata


class TestPIIRedaction:
    """Tests for PII redaction functionality."""

    def test_redaction_disabled_by_default(self, temp_audit_dir):
        """Test that PII is not redacted by default."""
        audit = DecisionAudit(project="test", audit_dir=temp_audit_dir)

        audit.log_decision(
            decision_type=DecisionType.CUSTOM,
            decision="test",
            reason="test",
            metadata={"email": "user@example.com"},
        )

        decisions = list(audit.get_decisions_for_date(date.today()))
        assert decisions[0].metadata["email"] == "user@example.com"

    def test_redaction_when_enabled(self, temp_audit_dir):
        """Test that PII is redacted when enabled."""
        audit = DecisionAudit(
            project="test",
            audit_dir=temp_audit_dir,
            redact_pii=True,
        )

        audit.log_decision(
            decision_type=DecisionType.CUSTOM,
            decision="test",
            reason="test",
            metadata={"user_email": "user@example.com", "patient_name": "John Doe"},
        )

        decisions = list(audit.get_decisions_for_date(date.today()))
        assert decisions[0].metadata["user_email"] == "[REDACTED]"
        assert decisions[0].metadata["patient_name"] == "[REDACTED]"


class TestSummaryStats:
    """Tests for summary statistics."""

    def test_get_summary_stats(self, audit):
        """Test getting summary statistics."""
        audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start",
            reason="Test",
            cost_usd=0.01,
            tokens_used=100,
        )
        audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start",
            reason="Test 2",
            cost_usd=0.02,
            tokens_used=200,
        )
        audit.log_decision(
            decision_type=DecisionType.RALPH_PASS,
            decision="pass",
            reason="Verified",
        )

        stats = audit.get_summary_stats()

        assert stats["count"] == 3
        assert stats["total_cost_usd"] == 0.03
        assert stats["total_tokens"] == 300
        assert stats["by_type"]["task_started"] == 2
        assert stats["by_type"]["ralph_pass"] == 1

    def test_get_summary_stats_empty(self, audit):
        """Test summary stats for empty date."""
        stats = audit.get_summary_stats(date(2020, 1, 1))

        assert stats["count"] == 0


class TestIntegrity:
    """Tests for integrity verification."""

    def test_verify_integrity_valid(self, audit):
        """Test integrity verification with valid entries."""
        audit.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision="start",
            reason="Test",
        )

        result = audit.verify_integrity()

        assert result["valid"] == 1
        assert result["invalid"] == 0
        assert result["integrity_ok"] is True


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_get_audit_returns_singleton(self, temp_audit_dir, monkeypatch):
        """Test that get_audit returns the same instance."""
        # Clear the global dict
        import orchestration.decision_audit as module
        module._default_audits = {}

        audit1 = get_audit("test-project")
        audit2 = get_audit("test-project")

        assert audit1 is audit2

    def test_log_decision_global(self, temp_audit_dir, monkeypatch):
        """Test the global log_decision function."""
        import orchestration.decision_audit as module
        module._default_audits = {}

        decision_id = log_decision(
            project="test-global",
            decision_type=DecisionType.TASK_STARTED,
            decision="start",
            reason="Global test",
        )

        assert decision_id.startswith("DEC-")
