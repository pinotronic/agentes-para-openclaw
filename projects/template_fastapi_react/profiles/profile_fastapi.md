# Perfil: FastAPI (Python)

## Objetivo
Backend API con TDD y Clean Architecture.

## Convenciones
- Dominio puro (sin FastAPI/SQLAlchemy/HTTP)
- App/use-cases orquestan
- Infra implementa repositorios/adapters
- Interfaces (FastAPI routers) solo traducen HTTP ↔ casos de uso
- DI, sin singletons con estado

## Comandos (placeholder)
- Tests: `pytest -q`
- Lint: `ruff check .`
- Format: `ruff format .`

## Estructura sugerida
- `backend/src/domain`
- `backend/src/app`
- `backend/src/infra`
- `backend/src/interfaces/http`
- `backend/tests`
