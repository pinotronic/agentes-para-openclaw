# Evaluación real del implementer sobre Phaser DKJR slice

## Caso

- Repo objetivo: `projects/phaser-dkjr-eval`
- Ticket: reemplazar starter Vite por base Phaser con escenas mínimas.

## Resultado del primer pase

Estado: no cumple.

### Evidencia

- El output fue un diff textual.
- El workspace no cambió.
- `npm run build` siguió construyendo el starter original de Vite, no una base Phaser.

## Diagnóstico

El prompt del implementer seguía permitiendo una interpretación tipo "entrego parche propuesto" en vez de "edito el repo real".

## Ajuste aplicado

Se reforzó `implementer.yaml` para obligar uso de tools cuando exista un workspace real y prohibir responder solo con diff textual salvo petición explícita.

## Próximo paso

Reejecutar el implementer sobre el mismo ticket y verificar que ahora sí modifique archivos reales y deje un build coherente.

## Segunda iteración

Estado: mejora parcial, todavía no cumple.

### Evidencia nueva

- Tras reforzar el protocolo de tools y aumentar `tool_max_rounds`, el implementer dejó de limitarse a devolver solo diff.
- Apareció el archivo `projects/phaser-dkjr-eval/src/game/State/GameState.ts`.
- El starter original siguió casi intacto: `src/main.ts` y `package.json` no fueron reemplazados por la base Phaser.
- El build pasó de "verde pero sin cambios" a "roto por cambio parcial":
	- `src/game/State/GameState.ts:1:13 - error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.`

## Lectura operativa

Esto indica que el implementer ya entró al loop de tools, pero todavía no es fiable para cerrar tickets multiarchivo sin supervisión fuerte.

## Estado actual

- Antes: no editaba nada.
- Ahora: edita parcialmente, pero deja el repo inconsistente.

## Conclusión

El ajuste al runtime sí mejoró el comportamiento del agente, pero el implementer aún requiere:

- tickets más pequeños,
- validación inmediata tras cada pase,
- y probablemente otro ajuste de prompt o cambio de modelo si se quiere autonomía real.

## Tercera iteración: micro-ticket con verificación externa

Estado: cumple en tarea mínima, con observaciones.

### Ticket

- Crear `src/game/logic/clampLadderProgress.ts` con una función pura que limite un progreso al rango `0..1`.
- Crear `src/game/logic/clampLadderProgress.test.ts` con tres casos de Vitest.
- Verificación objetiva: `npm run test` y `npm run build`.

### Incidencias encontradas durante la evaluación

- La primera corrida falló por precondición del repo, no por la lógica del ticket:
	- `vitest` no estaba instalado en `node_modules`.
- Al intentar reinstalar dependencias apareció otro problema del banco de pruebas:
	- `package.json` incluía `@types/phaser`, paquete inexistente en npm.
	- Se corrigió el repo eliminando esa dependencia inválida; Phaser ya incluye tipos.
- En esa primera pasada el implementer creó el archivo de utilidad, pero siguió mezclando edición real con salida textual tipo diff para el archivo de test.

### Resultado tras corregir el banco de pruebas

- Reejecutado sobre el faltante exacto (`clampLadderProgress.test.ts`), el implementer sí dejó el archivo en el workspace.
- Verificación externa manual posterior:
	- `npm run test` ✅
	- `npm run build` ✅

### Hallazgo adicional del runner

- El manifest nuevo quedó como `completed`, pero `latest/implementer.json` seguía apuntando al run fallido anterior.
- Se corrigió `agents/manifest.py` para que `get_agent_status(...)` recupere el manifest más reciente y sanee automáticamente el puntero `latest` si quedó desfasado.

### Lectura operativa actualizada

- El implementer ya puede cerrar un ticket realmente atómico cuando:
	- el entorno está sano,
	- el objetivo está extremadamente acotado,
	- y la validación externa es inmediata.
- Sigue sin ser fiable todavía para tickets multiarchivo o vertical slices completos.

## Cuarta iteración: evitar falsos `completed` por tickets no realizados

Estado: mejora del runner validada; implementer todavía no cumple.

### Problema detectado

- El runner ya validaba `npm run test` y `npm run build`, pero eso no garantizaba que el ticket solicitado hubiera sido realmente ejecutado.
- Caso real observado:
	- el implementer no creó `evaluateLevelOutcome.ts` ni `evaluateLevelOutcome.test.ts`,
	- pero como el repo seguía verde con los archivos anteriores, el run podía quedar como `completed`.

### Ajuste aplicado al framework

- Se agregó `--require-path` al runner en `runner/ollama_agent.py`.
- Ahora un run puede exigir archivos o directorios concretos además de test/build.
- Si falta cualquiera de esas rutas, el manifest queda en `error`.
- Se añadieron pruebas del runner para este hardening.

### Resultado de re-evaluación

- Reejecutado el mismo ticket con:
	- `--require-path src/game/logic/evaluateLevelOutcome.ts`
	- `--require-path src/game/logic/evaluateLevelOutcome.test.ts`
	- `--verify-command "npm run test"`
	- `--verify-command "npm run build"`
- Resultado:
	- el run falla correctamente con `Required path verification failed...`
	- ya no hay falso positivo.

## Quinta iteración: corrección del perfil del implementer

Estado: mejor diagnóstico de causa, pero sin mejora efectiva todavía.

### Evidencia nueva del output del agente

- El agente explicó dos errores concretos en su propio flujo:
	- seguía creyendo que debía responder como generador de diffs/Python backend,
	- intentó usar `write_file` con argumentos incorrectos (`file_path` en vez de `path`) y además razonó como si solo pudiera hacer una tool call total.

### Ajustes aplicados al perfil

- Se reforzó `implementer.yaml` para:
	- invalidar explícitamente instrucciones residuales de tipo Python/FastAPI/diff-only cuando el ticket sea frontend/TypeScript,
	- prohibir pseudo-tools textuales,
	- aclarar que puede hacer múltiples tool calls en una misma corrida,
	- documentar el esquema exacto de argumentos para `read_file`, `write_file`, `edit_file` y `bash`.

### Resultado tras el ajuste

- Reejecutado el mismo ticket con `--require-path`, el implementer siguió fallando y no creó los archivos esperados.

### Lectura operativa más reciente

- El problema ya no es de observabilidad:
	- el runner ahora detecta correctamente la ausencia de artefactos.
- El problema del implementer quedó más acotado:
	- ya no parece pura desobediencia general,
	- ahora apunta a una incapacidad persistente para emitir tool calls válidas bajo este entorno.
- Próximo frente recomendado:
	- revisar o reemplazar el modelo del implementer antes de seguir subiendo complejidad de tickets.

## Benchmark directo entre modelos del implementer

Se hizo una comparación justa sobre el mismo ticket, mismo prompt mejorado y mismas verificaciones (`--require-path`, `npm run test`, `npm run build`).

### Configuración del benchmark

- Se creó un override temporal local del perfil `implementer` dentro del repo de evaluación para que ambos modelos usaran el mismo prompt mejorado.
- Ticket medido: creación de `evaluateLevelOutcome.ts` y `evaluateLevelOutcome.test.ts`.

### Resultado: qwen3.5:9b

- Tiempo total observado: `32.15s`
- Resultado real: **éxito**
- Evidencia:
	- creó ambos archivos,
	- los tests quedaron verdes,
	- el build quedó verde.

### Resultado: qwen3-coder:30b

- Tiempo total observado: `22.41s`
- Resultado real: **fallo**
- Error del runner: `Agent exceeded maximum tool rounds (12)`
- Evidencia:
	- no dejó los archivos requeridos,
	- el manifest quedó en `error`.

### Conclusión del benchmark

- Para este entorno y este tipo de ticket, **qwen3.5:9b fue claramente mejor**.
- El 30b fue más rápido en tiempo bruto, pero operativamente peor porque no completó la tarea.
- El criterio útil aquí no es solo latencia; es `tiempo hasta tarea verificada`. Bajo ese criterio, el 9b gana.

## Promoción del perfil activo y validación posterior

Estado: mejora aplicada y validada.

### Cambio aplicado

- Se promovió el prompt mejorado al perfil activo real del implementer en `agents/implementer.yaml`.
- Se mantuvo `qwen3.5:9b` como modelo activo.
- Además se añadieron reglas específicas para:
	- `import type` en TypeScript/Vite,
	- evitar imports no usados,
	- respetar exactamente el número de tests pedidos.

### Resultado

- Tras estos cambios, el implementer volvió a ejecutar el ticket `evaluateLevelOutcome`.
- El repo terminó con:
	- `src/game/logic/evaluateLevelOutcome.ts`
	- `src/game/logic/evaluateLevelOutcome.test.ts`
	- `npm run test` ✅
	- `npm run build` ✅
- El estado más reciente del agente quedó en `completed` con modelo `qwen3.5:9b`.

### Lectura operativa actual

- El implementer activo ya no está en el prompt viejo de diffs.
- El sistema quedó en una posición mejor que al inicio de la sesión:
	- runner más estricto,
	- perfil activo alineado con el mejor modelo observado,
	- y validación real satisfactoria sobre un ticket pequeño de lógica + tests.