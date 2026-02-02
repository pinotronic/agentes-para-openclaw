# agentes-para-openclaw

Equipo inicial de agentes locales (Ollama) orquestados por Rex (OpenClaw), pensado para acelerar desarrollo de software con enfoque **TDD**.

## Quick start

Requisitos:
- Ollama instalado y funcionando
- Python 3

```bash
cd ollama-agents/runner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 ollama_agent.py --agent planner --input "Crear endpoint /health" \
  --context "Stack: Node/TS; Tests: jest"
```

## Estructura
- `ollama-agents/` → perfiles, runner, policy, diseño RAG.
- `docs/` → documentación del proyecto.

## Nota
Rex valida todo con herramientas (tests/lint/build). Los agentes no son la autoridad final: son especialistas.
