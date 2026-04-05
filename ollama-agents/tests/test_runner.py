"""Tests for runtime policy enforcement in the Ollama runner."""

import os
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from runner import ollama_agent
from runner.ollama_agent import (
    build_policy_context,
    build_prompt,
    detect_degenerate_output,
    get_required_paths,
    get_tool_max_rounds,
    get_verify_commands,
    load_profile,
    render_agent_discovery,
    render_agent_status,
    render_skill_discovery,
    run_verification_commands,
    check_stream_idle,
    update_degenerate_stream_window,
    run_with_tool_support,
    validate_model_output,
    validate_agent_policy,
    verify_required_paths,
)
from agents.manifest import complete_manifest, start_manifest
from agents.manifest import load_manifest
from runner.permission_mode_store import resolve_permission_mode, save_permission_mode
from runner.session_store import compact_transcript, load_session


@pytest.fixture(autouse=True)
def strict_runtime_permissions(monkeypatch):
    monkeypatch.setenv("OLLAMA_AGENT_PERMISSION_MODE", "strict")


def test_build_policy_context_uses_canonical_tool_names():
    context = build_policy_context("implementer")

    assert "Agent: implementer" in context
    assert "- bash: danger_full_access" in context
    assert "BashTool" not in context
    assert "- websearch" not in context


def test_build_policy_context_in_permissive_mode(monkeypatch):
    monkeypatch.setenv("OLLAMA_AGENT_PERMISSION_MODE", "permissive")

    context = build_policy_context("unknown_agent")

    assert "Runtime permission mode: permissive" in context
    assert "Allowed tools:" in context
    assert "- bash: danger_full_access" in context


def test_build_prompt_includes_policy_section():
    prompt = build_prompt(
        agent_id="reviewer",
        system="system prompt",
        context="repo context",
        task="review the diff",
    )

    assert "<POLICY>" in prompt
    assert "Agent: reviewer" in prompt
    assert "<TASK>\nreview the diff\n</TASK>" in prompt


def test_validate_agent_policy_rejects_unknown_agent():
    with pytest.raises(SystemExit, match="no explicit permission policy"):
        validate_agent_policy("unknown_agent")


def test_validate_agent_policy_allows_unknown_agent_in_explicit_permissive_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("OLLAMA_AGENT_PERMISSION_MODE", "strict")

    validate_agent_policy("unknown_agent", tmp_path, "permissive")


def test_all_agent_profiles_have_explicit_policy_and_loadable_profile():
    agents_dir = Path(__file__).parent.parent / "agents"
    profile_ids = sorted(path.stem for path in agents_dir.glob("*.yaml"))

    assert profile_ids, "Expected at least one agent profile"
    for agent_id in profile_ids:
        validate_agent_policy(agent_id)
        profile = ollama_agent.load_profile(agent_id)
        assert profile.get("id") == agent_id
        assert isinstance(profile.get("model"), str) and profile["model"].strip()
        assert isinstance(profile.get("system"), str) and profile["system"].strip()


def test_load_profile_prefers_project_override(tmp_path):
    override_dir = tmp_path / ".openclaw" / "agents"
    override_dir.mkdir(parents=True)
    (override_dir / "planner.yaml").write_text(
        "id: planner\nmodel: local-override\nsystem: project planner\n",
        encoding="utf-8",
    )

    profile = load_profile("planner", tmp_path)

    assert profile["model"] == "local-override"
    assert profile["system"] == "project planner"


def test_get_tool_max_rounds_reads_positive_integer_from_profile():
    value = get_tool_max_rounds({"tool_max_rounds": 9})

    assert value == 9


def test_get_tool_max_rounds_uses_default_when_missing():
    value = get_tool_max_rounds({})

    assert value == ollama_agent.OLLAMA_TOOL_MAX_ROUNDS


def test_get_tool_max_rounds_rejects_invalid_value():
    with pytest.raises(SystemExit, match="Invalid tool_max_rounds value"):
        get_tool_max_rounds({"tool_max_rounds": "abc"})


def test_get_verify_commands_reads_string_list():
    value = get_verify_commands({"verify_commands": ["npm run build", "npm test"]})

    assert value == ["npm run build", "npm test"]


def test_get_verify_commands_rejects_invalid_value():
    with pytest.raises(SystemExit, match="verify_commands must be a list of strings"):
        get_verify_commands({"verify_commands": "npm run build"})


def test_get_required_paths_reads_string_list():
    value = get_required_paths({"required_paths": ["src/foo.ts", "src/bar.test.ts"]})

    assert value == ["src/foo.ts", "src/bar.test.ts"]


def test_get_required_paths_rejects_invalid_value():
    with pytest.raises(SystemExit, match="required_paths must be a list of strings"):
        get_required_paths({"required_paths": "src/foo.ts"})


def test_detect_degenerate_output_flags_repetitive_text(monkeypatch):
    monkeypatch.setattr(ollama_agent, "DEGENERATE_OUTPUT_MIN_CHARS", 20)

    issue = detect_degenerate_output("y" * 40)

    assert issue is not None
    assert "degenerate/repetitive" in issue


def test_detect_degenerate_output_ignores_normal_text(monkeypatch):
    monkeypatch.setattr(ollama_agent, "DEGENERATE_OUTPUT_MIN_CHARS", 20)

    issue = detect_degenerate_output("Diagnostico concreto con varias palabras y estructura util")

    assert issue is None


def test_validate_model_output_raises_on_degenerate_text(monkeypatch):
    monkeypatch.setattr(ollama_agent, "DEGENERATE_OUTPUT_MIN_CHARS", 20)

    with pytest.raises(SystemExit, match="degenerate/repetitive"):
        validate_model_output("y" * 40)


def test_update_degenerate_stream_window_detects_repetition(monkeypatch):
    monkeypatch.setattr(ollama_agent, "DEGENERATE_OUTPUT_MIN_CHARS", 20)
    monkeypatch.setattr(ollama_agent, "DEGENERATE_OUTPUT_STREAM_WINDOW", 64)

    window = ""
    issue = None
    for chunk in ["yyyyy", "yyyyy", "yyyyy", "yyyyy"]:
        window, issue = update_degenerate_stream_window(window, chunk)

    assert issue is not None
    assert "degenerate/repetitive" in issue


def test_update_degenerate_stream_window_keeps_normal_text_clean(monkeypatch):
    monkeypatch.setattr(ollama_agent, "DEGENERATE_OUTPUT_MIN_CHARS", 20)
    monkeypatch.setattr(ollama_agent, "DEGENERATE_OUTPUT_STREAM_WINDOW", 64)

    window = ""
    issue = None
    for chunk in ["Diagnostico ", "con texto ", "normal y util"]:
        window, issue = update_degenerate_stream_window(window, chunk)

    assert issue is None


def test_check_stream_idle_raises_after_threshold(monkeypatch):
    monkeypatch.setattr(ollama_agent, "OLLAMA_STREAM_IDLE_TIMEOUT", 5.0)

    with pytest.raises(RuntimeError, match="stream idle timeout"):
        check_stream_idle(10.0, 15.5)


def test_check_stream_idle_allows_recent_output(monkeypatch):
    monkeypatch.setattr(ollama_agent, "OLLAMA_STREAM_IDLE_TIMEOUT", 5.0)

    check_stream_idle(10.0, 14.0)


def test_run_verification_commands_succeeds(tmp_path):
    results = run_verification_commands(["python3 -c \"print('ok')\""], tmp_path, timeout=10)

    assert results[0]["returncode"] == 0
    assert results[0]["stdout"] == "ok"


def test_run_verification_commands_fails_on_non_zero_exit(tmp_path):
    with pytest.raises(SystemExit, match="Verification failed"):
        run_verification_commands(["python3 -c \"import sys; sys.exit(3)\""], tmp_path, timeout=10)


def test_verify_required_paths_succeeds(tmp_path):
    file_path = tmp_path / "src" / "game" / "logic" / "demo.ts"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("export const demo = true\n", encoding="utf-8")

    verified = verify_required_paths(["src/game/logic/demo.ts"], tmp_path)

    assert verified == ["src/game/logic/demo.ts"]


def test_verify_required_paths_fails_when_missing(tmp_path):
    with pytest.raises(SystemExit, match="Required path verification failed"):
        verify_required_paths(["src/game/logic/missing.ts"], tmp_path)


def test_render_agent_discovery_includes_core_agents(tmp_path):
    output = render_agent_discovery(tmp_path)

    assert "planner" in output
    assert "[core]" in output


def test_render_skill_discovery_prefers_project_skill(tmp_path):
    skill_dir = tmp_path / ".openclaw" / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Project skill\n---\nBody\n",
        encoding="utf-8",
    )

    output = render_skill_discovery(tmp_path)

    assert "demo-skill [project-openclaw]" in output
    assert "Project skill" in output


def test_render_agent_status_reads_latest_manifest(tmp_path):
    manifest_path, manifest = start_manifest("reviewer", "fake-model", tmp_path)
    complete_manifest(manifest_path, manifest, "review output")

    output = render_agent_status("reviewer", tmp_path)

    assert "Agent status: reviewer" in output
    assert "status: completed" in output
    assert "output_file:" in output


def test_render_agent_status_can_include_output(tmp_path):
    manifest_path, manifest = start_manifest("planner", "fake-model", tmp_path)
    complete_manifest(manifest_path, manifest, "planner output body")

    output = render_agent_status("planner", tmp_path, include_output=True)

    assert "output:" in output
    assert "planner output body" in output


def test_build_policy_context_uses_project_policy_override(tmp_path):
    override_dir = tmp_path / ".openclaw" / "agents"
    override_dir.mkdir(parents=True)
    (override_dir / "reviewer.yaml").write_text(
        "id: reviewer\n"
        "model: local-reviewer\n"
        "system: local reviewer\n"
        "permissions:\n"
        "  inherit: true\n"
        "  add_allowed_tools:\n"
        "    - bash\n",
        encoding="utf-8",
    )

    context = build_policy_context("reviewer", tmp_path)

    assert "- bash: danger_full_access" in context


def test_validate_agent_policy_accepts_local_agent_with_permissions(tmp_path):
    local_dir = tmp_path / ".openclaw" / "agents"
    local_dir.mkdir(parents=True)
    (local_dir / "local_helper.yaml").write_text(
        "id: local_helper\n"
        "model: helper-model\n"
        "system: helper\n"
        "permissions:\n"
        "  inherit: false\n"
        "  allowed_tools:\n"
        "    - read_file\n",
        encoding="utf-8",
    )

    validate_agent_policy("local_helper", tmp_path)


def test_run_with_tool_support_executes_tool_and_returns_final_text(tmp_path, monkeypatch):
    (tmp_path / "context.txt").write_text("tool result\n", encoding="utf-8")
    outputs = iter([
        '<TOOL_CALL>\n{"tool":"read_file","arguments":{"path":"context.txt"}}\n</TOOL_CALL>',
        'final answer after tool',
    ])
    prompts: list[str] = []

    def fake_run(model, prompt, retries, timeout):
        prompts.append(prompt)
        return next(outputs)

    monkeypatch.setattr(ollama_agent, "run_ollama_with_retry", fake_run)

    result = run_with_tool_support(
        agent_id="reviewer",
        model="fake",
        prompt="base prompt",
        workspace=tmp_path,
        retries=1,
        timeout=5,
        max_rounds=2,
    )

    assert result == "final answer after tool"
    assert any("TOOL_RESULT" in prompt for prompt in prompts[1:])
    assert any("tool result" in prompt for prompt in prompts[1:])


def test_run_with_tool_support_persists_session(tmp_path, monkeypatch):
    session_file = tmp_path / "session.json"

    monkeypatch.setattr(ollama_agent, "run_ollama_with_retry", lambda model, prompt, retries, timeout: "final answer")

    result = run_with_tool_support(
        agent_id="reviewer",
        model="fake",
        prompt="base prompt",
        workspace=tmp_path,
        retries=1,
        timeout=5,
        session_file=session_file,
        resume_session=False,
        compact_session=False,
        max_rounds=1,
    )

    saved = load_session(session_file)
    assert result == "final answer"
    assert saved.final_output == "final answer"
    assert saved.agent_id == "reviewer"


def test_run_with_tool_support_rejects_degenerate_final_output(tmp_path, monkeypatch):
    monkeypatch.setattr(ollama_agent, "DEGENERATE_OUTPUT_MIN_CHARS", 20)
    monkeypatch.setattr(ollama_agent, "run_ollama_with_retry", lambda model, prompt, retries, timeout: "y" * 40)

    with pytest.raises(SystemExit, match="degenerate/repetitive"):
        run_with_tool_support(
            agent_id="reviewer",
            model="fake",
            prompt="base prompt",
            workspace=tmp_path,
            retries=1,
            timeout=5,
            max_rounds=1,
        )


def test_main_marks_manifest_error_on_keyboard_interrupt(tmp_path, monkeypatch):
    monkeypatch.setenv("OLLAMA_AGENT_PERMISSION_MODE", "strict")

    def fake_load_profile(agent_id, workspace=None):
        return {"id": agent_id, "model": "fake-model", "system": "system prompt"}

    def fake_run_with_tool_support(**kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(ollama_agent, "load_profile", fake_load_profile)
    monkeypatch.setattr(ollama_agent, "run_with_tool_support", fake_run_with_tool_support)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ollama_agent.py",
            "--agent",
            "reviewer",
            "--workspace",
            str(tmp_path),
            "--input",
            "trigger interrupt",
        ],
    )

    with pytest.raises(KeyboardInterrupt):
        ollama_agent.main()

    latest_path = tmp_path / ".agent_store" / "latest" / "reviewer.json"
    saved = load_manifest(latest_path)
    assert saved.status == "error"
    assert saved.error == "Runner interrupted by user"


def test_compact_transcript_preserves_recent_tail():
    transcript = "A" * 200 + "<TOOL_RESULT>recent</TOOL_RESULT>"

    compacted = compact_transcript(transcript, max_chars=80, preserve_tail_chars=30)

    assert "<COMPACTED_HISTORY>" in compacted
    assert compacted.endswith("<TOOL_RESULT>recent</TOOL_RESULT>")


def test_resolve_permission_mode_prefers_project_config(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_AGENT_PERMISSION_MODE", raising=False)
    save_permission_mode("strict", workspace=tmp_path, scope="project")

    mode, source, path = resolve_permission_mode(tmp_path)

    assert mode == "strict"
    assert source == "project"
    assert path == tmp_path / ".openclaw" / "ollama-agents.json"


def test_resolve_permission_mode_cli_overrides_persisted_mode(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_AGENT_PERMISSION_MODE", raising=False)
    save_permission_mode("strict", workspace=tmp_path, scope="project")

    mode, source, path = resolve_permission_mode(tmp_path, "permissive")

    assert mode == "permissive"
    assert source == "cli"
    assert path is None


def test_build_policy_context_uses_persisted_permission_mode(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_AGENT_PERMISSION_MODE", raising=False)
    save_permission_mode("strict", workspace=tmp_path, scope="project")

    context = build_policy_context("reviewer", tmp_path)

    assert "Runtime permission mode: strict" in context


def test_build_policy_context_respects_explicit_permissive_override_over_persisted_strict(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_AGENT_PERMISSION_MODE", raising=False)
    save_permission_mode("strict", workspace=tmp_path, scope="project")

    context = build_policy_context("unknown_agent", tmp_path, "permissive")

    assert "Runtime permission mode: permissive" in context