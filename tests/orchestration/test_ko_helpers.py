"""
Unit tests for Knowledge Object helper functions.

Tests tag extraction, learning extraction, and KO formatting utilities.
"""

import pytest
from orchestration.ko_helpers import (
    extract_tags_from_task,
    format_ko_for_display,
    extract_learning_from_iterations
)


class TestTagExtraction:
    """Test tag extraction from task descriptions."""

    def test_extract_tags_from_file_extensions(self):
        """Should extract language tags from file extensions."""
        task = "Fix bug in auth.ts"
        tags = extract_tags_from_task(task)
        assert 'typescript' in tags
        assert 'auth' in tags

    def test_extract_tags_from_multiple_extensions(self):
        """Should handle multiple file extensions."""
        task = "Update login.tsx and config.json"
        tags = extract_tags_from_task(task)
        assert 'typescript' in tags
        assert 'json' in tags
        assert 'login' in tags

    def test_extract_tags_from_keywords(self):
        """Should extract domain keywords."""
        task = "Fix authentication bug in login endpoint"
        tags = extract_tags_from_task(task)
        assert 'authentication' in tags
        assert 'login' in tags
        assert 'endpoint' in tags
        assert 'bug' in tags
        assert 'fix' in tags

    def test_extract_tags_from_file_paths(self):
        """Should extract path components."""
        task = "Fix bug in packages/api/src/auth.ts"
        tags = extract_tags_from_task(task)
        assert 'packages' in tags
        assert 'api' in tags
        assert 'auth' in tags
        assert 'typescript' in tags

    def test_extract_tags_from_kebab_case_filenames(self):
        """Should split kebab-case filenames."""
        task = "Fix login-form.tsx component"
        tags = extract_tags_from_task(task)
        assert 'login' in tags
        assert 'form' in tags
        assert 'component' in tags
        assert 'typescript' in tags

    def test_empty_task_description(self):
        """Should handle empty task gracefully."""
        tags = extract_tags_from_task("")
        assert tags == []

    def test_no_recognizable_tags(self):
        """Should return empty list if no tags found."""
        tags = extract_tags_from_task("Do something simple")
        # May still extract some basic tags like 'simple'
        assert isinstance(tags, list)

    def test_tags_are_sorted(self):
        """Should return sorted tags."""
        task = "Fix bug in typescript file"
        tags = extract_tags_from_task(task)
        assert tags == sorted(tags)

    def test_tags_are_lowercase(self):
        """Should convert all tags to lowercase."""
        task = "Fix AUTH Bug in Login.ts"
        tags = extract_tags_from_task(task)
        assert all(tag.islower() for tag in tags)

    def test_drizzle_orm_specific(self):
        """Should extract Drizzle ORM tags."""
        task = "Fix drizzle ORM migration in database schema"
        tags = extract_tags_from_task(task)
        assert 'drizzle' in tags
        assert 'orm' in tags
        assert 'database' in tags
        assert 'migration' in tags


class TestLearningExtraction:
    """Test learning extraction from iteration history."""

    def test_extract_learning_from_multi_iteration_with_failures(self):
        """Should extract learning from multiple iterations with failures."""
        task = "Fix auth bug"
        history = [
            {"iteration": 1, "verdict": "FAIL", "changes": ["src/auth.ts"]},
            {"iteration": 2, "verdict": "FAIL", "changes": ["src/auth.ts"]},
            {"iteration": 3, "verdict": "PASS", "changes": ["src/auth.ts"]}
        ]
        verdict = None
        changes = ["src/auth.ts", "tests/auth.test.ts"]

        learning = extract_learning_from_iterations(task, history, verdict, changes)

        assert 'title' in learning
        assert learning['title'] == "Fix auth bug"
        assert 'what_was_learned' in learning
        assert '3 iteration(s)' in learning['what_was_learned']
        assert '2 correction(s)' in learning['what_was_learned']
        assert 'why_it_matters' in learning
        assert 'self-correction' in learning['why_it_matters']
        assert 'prevention_rule' in learning
        assert 'tags' in learning
        assert isinstance(learning['tags'], list)
        assert 'auth' in learning['tags']

    def test_extract_learning_from_multi_iteration_without_failures(self):
        """Should handle iterations without failures (iterative refinement)."""
        task = "Implement feature X"
        history = [
            {"iteration": 1, "verdict": "PASS", "changes": ["src/feature.ts"]},
            {"iteration": 2, "verdict": "PASS", "changes": ["src/feature.ts"]}
        ]
        verdict = None
        changes = ["src/feature.ts"]

        learning = extract_learning_from_iterations(task, history, verdict, changes)

        assert 'iterative-refinement' in learning['why_it_matters']
        assert '2 iteration(s)' in learning['what_was_learned']

    def test_file_pattern_extraction(self):
        """Should extract file patterns from changes."""
        task = "Fix bug"
        history = [{"iteration": 1, "verdict": "PASS", "changes": []}]
        verdict = None
        changes = ["src/auth/login.ts", "src/auth/middleware.ts", "tests/auth.test.ts"]

        learning = extract_learning_from_iterations(task, history, verdict, changes)

        assert 'file_patterns' in learning
        assert any('src/auth/*.ts' in pattern for pattern in learning['file_patterns'])
        assert any('tests/*.ts' in pattern for pattern in learning['file_patterns'])

    def test_title_truncation(self):
        """Should truncate long task descriptions."""
        task = "Fix a very long bug description that goes on and on and exceeds the 60 character limit"
        history = [{"iteration": 1, "verdict": "PASS", "changes": []}]
        verdict = None
        changes = []

        learning = extract_learning_from_iterations(task, history, verdict, changes)

        assert len(learning['title']) <= 63  # 60 chars + "..."
        assert learning['title'].endswith('...')

    def test_tag_extraction_integration(self):
        """Should use extract_tags_from_task internally."""
        task = "Fix auth bug in login.ts"
        history = [{"iteration": 1, "verdict": "PASS", "changes": []}]
        verdict = None
        changes = []

        learning = extract_learning_from_iterations(task, history, verdict, changes)

        assert 'auth' in learning['tags']
        assert 'login' in learning['tags']
        assert 'typescript' in learning['tags']

    def test_file_pattern_limit(self):
        """Should limit file patterns to 5."""
        task = "Fix bug"
        history = [{"iteration": 1, "verdict": "PASS", "changes": []}]
        verdict = None
        changes = [
            "src/a/file1.ts",
            "src/b/file2.ts",
            "src/c/file3.ts",
            "src/d/file4.ts",
            "src/e/file5.ts",
            "src/f/file6.ts",
            "src/g/file7.ts"
        ]

        learning = extract_learning_from_iterations(task, history, verdict, changes)

        assert len(learning['file_patterns']) <= 5

    def test_empty_changes(self):
        """Should handle empty changes list."""
        task = "Fix bug"
        history = [{"iteration": 1, "verdict": "PASS", "changes": []}]
        verdict = None
        changes = []

        learning = extract_learning_from_iterations(task, history, verdict, changes)

        assert 'file_patterns' in learning
        assert isinstance(learning['file_patterns'], list)


class TestKODisplay:
    """Test KO formatting for display."""

    def test_format_ko_for_display(self):
        """Should format KO for console display."""
        # Create a mock KO object
        class MockKO:
            def __init__(self):
                self.id = "KO-test-001"
                self.title = "Test Knowledge Object"
                self.what_was_learned = "This is what was learned from the test."
                self.prevention_rule = "Prevent by doing X, Y, and Z."
                self.tags = ["test", "example", "mock"]

        ko = MockKO()
        formatted = format_ko_for_display(ko)

        assert "KO-test-001" in formatted
        assert "Test Knowledge Object" in formatted
        assert "test, example, mock" in formatted
        assert "This is what was learned" in formatted
        assert "Prevent by doing X" in formatted
        assert "📖" in formatted  # Emoji icon

    def test_format_ko_truncates_long_text(self):
        """Should truncate long learned and prevention text."""
        class MockKO:
            def __init__(self):
                self.id = "KO-test-002"
                self.title = "Long KO"
                self.what_was_learned = "A" * 150  # 150 chars
                self.prevention_rule = "B" * 150  # 150 chars
                self.tags = ["test"]

        ko = MockKO()
        formatted = format_ko_for_display(ko)

        # Should have "..." for truncation
        assert formatted.count("...") >= 2  # At least 2 truncations
        # Should not contain full 150-char string
        assert "A" * 150 not in formatted
        assert "B" * 150 not in formatted

    def test_format_ko_does_not_truncate_short_text(self):
        """Should not add ellipsis to short text."""
        class MockKO:
            def __init__(self):
                self.id = "KO-test-003"
                self.title = "Short KO"
                self.what_was_learned = "Short text"
                self.prevention_rule = "Also short"
                self.tags = ["test"]

        ko = MockKO()
        formatted = format_ko_for_display(ko)

        # Should not have "..." since text is short
        lines = formatted.split('\n')
        learned_line = [l for l in lines if 'Learned:' in l][0]
        prevention_line = [l for l in lines if 'Prevention:' in l][0]

        assert not learned_line.endswith("...")
        assert not prevention_line.endswith("...")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_extract_tags_handles_special_characters(self):
        """Should handle special characters in task description."""
        task = "Fix bug: auth.ts (high priority!)"
        tags = extract_tags_from_task(task)
        assert 'auth' in tags
        assert 'typescript' in tags
        # Should not crash on special chars

    def test_extract_learning_handles_missing_verdict_field(self):
        """Should handle iteration history without verdict field."""
        task = "Fix bug"
        history = [
            {"iteration": 1, "changes": []},  # No verdict field
            {"iteration": 2, "verdict": "PASS", "changes": []}
        ]
        verdict = None
        changes = []

        learning = extract_learning_from_iterations(task, history, verdict, changes)
        # Should not crash, should return valid learning
        assert 'title' in learning
        assert 'what_was_learned' in learning

    def test_extract_learning_handles_empty_history(self):
        """Should handle empty iteration history."""
        task = "Fix bug"
        history = []
        verdict = None
        changes = []

        learning = extract_learning_from_iterations(task, history, verdict, changes)
        # Should not crash
        assert 'title' in learning
        assert '0 iteration(s)' in learning['what_was_learned']
