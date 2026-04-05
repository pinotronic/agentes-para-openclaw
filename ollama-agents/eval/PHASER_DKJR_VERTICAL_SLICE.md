# Evaluación de Agentes: Phaser Donkey Kong Jr. Slice

## Objetivo

Evaluar si los agentes de ollama-agents cumplen su función real al construir un vertical slice estilo Donkey Kong Jr. con Phaser, sin scope creep y con validación verificable.

## Regla principal

No pedir "clona Donkey Kong Jr. completo".
El caso de prueba debe ser un slice ejecutable, acotado y medible.

## Slice objetivo

Juego 2D en Phaser 3 con Vite + TypeScript que incluya:

- Un solo nivel.
- Movimiento izquierda/derecha.
- Escalada por lianas o escaleras.
- Salto corto.
- Al menos un enemigo móvil que cause derrota por colisión.
- Al menos tres coleccionables.
- Condición de victoria al reunir los coleccionables y llegar a la meta.
- Pantalla de inicio simple y reinicio tras game over.
- Arte placeholder, sin assets externos obligatorios.

## No incluye en MVP

- Múltiples niveles.
- Física compleja estilo arcade perfecta.
- Sprites fidelidad arcade.
- Audio final.
- Backend.
- Persistencia remota.

## Stack esperado

- Frontend only.
- Phaser 3.
- Vite.
- TypeScript.
- Vitest para lógica desacoplada.

## Criterios de aceptación del producto

- El proyecto levanta localmente.
- El jugador puede completar el nivel.
- La derrota por colisión es reproducible.
- La victoria es reproducible.
- La lógica crítica está desacoplada lo suficiente para tener tests.
- No aparecen artefactos de backend inventados sin justificación.

## Qué debe hacer cada agente

### planner

Debe entregar:

- Alcance MVP claro para juego frontend only.
- Arquitectura adecuada para Phaser.
- Hitos pequeños y verificables.
- Estrategia de pruebas realista para un juego cliente.

Falla si:

- deriva a backend/API/DB sin necesidad,
- propone scope excesivo,
- no define vertical slices verificables.

### test_writer

Debe entregar:

- Casos de prueba para lógica de movimiento, colisión, victoria/derrota y bootstrap del juego.
- Propuesta concreta de archivos de tests.
- Prioridad a Vitest y módulos desacoplados.

Falla si:

- intenta testear internals de Phaser imposibles de estabilizar,
- no prioriza lógica extraíble,
- inventa tests e2e pesados sin necesidad.

### implementer

Debe entregar:

- Cambios mínimos y aplicables.
- Código jugable en el slice definido.
- Respeto por el plan y los tests.

Falla si:

- mete features fuera de alcance,
- rompe tests o cambia tests sin razón,
- mezcla demasiada lógica en una sola escena sin separación mínima.

### diagnoser

Debe entregar:

- Causa raíz concreta cuando fallen build/tests/runtime.
- Fix mínimo verificable.

Falla si:

- solo repite el error,
- no propone verificación,
- sugiere refactors enormes para bugs pequeños.

### reviewer

Debe entregar:

- Riesgos reales de arquitectura, jugabilidad, testabilidad y mantenibilidad.
- Prioridades claras.

Falla si:

- da opiniones vagas,
- no usa evidencia,
- ignora ausencia de tests o exceso de scope.

### debater

Debe entregar:

- Alternativas razonables para estructurar escenas, entidades o estado del juego.
- Recomendación con trade-offs.

Falla si:

- no compara opciones,
- solo reafirma una idea sin contraste.

## Prompt base recomendado

"Construye un vertical slice estilo Donkey Kong Jr. en Phaser 3 usando Vite + TypeScript. Debe ser frontend only. Un solo nivel, movimiento lateral, escalada, salto corto, un enemigo móvil, tres coleccionables, victoria y derrota reproducibles, pantalla de inicio y reinicio. Usa placeholders simples y deja la lógica clave desacoplada para poder probarla con Vitest. No agregues backend, base de datos ni servicios externos." 

## Orden de evaluación recomendado

1. planner
2. reviewer sobre el plan
3. test_writer
4. implementer
5. diagnoser si algo falla
6. reviewer final
7. debater si hay decisión estructural dudosa