from __future__ import annotations

import requests


def embed_texts(texts: list[str], *, model: str, host: str, timeout_s: int = 120) -> list[list[float]]:
    """Embed texts via Ollama embeddings API.

    Uses POST {host}/api/embeddings with {model, prompt}.

    Note: Ollama's embeddings endpoint is per-text; we loop.
    """
    out: list[list[float]] = []
    url = host.rstrip("/") + "/api/embeddings"

    for t in texts:
        r = requests.post(url, json={"model": model, "prompt": t}, timeout=timeout_s)
        r.raise_for_status()
        data = r.json()
        emb = data.get("embedding")
        if not emb:
            raise RuntimeError(f"No embedding returned from Ollama for model={model}")
        out.append(emb)

    return out
