"""Tests for the main pipeline helper integrations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

import run as pipeline_run


class _FakeMissionControl:
    def __init__(self):
        self.events = []
        self.summary_merges = []

    def event(self, name, payload=None):
        self.events.append((name, payload))

    def merge_summary(self, patch):
        self.summary_merges.append(patch)


def test_run_redblue_stage_skips_when_disabled(tmp_path):
    result = pipeline_run.run_redblue_stage(tmp_path, plan="plan text", enabled=False)

    assert result is None


def test_run_redblue_stage_skips_when_no_diff(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline_run, "_current_diff", lambda project: "")

    result = pipeline_run.run_redblue_stage(tmp_path, plan="plan text", enabled=True)

    assert result is None


def test_run_redblue_stage_runs_red_and_blue(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline_run, "_current_diff", lambda project: "diff content")
    monkeypatch.setattr(pipeline_run, "run_red_team", lambda code, plan, workspace=None: "red output")
    monkeypatch.setattr(
        pipeline_run,
        "run_blue_team",
        lambda critic_output, code, plan, workspace=None: "blue output",
    )
    monkeypatch.setattr(pipeline_run, "stop_ollama_model", lambda model_name: None)
    monkeypatch.setattr(pipeline_run, "get_agent_model", lambda agent_id, workspace=None: f"model-{agent_id}")

    result = pipeline_run.run_redblue_stage(tmp_path, plan="plan text", enabled=True)

    assert result == {
        "red": "red output",
        "blue": "blue output",
        "diff": "diff content",
    }


def test_extract_blocker_findings_returns_only_blocker_sections():
    text = "INFO\n\nBLOCKER: fix auth\nDetails line\n\nIMPORTANT: later\n"

    result = pipeline_run.extract_blocker_findings(text)

    assert result == "BLOCKER: fix auth\nDetails line"


def test_parse_structured_review_findings_reads_tagged_json_block():
    text = (
        "notes\n"
        "<REVIEW_FINDINGS>\n"
        '{"findings":[{"severity":"BLOCKER","title":"Fix auth","location":"api.py:10","details":"Missing auth check"}]}'
        "\n</REVIEW_FINDINGS>"
    )

    result = pipeline_run.parse_structured_review_findings(text)

    assert result == [
        {
            "severity": "BLOCKER",
            "title": "Fix auth",
            "details": "Missing auth check",
            "location": "api.py:10",
        }
    ]


def test_extract_blocker_findings_prefers_structured_payload():
    text = (
        "BLOCKER: old heuristic\n\n"
        "<REVIEW_FINDINGS>\n"
        '{"findings":[{"severity":"BLOCKER","title":"Structured auth","location":"svc.py:7","details":"Use middleware"}]}'
        "\n</REVIEW_FINDINGS>"
    )

    result = pipeline_run.extract_blocker_findings(text)

    assert result == "BLOCKER: Structured auth\nLocation: svc.py:7\nUse middleware"


def test_run_redblue_autofix_stage_skips_without_blockers(tmp_path):
    result = pipeline_run.run_redblue_autofix_stage(
        tmp_path,
        adapter_id="python-pytest",
        context="ctx",
        task="task",
        plan="plan",
        redblue_review={"red": "IMPORTANT: x", "blue": "NICE: y", "diff": "diff"},
        rag=None,
        rag_k=6,
        enabled=True,
    )

    assert result is None


def test_run_redblue_autofix_stage_runs_implementer_for_blockers(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline_run, "run_agent", lambda *args, **kwargs: "diff patch")
    monkeypatch.setattr(pipeline_run, "git_apply", lambda project, diff: (True, "ok"))
    monkeypatch.setattr(pipeline_run, "validate_project_changes", lambda project, adapter_id: (True, "ok"))
    monkeypatch.setattr(pipeline_run, "stop_ollama_model", lambda model_name: None)
    monkeypatch.setattr(pipeline_run, "get_agent_model", lambda agent_id, workspace=None: "implementer-model")

    result = pipeline_run.run_redblue_autofix_stage(
        tmp_path,
        adapter_id="python-pytest",
        context="ctx",
        task="task",
        plan="plan",
        redblue_review={"red": "BLOCKER: fix auth\nDetails", "blue": "", "diff": "diff"},
        rag=None,
        rag_k=6,
        enabled=True,
    )

    assert result == {"blockers": "BLOCKER: fix auth\nDetails", "diff": "diff patch"}


def test_build_reviewer_task_includes_structured_contract_and_context():
    result = pipeline_run.build_reviewer_task(
        redblue_review={"red": "red text", "blue": "blue text", "diff": "diff text"},
        redblue_autofix={"blockers": "BLOCKER: fix auth", "diff": "patch"},
        changed_paths=["src/app.py", "tests/test_app.py"],
    )

    assert "<REVIEW_FINDINGS>" in result
    assert '"severity":"BLOCKER|IMPORTANT|NICE"' in result
    assert "Changed paths under review:" in result
    assert "- src/app.py" in result
    assert "RED TEAM:\nred text" in result
    assert "BLUE TEAM:\nblue text" in result
    assert "AUTOFIX BLOCKERS:\nBLOCKER: fix auth" in result


def test_build_implementer_task_includes_candidate_paths_and_constraints():
    result = pipeline_run.build_implementer_task(
        task="fix failing test",
        plan="plan",
        diagnosis="diag",
        logs="logs",
        changed_paths=["src/app.py", "tests/test_app.py"],
    )

    assert "Output ONLY a unified diff patch" in result
    assert "Do not create parallel structures" in result
    assert "CANDIDATE PATHS:" in result
    assert "- src/app.py" in result


def test_record_agent_manifest_updates_mission_control(tmp_path, monkeypatch):
    fake_mc = _FakeMissionControl()
    monkeypatch.setattr(
        pipeline_run,
        "get_agent_status",
        lambda agent, workspace: type(
            "Manifest",
            (),
            {
                "run_id": "run-1",
                "agent_id": agent,
                "model": "fake-model",
                "workspace": str(workspace),
                "status": "completed",
                "output_file": str(workspace / ".agent_store" / f"{agent}.out.txt"),
                "error": "",
                "created_at": 1.0,
                "started_at": 1.0,
                "completed_at": 2.0,
            },
        )(),
    )

    payload = pipeline_run._record_agent_manifest(fake_mc, "planner", tmp_path)

    assert payload is not None
    assert payload["agent_id"] == "planner"
    assert fake_mc.events[0][0] == "agent_manifest"
    assert fake_mc.summary_merges[0]["agents"]["planner"]["run_id"] == "run-1"


def test_run_agent_records_manifest_to_mission_control(tmp_path, monkeypatch):
    fake_mc = _FakeMissionControl()
    captured = {}

    def fake_sh(cmd, cwd, timeout=None):
        captured["cmd"] = cmd
        return type("Result", (), {"returncode": 0, "stdout": "agent output", "stderr": ""})()

    monkeypatch.setattr(pipeline_run, "sh", fake_sh)
    monkeypatch.setattr(
        pipeline_run,
        "get_agent_status",
        lambda agent, workspace: type(
            "Manifest",
            (),
            {
                "run_id": "run-1",
                "agent_id": agent,
                "model": "fake-model",
                "workspace": str(workspace),
                "status": "completed",
                "output_file": str(workspace / ".agent_store" / f"{agent}.out.txt"),
                "error": "",
                "created_at": 1.0,
                "started_at": 1.0,
                "completed_at": 2.0,
            },
        )(),
    )

    result = pipeline_run.run_agent(
        "planner",
        "task",
        context="ctx",
        workspace=tmp_path,
        mission_control=fake_mc,
        permission_mode="strict",
    )

    assert result == "agent output"
    assert "--permission-mode" in captured["cmd"]
    assert "strict" in captured["cmd"]
    assert fake_mc.events[0][0] == "agent_manifest"
    assert fake_mc.events[0][1]["agent_id"] == "planner"
    assert fake_mc.summary_merges[0]["agents"]["planner"]["status"] == "completed"
    assert fake_mc.summary_merges[0]["agent_outputs"]["planner"]["output_file"].endswith("planner.out.txt")
    assert "preview" in fake_mc.summary_merges[0]["agent_outputs"]["planner"]