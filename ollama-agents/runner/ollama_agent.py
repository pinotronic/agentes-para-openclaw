#!/usr/bin/env python3
"""Minimal agent runner for Ollama.

Reads an agent profile YAML, composes system+user prompt, calls `ollama run`.
Designed to be orchestrated by Rex.

Usage:
  python3 ollama_agent.py --agent planner --input "..."
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "agents"


def load_profile(agent_id: str) -> dict:
    path = AGENTS_DIR / f"{agent_id}.yaml"
    if not path.exists():
        raise SystemExit(f"Agent profile not found: {path}")
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        raise SystemExit("PyYAML not installed. Install with: pip install pyyaml")
    return yaml.safe_load(text)


def run_ollama(model: str, prompt: str) -> str:
    # `ollama run <model>` reads prompt from stdin.
    p = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        raise SystemExit(f"ollama failed (code {p.returncode}):\n{p.stderr}")
    return p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, help="agent id (e.g. planner)")
    ap.add_argument("--input", required=True, help="user input / task")
    ap.add_argument("--context", default="", help="extra context text")
    args = ap.parse_args()

    prof = load_profile(args.agent)
    system = (prof.get("system") or "").strip()

    prompt = (
        f"<SYSTEM>\n{system}\n</SYSTEM>\n\n"
        f"<CONTEXT>\n{args.context.strip()}\n</CONTEXT>\n\n"
        f"<TASK>\n{args.input.strip()}\n</TASK>\n"
    )

    out = run_ollama(prof["model"], prompt)
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
