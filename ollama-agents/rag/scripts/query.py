#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import chromadb

from common import DEFAULT_EMBED_MODEL, DEFAULT_OLLAMA_HOST
from ollama_embed import embed_texts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True, help="query text")
    ap.add_argument(
        "--persist",
        default=str(Path(__file__).resolve().parents[1] / "data" / "chroma"),
        help="Chroma persist directory",
    )
    ap.add_argument("--collection", default="openclaw_team")
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    ap.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST)
    args = ap.parse_args()

    client = chromadb.PersistentClient(path=args.persist)
    col = client.get_collection(args.collection)

    q_emb = embed_texts([args.q], model=args.embed_model, host=args.ollama_host)[0]

    res = col.query(query_embeddings=[q_emb], n_results=args.k, include=["documents", "metadatas", "distances"])

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    print("# RAG context pack\n")
    print(f"Query: {args.q}\n")

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), start=1):
        src = (meta or {}).get("source", "unknown")
        chunk_index = (meta or {}).get("chunk_index", "?")
        print(f"## [{i}] {src} (chunk {chunk_index}) — distance={dist:.4f}\n")
        print(doc.strip())
        print("\n---\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
