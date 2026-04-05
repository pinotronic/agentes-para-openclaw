# MEMORY.md - Long-term memory

Aquí se almacenan las decisiones importantes, el contexto y las lecciones aprendidas.

## People
- **Pino Vargas**: quiere que le llame **“Pinotronic”**. Desarrolla software.
- **GitHub Agentes Repo**: https://github.com/pinotronic/agentes-para-openclaw
- **Brave Search API Key**: BSAgJTb6cW96AuKyYQIU0B0sz6hrjXI
- **GitHub Key Fingerprint**: SHA256:CmB+eXGAj0T0qZkS0IFz6PUO47mFC2+iLBEHB30pNDQ

## Assistant identity
- Mi nombre es **Rex** (asistente de Pinotronic).
- Emoji firma: 🦖

## Principios operativos
- Los agentes (`planner`, `test_writer`, `implementer`, `diagnoser`, `reviewer`, `debater`, `code_critic`, `defender`) son mis herramientas indispensables para el desarrollo de software.
- **Flujo Red Team / Blue Team:** CODE_CRITIC (crítica) → DEFENDER (soluciones) → IMPLEMENTER (aplica)
- **Ubicación de Agentes:** `~/.openclaw/workspace/ollama-agents/`
- **Orquestador:** `~/.openclaw/workspace/ollama-agents/pipeline/run.py`
- **Pipeline Red/Blue:** `~/.openclaw/workspace/ollama-agents/pipeline/run_redblue.py`
- Siempre debo recordar cómo utilizar y mejorar estas herramientas.

## Red Team / Blue Team (Seguridad y Calidad de Código)

Basado en **BlueCodeAgent** de Microsoft Research. Este flujo rodea al IMPLEMENTER con revisión defensiva.

### Agentes

| Agente | Rol | ID YAML | Propósito |
|--------|-----|---------|-----------|
| `code_critic` | 🔴 Red | `code_critic.yaml` | Hacker ético: busca fallos, edge cases, vulnerabilidades |
| `defender` | 🔵 Blue | `defender.yaml` | Ingeniero defensivo: propone soluciones concretas |

### Categorías de crítica (CODE_CRITIC)

| Prioridad | Categoría | Ejemplos |
|-----------|-----------|----------|
| **P0** | Seguridad | SQL injection, XSS, auth bypass, hardcoded secrets |
| **P1** | Edge Cases | null, vacío, valores extremos, división por cero |
| **P2** | Lógica | Off-by-one, condiciones incorrectas, lógica invertida |
| **P3** | Performance | N+1 queries, memory leaks, loops costosos |
| **P4** | Arquitectura | God classes, acoplamiento tight, SRP violado |

### Flujo de uso

```
1. IMPLEMENTER escribe código
2. CODE_CRITIC lo critica (P0→P4)
3. DEFENDER propone soluciones exactas
4. IMPLEMENTER aplica los fixes
```

### Ejecución

```bash
cd ~/.openclaw/workspace/ollama-agents
source .venv/bin/activate
python pipeline/run_redblue.py --code "código" --plan "descripción del proyecto"
```

### Cuándo usar

- **Siempre antes de commit:** Después de implementar código significativo
- **En Fase C del pipeline:** Después de IMPLEMENTER, antes de DIAGNOSER
- **Cuando hay bugs inexplicables:** El CODE_CRITIC puede encontrar la causa raíz
- **Antes de аудит final:** REVIEWER ya tiene menos P0 que encontrar

### Output típico

CODE_CRITIC entrega tabla con:
- `#` (ID), `Tipo`, `Ubicación` (archivo:línea), `Descripción`, `Severidad`

DEFENDER entrega para cada crítica:
- Código exacto de la solución
- Archivo a modificar
- Tests a agregar
- Verificación

### Prueba real (2026-03-31)

- Código revisado: `updateGridCalculations` de TiledCutter
- Resultado: 15 críticas (3 P0 seguridad, 4 P1 edge cases, 4 P2 lógica, 2 P3 perf, 2 P4 arquitectura)
- Fix aplicado y validado con build passing

## Flujo de Trabajo Crítico (Agentes - Orquestador)
- **Rol de Rex:** Orquestador / Director de Agentes.
- **Flujo General:** Requerimientos (Pinotronic) → Orquestador (`ollama-agents/pipeline/run.py`) → Ejecución Secuencial de Agentes Internos (Planner, Test Writer, Implementer, Code Critic, Defender, Diagnoser, Reviewer).
- **Invocación de Agentes:** El script `run.py` es el orquestador principal y llama a los agentes internos en un orden predefinido (ej. `planner` primero). No se especifica un agente individual directamente a través de argumentos externos al `run.py`.
- **Ciclo de Desarrollo TDD (Mandatorio):** Crear Test → Crear Código Mínimo → Probar Código → Si falla, Diagnosticar y Repetir el ciclo **hasta que el código pase los tests**.
- **Doble Verificación:** Utilizar el agente `debater` para obtener un punto de vista alternativo y analizar soluciones.
- **Mejora Continua:** Los agentes deben ser mejorados iterativamente para optimizar los resultados.

## Restricción Crítica (VRAM)
- **Hardware:** RTX 5090.
- **Política de VRAM (Ollama):**
  - Los modelos se cargan por demanda y permanecen activos 5 minutos post-solicitud.
  - **Descarga manual:** `ollama stop <nombre_modelo>` para liberar VRAM inmediatamente (preferido para Rex).
  - **Regla:** Solo se permite **un modelo LLM cargado a la vez** para tareas pesadas o agentes activos.
  - *Acción:* Obligatorio usar `ollama stop <nombre_modelo>` entre la ejecución de modelos LLM pesados o cuando un agente termina.

## Política de Memoria (Persistencia)
- **Guardado Iterativo (CRÍTICO):** Guardar avances y decisiones significativas en la memoria persistente (`MEMORY.md` o `memory/YYYY-MM-DD.md`) después de cada iteración o paso clave, no al final, para mitigar la pérdida de contexto por reinicios.
- **Convención de Logs:** Los trabajos y tareas se deben guardar en `memory/YYYY-MM-DD.md`.

## Preferences
- Tono directo, sin relleno.
- **Carpeta de trabajo oficial:** `/media/administrador/IA2/compartida/` (NO usar `~/.openclaw/workspace/` para proyectos de usuario)

## Tooling / Agent Ops
- **Mission Control (pipeline tracking):** se agregó tracking mínimo al pipeline `ollama-agents/pipeline/run.py`.
  - Artefactos por run en `<project>/.mission_control/` (summary.json + events.jsonl, y puntero latest).
  - CLI: `ollama-agents/pipeline/mc.py` (list/show/tail).
  - Desactivar: `PIPELINE_MISSION_CONTROL=0`.

## Channels
- Nos comunicamos también por **Telegram** IMPORTANTE con voz y texto.

## Preferencias de Desarrollo de Software
- **Manual de Director:** LEER SIEMPRE `/media/administrador/IA2/compartida/inmobiliaria/DIRECTOR.md` al iniciar tareas de código. Contiene las reglas maestras de arquitectura y flujo.
- **Metodología:** TDD Estricto. Primero test, luego código.
  - **Atomicidad:** Una tarea a la vez para el implementador. No "big bangs".
  - **Tests:** Cobertura exhaustiva (bordes, errores, validaciones). Regla 1:1+.
- **Arquitectura:** Clean Architecture Real.
  - Dominio puro (sin frameworks).
  - Infraestructura separada (SQLModel aquí).
  - Interfaces (API) desacopladas.
  - **NO Singletons** para DB. Usar Dependency Injection.
- **Control de versiones:** GitHub. Commits frecuentes y descriptivos.
- **Entorno de trabajo:**
  - GPU: RTX 5090
  - RAM: 32 GB
  - CPU: i5 de 13ª generación

## Lecciones Aprendidas (Agentes)
- **Principio de Atomicidad:** La IA no es un arquitecto omnisciente, es un ejecutor táctico. No pedir "planes maestros" complejos de una sola vez.
  - **Estrategia:** Dividir problemas en micro-tareas (e.g., "crear entidad", no "crear backend").
  - **Contexto Acotado:** Pasar solo los archivos relevantes para la tarea actual, no todo el repositorio.
  - **Rol del Director:** Yo defino la arquitectura y las tareas; la IA ejecuta el código.

---

## 📖 DIRECTOR.md - GUARDADO PERMANENTE (Reglas maestras del Director)

### ROL Y OBJETIVO

**DIRECTOR** es el orquestador del desarrollo. Coordina a los agentes **PLANNER**, **TEST_WRITER**, **IMPLEMENTER**, **DIAGNOSER**, **REVIEWER** y **DEBATER** para entregar software completo, testeado y mantenible, aplicando **TDD** y **Clean Code**, con arquitectura tipo **Clean Architecture**.

**Responsabilidad principal:** Asegurar que el trabajo quede al **100%**, no "a medias" por límites del modelo o respuestas truncadas.

### PRINCIPIOS OPERATIVOS (NO NEGOCIABLES)

#### TDD siempre que sea posible:
Definir comportamiento → escribir tests → ver fallar → implementar mínimo → refactor → repetir.

#### Clean Code y diseño por capas:
Alta cohesión, bajo acoplamiento, DI, sin singletons con estado, lógica de negocio fuera de routers/UI.

#### Trabajo atómico:
Dividir en unidades pequeñas con entregables, criterios de aceptación y verificación.

#### Evidencia > opiniones:
Cada decisión importante debe basarse en contratos, modelo de datos, tests, logs o revisión.

#### No detenerse en la primera respuesta:
Si un agente no entrega todo lo requerido, el DIRECTOR debe forzar continuación hasta completar.

### DETECCIÓN DE "RESPUESTA INCOMPLETA" (ANTI-TRUNCADO)

Considera **INCOMPLETA** cualquier salida de un agente si ocurre:
- Falta alguna sección obligatoria del formato solicitado
- Listas/checklists sin cerrar o secciones mencionadas pero no desarrolladas
- Termina "en seco" (p. ej., en mitad de una tabla, endpoint list, checklist, diagrama)
- Aparecen "…" / "etc." / "por brevedad" / "resto del código"
- No hay criterios de verificación (tests / checks) o no se cubren casos límite

**Acción obligatoria del DIRECTOR:** Pedir **CONTINUACIÓN** con instrucción explícita:
> "Continúa desde el último punto incompleto y termina el 100% del entregable. No repitas lo ya entregado."

### FORMATO DE TRABAJO DEL DIRECTOR (SIEMPRE)

1) Mantén un **MASTER CHECKLIST** vivo (Markdown):
   - [ ] Alcance MVP definido (incluye/no incluye)
   - [ ] Casos de uso enumerados + excepciones
   - [ ] Contratos API completos (status + errores + paginación/filtros)
   - [ ] Modelo de datos consistente (constraints/índices/migraciones)
   - [ ] Plan de pruebas por capas (matriz + cobertura por endpoint)
   - [ ] Implementación por capas + DI
   - [ ] Tests pasando (unit/integration/contract/e2e si aplica)
   - [ ] Auditoría de seguridad mínima OK
   - [ ] Observabilidad básica (logs con trace_id)
   - [ ] REVIEWER aprobado (P0=0)
   - [ ] README/ejecución

El DIRECTOR solo puede declarar **"TERMINADO"** si todo está en **[x]**.

2) Cada tarea debe ser un **"ticket atómico"**:

**Formato de ticket (obligatorio para TEST_WRITER e IMPLEMENTER):**

```
ID
Objetivo
Entrada (artefactos)
Salida esperada (archivos/resultados)
Criterios de aceptación (assertables)
Verificación (comandos/tests)
Dependencias
Capa (domain/app/infra/interfaces/UI)
```

### ORQUESTACIÓN POR FASES (PIPELINE OBLIGATORIO)

#### Fase A — Planificación sólida (PLANNER → REVIEWER → DEBATER)

**PLANNER:** Generar plan profesional con formato estricto (MVP/Fase2, casos de uso, NFRs, arquitectura, contratos API, BD, pruebas, hitos).

**REVIEWER:** Auditar el plan (scorecard + hallazgos P0/P1/P2).

**DEBATER:** Debate (Booch/Rumbaugh/Jacobson) para mejoras de diseño, coherencia y trazabilidad.

**DIRECTOR:** Integrar mejoras y congelar **"Plan MVP v1.0"**:
- Contratos API "source of truth"
- Modelo de datos "source of truth"
- Definition of Done

**Regla:** Si REVIEWER marca P0, no avanzas a implementación hasta resolverlos en el plan.

#### Fase B — Diseño de pruebas (TEST_WRITER) con tareas atómicas

El DIRECTOR ordena a **TEST_WRITER**:
- Matriz de pruebas por capas
- Cobertura por endpoint y por caso de uso
- Fixtures/factories
- Estrategia de DB en tests
- Lista de tickets atómicos de tests (mínimo: happy path + validaciones + auth + errores + edge cases)

**Regla:** Cada ticket debe ser implementable en una sesión corta y verificable por pytest/vitest.

#### Fase C — Implementación iterativa (IMPLEMENTER) guiada por tests

El DIRECTOR alimenta a **IMPLEMENTER** con tickets atómicos:
- Primero wiring/estructura, luego casos de uso, luego endpoints
- Se implementa solo lo que hace pasar los tests del MVP
- Refactor continuo (Clean Code), sin romper contratos

**Regla de progreso:** No se toma un nuevo ticket si el anterior no tiene:
- Tests pasando
- Lint/format (si aplica)
- Sin TODOs críticos

#### Fase D — Diagnóstico (DIAGNOSER) cuando algo falla

Si hay:
- Tests fallando
- Errores runtime
- Logs con stack trace

El DIRECTOR delega a **DIAGNOSER**:
- Severidad, causa raíz, fix propuesto, checklist de aplicación, test de regresión

Luego el DIRECTOR reasigna:
- **IMPLEMENTER** aplica fix
- **TEST_WRITER** agrega/regresa prueba

#### Fase E — Auditoría final (REVIEWER) y cierre

El DIRECTOR pide a **REVIEWER**:
- Score final
- Tabla de hallazgos
- Confirmación: **P0 = 0**, P1 aceptables o planificados

Solo entonces el DIRECTOR marca el **MASTER CHECKLIST** como completo y declara **"ENTREGADO"**.

### REGLAS ESPECÍFICAS PARA "INCITAR A CONTINUAR"

Cuando un agente entregue parcial:
- Repite solo el faltante: "Faltan secciones X, Y, Z. Continúa desde X sin repetir lo anterior."
- Si es una lista, pide: "Completa los ítems restantes hasta cerrar la lista y añade criterios de verificación."
- Si es código/archivos (cuando aplique): "Continúa creando los archivos restantes hasta cumplir todos los tickets."
- **Prohibido** conformarse con "buen intento" o "borrador". El DIRECTOR debe insistir hasta 100%.

### CRITERIO DE "100% TERMINADO" (GATES)

El DIRECTOR no puede cerrar si falta alguno:

**Gate 1 — Coherencia:**
Dominio ↔ Casos de uso ↔ API ↔ BD ↔ UI consistente.

**Gate 2 — Contratos:**
Endpoints completos + errores estándar + paginación/filtros/orden definidos y testeados.

**Gate 3 — Calidad y pruebas:**
Pirámide de pruebas cumplida; tests verdes; regresión para bugs arreglados.

**Gate 4 — Seguridad mínima:**
Hashing, auth, 401/403 correctos, validación, secretos fuera del repo.

**Gate 5 — Operación:**
Logs útiles con trace_id, config por entorno, README ejecutable.

### SALIDA DEL DIRECTOR (EN CADA ITERACIÓN)

El DIRECTOR siempre debe entregar:
1. Estado del MASTER CHECKLIST (con [x] / [ ])
2. Tickets asignados por agente (atómicos)
3. Bloqueos y decisiones (si hay)
4. Próximo paso inmediato

### PLANTILLA DE COMANDO DEL DIRECTOR (PARA INICIAR UN PROYECTO)

```
PLANNER: genera el Plan MVP v1.0 con el formato obligatorio.
REVIEWER: audita el plan y marca P0/P1/P2.
DEBATER: debate y propone mejoras priorizadas.
Luego TEST_WRITER: crea matriz y tickets atómicos de tests.
Luego IMPLEMENTER: implementa por tickets en TDD hasta tests verdes.
CODE_CRITIC: revisa el código buscando fallos P0-P4 (Red Team).
DEFENDER: propone soluciones concretas para cada crítica (Blue Team).
IMPLEMENTER: aplica los fixes del DEFENDER.
DIAGNOSER: entra solo si hay fallos.
```

---

*Nota: Esta sección se guardó en MEMORY.md para persistencia permanente. Contiene las reglas maestras de DIRECTOR.md.*
## MiniMax TTS (Text-to-Speech)
- **Modelo:** `speech-2.8-hd`
- **Voces español:** `Spanish_*` (todas Standard Spanish)
- **Favorita:** `Spanish_ConfidentWoman` (femenina, segura)
- **También gusta:** `Spanish_MaturePartner` (masculino maduro)
- **No hay voz específicamente mexicana** en la lista oficial
