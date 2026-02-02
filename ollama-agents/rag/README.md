# RAG (memoria de trabajo)

Objetivo: dar a los agentes contexto consistente sobre **cómo trabajamos** y **cómo es el repo** sin meter datos privados.

## Principios
- **Allowlist** (preferido): indexar únicamente rutas seguras.
- Nunca indexar secretos/datos personales/bancarios (ver `../POLICY.md`).
- **No se guardan chats** (solo docs/código permitido).
- El RAG asiste; la verificación final siempre es por herramientas (tests/lint/build).

## Modo recomendado (estable): Lexical RAG (sin vectores)
Este modo evita dependencias pesadas (Chroma/onnx/tokenizers) que pueden congelar la máquina.

Consulta (no requiere indexado):

```bash
python3 scripts/lexical_rag.py --q "flujo TDD" --k 6
```

## Modo experimental: Chroma + embeddings
Existe, pero **NO es default** debido a congelamientos reportados.

- Vector DB: Chroma (persistente)
- Embeddings: Ollama `nomic-embed-text-v2-moe:latest`

Instalación:

```bash
cd ollama-agents/rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Indexar (si tu máquina lo tolera):

```bash
python3 scripts/index.py --reset --batch 1 --max-chunks 50
```

Consultar:

```bash
python3 scripts/query.py --q "flujo TDD" --k 6
```

## Qué se consulta (allowlist)
- `README.md`
- `docs/**`
- `ollama-agents/**`

## Nota
Si un chunk parece sensible según patrones conservadores, se omite.
