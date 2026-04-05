# Evaluación real del test_writer sobre Phaser DKJR slice

## Caso

- Entrada: plan del planner para un vertical slice Phaser frontend-only.
- Objetivo: comprobar si TEST_WRITER propone pruebas útiles y realistas para un juego cliente.

## Resultado del primer pase

Estado: cumplimiento parcial.

### Lo que sí hizo bien

- Priorizó colisiones, movimiento, victoria/derrota y estado.
- Propuso Vitest como herramienta base.
- Identificó la necesidad de desacoplar lógica del motor.

### Lo que hizo mal

- Mantuvo lenguaje de "endpoint" y "DB" aunque no aplica.
- Sugirió Puppeteer opcional sin necesidad real para este slice.
- Mezcló a ratos pruebas útiles con secciones heredadas del contexto full-stack.

## Scorecard

- Prioriza lógica testeable: 2/2
- Casos de victoria/derrota incluidos: 2/2
- Estructura de tests concreta: 1/2
- Evita tests frágiles del motor: 1/2
- Verificación clara: 1/2

Total: 7/10

## Ajuste aplicado

Se reforzó `test_writer.yaml` con una regla especial para frontend-only y videojuegos:

- prohibir backend/DB/endpoints inventados,
- evitar navegadores pesados por defecto,
- reinterpretar cobertura por endpoint como contratos internos del juego,
- priorizar Vitest + mocks ligeros + lógica desacoplada.

## Próximo paso

Reejecutar el test_writer con el mismo caso para verificar que el plan de pruebas quede más limpio y específico para Phaser.

## Segunda iteración

Estado: mejora insuficiente.

### Evidencia

- Siguió mostrando `Thinking...` al inicio.
- Continuó inventando semánticas y contratos que no están en el código real.
	- Ejemplo: trató `clampLadderProgress` como si trabajara con escalas 0..100, cuando el módulo real clampa en 0..1.
	- Inventó salidas y estados para `evaluateLevelOutcome` que no existen en la implementación observada.
- Aunque redujo algo de backend explícito, todavía mezcló secciones no aplicables y hasta volvió a usar bloques prohibidos en la sección de fixtures.

## Ajuste aplicado

- Se reforzó `agents/test_writer.yaml` para:
	- prohibir `Thinking...` y razonamiento visible,
	- obligar a usar nombres y firmas exactas del código real,
	- prohibir React, Playwright, DOM, stores, DB y backend cuando el repo solo muestra lógica pura en `src/game/logic`,
	- separar claramente contratos pendientes de módulos aún no implementados.

## Benchmark de modelos

### qwen3.5:9b

- Produjo salida utilizable pero todavía defectuosa.
- Problemas principales:
	- pensamiento visible,
	- contratos inventados,
	- semántica incorrecta sobre funciones reales.

### qwen3.5:27b

- Resultado peor en este entorno.
- Falló con `Agent exceeded maximum tool rounds (4)` y ni siquiera dejó una salida final útil.

## Conclusión actualizada

- Para `test_writer`, igual que con `implementer`, el mejor modelo observado por ahora sigue siendo `qwen3.5:9b`.
- Aun así, el `test_writer` sigue por debajo del umbral de calidad deseado y requiere más trabajo de prompt o un rediseño más fuerte del rol.