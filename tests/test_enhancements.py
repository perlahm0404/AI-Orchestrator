"""
Test suite for Wiggum Enhancement implementations.

Tests:
1. Enhancement 1: KO CLI commands (already covered by existing CLI tests)
2. Enhancement 3: CodeQualityAgent Claude CLI integration
3. Enhancement 4: Completion signal templates
"""

import pytest
from pathlib import Path
from agents.codequality import CodeQualityAgent
from agents.base import AgentConfig
from orchestration.signal_templates import (
    infer_task_type,
    get_template,
    build_prompt_with_signal,
    TEMPLATES
)


class TestSignalTemplates:
    """Test completion signal template system."""

    def test_infer_task_type_bugfix(self):
        """Test inference of bugfix tasks."""
        test_cases = [
            "Fix authentication bug",
            "Resolve error in login",
            "Issue with payment processing",
            "Bug in credentialing wizard"
        ]
        for desc in test_cases:
            assert infer_task_type(desc) == "bugfix"

    def test_infer_task_type_codequality(self):
        """Test inference of code quality tasks."""
        test_cases = [
            "Improve code quality",
            "Lint fix src/utils",
            "Clean up unused imports"
        ]
        for desc in test_cases:
            assert infer_task_type(desc) == "codequality"

    def test_infer_task_type_refactor(self):
        """Test inference of refactor tasks."""
        test_cases = [
            "Refactor auth module",
            "Restructure user management",
            "Reorganize components"
        ]
        for desc in test_cases:
            assert infer_task_type(desc) == "refactor"

    def test_infer_task_type_feature(self):
        """Test inference of feature tasks."""
        test_cases = [
            "Add matching algorithm",
            "Implement new dashboard",
            "Build notification system",
            "Create user profile page"
        ]
        for desc in test_cases:
            assert infer_task_type(desc) == "feature"

    def test_infer_task_type_test(self):
        """Test inference of test tasks."""
        test_cases = [
            "Write tests for auth service",
            "Add test coverage for matching",
            "Create spec for wizard"
        ]
        for desc in test_cases:
            assert infer_task_type(desc) == "test"

    def test_get_template_valid(self):
        """Test retrieval of valid templates."""
        for task_type in ["bugfix", "codequality", "feature", "test", "refactor"]:
            template = get_template(task_type)
            assert template is not None
            assert template.promise
            assert template.prompt_suffix
            assert template.description

    def test_get_template_invalid(self):
        """Test retrieval of invalid template."""
        assert get_template("nonexistent") is None

    def test_build_prompt_with_signal(self):
        """Test prompt enhancement with signal."""
        base_prompt = "Fix the authentication bug"
        enhanced = build_prompt_with_signal(base_prompt, "bugfix")

        assert base_prompt in enhanced
        assert "<promise>BUGFIX_COMPLETE</promise>" in enhanced
        assert len(enhanced) > len(base_prompt)

    def test_build_prompt_invalid_type(self):
        """Test prompt with invalid task type returns unchanged."""
        base_prompt = "Fix the authentication bug"
        enhanced = build_prompt_with_signal(base_prompt, "nonexistent")

        assert enhanced == base_prompt

    def test_all_templates_have_required_fields(self):
        """Test all templates have required fields."""
        for task_type, template in TEMPLATES.items():
            assert template.promise, f"{task_type} missing promise"
            assert template.prompt_suffix, f"{task_type} missing prompt_suffix"
            assert template.description, f"{task_type} missing description"
            assert "<promise>" in template.prompt_suffix, f"{task_type} prompt_suffix missing <promise> tag"
            assert "</promise>" in template.prompt_suffix, f"{task_type} prompt_suffix missing </promise> tag"

    def test_promises_are_uppercase(self):
        """Test all promise strings are uppercase."""
        for task_type, template in TEMPLATES.items():
            assert template.promise.isupper(), f"{task_type} promise not uppercase: {template.promise}"

    def test_promises_end_with_complete(self):
        """Test all promise strings end with _COMPLETE."""
        for task_type, template in TEMPLATES.items():
            assert template.promise.endswith("_COMPLETE"), f"{task_type} promise doesn't end with _COMPLETE"


class TestCodeQualityAgentIntegration:
    """Test CodeQualityAgent Claude CLI integration."""

    def test_execute_has_claude_cli_integration(self):
        """Test that execute method imports ClaudeCliWrapper."""
        import inspect
        from agents.codequality import CodeQualityAgent

        source = inspect.getsource(CodeQualityAgent.execute)

        # Check for Claude CLI integration
        assert "ClaudeCliWrapper" in source
        assert "wrapper.execute_task" in source
        assert "quality_prompt" in source

    def test_execute_adds_quality_instructions(self):
        """Test that execute adds quality-specific instructions."""
        import inspect
        from agents.codequality import CodeQualityAgent

        source = inspect.getsource(CodeQualityAgent.execute)

        # Check for quality-specific instructions
        assert "Remove unused imports" in source or "unused imports" in source.lower()
        assert "Fix linting issues" in source or "linting" in source.lower()
        assert "type annotations" in source.lower()

    def test_execute_checks_completion_signal(self):
        """Test that execute checks for completion signal."""
        import inspect
        from agents.codequality import CodeQualityAgent

        source = inspect.getsource(CodeQualityAgent.execute)

        # Check for completion signal handling
        assert "check_completion_signal" in source
        assert "expected_completion_signal" in source

    def test_codequality_default_signal(self):
        """Test that CodeQuality tasks use CODEQUALITY_COMPLETE signal."""
        template = get_template("codequality")
        assert template.promise == "CODEQUALITY_COMPLETE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
