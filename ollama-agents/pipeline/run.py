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
import re
import subprocess
import sys
import time
from pathlib import Path

from adapters import ALL_ADAPTERS
from run_redblue import run_blue_team, run_red_team
from patch_apply import git_apply
from mission_control import MissionControl


def _changed_paths(project: Path) -> list[str]:
    # Includes staged+unstaged paths after applying diffs.
    p = sh(["git", "status", "--porcelain"], cwd=project)
    if p.returncode != 0:
        return []
    paths: list[str] = []
    for line in p.stdout.splitlines():
        if not line.strip():
            continue
        # Porcelain format: XY <path>
        path = line[3:]
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        paths.append(path)
    return paths


def _current_diff(project: Path) -> str:
    """Return the current unstaged/staged diff for the workspace."""
    p = sh(["git", "diff", "--no-ext-diff", "HEAD", "--"], cwd=project)
    if p.returncode != 0:
        return ""
    return p.stdout.strip()


def extract_blocker_findings(*texts: str) -> str:
    """Extract blocker-focused lines from review outputs.

    Conservative heuristic: only keep lines containing BLOCKER and nearby non-empty
    context until the next blank line.
    """
    structured = parse_structured_review_findings(*texts)
    if structured:
        blocks: list[str] = []
        for finding in structured:
            if finding["severity"] != "BLOCKER":
                continue
            lines = [f"BLOCKER: {finding['title']}" if finding["title"] else "BLOCKER"]
            if finding["location"]:
                lines.append(f"Location: {finding['location']}")
            if finding["details"]:
                lines.append(finding["details"])
            blocks.append("\n".join(lines).strip())
        if blocks:
            return "\n\n".join(blocks).strip()

    findings: list[str] = []
    for text in texts:
        if not text:
            continue
        lines = text.splitlines()
        capture = False
        for line in lines:
            if "BLOCKER" in line.upper():
                capture = True
                findings.append(line)
                continue
            if capture:
                if not line.strip():
                    capture = False
                    continue
                findings.append(line)
    return "\n".join(findings).strip()


def run_redblue_stage(project: Path, *, plan: str, enabled: bool) -> dict[str, str] | None:
    """Run optional red/blue review on the current diff.

    Returns a dict with red/blue outputs when the stage runs, else None.
    """
    if not enabled:
        return None

    current_diff = _current_diff(project)
    if not current_diff:
        log.info("Skipping red/blue stage because there is no diff to review")
        return None

    log.info("Running optional red/blue review stage")
    red_output = run_red_team(current_diff, plan, workspace=project)
    stop_ollama_model(get_agent_model("code_critic", workspace=project))
    blue_output = run_blue_team(red_output, current_diff, plan, workspace=project)
    stop_ollama_model(get_agent_model("defender", workspace=project))
    return {"red": red_output, "blue": blue_output, "diff": current_diff}


def run_redblue_autofix_stage(
    project: Path,
    *,
    adapter_id: str,
    context: str,
    task: str,
    plan: str,
    redblue_review: dict[str, str] | None,
    rag: str | None,
    rag_k: int,
    enabled: bool,
) -> dict[str, str] | None:
    """Apply one implementer pass from red/blue BLOCKER findings."""
    if not enabled or not redblue_review:
        return None

    blockers = extract_blocker_findings(redblue_review.get("red", ""), redblue_review.get("blue", ""))
    if not blockers:
        log.info("Skipping red/blue autofix because no BLOCKER findings were detected")
        return None

    log.info("Running implementer autofix pass from red/blue BLOCKER findings")
    impl_task = (
        "Fix only the BLOCKER findings below with minimal changes. "
        "Output ONLY a unified diff patch applicable with git apply.\n\n"
        f"TASK: {task}\n\n"
        f"PLAN:\n{plan}\n\n"
        f"CURRENT DIFF UNDER REVIEW:\n{redblue_review.get('diff', '')}\n\n"
        f"BLOCKER FINDINGS:\n{blockers}\n"
    )
    impl_diff = run_agent("implementer", impl_task, context=context, workspace=project, rag=rag, rag_k=rag_k)
    ok, message = git_apply(project, impl_diff)
    if not ok:
        raise SystemExit(f"Failed to apply red/blue autofix diff: {message}")

    okv, why = validate_project_changes(project, adapter_id=adapter_id)
    if not okv:
        sh(["git", "reset", "--hard"], cwd=project)
        sh(["git", "clean", "-fd"], cwd=project)
        raise SystemExit(
            "Safety guardrail triggered after red/blue autofix diff. "
            f"{why}. Reverted changes; adjust prompts/adapter rules."
        )

    stop_ollama_model(get_agent_model("implementer", workspace=project))
    return {"blockers": blockers, "diff": impl_diff}


def validate_project_changes(project: Path, *, adapter_id: str) -> tuple[bool, str]:
    """Fail-closed guardrails to prevent agents from inventing parallel structures."""

    paths = _changed_paths(project)
    if not paths:
        return True, "no changes"

    # Hard rules for this monorepo (extend as needed)
    if adapter_id == "fastapi-react-monorepo":
        disallowed_prefixes = [
            "frontend/tests/",  # tests must live under frontend/src/ for this repo
            "frontend/src/components/App/",  # prevents parallel App tree
        ]
        for p in paths:
            for pref in disallowed_prefixes:
                if p.startswith(pref):
                    return False, f"Disallowed change path: {p} (prefix {pref})"

    return True, "ok"

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
OLLAMA_AGENTS_ROOT = REPO_ROOT / "ollama-agents"
if str(OLLAMA_AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(OLLAMA_AGENTS_ROOT))

from discovery import resolve_agent_definition
from agents.manifest import get_agent_status, manifest_summary

RUNNER = REPO_ROOT / "ollama-agents" / "runner" / "ollama_agent.py"
STRUCTURED_FINDINGS_SPEC = """
Además de tu salida normal, DEBES terminar con este bloque exacto:
<REVIEW_FINDINGS>
{"findings":[
  {"severity":"BLOCKER|IMPORTANT|NICE","title":"...","location":"archivo:linea","details":"..."}
]}
</REVIEW_FINDINGS>

Reglas:
- Si no hay findings, usa {"findings":[]}.
- El bloque final debe ser JSON válido.
- No uses otras severidades.
""".strip()


def build_reviewer_task(
    *,
    redblue_review: dict[str, str] | None,
    redblue_autofix: dict[str, str] | None,
) -> str:
    """Build reviewer task text with structured findings contract."""
    review_task = (
        "Review the current changes for quality/security/testability.\n\n"
        "Provide BLOCKER/IMPORTANT/NICE issues.\n\n"
        f"{STRUCTURED_FINDINGS_SPEC}\n"
    )
    if redblue_review:
        review_task += (
            "\nConsider these prior red/blue findings as additional review context.\n\n"
            f"RED TEAM:\n{redblue_review['red']}\n\n"
            f"BLUE TEAM:\n{redblue_review['blue']}\n"
        )
    if redblue_autofix:
        review_task += (
            "\nAn implementer autofix pass was run for BLOCKER findings. "
            "Re-review whether those blockers were actually resolved.\n\n"
            f"AUTOFIX BLOCKERS:\n{redblue_autofix['blockers']}\n"
        )
    return review_task
REVIEW_FINDINGS_RE = re.compile(r"<REVIEW_FINDINGS>\s*(.*?)\s*</REVIEW_FINDINGS>", re.DOTALL)


def parse_structured_review_findings(*texts: str) -> list[dict[str, str]]:
    """Parse structured review findings emitted by review agents."""
    findings: list[dict[str, str]] = []
    for text in texts:
        if not text:
            continue
        for match in REVIEW_FINDINGS_RE.finditer(text):
            payload = match.group(1).strip()
            try:
                decoded = json.loads(payload)
            except json.JSONDecodeError:
                continue
            raw_findings = decoded.get("findings", [])
            if not isinstance(raw_findings, list):
                continue
            for item in raw_findings:
                if not isinstance(item, dict):
                    continue
                severity = str(item.get("severity", "")).upper().strip()
                if severity not in {"BLOCKER", "IMPORTANT", "NICE"}:
                    continue
                findings.append({
                    "severity": severity,
                    "title": str(item.get("title", "")).strip(),
                    "details": str(item.get("details", "")).strip(),
                    "location": str(item.get("location", "")).strip(),
                })
    return findings


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


def get_agent_model(agent_id: str, workspace: Path | None = None) -> str:
    """Reads the agent's YAML file to get its model."""
    definition = resolve_agent_definition(agent_id, workspace, OLLAMA_AGENTS_ROOT)
    if definition is None:
        raise FileNotFoundError(f"Agent profile not found: {agent_id}")
    agent_profile_path = definition.path
    
    # We need pyyaml to parse the yaml file
    try:
        import yaml
    except ImportError:
        raise SystemExit("PyYAML not installed. Install with: pip install pyyaml")

    with open(agent_profile_path, "r") as f:
        profile = yaml.safe_load(f)
    return profile["model"]

def stop_ollama_model(model_name: str):
    """Executes 'ollama stop <model_name>' to free VRAM."""
    log.info(f"Stopping Ollama model: {model_name}")
    try:
        subprocess.run(["ollama", "stop", model_name], check=True, capture_output=True, text=True)
        log.info(f"Successfully stopped Ollama model: {model_name}")
    except subprocess.CalledProcessError as e:
        log.warning(f"Failed to stop Ollama model {model_name}: {e.stderr}")
    except FileNotFoundError:
        log.warning("Ollama command not found. Is Ollama installed and in PATH?")


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


def run_agent(
    agent: str,
    task: str,
    *,
    context: str,
    workspace: Path | None = None,
    rag: str | None = None,
    rag_k: int = 6,
    mission_control: MissionControl | None = None,
) -> str:
    """Run an agent with timeout and retry logic."""
    cmd = [sys.executable, str(RUNNER), "--agent", agent, "--input", task, "--context", context]
    if workspace is not None:
        cmd += ["--workspace", str(workspace)]
    if rag:
        cmd += ["--rag", rag, "--rag-k", str(rag_k)]

    log.info(f"Running agent: {agent}")
    p = sh(cmd, cwd=REPO_ROOT, timeout=AGENT_TIMEOUT)
    _record_agent_manifest(mission_control, agent, workspace)
    if p.returncode != 0:
        raise SystemExit(f"Agent {agent} failed:\n{p.stderr}")
    return p.stdout


def _record_agent_manifest(
    mission_control: MissionControl | None,
    agent: str,
    workspace: Path | None,
) -> dict[str, object] | None:
    if mission_control is None or workspace is None:
        return None

    manifest = get_agent_status(agent, workspace)
    if manifest is None:
        return None

    payload = manifest_summary(manifest)
    mission_control.event("agent_manifest", payload)
    mission_control.merge_summary(
        {
            "agents": {agent: payload},
            "agent_outputs": {
                agent: {
                    "run_id": payload["run_id"],
                    "output_file": payload["output_file"],
                    "status": payload["status"],
                    "preview": payload.get("output_preview", ""),
                }
            },
        }
    )
    return payload


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
    ap.add_argument("--redblue", action="store_true", help="run optional red/blue review stage before reviewer")
    ap.add_argument("--redblue-autofix", action="store_true", help="run one implementer autofix pass for red/blue BLOCKER findings")
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

    # Project structure hints (critical to avoid agents inventing paths)
    backend_hint = ""
    if (project / "backend" / "src").exists():
        backend_hint = "Backend: Python code in backend/src/. Tests in backend/tests/."
    elif (project / "backend" / "app").exists():
        backend_hint = "Backend: Python code in backend/app/. Tests in backend/tests/."

    frontend_hint = ""
    if (project / "frontend" / "src" / "App.tsx").exists():
        frontend_hint = (
            "Frontend: React entrypoint is frontend/src/App.tsx. "
            "Do NOT create a parallel app under frontend/src/components/App/ unless explicitly requested."
        )

    context = (
        f"Project: {project}\n"
        f"Adapter: {adapter.id} ({adapter.describe()})\n"
        f"Rules: TDD-first; small diffs; no secrets; follow repo conventions.\n"
        + (f"{backend_hint}\n" if backend_hint else "")
        + (f"{frontend_hint}\n" if frontend_hint else "")
    )

    rag = args.rag.strip() or None

    log.info(f"Adapter: {adapter.id} - {adapter.describe()}")
    log.info(f"Task: {args.task}")

    # Mission Control (run tracking)
    mc = MissionControl.start(project, task=args.task, adapter_id=adapter.id)

    # Safety: require git repo and clean state
    if not (project / ".git").exists():
        raise SystemExit("Project is not a git repo (.git missing). Initialize git first.")
    dirty = sh(["git", "status", "--porcelain"], cwd=project).stdout.strip()
    if dirty:
        raise SystemExit("Project has uncommitted changes. Commit/stash first to keep pipeline safe.")

    mc.event("safety_ok")

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
        mc.event("agent_start", {"agent": "planner"})
        plan = run_agent("planner", args.task, context=context, workspace=project, rag=rag, rag_k=args.rag_k, mission_control=mc)
        print("\n== Planner output ==")
        print(plan)
        stop_ollama_model(get_agent_model("planner", workspace=project))
        mc.event("agent_stop", {"agent": "planner"})

        # 2) Write tests (diff)
        log.info("Running test writer...")
        mc.event("agent_start", {"agent": "test_writer"})
        print("\n== Test writer (diff) ==")
        test_task = (
            "Write tests FIRST for this task. Output ONLY a unified diff patch applicable with git apply.\n\n"
            f"TASK: {args.task}\n\nPLAN:\n{plan}\n"
        )
        test_diff = run_agent("test_writer", test_task, context=context, workspace=project, rag=rag, rag_k=args.rag_k, mission_control=mc)
        ok, msg = git_apply(project, test_diff)
        if not ok:
            raise SystemExit(f"Failed to apply test diff: {msg}")

        okv, why = validate_project_changes(project, adapter_id=adapter.id)
        if not okv:
            # Revert to keep repo clean
            sh(["git", "reset", "--hard"], cwd=project)
            sh(["git", "clean", "-fd"], cwd=project)
            raise SystemExit(
                "Safety guardrail triggered after test diff. "
                f"{why}. Reverted changes; adjust prompts/adapter rules."
            )

        stop_ollama_model(get_agent_model("test_writer", workspace=project))
        mc.event("agent_stop", {"agent": "test_writer"})

        # Save initial state
        save_state(project, {"task": args.task, "plan": plan, "iteration": 1, "phase": "gates"})

    # Loop: run gates, diagnose+implement until green or max-iters
    last_logs = ""
    for i in range(start_iteration, args.max_iters + 1):
        log.info(f"Iteration {i}/{args.max_iters}: running gates")
        print(f"\n== Iteration {i}/{args.max_iters}: run gates ==")
        ok, logs = run_gates(project, gate_cmds)
        mc.event("gates", {"iteration": i, "ok": ok})
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
        mc.event("agent_start", {"agent": "diagnoser", "iteration": i})
        diag = run_agent("diagnoser", diag_task, context=context, workspace=project, rag=rag, rag_k=args.rag_k, mission_control=mc)
        print("\n== Diagnoser ==")
        print(diag)
        stop_ollama_model(get_agent_model("diagnoser", workspace=project))
        mc.event("agent_stop", {"agent": "diagnoser", "iteration": i})

        # 4) Implement fix (diff)
        log.info("Running implementer...")
        mc.event("agent_start", {"agent": "implementer", "iteration": i})
        impl_task = (
            "Fix the failing gates with minimal changes. Output ONLY a unified diff patch applicable with git apply.\n\n"
            f"TASK: {args.task}\n\nPLAN:\n{plan}\n\nDIAGNOSIS:\n{diag}\n\nLOGS:\n{logs}\n"
        )
        impl_diff = run_agent("implementer", impl_task, context=context, workspace=project, rag=rag, rag_k=args.rag_k, mission_control=mc)
        ok2, msg2 = git_apply(project, impl_diff)
        if not ok2:
            raise SystemExit(f"Failed to apply implementer diff: {msg2}")

        okv2, why2 = validate_project_changes(project, adapter_id=adapter.id)
        if not okv2:
            sh(["git", "reset", "--hard"], cwd=project)
            sh(["git", "clean", "-fd"], cwd=project)
            raise SystemExit(
                "Safety guardrail triggered after implementer diff. "
                f"{why2}. Reverted changes; adjust prompts/adapter rules."
            )

        stop_ollama_model(get_agent_model("implementer", workspace=project))
        mc.event("agent_stop", {"agent": "implementer", "iteration": i})

        # Save state after implementation
        save_state(project, {"task": args.task, "plan": plan, "iteration": i + 1, "phase": "gates"})

    else:
        log.warning("Reached max iterations without green gates")
        print("\nReached max iterations without green gates.")

    redblue_review = run_redblue_stage(project, plan=plan, enabled=args.redblue)
    if redblue_review:
        print("\n== Red Team / Blue Team ==")
        print("\n[RED]\n")
        print(redblue_review["red"])
        print("\n[BLUE]\n")
        print(redblue_review["blue"])
        mc.event("redblue", {"enabled": True, "diff_bytes": len(redblue_review["diff"])})
    else:
        mc.event("redblue", {"enabled": False})

    redblue_autofix = run_redblue_autofix_stage(
        project,
        adapter_id=adapter.id,
        context=context,
        task=args.task,
        plan=plan,
        redblue_review=redblue_review,
        rag=rag,
        rag_k=args.rag_k,
        enabled=args.redblue_autofix,
    )
    if redblue_autofix:
        print("\n== Red/Blue Autofix ==")
        print(redblue_autofix["blockers"])
        mc.event("redblue_autofix", {"enabled": True, "blocker_bytes": len(redblue_autofix["blockers"])})
        autofix_ok, autofix_logs = run_gates(project, gate_cmds)
        print("\n== Gates After Red/Blue Autofix ==")
        print("All gates passed ✅" if autofix_ok else "Gates failed ❌")
        if not autofix_ok:
            print(autofix_logs)
        mc.event("gates_after_redblue_autofix", {"ok": autofix_ok})
    else:
        mc.event("redblue_autofix", {"enabled": False})

    # Reviewer summary (optional)
    log.info("Running reviewer...")
    mc.event("agent_start", {"agent": "reviewer"})
    print("\n== Reviewer ==")
    rev_task = build_reviewer_task(redblue_review=redblue_review, redblue_autofix=redblue_autofix)
    review = run_agent("reviewer", rev_task, context=context, workspace=project, rag=rag, rag_k=args.rag_k, mission_control=mc)
    print(review)
    stop_ollama_model(get_agent_model("reviewer", workspace=project))
    mc.event("agent_stop", {"agent": "reviewer"})

    # Show git status summary
    print("\n== Git status ==")
    print(sh(["git", "status", "--porcelain"], cwd=project).stdout)

    # Clear state on success
    clear_state(project)

    mc.finish_ok()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
