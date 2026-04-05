#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.manifest import get_manifest_by_run_id, list_manifests, manifest_summary, prune_manifests


def render_manifest_list(
    workspace: Path | None,
    *,
    agent_id: str | None = None,
    limit: int = 20,
) -> str:
    manifests = list_manifests(workspace, agent_id=agent_id, limit=limit)
    if not manifests:
        return "No manifests found."

    lines = ["Agent store"]
    for manifest in manifests:
        summary = manifest_summary(manifest)
        lines.append(
            f"  {summary['run_id']} | {summary['agent_id']} | {summary['status']} | {summary['output_file']}"
        )
    return "\n".join(lines)


def render_manifest_detail(
    workspace: Path | None,
    *,
    run_id: str,
    agent_id: str | None = None,
    include_output: bool = False,
) -> str:
    manifest = get_manifest_by_run_id(workspace, run_id, agent_id=agent_id)
    if manifest is None:
        return f"Manifest not found for run_id: {run_id}"

    summary = manifest_summary(manifest)
    lines = [json.dumps(summary, ensure_ascii=False, indent=2)]
    if include_output:
        output_path = Path(manifest.output_file)
        output = output_path.read_text(encoding="utf-8") if output_path.is_file() else ""
        lines.append(output)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect .agent_store manifests")
    parser.add_argument("--workspace", default="", help="workspace root")
    parser.add_argument("--agent", help="filter by agent id")
    parser.add_argument("--limit", type=int, default=20, help="max manifests to list")
    parser.add_argument("--run-id", help="show details for one run id")
    parser.add_argument("--show-output", action="store_true", help="include persisted output when using --run-id")
    parser.add_argument("--prune-keep", type=int, help="keep only the latest N manifests (optionally filtered by --agent)")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace.strip() else None

    if args.prune_keep is not None:
        result = prune_manifests(workspace, keep=args.prune_keep, agent_id=args.agent)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.run_id:
        print(render_manifest_detail(workspace, run_id=args.run_id, agent_id=args.agent, include_output=args.show_output))
        return 0

    print(render_manifest_list(workspace, agent_id=args.agent, limit=args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())