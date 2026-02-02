from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path


def extract_unified_diff(text: str) -> str:
    """Extract unified diff from model output.

    Accepts either raw diff or markdown fenced block.
    """
    # Prefer fenced code blocks if present
    m = re.search(r"```(?:diff)?\n(.*?)\n```", text, re.S)
    if m:
        text = m.group(1)

    # Heuristic: start at first 'diff --git' or '--- a/'
    start = None
    for pat in ("diff --git ", "--- a/"):
        idx = text.find(pat)
        if idx != -1:
            start = idx
            break
    if start is not None:
        text = text[start:]

    return text.strip() + "\n"


def git_apply(project: Path, diff_text: str) -> tuple[bool, str]:
    diff_text = extract_unified_diff(diff_text)
    if not diff_text.strip():
        return False, "Empty diff"

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".patch") as f:
        f.write(diff_text)
        patch_path = f.name

    try:
        p = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", patch_path],
            cwd=str(project),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if p.returncode != 0:
            return False, p.stderr.strip() or p.stdout.strip()
        return True, "applied"
    finally:
        try:
            Path(patch_path).unlink(missing_ok=True)
        except Exception:
            pass
