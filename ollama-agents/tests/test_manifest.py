"""Tests for per-agent manifest persistence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.manifest import (
    complete_manifest,
    get_agent_status,
    get_manifest_by_run_id,
    list_manifests,
    load_manifest,
    manifest_summary,
    output_preview,
    prune_manifests,
    start_manifest,
)
from runner.agent_store import render_manifest_detail, render_manifest_list


def test_manifest_persists_completed_output(tmp_path):
    manifest_path, manifest = start_manifest("planner", "fake-model", tmp_path)

    complete_manifest(manifest_path, manifest, "final planner output")
    saved = load_manifest(manifest_path)

    assert saved.agent_id == "planner"
    assert saved.status == "completed"
    assert Path(saved.output_file).read_text(encoding="utf-8") == "final planner output"


def test_get_agent_status_reads_latest_manifest(tmp_path):
    manifest_path, manifest = start_manifest("reviewer", "fake-model", tmp_path)

    complete_manifest(manifest_path, manifest, "review result")
    latest = get_agent_status("reviewer", tmp_path)

    assert latest is not None
    assert latest.agent_id == "reviewer"
    assert latest.status == "completed"
    assert latest.output_file.endswith("-reviewer.out.txt")


def test_get_agent_status_recovers_when_latest_pointer_is_stale(tmp_path):
    first_path, first = start_manifest("implementer", "model-a", tmp_path)
    complete_manifest(first_path, first, "first result")

    second_path, second = start_manifest("implementer", "model-a", tmp_path)
    complete_manifest(second_path, second, "second result")

    stale_payload = Path(first_path).read_text(encoding="utf-8")
    latest_path = tmp_path / ".agent_store" / "latest" / "implementer.json"
    latest_path.write_text(stale_payload, encoding="utf-8")

    latest = get_agent_status("implementer", tmp_path)

    assert latest is not None
    assert latest.run_id == second.run_id
    assert latest.status == "completed"
    assert load_manifest(latest_path).run_id == second.run_id


def test_manifest_summary_returns_serializable_fields(tmp_path):
    manifest_path, manifest = start_manifest("planner", "fake-model", tmp_path)

    complete_manifest(manifest_path, manifest, "done")
    summary = manifest_summary(load_manifest(manifest_path))

    assert summary["agent_id"] == "planner"
    assert summary["status"] == "completed"
    assert summary["output_file"].endswith("-planner.out.txt")


def test_list_manifests_returns_latest_first_and_filters_by_agent(tmp_path):
    first_path, first = start_manifest("planner", "model-a", tmp_path)
    complete_manifest(first_path, first, "first")
    second_path, second = start_manifest("reviewer", "model-b", tmp_path)
    complete_manifest(second_path, second, "second")

    all_manifests = list_manifests(tmp_path)
    planner_only = list_manifests(tmp_path, agent_id="planner")

    assert [item.agent_id for item in all_manifests] == ["reviewer", "planner"]
    assert [item.agent_id for item in planner_only] == ["planner"]


def test_get_manifest_by_run_id_returns_matching_manifest(tmp_path):
    manifest_path, manifest = start_manifest("reviewer", "fake-model", tmp_path)
    complete_manifest(manifest_path, manifest, "review output")

    found = get_manifest_by_run_id(tmp_path, manifest.run_id, agent_id="reviewer")

    assert found is not None
    assert found.run_id == manifest.run_id
    assert found.agent_id == "reviewer"


def test_output_preview_compacts_and_truncates_output(tmp_path):
    manifest_path, manifest = start_manifest("planner", "fake-model", tmp_path)
    complete_manifest(manifest_path, manifest, "line one\nline two\nline three")

    preview = output_preview(load_manifest(manifest_path), max_chars=12)

    assert preview == "line one..."


def test_prune_manifests_keeps_latest_entries(tmp_path):
    first_path, first = start_manifest("planner", "model-a", tmp_path)
    complete_manifest(first_path, first, "first")
    second_path, second = start_manifest("planner", "model-a", tmp_path)
    complete_manifest(second_path, second, "second")

    result = prune_manifests(tmp_path, keep=1, agent_id="planner")
    remaining = list_manifests(tmp_path, agent_id="planner")

    assert result["removed_manifests"] == 1
    assert result["removed_outputs"] == 1
    assert [item.run_id for item in remaining] == [second.run_id]


def test_render_manifest_list_and_detail_include_expected_fields(tmp_path):
    manifest_path, manifest = start_manifest("reviewer", "fake-model", tmp_path)
    complete_manifest(manifest_path, manifest, "review result body")

    listing = render_manifest_list(tmp_path, agent_id="reviewer", limit=10)
    detail = render_manifest_detail(tmp_path, run_id=manifest.run_id, agent_id="reviewer", include_output=True)

    assert manifest.run_id in listing
    assert "reviewer | completed" in listing
    assert '"agent_id": "reviewer"' in detail
    assert "review result body" in detail