"""Tests for simplified governance enforcement"""

import pytest
from governance.enforce import GovernanceEnforcement
from governance.contract import ContractViolation, AutonomyContract


def test_check_allowed_action():
    """Test checking allowed actions"""
    contract = AutonomyContract(
        name="test",
        team="qa",
        branches=["main"],
        allowed_actions=["read_file", "write_file"],
        limits={"max_lines_changed": 100, "max_files_changed": 5},
        forbidden=["push_to_main"]
    )

    enforcer = GovernanceEnforcement(contract)

    # Should not raise
    assert enforcer.check_action("write_file") is True


def test_check_forbidden_action():
    """Test checking forbidden actions"""
    contract = AutonomyContract(
        name="test",
        team="qa",
        branches=["main"],
        allowed_actions=["read_file"],
        limits={},
        forbidden=[]
    )

    enforcer = GovernanceEnforcement(contract)

    with pytest.raises(ContractViolation):
        enforcer.check_action("write_file")


def test_check_lines_limit():
    """Test checking lines changed limit"""
    contract = AutonomyContract(
        name="test",
        team="qa",
        branches=["main"],
        allowed_actions=["write_file"],
        limits={"max_lines_changed": 50},
        forbidden=[]
    )

    enforcer = GovernanceEnforcement(contract)

    # Should pass
    enforcer.check_action("write_file", {"lines_changed": 30})

    # Should fail
    with pytest.raises(ContractViolation):
        enforcer.check_action("write_file", {"lines_changed": 100})


def test_check_file_write_convenience():
    """Test file write convenience method"""
    contract = AutonomyContract(
        name="test",
        team="qa",
        branches=["main"],
        allowed_actions=["write_file"],
        limits={"max_lines_changed": 100},
        forbidden=[]
    )

    enforcer = GovernanceEnforcement(contract)

    # Should not raise
    assert enforcer.check_file_write("test.ts", 50) is True
