"""Tests for icebox (parking lot) system."""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from parking.icebox import IceboxIdea, generate_idea_id


class TestIceboxIdea:
    """Tests for IceboxIdea dataclass."""

    def test_create_idea_basic(self):
        """Test basic idea creation."""
        idea = IceboxIdea(
            id="IDEA-20260207-1430-001",
            title="Test Idea",
            description="This is a test idea",
            project="ai-orchestrator",
        )

        assert idea.id == "IDEA-20260207-1430-001"
        assert idea.title == "Test Idea"
        assert idea.description == "This is a test idea"
        assert idea.project == "ai-orchestrator"
        assert idea.status == "raw"
        assert idea.priority == 2  # default
        assert idea.effort_estimate == "M"  # default

    def test_create_idea_with_all_fields(self):
        """Test idea creation with all fields."""
        idea = IceboxIdea(
            id="IDEA-20260207-1430-001",
            title="Full Idea",
            description="Complete description",
            project="credentialmate",
            category="feature",
            priority=0,
            effort_estimate="XL",
            tags=["auth", "security"],
            dependencies=["FEAT-001"],
            source="agent",
            discovered_by="app-advisor",
        )

        assert idea.category == "feature"
        assert idea.priority == 0
        assert idea.effort_estimate == "XL"
        assert idea.tags == ["auth", "security"]
        assert idea.dependencies == ["FEAT-001"]
        assert idea.source == "agent"
        assert idea.discovered_by == "app-advisor"

    def test_fingerprint_generation(self):
        """Test that fingerprint is auto-generated."""
        idea = IceboxIdea(
            id="IDEA-001",
            title="Test Idea",
            description="Description",
            project="test",
        )

        assert idea.fingerprint != ""
        assert len(idea.fingerprint) == 16  # SHA256 truncated to 16 chars

    def test_fingerprint_deduplication(self):
        """Test that similar ideas get same fingerprint."""
        idea1 = IceboxIdea(
            id="IDEA-001",
            title="Test Idea",
            description="Description here",
            project="test",
        )
        idea2 = IceboxIdea(
            id="IDEA-002",
            title="Test Idea",  # Same title
            description="Description here",  # Same description
            project="test",
        )

        assert idea1.fingerprint == idea2.fingerprint

    def test_fingerprint_different_for_different_ideas(self):
        """Test that different ideas get different fingerprints."""
        idea1 = IceboxIdea(
            id="IDEA-001",
            title="Test Idea",
            description="Description",
            project="test",
        )
        idea2 = IceboxIdea(
            id="IDEA-002",
            title="Different Idea",  # Different title
            description="Description",
            project="test",
        )

        assert idea1.fingerprint != idea2.fingerprint

    def test_to_dict(self):
        """Test conversion to dictionary."""
        idea = IceboxIdea(
            id="IDEA-001",
            title="Test",
            description="Desc",
            project="test",
        )

        data = idea.to_dict()

        assert data["id"] == "IDEA-001"
        assert data["title"] == "Test"
        assert data["description"] == "Desc"
        assert data["project"] == "test"
        assert "fingerprint" in data

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "IDEA-001",
            "title": "Test",
            "description": "Desc",
            "project": "test",
            "category": "feature",
            "priority": 1,
        }

        idea = IceboxIdea.from_dict(data)

        assert idea.id == "IDEA-001"
        assert idea.title == "Test"
        assert idea.category == "feature"
        assert idea.priority == 1

    def test_from_dict_with_unknown_fields(self):
        """Test that unknown fields are preserved in metadata."""
        data = {
            "id": "IDEA-001",
            "title": "Test",
            "description": "Desc",
            "project": "test",
            "custom_field": "custom_value",
        }

        idea = IceboxIdea.from_dict(data)

        assert idea.metadata.get("custom_field") == "custom_value"

    def test_to_markdown(self):
        """Test markdown generation."""
        idea = IceboxIdea(
            id="IDEA-001",
            title="Test Idea",
            description="This is the description",
            project="test",
            tags=["tag1", "tag2"],
        )

        md = idea.to_markdown()

        assert "---" in md  # YAML frontmatter
        assert "id: IDEA-001" in md
        assert "title: Test Idea" in md
        assert "# Test Idea" in md
        assert "## Description" in md
        assert "This is the description" in md

    def test_from_markdown(self):
        """Test parsing markdown."""
        md = """---
id: IDEA-001
title: Test Idea
category: feature
priority: 1
effort_estimate: L
dependencies: []
tags:
  - tag1
  - tag2
project: test
source: human
discovered_by: cli
created_at: 2026-02-07T14:30:00
last_reviewed: null
status: raw
promoted_to: null
archived_reason: null
fingerprint: abc123
---

# Test Idea

## Description

This is the full description.
"""

        idea = IceboxIdea.from_markdown(md)

        assert idea.id == "IDEA-001"
        assert idea.title == "Test Idea"
        assert idea.category == "feature"
        assert idea.priority == 1
        assert idea.effort_estimate == "L"
        assert idea.tags == ["tag1", "tag2"]
        assert idea.description == "This is the full description."


class TestGenerateIdeaId:
    """Tests for ID generation."""

    def test_generate_idea_id_format(self):
        """Test ID format."""
        idea_id = generate_idea_id("test", 1)

        assert idea_id.startswith("IDEA-")
        parts = idea_id.split("-")
        assert len(parts) == 4
        assert parts[0] == "IDEA"
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 4  # HHMM
        assert parts[3] == "001"  # sequence

    def test_generate_idea_id_sequence(self):
        """Test sequence numbering."""
        id1 = generate_idea_id("test", 1)
        id2 = generate_idea_id("test", 2)
        id3 = generate_idea_id("test", 10)

        assert id1.endswith("-001")
        assert id2.endswith("-002")
        assert id3.endswith("-010")


# Tests for service layer require mocking file I/O
class TestIceboxService:
    """Tests for icebox service functions."""

    @pytest.fixture
    def icebox_dir(self, tmp_path):
        """Create temporary icebox directory."""
        icebox = tmp_path / ".aibrain" / "icebox"
        archive = icebox / "archive"
        icebox.mkdir(parents=True)
        archive.mkdir()
        return icebox

    def test_capture_idea(self, icebox_dir, monkeypatch):
        """Test capturing a new idea."""
        # Patch the ICEBOX_DIR
        import parking.service as service
        monkeypatch.setattr(service, "ICEBOX_DIR", icebox_dir)
        monkeypatch.setattr(service, "ARCHIVE_DIR", icebox_dir / "archive")

        from parking.service import capture_idea

        idea = capture_idea(
            title="Test Idea",
            description="Test description",
            project="test",
            category="feature",
        )

        assert idea is not None
        assert idea.title == "Test Idea"
        assert idea.project == "test"
        assert idea.category == "feature"

        # Check file was created
        idea_files = list(icebox_dir.glob("IDEA-*.md"))
        assert len(idea_files) == 1

    def test_capture_idea_dedup(self, icebox_dir, monkeypatch):
        """Test that duplicate ideas are rejected."""
        import parking.service as service
        monkeypatch.setattr(service, "ICEBOX_DIR", icebox_dir)
        monkeypatch.setattr(service, "ARCHIVE_DIR", icebox_dir / "archive")

        from parking.service import capture_idea

        idea1 = capture_idea(
            title="Test Idea",
            description="Description",
            project="test",
        )
        assert idea1 is not None

        idea2 = capture_idea(
            title="Test Idea",  # Same title
            description="Description",  # Same description
            project="test",
        )
        assert idea2 is None  # Duplicate rejected

    def test_list_ideas(self, icebox_dir, monkeypatch):
        """Test listing ideas."""
        import parking.service as service
        monkeypatch.setattr(service, "ICEBOX_DIR", icebox_dir)
        monkeypatch.setattr(service, "ARCHIVE_DIR", icebox_dir / "archive")

        from parking.service import capture_idea, list_ideas

        # Create some ideas
        capture_idea(title="Idea 1", description="D1", project="test")
        capture_idea(title="Idea 2", description="D2", project="test")
        capture_idea(title="Idea 3", description="D3", project="other")

        # List all
        all_ideas = list_ideas()
        assert len(all_ideas) == 3

        # Filter by project
        test_ideas = list_ideas(project="test")
        assert len(test_ideas) == 2

    def test_get_idea(self, icebox_dir, monkeypatch):
        """Test getting a specific idea."""
        import parking.service as service
        monkeypatch.setattr(service, "ICEBOX_DIR", icebox_dir)
        monkeypatch.setattr(service, "ARCHIVE_DIR", icebox_dir / "archive")

        from parking.service import capture_idea, get_idea

        created = capture_idea(
            title="Test Idea",
            description="Description",
            project="test",
        )

        retrieved = get_idea(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == created.title

    def test_archive_idea(self, icebox_dir, monkeypatch):
        """Test archiving an idea."""
        import parking.service as service
        monkeypatch.setattr(service, "ICEBOX_DIR", icebox_dir)
        monkeypatch.setattr(service, "ARCHIVE_DIR", icebox_dir / "archive")

        from parking.service import capture_idea, archive_idea, get_idea

        idea = capture_idea(
            title="Test Idea",
            description="Description",
            project="test",
        )

        result = archive_idea(idea.id, "No longer needed")
        assert result is True

        # Check idea is now in archive
        archived = get_idea(idea.id)
        assert archived is not None
        assert archived.status == "archived"
        assert archived.archived_reason == "No longer needed"

        # Check file moved
        assert not (icebox_dir / f"{idea.id}.md").exists()
        assert (icebox_dir / "archive" / f"{idea.id}.md").exists()

    def test_get_stale_ideas(self, icebox_dir, monkeypatch):
        """Test finding stale ideas."""
        import parking.service as service
        monkeypatch.setattr(service, "ICEBOX_DIR", icebox_dir)
        monkeypatch.setattr(service, "ARCHIVE_DIR", icebox_dir / "archive")

        from parking.service import get_stale_ideas
        from parking.icebox import IceboxIdea

        # Create an old idea manually
        old_date = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        old_idea = IceboxIdea(
            id="IDEA-OLD-001",
            title="Old Idea",
            description="Old description",
            project="test",
            created_at=old_date,
        )
        (icebox_dir / "IDEA-OLD-001.md").write_text(old_idea.to_markdown())

        # Create a recent idea
        recent_idea = IceboxIdea(
            id="IDEA-NEW-001",
            title="New Idea",
            description="New description",
            project="test",
        )
        (icebox_dir / "IDEA-NEW-001.md").write_text(recent_idea.to_markdown())

        stale = get_stale_ideas(days=30)

        assert len(stale) == 1
        assert stale[0].id == "IDEA-OLD-001"


class TestWorkQueueIntegration:
    """Tests for work queue integration."""

    def test_parked_status_in_task_status(self):
        """Test that 'parked' is a valid TaskStatus."""
        from tasks.work_queue import TaskStatus, Task

        # This should not raise
        task = Task(
            id="TEST-001",
            description="Test",
            file="test.py",
            status="parked",
        )
        assert task.status == "parked"

    def test_work_queue_get_parked(self):
        """Test getting parked tasks."""
        from tasks.work_queue import WorkQueue, Task

        queue = WorkQueue(
            project="test",
            features=[
                Task(id="T1", description="D1", file="a.py", status="pending"),
                Task(id="T2", description="D2", file="b.py", status="parked"),
                Task(id="T3", description="D3", file="c.py", status="parked"),
                Task(id="T4", description="D4", file="d.py", status="complete"),
            ]
        )

        parked = queue.get_parked()

        assert len(parked) == 2
        assert all(t.status == "parked" for t in parked)

    def test_work_queue_park_task(self):
        """Test parking a task."""
        from tasks.work_queue import WorkQueue, Task

        queue = WorkQueue(
            project="test",
            features=[
                Task(id="T1", description="D1", file="a.py", status="pending"),
            ]
        )

        queue.park_task("T1", "Waiting for dependency")

        assert queue.features[0].status == "parked"
        assert queue.features[0].error == "Waiting for dependency"

    def test_work_queue_unpark_task(self):
        """Test unparking a task."""
        from tasks.work_queue import WorkQueue, Task

        queue = WorkQueue(
            project="test",
            features=[
                Task(id="T1", description="D1", file="a.py", status="parked", error="Waiting"),
            ]
        )

        queue.unpark_task("T1")

        assert queue.features[0].status == "pending"
        assert queue.features[0].error is None

    def test_work_queue_stats_include_parked(self):
        """Test that stats include parked count."""
        from tasks.work_queue import WorkQueue, Task

        queue = WorkQueue(
            project="test",
            features=[
                Task(id="T1", description="D1", file="a.py", status="pending"),
                Task(id="T2", description="D2", file="b.py", status="parked"),
                Task(id="T3", description="D3", file="c.py", status="parked"),
            ]
        )

        stats = queue.get_stats()

        assert stats["parked"] == 2
        assert stats["pending"] == 1
        assert stats["total"] == 3
