"""Runtime tool executor with permission enforcement.

This module introduces a minimal structured tool-call protocol so local agents
can request tool execution without bypassing the registry/policy layer.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.error import URLError
from urllib.request import Request, urlopen

from discovery import resolve_skill_definition
from .hooks import HookRunner
from .permissions import PermissionPolicy, get_agent_policy, has_agent_policy
from .registry import ToolRegistry, get_registry


TOOL_CALL_RE = re.compile(r"<TOOL_CALL>\s*(.*?)\s*</TOOL_CALL>", re.DOTALL)


class ToolExecutionError(RuntimeError):
    """Base error for runtime tool execution failures."""


class ToolPermissionError(ToolExecutionError):
    """Raised when an agent tries to use a blocked tool."""


class ToolValidationError(ToolExecutionError):
    """Raised when a tool call payload is malformed."""


@dataclass(frozen=True)
class ToolCall:
    """Canonical structured tool invocation."""

    tool: str
    arguments: dict[str, Any]


class _HTMLTextExtractor(HTMLParser):
    """Best-effort HTML to text extractor for WebFetch."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in {"p", "div", "section", "article", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._chunks.append(text)

    def get_text(self) -> str:
        raw = html.unescape(" ".join(self._chunks))
        return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", raw)).strip()


def parse_tool_call(text: str) -> ToolCall | None:
    """Extract one structured tool call from model output.

    Supported formats:
    - <TOOL_CALL>{...}</TOOL_CALL>
    - a raw JSON object with {"tool": ..., "arguments": ...}
    """

    stripped = text.strip()
    payload: str | None = None

    match = TOOL_CALL_RE.search(stripped)
    if match:
        payload = match.group(1).strip()
    elif stripped.startswith("{") and stripped.endswith("}"):
        payload = stripped
    else:
        return None

    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ToolValidationError(f"invalid tool call JSON: {exc}") from exc

    if not isinstance(decoded, dict):
        raise ToolValidationError("tool call payload must be a JSON object")

    tool_name = decoded.get("tool")
    arguments = decoded.get("arguments", {})

    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ToolValidationError("tool call must include a non-empty 'tool' string")
    if not isinstance(arguments, dict):
        raise ToolValidationError("tool call 'arguments' must be an object")

    return ToolCall(tool=tool_name, arguments=arguments)


def build_tool_instructions(agent_id: str, workspace: Path | None = None, explicit_mode: str | None = None) -> str:
    """Return prompt instructions for the structured tool-call protocol."""

    registry = get_registry()
    policy = get_agent_policy(agent_id, workspace, explicit_mode)
    allowed_raw = policy.allowed_tools or frozenset(registry.list_tools())
    allowed = sorted({registry.normalize_name(name) for name in allowed_raw})

    lines = [
        "You may optionally use runtime tools.",
        "If you need a tool, respond with exactly one tool call and nothing else:",
        "<TOOL_CALL>",
        '{"tool":"canonical_name","arguments":{}}',
        "</TOOL_CALL>",
        "Use only canonical tool names from the allowed list below.",
        "If no tool is needed, return the final answer directly.",
        "Allowed canonical tools:",
    ]
    lines.extend(f"- {tool_name}" for tool_name in allowed)
    return "\n".join(lines)


class ToolExecutor:
    """Execute a minimal subset of registry tools inside a workspace."""

    def __init__(self, *, agent_id: str, workspace: Path, explicit_mode: str | None = None):
        if not has_agent_policy(agent_id, workspace, explicit_mode):
            raise ToolPermissionError(f"Agent {agent_id!r} has no explicit permission policy")

        self.agent_id = agent_id
        self.workspace = workspace.expanduser().resolve()
        self.core_root = Path(__file__).resolve().parents[1]
        self.registry: ToolRegistry = get_registry()
        self.policy: PermissionPolicy = get_agent_policy(agent_id, self.workspace, explicit_mode)
        self.hooks = HookRunner(agent_id=agent_id, workspace=self.workspace)

    def execute(self, call: ToolCall) -> dict[str, Any]:
        canonical_tool = self.registry.normalize_name(call.tool)
        spec = self.registry.get(canonical_tool)
        if spec is None:
            raise ToolValidationError(f"unknown tool: {call.tool}")

        if not self.policy.can_use(canonical_tool, self.policy.requires(canonical_tool)):
            raise ToolPermissionError(
                f"agent {self.agent_id!r} is not allowed to use tool {canonical_tool!r}"
            )

        self._validate_input(spec.input_schema, call.arguments)

        pre_hook = self.hooks.run_pre_tool_use(tool_name=canonical_tool, arguments=call.arguments)
        if not pre_hook.allowed:
            error = pre_hook.error or f"pre_tool_use hook denied tool {canonical_tool!r}"
            raise ToolPermissionError(error)

        if canonical_tool == "read_file":
            result = self._exec_read_file(call.arguments)
        elif canonical_tool == "glob_search":
            result = self._exec_glob_search(call.arguments)
        elif canonical_tool == "grep_search":
            result = self._exec_grep_search(call.arguments)
        elif canonical_tool == "write_file":
            result = self._exec_write_file(call.arguments)
        elif canonical_tool == "edit_file":
            result = self._exec_edit_file(call.arguments)
        elif canonical_tool == "WebFetch":
            result = self._exec_web_fetch(call.arguments)
        elif canonical_tool == "WebSearch":
            result = self._exec_web_search(call.arguments)
        elif canonical_tool == "ToolSearch":
            result = self._exec_tool_search(call.arguments)
        elif canonical_tool == "Skill":
            result = self._exec_skill(call.arguments)
        elif canonical_tool == "bash":
            result = self._exec_bash(call.arguments)
        elif canonical_tool == "TodoWrite":
            result = {"ok": True, "todos": call.arguments["todos"]}
        elif canonical_tool == "SendUserMessage":
            result = {"ok": True, "message": call.arguments["message"], "status": call.arguments["status"]}
        elif canonical_tool == "StructuredOutput":
            result = {"ok": True, "output": call.arguments}
        else:
            raise ToolExecutionError(f"tool {canonical_tool!r} is allowed but not implemented at runtime")

        hook_messages = list(pre_hook.messages)
        post_hook = self.hooks.run_post_tool_use(tool_name=canonical_tool, arguments=call.arguments, result=result)
        hook_messages.extend(post_hook.messages)
        if hook_messages:
            result["hook_messages"] = hook_messages
        if not post_hook.allowed:
            result["hook_error"] = post_hook.error or f"post_tool_use hook failed for {canonical_tool!r}"
        return result

    def _validate_input(self, schema: dict[str, Any], arguments: dict[str, Any]) -> None:
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        additional_allowed = schema.get("additionalProperties", True)

        for key in required:
            if key not in arguments:
                raise ToolValidationError(f"missing required argument: {key}")

        if additional_allowed is False:
            unknown = sorted(key for key in arguments if key not in properties)
            if unknown:
                raise ToolValidationError(f"unexpected arguments: {', '.join(unknown)}")

        for key, value in arguments.items():
            property_schema = properties.get(key)
            if property_schema is None:
                continue
            self._validate_value(value=value, schema=property_schema, path=key)

    def _validate_value(self, *, value: Any, schema: dict[str, Any], path: str) -> None:
        expected_type = schema.get("type")
        if expected_type is not None:
            self._validate_type(value=value, expected_type=expected_type, path=path)

        if "enum" in schema and value not in schema["enum"]:
            allowed = ", ".join(repr(item) for item in schema["enum"])
            raise ToolValidationError(f"{path} must be one of: {allowed}")

        if isinstance(value, str):
            min_length = schema.get("minLength")
            if min_length is not None and len(value) < int(min_length):
                raise ToolValidationError(f"{path} must have at least {min_length} characters")
            if schema.get("format") == "uri" and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
                raise ToolValidationError(f"{path} must be a valid URI")

        if isinstance(value, int) and not isinstance(value, bool):
            minimum = schema.get("minimum")
            if minimum is not None and value < int(minimum):
                raise ToolValidationError(f"{path} must be >= {minimum}")

        if isinstance(value, list):
            item_schema = schema.get("items")
            if item_schema is not None:
                for index, item in enumerate(value):
                    self._validate_value(value=item, schema=item_schema, path=f"{path}[{index}]")

        if isinstance(value, dict):
            nested_properties = schema.get("properties", {})
            nested_required = schema.get("required", [])
            nested_additional = schema.get("additionalProperties", True)

            for key in nested_required:
                if key not in value:
                    raise ToolValidationError(f"{path}.{key} is required")

            if nested_additional is False:
                unknown = sorted(key for key in value if key not in nested_properties)
                if unknown:
                    raise ToolValidationError(f"{path} has unexpected fields: {', '.join(unknown)}")

            for key, nested_value in value.items():
                nested_schema = nested_properties.get(key)
                if nested_schema is None:
                    continue
                self._validate_value(value=nested_value, schema=nested_schema, path=f"{path}.{key}")

    def _validate_type(self, *, value: Any, expected_type: Any, path: str) -> None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if any(self._matches_type(value=value, expected_type=item) for item in expected_types):
            return
        expected = ", ".join(str(item) for item in expected_types)
        actual = type(value).__name__
        raise ToolValidationError(f"{path} must be of type {expected}, got {actual}")

    @staticmethod
    def _matches_type(*, value: Any, expected_type: str) -> bool:
        if expected_type == "string":
            return isinstance(value, str)
        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "boolean":
            return isinstance(value, bool)
        if expected_type == "number":
            return (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)
        if expected_type == "array":
            return isinstance(value, list)
        if expected_type == "object":
            return isinstance(value, dict)
        return True

    def _resolve_workspace_path(self, raw_path: str) -> Path:
        candidate = (self.workspace / raw_path).resolve()
        if candidate != self.workspace and self.workspace not in candidate.parents:
            raise ToolExecutionError(f"path escapes workspace: {raw_path}")
        return candidate

    def _exec_read_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_workspace_path(arguments["path"])
        if not path.exists():
            raise ToolExecutionError(f"file not found: {arguments['path']}")
        if path.is_dir():
            raise ToolExecutionError(f"path is a directory: {arguments['path']}")

        offset = int(arguments.get("offset", 0))
        limit = arguments.get("limit")
        lines = path.read_text(encoding="utf-8").splitlines()
        selected = lines[offset:] if limit is None else lines[offset: offset + int(limit)]
        return {
            "ok": True,
            "path": str(path.relative_to(self.workspace)),
            "content": "\n".join(selected),
            "line_count": len(selected),
        }

    def _exec_write_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_workspace_path(arguments["path"])
        if path.exists() and path.is_dir():
            raise ToolExecutionError(f"path is a directory: {arguments['path']}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(arguments["content"], encoding="utf-8")
        return {
            "ok": True,
            "path": str(path.relative_to(self.workspace)),
            "bytes_written": len(arguments["content"].encode("utf-8")),
        }

    def _exec_edit_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_workspace_path(arguments["path"])
        if not path.exists():
            raise ToolExecutionError(f"file not found: {arguments['path']}")
        if path.is_dir():
            raise ToolExecutionError(f"path is a directory: {arguments['path']}")

        original = path.read_text(encoding="utf-8")
        old_string = arguments["old_string"]
        new_string = arguments["new_string"]
        replace_all = bool(arguments.get("replace_all", False))

        occurrences = original.count(old_string)
        if occurrences == 0:
            raise ToolExecutionError("old_string not found in file")
        if not replace_all and occurrences != 1:
            raise ToolExecutionError(
                "old_string appears multiple times; pass replace_all=true to replace all occurrences"
            )

        if replace_all:
            updated = original.replace(old_string, new_string)
            replacements = occurrences
        else:
            updated = original.replace(old_string, new_string, 1)
            replacements = 1

        path.write_text(updated, encoding="utf-8")
        return {
            "ok": True,
            "path": str(path.relative_to(self.workspace)),
            "replacements": replacements,
        }

    def _exec_glob_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        pattern = arguments["pattern"]
        base = self.workspace
        if "path" in arguments:
            base = self._resolve_workspace_path(arguments["path"])
            if not base.exists() or not base.is_dir():
                raise ToolExecutionError(f"search path is not a directory: {arguments['path']}")

        matches = sorted(
            str(path.relative_to(self.workspace))
            for path in base.glob(pattern)
            if path.exists()
        )
        return {"ok": True, "matches": matches, "count": len(matches)}

    def _exec_web_fetch(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            arguments["url"],
            headers={"User-Agent": "ollama-agents/1.0 (+runtime-webfetch)"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                status_code = getattr(response, "status", None) or response.getcode()
                content_type = response.headers.get("Content-Type", "")
                body = response.read(1_000_000)
        except URLError as exc:
            raise ToolExecutionError(f"failed to fetch URL: {exc}") from exc

        decoded = body.decode("utf-8", errors="replace")
        if "html" in content_type.lower() or "<html" in decoded.lower():
            parser = _HTMLTextExtractor()
            parser.feed(decoded)
            content = parser.get_text()
        else:
            content = decoded.strip()

        excerpt = content[:4000]
        return {
            "ok": True,
            "url": arguments["url"],
            "status_code": status_code,
            "content_type": content_type,
            "prompt": arguments["prompt"],
            "content": excerpt,
        }

    def _exec_web_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments["query"]
        params = urlencode({"q": query})
        request = Request(
            f"https://duckduckgo.com/html/?{params}",
            headers={"User-Agent": "ollama-agents/1.0 (+runtime-websearch)"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                status_code = getattr(response, "status", None) or response.getcode()
                body = response.read(1_000_000).decode("utf-8", errors="replace")
        except URLError as exc:
            raise ToolExecutionError(f"failed to search web: {exc}") from exc

        results = self._parse_web_search_results(body)
        allowed_domains = {domain.lower() for domain in arguments.get("allowed_domains", [])}
        blocked_domains = {domain.lower() for domain in arguments.get("blocked_domains", [])}

        filtered: list[dict[str, Any]] = []
        for item in results:
            domain = item["domain"].lower()
            if allowed_domains and domain not in allowed_domains:
                continue
            if domain in blocked_domains:
                continue
            filtered.append(item)

        return {
            "ok": True,
            "query": query,
            "status_code": status_code,
            "results": filtered[:10],
            "count": min(len(filtered), 10),
        }

    def _parse_web_search_results(self, html_text: str) -> list[dict[str, Any]]:
        matches = re.findall(
            r'<a[^>]+class="[^\"]*result__a[^\"]*"[^>]+href="([^\"]+)"[^>]*>(.*?)</a>',
            html_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        results: list[dict[str, Any]] = []
        for raw_href, raw_title in matches:
            href = html.unescape(raw_href)
            title = self._strip_html(raw_title)
            final_url = self._extract_result_url(href)
            parsed = urlparse(final_url)
            domain = parsed.netloc.lower()
            if not domain:
                continue
            results.append({
                "title": title,
                "url": final_url,
                "domain": domain,
            })
        return results

    @staticmethod
    def _extract_result_url(href: str) -> str:
        parsed = urlparse(href)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            target = parse_qs(parsed.query).get("uddg")
            if target:
                return unquote(target[0])
        return href

    @staticmethod
    def _strip_html(value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value)
        return re.sub(r"\s+", " ", html.unescape(text)).strip()

    def _exec_tool_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments["query"].strip().lower()
        query_terms = [term for term in re.split(r"\s+", query) if term]
        max_results = int(arguments.get("max_results", 10))

        scored: list[tuple[int, dict[str, Any]]] = []
        for tool_name in self.registry.list_tools():
            spec = self.registry.get(tool_name)
            if spec is None:
                continue
            haystack = " ".join([
                spec.name.lower(),
                spec.description.lower(),
                " ".join(alias.lower() for alias in spec.aliases),
            ])
            score = 0
            if spec.name.lower() == query:
                score += 100
            if query in spec.name.lower():
                score += 50
            if query in haystack:
                score += 20
            score += sum(5 for term in query_terms if term in haystack)
            if score == 0:
                continue
            scored.append((score, {
                "name": spec.name,
                "description": spec.description,
                "required_permission": spec.required_permission.value,
                "aliases": list(spec.aliases),
            }))

        scored.sort(key=lambda item: (-item[0], item[1]["name"]))
        results = [item[1] for item in scored[:max_results]]
        return {
            "ok": True,
            "query": arguments["query"],
            "matches": results,
            "count": len(results),
        }

    def _exec_skill(self, arguments: dict[str, Any]) -> dict[str, Any]:
        definition = resolve_skill_definition(arguments["skill"], self.workspace, self.core_root)
        if definition is None:
            raise ToolExecutionError(f"skill not found: {arguments['skill']}")

        return {
            "ok": True,
            "skill": definition.name,
            "path": str(definition.path),
            "source": definition.source.label,
            "description": definition.description,
            "args": arguments.get("args", ""),
            "content": definition.path.read_text(encoding="utf-8"),
        }

    def _exec_grep_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        pattern = arguments["pattern"]
        flags = re.IGNORECASE if arguments.get("-i") else 0
        try:
            compiled = re.compile(pattern, flags)
        except re.error as exc:
            raise ToolValidationError(f"invalid regex pattern: {exc}") from exc

        base = self.workspace
        if "path" in arguments:
            base = self._resolve_workspace_path(arguments["path"])
            if not base.exists() or not base.is_dir():
                raise ToolExecutionError(f"search path is not a directory: {arguments['path']}")

        file_glob = arguments.get("glob", "**/*")
        head_limit = int(arguments.get("head_limit", 50))
        offset = int(arguments.get("offset", 0))
        include_line_numbers = bool(arguments.get("-n", True))

        hits: list[str] = []
        for path in sorted(base.glob(file_glob)):
            if not path.is_file():
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if compiled.search(line):
                    rel = str(path.relative_to(self.workspace))
                    if include_line_numbers:
                        hits.append(f"{rel}:{line_number}:{line}")
                    else:
                        hits.append(f"{rel}:{line}")

        sliced = hits[offset: offset + head_limit]
        return {"ok": True, "matches": sliced, "count": len(sliced), "total_matches": len(hits)}

    def _exec_bash(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if arguments.get("run_in_background"):
            raise ToolExecutionError("background bash execution is not supported")
        if arguments.get("dangerouslyDisableSandbox"):
            raise ToolExecutionError("sandbox disabling is not supported")

        timeout = int(arguments.get("timeout", 30))
        result = subprocess.run(
            ["bash", "-lc", arguments["command"]],
            cwd=str(self.workspace),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "ok": result.returncode == 0,
            "command": arguments["command"],
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }