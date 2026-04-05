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


def _resolve_safe_path(project: Path, path_str: str) -> Path:
    """Resolve a relative path and ensure it stays inside the project root."""
    candidate = Path(path_str)
    if candidate.is_absolute():
        raise ValueError(f"Absolute paths are not allowed: {path_str}")

    full_path = (project / candidate).resolve(strict=False)
    project_root = project.resolve(strict=False)
    try:
        full_path.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {path_str}") from exc
    return full_path


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


def apply_diff_manually(project: Path, diff_text: str) -> tuple[bool, str]:
    """Manually apply a diff, creating new files and overwriting existing ones.
    This is a fallback for when git apply is too strict.
    Assumes unified diff format where all lines are additions for new files.
    """
    log.info("Attempting manual diff application...")
    lines = diff_text.splitlines()
    
    current_file_path: Path | None = None
    file_content_lines: list[str] = []
    in_hunk = False
    files_written = 0

    def flush_current_file() -> tuple[bool, str]:
        nonlocal file_content_lines, files_written
        if current_file_path is None:
            return True, "OK"
        if not file_content_lines:
            return False, f"No file content collected for {current_file_path}"

        try:
            full_path = _resolve_safe_path(project, str(current_file_path))
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("\n".join(file_content_lines), encoding="utf-8")
            log.debug(f"Manually wrote: {full_path}")
            files_written += 1
            file_content_lines = []
            return True, "OK"
        except Exception as e:
            return False, f"Error writing file {current_file_path}: {e}"

    for line in lines:
        if line.startswith("--- "):
            # Start of a new file diff, but we are only interested in '+++' for the new path
            continue
        elif line.startswith("+++ "):
            ok, message = flush_current_file()
            if not ok:
                return False, message
            
            # Extract new file path, remove 'b/' prefix
            if not line.startswith("+++ b/"):
                return False, f"Unsupported diff target header: {line}"
            new_file_str = line[len("+++ b/"):]
            current_file_path = Path(new_file_str)
            in_hunk = False
        elif line.startswith("@@"):
            if not line.startswith("@@ -0,0"):
                return False, "Manual patch application only supports new-file diffs"
            in_hunk = True
        elif in_hunk:
            if line.startswith("+"):
                file_content_lines.append(line[1:])
            elif line.startswith("\\"):
                continue
            else:
                return False, "Manual patch application only supports added lines for new files"
        else:
            # Lines outside of recognized diff headers or hunks for new files are ignored
            continue

    # Save the last file
    ok, message = flush_current_file()
    if not ok:
        return False, message
    if files_written == 0:
        return False, "Manual patch application found no supported file writes"
    
    log.info("Manual diff application completed successfully.")
    return True, "manually applied"


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

    # Fix for new files: git apply expects '--- /dev/null' for new files
    # but LLMs might generate '--- a/path/to/file'
    # Detect pattern: '--- a/path\n+++ b/path\n@@ -0,0 +...'
    # And replace '--- a/path' with '--- /dev/null'
    def fix_new_file_headers(d: str) -> str:
        # Regex to find diff headers for new files
        # Group 1: '--- a/...'
        # Group 2: '+++ b/...'
        # Group 3: '@@ -0,0 +...'
        pattern = re.compile(r"^(--- a/.*)(\n\+\+\+ b/.*)(\n@@ -0,0 \+.*@@)", re.MULTILINE)

        def replacer(match):
            # Replace the first line (--- a/...) with '--- /dev/null'
            return "--- /dev/null" + match.group(2) + match.group(3)
        return pattern.sub(replacer, d)

    diff_text = fix_new_file_headers(diff_text)
    log.debug(f"Modified diff after header fix:\n{diff_text}")

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
            log.warning(f"git apply --check failed: {error}. Attempting manual application as fallback.")
            # Fallback to manual application if git apply check fails
            return apply_diff_manually(project, diff_text)

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
