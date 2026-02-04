from __future__ import annotations

import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

# Logging setup
logging.basicConfig(
    level=os.environ.get("PATCH_LOG_LEVEL", "WARNING"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def extract_unified_diff(text: str) -> str:
    """Extract unified diff from model output.

    Accepts either raw diff or markdown fenced block.
    """
    # Prefer fenced code blocks if present
    m = re.search(r"```(?:diff)?\n(.*?)\n```", text, re.S)
    if m:
        text = m.group(1)
        log.debug("Extracted diff from markdown code block")

    # Heuristic: start at first 'diff --git' or '--- a/'
    start = None
    for pat in ("diff --git ", "--- a/"):
        idx = text.find(pat)
        if idx != -1:
            start = idx
            break
    if start is not None:
        text = text[start:]
        log.debug(f"Found diff start at position {start}")

    return text.strip() + "\n"


def validate_diff(diff_text: str) -> tuple[bool, str]:
    """Validate that the diff has basic structure.

    Returns (is_valid, error_message).
    """
    if not diff_text.strip():
        return False, "Empty diff"

    # Check for basic diff markers
    has_minus = "---" in diff_text or "-" in diff_text
    has_plus = "+++" in diff_text or "+" in diff_text

    # More specific checks for unified diff format
    has_file_headers = ("--- " in diff_text and "+++ " in diff_text) or "diff --git" in diff_text
    has_hunks = re.search(r"^@@.*@@", diff_text, re.MULTILINE) is not None

    if not has_file_headers:
        # Could be a simple diff without full headers
        if not (has_minus and has_plus):
            return False, "Diff missing file markers (--- and +++)"
        log.warning("Diff has minimal structure, may not apply cleanly")

    if not has_hunks:
        # Check if it at least has some change lines
        has_changes = re.search(r"^[+-][^+-]", diff_text, re.MULTILINE) is not None
        if not has_changes:
            return False, "Diff has no change lines (lines starting with + or -)"
        log.warning("Diff missing hunk headers (@@), may not apply cleanly")

    # Check for common LLM hallucinations
    if "```" in diff_text:
        log.warning("Diff still contains markdown code fence markers")

    if "<TASK>" in diff_text or "<CONTEXT>" in diff_text or "<SYSTEM>" in diff_text:
        return False, "Diff contains prompt markers - LLM did not generate proper diff"

    return True, "OK"


def git_apply(project: Path, diff_text: str, dry_run: bool = False) -> tuple[bool, str]:
    """Apply a diff to the project using git apply.

    Args:
        project: Path to the git repository
        diff_text: The diff text to apply
        dry_run: If True, only check if the diff would apply cleanly

    Returns:
        Tuple of (success, message)
    """
    diff_text = extract_unified_diff(diff_text)

    # Validate diff structure
    is_valid, error_msg = validate_diff(diff_text)
    if not is_valid:
        log.error(f"Invalid diff: {error_msg}")
        return False, error_msg

    log.debug(f"Diff size: {len(diff_text)} chars")

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".patch") as f:
        f.write(diff_text)
        patch_path = f.name

    try:
        # First do a dry run to check if it would apply
        check_cmd = ["git", "apply", "--check", "--whitespace=nowarn", patch_path]
        check_result = subprocess.run(
            check_cmd,
            cwd=str(project),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if check_result.returncode != 0:
            error = check_result.stderr.strip() or check_result.stdout.strip()
            log.error(f"Diff would not apply cleanly: {error}")
            return False, f"Diff check failed: {error}"

        if dry_run:
            log.info("Dry run successful - diff would apply cleanly")
            return True, "dry-run OK"

        # Actually apply the patch
        apply_cmd = ["git", "apply", "--whitespace=nowarn", patch_path]
        p = subprocess.run(
            apply_cmd,
            cwd=str(project),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if p.returncode != 0:
            error = p.stderr.strip() or p.stdout.strip()
            log.error(f"Failed to apply diff: {error}")
            return False, error

        log.info("Diff applied successfully")
        return True, "applied"
    finally:
        try:
            Path(patch_path).unlink(missing_ok=True)
        except Exception:
            pass
