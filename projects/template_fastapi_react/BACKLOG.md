# Backlog

## Cómo escribir tickets (regla)
- Un ticket = **1 entregable verificable**.
- Si falta `Verificación`, el ticket es inválido.

---

## Tickets

### T-001 — (ejemplo) Crear esqueleto de backend FastAPI
- Objetivo: 
- Perfil: fastapi
- Capa: interfaces/app/infra/domain (según aplique)
- Entrada (artefactos): SPEC.md, contracts/*
- Salida esperada:
  - `backend/` con estructura base
- Criterios de aceptación:
  - `pytest` corre
  - endpoint `/health` responde 200
- Verificación:
  - `cd backend && pytest -q`
- No-hacer:
  - No implementar lógica de negocio

### T-002 — (ejemplo) Crear esqueleto de frontend React
- Objetivo:
- Perfil: react
- Salida esperada:
  - `frontend/` app base
- Criterios de aceptación:
  - build ok
- Verificación:
  - `cd frontend && pnpm -s build`
