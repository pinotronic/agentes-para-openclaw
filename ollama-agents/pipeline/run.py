#!/usr/bin/env python3
"""TDD pipeline MVP.

- Detects project adapter (python/rust/node).
- Orchestrates local Ollama agents via `ollama-agents/runner/ollama_agent.py`.
- Runs quality gate commands from adapter.

This is an MVP+ loop: it can apply unified diffs from agents via `git apply` and iterate.
Structured IO and richer patch hygiene will be added next.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from adapters import ALL_ADAPTERS
from patch_apply import git_apply

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "ollama-agents" / "runner" / "ollama_agent.py"


def sh(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_gates(project: Path, commands: list[list[str]]) -> tuple[bool, str]:
    """Run quality gates, return (ok, combined_log)."""
    logs: list[str] = []
    for cmd in commands:
        p = sh(cmd, cwd=project)
        logs.append(f"$ {' '.join(cmd)}\n{p.stdout}\n{p.stderr}\n")
        if p.returncode != 0:
            return False, "\n".join(logs)
    return True, "\n".join(logs)


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

    # Safety: require git repo and clean state
    if not (project / ".git").exists():
        raise SystemExit("Project is not a git repo (.git missing). Initialize git first.")
    dirty = sh(["git", "status", "--porcelain"], cwd=project).stdout.strip()
    if dirty:
        raise SystemExit("Project has uncommitted changes. Commit/stash first to keep pipeline safe.")

    gate_cmds = adapter.commands(project)

    # 1) Plan
    print("\n== Planner output ==")
    plan = run_agent("planner", args.task, context=context, rag=rag, rag_k=args.rag_k)
    print(plan)

    # 2) Write tests (diff)
    print("\n== Test writer (diff) ==")
    test_task = (
        "Write tests FIRST for this task. Output ONLY a unified diff patch applicable with git apply.\n\n"
        f"TASK: {args.task}\n\nPLAN:\n{plan}\n"
    )
    test_diff = run_agent("test_writer", test_task, context=context, rag=rag, rag_k=args.rag_k)
    ok, msg = git_apply(project, test_diff)
    if not ok:
        raise SystemExit(f"Failed to apply test diff: {msg}")

    # Loop: run gates, diagnose+implement until green or max-iters
    last_logs = ""
    for i in range(1, args.max_iters + 1):
        print(f"\n== Iteration {i}/{args.max_iters}: run gates ==")
        ok, logs = run_gates(project, gate_cmds)
        last_logs = logs
        if ok:
            print("All gates passed ✅")
            break

        print("Gates failed ❌")
        # 3) Diagnose
        diag_task = (
            "You are given real command output (tests/lint/build). Diagnose and propose minimal fix.\n\n"
            f"LOGS:\n{logs}\n"
        )
        diag = run_agent("diagnoser", diag_task, context=context, rag=rag, rag_k=args.rag_k)
        print("\n== Diagnoser ==")
        print(diag)

        # 4) Implement fix (diff)
        impl_task = (
            "Fix the failing gates with minimal changes. Output ONLY a unified diff patch applicable with git apply.\n\n"
            f"TASK: {args.task}\n\nPLAN:\n{plan}\n\nDIAGNOSIS:\n{diag}\n\nLOGS:\n{logs}\n"
        )
        impl_diff = run_agent("implementer", impl_task, context=context, rag=rag, rag_k=args.rag_k)
        ok2, msg2 = git_apply(project, impl_diff)
        if not ok2:
            raise SystemExit(f"Failed to apply implementer diff: {msg2}")

    else:
        print("\nReached max iterations without green gates.")

    # Reviewer summary (optional)
    print("\n== Reviewer ==")
    rev_task = (
        "Review the current changes for quality/security/testability.\n\n"
        "Provide BLOCKER/IMPORTANT/NICE issues.\n"
    )
    review = run_agent("reviewer", rev_task, context=context, rag=rag, rag_k=args.rag_k)
    print(review)

    # Show git status summary
    print("\n== Git status ==")
    print(sh(["git", "status", "--porcelain"], cwd=project).stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
