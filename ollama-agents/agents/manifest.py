from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AgentManifest:
    version: int
    run_id: str
    agent_id: str
    model: str
    workspace: str
    status: str
    output_file: str
    error: str
    created_at: float
    started_at: float
    completed_at: float | None


def agent_store_dir(workspace: Path | None) -> Path:
    base = workspace.resolve() if workspace is not None else Path.cwd().resolve()
    return base / ".agent_store"


def start_manifest(agent_id: str, model: str, workspace: Path | None) -> tuple[Path, AgentManifest]:
    now = time.time()
    run_id = f"{time.strftime('%Y%m%d-%H%M%S', time.localtime(now))}-{uuid.uuid4().hex[:8]}"
    store_dir = agent_store_dir(workspace)
    manifest_path = store_dir / f"{run_id}-{agent_id}.json"
    output_path = store_dir / f"{run_id}-{agent_id}.out.txt"
    manifest = AgentManifest(
        version=1,
        run_id=run_id,
        agent_id=agent_id,
        model=model,
        workspace=str(workspace.resolve()) if workspace is not None else str(Path.cwd().resolve()),
        status="running",
        output_file=str(output_path),
        error="",
        created_at=now,
        started_at=now,
        completed_at=None,
    )
    save_manifest(manifest_path, manifest)
    return manifest_path, manifest


def complete_manifest(manifest_path: Path, manifest: AgentManifest, output: str) -> AgentManifest:
    _write_output_file(manifest, output)
    manifest.status = "completed"
    manifest.error = ""
    manifest.completed_at = time.time()
    save_manifest(manifest_path, manifest)
    return manifest


def fail_manifest(manifest_path: Path, manifest: AgentManifest, error: str, output: str | None = None) -> AgentManifest:
    if output is not None:
        _write_output_file(manifest, output)
    manifest.status = "error"
    manifest.error = error
    manifest.completed_at = time.time()
    save_manifest(manifest_path, manifest)
    return manifest


def _write_output_file(manifest: AgentManifest, output: str) -> None:
    output_path = Path(manifest.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")


def save_manifest(path: Path, manifest: AgentManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(manifest)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    latest_dir = path.parent / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_path = latest_dir / f"{manifest.agent_id}.json"
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_manifest(path: Path) -> AgentManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    return AgentManifest(
        version=int(data.get("version", 1)),
        run_id=str(data.get("run_id", "")),
        agent_id=str(data.get("agent_id", "")),
        model=str(data.get("model", "")),
        workspace=str(data.get("workspace", "")),
        status=str(data.get("status", "")),
        output_file=str(data.get("output_file", "")),
        error=str(data.get("error", "")),
        created_at=float(data.get("created_at", 0)),
        started_at=float(data.get("started_at", 0)),
        completed_at=(None if data.get("completed_at") is None else float(data.get("completed_at"))),
    )


def get_agent_status(agent_id: str, workspace: Path | None) -> AgentManifest | None:
    latest_path = agent_store_dir(workspace) / "latest" / f"{agent_id}.json"
    latest_manifest = None
    if latest_path.is_file():
        try:
            latest_manifest = load_manifest(latest_path)
        except Exception:
            latest_manifest = None

    manifests = list_manifests(workspace, agent_id=agent_id, limit=1)
    if not manifests:
        return latest_manifest

    newest_manifest = manifests[0]
    if latest_manifest is None or latest_manifest.run_id != newest_manifest.run_id:
        save_manifest(agent_store_dir(workspace) / f"{newest_manifest.run_id}-{newest_manifest.agent_id}.json", newest_manifest)
    return newest_manifest


def list_manifests(
    workspace: Path | None,
    *,
    agent_id: str | None = None,
    limit: int | None = None,
) -> list[AgentManifest]:
    store = agent_store_dir(workspace)
    if not store.is_dir():
        return []

    manifests: list[AgentManifest] = []
    for path in store.glob("*.json"):
        try:
            manifest = load_manifest(path)
        except Exception:
            continue
        if agent_id is not None and manifest.agent_id != agent_id:
            continue
        manifests.append(manifest)

    manifests.sort(key=lambda item: (item.created_at, item.run_id), reverse=True)

    if limit is not None:
        manifests = manifests[:limit]
    return manifests


def get_manifest_by_run_id(
    workspace: Path | None,
    run_id: str,
    *,
    agent_id: str | None = None,
) -> AgentManifest | None:
    for manifest in list_manifests(workspace, agent_id=agent_id):
        if manifest.run_id == run_id:
            return manifest
    return None


def output_preview(manifest: AgentManifest, *, max_chars: int = 160) -> str:
    output_path = Path(manifest.output_file)
    if not output_path.is_file():
        return ""
    content = output_path.read_text(encoding="utf-8")
    compact = " ".join(content.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def prune_manifests(
    workspace: Path | None,
    *,
    keep: int,
    agent_id: str | None = None,
) -> dict[str, int]:
    if keep < 1:
        raise ValueError("keep must be >= 1")

    store = agent_store_dir(workspace)
    manifests = list_manifests(workspace, agent_id=agent_id)
    to_remove = manifests[keep:]
    removed_manifests = 0
    removed_outputs = 0

    for manifest in to_remove:
        manifest_path = store / f"{manifest.run_id}-{manifest.agent_id}.json"
        output_path = Path(manifest.output_file)
        if manifest_path.is_file():
            manifest_path.unlink()
            removed_manifests += 1
        if output_path.is_file() and store in output_path.resolve().parents:
            output_path.unlink()
            removed_outputs += 1

    return {
        "kept": min(len(manifests), keep),
        "removed_manifests": removed_manifests,
        "removed_outputs": removed_outputs,
    }


def manifest_summary(manifest: AgentManifest) -> dict[str, str | float | None]:
    return {
        "run_id": manifest.run_id,
        "agent_id": manifest.agent_id,
        "model": manifest.model,
        "workspace": manifest.workspace,
        "status": manifest.status,
        "output_file": manifest.output_file,
        "error": manifest.error,
        "output_preview": output_preview(manifest),
        "created_at": manifest.created_at,
        "started_at": manifest.started_at,
        "completed_at": manifest.completed_at,
    }