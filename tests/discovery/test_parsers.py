"""Unit tests for bug discovery parsers.

Tests each parser with sample outputs to verify correct extraction of bugs.
"""

import json
import pytest

from discovery.parsers.eslint import ESLintParser, LintError
from discovery.parsers.typescript import TypeScriptParser, TypeScriptError
from discovery.parsers.test import TestParser, TestFailure
from discovery.parsers.guardrails import GuardrailParser, GuardrailViolation


class TestESLintParser:
    """Tests for ESLintParser."""

    def test_parse_valid_json(self):
        """Test parsing valid ESLint JSON output."""
        sample_json = json.dumps([
            {
                "filePath": "/path/to/project/src/auth.ts",
                "messages": [
                    {
                        "ruleId": "unused-imports/no-unused-imports",
                        "severity": 2,
                        "message": "Import 'foo' is not used",
                        "line": 5,
                        "column": 10
                    },
                    {
                        "ruleId": "no-console",
                        "severity": 1,
                        "message": "Unexpected console statement",
                        "line": 42,
                        "column": 5
                    }
                ]
            }
        ])

        parser = ESLintParser()
        errors = parser.parse(sample_json)

        assert len(errors) == 2
        assert errors[0].rule_id == "unused-imports/no-unused-imports"
        assert errors[0].line == 5
        assert errors[0].severity == 2
        assert errors[1].rule_id == "no-console"
        assert errors[1].line == 42
        assert errors[1].severity == 1

    def test_parse_empty_output(self):
        """Test parsing empty JSON array."""
        parser = ESLintParser()
        errors = parser.parse("[]")

        assert len(errors) == 0

    def test_parse_security_rule(self):
        """Test that security rules get P0 priority."""
        sample_json = json.dumps([
            {
                "filePath": "src/unsafe.ts",
                "messages": [
                    {
                        "ruleId": "no-eval",
                        "severity": 2,
                        "message": "eval can be harmful",
                        "line": 10,
                        "column": 5
                    }
                ]
            }
        ])

        parser = ESLintParser()
        errors = parser.parse(sample_json)

        assert len(errors) == 1
        assert errors[0].priority == 0  # P0 for security

    def test_parse_correctness_rule(self):
        """Test that correctness rules get P1 priority."""
        sample_json = json.dumps([
            {
                "filePath": "src/code.ts",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "message": "Variable 'x' is not used",
                        "line": 20,
                        "column": 10
                    }
                ]
            }
        ])

        parser = ESLintParser()
        errors = parser.parse(sample_json)

        assert len(errors) == 1
        assert errors[0].priority == 1  # P1 for correctness


class TestTypeScriptParser:
    """Tests for TypeScriptParser."""

    def test_parse_type_errors(self):
        """Test parsing TypeScript compiler errors."""
        sample_output = """
src/auth/session.ts(42,10): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
src/auth/login.ts(15,5): error TS2339: Property 'foo' does not exist on type 'User'.
        """

        parser = TypeScriptParser()
        errors = parser.parse(sample_output)

        assert len(errors) == 2
        assert errors[0].file == "src/auth/session.ts"
        assert errors[0].line == 42
        assert errors[0].column == 10
        assert errors[0].error_code == "TS2345"
        assert errors[1].file == "src/auth/login.ts"
        assert errors[1].line == 15
        assert errors[1].error_code == "TS2339"

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        parser = TypeScriptParser()
        errors = parser.parse("")

        assert len(errors) == 0

    def test_critical_path_priority(self):
        """Test that errors in critical paths get P0 priority."""
        sample_output = "src/auth/session.ts(42,10): error TS2345: Type mismatch."

        parser = TypeScriptParser()
        errors = parser.parse(sample_output)

        assert len(errors) == 1
        assert errors[0].priority == 0  # P0 for critical path + critical error

    def test_missing_type_priority(self):
        """Test that missing type annotations get P1 priority."""
        sample_output = "src/utils.ts(10,5): error TS7006: Parameter 'x' implicitly has 'any' type."

        parser = TypeScriptParser()
        errors = parser.parse(sample_output)

        assert len(errors) == 1
        assert errors[0].priority == 1  # P1 for missing types


class TestTestParser:
    """Tests for TestParser."""

    def test_parse_test_failures(self):
        """Test parsing Vitest JSON test failures."""
        sample_json = json.dumps({
            "testResults": [
                {
                    "name": "services/auth/tests/login.test.ts",
                    "status": "failed",
                    "assertionResults": [
                        {
                            "title": "should authenticate valid user",
                            "status": "failed",
                            "failureMessages": ["Expected 200, got 401"]
                        }
                    ]
                }
            ]
        })

        parser = TestParser()
        failures = parser.parse(sample_json)

        assert len(failures) == 1
        assert failures[0].test_file == "services/auth/tests/login.test.ts"
        assert failures[0].test_name == "should authenticate valid user"
        assert "Expected 200, got 401" in failures[0].failure_message

    def test_infer_source_file(self):
        """Test source file inference from test file path."""
        parser = TestParser()

        # Case 1: /tests/ pattern
        source = parser._infer_source_file("services/auth/tests/login.test.ts")
        assert source == "services/auth/src/login.ts"

        # Case 2: __tests__ pattern
        source = parser._infer_source_file("packages/utils/__tests__/index.test.ts")
        assert source == "packages/utils/index.ts"

    def test_critical_test_priority(self):
        """Test that critical test failures get P0 priority."""
        sample_json = json.dumps({
            "testResults": [
                {
                    "name": "services/auth/tests/login.test.ts",
                    "status": "failed",
                    "assertionResults": [
                        {
                            "title": "should login",
                            "status": "failed",
                            "failureMessages": ["Login failed"]
                        }
                    ]
                }
            ]
        })

        parser = TestParser()
        failures = parser.parse(sample_json)

        assert len(failures) == 1
        assert failures[0].priority == 0  # P0 for auth test failure


class TestGuardrailParser:
    """Tests for GuardrailParser."""

    def test_parse_guardrail_violations(self):
        """Test parsing ripgrep JSON output for guardrail violations."""
        sample_output = """
{"type":"match","data":{"path":{"text":"src/auth.ts"},"lines":{"text":"// @ts-ignore\\n"},"line_number":42}}
{"type":"match","data":{"path":{"text":"src/test.ts"},"lines":{"text":"it.only('should work', () => {})\\n"},"line_number":10}}
        """

        parser = GuardrailParser()
        violations = parser.parse(sample_output)

        assert len(violations) == 2
        assert violations[0].file == "src/auth.ts"
        assert violations[0].line == 42
        assert violations[0].pattern == "@ts-ignore"
        assert violations[1].file == "src/test.ts"
        assert violations[1].line == 10
        assert violations[1].pattern == "it.only"

    def test_only_skip_priority(self):
        """Test that .only() and .skip() get P0 priority."""
        sample_output = '{"type":"match","data":{"path":{"text":"test.ts"},"lines":{"text":"it.only(\'test\', () => {})"},"line_number":5}}'

        parser = GuardrailParser()
        violations = parser.parse(sample_output)

        assert len(violations) == 1
        assert violations[0].priority == 0  # P0 for .only()

    def test_ts_ignore_priority(self):
        """Test that @ts-ignore gets P1 priority."""
        sample_output = '{"type":"match","data":{"path":{"text":"code.ts"},"lines":{"text":"// @ts-ignore"},"line_number":10}}'

        parser = GuardrailParser()
        violations = parser.parse(sample_output)

        assert len(violations) == 1
        assert violations[0].priority == 1  # P1 for @ts-ignore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
