"""Mission Control: lightweight run tracking for the local TDD pipeline.

Writes *structured* run artifacts under <project>/.mission_control/

Layout:
  .mission_control/
    latest -> <run_id>/
    <run_id>/
      summary.json
      events.jsonl

Design goals:
- Zero external dependencies
- Append-only event log (JSONL)
- Safe-by-default: store metadata, timings, exit codes; avoid persisting full agent outputs
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


@dataclass
class MissionControl:
    project: Path
    run_id: str
    root: Path
    events_path: Path
    summary_path: Path
    enabled: bool = True

    @classmethod
    def start(cls, project: Path, *, task: str, adapter_id: str, enabled: bool = True) -> "MissionControl":
        # Allow hard-disable via env var for ultra-quiet runs.
        if os.environ.get("PIPELINE_MISSION_CONTROL", "1").strip() in {"0", "false", "False"}:
            enabled = False

        run_id = time.strftime("%Y%m%d-%H%M%S")
        root = project / ".mission_control" / run_id
        events_path = root / "events.jsonl"
        summary_path = root / "summary.json"

        mc = cls(
            project=project,
            run_id=run_id,
            root=root,
            events_path=events_path,
            summary_path=summary_path,
            enabled=enabled,
        )

        if enabled:
            _safe_mkdir(root)
            mc._write_latest_pointer()
            mc.write_summary(
                {
                    "run_id": run_id,
                    "started_at": _now_iso(),
                    "task": task,
                    "adapter_id": adapter_id,
                    "status": "running",
                }
            )
            mc.event("run_started", {"task": task, "adapter_id": adapter_id})

        return mc

    def _write_latest_pointer(self) -> None:
        latest = self.project / ".mission_control" / "latest"
        _safe_mkdir(latest.parent)
        # Use a small file pointer instead of symlink for portability.
        _atomic_write(latest, self.run_id + "\n")

    def event(self, name: str, payload: dict[str, Any] | None = None) -> None:
        if not self.enabled:
            return
        rec = {
            "ts": _now_iso(),
            "event": name,
            "run_id": self.run_id,
        }
        if payload:
            rec["data"] = payload
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def write_summary(self, summary: dict[str, Any]) -> None:
        if not self.enabled:
            return
        _atomic_write(self.summary_path, json.dumps(summary, indent=2, ensure_ascii=False) + "\n")

    def set_status(self, status: str, **extra: Any) -> None:
        if not self.enabled:
            return
        base = self.read_summary()
        base.update({"status": status, **extra})
        self.write_summary(base)

    def read_summary(self) -> dict[str, Any]:
        if not self.enabled:
            return {"run_id": self.run_id}
        try:
            return json.loads(self.summary_path.read_text(encoding="utf-8"))
        except Exception:
            return {"run_id": self.run_id}

    def merge_summary(self, patch: dict[str, Any]) -> None:
        if not self.enabled:
            return
        base = self.read_summary()
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                merged = dict(base[key])
                merged.update(value)
                base[key] = merged
            else:
                base[key] = value
        self.write_summary(base)

    def finish_ok(self) -> None:
        self.event("run_finished", {"ok": True})
        self.set_status("ok", finished_at=_now_iso())

    def finish_fail(self, reason: str) -> None:
        self.event("run_finished", {"ok": False, "reason": reason})
        self.set_status("failed", finished_at=_now_iso(), reason=reason)
