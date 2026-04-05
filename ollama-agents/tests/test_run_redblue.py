"""Tests for red/blue pipeline runtime tool integration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import run_redblue


def test_run_red_team_uses_runtime_tool_support(tmp_path, monkeypatch):
    monkeypatch.setattr(run_redblue, "validate_agent_policy", lambda agent_id, workspace=None: None)
    monkeypatch.setattr(
        run_redblue,
        "load_profile",
        lambda agent_id, workspace=None: {"model": "fake-model", "system": "system prompt"},
    )

    captured: dict[str, object] = {}

    def fake_run_with_tool_support(*, agent_id, model, prompt, workspace, retries, timeout):
        captured["agent_id"] = agent_id
        captured["model"] = model
        captured["prompt"] = prompt
        captured["workspace"] = workspace
        captured["retries"] = retries
        captured["timeout"] = timeout
        return "critic result"

    monkeypatch.setattr(run_redblue, "run_with_tool_support", fake_run_with_tool_support)

    result = run_redblue.run_red_team("print('ok')", "plan text", workspace=tmp_path)

    assert result == "critic result"
    assert captured["agent_id"] == "code_critic"
    assert captured["workspace"] == tmp_path
    assert captured["model"] == "fake-model"
    assert "CÓDIGO A REVISAR" in captured["prompt"]