#!/usr/bin/env python3
"""Minimal agent runner for Ollama.

Reads an agent profile YAML, composes system+user prompt, calls `ollama run`.
Designed to be orchestrated by Rex.

Usage:
  python3 ollama_agent.py --agent planner --input "..."
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

# Configuration from environment variables
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", 300))  # 5 minutes default
OLLAMA_RETRIES = int(os.environ.get("OLLAMA_RETRIES", 2))
OLLAMA_RETRY_DELAY = int(os.environ.get("OLLAMA_RETRY_DELAY", 5))  # seconds

# Logging setup
logging.basicConfig(
    level=os.environ.get("AGENT_LOG_LEVEL", "WARNING"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

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


def run_ollama(model: str, prompt: str, timeout: int = OLLAMA_TIMEOUT) -> str:
    """Run ollama with timeout."""
    try:
        p = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        if p.returncode != 0:
            raise RuntimeError(f"ollama failed (code {p.returncode}):\n{p.stderr}")
        return p.stdout
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
    ap.add_argument("--input", required=True, help="user input / task")
    ap.add_argument("--context", default="", help="extra context text")
    ap.add_argument("--rag", default="", help="optional RAG query to inject additional context")
    ap.add_argument(
        "--rag-k",
        type=int,
        default=6,
        help="top-k chunks to retrieve when --rag is provided",
    )
    ap.add_argument("--timeout", type=int, default=OLLAMA_TIMEOUT, help="timeout in seconds")
    ap.add_argument("--retries", type=int, default=OLLAMA_RETRIES, help="number of retries")
    ap.add_argument("--verbose", "-v", action="store_true", help="enable debug logging")
    args = ap.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    log.debug(f"Loading agent profile: {args.agent}")
    prof = load_profile(args.agent)
    system = (prof.get("system") or "").strip()
    model = prof["model"]

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

    prompt = (
        f"<SYSTEM>\n{system}\n</SYSTEM>\n\n"
        f"<CONTEXT>\n{merged_context}\n</CONTEXT>\n\n"
        f"<TASK>\n{args.input.strip()}\n</TASK>\n"
    )

    log.info(f"Running agent {args.agent} with model {model}")
    out = run_ollama_with_retry(model, prompt, retries=args.retries, timeout=args.timeout)
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
