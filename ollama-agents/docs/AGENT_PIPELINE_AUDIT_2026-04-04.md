# Auditoria y Estrategia de Agentes

Fecha: 2026-04-04

## 2. Auditoria del pipeline actual

Hallazgos principales:

1. Desalineacion entre perfil y pipeline.
   - El pipeline en [pipeline/run.py](../pipeline/run.py) pide a `test_writer` e `implementer` que devuelvan un unified diff.
   - El perfil activo de [agents/implementer.yaml](../agents/implementer.yaml) estaba orientado a editar el workspace real con tools.
   - Resultado: el agente recibe dos contratos distintos y puede producir salidas inconsistentes.

2. Permisos efectivos demasiado abiertos en ejecucion real.
   - El runner soporta modo `strict`, pero el pipeline no lo forzaba.
   - En `permissive`, cualquier agente cae en una policy amplia y la allowlist deja de ser una barrera real.

3. Guardrails tarde y con cobertura parcial.
   - `validate_project_changes()` existe, pero hoy detecta muy pocos patrones generales.
   - No previene por si solo scope creep, codigo muerto, archivos paralelos ni artefactos temporales.

4. Implementer con demasiada libertad operativa.
   - Permitiria `write_file`, `edit_file` y `bash` aunque el pipeline no consume cambios directos del workspace, sino diffs por stdout.
   - Eso aumenta el espacio de error sin aportar valor al flujo actual.

5. Reviewer demasiado genericamente correcto.
   - Revisa calidad, pero no enfatiza suficiente la deteccion de drift, archivos huerfanos, estructura paralela y alcance inventado.

6. Bash sin restricciones semanticas.
   - Tener `bash` habilitado sin filtrar intencion favorece exploracion ruidosa y comandos no alineados con verificacion.

## 1. Estrategia operativa recomendada

Principio central:

- Los agentes no deben comportarse como desarrolladores autonomos de repo completo.
- Deben operar como ejecutores tacticos con contrato estricto, alcance pequeno y verificacion externa.

Estrategia:

1. `planner` y `debater` solo analizan y proponen.
2. `test_writer` y `implementer` trabajan en modo diff-first cuando el pipeline aplica parches.
3. `implementer` no crea estructura nueva salvo necesidad evidente y verificable.
4. `reviewer` bloquea scope creep, codigo muerto, archivos no referenciados y drift entre plan, tests y codigo.
5. El pipeline corre en `strict` por defecto para que la allowlist realmente importe.
6. `bash` se reserva para verificacion; la inspeccion debe hacerse con read/glob/grep.
7. La unidad de trabajo debe ser un ticket atomico con archivos candidatos y criterio de salida verificable.

## 3. Cambios tecnicos aplicados

1. El pipeline ahora fuerza `strict` por defecto y puede overridearse por CLI/env si hace falta.
2. `implementer` fue realineado al contrato diff-first del pipeline.
3. `implementer` ya no necesita herramientas de escritura directa en este flujo.
4. `implementer` restringe `bash` a comandos de verificacion comunes.
5. `reviewer` ahora audita explicitamente scope creep, codigo muerto, estructuras paralelas y archivos sin referencia.
6. El task del implementer ahora incluye paths candidatos ya tocados para reducir dispersion.

## Siguiente capa recomendada

- Agregar guardrails genericos por adapter para paths permitidos/denegados.
- Separar perfiles `implementer_diff` y `implementer_workspace` si en el futuro quieres soportar ambos modos.
- Hacer que el reviewer falle de manera estructurada si detecta archivos nuevos no referenciados.