# Template: FastAPI + React (TDD / Clean Architecture)

Este folder es una **plantilla de proceso** (artefactos + checklists) para que el trabajo con agentes sea **reanudable** (corte de luz, reinicio, etc.) y **sin invenciones**.

## Cómo usar

1) Copia este folder para un proyecto real (o inicialízalo ahí).
2) Rellena `SPEC.md`.
3) Congela contratos en `contracts/`.
4) Mantén `BACKLOG.md` con tickets atómicos.
5) Trabaja por fases (Planner → Test Writer → Implementer → Diagnoser → Reviewer → Debater), usando `MASTER_CHECKLIST.md` como gate.

## Comandos de verificación (placeholder)

- Backend: `make test` / `pytest -q`
- Frontend: `pnpm test` / `pnpm lint` / `pnpm build`

(Se ajusta al stack exacto cuando creemos el repo real.)
