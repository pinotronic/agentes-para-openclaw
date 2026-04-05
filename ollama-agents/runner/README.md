# Runner

`ollama_agent.py` es un runner mínimo para invocar un agente (perfil YAML) usando Ollama local.
Ahora también puede ejecutar un subconjunto de tools en runtime con enforcement real de permisos.

Modo de permisos:

- Por defecto corre en modo `permissive` para trabajo local autónomo.
- Puedes forzarlo por CLI con `--permission-mode strict`.
- También puedes persistirlo en config de proyecto o de usuario con `--save-permission-mode`.
- La precedencia es: CLI > variable de entorno > config de proyecto > config de usuario > default `permissive`.

## Requisitos

- Ollama instalado y corriendo
- Python 3

Instala deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python3 ollama_agent.py --agent planner --input "Implementar feature X" --context "(contexto opcional)"
```

Si quieres habilitar ejecución de tools sobre un repo real, pasa `--workspace`:

```bash
python3 ollama_agent.py --agent reviewer --workspace /ruta/al/repo --input "Revisa el cambio" --context "..."
```

Para forzar el modo estricto:

```bash
python3 ollama_agent.py --agent reviewer --workspace /ruta/al/repo --permission-mode strict --input "Revisa el cambio"
```

Para inspeccionar o persistir el modo efectivo:

```bash
python3 ollama_agent.py --agent reviewer --workspace /ruta/al/repo --show-permission-mode --input x
python3 ollama_agent.py --agent reviewer --workspace /ruta/al/repo --save-permission-mode strict --permission-scope project --input x
python3 ollama_agent.py --agent reviewer --save-permission-mode permissive --permission-scope user --input x
```

Scopes soportados:

- `project`: guarda en `.openclaw/ollama-agents.json` dentro del workspace.
- `user`: guarda en `~/.openclaw/ollama-agents.json`.

Sesiones persistentes:

- Usa `--session-file /ruta/session.json` para guardar transcript y salida final.
- Usa `--resume-session` para reanudar desde la sesión previa.
- Usa `--compact-session` para compactar transcript viejo antes de continuar.

Ejemplo:

```bash
python3 ollama_agent.py --agent planner --workspace /ruta/al/repo --session-file /tmp/planner-session.json --resume-session --compact-session --input "continua el analisis"
```

Persistencia de output por agente:

- Cada ejecución del runner guarda un manifest JSON y el output final en `.agent_store/` del workspace.
- También se mantiene una copia del último estado en `.agent_store/latest/<agent>.json`.
- El manifest registra `status`, `output_file`, timestamps y error si la ejecución falla.

Inspección de manifests:

```bash
python3 ollama_agent.py --agent reviewer --workspace /ruta/al/repo --show-agent-status
python3 ollama_agent.py --agent reviewer --workspace /ruta/al/repo --show-agent-output
python3 agent_store.py --workspace /ruta/al/repo --agent reviewer --limit 10
python3 agent_store.py --workspace /ruta/al/repo --run-id 20260402-101500-abcd1234 --show-output
python3 agent_store.py --workspace /ruta/al/repo --agent reviewer --prune-keep 20
```

- `--show-agent-status` imprime el último manifest persistido para ese agente.
- `--show-agent-output` además imprime el output guardado en el archivo persistido.
- `agent_store.py` lista historiales de `.agent_store/` y permite inspeccionar una ejecución concreta por `run_id`.
- `--prune-keep N` elimina manifests y outputs antiguos dentro de `.agent_store`, conservando solo los N más recientes del filtro actual.

Discovery jerárquico:

- Agents: `.openclaw/agents` y `.ollama-agents/agents` del proyecto tienen prioridad sobre definiciones del usuario y luego sobre el core.
- Skills: `.openclaw/skills`, `.ollama-agents/skills` y `commands/` legacy se resuelven con la misma precedencia.
- Usuario: también se revisan `~/.openclaw`, `~/.agents` y `~/.ollama-agents`.
- Variable opcional: `OLLAMA_AGENTS_HOME` añade una raíz extra de usuario.

Inspección:

```bash
python3 ollama_agent.py --agent planner --input x --workspace /ruta/al/repo --list-agents
python3 ollama_agent.py --agent planner --input x --workspace /ruta/al/repo --list-skills
```

Override local de policies:

- Un agente local puede incluir `permissions:` dentro de su YAML.
- Si `inherit: true`, parte de la policy base del core y la ajusta.
- Si `inherit: false`, define una policy nueva desde cero.

Campos soportados:

- `default_mode`
- `allowed_tools`
- `add_allowed_tools`
- `remove_allowed_tools`
- `tool_requirements`

Ejemplo:

```yaml
id: reviewer
model: qwen3.5:9b
system: |
	Reviewer local
permissions:
	inherit: true
	add_allowed_tools:
		- bash
	tool_requirements:
		bash: danger_full_access
```

Hooks de tools:

- Un agente local puede declarar `hooks.pre_tool_use` y `hooks.post_tool_use` en su YAML.
- También puedes definir hooks separados por agente en `.openclaw/hooks/<agente>.yaml` o `.ollama-agents/hooks/<agente>.yaml`.
- Cada hook es un comando shell ejecutado dentro del workspace.
- `pre_tool_use` puede bloquear la ejecución si termina con código distinto de cero.
- `post_tool_use` no revierte la ejecución, pero anota el resultado con mensajes o error de hook.
- En archivos separados se soporta además: `inherit`, `add_pre_tool_use` y `add_post_tool_use`.

Variables de entorno disponibles en hooks:

- `OLLAMA_AGENT_ID`
- `OLLAMA_TOOL_NAME`
- `OLLAMA_TOOL_ARGS_JSON`
- `OLLAMA_TOOL_RESULT_JSON` solo en `post_tool_use`

Ejemplo:

```yaml
id: reviewer
model: qwen3.5:9b
system: |
	Reviewer local
hooks:
	pre_tool_use:
		- 'if [ "$OLLAMA_TOOL_NAME" = "bash" ]; then echo "bash bloqueado" >&2; exit 1; fi'
	post_tool_use:
		- 'echo "hook ejecutado para $OLLAMA_TOOL_NAME"'
```

Ejemplo en archivo separado `.openclaw/hooks/reviewer.yaml`:

```yaml
inherit: false
pre_tool_use:
	- 'if [ "$OLLAMA_TOOL_NAME" = "bash" ]; then echo "bash bloqueado por config de proyecto" >&2; exit 1; fi'
add_post_tool_use:
	- 'echo "post hook desde archivo para $OLLAMA_TOOL_NAME"'
```

## Protocolo de tools

El runner acepta una invocación estructurada del modelo con este formato exacto:

```text
<TOOL_CALL>
{"tool":"canonical_name","arguments":{}}
</TOOL_CALL>
```

Comportamiento:

- Si el modelo devuelve texto normal, ese texto se trata como respuesta final.
- Si devuelve `TOOL_CALL`, el runner valida tool y argumentos contra policy y registry.
- El resultado vuelve al modelo como `TOOL_RESULT` y se permite otra ronda.
- Si el tool está bloqueado, mal formado o no implementado, el modelo recibe un error estructurado.

Tools soportados hoy en runtime:

- `read_file`
- `write_file`
- `edit_file`
- `glob_search`
- `grep_search`
- `WebFetch`
- `WebSearch`
- `ToolSearch`
- `Skill`
- `bash`
- `TodoWrite`
- `SendUserMessage`
- `StructuredOutput`

Perfiles disponibles (ver `../agents/*.yaml`):

- planner
- debater
- test_writer
- implementer
- diagnoser
- reviewer

## Nota de recursos

Algunos modelos son pesados; Rex debe orquestar con criterio:

- **Un modelo a la vez (serial)**.
- Tras modelos pesados, considerar reiniciar Ollama para liberar VRAM.

Ver: `../docs/VRAM_POLICY.md`.
