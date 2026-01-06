"""
Tests for branch enforcement in team contracts.

These tests verify that:
1. Branch pattern matching works correctly
2. QA Team can only work on main/fix/* branches
3. Dev Team can only work on feature/* branches
4. Contract violations are raised appropriately
"""

import pytest
from pathlib import Path
from governance.contract import (
    Contract,
    load,
    require_branch,
    ContractViolation,
)


# Test fixtures
@pytest.fixture
def qa_team_contract():
    """Load QA team contract."""
    contracts_dir = Path(__file__).parent.parent.parent / "governance" / "contracts"
    return load("qa-team", contracts_dir)


@pytest.fixture
def dev_team_contract():
    """Load Dev team contract."""
    contracts_dir = Path(__file__).parent.parent.parent / "governance" / "contracts"
    return load("dev-team", contracts_dir)


class TestBranchPatternMatching:
    """Test the branch pattern matching logic."""

    def test_exact_match(self):
        """Test exact branch name matching."""
        contract = Contract(
            agent="test",
            version="1.0",
            allowed_actions=[],
            forbidden_actions=[],
            requires_approval=[],
            limits={},
            invariants={},
            on_violation="halt",
            branch_restrictions={
                "allowed_patterns": ["main"],
                "forbidden_patterns": []
            }
        )
        assert contract.is_branch_allowed("main") is True
        assert contract.is_branch_allowed("master") is False
        assert contract.is_branch_allowed("main-backup") is False

    def test_wildcard_match(self):
        """Test wildcard pattern matching like feature/*."""
        contract = Contract(
            agent="test",
            version="1.0",
            allowed_actions=[],
            forbidden_actions=[],
            requires_approval=[],
            limits={},
            invariants={},
            on_violation="halt",
            branch_restrictions={
                "allowed_patterns": ["feature/*"],
                "forbidden_patterns": []
            }
        )
        assert contract.is_branch_allowed("feature/matching-algorithm") is True
        assert contract.is_branch_allowed("feature/admin-dashboard") is True
        assert contract.is_branch_allowed("feature") is True  # Prefix without slash
        assert contract.is_branch_allowed("fix/bug") is False
        assert contract.is_branch_allowed("main") is False

    def test_forbidden_takes_precedence(self):
        """Test that forbidden patterns take precedence over allowed."""
        contract = Contract(
            agent="test",
            version="1.0",
            allowed_actions=[],
            forbidden_actions=[],
            requires_approval=[],
            limits={},
            invariants={},
            on_violation="halt",
            branch_restrictions={
                "allowed_patterns": ["feature/*"],
                "forbidden_patterns": ["feature/experimental"]
            }
        )
        assert contract.is_branch_allowed("feature/good") is True
        assert contract.is_branch_allowed("feature/experimental") is False

    def test_no_restrictions_allows_all(self):
        """Test that no branch restrictions allows all branches."""
        contract = Contract(
            agent="test",
            version="1.0",
            allowed_actions=[],
            forbidden_actions=[],
            requires_approval=[],
            limits={},
            invariants={},
            on_violation="halt",
            branch_restrictions=None
        )
        assert contract.is_branch_allowed("main") is True
        assert contract.is_branch_allowed("feature/anything") is True
        assert contract.is_branch_allowed("random-branch") is True


class TestQATeamBranchRestrictions:
    """Test that QA team contract enforces correct branches."""

    def test_qa_team_allowed_on_main(self, qa_team_contract):
        """QA team should be allowed on main branch."""
        assert qa_team_contract.is_branch_allowed("main") is True

    def test_qa_team_allowed_on_fix_branch(self, qa_team_contract):
        """QA team should be allowed on fix/* branches."""
        assert qa_team_contract.is_branch_allowed("fix/BUG-123") is True
        assert qa_team_contract.is_branch_allowed("fix/test-infrastructure") is True

    def test_qa_team_allowed_on_hotfix_branch(self, qa_team_contract):
        """QA team should be allowed on hotfix/* branches."""
        assert qa_team_contract.is_branch_allowed("hotfix/urgent-fix") is True

    def test_qa_team_forbidden_on_feature_branch(self, qa_team_contract):
        """QA team should NOT be allowed on feature/* branches."""
        assert qa_team_contract.is_branch_allowed("feature/matching-algorithm") is False
        assert qa_team_contract.is_branch_allowed("feature/admin") is False

    def test_qa_team_require_branch_raises(self, qa_team_contract):
        """require_branch should raise ContractViolation for forbidden branches."""
        with pytest.raises(ContractViolation) as exc_info:
            require_branch(qa_team_contract, "feature/new-feature")

        assert "feature/new-feature" in str(exc_info.value)
        assert "qa-team" in str(exc_info.value)


class TestDevTeamBranchRestrictions:
    """Test that Dev team contract enforces correct branches."""

    def test_dev_team_allowed_on_feature_branch(self, dev_team_contract):
        """Dev team should be allowed on feature/* branches."""
        assert dev_team_contract.is_branch_allowed("feature/matching-algorithm") is True
        assert dev_team_contract.is_branch_allowed("feature/admin-dashboard") is True

    def test_dev_team_forbidden_on_main(self, dev_team_contract):
        """Dev team should NOT be allowed on main branch."""
        assert dev_team_contract.is_branch_allowed("main") is False

    def test_dev_team_forbidden_on_fix_branch(self, dev_team_contract):
        """Dev team should NOT be allowed on fix/* branches."""
        assert dev_team_contract.is_branch_allowed("fix/bug") is False

    def test_dev_team_forbidden_on_hotfix_branch(self, dev_team_contract):
        """Dev team should NOT be allowed on hotfix/* branches."""
        assert dev_team_contract.is_branch_allowed("hotfix/urgent") is False

    def test_dev_team_require_branch_raises_for_main(self, dev_team_contract):
        """require_branch should raise ContractViolation when Dev team on main."""
        with pytest.raises(ContractViolation) as exc_info:
            require_branch(dev_team_contract, "main")

        assert "main" in str(exc_info.value)
        assert "dev-team" in str(exc_info.value)

    def test_dev_team_require_branch_raises_for_fix(self, dev_team_contract):
        """require_branch should raise ContractViolation when Dev team on fix/*."""
        with pytest.raises(ContractViolation) as exc_info:
            require_branch(dev_team_contract, "fix/someone-elses-bug")

        assert "fix/someone-elses-bug" in str(exc_info.value)


class TestContractLoading:
    """Test contract loading with branch restrictions."""

    def test_qa_team_contract_has_branch_restrictions(self, qa_team_contract):
        """QA team contract should have branch_restrictions field."""
        assert qa_team_contract.branch_restrictions is not None
        assert "allowed_patterns" in qa_team_contract.branch_restrictions

    def test_dev_team_contract_has_branch_restrictions(self, dev_team_contract):
        """Dev team contract should have branch_restrictions field."""
        assert dev_team_contract.branch_restrictions is not None
        assert "allowed_patterns" in dev_team_contract.branch_restrictions
        assert "forbidden_patterns" in dev_team_contract.branch_restrictions

    def test_qa_team_is_l2_autonomy(self, qa_team_contract):
        """QA team should have L2 (higher) autonomy level."""
        assert qa_team_contract.autonomy_level == "L2"

    def test_dev_team_is_l1_autonomy(self, dev_team_contract):
        """Dev team should have L1 (stricter) autonomy level."""
        assert dev_team_contract.autonomy_level == "L1"


class TestTeamIsolation:
    """Test that teams are properly isolated from each other's branches."""

    def test_teams_have_no_branch_overlap(self, qa_team_contract, dev_team_contract):
        """QA and Dev teams should have no overlapping allowed branches."""
        test_branches = [
            "main",
            "fix/bug-1",
            "hotfix/urgent",
            "feature/new-feature",
            "feature/admin",
        ]

        for branch in test_branches:
            qa_allowed = qa_team_contract.is_branch_allowed(branch)
            dev_allowed = dev_team_contract.is_branch_allowed(branch)

            # At most one team should be allowed on each branch
            assert not (qa_allowed and dev_allowed), \
                f"Both teams allowed on branch '{branch}' - violation of isolation"

    def test_qa_team_owns_fix_branches(self, qa_team_contract, dev_team_contract):
        """Only QA team should be able to work on fix/* branches."""
        assert qa_team_contract.is_branch_allowed("fix/test") is True
        assert dev_team_contract.is_branch_allowed("fix/test") is False

    def test_dev_team_owns_feature_branches(self, qa_team_contract, dev_team_contract):
        """Only Dev team should be able to work on feature/* branches."""
        assert dev_team_contract.is_branch_allowed("feature/test") is True
        assert qa_team_contract.is_branch_allowed("feature/test") is False
