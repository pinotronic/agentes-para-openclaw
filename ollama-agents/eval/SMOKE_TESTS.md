# Smoke tests (manual)

Estos checks validan que cada agente respeta su rol y formato.

## planner
Input: "Agregar endpoint /health"
Esperado:
- Plan con DoD
- Estrategia TDD
- No código

## test_writer
Input: "Especificación de endpoint /health (200 + body)"
Esperado:
- Tests primero
- Archivos/rutas claras
- Comandos de ejecución

## implementer
Input: "Aquí están los tests y fallan por X"
Esperado:
- Cambios mínimos
- No cambia tests sin permiso

## diagnoser
Input: pegar salida de test/lint
Esperado:
- Resume error
- Causa probable
- Fix mínimo + comando de verificación

## reviewer
Input: diff
Esperado:
- Severidad BLOCKER/IMPORTANT/NICE
- Foco en seguridad/testabilidad

## debater
Input: decisión de arquitectura (A/B)
Esperado:
- >=2 opciones
- tradeoffs
- recomendación + validación
