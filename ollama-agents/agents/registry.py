"""Tool registry inspired by claw-code.

Central registry of all available tools with their schemas and permission requirements.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .permissions import PermissionMode


# -----------------------------------------------------------------------------
# Tool Specification
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolSpec:
    """Specification for a single tool."""
    name: str
    description: str
    input_schema: dict[str, Any]
    required_permission: PermissionMode
    aliases: tuple[str, ...] = ()

    def __post_init__(self):
        # Validate schema
        if not isinstance(self.input_schema, dict):
            raise ValueError(f"ToolSpec {self.name}: input_schema must be a dict")
        if "type" not in self.input_schema:
            object.__setattr__(
                self, "input_schema",
                {**{"type": "object"}, **self.input_schema}
            )


# -----------------------------------------------------------------------------
# Tool Registry
# -----------------------------------------------------------------------------

class ToolRegistry:
    """Central registry of all tools with aliases and permission lookup.
    
    Inspired by claw-code's GlobalToolRegistry.
    """

    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
        self._normalized_tools: dict[str, str] = {}  # normalized name -> canonical name
        self._aliases: dict[str, str] = {}  # alias -> canonical name
        self._load_builtin_tools()

    @staticmethod
    def _normalize(name: str) -> str:
        return name.strip().lower().replace('-', '_')

    def _load_builtin_tools(self) -> None:
        """Load the 18 MVP tools from claw-code."""
        tools = MVP_TOOL_SPECS
        for spec in tools:
            self.register(spec)

    def register(self, spec: ToolSpec) -> None:
        """Register a tool and its aliases."""
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        normalized_name = self._normalize(spec.name)
        if normalized_name in self._normalized_tools or normalized_name in self._aliases:
            raise ValueError(f"Normalized tool name already registered: {spec.name}")
        self._tools[spec.name] = spec
        self._normalized_tools[normalized_name] = spec.name
        # Register aliases
        for alias in spec.aliases:
            normalized_alias = self._normalize(alias)
            if normalized_alias in self._aliases:
                raise ValueError(f"Alias {alias!r} already registered for {self._aliases[normalized_alias]}")
            if normalized_alias in self._normalized_tools:
                if self._normalized_tools[normalized_alias] != spec.name:
                    raise ValueError(
                        f"Alias {alias!r} conflicts with registered tool {self._normalized_tools[normalized_alias]}"
                    )
                continue
            self._aliases[normalized_alias] = spec.name

    def get(self, name: str) -> Optional[ToolSpec]:
        """Get a tool spec by name or alias."""
        # Try direct name
        if name in self._tools:
            return self._tools[name]
        normalized = self._normalize(name)
        canonical = self._normalized_tools.get(normalized)
        if canonical:
            return self._tools.get(canonical)
        # Try resolving alias
        canonical = self._aliases.get(normalized)
        if canonical:
            return self._tools.get(canonical)
        return None

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_aliases(self) -> list[str]:
        """List all registered aliases."""
        return list(self._aliases.keys())

    def normalize_name(self, name: str) -> str:
        """Normalize a tool name: resolve alias to canonical name, lowercase."""
        normalized = self._normalize(name)
        canonical = self._normalized_tools.get(normalized)
        if canonical:
            return canonical
        if normalized in self._aliases:
            return self._aliases[normalized]
        return normalized

    def get_permission(self, name: str) -> PermissionMode:
        """Get the required permission for a tool."""
        spec = self.get(name)
        if spec is None:
            return PermissionMode.DANGER_FULL_ACCESS  # Unknown tools = dangerous
        return spec.required_permission

    def filter_by_permission(
        self, 
        mode: PermissionMode,
        max_permission: Optional[PermissionMode] = None,
    ) -> list[str]:
        """List tools accessible at or below a given permission level."""
        if max_permission is None:
            max_permission = mode
        
        max_level = max_permission.level
        return [
            name for name, spec in self._tools.items()
            if spec.required_permission.level <= max_level
        ]

    def to_manifest(self) -> dict[str, Any]:
        """Export registry as a manifest dict."""
        return {
            "tools": [
                {
                    "name": spec.name,
                    "description": spec.description,
                    "input_schema": spec.input_schema,
                    "required_permission": str(spec.required_permission),
                    "aliases": list(spec.aliases),
                }
                for spec in self._tools.values()
            ],
            "total": len(self._tools),
        }


# -----------------------------------------------------------------------------
# MVP Tool Specs (18 tools from claw-code)
# -----------------------------------------------------------------------------

MISC_SCHEMA = {"type": "object", "additionalProperties": True}

MISC_STRING_SCHEMA = {
    "type": "object",
    "properties": {"message": {"type": "string"}},
    "required": ["message"],
}

MVP_TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="bash",
        description="Execute a shell command in the current workspace.",
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "minimum": 1},
                "description": {"type": "string"},
                "run_in_background": {"type": "boolean"},
                "dangerouslyDisableSandbox": {"type": "boolean"},
            },
            "required": ["command"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.DANGER_FULL_ACCESS,
        aliases=("BashTool", "shell", "sh"),
    ),
    ToolSpec(
        name="read_file",
        description="Read a text file from the workspace.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0},
                "limit": {"type": "integer", "minimum": 1},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.READ_ONLY,
        aliases=("read", "FileReadTool", "cat"),
    ),
    ToolSpec(
        name="write_file",
        description="Write a text file in the workspace.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.WORKSPACE_WRITE,
        aliases=("write", "FileWriteTool", "create", "FileCreateTool"),
    ),
    ToolSpec(
        name="edit_file",
        description="Replace text in a workspace file.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
                "replace_all": {"type": "boolean"},
            },
            "required": ["path", "old_string", "new_string"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.WORKSPACE_WRITE,
        aliases=("edit", "FileEditTool", "replace", "sed"),
    ),
    ToolSpec(
        name="glob_search",
        description="Find files by glob pattern.",
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.READ_ONLY,
        aliases=("glob", "GlobTool", "find", "GlobSearchTool"),
    ),
    ToolSpec(
        name="grep_search",
        description="Search file contents with a regex pattern.",
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
                "glob": {"type": "string"},
                "output_mode": {"type": "string"},
                "-B": {"type": "integer", "minimum": 0},
                "-A": {"type": "integer", "minimum": 0},
                "-C": {"type": "integer", "minimum": 0},
                "context": {"type": "integer", "minimum": 0},
                "-n": {"type": "boolean"},
                "-i": {"type": "boolean"},
                "type": {"type": "string"},
                "head_limit": {"type": "integer", "minimum": 1},
                "offset": {"type": "integer", "minimum": 0},
                "multiline": {"type": "boolean"},
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.READ_ONLY,
        aliases=("grep", "GrepTool", "GrepSearchTool", "rg", "ack"),
    ),
    ToolSpec(
        name="WebFetch",
        description="Fetch a URL and convert it into readable text.",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "prompt": {"type": "string"},
            },
            "required": ["url", "prompt"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.READ_ONLY,
        aliases=("web_fetch", "fetch", "curl", "http_get"),
    ),
    ToolSpec(
        name="WebSearch",
        description="Search the web for current information and return cited results.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 2},
                "allowed_domains": {"type": "array", "items": {"type": "string"}},
                "blocked_domains": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.READ_ONLY,
        aliases=("web_search", "search", "google", "bing", "ddg"),
    ),
    ToolSpec(
        name="TodoWrite",
        description="Update the structured task list for the current session.",
        input_schema={
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "activeForm": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed"],
                            },
                        },
                        "required": ["content", "activeForm", "status"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["todos"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.WORKSPACE_WRITE,
        aliases=("todo_write", "TodoTool", "todos"),
    ),
    ToolSpec(
        name="Skill",
        description="Load a local skill definition and its instructions.",
        input_schema={
            "type": "object",
            "properties": {
                "skill": {"type": "string"},
                "args": {"type": "string"},
            },
            "required": ["skill"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.READ_ONLY,
        aliases=("skill", "skill_load", "SkillTool"),
    ),
    ToolSpec(
        name="Agent",
        description="Launch a specialized agent task and persist its handoff metadata.",
        input_schema={
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "prompt": {"type": "string"},
                "subagent_type": {"type": "string"},
                "name": {"type": "string"},
                "model": {"type": "string"},
            },
            "required": ["description", "prompt"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.DANGER_FULL_ACCESS,
        aliases=("agent", "spawn", "AgentTool"),
    ),
    ToolSpec(
        name="ToolSearch",
        description="Search for deferred or specialized tools by exact name or keywords.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "minimum": 1},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.READ_ONLY,
        aliases=("tool_search", "search_tools"),
    ),
    ToolSpec(
        name="NotebookEdit",
        description="Replace, insert, or delete a cell in a Jupyter notebook.",
        input_schema={
            "type": "object",
            "properties": {
                "notebook_path": {"type": "string"},
                "cell_id": {"type": "string"},
                "new_source": {"type": "string"},
                "cell_type": {"type": "string", "enum": ["code", "markdown"]},
                "edit_mode": {"type": "string", "enum": ["replace", "insert", "delete"]},
            },
            "required": ["notebook_path"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.WORKSPACE_WRITE,
        aliases=("notebook_edit", "jupyter", "ipynb"),
    ),
    ToolSpec(
        name="Sleep",
        description="Wait for a specified duration without holding a shell process.",
        input_schema={
            "type": "object",
            "properties": {
                "duration_ms": {"type": "integer", "minimum": 0},
            },
            "required": ["duration_ms"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.READ_ONLY,
        aliases=("sleep", "wait"),
    ),
    ToolSpec(
        name="SendUserMessage",
        description="Send a message to the user.",
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "attachments": {"type": "array", "items": {"type": "string"}},
                "status": {"type": "string", "enum": ["normal", "proactive"]},
            },
            "required": ["message", "status"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.READ_ONLY,
        aliases=("send_message", "send", "message", "msg", "Brief"),
    ),
    ToolSpec(
        name="Config",
        description="Get or set Claw settings.",
        input_schema={
            "type": "object",
            "properties": {
                "setting": {"type": "string"},
                "value": {"type": ["string", "boolean", "number"]},
            },
            "required": ["setting"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.WORKSPACE_WRITE,
        aliases=("config", "ConfigTool", "setting", "settings"),
    ),
    ToolSpec(
        name="StructuredOutput",
        description="Return structured output in the requested format.",
        input_schema=MISC_SCHEMA,
        required_permission=PermissionMode.READ_ONLY,
        aliases=("structured_output", "json_output", "StructuredOutputTool"),
    ),
    ToolSpec(
        name="REPL",
        description="Execute code in a REPL-like subprocess.",
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "language": {"type": "string"},
                "timeout_ms": {"type": "integer", "minimum": 1},
            },
            "required": ["code", "language"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.DANGER_FULL_ACCESS,
        aliases=("repl", "REPLTool", "eval", "interpret"),
    ),
    ToolSpec(
        name="PowerShell",
        description="Execute a PowerShell command with optional timeout.",
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "minimum": 1},
                "description": {"type": "string"},
                "run_in_background": {"type": "boolean"},
            },
            "required": ["command"],
            "additionalProperties": False,
        },
        required_permission=PermissionMode.DANGER_FULL_ACCESS,
        aliases=("powershell", "pwsh", "ps1"),
    ),
]


# -----------------------------------------------------------------------------
# Global registry instance
# -----------------------------------------------------------------------------

_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry (singleton)."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
