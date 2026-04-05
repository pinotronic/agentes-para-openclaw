"""Tests for the permission system - fresh file."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.permissions import (
    PermissionMode,
    PermissionPolicy,
    get_agent_policy,
    code_critic_policy,
    defender_policy,
    implementer_policy,
)


def test_fresh_01_default_policy_bash_danger():
    """Default policy should allow bash for DANGER_FULL_ACCESS agent."""
    policy = PermissionPolicy()
    assert policy.can_use("bash", PermissionMode.DANGER_FULL_ACCESS) is True


def test_fresh_02_default_policy_read_file_readonly():
    """Default policy should allow read_file for READ_ONLY agent."""
    policy = PermissionPolicy()
    assert policy.can_use("read_file", PermissionMode.READ_ONLY) is True


def test_fresh_03_implementer_read_write_edit():
    """Implementer can use read, write, edit."""
    policy = implementer_policy()
    assert policy.can_use("read", PermissionMode.READ_ONLY) is True
    assert policy.can_use("write", PermissionMode.WORKSPACE_WRITE) is True
    assert policy.can_use("edit", PermissionMode.WORKSPACE_WRITE) is True


def test_fresh_04_implementer_bash():
    """Implementer can use bash."""
    policy = implementer_policy()
    assert policy.can_use("bash", PermissionMode.DANGER_FULL_ACCESS) is True


def test_fresh_05_implementer_no_websearch():
    """Implementer cannot use web_search."""
    policy = implementer_policy()
    assert policy.can_use("web_search", PermissionMode.READ_ONLY) is False


def test_fresh_06_code_critic_read_only():
    """Code critic can read."""
    policy = code_critic_policy()
    assert policy.can_use("read", PermissionMode.READ_ONLY) is True


def test_fresh_07_code_critic_no_bash():
    """Code critic cannot use bash."""
    policy = code_critic_policy()
    assert policy.can_use("bash", PermissionMode.DANGER_FULL_ACCESS) is False


def test_fresh_08_defender_no_bash():
    """Defender cannot use bash."""
    policy = defender_policy()
    assert policy.can_use("bash", PermissionMode.DANGER_FULL_ACCESS) is False


def test_fresh_09_policy_restricts_allowed_tools():
    """allowed_tools restricts access."""
    policy = PermissionPolicy(allowed_tools=frozenset({"read", "glob"}))
    assert policy.can_use("read", PermissionMode.READ_ONLY) is True
    assert policy.can_use("glob", PermissionMode.READ_ONLY) is True
    assert policy.can_use("bash", PermissionMode.DANGER_FULL_ACCESS) is False


def test_fresh_10_readonly_cannot_do_danger():
    """READ_ONLY agent cannot use DANGER_FULL_ACCESS tools."""
    policy = PermissionPolicy()
    assert policy.can_use("bash", PermissionMode.READ_ONLY) is False


def test_fresh_11_implementer_alias_needs_danger_mode():
    """Mixed-case aliases should resolve to the same permission requirement."""
    policy = implementer_policy()
    assert policy.can_use("BashTool", PermissionMode.READ_ONLY) is False
    assert policy.can_use("BashTool", PermissionMode.DANGER_FULL_ACCESS) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
