# Mission Control (seguimiento de runs)

El pipeline ahora genera artefactos de seguimiento por cada ejecución, para poder ver *qué pasó*, *cuándo* y *en qué fase*.

## Dónde se guarda
En el repo objetivo (el que pasas con `--project`):

- `<project>/.mission_control/latest` → contiene el `run_id` del último run
- `<project>/.mission_control/<run_id>/summary.json` → resumen del run
- `<project>/.mission_control/<run_id>/events.jsonl` → eventos (JSONL, append-only)

> Nota: No guardamos el output completo de los agentes aquí (para evitar basura/secretos en disco). El objetivo es tracking/telemetría mínima.

## Cómo verlo
### Listar runs
```bash
python /home/administrador/.openclaw/workspace/ollama-agents/pipeline/mc.py --project /path/al/repo list
```

### Ver el resumen del último run
```bash
python /home/administrador/.openclaw/workspace/ollama-agents/pipeline/mc.py --project /path/al/repo show --run latest
```

### Seguir eventos en vivo (tail)
```bash
python /home/administrador/.openclaw/workspace/ollama-agents/pipeline/mc.py --project /path/al/repo tail --run latest
```

## Desactivar Mission Control
Si quieres correr el pipeline sin generar tracking:

```bash
PIPELINE_MISSION_CONTROL=0 python ollama-agents/pipeline/run.py --project ... --task ...
```
