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
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from adapters import ALL_ADAPTERS
from patch_apply import git_apply

# Configuration from environment variables
DEFAULT_MAX_ITERS = int(os.environ.get("PIPELINE_MAX_ITERS", 4))
DEFAULT_RAG_K = int(os.environ.get("PIPELINE_RAG_K", 6))
AGENT_TIMEOUT = int(os.environ.get("PIPELINE_AGENT_TIMEOUT", 300))  # 5 minutes
GATE_TIMEOUT = int(os.environ.get("PIPELINE_GATE_TIMEOUT", 120))  # 2 minutes
STATE_FILE = ".pipeline_state.json"

# Logging setup
logging.basicConfig(
    level=os.environ.get("PIPELINE_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "ollama-agents" / "runner" / "ollama_agent.py"


def sh(cmd: list[str], cwd: Path, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    """Run a shell command with optional timeout."""
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        log.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        # Return a failed result
        result = subprocess.CompletedProcess(cmd, returncode=-1, stdout="", stderr=f"Timeout after {timeout}s")
        return result


def run_gates(project: Path, commands: list[list[str]]) -> tuple[bool, str]:
    """Run quality gates, return (ok, combined_log)."""
    logs: list[str] = []
    for cmd in commands:
        log.debug(f"Running gate: {' '.join(cmd)}")
        p = sh(cmd, cwd=project, timeout=GATE_TIMEOUT)
        logs.append(f"$ {' '.join(cmd)}\n{p.stdout}\n{p.stderr}\n")
        if p.returncode != 0:
            log.warning(f"Gate failed: {' '.join(cmd)}")
            return False, "\n".join(logs)
    return True, "\n".join(logs)


def pick_adapter(project: Path):
    for a in ALL_ADAPTERS:
        if a.detect(project):
            return a
    return None


def run_agent(agent: str, task: str, *, context: str, rag: str | None = None, rag_k: int = 6) -> str:
    """Run an agent with timeout and retry logic."""
    cmd = [sys.executable, str(RUNNER), "--agent", agent, "--input", task, "--context", context]
    if rag:
        cmd += ["--rag", rag, "--rag-k", str(rag_k)]

    log.info(f"Running agent: {agent}")
    p = sh(cmd, cwd=REPO_ROOT, timeout=AGENT_TIMEOUT)
    if p.returncode != 0:
        raise SystemExit(f"Agent {agent} failed:\n{p.stderr}")
    return p.stdout


def save_state(project: Path, state: dict) -> None:
    """Save pipeline state for resumption."""
    state_path = project / STATE_FILE
    state["timestamp"] = time.time()
    try:
        state_path.write_text(json.dumps(state, indent=2))
        log.debug(f"State saved to {state_path}")
    except Exception as e:
        log.warning(f"Failed to save state: {e}")


def load_state(project: Path) -> dict | None:
    """Load pipeline state if exists."""
    state_path = project / STATE_FILE
    if not state_path.exists():
        return None
    try:
        state = json.loads(state_path.read_text())
        log.info(f"Loaded previous state from {state_path}")
        return state
    except Exception as e:
        log.warning(f"Failed to load state: {e}")
        return None


def clear_state(project: Path) -> None:
    """Clear pipeline state after successful completion."""
    state_path = project / STATE_FILE
    if state_path.exists():
        state_path.unlink()
        log.debug("State file cleared")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="path to target repo")
    ap.add_argument("--task", required=True, help="feature/task request")
    ap.add_argument("--max-iters", type=int, default=DEFAULT_MAX_ITERS)
    ap.add_argument("--rag", default="", help="optional RAG query to inject")
    ap.add_argument("--rag-k", type=int, default=DEFAULT_RAG_K)
    ap.add_argument("--resume", action="store_true", help="resume from saved state")
    ap.add_argument("--verbose", "-v", action="store_true", help="enable debug logging")
    args = ap.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

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

    log.info(f"Adapter: {adapter.id} - {adapter.describe()}")
    log.info(f"Task: {args.task}")

    # Safety: require git repo and clean state
    if not (project / ".git").exists():
        raise SystemExit("Project is not a git repo (.git missing). Initialize git first.")
    dirty = sh(["git", "status", "--porcelain"], cwd=project).stdout.strip()
    if dirty:
        raise SystemExit("Project has uncommitted changes. Commit/stash first to keep pipeline safe.")

    gate_cmds = adapter.commands(project)

    # Check for resumable state
    state = load_state(project) if args.resume else None
    start_iteration = 1
    plan = None

    if state and state.get("task") == args.task:
        plan = state.get("plan")
        start_iteration = state.get("iteration", 1)
        log.info(f"Resuming from iteration {start_iteration}")
    else:
        # 1) Plan
        log.info("Running planner...")
        plan = run_agent("planner", args.task, context=context, rag=rag, rag_k=args.rag_k)
        print("\n== Planner output ==")
        print(plan)

        # 2) Write tests (diff)
        log.info("Running test writer...")
        print("\n== Test writer (diff) ==")
        test_task = (
            "Write tests FIRST for this task. Output ONLY a unified diff patch applicable with git apply.\n\n"
            f"TASK: {args.task}\n\nPLAN:\n{plan}\n"
        )
        test_diff = run_agent("test_writer", test_task, context=context, rag=rag, rag_k=args.rag_k)
        ok, msg = git_apply(project, test_diff)
        if not ok:
            raise SystemExit(f"Failed to apply test diff: {msg}")

        # Save initial state
        save_state(project, {"task": args.task, "plan": plan, "iteration": 1, "phase": "gates"})

    # Loop: run gates, diagnose+implement until green or max-iters
    last_logs = ""
    for i in range(start_iteration, args.max_iters + 1):
        log.info(f"Iteration {i}/{args.max_iters}: running gates")
        print(f"\n== Iteration {i}/{args.max_iters}: run gates ==")
        ok, logs = run_gates(project, gate_cmds)
        last_logs = logs
        if ok:
            log.info("All gates passed")
            print("All gates passed ✅")
            break

        log.warning("Gates failed, running diagnosis")
        print("Gates failed ❌")

        # Save state before diagnosis
        save_state(project, {"task": args.task, "plan": plan, "iteration": i, "phase": "diagnose"})

        # 3) Diagnose
        diag_task = (
            "You are given real command output (tests/lint/build). Diagnose and propose minimal fix.\n\n"
            f"LOGS:\n{logs}\n"
        )
        diag = run_agent("diagnoser", diag_task, context=context, rag=rag, rag_k=args.rag_k)
        print("\n== Diagnoser ==")
        print(diag)

        # 4) Implement fix (diff)
        log.info("Running implementer...")
        impl_task = (
            "Fix the failing gates with minimal changes. Output ONLY a unified diff patch applicable with git apply.\n\n"
            f"TASK: {args.task}\n\nPLAN:\n{plan}\n\nDIAGNOSIS:\n{diag}\n\nLOGS:\n{logs}\n"
        )
        impl_diff = run_agent("implementer", impl_task, context=context, rag=rag, rag_k=args.rag_k)
        ok2, msg2 = git_apply(project, impl_diff)
        if not ok2:
            raise SystemExit(f"Failed to apply implementer diff: {msg2}")

        # Save state after implementation
        save_state(project, {"task": args.task, "plan": plan, "iteration": i + 1, "phase": "gates"})

    else:
        log.warning("Reached max iterations without green gates")
        print("\nReached max iterations without green gates.")

    # Reviewer summary (optional)
    log.info("Running reviewer...")
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

    # Clear state on success
    clear_state(project)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
