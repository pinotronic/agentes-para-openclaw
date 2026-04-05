# Evaluación real del planner sobre Phaser DKJR slice

## Caso

- Prompt: vertical slice estilo Donkey Kong Jr. en Phaser 3, Vite + TypeScript, frontend only.
- Objetivo: comprobar si el planner respeta su rol y evita sesgos de backend.

## Resultado del primer pase

Estado: cumplimiento parcial.

### Lo que sí hizo bien

- Detectó entidades del dominio del juego como player, enemy y collectables.
- Intentó separar dominio, aplicación e infraestructura.
- Propuso contratos internos y lógica desacoplada.

### Lo que hizo mal

- Arrastró sesgo de backend y propuso pseudo-endpoints `/api/game/...`.
- Metió códigos HTTP y catálogo de errores HTTP innecesarios.
- No aterrizó suficientemente el slice jugable en términos de escenas y hitos concretos.
- La salida incluyó texto de razonamiento tipo `Thinking...`, que no aporta al entregable final.

## Scorecard

- MVP acotado: 1/2
- No inventa backend: 0/2
- Hitos verificables: 1/2
- Pruebas realistas para Phaser: 1/2
- Riesgos y mitigaciones útiles: 1/2

Total: 4/10

## Ajuste aplicado

Se reforzó `planner.yaml` con una regla específica para frontend-only y videojuegos:

- prohibir backend/API/DB inventados,
- reinterpretar contratos como interfaces internas,
- priorizar escenas, input, colisiones, estado y testabilidad con Vitest.

## Próximo paso

Reejecutar el planner con el mismo caso y comparar si desaparece el sesgo de backend.