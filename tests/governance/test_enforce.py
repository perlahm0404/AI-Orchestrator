"""Tests for simplified governance enforcement"""

import pytest
from governance.enforce import GovernanceEnforcement
from governance.contract import ContractViolation, Contract


def test_check_allowed_action():
    """Test checking allowed actions"""
    contract = Contract(
        agent="test",
        version="1.0",
        allowed_actions=["read_file", "write_file"],
        forbidden_actions=["push_to_main"],
        requires_approval=[],
        limits={"max_lines_changed": 100, "max_files_changed": 5},
        invariants={},
        on_violation="halt",
        team="qa"
    )

    enforcer = GovernanceEnforcement(contract)

    # Should not raise
    assert enforcer.check_action("write_file") is True


def test_check_forbidden_action():
    """Test checking forbidden actions"""
    contract = Contract(
        agent="test",
        version="1.0",
        allowed_actions=["read_file"],
        forbidden_actions=[],
        requires_approval=[],
        limits={},
        invariants={},
        on_violation="halt",
        team="qa"
    )

    enforcer = GovernanceEnforcement(contract)

    with pytest.raises(ContractViolation):
        enforcer.check_action("write_file")


def test_check_lines_limit():
    """Test checking lines changed limit"""
    contract = Contract(
        agent="test",
        version="1.0",
        allowed_actions=["write_file"],
        forbidden_actions=[],
        requires_approval=[],
        limits={"max_lines_changed": 50},
        invariants={},
        on_violation="halt",
        team="qa"
    )

    enforcer = GovernanceEnforcement(contract)

    # Should pass
    enforcer.check_action("write_file", {"lines_changed": 30})

    # Should fail
    with pytest.raises(ContractViolation):
        enforcer.check_action("write_file", {"lines_changed": 100})


def test_check_file_write_convenience():
    """Test file write convenience method"""
    contract = Contract(
        agent="test",
        version="1.0",
        allowed_actions=["write_file"],
        forbidden_actions=[],
        requires_approval=[],
        limits={"max_lines_changed": 100},
        invariants={},
        on_violation="halt",
        team="qa"
    )

    enforcer = GovernanceEnforcement(contract)

    # Should not raise
    assert enforcer.check_file_write("test.ts", 50) is True
