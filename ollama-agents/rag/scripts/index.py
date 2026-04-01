#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import chromadb

from common import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_OLLAMA_HOST,
    DocChunk,
    chunk_text,
    iter_allowed_files,
    looks_sensitive,
    sha256,
)
from ollama_embed import embed_texts


def build_chunks(*, max_files: int | None = None, max_chunks: int | None = None) -> list[DocChunk]:
    chunks: list[DocChunk] = []
    file_count = 0

    for p in iter_allowed_files():
        if max_files is not None and file_count >= max_files:
            break
        file_count += 1

        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        parts = chunk_text(text)
        for idx, part in enumerate(parts):
            if looks_sensitive(part):
                # Drop sensitive chunks entirely.
                continue
            doc_id = sha256(str(p) + "::" + str(idx) + "::" + sha256(part))
            chunks.append(
                DocChunk(
                    doc_id=doc_id,
                    source_path=str(p),
                    chunk_index=idx,
                    text=part,
                )
            )
            if max_chunks is not None and len(chunks) >= max_chunks:
                return chunks

    return chunks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--persist",
        default=str(Path(__file__).resolve().parents[1] / "data" / "chroma"),
        help="Chroma persist directory",
    )
    ap.add_argument("--collection", default="openclaw_team")
    ap.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    ap.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST)
    ap.add_argument("--reset", action="store_true", help="Delete and recreate collection")
    ap.add_argument("--batch", type=int, default=8, help="upsert batch size (smaller = less RAM/VRAM)")
    ap.add_argument("--max-files", type=int, default=0, help="limit files (0 = no limit)")
    ap.add_argument("--max-chunks", type=int, default=0, help="limit chunks (0 = no limit)")
    args = ap.parse_args()

    client = chromadb.PersistentClient(path=args.persist)

    if args.reset:
        try:
            client.delete_collection(args.collection)
        except Exception:
            pass

    col = client.get_or_create_collection(args.collection, metadata={"hnsw:space": "cosine"})

    max_files = None if args.max_files == 0 else args.max_files
    max_chunks = None if args.max_chunks == 0 else args.max_chunks

    chunks = build_chunks(max_files=max_files, max_chunks=max_chunks)
    if not chunks:
        print("No chunks found (check allowlist paths).")
        return 0

    # Upsert in batches (small default to reduce pressure)
    BATCH = max(1, int(args.batch))
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i : i + BATCH]
        texts = [c.text for c in batch]
        ids = [c.doc_id for c in batch]
        metas = [
            {"source": c.source_path, "chunk_index": c.chunk_index}
            for c in batch
        ]
        embs = embed_texts(texts, model=args.embed_model, host=args.ollama_host)
        col.upsert(ids=ids, embeddings=embs, documents=texts, metadatas=metas)

    print(
        f"Indexed {len(chunks)} chunks into collection '{args.collection}' (persist={args.persist})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
