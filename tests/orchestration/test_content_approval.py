"""
Unit tests for ContentApprovalGate - Interactive human review

Tests:
- Approval gate UI rendering (mocked input)
- Decision logging to JSONL
- Three decision paths (APPROVE, REJECT, MODIFY)
- Approval history retrieval
- Approval statistics
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile
import shutil
import json
from datetime import datetime

from orchestration.content_approval import (
    ContentApprovalGate,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalResult
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def approval_gate(temp_dir):
    """ContentApprovalGate instance with temp log directory"""
    return ContentApprovalGate(log_dir=temp_dir)


@pytest.fixture
def sample_draft(temp_dir):
    """Create a sample draft file"""
    draft_path = temp_dir / "sample-draft.md"
    content = """---
title: "Test Article"
keywords: ["test", "article"]
---

# Test Article

This is a test article with some content.

## Section 1

Content here.

## Section 2

More content here.
"""
    draft_path.write_text(content)
    return draft_path


@pytest.fixture
def sample_request(sample_draft):
    """Sample approval request"""
    return ApprovalRequest(
        content_id="TEST-001",
        draft_path=sample_draft,
        seo_score=75,
        validation_issues=["Keyword density too low"],
        validation_warnings=["Missing meta description"],
        stage="review"
    )


class TestApprovalDecisions:
    """Test the three approval decision paths"""

    @patch('builtins.input', return_value='A')
    def test_approve_decision(self, mock_input, approval_gate, sample_request):
        """User approves content"""
        result = approval_gate.request_approval(sample_request)

        assert result.decision == ApprovalDecision.APPROVE
        assert result.approved_by == "human"
        assert result.notes is None

    @patch('builtins.input', side_effect=['R', 'Not ready for publication'])
    def test_reject_decision_with_notes(self, mock_input, approval_gate, sample_request):
        """User rejects content with notes"""
        result = approval_gate.request_approval(sample_request)

        assert result.decision == ApprovalDecision.REJECT
        assert result.approved_by == "human"
        assert result.notes == "Not ready for publication"

    @patch('builtins.input', side_effect=['M', 'Needs more examples'])
    def test_modify_decision_with_notes(self, mock_input, approval_gate, sample_request):
        """User requests modifications with notes"""
        result = approval_gate.request_approval(sample_request)

        assert result.decision == ApprovalDecision.MODIFY
        assert result.approved_by == "human"
        assert result.notes == "Needs more examples"

    @patch('builtins.input', side_effect=['X', 'Y', 'A'])  # Invalid, Invalid, Valid
    def test_invalid_input_retries(self, mock_input, approval_gate, sample_request):
        """Invalid input prompts retry until valid choice"""
        result = approval_gate.request_approval(sample_request)

        assert result.decision == ApprovalDecision.APPROVE
        assert mock_input.call_count == 3  # Two invalid, one valid

    @patch('builtins.input', side_effect=EOFError)
    def test_interrupt_defaults_to_reject(self, mock_input, approval_gate, sample_request):
        """Interrupt (Ctrl+C/Ctrl+D) defaults to REJECT"""
        result = approval_gate.request_approval(sample_request)

        assert result.decision == ApprovalDecision.REJECT


class TestApprovalLogging:
    """Test audit logging to JSONL"""

    @patch('builtins.input', return_value='A')
    def test_approval_logged_to_jsonl(self, mock_input, approval_gate, sample_request, temp_dir):
        """Approval decision is logged to JSONL file"""
        result = approval_gate.request_approval(sample_request)

        log_file = temp_dir / "content-approvals.jsonl"
        assert log_file.exists()

        # Read log entry
        with open(log_file, 'r') as f:
            log_entry = json.loads(f.read().strip())

        assert log_entry["content_id"] == "TEST-001"
        assert log_entry["decision"] == "approve"
        assert log_entry["seo_score"] == 75
        assert log_entry["approved_by"] == "human"
        assert "timestamp" in log_entry

    @patch('builtins.input', side_effect=['A', 'R'])
    def test_multiple_approvals_append_to_log(self, mock_input, approval_gate, sample_request, temp_dir):
        """Multiple approvals append to same JSONL file"""
        # First approval
        approval_gate.request_approval(sample_request)

        # Second approval
        sample_request.content_id = "TEST-002"
        approval_gate.request_approval(sample_request)

        log_file = temp_dir / "content-approvals.jsonl"

        # Should have 2 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 2

        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])

        assert entry1["content_id"] == "TEST-001"
        assert entry1["decision"] == "approve"
        assert entry2["content_id"] == "TEST-002"
        assert entry2["decision"] == "reject"


class TestApprovalHistory:
    """Test approval history retrieval"""

    def setup_log_entries(self, approval_gate, temp_dir):
        """Create sample log entries"""
        log_file = temp_dir / "content-approvals.jsonl"

        entries = [
            {
                "timestamp": "2026-01-22T10:00:00",
                "content_id": "TEST-001",
                "draft_path": "/test/draft1.md",
                "seo_score": 70,
                "decision": "approve",
                "approved_by": "human",
                "notes": None
            },
            {
                "timestamp": "2026-01-22T11:00:00",
                "content_id": "TEST-002",
                "draft_path": "/test/draft2.md",
                "seo_score": 45,
                "decision": "reject",
                "approved_by": "human",
                "notes": "SEO score too low"
            },
            {
                "timestamp": "2026-01-22T12:00:00",
                "content_id": "TEST-003",
                "draft_path": "/test/draft3.md",
                "seo_score": 85,
                "decision": "approve",
                "approved_by": "human",
                "notes": None
            }
        ]

        with open(log_file, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    def test_get_all_approval_history(self, approval_gate, temp_dir):
        """Get all approval history"""
        self.setup_log_entries(approval_gate, temp_dir)

        history = approval_gate.get_approval_history(limit=10)

        assert len(history) == 3
        # Most recent first
        assert history[0]["content_id"] == "TEST-003"
        assert history[1]["content_id"] == "TEST-002"
        assert history[2]["content_id"] == "TEST-001"

    def test_get_approval_history_filtered_by_content_id(self, approval_gate, temp_dir):
        """Filter approval history by content_id"""
        self.setup_log_entries(approval_gate, temp_dir)

        history = approval_gate.get_approval_history(content_id="TEST-002")

        assert len(history) == 1
        assert history[0]["content_id"] == "TEST-002"
        assert history[0]["decision"] == "reject"

    def test_get_approval_history_limited(self, approval_gate, temp_dir):
        """Limit number of approval history entries"""
        self.setup_log_entries(approval_gate, temp_dir)

        history = approval_gate.get_approval_history(limit=2)

        assert len(history) == 2
        assert history[0]["content_id"] == "TEST-003"
        assert history[1]["content_id"] == "TEST-002"

    def test_get_approval_history_empty_log(self, approval_gate):
        """Empty log returns empty history"""
        history = approval_gate.get_approval_history()

        assert history == []


class TestApprovalStatistics:
    """Test approval statistics"""

    def test_get_approval_stats(self, approval_gate, temp_dir):
        """Get approval statistics"""
        log_file = temp_dir / "content-approvals.jsonl"

        # Create sample log with mixed decisions
        entries = [
            {"decision": "approve"},
            {"decision": "approve"},
            {"decision": "approve"},
            {"decision": "reject"},
            {"decision": "reject"},
            {"decision": "modify"}
        ]

        with open(log_file, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        stats = approval_gate.get_approval_stats()

        assert stats["approved"] == 3
        assert stats["rejected"] == 2
        assert stats["modified"] == 1
        assert stats["total"] == 6

    def test_get_approval_stats_empty_log(self, approval_gate):
        """Empty log returns zero stats"""
        stats = approval_gate.get_approval_stats()

        assert stats["approved"] == 0
        assert stats["rejected"] == 0
        assert stats["modified"] == 0
        assert stats["total"] == 0


class TestApprovalGateDisplay:
    """Test approval gate display methods"""

    @patch('builtins.input', return_value='A')
    @patch('builtins.print')
    def test_displays_seo_score(self, mock_print, mock_input, approval_gate, sample_request):
        """Approval gate displays SEO score"""
        approval_gate.request_approval(sample_request)

        # Check that SEO score was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("SEO Score: 75/100" in call for call in print_calls)

    @patch('builtins.input', return_value='A')
    @patch('builtins.print')
    def test_displays_validation_issues(self, mock_print, mock_input, approval_gate, sample_request):
        """Approval gate displays validation issues"""
        approval_gate.request_approval(sample_request)

        # Check that issues were printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Keyword density too low" in call for call in print_calls)

    @patch('builtins.input', return_value='A')
    @patch('builtins.print')
    def test_displays_validation_warnings(self, mock_print, mock_input, approval_gate, sample_request):
        """Approval gate displays validation warnings"""
        approval_gate.request_approval(sample_request)

        # Check that warnings were printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Missing meta description" in call for call in print_calls)

    @patch('builtins.input', return_value='A')
    @patch('builtins.print')
    def test_displays_content_preview(self, mock_print, mock_input, approval_gate, sample_request):
        """Approval gate displays content preview"""
        approval_gate.request_approval(sample_request)

        # Check that draft content was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Test Article" in call for call in print_calls)
