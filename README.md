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

#Comandos de Uso
Agente Planner (planificar features):
python ollama_agent.py --agent planner --input "Crear endpoint /health" --context "Stack: Node/TS; Tests: jest"

Agente Test Writer (escribir tests):
python ollama_agent.py --agent test_writer --input "Función para validar email" --context "Framework: Jest"

Agente Implementer (implementar código):
python ollama_agent.py --agent implementer --input "POST /api/users" --context "Express.js, TypeScript"

Agente Debater (analizar pros/contras):
python ollama_agent.py --agent debater --input "Usar SQLite o PostgreSQL"

Agente Diagnoser (diagnosticar problemas):
python ollama_agent.py --agent diagnoser --input "El servidor no inicia"

Agente Reviewer (revisar código):
python ollama_agent.py --agent reviewer --input "<código a revisar>"
