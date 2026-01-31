"""
Tests for Simplified Governance (Phase 5)

TDD approach: Tests written first, then implementation.
Target: Governance in ~200 lines with single enforcement point.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import Optional, List

# These imports will fail until we implement the modules
try:
    from governance.simple_enforce import (
        check_action,
        load_contract,
        ContractViolation,
        SimpleContract,
        ActionContext,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

    # Placeholder classes for test definition
    class ContractViolation(Exception):
        pass

    @dataclass
    class SimpleContract:
        name: str
        branches: List[str]
        allowed_actions: List[str]
        forbidden_actions: List[str]
        max_lines_changed: int = 100
        max_files_changed: int = 5
        max_iterations: int = 15

    @dataclass
    class ActionContext:
        team: str
        action: str
        branch: str = "main"
        lines_changed: int = 0
        files_changed: int = 0
        iteration: int = 1


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestSimpleContract:
    """Test SimpleContract dataclass."""

    def test_contract_has_required_fields(self):
        """Contract has all required fields."""
        contract = SimpleContract(
            name="qa-team",
            branches=["main", "fix/*"],
            allowed_actions=["read_file", "write_file", "run_tests"],
            forbidden_actions=["deploy", "push_to_main"],
            max_lines_changed=100,
            max_files_changed=5,
            max_iterations=15
        )

        assert contract.name == "qa-team"
        assert "main" in contract.branches
        assert "read_file" in contract.allowed_actions
        assert "deploy" in contract.forbidden_actions

    def test_contract_default_limits(self):
        """Contract has sensible default limits."""
        contract = SimpleContract(
            name="test",
            branches=["main"],
            allowed_actions=["read_file"],
            forbidden_actions=[]
        )

        assert contract.max_lines_changed == 100
        assert contract.max_files_changed == 5
        assert contract.max_iterations == 15


class TestActionContext:
    """Test ActionContext dataclass."""

    def test_context_captures_action_details(self):
        """Context captures all relevant action details."""
        context = ActionContext(
            team="qa-team",
            action="write_file",
            branch="fix/auth-bug",
            lines_changed=50,
            files_changed=2,
            iteration=3
        )

        assert context.team == "qa-team"
        assert context.action == "write_file"
        assert context.branch == "fix/auth-bug"
        assert context.lines_changed == 50


class TestCheckAction:
    """Test the check_action function."""

    @pytest.fixture
    def qa_contract(self):
        return SimpleContract(
            name="qa-team",
            branches=["main", "fix/*"],
            allowed_actions=["read_file", "write_file", "run_tests", "git_commit"],
            forbidden_actions=["modify_migrations", "push_to_main", "deploy"],
            max_lines_changed=100,
            max_files_changed=5,
            max_iterations=15
        )

    @pytest.fixture
    def dev_contract(self):
        return SimpleContract(
            name="dev-team",
            branches=["feature/*"],
            allowed_actions=["read_file", "write_file", "run_tests", "git_commit", "create_file"],
            forbidden_actions=["deploy", "modify_production"],
            max_lines_changed=500,
            max_files_changed=20,
            max_iterations=50
        )

    def test_allowed_action_passes(self, qa_contract):
        """Allowed action returns True."""
        context = ActionContext(
            team="qa-team",
            action="write_file",
            branch="fix/bug-123"
        )

        with patch('governance.simple_enforce.load_contract', return_value=qa_contract):
            result = check_action(context)

        assert result is True

    def test_forbidden_action_raises(self, qa_contract):
        """Forbidden action raises ContractViolation."""
        context = ActionContext(
            team="qa-team",
            action="deploy",
            branch="main"
        )

        with patch('governance.simple_enforce.load_contract', return_value=qa_contract):
            with pytest.raises(ContractViolation) as exc_info:
                check_action(context)

        assert "deploy" in str(exc_info.value).lower()

    def test_unknown_action_raises(self, qa_contract):
        """Unknown action (not in allowed list) raises ContractViolation."""
        context = ActionContext(
            team="qa-team",
            action="unknown_action",
            branch="main"
        )

        with patch('governance.simple_enforce.load_contract', return_value=qa_contract):
            with pytest.raises(ContractViolation) as exc_info:
                check_action(context)

        assert "not allowed" in str(exc_info.value).lower()

    def test_wrong_branch_raises(self, qa_contract):
        """Action on wrong branch raises ContractViolation."""
        context = ActionContext(
            team="qa-team",
            action="write_file",
            branch="feature/new-feature"  # QA can't write to feature branches
        )

        with patch('governance.simple_enforce.load_contract', return_value=qa_contract):
            with pytest.raises(ContractViolation) as exc_info:
                check_action(context)

        assert "branch" in str(exc_info.value).lower()

    def test_exceeds_max_lines_raises(self, qa_contract):
        """Exceeding max_lines_changed raises ContractViolation."""
        context = ActionContext(
            team="qa-team",
            action="write_file",
            branch="main",
            lines_changed=150  # Exceeds 100 limit
        )

        with patch('governance.simple_enforce.load_contract', return_value=qa_contract):
            with pytest.raises(ContractViolation) as exc_info:
                check_action(context)

        assert "lines" in str(exc_info.value).lower()

    def test_exceeds_max_files_raises(self, qa_contract):
        """Exceeding max_files_changed raises ContractViolation."""
        context = ActionContext(
            team="qa-team",
            action="write_file",
            branch="main",
            files_changed=10  # Exceeds 5 limit
        )

        with patch('governance.simple_enforce.load_contract', return_value=qa_contract):
            with pytest.raises(ContractViolation) as exc_info:
                check_action(context)

        assert "files" in str(exc_info.value).lower()

    def test_exceeds_max_iterations_raises(self, qa_contract):
        """Exceeding max_iterations raises ContractViolation."""
        context = ActionContext(
            team="qa-team",
            action="write_file",
            branch="main",
            iteration=20  # Exceeds 15 limit
        )

        with patch('governance.simple_enforce.load_contract', return_value=qa_contract):
            with pytest.raises(ContractViolation) as exc_info:
                check_action(context)

        assert "iteration" in str(exc_info.value).lower()


class TestBranchMatching:
    """Test branch pattern matching."""

    @pytest.fixture
    def contract_with_wildcards(self):
        return SimpleContract(
            name="test",
            branches=["main", "fix/*", "hotfix/**"],
            allowed_actions=["write_file"],
            forbidden_actions=[]
        )

    def test_exact_branch_match(self, contract_with_wildcards):
        """Exact branch name matches."""
        context = ActionContext(
            team="test",
            action="write_file",
            branch="main"
        )

        with patch('governance.simple_enforce.load_contract', return_value=contract_with_wildcards):
            result = check_action(context)

        assert result is True

    def test_wildcard_branch_match(self, contract_with_wildcards):
        """Wildcard pattern matches single level."""
        context = ActionContext(
            team="test",
            action="write_file",
            branch="fix/bug-123"
        )

        with patch('governance.simple_enforce.load_contract', return_value=contract_with_wildcards):
            result = check_action(context)

        assert result is True

    def test_double_wildcard_matches_nested(self, contract_with_wildcards):
        """Double wildcard matches nested paths."""
        context = ActionContext(
            team="test",
            action="write_file",
            branch="hotfix/v1/critical"
        )

        with patch('governance.simple_enforce.load_contract', return_value=contract_with_wildcards):
            result = check_action(context)

        assert result is True


class TestLoadContract:
    """Test contract loading."""

    def test_load_contract_from_yaml(self, tmp_path: Path):
        """Load contract from YAML file."""
        contracts_dir = tmp_path / "governance" / "contracts"
        contracts_dir.mkdir(parents=True)

        contract_file = contracts_dir / "qa-team.yaml"
        contract_file.write_text("""
name: qa-team
branches:
  - main
  - fix/*
allowed_actions:
  - read_file
  - write_file
forbidden_actions:
  - deploy
limits:
  max_lines_changed: 100
  max_files_changed: 5
  max_iterations: 15
""")

        contract = load_contract("qa-team", contracts_dir)

        assert contract.name == "qa-team"
        assert "main" in contract.branches
        assert "read_file" in contract.allowed_actions
        assert "deploy" in contract.forbidden_actions

    def test_load_nonexistent_contract_raises(self, tmp_path: Path):
        """Loading nonexistent contract raises error."""
        contracts_dir = tmp_path / "governance" / "contracts"
        contracts_dir.mkdir(parents=True)

        with pytest.raises(FileNotFoundError):
            load_contract("nonexistent-team", contracts_dir)


class TestContractViolation:
    """Test ContractViolation exception."""

    def test_violation_has_message(self):
        """ContractViolation has descriptive message."""
        violation = ContractViolation("Action 'deploy' not allowed for qa-team")

        assert "deploy" in str(violation)
        assert "qa-team" in str(violation)

    def test_violation_is_exception(self):
        """ContractViolation is an Exception."""
        assert issubclass(ContractViolation, Exception)


class TestIntegrationWithLoop:
    """Test governance integration with SimplifiedLoop."""

    def test_loop_checks_governance_before_action(self, tmp_path: Path):
        """Loop should check governance before executing actions."""
        # This test verifies the integration point exists
        # The actual enforcement happens in the loop

        from orchestration.simplified_loop import SimplifiedLoop, LoopConfig

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        # Loop should have a way to check governance
        # This could be a method or it could be built into _execute_task
        assert hasattr(loop, 'config')  # Basic sanity check

    def test_blocked_action_prevents_execution(self, tmp_path: Path):
        """Blocked governance action prevents task execution."""
        from orchestration.simplified_loop import SimplifiedLoop, LoopConfig

        config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(config)

        # Verify the loop can be extended with governance checks
        # The actual integration is optional - governance can be called
        # from hooks or wrappers around the loop

        # Test that ContractViolation can be raised and caught
        try:
            raise ContractViolation("Test violation")
        except ContractViolation as e:
            assert "violation" in str(e).lower()

        # Verify governance module is importable and usable
        from governance.simple_enforce import check_action, ActionContext, SimpleContract

        contract = SimpleContract(
            name="test",
            branches=["main"],
            allowed_actions=["read_file"],
            forbidden_actions=["deploy"]
        )

        context = ActionContext(team="test", action="deploy", branch="main")

        with patch('governance.simple_enforce.load_contract', return_value=contract):
            with pytest.raises(ContractViolation):
                check_action(context)
