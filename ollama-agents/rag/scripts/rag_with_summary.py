#!/usr/bin/env python3
"""RAG híbrido: RAG léxico + Resumen con LLM para agentes

Combina:
1. RAG lexical (rápido, estable) para encontrar docs relevantes
2. LLM (Qwen) para resumir y contextualizar

Resultado: Contexto mejorado sin saturar VRAM.
"""

from __future__ import annotations

import argparse
import sys
import re
import math
from collections import Counter
from pathlib import Path

from common import chunk_text, iter_allowed_files, looks_sensitive

try:
    from ollama import chat
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ollama", "-q"])
    from ollama import chat


SUMMARY_PROMPT = """Analiza los siguientes documentos técnicos y devuelve un RESUMEN CONCISO en español:

{docs}

Instrucciones:
- Resuma lo más IMPORTANTE para entender el contexto
- Incluye: decisiones arquitectónicas, patrones, restricciones, lecciones
- Mantén entre 50-150 palabras (suficiente, no excesivo)
- Usa lista con viñetas
- Omiti detalles triviales
- NO añadas información externa

Salida: lista concisa con viñetas
"""

DEFAULT_SUMMARY_MODEL = "qwen3.5:9b"
DEFAULT_K = 6


def summarize_with_llm(docs_text: str, model: str = DEFAULT_SUMMARY_MODEL) -> str:
    """Envía docs al LLM para resumen."""
    try:
        context = SUMMARY_PROMPT.format(docs=docs_text)
        response = chat(model=model, messages=[{"role": "user", "content": context}],
                       options={"temperature": 0.0, "num_predict": 200})
        return response.get("message", {}).get("content", "")
    except Exception as e:
        print(f"⚠️ Error resumen LLM: {e}", file=sys.stderr)
        return """- [Contexto no disponible]
- Usa RAG léxico puro si ocurre
"""


def tokenize(s: str) -> list:
    return [w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_\-/]{2,}", s)]


def score(query_tokens, chunk_tokens) -> float:
    if not query_tokens or not chunk_tokens:
        return 0.0
    q = Counter(query_tokens)
    c = Counter(chunk_tokens)
    overlap = sum(w * (1.0 + math.log(1 + c[t])) for t, w in q.items() if t in c)
    return overlap / math.sqrt(len(chunk_tokens) + 50)


def main() -> int:
    ap = argparse.ArgumentParser(description="RAG híbrido: Léxico + LLM Summary")
    ap.add_argument("--q", required=True, help="Consulta RAG")
    ap.add_argument("--k", type=int, default=DEFAULT_K, help=f"Top-K (default: {DEFAULT_K})")
    ap.add_argument("--model", default=DEFAULT_SUMMARY_MODEL, help=f"Modelo LLM (default: {DEFAULT_SUMMARY_MODEL})")
    ap.add_argument("--raw", action="store_true", help="Salida RAW sin Markdown")
    args = ap.parse_args()

    print("🔍 Buscando documentos relevantes...\n")
    
    q_tokens_raw = tokenize(args.q)
    results = []
    chunk_count = 0
    
    for p in iter_allowed_files():
        if len(results) >= args.k * 2:
            break
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for idx, ch in enumerate(chunk_text(text)):
            if looks_sensitive(ch):
                continue
            chunk_count += 1

            s = score(q_tokens_raw, tokenize(ch))
            if s > 0.15:
                results.append((s, str(p), idx, ch))
                if len(results) >= args.k * 2:
                    break
            
            if chunk_count > 1000:
                break

    results.sort(key=lambda x: x[0], reverse=True)
    top_docs = results[:args.k]

    if not top_docs:
        print("\n⚠️ No se encontraron documentos relevantes\n")
        return 1

    docs_text = "\n\n---\n\n".join([d[3] for d in top_docs])
    print(f"📄 {len(top_docs)} documentos encontrados\n")

    print(f"🤖 Resumiendo con {args.model}...\n")
    summary = summarize_with_llm(docs_text, args.model)

    if not summary:
        print("⚠️ Resumen vacío (fallback a léxico puro)\n")
        print("# RAG context pack (lexical fallback)\n")
        print(f"Query: {args.q}\n")
        for i, (s, path, idx, ch) in enumerate(top_docs, start=1):
            print(f"## [{i}] {path} (chunk {idx}) — score={s:.4f}\n")
            print(ch.strip())
            print("\n---\n")
        return 0

    print("# RAG context pack (híbrido)\n")
    print(f"Query: {args.q}\n")
    print(summary)

    if not args.raw:
        print("\n#===")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())