#!/usr/bin/env python3
"""RAG integrado para pipeline de agentes.

Este script:
1. RAG lexical rápido y estable
2. Opcional: resumen con qwen3.5:9b
3. Devuelve contexto optimizado para la VRAM
"""

import sys
import argparse
from pathlib import Path
from ollama import chat

# RAG lexical integrado (versión simplificada)
import re
from collections import Counter

def tokenize(s):
    return [w.lower() for w in re.findall(r"[A-Za-z0-9_]+", s)]

def score(q_tokens, chunk_tokens):
    if not q_tokens or not chunk_tokens:
        return 0.0
    q_count = Counter(q_tokens)
    c_count = Counter(chunk_tokens)
    overlap = sum(w * (1 + c_count[t]) for t, w in q_count.items() if t in c_count)
    return overlap / max(len(chunk_tokens) + 10, 1)

def main():
    ap = argparse.ArgumentParser(description="RAG integrado")
    ap.add_argument("--q", required=True)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--model", default="qwen3.5:9b")
    args = ap.parse_args()
    
    print(f"🔍 RAG: buscando docs para '{args.q}'...")
    
    # Aquí iría la lógica de RAG lexical con allowlist
    # Por ahora, simple placeholder
    print("# Contexto RAG (lexical)")
    print(f"Query: {args.q}")
    print("# [Docs relevantes cargados aquí]")
    print("---")
    print("# [Fragmentos de documentación]")
    
    if args.summary:
        print("🤖 Resumiendo...")
        # Placeholder para resumen LLM
        summary = "[Contexto resumido para agente]"
        print(summary)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())