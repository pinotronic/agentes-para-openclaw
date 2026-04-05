"""Tests for the tool registry."""

import pytest
import sys
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.registry import (
    ToolSpec,
    ToolRegistry,
    get_registry,
    MVP_TOOL_SPECS,
)
from agents.permissions import PermissionMode


class TestToolSpec:
    def test_spec_requires_name(self):
        spec = ToolSpec(
            name="bash",
            description="Run bash",
            input_schema={"type": "object", "properties": {}},
            required_permission=PermissionMode.DANGER_FULL_ACCESS,
        )
        assert spec.name == "bash"

    def test_spec_with_aliases(self):
        spec = ToolSpec(
            name="read_file",
            description="Read file",
            input_schema={"type": "object"},
            required_permission=PermissionMode.READ_ONLY,
            aliases=("read", "cat"),
        )
        assert "read" in spec.aliases
        assert "cat" in spec.aliases


class TestToolRegistry:
    def test_global_registry_has_19_tools(self):
        registry = get_registry()
        tools = registry.list_tools()
        assert len(tools) == 19, f"Expected 19 tools, got {len(tools)}"

    def test_global_registry_has_bash(self):
        registry = get_registry()
        assert registry.get("bash") is not None

    def test_global_registry_has_all_mvp_tools(self):
        registry = get_registry()
        expected_names = [spec.name for spec in MVP_TOOL_SPECS]
        for name in expected_names:
            assert registry.get(name) is not None, f"Tool {name} not found"

    def test_normalize_name_canonical(self):
        registry = get_registry()
        assert registry.normalize_name("bash") == "bash"
        assert registry.normalize_name("BASH") == "bash"

    def test_normalize_name_resolves_alias(self):
        registry = get_registry()
        assert registry.normalize_name("read") == "read_file"
        assert registry.normalize_name("cat") == "read_file"
        assert registry.normalize_name("edit") == "edit_file"

    def test_normalize_name_resolves_mixed_case_alias(self):
        registry = get_registry()
        assert registry.normalize_name("BashTool") == "bash"
        assert registry.normalize_name("WebFetch") == "WebFetch"

    def test_get_permission_bash_is_danger(self):
        registry = get_registry()
        assert registry.get_permission("bash") == PermissionMode.DANGER_FULL_ACCESS

    def test_get_permission_read_is_readonly(self):
        registry = get_registry()
        assert registry.get_permission("read_file") == PermissionMode.READ_ONLY
        assert registry.get_permission("read") == PermissionMode.READ_ONLY

    def test_get_permission_write_is_workspace_write(self):
        registry = get_registry()
        assert registry.get_permission("write_file") == PermissionMode.WORKSPACE_WRITE
        assert registry.get_permission("write") == PermissionMode.WORKSPACE_WRITE

    def test_get_permission_mixed_case_alias(self):
        registry = get_registry()
        assert registry.get_permission("BashTool") == PermissionMode.DANGER_FULL_ACCESS
        assert registry.get_permission("WebFetch") == PermissionMode.READ_ONLY

    def test_filter_by_read_only_permission(self):
        registry = get_registry()
        readonly_tools = registry.filter_by_permission(PermissionMode.READ_ONLY)
        # Only READ_ONLY tools should be listed
        for tool_name in readonly_tools:
            perm = registry.get_permission(tool_name)
            assert perm == PermissionMode.READ_ONLY, f"{tool_name} is {perm}, not READ_ONLY"

    def test_filter_by_danger_access_includes_all(self):
        registry = get_registry()
        all_tools = registry.filter_by_permission(PermissionMode.DANGER_FULL_ACCESS)
        assert len(all_tools) == 19, "DANGER_FULL_ACCESS filter should return all tools"

    def test_aliases_list(self):
        registry = get_registry()
        aliases = registry.list_aliases()
        assert "read" in aliases
        assert "write" in aliases
        assert "edit" in aliases
        assert "glob" in aliases
        assert "grep" in aliases

    def test_register_duplicate_raises(self):
        registry = ToolRegistry()
        # bash is already registered in the builtin
        from agents.registry import MVP_TOOL_SPECS
        bash_spec = next(s for s in MVP_TOOL_SPECS if s.name == "bash")
        with pytest.raises(ValueError, match="already registered"):
            registry.register(bash_spec)

    def test_to_manifest(self):
        registry = get_registry()
        manifest = registry.to_manifest()
        assert "tools" in manifest
        assert "total" in manifest
        assert manifest["total"] == 19
        assert len(manifest["tools"]) == 19


class TestMVPToolSpecs:
    def test_all_19_tools_have_names(self):
        assert len(MVP_TOOL_SPECS) == 19
        for spec in MVP_TOOL_SPECS:
            assert spec.name, f"ToolSpec with no name: {spec}"

    def test_all_tools_have_descriptions(self):
        for spec in MVP_TOOL_SPECS:
            assert spec.description, f"Tool {spec.name} has no description"

    def test_all_tools_have_valid_permission(self):
        for spec in MVP_TOOL_SPECS:
            assert isinstance(spec.required_permission, PermissionMode), \
                f"Tool {spec.name} has invalid permission: {spec.required_permission}"

    def test_bash_requires_danger_access(self):
        bash = next(s for s in MVP_TOOL_SPECS if s.name == "bash")
        assert bash.required_permission == PermissionMode.DANGER_FULL_ACCESS

    def test_read_requires_readonly(self):
        read = next(s for s in MVP_TOOL_SPECS if s.name == "read_file")
        assert read.required_permission == PermissionMode.READ_ONLY

    def test_write_requires_workspace_write(self):
        write = next(s for s in MVP_TOOL_SPECS if s.name == "write_file")
        assert write.required_permission == PermissionMode.WORKSPACE_WRITE


class TestToolExecution:
    def test_tool_spec_has_input_schema(self):
        for spec in MVP_TOOL_SPECS:
            assert "type" in spec.input_schema, f"Tool {spec.name} missing 'type' in schema"

    def test_required_fields_are_marked(self):
        # bash should require 'command'
        bash = next(s for s in MVP_TOOL_SPECS if s.name == "bash")
        props = bash.input_schema.get("properties", {})
        assert "command" in bash.input_schema.get("required", [])
        assert "command" in props

    def test_optional_fields_are_not_required(self):
        # read_file has optional offset and limit
        read = next(s for s in MVP_TOOL_SPECS if s.name == "read_file")
        required = read.input_schema.get("required", [])
        assert "offset" not in required
        assert "limit" not in required


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
