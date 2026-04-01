#!/usr/bin/env python3
"""Wrapper RAG híbrido para el pipeline de agentes.

Este script:
1. Ejecuta RAG lexical para obtener documentos relevantes
2. Suministra el resumen con LLM para contexto mejorado
3. Devuelve el contexto en formato JSON compatible con el pipeline

Uso desde run.py:
    run_agent("...", rag=f"python3 rag_with_summary_wrapper.py --q $query")
"""

import sys
import json
import subprocess
from pathlib import Path
from ollama import chat

# Configuración
DEFAULT_K = 6
DEFAULT_SUMMARY_MODEL = "qwen3.5:9b"

SUMMARY_PROMPT = """Analiza estos documentos técnicos y devuelve un resumen conciso en español:

{docs}

INSTRUCCIONES:
- Resuma lo MÁS IMPORTANTE para el contexto del proyecto
- Incluye: decisiones arquitectónicas, patrones, restricciones técnicas, lecciones
- 50-150 palabras máximo
- Lista con viñetas
- NO información externa, solo resume lo dado

SALIDA: JSON simple con campos: summary (texto), sources (lista de paths)
"""


def run_lexical_rag(query: str, k: int) -> list:
    """Ejecuta RAG lexical puro."""
    try:
        from scripts import lexical_rag
        return lexical_rag.run_lexical(query, k)
    except ImportError:
        # Fallback: ejecutar con el script directo
        result = subprocess.run(
            [sys.executable, "scripts/lexical_rag.py", "--q", query, "--k", str(k)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return parse_lexical_output(result.stdout)
        return []


def parse_lexical_output(output: str) -> list:
    """Parsea salida del RAG lexical."""
    docs = []
    # Simple parser para chunks
    chunks = output.split("\n---\n")
    for chunk in chunks:
        if "## [" in chunk:
            # Extrair metadata y texto
            lines = chunk.split("\n")
            doc_text = "\n".join([l for l in lines if l.strip() and not l.startswith("##")])
            if doc_text.strip():
                docs.append(doc_text)
    return docs[:k]


def summarize_context(docs: list[str], model: str = DEFAULT_SUMMARY_MODEL) -> str:
    """Resumir docs con LLM."""
    if not docs:
        return ""
    
    docs_text = "\n\n---\n\n".join(docs)
    context = SUMMARY_PROMPT.format(docs=docs_text)
    
    try:
        response = chat(
            model=model,
            messages=[{"role": "user", "content": context}],
            options={"temperature": 0.0, "num_predict": 150}
        )
        return response.get("message", {}).get("content", "")
    except Exception as e:
        print(f"⚠️ Error resumen LLM: {e}", file=sys.stderr)
        return ""


def rag_hybrid(query: str, k: int = DEFAULT_K, model: str = DEFAULT_SUMMARY_MODEL) -> dict:
    """RAG híbrido completo."""
    print(f"🔍 RAG lexical: buscando docs para '{query}'...")
    docs = run_lexical_rag(query, k)
    
    if not docs:
        return {"summary": "[No hay documentos relevantes]", "sources": []}
    
    print(f"📄 Encontrados: {len(docs)} docs")
    print("🤖 Resumiendo con LLM...")
    summary = summarize_context(docs, model)
    
    sources = [Path(d).name for d in docs]
    
    return {
        "summary": summary or "[Contexto no disponible]",
        "sources": sources,
        "docs_count": len(docs)
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="RAG híbrido para pipeline")
    ap.add_argument("--q", required=True, help="Consulta")
    ap.add_argument("--k", type=int, default=DEFAULT_K)
    ap.add_argument("--model", default=DEFAULT_SUMMARY_MODEL)
    ap.add_argument("--json", action="store_true", help="Salida JSON")
    ap.add_argument("--raw", action="store_true", help="Salida RAW")
    args = ap.parse_args()
    
    result = rag_hybrid(args.q, args.k, args.model)
    
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.raw:
        print(result.get("summary", ""))
    else:
        print("# RAG híbrido\n")
        print(result.get("summary", ""))
        if result.get("sources"):
            print(f"\n\nFuente(s): {', '.join(result['sources'])}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())