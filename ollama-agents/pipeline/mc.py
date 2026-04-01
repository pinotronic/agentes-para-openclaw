#!/usr/bin/env python3
"""Mission Control CLI.

Examples:
  python ollama-agents/pipeline/mc.py --project /path/to/repo list
  python ollama-agents/pipeline/mc.py --project /path/to/repo show --run latest
  python ollama-agents/pipeline/mc.py --project /path/to/repo tail --run latest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _mc_root(project: Path) -> Path:
    return project / ".mission_control"


def _resolve_run(project: Path, run: str) -> Path:
    root = _mc_root(project)
    if run == "latest":
        ptr = root / "latest"
        if not ptr.exists():
            raise SystemExit("No latest run found (missing .mission_control/latest)")
        run = ptr.read_text(encoding="utf-8").strip()
    rp = root / run
    if not rp.exists():
        raise SystemExit(f"Run not found: {rp}")
    return rp


def cmd_list(project: Path) -> int:
    root = _mc_root(project)
    if not root.exists():
        print("No .mission_control directory")
        return 0
    runs = sorted([p for p in root.iterdir() if p.is_dir()])
    for p in runs:
        summ = p / "summary.json"
        status = "?"
        task = ""
        if summ.exists():
            try:
                s = json.loads(summ.read_text(encoding="utf-8"))
                status = s.get("status", "?")
                task = s.get("task", "")
            except Exception:
                pass
        print(f"{p.name}\t{status}\t{task}")
    return 0


def cmd_show(project: Path, run: str) -> int:
    rp = _resolve_run(project, run)
    summ = rp / "summary.json"
    if not summ.exists():
        raise SystemExit(f"Missing summary: {summ}")
    print(summ.read_text(encoding="utf-8"))
    return 0


def cmd_tail(project: Path, run: str) -> int:
    rp = _resolve_run(project, run)
    ev = rp / "events.jsonl"
    if not ev.exists():
        raise SystemExit(f"Missing events: {ev}")
    # Simple tail -f
    with open(ev, "r", encoding="utf-8") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                import time

                time.sleep(0.2)
                continue
            sys.stdout.write(line)
            sys.stdout.flush()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="path to target repo")

    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")

    ap_show = sub.add_parser("show")
    ap_show.add_argument("--run", default="latest")

    ap_tail = sub.add_parser("tail")
    ap_tail.add_argument("--run", default="latest")

    args = ap.parse_args()
    project = Path(args.project).expanduser().resolve()

    if args.cmd == "list":
        return cmd_list(project)
    if args.cmd == "show":
        return cmd_show(project, args.run)
    if args.cmd == "tail":
        return cmd_tail(project, args.run)

    raise SystemExit("unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
