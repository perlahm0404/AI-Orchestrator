"""
Unit tests for Knowledge Object CLI commands.

Tests the ko subcommands: pending, approve, list, search, show
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from cli.commands.ko import (
    ko_pending_command,
    ko_approve_command,
    ko_list_command,
    ko_search_command,
    ko_show_command
)
from knowledge.service import create_draft, KO_DRAFTS_DIR, KO_APPROVED_DIR


@pytest.fixture
def temp_ko_dirs(monkeypatch):
    """Create temporary KO directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        drafts_dir = Path(tmpdir) / "drafts"
        approved_dir = Path(tmpdir) / "approved"
        drafts_dir.mkdir()
        approved_dir.mkdir()

        # Monkeypatch the directories
        import knowledge.service as service
        monkeypatch.setattr(service, 'KO_DRAFTS_DIR', drafts_dir)
        monkeypatch.setattr(service, 'KO_APPROVED_DIR', approved_dir)

        # Also patch in cli.commands.ko
        import cli.commands.ko as ko
        monkeypatch.setattr(ko, 'KO_DRAFTS_DIR', drafts_dir)
        monkeypatch.setattr(ko, 'KO_APPROVED_DIR', approved_dir)

        yield drafts_dir, approved_dir


class TestKOPending:
    """Test ko pending command."""

    def test_pending_lists_drafts(self, temp_ko_dirs, capsys):
        """Should list pending draft KOs."""
        # Create a draft KO
        ko = create_draft(
            project="test",
            title="Test KO",
            what_was_learned="Test learning",
            why_it_matters="Test importance",
            prevention_rule="Test prevention",
            tags=["test"]
        )

        # Execute command
        args = type('Args', (), {})()
        exit_code = ko_pending_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "PENDING KNOWLEDGE OBJECTS (1)" in captured.out
        assert ko.id in captured.out
        assert "Test KO" in captured.out

    def test_pending_empty(self, temp_ko_dirs, capsys):
        """Should show message when no pending KOs."""
        # Execute command with no drafts
        args = type('Args', (), {})()
        exit_code = ko_pending_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No pending Knowledge Objects" in captured.out


class TestKOApprove:
    """Test ko approve command."""

    def test_approve_moves_draft_to_approved(self, temp_ko_dirs, capsys):
        """Should approve draft and move to approved."""
        # Create draft
        ko = create_draft(
            project="test",
            title="Test KO",
            what_was_learned="Test learning",
            why_it_matters="Test importance",
            prevention_rule="Test prevention",
            tags=["test"]
        )

        # Execute approve command
        args = type('Args', (), {'ko_id': ko.id})()
        exit_code = ko_approve_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert f"Approved: {ko.id}" in captured.out
        assert "This knowledge will now be consulted by agents" in captured.out

        # Verify file moved
        drafts_dir, approved_dir = temp_ko_dirs
        assert not (drafts_dir / f"{ko.id}.md").exists()
        assert (approved_dir / f"{ko.id}.md").exists()

    def test_approve_nonexistent_ko(self, temp_ko_dirs, capsys):
        """Should show error for nonexistent KO."""
        # Execute approve with invalid ID
        args = type('Args', (), {'ko_id': 'KO-invalid-999'})()
        exit_code = ko_approve_command(args)

        # Verify
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Knowledge Object not found" in captured.out


class TestKOList:
    """Test ko list command."""

    def test_list_shows_approved_kos(self, temp_ko_dirs, capsys):
        """Should list approved KOs."""
        from knowledge.service import approve

        # Create and approve a KO
        ko = create_draft(
            project="test",
            title="Test KO",
            what_was_learned="Test learning",
            why_it_matters="Test importance",
            prevention_rule="Test prevention",
            tags=["test"]
        )
        approve(ko.id)

        # Execute list command
        args = type('Args', (), {'project': None})()
        exit_code = ko_list_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "APPROVED KNOWLEDGE OBJECTS (1)" in captured.out
        assert ko.id in captured.out
        assert "Test KO" in captured.out

    def test_list_filters_by_project(self, temp_ko_dirs, capsys):
        """Should filter by project."""
        from knowledge.service import approve

        # Create and approve KOs for different projects
        ko1 = create_draft(
            project="projectA",
            title="KO A",
            what_was_learned="Learning A",
            why_it_matters="Matters A",
            prevention_rule="Prevention A",
            tags=["a"]
        )
        ko2 = create_draft(
            project="projectB",
            title="KO B",
            what_was_learned="Learning B",
            why_it_matters="Matters B",
            prevention_rule="Prevention B",
            tags=["b"]
        )
        approve(ko1.id)
        approve(ko2.id)

        # Execute list with project filter
        args = type('Args', (), {'project': 'projectA'})()
        exit_code = ko_list_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "KO A" in captured.out
        assert "KO B" not in captured.out

    def test_list_empty(self, temp_ko_dirs, capsys):
        """Should show message when no approved KOs."""
        # Execute list with no approved KOs
        args = type('Args', (), {'project': None})()
        exit_code = ko_list_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No approved Knowledge Objects" in captured.out


class TestKOSearch:
    """Test ko search command."""

    def test_search_finds_by_tags(self, temp_ko_dirs, capsys):
        """Should search KOs by tags."""
        from knowledge.service import approve

        # Create and approve KO with specific tags
        ko = create_draft(
            project="test",
            title="Auth KO",
            what_was_learned="Auth learning",
            why_it_matters="Auth matters",
            prevention_rule="Auth prevention",
            tags=["auth", "typescript"]
        )
        approve(ko.id)

        # Execute search with project filter to match the created KO
        args = type('Args', (), {'tags': 'auth', 'project': 'test'})()
        exit_code = ko_search_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "SEARCH RESULTS (1 found)" in captured.out
        assert "Auth KO" in captured.out

    def test_search_multiple_tags(self, temp_ko_dirs, capsys):
        """Should search with multiple tags."""
        from knowledge.service import approve

        # Create KO with multiple tags
        ko = create_draft(
            project="test",
            title="Multi-tag KO",
            what_was_learned="Learning",
            why_it_matters="Matters",
            prevention_rule="Prevention",
            tags=["auth", "typescript", "jwt"]
        )
        approve(ko.id)

        # Execute search with multiple tags and project filter
        args = type('Args', (), {'tags': 'auth,typescript', 'project': 'test'})()
        exit_code = ko_search_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "SEARCH RESULTS (1 found)" in captured.out

    def test_search_no_results(self, temp_ko_dirs, capsys):
        """Should show message when no results found."""
        # Execute search with no matching KOs
        args = type('Args', (), {'tags': 'nonexistent', 'project': None})()
        exit_code = ko_search_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No Knowledge Objects found" in captured.out


class TestKOShow:
    """Test ko show command."""

    def test_show_displays_full_details(self, temp_ko_dirs, capsys):
        """Should display full KO details."""
        from knowledge.service import approve

        # Create and approve KO
        ko = create_draft(
            project="test",
            title="Detailed KO",
            what_was_learned="Detailed learning",
            why_it_matters="Detailed importance",
            prevention_rule="Detailed prevention",
            tags=["detail", "test"],
            detection_pattern="error.*pattern",
            file_patterns=["src/*.ts", "tests/*.test.ts"]
        )
        approve(ko.id)

        # Execute show
        args = type('Args', (), {'ko_id': ko.id})()
        exit_code = ko_show_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert f"KNOWLEDGE OBJECT: {ko.id}" in captured.out
        assert "Detailed KO" in captured.out
        assert "Detailed learning" in captured.out
        assert "Detailed importance" in captured.out
        assert "Detailed prevention" in captured.out
        assert "detail, test" in captured.out
        assert "error.*pattern" in captured.out
        assert "src/*.ts" in captured.out

    def test_show_works_for_drafts(self, temp_ko_dirs, capsys):
        """Should show draft KOs too."""
        # Create draft (not approved)
        ko = create_draft(
            project="test",
            title="Draft KO",
            what_was_learned="Draft learning",
            why_it_matters="Draft importance",
            prevention_rule="Draft prevention",
            tags=["draft"]
        )

        # Execute show
        args = type('Args', (), {'ko_id': ko.id})()
        exit_code = ko_show_command(args)

        # Verify
        assert exit_code == 0
        captured = capsys.readouterr()
        assert f"KNOWLEDGE OBJECT: {ko.id}" in captured.out
        assert "Draft KO" in captured.out
        assert "Status: draft" in captured.out

    def test_show_nonexistent_ko(self, temp_ko_dirs, capsys):
        """Should show error for nonexistent KO."""
        # Execute show with invalid ID
        args = type('Args', (), {'ko_id': 'KO-invalid-999'})()
        exit_code = ko_show_command(args)

        # Verify
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Knowledge Object not found" in captured.out
