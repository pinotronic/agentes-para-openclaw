# Runner

`ollama_agent.py` es un runner mínimo para invocar un agente (perfil YAML) usando Ollama local.

## Requisitos
- Ollama instalado y corriendo
- Python 3

Instala deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python3 ollama_agent.py --agent planner --input "Implementar feature X" --context "(contexto opcional)"
```

Perfiles disponibles (ver `../agents/*.yaml`):
- planner
- debater
- test_writer
- implementer
- diagnoser
- reviewer

## Nota de recursos
Algunos modelos son pesados; Rex debe orquestar con criterio (tareas acotadas, logs reales, iteración por gating).
