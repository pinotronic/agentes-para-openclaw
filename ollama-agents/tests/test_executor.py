"""Tests for the runtime tool executor."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.executor import (
    ToolExecutor,
    ToolPermissionError,
    ToolValidationError,
    parse_tool_call,
)


@pytest.fixture(autouse=True)
def strict_runtime_permissions(monkeypatch):
    monkeypatch.setenv("OLLAMA_AGENT_PERMISSION_MODE", "strict")


def test_parse_tool_call_from_tagged_block():
    call = parse_tool_call(
        '<TOOL_CALL>\n{"tool": "read", "arguments": {"path": "README.md"}}\n</TOOL_CALL>'
    )

    assert call is not None
    assert call.tool == "read"
    assert call.arguments == {"path": "README.md"}


def test_parse_tool_call_rejects_invalid_json():
    with pytest.raises(ToolValidationError, match="invalid tool call JSON"):
        parse_tool_call("<TOOL_CALL>{bad json}</TOOL_CALL>")


def test_executor_reads_file_inside_workspace(tmp_path):
    (tmp_path / "notes.txt").write_text("a\nb\nc\n", encoding="utf-8")
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call('<TOOL_CALL>{"tool":"read_file","arguments":{"path":"notes.txt","offset":1,"limit":1}}</TOOL_CALL>')
    )

    assert result["ok"] is True
    assert result["content"] == "b"
    assert result["path"] == "notes.txt"


def test_executor_rejects_disallowed_tool(tmp_path):
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    with pytest.raises(ToolPermissionError, match="not allowed"):
        executor.execute(
            parse_tool_call('<TOOL_CALL>{"tool":"bash","arguments":{"command":"pwd"}}</TOOL_CALL>')
        )


def test_executor_allows_bash_in_permissive_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("OLLAMA_AGENT_PERMISSION_MODE", "permissive")
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call('<TOOL_CALL>{"tool":"bash","arguments":{"command":"pwd"}}</TOOL_CALL>')
    )

    assert result["ok"] is True


def test_executor_explicit_permissive_mode_overrides_persisted_strict(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_AGENT_PERMISSION_MODE", raising=False)
    config_dir = tmp_path / ".openclaw"
    config_dir.mkdir(parents=True)
    (config_dir / "ollama-agents.json").write_text('{"permission_mode": "strict"}', encoding="utf-8")

    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path, explicit_mode="permissive")

    result = executor.execute(
        parse_tool_call('<TOOL_CALL>{"tool":"bash","arguments":{"command":"pwd"}}</TOOL_CALL>')
    )

    assert result["ok"] is True


def test_executor_rejects_path_escape(tmp_path):
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    with pytest.raises(Exception, match="escapes workspace"):
        executor.execute(
            parse_tool_call('<TOOL_CALL>{"tool":"read_file","arguments":{"path":"../../etc/passwd"}}</TOOL_CALL>')
        )


def test_executor_write_file_creates_parent_dirs(tmp_path):
    executor = ToolExecutor(agent_id="test_writer", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call(
            '<TOOL_CALL>{"tool":"write_file","arguments":{"path":"tests/unit/new_test.py","content":"assert True\\n"}}</TOOL_CALL>'
        )
    )

    assert result["ok"] is True
    assert (tmp_path / "tests" / "unit" / "new_test.py").read_text(encoding="utf-8") == "assert True\n"


def test_executor_edit_file_replaces_single_match(tmp_path):
    (tmp_path / "module.py").write_text("value = 1\n", encoding="utf-8")
    executor = ToolExecutor(agent_id="implementer", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call(
            '<TOOL_CALL>{"tool":"edit_file","arguments":{"path":"module.py","old_string":"1","new_string":"2"}}</TOOL_CALL>'
        )
    )

    assert result["ok"] is True
    assert result["replacements"] == 1
    assert (tmp_path / "module.py").read_text(encoding="utf-8") == "value = 2\n"


def test_executor_edit_file_requires_replace_all_for_multiple_matches(tmp_path):
    (tmp_path / "module.py").write_text("x\nx\n", encoding="utf-8")
    executor = ToolExecutor(agent_id="implementer", workspace=tmp_path)

    with pytest.raises(Exception, match="replace_all=true"):
        executor.execute(
            parse_tool_call(
                '<TOOL_CALL>{"tool":"edit_file","arguments":{"path":"module.py","old_string":"x","new_string":"y"}}</TOOL_CALL>'
            )
        )


def test_executor_edit_file_can_replace_all_matches(tmp_path):
    (tmp_path / "module.py").write_text("x\nx\n", encoding="utf-8")
    executor = ToolExecutor(agent_id="implementer", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call(
            '<TOOL_CALL>{"tool":"edit_file","arguments":{"path":"module.py","old_string":"x","new_string":"y","replace_all":true}}</TOOL_CALL>'
        )
    )

    assert result["ok"] is True
    assert result["replacements"] == 2
    assert (tmp_path / "module.py").read_text(encoding="utf-8") == "y\ny\n"


def test_executor_rejects_edit_for_agent_without_permission(tmp_path):
    (tmp_path / "module.py").write_text("value = 1\n", encoding="utf-8")
    executor = ToolExecutor(agent_id="test_writer", workspace=tmp_path)

    with pytest.raises(ToolPermissionError, match="not allowed"):
        executor.execute(
            parse_tool_call(
                '<TOOL_CALL>{"tool":"edit_file","arguments":{"path":"module.py","old_string":"1","new_string":"2"}}</TOOL_CALL>'
            )
        )


def test_executor_rejects_wrong_argument_type(tmp_path):
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    with pytest.raises(ToolValidationError, match="offset must be of type integer"):
        executor.execute(
            parse_tool_call(
                '<TOOL_CALL>{"tool":"read_file","arguments":{"path":"notes.txt","offset":"1"}}</TOOL_CALL>'
            )
        )


def test_executor_rejects_integer_below_minimum(tmp_path):
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    with pytest.raises(ToolValidationError, match="limit must be >= 1"):
        executor.execute(
            parse_tool_call(
                '<TOOL_CALL>{"tool":"read_file","arguments":{"path":"notes.txt","limit":0}}</TOOL_CALL>'
            )
        )


def test_executor_rejects_invalid_enum_value(tmp_path):
    executor = ToolExecutor(agent_id="planner", workspace=tmp_path)

    with pytest.raises(ToolValidationError, match=r"todos\[0\]\.status must be one of"):
        executor.execute(
            parse_tool_call(
                '<TOOL_CALL>{"tool":"TodoWrite","arguments":{"todos":[{"content":"x","activeForm":"doing x","status":"doing"}]}}</TOOL_CALL>'
            )
        )


def test_executor_rejects_invalid_uri_format(tmp_path):
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    with pytest.raises(ToolValidationError, match="url must be a valid URI"):
        executor.execute(
            parse_tool_call(
                '<TOOL_CALL>{"tool":"WebFetch","arguments":{"url":"example.com","prompt":"summarize"}}</TOOL_CALL>'
            )
        )


def test_executor_tool_search_returns_matches(tmp_path):
    executor = ToolExecutor(agent_id="code_critic", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call(
            '<TOOL_CALL>{"tool":"ToolSearch","arguments":{"query":"search tools","max_results":3}}</TOOL_CALL>'
        )
    )

    assert result["ok"] is True
    assert result["count"] >= 1
    assert any(match["name"] == "ToolSearch" for match in result["matches"])


def test_executor_skill_loads_project_skill(tmp_path):
    skill_dir = tmp_path / ".openclaw" / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Demo skill\n---\nSkill body\n",
        encoding="utf-8",
    )
    executor = ToolExecutor(agent_id="planner", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call(
            '<TOOL_CALL>{"tool":"Skill","arguments":{"skill":"demo-skill"}}</TOOL_CALL>'
        )
    )

    assert result["ok"] is True
    assert result["skill"] == "demo-skill"
    assert result["source"] == "project-openclaw"
    assert "Skill body" in result["content"]


def test_executor_uses_project_policy_override_for_bash(tmp_path):
    agent_dir = tmp_path / ".openclaw" / "agents"
    agent_dir.mkdir(parents=True)
    (agent_dir / "reviewer.yaml").write_text(
        "id: reviewer\n"
        "model: local-reviewer\n"
        "system: local reviewer\n"
        "permissions:\n"
        "  inherit: true\n"
        "  add_allowed_tools:\n"
        "    - bash\n",
        encoding="utf-8",
    )
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call('<TOOL_CALL>{"tool":"bash","arguments":{"command":"pwd"}}</TOOL_CALL>')
    )

    assert result["ok"] is True


def test_executor_pre_tool_hook_can_deny_execution(tmp_path):
    agent_dir = tmp_path / ".openclaw" / "agents"
    agent_dir.mkdir(parents=True)
    (agent_dir / "reviewer.yaml").write_text(
        "id: reviewer\n"
        "model: local-reviewer\n"
        "system: local reviewer\n"
        "permissions:\n"
        "  inherit: true\n"
        "  add_allowed_tools:\n"
        "    - bash\n"
        "hooks:\n"
        "  pre_tool_use:\n"
        "    - 'echo blocked by hook >&2; exit 1'\n",
        encoding="utf-8",
    )
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    with pytest.raises(ToolPermissionError, match="blocked by hook"):
        executor.execute(
            parse_tool_call('<TOOL_CALL>{"tool":"bash","arguments":{"command":"pwd"}}</TOOL_CALL>')
        )


def test_executor_post_tool_hook_adds_messages(tmp_path):
    agent_dir = tmp_path / ".openclaw" / "agents"
    agent_dir.mkdir(parents=True)
    (agent_dir / "reviewer.yaml").write_text(
        "id: reviewer\n"
        "model: local-reviewer\n"
        "system: local reviewer\n"
        "permissions:\n"
        "  inherit: true\n"
        "hooks:\n"
        "  post_tool_use:\n"
        "    - 'echo post hook ok'\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.txt").write_text("hello\n", encoding="utf-8")
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call('<TOOL_CALL>{"tool":"read_file","arguments":{"path":"notes.txt"}}</TOOL_CALL>')
    )

    assert result["ok"] is True
    assert "hook_messages" in result
    assert any("post hook ok" in message for message in result["hook_messages"])


def test_executor_project_hook_file_can_deny_execution(tmp_path):
    agent_dir = tmp_path / ".openclaw" / "agents"
    hook_dir = tmp_path / ".openclaw" / "hooks"
    agent_dir.mkdir(parents=True)
    hook_dir.mkdir(parents=True)
    (agent_dir / "reviewer.yaml").write_text(
        "id: reviewer\n"
        "model: local-reviewer\n"
        "system: local reviewer\n"
        "permissions:\n"
        "  inherit: true\n"
        "  add_allowed_tools:\n"
        "    - bash\n",
        encoding="utf-8",
    )
    (hook_dir / "reviewer.yaml").write_text(
        "inherit: false\n"
        "pre_tool_use:\n"
        "  - 'echo denied from project hook >&2; exit 1'\n",
        encoding="utf-8",
    )
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    with pytest.raises(ToolPermissionError, match="denied from project hook"):
        executor.execute(
            parse_tool_call('<TOOL_CALL>{"tool":"bash","arguments":{"command":"pwd"}}</TOOL_CALL>')
        )


def test_executor_project_hook_file_can_append_post_hook(tmp_path):
    agent_dir = tmp_path / ".openclaw" / "agents"
    hook_dir = tmp_path / ".openclaw" / "hooks"
    agent_dir.mkdir(parents=True)
    hook_dir.mkdir(parents=True)
    (agent_dir / "reviewer.yaml").write_text(
        "id: reviewer\n"
        "model: local-reviewer\n"
        "system: local reviewer\n",
        encoding="utf-8",
    )
    (hook_dir / "reviewer.yaml").write_text(
        "add_post_tool_use:\n"
        "  - 'echo post from file hook'\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.txt").write_text("hello\n", encoding="utf-8")
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    result = executor.execute(
        parse_tool_call('<TOOL_CALL>{"tool":"read_file","arguments":{"path":"notes.txt"}}</TOOL_CALL>')
    )

    assert result["ok"] is True
    assert any("post from file hook" in message for message in result.get("hook_messages", []))


def test_executor_web_fetch_returns_text_content(tmp_path, monkeypatch):
    executor = ToolExecutor(agent_id="reviewer", workspace=tmp_path)

    class FakeResponse:
        def __init__(self):
            self.headers = {"Content-Type": "text/html; charset=utf-8"}
            self.status = 200

        def read(self, limit):
            return b"<html><body><h1>Hello</h1><p>World</p></body></html>"

        def getcode(self):
            return self.status

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("agents.executor.urlopen", lambda request, timeout: FakeResponse())

    result = executor.execute(
        parse_tool_call(
            '<TOOL_CALL>{"tool":"WebFetch","arguments":{"url":"https://example.com","prompt":"summarize"}}</TOOL_CALL>'
        )
    )

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert "Hello" in result["content"]
    assert "World" in result["content"]


def test_executor_web_search_returns_filtered_results(tmp_path, monkeypatch):
    executor = ToolExecutor(agent_id="planner", workspace=tmp_path)

    html_doc = """
    <html><body>
      <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fallowed.example%2Fpost">Allowed Result</a>
      <a class="result__a" href="https://blocked.example/post">Blocked Result</a>
    </body></html>
    """

    class FakeResponse:
        def __init__(self):
            self.status = 200

        def read(self, limit):
            return html_doc.encode("utf-8")

        def getcode(self):
            return self.status

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("agents.executor.urlopen", lambda request, timeout: FakeResponse())

    result = executor.execute(
        parse_tool_call(
            '<TOOL_CALL>{"tool":"WebSearch","arguments":{"query":"agent tools","allowed_domains":["allowed.example"],"blocked_domains":["blocked.example"]}}</TOOL_CALL>'
        )
    )

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["count"] == 1
    assert result["results"][0]["domain"] == "allowed.example"
    assert result["results"][0]["url"] == "https://allowed.example/post"