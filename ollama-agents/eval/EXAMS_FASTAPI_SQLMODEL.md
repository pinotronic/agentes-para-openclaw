# Exámenes de agentes (Opción B) — FastAPI + SQLModel + pytest (+ React opcional)

Objetivo: evaluar y mejorar cada agente para que sea **experto en su oficio** y **entregue correctamente** (completo, verificable, sin inventar alcance), antes de trabajar en el proyecto `inmobiliaria`.

## Stack objetivo
- Backend: **Python + FastAPI**
- Persistencia: **SQLModel/SQLAlchemy** (SQLite para tests/dev; Postgres opcional)
- Tests: **pytest + httpx/TestClient + pytest-cov**
- Frontend: **React** (solo si el plan lo incluye)

## Scorecard (0–5 por rubro)
- Rol correcto (sigue su oficio; no invade otros)
- Completitud del entregable
- Precisión técnica (FastAPI/SQLModel/pytest)
- Manejo de edge cases
- Verificación/evidencia (comandos, asserts, criterios)
- No inventar alcance / supuestos explícitos
- Alineación con DIRECTOR.MD (anti-truncado, atomicidad, TDD, DI)

**Criterio de aprobación:**
- Planner/TestWriter/Reviewer ≥ 28/35
- Implementer/Diagnoser ≥ 26/35
- Debater ≥ 26/35 (por calidad de tradeoffs + verificabilidad)

## Exámenes por agente

### 1) PLANNER — Examen de oficio (P1)
**Prompt:** Diseña el MVP de una mini-inmobiliaria.
- Usuarios/roles: Admin, Agente, Visitante
- Moneda: MXN
- MVP: alta/edición de inmuebles, listado con filtros/orden/paginación, detalle, auth básica.
- No incluye: pagos, mapas, chat, CRM completo.

**Debe incluir (mínimo):**
- Contratos API completos (status + errores estándar + esquemas)
- Modelo de datos coherente con filtros (índices)
- Estrategia TDD + plan por hitos con criterios de aceptación
- Seguridad mínima (hashing, JWT/refresh, rate limit básico)

**Fallas típicas a penalizar:** endpoints incompletos, no define errores/paginación, modelo de datos no soporta filtros.

### 2) TEST_WRITER — Examen de oficio (T1)
**Input:** copiar/pegar los endpoints del plan del PLANNER.
**Debe producir:**
- Matriz por capas
- Cobertura por endpoint (happy/validación/auth/notfound/conflict/paginación)
- Factories/fixtures
- Estrategia DB (transaction rollback o DB efímera)
- Comandos de ejecución

**Falla crítica:** inventar endpoints/features que el plan no definió.

### 3) IMPLEMENTER — Examen (I1)
**Input:** un set mínimo de tests (del T1) que falla.
**Debe:**
- Implementar lo mínimo para pasar
- Mantener DI por request
- Mantener dominio/app sin imports de FastAPI/SQLModel
- No cambiar tests sin permiso

### 4) DIAGNOSER — Examen (D1)
**Input:** salida real de pytest con stacktrace.
**Debe:**
- Triage SEV + evidencia
- Causa proximal vs raíz
- Fix mínimo (archivo/capa)
- Plan de verificación + prueba de regresión sugerida

### 5) REVIEWER (Auditor) — Examen (R1)
**Input:** diff (o árbol) del implementer + tests.
**Debe:**
- Hallazgos P0/P1/P2 con evidencia
- Checklist de calidad marcada
- Plan de remediación verificable

### 6) DEBATER — Examen (B1)
**Input:** decisión “JWT refresh vs cookies httpOnly” y “SQLModel vs SQLAlchemy”.
**Debe:**
- ≥2 opciones, tradeoffs
- Recomendación + cómo validarla
- Tabla P0/P1/P2 de mejoras + verificación

## Registro de resultados
- Guardar resultados por corrida en: `ollama-agents/eval/results/YYYY-MM-DD_runN.md`
- Guardar cambios propuestos a YAML en: `ollama-agents/eval/patches/YYYY-MM-DD/*.diff`

## Proceso iterativo
1. Ejecutar examen
2. Calificar con scorecard
3. Identificar 1–3 ajustes al YAML/prompt
4. Aplicar ajuste
5. Repetir el mismo examen hasta aprobar
