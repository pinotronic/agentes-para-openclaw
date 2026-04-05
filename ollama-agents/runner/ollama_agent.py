#!/usr/bin/env python3
"""Minimal agent runner for Ollama.

Reads an agent profile YAML, composes system+user prompt, calls `ollama run`.
Designed to be orchestrated by Rex.

Usage:
  python3 ollama_agent.py --agent planner --input "..."
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import logging
import os
import selectors
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.executor import (
    ToolExecutionError,
    ToolExecutor,
    ToolPermissionError,
    ToolValidationError,
    build_tool_instructions,
    parse_tool_call,
)
from agents.manifest import complete_manifest, fail_manifest, get_agent_status, manifest_summary, start_manifest
from agents.permissions import (
    PermissionMode,
    get_agent_policy,
    get_runtime_permission_mode,
    has_agent_policy,
)
from agents.registry import get_registry
from discovery import list_agent_definitions, list_skill_definitions, resolve_agent_definition
from runner.permission_mode_store import resolve_permission_mode, save_permission_mode
from runner.session_store import compact_transcript, default_session_path, load_session, new_session, save_session

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

# Configuration from environment variables
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", 1200))  # 20 minutes default
OLLAMA_RETRIES = int(os.environ.get("OLLAMA_RETRIES", 2))
OLLAMA_RETRY_DELAY = int(os.environ.get("OLLAMA_RETRY_DELAY", 5))  # seconds
OLLAMA_TOOL_MAX_ROUNDS = int(os.environ.get("OLLAMA_TOOL_MAX_ROUNDS", 4))
DEGENERATE_OUTPUT_MIN_CHARS = int(os.environ.get("OLLAMA_DEGENERATE_OUTPUT_MIN_CHARS", 128))
DEGENERATE_OUTPUT_MAX_UNIQUE = int(os.environ.get("OLLAMA_DEGENERATE_OUTPUT_MAX_UNIQUE", 3))
DEGENERATE_OUTPUT_DOMINANCE = float(os.environ.get("OLLAMA_DEGENERATE_OUTPUT_DOMINANCE", 0.85))
DEGENERATE_OUTPUT_STREAM_WINDOW = int(os.environ.get("OLLAMA_DEGENERATE_OUTPUT_STREAM_WINDOW", 512))
OLLAMA_STREAM_IDLE_TIMEOUT = float(os.environ.get("OLLAMA_STREAM_IDLE_TIMEOUT", 45))

# Logging setup
logging.basicConfig(
    level=os.environ.get("AGENT_LOG_LEVEL", "WARNING"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)
AGENTS_DIR = ROOT / "agents"


def resolve_agent_profile_path(agent_id: str, workspace: Path | None = None) -> Path:
    definition = resolve_agent_definition(agent_id, workspace, ROOT)
    if definition is None:
        raise SystemExit(f"Agent profile not found for id: {agent_id}")
    return definition.path


def load_profile(agent_id: str, workspace: Path | None = None) -> dict:
    path = resolve_agent_profile_path(agent_id, workspace)
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        raise SystemExit("PyYAML not installed. Install with: pip install pyyaml")
    return yaml.safe_load(text)


def get_tool_max_rounds(profile: dict) -> int:
    raw_value = profile.get("tool_max_rounds", OLLAMA_TOOL_MAX_ROUNDS)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"Invalid tool_max_rounds value: {raw_value!r}") from exc
    if value < 1:
        raise SystemExit(f"tool_max_rounds must be >= 1, got: {value}")
    return value


def get_verify_commands(profile: dict) -> list[str]:
    raw_value = profile.get("verify_commands", [])
    if raw_value is None:
        return []
    if not isinstance(raw_value, list) or any(not isinstance(item, str) for item in raw_value):
        raise SystemExit("verify_commands must be a list of strings")
    return [item.strip() for item in raw_value if item.strip()]


def get_required_paths(profile: dict) -> list[str]:
    value = profile.get("required_paths")
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SystemExit("required_paths must be a list of strings when provided in the profile")
    return [item.strip() for item in value if item.strip()]


def detect_degenerate_output(output: str) -> str | None:
    normalized = "".join(char for char in output if not char.isspace())
    if len(normalized) < DEGENERATE_OUTPUT_MIN_CHARS:
        return None

    counts = Counter(normalized)
    unique_chars = len(counts)
    if unique_chars > DEGENERATE_OUTPUT_MAX_UNIQUE:
        return None

    dominant_char, dominant_count = counts.most_common(1)[0]
    dominance = dominant_count / len(normalized)
    if dominance < DEGENERATE_OUTPUT_DOMINANCE:
        return None

    return (
        "Model output appears degenerate/repetitive "
        f"(dominant_char={dominant_char!r}, unique_chars={unique_chars}, dominance={dominance:.2f})"
    )


def validate_model_output(output: str) -> str:
    issue = detect_degenerate_output(output)
    if issue is not None:
        raise SystemExit(issue)
    return output


def update_degenerate_stream_window(window: str, chunk: str) -> tuple[str, str | None]:
    next_window = (window + chunk)[-DEGENERATE_OUTPUT_STREAM_WINDOW:]
    return next_window, detect_degenerate_output(next_window)


def check_stream_idle(last_stdout_at: float, now: float) -> None:
    if OLLAMA_STREAM_IDLE_TIMEOUT <= 0:
        return
    idle_for = now - last_stdout_at
    if idle_for >= OLLAMA_STREAM_IDLE_TIMEOUT:
        raise RuntimeError(f"ollama stream idle timeout after {idle_for:.1f}s without stdout")


def run_verification_commands(commands: list[str], workspace: Path | None, *, timeout: int) -> list[dict[str, str | int]]:
    if not commands:
        return []
    if workspace is None:
        raise SystemExit("verify commands require --workspace")

    results: list[dict[str, str | int]] = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=str(workspace),
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        result = {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
        results.append(result)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "verification command failed"
            raise SystemExit(f"Verification failed for `{command}`: {detail}")
    return results


def verify_required_paths(paths: list[str], workspace: Path | None) -> list[str]:
    if not paths:
        return []
    if workspace is None:
        raise SystemExit("required path verification requires --workspace")

    verified: list[str] = []
    missing: list[str] = []
    for relative_path in paths:
        candidate = (workspace / relative_path).resolve()
        try:
            candidate.relative_to(workspace)
        except ValueError:
            raise SystemExit(f"Required path escapes workspace: {relative_path}")
        if candidate.exists():
            verified.append(relative_path)
        else:
            missing.append(relative_path)

    if missing:
        raise SystemExit(f"Required path verification failed: missing {', '.join(missing)}")
    return verified


def render_agent_discovery(workspace: Path | None = None) -> str:
    lines = ["Agents"]
    definitions = list_agent_definitions(workspace, ROOT)
    if not definitions:
        return "Agents\n  No agents found."
    for definition in definitions:
        suffix = f" (shadowed by {definition.shadowed_by})" if definition.shadowed_by else ""
        lines.append(f"  {definition.name} [{definition.source.label}] -> {definition.path}{suffix}")
    return "\n".join(lines)


def render_skill_discovery(workspace: Path | None = None) -> str:
    lines = ["Skills"]
    definitions = list_skill_definitions(workspace, ROOT)
    if not definitions:
        return "Skills\n  No skills found."
    for definition in definitions:
        detail = f" - {definition.description}" if definition.description else ""
        suffix = f" (shadowed by {definition.shadowed_by})" if definition.shadowed_by else ""
        lines.append(f"  {definition.name} [{definition.source.label}] -> {definition.path}{detail}{suffix}")
    return "\n".join(lines)


def render_agent_status(agent_id: str, workspace: Path | None = None, include_output: bool = False) -> str:
    manifest = get_agent_status(agent_id, workspace)
    if manifest is None:
        return f"No manifest found for agent: {agent_id}"

    data = manifest_summary(manifest)
    lines = [
        f"Agent status: {data['agent_id']}",
        f"  run_id: {data['run_id']}",
        f"  status: {data['status']}",
        f"  model: {data['model']}",
        f"  output_file: {data['output_file']}",
    ]
    if data["error"]:
        lines.append(f"  error: {data['error']}")
    if data["completed_at"] is not None:
        lines.append(f"  completed_at: {data['completed_at']}")
    if include_output:
        output_path = Path(str(data["output_file"]))
        output = output_path.read_text(encoding="utf-8") if output_path.is_file() else ""
        lines.append("  output:")
        lines.append(output)
    return "\n".join(lines)


def validate_agent_policy(agent_id: str, workspace: Path | None = None, explicit_mode: str | None = None) -> None:
    """Fail closed when an agent has no explicit runtime policy."""
    if not has_agent_policy(agent_id, workspace, explicit_mode):
        raise SystemExit(f"Agent {agent_id!r} has no explicit permission policy")


def build_policy_context(agent_id: str, workspace: Path | None = None, explicit_mode: str | None = None) -> str:
    """Build a canonical permission manifest for prompt injection."""
    validate_agent_policy(agent_id, workspace, explicit_mode)

    registry = get_registry()
    policy = get_agent_policy(agent_id, workspace, explicit_mode)
    runtime_mode = get_runtime_permission_mode(workspace, explicit_mode)
    allowed_raw = policy.allowed_tools or frozenset(registry.list_tools())

    allowed_canonical: list[str] = []
    seen: set[str] = set()
    for tool_name in sorted(allowed_raw):
        canonical = registry.normalize_name(tool_name)
        if canonical in seen:
            continue
        seen.add(canonical)
        allowed_canonical.append(canonical)

    allowed_set = set(allowed_canonical)
    all_canonical = [registry.normalize_name(name) for name in registry.list_tools()]
    danger_blocked = sorted(
        canonical
        for canonical in set(all_canonical)
        if registry.get_permission(canonical) == PermissionMode.DANGER_FULL_ACCESS
        and canonical not in allowed_set
    )

    lines = [
        f"Agent: {agent_id}",
        f"Runtime permission mode: {runtime_mode}",
        "Allowed tools:",
    ]
    lines.extend(
        f"- {tool_name}: {registry.get_permission(tool_name).value}"
        for tool_name in allowed_canonical
    )

    if danger_blocked:
        lines.append("Blocked dangerous tools:")
        lines.extend(f"- {tool_name}" for tool_name in danger_blocked)

    lines.append("Rules:")
    if runtime_mode == "strict":
        lines.append("- Never request or imply use of tools outside the allowed list.")
        lines.append("- If a required action is blocked by policy, explain the limitation instead of inventing access.")
    else:
        lines.append("- Local permissive mode is active: use tools directly when they are necessary.")
        lines.append("- Stay within the workspace boundary and avoid destructive actions unless the task requires them.")
    return "\n".join(lines)


def build_prompt(*, agent_id: str, system: str, context: str, task: str, workspace: Path | None = None, explicit_mode: str | None = None) -> str:
    """Build the final agent prompt with runtime policy context."""
    policy_context = build_policy_context(agent_id, workspace, explicit_mode)
    tool_context = build_tool_instructions(agent_id, workspace, explicit_mode)
    return (
        f"<SYSTEM>\n{system.strip()}\n</SYSTEM>\n\n"
        f"<POLICY>\n{policy_context}\n</POLICY>\n\n"
        f"<TOOLS>\n{tool_context}\n</TOOLS>\n\n"
        f"<CONTEXT>\n{context.strip()}\n</CONTEXT>\n\n"
        f"<TASK>\n{task.strip()}\n</TASK>\n"
    )


def run_with_tool_support(
    *,
    agent_id: str,
    model: str,
    prompt: str,
    workspace: Path | None,
    retries: int,
    timeout: int,
    session_file: Path | None = None,
    resume_session: bool = False,
    compact_session: bool = False,
    max_rounds: int = OLLAMA_TOOL_MAX_ROUNDS,
    explicit_mode: str | None = None,
) -> str:
    """Run an agent session with optional structured tool execution."""

    executor = ToolExecutor(agent_id=agent_id, workspace=workspace, explicit_mode=explicit_mode) if workspace else None
    transcript = ""
    session = None

    if session_file is not None:
        if resume_session and session_file.exists():
            session = load_session(session_file)
            transcript = session.transcript
        else:
            session = new_session(agent_id, model, workspace, prompt)

        if compact_session:
            transcript = compact_transcript(transcript)
            session.transcript = transcript
            session.updated_at = time.time()
            save_session(session_file, session)

    for _ in range(max_rounds + 1):
        full_prompt = prompt if not transcript else f"{prompt}\n\n<TRANSCRIPT>\n{transcript}\n</TRANSCRIPT>\n"
        output = run_ollama_with_retry(model, full_prompt, retries=retries, timeout=timeout)
        output = validate_model_output(output)

        try:
            call = parse_tool_call(output)
        except ToolValidationError as exc:
            transcript += (
                f"<ASSISTANT>\n{output.strip()}\n</ASSISTANT>\n\n"
                f"<TOOL_RESULT>\n{json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False)}\n</TOOL_RESULT>\n"
            )
            if session is not None and session_file is not None:
                session.transcript = transcript
                session.tool_rounds += 1
                session.updated_at = time.time()
                save_session(session_file, session)
            continue

        if call is None:
            if session is not None and session_file is not None:
                session.transcript = transcript
                session.final_output = output
                session.updated_at = time.time()
                save_session(session_file, session)
            return output

        if executor is None:
            raise SystemExit("Agent returned a tool call but no workspace was provided for runtime execution")

        try:
            result = executor.execute(call)
        except (ToolExecutionError, ToolPermissionError, ToolValidationError) as exc:
            result = {"ok": False, "error": str(exc), "tool": call.tool}

        transcript += (
            f"<ASSISTANT>\n{output.strip()}\n</ASSISTANT>\n\n"
            f"<TOOL_RESULT>\n{json.dumps(result, ensure_ascii=False, indent=2)}\n</TOOL_RESULT>\n"
        )
        if session is not None and session_file is not None:
            session.transcript = transcript
            session.tool_rounds += 1
            session.updated_at = time.time()
            save_session(session_file, session)

    raise SystemExit(f"Agent exceeded maximum tool rounds ({max_rounds})")


def run_ollama(model: str, prompt: str, timeout: int = OLLAMA_TIMEOUT) -> str:
    """Run ollama with timeout and streaming guardrails."""
    try:
        p = subprocess.Popen(
            ["ollama", "run", model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
        )
        assert p.stdin is not None
        p.stdin.write(prompt.encode("utf-8"))
        p.stdin.close()

        selector = selectors.DefaultSelector()
        assert p.stdout is not None
        assert p.stderr is not None
        selector.register(p.stdout, selectors.EVENT_READ, data="stdout")
        selector.register(p.stderr, selectors.EVENT_READ, data="stderr")

        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []
        recent_stdout = ""
        deadline = time.monotonic() + timeout
        last_stdout_at = time.monotonic()

        while selector.get_map():
            now = time.monotonic()
            remaining = deadline - now
            if remaining <= 0:
                p.kill()
                raise RuntimeError(f"ollama timed out after {timeout}s")

            events = selector.select(timeout=min(0.2, remaining))
            if not events:
                try:
                    check_stream_idle(last_stdout_at, time.monotonic())
                except RuntimeError:
                    p.kill()
                    raise
                if p.poll() is not None:
                    break
                continue

            for key, _ in events:
                chunk = os.read(key.fileobj.fileno(), 4096)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue

                text = chunk.decode("utf-8", errors="replace")
                if key.data == "stdout":
                    stdout_chunks.append(text)
                    last_stdout_at = time.monotonic()
                    recent_stdout, issue = update_degenerate_stream_window(recent_stdout, text)
                    if issue is not None:
                        p.kill()
                        raise RuntimeError(issue)
                else:
                    stderr_chunks.append(text)

        returncode = p.wait(timeout=max(deadline - time.monotonic(), 0.1))
        stdout = "".join(stdout_chunks)
        stderr = "".join(stderr_chunks)
        if returncode != 0:
            raise RuntimeError(f"ollama failed (code {returncode}):\n{stderr}")
        return stdout
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ollama timed out after {timeout}s")


def run_ollama_with_retry(
    model: str,
    prompt: str,
    retries: int = OLLAMA_RETRIES,
    timeout: int = OLLAMA_TIMEOUT,
    delay: int = OLLAMA_RETRY_DELAY,
) -> str:
    """Run ollama with retry logic for transient failures."""
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            log.debug(f"Attempt {attempt}/{retries} for model {model}")
            return run_ollama(model, prompt, timeout=timeout)
        except RuntimeError as e:
            last_error = e
            log.warning(f"Attempt {attempt} failed: {e}")

            if attempt < retries:
                log.info(f"Retrying in {delay}s...")
                time.sleep(delay)
                # Exponential backoff
                delay = min(delay * 2, 60)

    raise SystemExit(f"All {retries} attempts failed. Last error: {last_error}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, help="agent id (e.g. planner)")
    ap.add_argument("--input", default="", help="user input / task")
    ap.add_argument("--context", default="", help="extra context text")
    ap.add_argument("--rag", default="", help="optional RAG query to inject additional context")
    ap.add_argument("--workspace", default="", help="workspace root for runtime tool execution")
    ap.add_argument("--list-agents", action="store_true", help="list active and shadowed agent definitions")
    ap.add_argument("--list-skills", action="store_true", help="list active and shadowed skill definitions")
    ap.add_argument("--permission-mode", choices=["permissive", "strict"], help="override runtime permission mode for this run")
    ap.add_argument("--show-permission-mode", action="store_true", help="show active runtime permission mode and exit")
    ap.add_argument("--show-agent-status", action="store_true", help="show latest manifest status for the agent and exit")
    ap.add_argument("--show-agent-output", action="store_true", help="show latest manifest status plus persisted output and exit")
    ap.add_argument("--save-permission-mode", action="store_true", help="persist the provided permission mode to config")
    ap.add_argument("--permission-scope", choices=["project", "user"], default="project", help="where to persist permission mode")
    ap.add_argument("--session-file", default="", help="path to persist runner session state")
    ap.add_argument("--resume-session", action="store_true", help="resume from an existing session file")
    ap.add_argument("--compact-session", action="store_true", help="compact old transcript before running")
    ap.add_argument(
        "--rag-k",
        type=int,
        default=6,
        help="top-k chunks to retrieve when --rag is provided",
    )
    # Allow command line to override timeout, but default to env or 1200
    timeout = ap.get_default("timeout") or OLLAMA_TIMEOUT
    ap.add_argument("--timeout", type=int, default=timeout, help="timeout in seconds")
    ap.add_argument("--retries", type=int, default=OLLAMA_RETRIES, help="number of retries")
    ap.add_argument("--verify-command", action="append", default=[], help="post-run verification command to execute inside the workspace")
    ap.add_argument("--require-path", action="append", default=[], help="workspace-relative file or directory that must exist after the run")
    ap.add_argument("--verbose", "-v", action="store_true", help="enable debug logging")
    args = ap.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace.strip() else None

    if not args.input and not any([
        args.list_agents,
        args.list_skills,
        args.show_permission_mode,
        args.show_agent_status,
        args.show_agent_output,
        args.save_permission_mode,
    ]):
        raise SystemExit("--input is required unless using an inspection flag")

    if args.save_permission_mode and not args.permission_mode:
        raise SystemExit("--save-permission-mode requires --permission-mode")

    if args.save_permission_mode:
        path = save_permission_mode(args.permission_mode, workspace=workspace, scope=args.permission_scope)
        print(f"Saved permission mode: {args.permission_mode} [{args.permission_scope}] -> {path}")
        return 0

    active_mode, active_source, active_path = resolve_permission_mode(workspace, args.permission_mode)

    if args.show_permission_mode:
        suffix = f" -> {active_path}" if active_path is not None else ""
        print(f"Permission mode: {active_mode} [{active_source}]{suffix}")
        return 0

    if args.show_agent_status or args.show_agent_output:
        print(render_agent_status(args.agent, workspace, include_output=args.show_agent_output))
        return 0

    if args.list_agents:
        print(render_agent_discovery(workspace))
        return 0

    if args.list_skills:
        print(render_skill_discovery(workspace))
        return 0

    log.debug(f"Loading agent profile: {args.agent}")
    validate_agent_policy(args.agent, workspace, active_mode)
    prof = load_profile(args.agent, workspace)
    system = (prof.get("system") or "").strip()
    model = prof["model"]
    tool_max_rounds = get_tool_max_rounds(prof)
    verify_commands = get_verify_commands(prof) + [command.strip() for command in args.verify_command if command.strip()]
    required_paths = get_required_paths(prof) + [path.strip() for path in args.require_path if path.strip()]

    log.debug(f"Using model: {model}")

    rag_context = ""
    if args.rag.strip():
        # Prefer lexical fallback to avoid heavy deps/freezes.
        # Chroma-based query remains available via query.py, but is not default.
        try:
            import subprocess as _sp

            rag_script = ROOT / "rag" / "scripts" / "lexical_rag.py"
            log.debug(f"Running RAG query: {args.rag}")
            p = _sp.run(
                [sys.executable, str(rag_script), "--q", args.rag.strip(), "--k", str(args.rag_k)],
                text=True,
                stdout=_sp.PIPE,
                stderr=_sp.PIPE,
                timeout=30,  # RAG should be fast
            )
            if p.returncode == 0:
                rag_context = p.stdout
                log.debug(f"RAG returned {len(rag_context)} chars")
            else:
                rag_context = f"(RAG query failed: {p.stderr.strip()})"
                log.warning(f"RAG query failed: {p.stderr.strip()}")
        except subprocess.TimeoutExpired:
            rag_context = "(RAG query timed out)"
            log.warning("RAG query timed out")
        except Exception as e:
            rag_context = f"(RAG unavailable: {e})"
            log.warning(f"RAG unavailable: {e}")

    merged_context = "\n\n".join([c for c in [args.context.strip(), rag_context.strip()] if c.strip()])

    prompt = build_prompt(
        agent_id=args.agent,
        system=system,
        context=merged_context,
        task=args.input,
        workspace=workspace,
        explicit_mode=active_mode,
    )

    log.info(f"Running agent {args.agent} with model {model}")
    session_file = None
    if args.session_file.strip():
        session_file = Path(args.session_file).expanduser().resolve()
    elif args.resume_session or args.compact_session:
        session_file = default_session_path(args.agent, workspace)

    manifest_path = None
    manifest = None
    try:
        manifest_path, manifest = start_manifest(args.agent, model, workspace)
        out = run_with_tool_support(
            agent_id=args.agent,
            model=model,
            prompt=prompt,
            workspace=workspace,
            retries=args.retries,
            timeout=args.timeout,
            session_file=session_file,
            resume_session=args.resume_session,
            compact_session=args.compact_session,
            max_rounds=tool_max_rounds,
            explicit_mode=active_mode,
        )
        verify_required_paths(required_paths, workspace)
        run_verification_commands(verify_commands, workspace, timeout=args.timeout)
        complete_manifest(manifest_path, manifest, out)
        sys.stdout.write(out)
        return 0
    except SystemExit as exc:
        if manifest_path is not None and manifest is not None:
            fail_manifest(manifest_path, manifest, str(exc), locals().get("out"))
        raise
    except KeyboardInterrupt:
        if manifest_path is not None and manifest is not None:
            fail_manifest(manifest_path, manifest, "Runner interrupted by user", locals().get("out"))
        raise
    except Exception as exc:
        if manifest_path is not None and manifest is not None:
            fail_manifest(manifest_path, manifest, str(exc), locals().get("out"))
        raise


if __name__ == "__main__":
    raise SystemExit(main())