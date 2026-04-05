# Evaluación real del diagnoser sobre fallo del implementer

## Caso

- Problema: implementer devuelve texto o diff, pero no modifica el workspace real.
- Evidencia: `projects/phaser-dkjr-eval` siguió intacto y el build correspondía al starter de Vite.

## Resultado del primer pase

Estado: no cumple.

### Fallos observados

- Ignoró la evidencia principal: ausencia total de cambios reales.
- Inventó señales no dadas, incluyendo pytest y configuración Phaser.
- No distinguió entre fallo del proyecto objetivo y fallo del sistema de agentes/runtime.

## Ajuste aplicado

Se reforzó `diagnoser.yaml` con una rama específica para fallos del sistema de agentes:

- priorizar uso o no uso de `<TOOL_CALL>`,
- prohibir diagnósticos del proyecto cuando el agente ni siquiera editó,
- centrar la causa raíz en protocolo, prompt y validación del agente.

## Próximo paso

Reusar el diagnoser ajustado solo si el implementer vuelve a fallar tras la nueva instrucción explícita del protocolo de tools.

## Segunda iteración

Estado: sigue sin cumplir.

### Nuevo intento evaluado

Se le pidió diagnosticar un fallo real y concreto del repo:

- `src/game/State/GameState.ts` creado parcialmente,
- starter original aún presente,
- build roto con `TS1294` por `enum` en `GameState.ts`.

### Resultado

- No produjo diagnóstico útil.
- Rebotó el contexto del sistema/política/tools en vez de analizar la evidencia.

## Conclusión

El diagnoser sigue siendo el agente más débil del conjunto para este flujo. Aún no está listo para diagnosticar de forma fiable ni fallos del runtime de agentes ni fallos concretos del repo Phaser.

## Tercera iteración

Estado: mejora material; baseline promovible.

### Nuevo benchmark evaluado

- Mismo caso concreto de TypeScript usado para comparar contra el baseline:
	- `TS1484`: `LevelOutcome` importado como valor aunque solo es tipo con `verbatimModuleSyntax` activo.
	- `TS6133`: ese mismo import no se usa como valor.
- Baseline previo: `llama3.2:3b`.
- Modelo comparado: `qwen3.5:9b` con prompt compacto orientado a frontend-only y evidencia estricta.

### Resultado

- Identificó el fix correcto: separar o marcar `LevelOutcome` como `import type`.
- Se mantuvo dentro del error real y dejó de inventar backend, DB o runtime ajeno.
- Todavía añadió relleno de baja calidad en la sección de “prueba de regresión”, pero ya no rompió el diagnóstico principal.

### Comparativa práctica

- `llama3.2:3b`:
	- inventó versión de TypeScript y cambios de tooling/config poco justificados;
	- no se mantuvo en el fix mínimo local.
- `qwen3.5:9b`:
	- aisló mejor el síntoma y la causa raíz;
	- recomendó el cambio mínimo correcto sobre el import;
	- mantuvo mejor disciplina respecto a la evidencia.

## Decisión

- Promover `qwen3.5:9b` como nuevo baseline del diagnoser.
- Mantener prompt corto y específico; el prompt genérico largo estaba empujando al agente a alucinar contexto no provisto.

## Cuarta iteración

Estado: parcialmente útil para runtime del sistema de agentes.

### Nuevo benchmark evaluado

- Caso: fallo del `implementer` a nivel runtime, no del repo objetivo.
- Evidencia entregada al diagnoser:
	- run `20260402-132646-019c0fa2` de `implementer` con `nemotron-cascade-2:latest` quedó en `running` con `completed_at = null`;
	- durante la corrida emitió una secuencia larga de `y` repetidas hasta aborto manual con `Ctrl+C`;
	- sin evidencia de tool calls válidas ni artefactos completos;
	- contraste adicional: run previo con `devstral-small-2:latest` terminó en `error` por `Required path verification failed`, aunque su output textual decía falsamente que había creado ambos archivos y que test/build pasaron.

### Resultado

- Mejora clara respecto a iteraciones anteriores:
	- sí distinguió que el problema estaba en el sistema de agentes/runtime y no en Phaser;
	- identificó razonablemente un patrón de generación degenerada/filler output y falta de cierres/guardrails del runner.
- Límite actual:
	- siguió inventando detalles concretos de implementación del runner (config flags, APIs y tests ejemplo) que no estaban respaldados por evidencia directa del código real.

### Veredicto práctico

- Para fallos de runtime del sistema, el diagnoser ya sirve como orientador inicial.
- Aún no sirve como especificación confiable de implementación: sus fixes y tests propuestos deben contrastarse con el código real del runner antes de aplicarlos.

## Quinta iteración

Estado: comparación cerrada; `qwen3.5:9b` sigue ganando también en runtime.

### Benchmark comparativo

- Se repitió exactamente el mismo caso de runtime del `implementer` usando un override temporal del `diagnoser` con `llama3.2:3b`.
- Prompt: el mismo prompt compacto evidence-first usado por el baseline actual.

### Resultado de `llama3.2:3b`

- Produjo un diagnóstico demasiado genérico.
- Reconoció el síntoma, pero no aisló de forma convincente la causa proximal ni la causa raíz.
- Volvió a proponer respuestas vagas del tipo “revisar implementación/configuración/runtime” sin aterrizar guardrails concretos del sistema.
- Quedó claramente por debajo del benchmark previo con `qwen3.5:9b`.

### Comparativa práctica

- `qwen3.5:9b`:
	- sí separa mejor fallo del sistema de agentes vs fallo del proyecto;
	- da hipótesis y guardrails iniciales útiles, aunque todavía inventa parte de la implementación.
- `llama3.2:3b`:
	- cae en generalidades y pierde poder de discriminación en runtime;
	- no aporta suficiente precisión para triage técnico serio.

## Decisión final por ahora

- Mantener `qwen3.5:9b` como baseline del `diagnoser`.
- No merece la pena volver a `llama3.2:3b` para casos de runtime del sistema.