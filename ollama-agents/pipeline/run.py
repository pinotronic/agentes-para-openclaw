#!/usr/bin/env python3
"""TDD pipeline MVP.

- Detects project adapter (python/rust/node).
- Orchestrates local Ollama agents via `ollama-agents/runner/ollama_agent.py`.
- Runs quality gate commands from adapter.

This is an MVP: it prints suggested actions and runs gates; applying patches is manual for now.
Next iteration will add patch application and structured IO.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from adapters import ALL_ADAPTERS

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "ollama-agents" / "runner" / "ollama_agent.py"


def sh(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def pick_adapter(project: Path):
    for a in ALL_ADAPTERS:
        if a.detect(project):
            return a
    return None


def run_agent(agent: str, task: str, *, context: str, rag: str | None = None, rag_k: int = 6) -> str:
    cmd = [sys.executable, str(RUNNER), "--agent", agent, "--input", task, "--context", context]
    if rag:
        cmd += ["--rag", rag, "--rag-k", str(rag_k)]
    p = sh(cmd, cwd=REPO_ROOT)
    if p.returncode != 0:
        raise SystemExit(f"Agent {agent} failed:\n{p.stderr}")
    return p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="path to target repo")
    ap.add_argument("--task", required=True, help="feature/task request")
    ap.add_argument("--max-iters", type=int, default=4)
    ap.add_argument("--rag", default="", help="optional RAG query to inject")
    ap.add_argument("--rag-k", type=int, default=6)
    args = ap.parse_args()

    project = Path(args.project).expanduser().resolve()
    if not project.exists():
        raise SystemExit(f"Project not found: {project}")

    adapter = pick_adapter(project)
    if adapter is None:
        raise SystemExit("No adapter matched. Add one in ollama-agents/pipeline/adapters.")

    context = (
        f"Project: {project}\n"
        f"Adapter: {adapter.id} ({adapter.describe()})\n"
        f"Rules: TDD-first; small diffs; no secrets; follow repo conventions.\n"
    )

    rag = args.rag.strip() or None

    print("== Adapter ==")
    print(adapter.id, "-", adapter.describe())
    print("== Task ==")
    print(args.task)

    # 1) Plan
    print("\n== Planner output ==")
    plan = run_agent("planner", args.task, context=context, rag=rag, rag_k=args.rag_k)
    print(plan)

    # 2) Tests
    print("\n== Test writer output ==")
    tests = run_agent("test_writer", f"Based on this plan, write tests first:\n\n{plan}", context=context, rag=rag, rag_k=args.rag_k)
    print(tests)

    # NOTE: MVP stops short of applying patches automatically.
    # Next version will apply diffs and loop.

    print("\n== Quality gate commands (adapter) ==")
    for c in adapter.commands(project):
        print("-", " ".join(c))

    print("\nMVP note: apply suggested test/code changes, then re-run gates. Next iteration will auto-apply diffs and loop until green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
