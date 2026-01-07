"""
Tests for Agent Factory

Verifies that create_agent() correctly:
1. Infers agent type from task ID
2. Creates appropriate agent with AgentConfig
3. Sets correct iteration budgets
4. Sets correct completion promises
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from agents.factory import create_agent, infer_agent_type
from agents.bugfix import BugFixAgent
from agents.codequality import CodeQualityAgent
from agents.base import AgentConfig


class TestInferAgentType:
    """Test agent type inference from task IDs"""

    def test_infer_bugfix_from_bug_prefix(self):
        assert infer_agent_type("BUG-001") == "bugfix"
        assert infer_agent_type("BUG-APT-001") == "bugfix"
        assert infer_agent_type("BUGFIX-123") == "bugfix"

    def test_infer_bugfix_from_fix_prefix(self):
        assert infer_agent_type("FIX-001") == "bugfix"
        assert infer_agent_type("FIX-AUTH-001") == "bugfix"

    def test_infer_codequality_from_quality_prefix(self):
        assert infer_agent_type("QUALITY-001") == "codequality"
        assert infer_agent_type("QUALITY-LINT-001") == "codequality"

    def test_infer_codequality_from_refactor_prefix(self):
        assert infer_agent_type("REFACTOR-001") == "codequality"
        assert infer_agent_type("CODE-001") == "codequality"

    def test_infer_feature_from_feature_prefix(self):
        assert infer_agent_type("FEATURE-001") == "feature"
        assert infer_agent_type("FEATURE-AUTH-001") == "feature"
        assert infer_agent_type("FEAT-001") == "feature"

    def test_infer_test_from_test_prefix(self):
        assert infer_agent_type("TEST-001") == "test"
        assert infer_agent_type("TEST-UNIT-001") == "test"
        assert infer_agent_type("TESTS-001") == "test"

    def test_default_to_bugfix_for_unknown_prefix(self):
        assert infer_agent_type("UNKNOWN-001") == "bugfix"
        assert infer_agent_type("XYZ-123") == "bugfix"

    def test_case_insensitive_matching(self):
        assert infer_agent_type("bug-001") == "bugfix"
        assert infer_agent_type("Bug-001") == "bugfix"
        assert infer_agent_type("FEATURE-001") == "feature"


class TestCreateAgent:
    """Test agent creation with proper configuration"""

    def test_create_bugfix_agent(self):
        """Test creating BugFixAgent with correct config"""
        agent = create_agent(task_type="bugfix", project_name="karematch")

        assert isinstance(agent, BugFixAgent)
        assert agent.config is not None
        assert agent.config.expected_completion_signal == "BUGFIX_COMPLETE"
        assert agent.config.max_iterations == 15
        assert agent.config.agent_name == "bugfix"

    def test_create_codequality_agent(self):
        """Test creating CodeQualityAgent with correct config"""
        agent = create_agent(task_type="codequality", project_name="karematch")

        assert isinstance(agent, CodeQualityAgent)
        assert agent.config is not None
        assert agent.config.expected_completion_signal == "CODEQUALITY_COMPLETE"
        assert agent.config.max_iterations == 20
        assert agent.config.agent_name == "codequality"

    def test_agent_has_project_name(self):
        """Test that agent config has project name"""
        agent = create_agent(task_type="bugfix", project_name="karematch")

        assert agent.config.project_name == "karematch"

    def test_custom_max_iterations(self):
        """Test overriding default max_iterations"""
        agent = create_agent(
            task_type="bugfix",
            project_name="karematch",
            max_iterations=25  # Override default 15
        )

        assert agent.config.max_iterations == 25

    def test_custom_completion_signal(self):
        """Test overriding default completion signal"""
        agent = create_agent(
            task_type="bugfix",
            project_name="karematch",
            completion_promise="CUSTOM_DONE"
        )

        assert agent.config.expected_completion_signal == "CUSTOM_DONE"

    def test_different_task_types_get_different_budgets(self):
        """Test that different agent types have different iteration budgets"""
        bugfix_agent = create_agent(task_type="bugfix", project_name="karematch")
        quality_agent = create_agent(task_type="codequality", project_name="karematch")

        assert bugfix_agent.config.max_iterations == 15
        assert quality_agent.config.max_iterations == 20
        assert bugfix_agent.config.max_iterations != quality_agent.config.max_iterations

    def test_different_task_types_get_different_promises(self):
        """Test that different agent types have different completion signals"""
        bugfix_agent = create_agent(task_type="bugfix", project_name="karematch")
        quality_agent = create_agent(task_type="codequality", project_name="karematch")

        assert bugfix_agent.config.expected_completion_signal == "BUGFIX_COMPLETE"
        assert quality_agent.config.expected_completion_signal == "CODEQUALITY_COMPLETE"

    def test_supports_credentialmate_project(self):
        """Test creating agent for credentialmate project"""
        agent = create_agent(task_type="bugfix", project_name="credentialmate")

        assert agent.config.project_name == "credentialmate"
        # Adapter is internal, just verify agent is created successfully
        assert isinstance(agent, BugFixAgent)


class TestAgentTypeAndConfigMapping:
    """Test that agent types map to correct configs"""

    def test_bugfix_config(self):
        """BugFix agent should have correct defaults"""
        agent = create_agent("bugfix", "karematch")
        assert agent.config.max_iterations == 15
        assert agent.config.expected_completion_signal == "BUGFIX_COMPLETE"

    def test_codequality_config(self):
        """CodeQuality agent should have correct defaults"""
        agent = create_agent("codequality", "karematch")
        assert agent.config.max_iterations == 20
        assert agent.config.expected_completion_signal == "CODEQUALITY_COMPLETE"
