# Ollama Agents (Rex team)

Este folder define un "equipo" de agentes locales (Ollama) que Rex orquesta.

## Filosofía
- Rex es el **orquestador**: decide, valida con herramientas (tests/lint/build), y entrega.
- Los agentes son **especialistas**: reciben tareas acotadas + contexto recuperado.
- Calidad se asegura con **TDD** + verificación real en terminal.

## Roles
- planner: descompone, define DoD, riesgos, plan TDD.
- debater: debate opciones y tradeoffs, propone recomendación.
- test_writer: escribe pruebas primero (TDD).
- implementer: implementa para pasar pruebas.
- diagnoser: interpreta fallos (logs) y propone fix mínimo.
- reviewer: revisión de calidad/seguridad/mantenibilidad.

## Seguridad / Privacidad
Ver `POLICY.md`.

## Uso
Ver `runner/`.
