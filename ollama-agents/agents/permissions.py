"""Permission system inspired by claw-code.

Defines permission modes and policies for agent tool access control.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from discovery import resolve_agent_definition
from runner.permission_mode_store import resolve_permission_mode


# -----------------------------------------------------------------------------
# Permission Mode Hierarchy (explicit, not relying on Enum auto() values)
# -----------------------------------------------------------------------------

class PermissionMode(Enum):
    """Permission levels for tool execution.
    
    Hierarchy (lowest to highest):
    - READ_ONLY: Tools that only read data, no side effects
    - WORKSPACE_WRITE: Tools that modify files within the workspace
    - DANGER_FULL_ACCESS: Tools that can execute commands, delete data, etc.
    """
    READ_ONLY = "read_only"
    WORKSPACE_WRITE = "workspace_write"
    DANGER_FULL_ACCESS = "danger_full_access"

    def __str__(self) -> str:
        return self.name

    @property
    def level(self) -> int:
        """Numeric level for comparison (0=lowest, 2=highest)."""
        return {"READ_ONLY": 0, "WORKSPACE_WRITE": 1, "DANGER_FULL_ACCESS": 2}[self.name]

    def satisfies(self, required: "PermissionMode") -> bool:
        """Check if this mode satisfies a required permission level."""
        return self.level >= required.level

    @classmethod
    def from_string(cls, value: str) -> "PermissionMode":
        """Parse from string representation."""
        mapping = {
            "read_only": cls.READ_ONLY,
            "readonly": cls.READ_ONLY,
            "read-only": cls.READ_ONLY,
            "workspace_write": cls.WORKSPACE_WRITE,
            "workspacewrite": cls.WORKSPACE_WRITE,
            "workspace-write": cls.WORKSPACE_WRITE,
            "danger_full_access": cls.DANGER_FULL_ACCESS,
            "dangerfullaccess": cls.DANGER_FULL_ACCESS,
            "danger-full-access": cls.DANGER_FULL_ACCESS,
            "danger": cls.DANGER_FULL_ACCESS,
        }
        normalized = value.lower().strip()
        if normalized not in mapping:
            raise ValueError(f"Unknown permission mode: {value!r}. Valid: {list(mapping.keys())}")
        return mapping[normalized]


class PermissionOutcome(Enum):
    """Result of a permission check."""
    GRANTED = auto()
    DENIED = auto()


@dataclass(frozen=True)
class PermissionDenied:
    """Details of a denied permission."""
    tool_name: str
    reason: str
    required_mode: PermissionMode


def get_runtime_permission_mode(workspace: Path | None = None, explicit_mode: str | None = None) -> str:
    """Return the current runtime permission mode.

    Modes:
    - permissive: local-first, no agent allowlist enforcement
    - strict: explicit per-agent allowlist enforcement
    """

    mode, _source, _path = resolve_permission_mode(workspace, explicit_mode)
    return mode


def runtime_permissions_are_strict(workspace: Path | None = None, explicit_mode: str | None = None) -> bool:
    """Return True when explicit agent policies must be enforced."""

    return get_runtime_permission_mode(workspace, explicit_mode) == "strict"


# -----------------------------------------------------------------------------
# Permission Policy
# -----------------------------------------------------------------------------

@dataclass
class PermissionPolicy:
    """Maps tools to their required permission levels.
    
    An agent can only use a tool if:
    1. The tool is in the policy's allowed tools set (if defined)
    2. The agent's permission mode >= tool's required permission mode
    """
    default_mode: PermissionMode = PermissionMode.READ_ONLY
    tool_requirements: dict[str, PermissionMode] = field(default_factory=dict)
    allowed_tools: Optional[frozenset[str]] = None  # None = all tools allowed
    _normalize_registry: bool = True  # Flag to prevent recursion during __post_init__

    def __post_init__(self):
        """Normalize allowed_tools to ensure consistent lookups."""
        if self._normalize_registry:
            normalized_requirements = {
                self._normalize(tool): mode
                for tool, mode in self.tool_requirements.items()
            }
            object.__setattr__(self, 'tool_requirements', normalized_requirements)
        if self._normalize_registry and self.allowed_tools is not None:
            normalized = frozenset(self._normalize(t) for t in self.allowed_tools)
            object.__setattr__(self, 'allowed_tools', normalized)

    @staticmethod
    def _normalize(name: str) -> str:
        """Normalize a tool name for consistent lookup."""
        return name.strip().lower().replace('-', '_')

    def requires(self, tool_name: str) -> PermissionMode:
        """Get the required permission mode for a tool."""
        normalized = self._normalize(tool_name)
        explicit = self.tool_requirements.get(normalized)
        if explicit is not None:
            return explicit

        try:
            from .registry import get_registry

            return get_registry().get_permission(tool_name)
        except Exception:
            return PermissionMode.DANGER_FULL_ACCESS

    def check(self, tool_name: str, agent_mode: PermissionMode) -> PermissionOutcome:
        """Check if an agent with given mode can use a tool."""
        normalized = self._normalize(tool_name)
        required = self.requires(normalized)
        if self._mode_sufficient(agent_mode, required):
            return PermissionOutcome.GRANTED
        return PermissionOutcome.DENIED

    @staticmethod
    def _mode_sufficient(agent: PermissionMode, required: PermissionMode) -> bool:
        """Check if agent mode satisfies required mode."""
        return agent.satisfies(required)

    def with_tool_requirement(self, tool: str, mode: PermissionMode) -> PermissionPolicy:
        """Return a new policy with an additional tool requirement."""
        new_requirements = dict(self.tool_requirements)
        new_requirements[self._normalize(tool)] = mode
        return PermissionPolicy(
            default_mode=self.default_mode,
            tool_requirements=new_requirements,
            allowed_tools=self.allowed_tools,
            _normalize_registry=False,
        )

    def add_tool_requirement(self, tool: str, mode: PermissionMode) -> None:
        """Add a tool requirement in place (mutates self)."""
        self.tool_requirements[self._normalize(tool)] = mode

    def with_allowed_tools(self, tools: set[str]) -> PermissionPolicy:
        """Return a new policy that only allows specific tools (names are normalized)."""
        normalized = frozenset(self._normalize(t) for t in tools)
        return PermissionPolicy(
            default_mode=self.default_mode,
            tool_requirements=self.tool_requirements,
            allowed_tools=normalized,
            _normalize_registry=False,
        )

    def can_use(self, tool_name: str, agent_mode: PermissionMode) -> bool:
        """Quick check if agent can use a tool."""
        normalized = self._normalize(tool_name)
        if self.allowed_tools is not None and normalized not in self.allowed_tools:
            return False
        return self.check(normalized, agent_mode) == PermissionOutcome.GRANTED


def _clone_policy(policy: PermissionPolicy) -> PermissionPolicy:
    return PermissionPolicy(
        default_mode=policy.default_mode,
        tool_requirements=dict(policy.tool_requirements),
        allowed_tools=None if policy.allowed_tools is None else frozenset(policy.allowed_tools),
    )


def _load_profile_policy_override(agent_name: str, workspace: Optional[Path]) -> PermissionPolicy | None:
    definition = resolve_agent_definition(agent_name, workspace, Path(__file__).resolve().parents[1])
    if definition is None:
        return None

    try:
        import yaml  # type: ignore
    except Exception:
        return None

    try:
        profile = yaml.safe_load(definition.path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None

    permissions = profile.get("permissions")
    if not isinstance(permissions, dict):
        return None

    inherit = permissions.get("inherit", True)
    if not isinstance(inherit, bool):
        inherit = True

    base_policy = AGENT_POLICIES.get(agent_name)
    if inherit and base_policy is not None:
        policy = _clone_policy(base_policy)
    else:
        policy = PermissionPolicy(default_mode=PermissionMode.READ_ONLY, allowed_tools=frozenset())

    default_mode = permissions.get("default_mode")
    if isinstance(default_mode, str):
        policy.default_mode = PermissionMode.from_string(default_mode)

    allowed_tools = permissions.get("allowed_tools")
    if isinstance(allowed_tools, list):
        policy.allowed_tools = frozenset(policy._normalize(str(tool)) for tool in allowed_tools)

    add_allowed_tools = permissions.get("add_allowed_tools", [])
    if isinstance(add_allowed_tools, list):
        current = set(policy.allowed_tools or ())
        current.update(policy._normalize(str(tool)) for tool in add_allowed_tools)
        policy.allowed_tools = frozenset(current)

    remove_allowed_tools = permissions.get("remove_allowed_tools", [])
    if isinstance(remove_allowed_tools, list):
        current = set(policy.allowed_tools or ())
        for tool in remove_allowed_tools:
            current.discard(policy._normalize(str(tool)))
        policy.allowed_tools = frozenset(current)

    tool_requirements = permissions.get("tool_requirements", {})
    if isinstance(tool_requirements, dict):
        for tool_name, mode in tool_requirements.items():
            if isinstance(mode, str):
                policy.tool_requirements[policy._normalize(str(tool_name))] = PermissionMode.from_string(mode)

    return policy


# -----------------------------------------------------------------------------
# Predefined policies for agents
# -----------------------------------------------------------------------------

def code_critic_policy() -> PermissionPolicy:
    """Code Critic: read-only + web search only. No write, no bash."""
    return PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file", "glob", "glob_search",
            "grep", "grep_search", "web_search", "WebSearch",
            "tool_search", "ToolSearch", "skill", "Skill",
            "structured_output", "StructuredOutput",
        }),
    )


def defender_policy() -> PermissionPolicy:
    """Defender: read-only + sending messages. No write, no bash."""
    return PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file", "glob", "glob_search",
            "grep", "grep_search", "skill", "Skill",
            "structured_output", "StructuredOutput",
            "send_message", "SendUserMessage",
        }),
    )


def implementer_policy() -> PermissionPolicy:
    """Implementer: full file access + bash (dangerous but necessary)."""
    policy = PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file", "write", "write_file",
            "edit", "edit_file", "bash", "BashTool",
            "glob", "glob_search", "grep", "grep_search",
            "skill", "Skill",
        }),
    )
    # Add explicit requirements (keys are normalized by requires())
    policy.tool_requirements["bash"] = PermissionMode.DANGER_FULL_ACCESS
    return policy


def reviewer_policy() -> PermissionPolicy:
    """Reviewer: read-only + web fetch for documentation."""
    return PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file", "glob", "glob_search",
            "grep", "grep_search", "web_fetch", "WebFetch",
            "skill", "Skill", "structured_output", "StructuredOutput",
        }),
    )


def planner_policy() -> PermissionPolicy:
    """Planner: read + web + todo write (no destructive tools)."""
    return PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file", "glob", "glob_search",
            "grep", "grep_search", "web_search", "WebSearch",
            "web_fetch", "WebFetch", "todo_write", "TodoWrite",
            "skill", "Skill", "structured_output", "StructuredOutput",
            "send_message", "SendUserMessage",
        }),
    )


def planner_lite_policy() -> PermissionPolicy:
    """Planner Lite: lightweight planning with read/search tools only."""
    return PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file", "glob", "glob_search",
            "grep", "grep_search", "web_search", "WebSearch",
            "web_fetch", "WebFetch", "tool_search", "ToolSearch",
            "skill", "Skill", "structured_output", "StructuredOutput",
            "send_message", "SendUserMessage",
        }),
    )


def coordinator_policy() -> PermissionPolicy:
    """Coordinator: orchestration, delegation metadata, and user coordination."""
    policy = PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file", "glob", "glob_search",
            "grep", "grep_search", "web_search", "WebSearch",
            "web_fetch", "WebFetch", "todo_write", "TodoWrite",
            "tool_search", "ToolSearch", "agent", "Agent",
            "skill", "Skill", "structured_output", "StructuredOutput",
            "send_message", "SendUserMessage",
        }),
    )
    policy.tool_requirements["agent"] = PermissionMode.DANGER_FULL_ACCESS
    return policy


def diagnoser_policy() -> PermissionPolicy:
    """Diagnoser: read + bash for diagnostics (limited)."""
    return PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file", "bash", "BashTool",
            "glob", "glob_search", "grep", "grep_search",
        }),
        tool_requirements={
            "bash": PermissionMode.DANGER_FULL_ACCESS,
        },
    )


def debater_policy() -> PermissionPolicy:
    """Debater: read-only + structured output + sending messages."""
    return PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file", "glob", "glob_search",
            "grep", "grep_search", "skill", "Skill",
            "structured_output", "StructuredOutput",
            "send_message", "SendUserMessage",
        }),
    )


def test_writer_policy() -> PermissionPolicy:
    """Test Writer: diff-first inspection only in the main pipeline."""
    return PermissionPolicy(
        default_mode=PermissionMode.READ_ONLY,
        allowed_tools=frozenset({
            "read", "read_file",
            "glob", "glob_search", "grep", "grep_search",
        }),
    )


# -----------------------------------------------------------------------------
# Registry of agent policies
# -----------------------------------------------------------------------------

AGENT_POLICIES: dict[str, PermissionPolicy] = {
    "code_critic": code_critic_policy(),
    "coordinator": coordinator_policy(),
    "defender": defender_policy(),
    "implementer": implementer_policy(),
    "reviewer": reviewer_policy(),
    "planner": planner_policy(),
    "planner_lite": planner_lite_policy(),
    "diagnoser": diagnoser_policy(),
    "debater": debater_policy(),
    "test_writer": test_writer_policy(),
}


def has_agent_policy(agent_name: str, workspace=None, explicit_mode: str | None = None) -> bool:
    """Return True when an agent has an explicit registered policy."""
    if not runtime_permissions_are_strict(workspace, explicit_mode):
        return True
    return agent_name in AGENT_POLICIES or _load_profile_policy_override(agent_name, workspace) is not None


def get_agent_policy(agent_name: str, workspace=None, explicit_mode: str | None = None) -> PermissionPolicy:
    """Get the permission policy for an agent."""
    if not runtime_permissions_are_strict(workspace, explicit_mode):
        return PermissionPolicy(default_mode=PermissionMode.DANGER_FULL_ACCESS)
    override = _load_profile_policy_override(agent_name, workspace)
    if override is not None:
        return override
    return AGENT_POLICIES.get(agent_name, PermissionPolicy())
