# Agentes para OpenClaw (Ollama Team)

Este repo contiene un "equipo" de agentes locales (Ollama) para ser orquestados por Rex (OpenClaw).

## Qué incluye
- Perfiles por rol (YAML) en `ollama-agents/agents/`
- Runner mínimo en Python para invocar perfiles con Ollama: `ollama-agents/runner/ollama_agent.py`
- Política de seguridad/privacidad: `ollama-agents/POLICY.md`
- Diseño inicial de RAG (memoria de trabajo): `ollama-agents/rag/README.md`

## Flujo de trabajo recomendado (TDD)
1) Planner → define DoD + plan + estrategia de pruebas.
2) Test Writer → escribe tests primero.
3) Implementer → implementa lo mínimo para pasar.
4) Runner → ejecuta tests/lint/build.
5) Diagnoser → interpreta fallos y propone fix mínimo.
6) Reviewer → revisión de calidad y riesgos.

## Seguridad
Nunca se indexa/guarda en RAG: datos personales/bancarios/secretos. Ver `ollama-agents/POLICY.md`.
