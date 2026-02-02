#!/usr/bin/env python3
"""Lexical RAG (no vectors) to avoid heavy deps and freezes.

- Uses allowlist file set from `common.py`.
- Splits into chunks.
- Scores chunks by simple token overlap (plus small bonuses).

This is a pragmatic fallback when Chroma/embeddings are unstable.
"""

from __future__ import annotations

import argparse
import math
import re
from collections import Counter

from common import chunk_text, iter_allowed_files, looks_sensitive

WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_\-/]{2,}")


def tokenize(s: str) -> list[str]:
    return [w.lower() for w in WORD_RE.findall(s)]


def score(query_tokens: list[str], chunk_tokens: list[str]) -> float:
    if not query_tokens or not chunk_tokens:
        return 0.0

    q = Counter(query_tokens)
    c = Counter(chunk_tokens)

    # Weighted overlap
    overlap = 0.0
    for t, w in q.items():
        if t in c:
            overlap += w * (1.0 + math.log(1 + c[t]))

    # Normalize by chunk length a bit
    denom = math.sqrt(len(chunk_tokens) + 50)
    return overlap / denom


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--format", choices=["md", "toon"], default="md")
    ap.add_argument("--max-files", type=int, default=400, help="limit scanned files (0 = no limit)")
    ap.add_argument("--max-chunks", type=int, default=1200, help="limit scanned chunks (0 = no limit)")
    args = ap.parse_args()

    q_tokens = tokenize(args.q)

    # Keep only top-N while scanning to avoid large memory/sort cost.
    keep_n = max(args.k * 12, 50)
    results: list[tuple[float, str, int, str]] = []  # score, path, idx, text

    file_count = 0
    chunk_count = 0

    def maybe_add(item: tuple[float, str, int, str]) -> None:
        nonlocal results
        results.append(item)
        if len(results) <= keep_n:
            return
        # Drop worst 25% occasionally
        results.sort(key=lambda x: x[0], reverse=True)
        results = results[: int(keep_n * 0.75)]

    for p in iter_allowed_files():
        if args.max_files and file_count >= args.max_files:
            break
        file_count += 1

        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for idx, ch in enumerate(chunk_text(text)):
            if looks_sensitive(ch):
                continue
            chunk_count += 1
            if args.max_chunks and chunk_count > args.max_chunks:
                break

            s = score(q_tokens, tokenize(ch))
            if s > 0:
                maybe_add((s, str(p), idx, ch))

    results.sort(key=lambda x: x[0], reverse=True)
    top = results[: args.k]

    if args.format == "toon":
        from toon_min import toon_table

        rows = []
        for i, (s, path, idx, ch) in enumerate(top, start=1):
            rows.append(
                {
                    "rank": i,
                    "source": path,
                    "chunk": idx,
                    "score": round(float(s), 6),
                    "snippet": ch.strip(),
                }
            )
        print("query: " + args.q)
        print(toon_table("chunks", rows))
        return 0

    print("# RAG context pack (lexical)\n")
    print(f"Query: {args.q}\n")

    for i, (s, path, idx, ch) in enumerate(top, start=1):
        print(f"## [{i}] {path} (chunk {idx}) — score={s:.4f}\n")
        print(ch.strip())
        print("\n---\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
