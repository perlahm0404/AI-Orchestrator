"""
Tests for Work Queue Schema (Phase 1, Step 1.5)

Tests cover:
- Task creation and serialization
- Complexity category validation
- Value-based routing
- Agent type assignment
- Backward compatibility
- Schema validation

Author: Claude Code (Autonomous Implementation)
Date: 2026-02-07
"""

import pytest
from orchestration.work_queue_schema import (
    WorkQueueTaskMultiAgent,
    ComplexityCategory,
    EstimatedValueTier,
    AgentType,
    WorkQueueValidator,
    SIMPLE_BUG_TASK_TEMPLATE,
    FEATURE_TASK_TEMPLATE,
    COMPLEX_TASK_TEMPLATE,
    DEPLOYMENT_TASK_TEMPLATE,
)


class TestComplexityCategories:
    """Test complexity category enumeration."""

    def test_complexity_category_values(self):
        """Test that all complexity categories are defined."""
        assert ComplexityCategory.LOW.value == "low"
        assert ComplexityCategory.MEDIUM.value == "medium"
        assert ComplexityCategory.HIGH.value == "high"
        assert ComplexityCategory.CRITICAL.value == "critical"

    def test_complexity_category_from_string(self):
        """Test creating complexity category from string."""
        cat = ComplexityCategory("low")
        assert cat == ComplexityCategory.LOW


class TestEstimatedValueTiers:
    """Test estimated value tier enumeration."""

    def test_value_tiers_exist(self):
        """Test that all value tiers are defined."""
        assert EstimatedValueTier.TRIVIAL.value == "trivial"
        assert EstimatedValueTier.LOW.value == "low"
        assert EstimatedValueTier.MEDIUM.value == "medium"
        assert EstimatedValueTier.HIGH.value == "high"
        assert EstimatedValueTier.CRITICAL.value == "critical"


class TestAgentTypes:
    """Test agent type enumeration."""

    def test_all_agent_types_defined(self):
        """Test that all specialist agent types exist."""
        assert AgentType.BUGFIX.value == "bugfix"
        assert AgentType.FEATUREBUILDER.value == "featurebuilder"
        assert AgentType.TESTWRITER.value == "testwriter"
        assert AgentType.CODEQUALITY.value == "codequality"
        assert AgentType.ADVISOR.value == "advisor"
        assert AgentType.DEPLOYMENT.value == "deployment"
        assert AgentType.MIGRATION.value == "migration"


class TestWorkQueueTaskCreation:
    """Test work queue task creation and initialization."""

    def test_create_minimal_task(self):
        """Test creating task with required fields only."""
        task = WorkQueueTaskMultiAgent(
            id="TASK-001",
            description="Fix bug",
            status="pending",
            priority="P1",
            type="bug",
        )

        assert task.id == "TASK-001"
        assert task.description == "Fix bug"
        assert task.status == "pending"
        assert task.complexity_category == ComplexityCategory.MEDIUM
        assert task.estimated_value_usd == 50.0

    def test_create_task_with_complexity(self):
        """Test creating task with complexity category."""
        task = WorkQueueTaskMultiAgent(
            id="TASK-002",
            description="Refactor service",
            status="pending",
            priority="P0",
            type="refactor",
            complexity_category=ComplexityCategory.HIGH,
            estimated_value_usd=200.0,
        )

        assert task.complexity_category == ComplexityCategory.HIGH
        assert task.estimated_value_usd == 200.0

    def test_create_task_with_preferred_agents(self):
        """Test creating task with preferred agents."""
        task = WorkQueueTaskMultiAgent(
            id="TASK-003",
            description="Add feature",
            status="pending",
            priority="P2",
            type="feature",
            preferred_agents=[AgentType.FEATUREBUILDER, AgentType.TESTWRITER],
        )

        assert len(task.preferred_agents) == 2
        assert AgentType.FEATUREBUILDER in task.preferred_agents


class TestTaskSerialization:
    """Test task serialization and deserialization."""

    def test_task_to_dict(self):
        """Test converting task to dictionary."""
        task = WorkQueueTaskMultiAgent(
            id="TASK-004",
            description="Test task",
            status="in_progress",
            priority="P1",
            type="test",
            complexity_category=ComplexityCategory.MEDIUM,
            estimated_value_usd=75.0,
            preferred_agents=[AgentType.TESTWRITER],
        )

        task_dict = task.to_dict()

        assert task_dict["id"] == "TASK-004"
        assert task_dict["complexity_category"] == "medium"
        assert task_dict["estimated_value_usd"] == 75.0
        assert task_dict["preferred_agents"] == ["testwriter"]

    def test_task_from_dict(self):
        """Test creating task from dictionary."""
        task_dict = {
            "id": "TASK-005",
            "description": "Deploy to prod",
            "status": "pending",
            "priority": "P0",
            "type": "deploy",
            "complexity_category": "critical",
            "estimated_value_usd": 500.0,
            "preferred_agents": ["deployment", "advisor"],
        }

        task = WorkQueueTaskMultiAgent.from_dict(task_dict)

        assert task.id == "TASK-005"
        assert task.complexity_category == ComplexityCategory.CRITICAL
        assert len(task.preferred_agents) == 2

    def test_roundtrip_serialization(self):
        """Test roundtrip serialization and deserialization."""
        original = WorkQueueTaskMultiAgent(
            id="TASK-006",
            description="Round-trip test",
            status="completed",
            priority="P2",
            type="bug",
            complexity_category=ComplexityCategory.LOW,
            estimated_value_usd=25.0,
            agent_type_override=AgentType.BUGFIX,
            use_multi_agent=False,
        )

        serialized = original.to_dict()
        restored = WorkQueueTaskMultiAgent.from_dict(serialized)

        assert restored.id == original.id
        assert restored.complexity_category == original.complexity_category
        assert restored.estimated_value_usd == original.estimated_value_usd
        assert restored.agent_type_override == original.agent_type_override


class TestWorkQueueValidation:
    """Test work queue task validation."""

    def test_validate_valid_task(self):
        """Test validation of valid task."""
        task_dict = {
            "id": "TASK-007",
            "description": "Valid task",
            "status": "pending",
            "priority": "P1",
            "type": "feature",
        }

        is_valid, error = WorkQueueValidator.validate_task(task_dict)

        assert is_valid is True
        assert error is None

    def test_validate_missing_required_field(self):
        """Test validation catches missing required field."""
        task_dict = {
            "id": "TASK-008",
            "description": "Missing status",
            # status missing
            "priority": "P1",
            "type": "bug",
        }

        is_valid, error = WorkQueueValidator.validate_task(task_dict)

        assert is_valid is False
        assert "status" in error.lower()

    def test_validate_invalid_status(self):
        """Test validation catches invalid status."""
        task_dict = {
            "id": "TASK-009",
            "description": "Invalid status",
            "status": "invalid_status",
            "priority": "P1",
            "type": "bug",
        }

        is_valid, error = WorkQueueValidator.validate_task(task_dict)

        assert is_valid is False
        assert "status" in error.lower()

    def test_validate_invalid_priority(self):
        """Test validation catches invalid priority."""
        task_dict = {
            "id": "TASK-010",
            "description": "Invalid priority",
            "status": "pending",
            "priority": "INVALID",
            "type": "bug",
        }

        is_valid, error = WorkQueueValidator.validate_task(task_dict)

        assert is_valid is False
        assert "priority" in error.lower()

    def test_validate_invalid_type(self):
        """Test validation catches invalid type."""
        task_dict = {
            "id": "TASK-011",
            "description": "Invalid type",
            "status": "pending",
            "priority": "P1",
            "type": "invalid_type",
        }

        is_valid, error = WorkQueueValidator.validate_task(task_dict)

        assert is_valid is False
        assert "type" in error.lower()

    def test_validate_invalid_complexity(self):
        """Test validation catches invalid complexity."""
        task_dict = {
            "id": "TASK-012",
            "description": "Invalid complexity",
            "status": "pending",
            "priority": "P1",
            "type": "bug",
            "complexity_category": "super_high",
        }

        is_valid, error = WorkQueueValidator.validate_task(task_dict)

        assert is_valid is False
        assert "complexity" in error.lower()

    def test_validate_invalid_value(self):
        """Test validation catches invalid estimated value."""
        task_dict = {
            "id": "TASK-013",
            "description": "Invalid value",
            "status": "pending",
            "priority": "P1",
            "type": "bug",
            "estimated_value_usd": "not_a_number",
        }

        is_valid, error = WorkQueueValidator.validate_task(task_dict)

        assert is_valid is False
        assert "estimated_value_usd" in error.lower()

    def test_validate_invalid_agent_type(self):
        """Test validation catches invalid agent type."""
        task_dict = {
            "id": "TASK-014",
            "description": "Invalid agent",
            "status": "pending",
            "priority": "P1",
            "type": "bug",
            "preferred_agents": ["invalid_agent"],
        }

        is_valid, error = WorkQueueValidator.validate_task(task_dict)

        assert is_valid is False
        assert "agent" in error.lower()


class TestTaskTemplates:
    """Test predefined task templates."""

    def test_simple_bug_template(self):
        """Test simple bug task template."""
        template = SIMPLE_BUG_TASK_TEMPLATE

        assert template["complexity_category"] == "low"
        assert template["estimated_value_usd"] == 25.0
        assert template["use_multi_agent"] is False
        assert "bugfix" in template["preferred_agents"]

    def test_feature_template(self):
        """Test feature task template."""
        template = FEATURE_TASK_TEMPLATE

        assert template["complexity_category"] == "medium"
        assert template["estimated_value_usd"] == 100.0
        assert template["use_multi_agent"] is True
        assert "featurebuilder" in template["preferred_agents"]
        assert "testwriter" in template["preferred_agents"]

    def test_complex_task_template(self):
        """Test complex task template."""
        template = COMPLEX_TASK_TEMPLATE

        assert template["complexity_category"] == "high"
        assert template["estimated_value_usd"] == 200.0
        assert template["use_multi_agent"] is True
        assert len(template["preferred_agents"]) >= 3

    def test_deployment_template(self):
        """Test deployment task template."""
        template = DEPLOYMENT_TASK_TEMPLATE

        assert template["complexity_category"] == "critical"
        assert template["estimated_value_usd"] == 500.0
        assert template["use_multi_agent"] is True
        assert "deployment" in template["preferred_agents"]


class TestBackwardCompatibility:
    """Test backward compatibility with existing work queue format."""

    def test_create_from_legacy_task(self):
        """Test creating task from legacy format (no multi-agent fields)."""
        legacy_task = {
            "id": "LEGACY-001",
            "description": "Legacy task",
            "status": "completed",
            "priority": "P1",
            "type": "bug",
            "passes": True,
            "attempts": 2,
        }

        task = WorkQueueTaskMultiAgent.from_dict(legacy_task)

        assert task.id == "LEGACY-001"
        assert task.passes is True
        assert task.attempts == 2
        # Multi-agent fields should have defaults
        assert task.complexity_category == ComplexityCategory.MEDIUM
        assert task.estimated_value_usd == 50.0

    def test_legacy_task_to_dict_preserves_fields(self):
        """Test that converting legacy task preserves all fields."""
        task = WorkQueueTaskMultiAgent(
            id="LEGACY-002",
            description="Legacy task",
            status="in_progress",
            priority="P2",
            type="feature",
            passes=False,
            attempts=3,
            branch="feature/test",
            created_at="2026-01-01T00:00:00Z",
        )

        task_dict = task.to_dict()

        assert task_dict["passes"] is False
        assert task_dict["attempts"] == 3
        assert task_dict["branch"] == "feature/test"
        assert task_dict["created_at"] == "2026-01-01T00:00:00Z"


class TestRoutingDecisions:
    """Test multi-agent routing decision fields."""

    def test_routing_override(self):
        """Test setting agent type override."""
        task = WorkQueueTaskMultiAgent(
            id="ROUTE-001",
            description="Test routing",
            status="pending",
            priority="P1",
            type="bug",
            agent_type_override=AgentType.BUGFIX,
            routing_reason="Explicitly assigned to BugFix agent",
        )

        assert task.agent_type_override == AgentType.BUGFIX
        assert "explicitly" in task.routing_reason.lower()

    def test_multi_agent_decision(self):
        """Test multi-agent routing decision."""
        task = WorkQueueTaskMultiAgent(
            id="ROUTE-002",
            description="Multi-agent task",
            status="pending",
            priority="P0",
            type="refactor",
            complexity_category=ComplexityCategory.HIGH,
            estimated_value_usd=300.0,
            use_multi_agent=True,
            routing_reason="High complexity and value justify multi-agent",
        )

        assert task.use_multi_agent is True
        assert task.complexity_category == ComplexityCategory.HIGH
