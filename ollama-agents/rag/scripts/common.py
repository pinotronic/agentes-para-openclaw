from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]  # ollama-agents/
REPO_ROOT = ROOT.parent

ALLOWLIST_DIRS = [
    REPO_ROOT / "docs",
    REPO_ROOT / "ollama-agents",
]
ALLOWLIST_FILES = [
    REPO_ROOT / "README.md",
]

DEFAULT_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text-v2-moe:latest")
DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

# Very conservative patterns: if we see them, we drop/redact the chunk.
SENSITIVE_PATTERNS = [
    re.compile(r"\b\d{16}\b"),  # possible card (naive)
    re.compile(r"\b\d{18}\b"),  # possible CLABE length (naive)
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS key id
    re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH) PRIVATE KEY-----"),
    re.compile(r"(?i)github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]"),
    re.compile(r"(?i)secret\s*[:=]"),
    re.compile(r"(?i)token\s*[:=]"),
]


@dataclass
class DocChunk:
    doc_id: str
    source_path: str
    chunk_index: int
    text: str


def is_allowed_path(p: Path) -> bool:
    p = p.resolve()
    if p in ALLOWLIST_FILES:
        return True
    for d in ALLOWLIST_DIRS:
        try:
            p.relative_to(d.resolve())
            return True
        except Exception:
            pass
    return False


def iter_allowed_files() -> Iterable[Path]:
    # Explicit files
    for f in ALLOWLIST_FILES:
        if f.exists() and f.is_file():
            yield f

    # Directories
    for d in ALLOWLIST_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".md", ".txt", ".py", ".ts", ".js", ".yaml", ".yml"}:
                # skip virtualenvs and data dirs (cross-platform)
                parts = p.parts
                if ".venv" in parts or "node_modules" in parts or ("rag" in parts and "data" in parts):
                    continue
                yield p


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def looks_sensitive(text: str) -> bool:
    for pat in SENSITIVE_PATTERNS:
        if pat.search(text):
            return True
    return False


def chunk_text(text: str, max_chars: int = 1800, overlap: int = 150) -> list[str]:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    chunks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        end = min(n, i + max_chars)
        chunk = text[i:end]
        # Try not to cut mid-line if possible
        if end < n:
            last_nl = chunk.rfind("\n")
            if last_nl > int(max_chars * 0.6):
                end = i + last_nl
                chunk = text[i:end]
        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
        # If we reached the end, we're done.
        if end >= n:
            break
        # Advance with overlap, but never go backwards.
        next_i = end - overlap
        if next_i <= i:
            next_i = end
        i = next_i
    return chunks
