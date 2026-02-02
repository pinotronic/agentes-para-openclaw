# Pipeline (MVP)

Pipeline TDD multi-stack para orquestar el equipo de agentes:

1) planner → plan + DoD + estrategia de pruebas
2) test_writer → tests primero
3) implementer → implementación mínima
4) run checks → tests/lint/typecheck (según adapter)
5) diagnoser → interpreta fallos
6) repeat hasta pasar o hasta llegar al límite

## Objetivo
- Core genérico + adaptadores por stack.
- Serial (1 modelo a la vez).

## Uso (MVP)

```bash
python3 -m ollama_agents_pipeline.run --project /ruta/al/repo --task "..." \
  --max-iters 5 --rag "TDD"
```

> Nota: el módulo se instala como scripts locales (ver `docs/SETUP.md`).
