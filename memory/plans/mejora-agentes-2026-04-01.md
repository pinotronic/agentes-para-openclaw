# Plan: Mejora de Agentes con lessons de claw-code

**Fecha:** 2026-04-01  
**Inspiración:** `claw-code` (Rust) — permission system, tool restrictions per agent, agent spawning  
**Ubicación plan:** `memory/plans/mejora-agentes-2026-04-01.md`

---

## Diagnóstico Actual

Nuestros agentes en `~/.openclaw/workspace/ollama-agents/agents/*.yaml`):

| Agente | Problema |
|--------|----------|
| `code_critic` | Sin restricción de tools — podría escribir archivos |
| `defender` | Sin restricción — podría ejecutar bash |
| `implementer` | Acceso total — sin permisos |
| `planner` | Sin permisos granulares |
| `reviewer` | Sin estructura de manifest |
| `coordinator` | Muy básico, no maneja permisos |

**Problemas concretos:**
1. Aucun agent n'a de restrictions sur les tools — tout peut tout faire
2. Pas de `permission mode` (ReadOnly, WorkspaceWrite, DangerFullAccess)
3. Les agents ne persitent pas leur output dans un format structuré
4. Pas de registry centralisé des tools disponibles
5. Pas d'aliases pour les tools (read → read_file, etc.)
6. Pas de skill loader intégré
7. Pas de notion de "policy" par agent

---

## Arquitectura Deseada (Inspirada en claw-code)

```
┌─────────────────────────────────────────────────┐
│              GlobalToolRegistry                  │
│  ┌─────────────┐  ┌──────────────────────────┐  │
│  │ Builtin     │  │ Plugin Tools            │  │
│  │ (bash,      │  │ (custom)                │  │
│  │  read_file, │  │                         │  │
│  │  write_file)│  │                         │  │
│  └─────────────┘  └──────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ PermissionPolicy (par tool)              │  │
│  │   bash       → DangerFullAccess         │  │
│  │   read_file  → ReadOnly                  │  │
│  │   write_file → WorkspaceWrite            │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ AgentPermissionPolicy                           │
│  ┌──────────┬─────────────────────────────────┐ │
│  │code_critic│ read, glob, grep, web_search │ │
│  │defender  │ read, glob, grep              │ │
│  │implementer│ read, write, edit, bash       │ │
│  │reviewer  │ read, glob, grep              │ │
│  │planner   │ read, glob, grep, todo_write  │ │
│  └──────────┴─────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## Fases de Implementación

### Fase 0 — Auditoría y Estructura Base

**Objetivo:** Crear el esqueleto del nuevo sistema de permisos

**Entregables:**
- [ ] `agents/registry.py` — ToolRegistry centralizado con specs
- [ ] `agents/permissions.py` — PermissionMode enum + PermissionPolicy
- [ ] `agents/base.py` — Clase Agent base con permission checking
- [ ] Tests para PermissionMode y PermissionPolicy

**Criterio de aceptación:** 
```bash
python -c "from agents.registry import ToolRegistry; r = ToolRegistry(); print(r.list_tools())"
# Output: ['bash', 'read', 'write', 'edit', 'glob', 'grep', ...]
```

---

### Fase 1 — Tool Registry y Specs

**Objetivo:** Definir todas las tools con sus schemas y permissions requeridos

**Entregables:**
- [ ] `ToolSpec` dataclass: name, description, input_schema, required_permission
- [ ] 18 tool specs mínimo (clon de MVP de claw-code)
- [ ] Tool aliases: `read` → `read_file`, `write` → `write_file`, `edit` → `edit_file`, `glob` → `glob_search`, `grep` → `grep_search`
- [ ] `GlobalToolRegistry` con `normalize_allowed_tools()`
- [ ] Tests: verify tool specs, aliases, permission lookup

**Tool Specs a implementar:**

| Tool | Permission | Input Schema |
|------|------------|--------------|
| `bash` | DangerFullAccess | `{command, timeout?, run_in_background?}` |
| `read_file` | ReadOnly | `{path, offset?, limit?}` |
| `write_file` | WorkspaceWrite | `{path, content}` |
| `edit_file` | WorkspaceWrite | `{path, old_string, new_string, replace_all?}` |
| `glob_search` | ReadOnly | `{pattern, path?}` |
| `grep_search` | ReadOnly | `{pattern, path?, glob?, output_mode?, ...}` |
| `web_fetch` | ReadOnly | `{url, prompt}` |
| `web_search` | ReadOnly | `{query, allowed_domains?, blocked_domains?}` |
| `todo_write` | WorkspaceWrite | `{todos: [{content, activeForm, status}]}` |
| `skill` | ReadOnly | `{skill, args?}` |
| `agent` | DangerFullAccess | `{description, prompt, subagent_type?, name?, model?}` |
| `tool_search` | ReadOnly | `{query, max_results?}` |
| `notebook_edit` | WorkspaceWrite | `{notebook_path, cell_id?, new_source?, cell_type?, edit_mode?}` |
| `sleep` | ReadOnly | `{duration_ms}` |
| `send_message` | ReadOnly | `{message, attachments?, status}` |
| `config` | WorkspaceWrite | `{setting, value?}` |
| `structured_output` | ReadOnly | `{...}` |
| `repl` | DangerFullAccess | `{code, language, timeout_ms?}` |
| `powershell` | DangerFullAccess | `{command, timeout?, run_in_background?}` |

---

### Fase 2 — Agent Permission Policies

**Objetivo:** Definir qué tools puede usar cada agente

**Entregables:**
- [ ] `AgentPermissionPolicy` — mapeo agente → tools permitidas
- [ ] Aplicar a cada archivo `.yaml` existente

**Policies propuestas:**

```python
AGENT_TOOLS = {
    "code_critic": ["read", "glob", "grep", "web_search", "tool_search", "skill", "structured_output"],
    "defender": ["read", "glob", "grep", "skill", "structured_output", "send_message"],
    "implementer": ["read", "write", "edit", "bash", "glob", "grep", "skill"],
    "reviewer": ["read", "glob", "grep", "web_fetch", "skill", "structured_output"],
    "planner": ["read", "glob", "grep", "web_search", "web_fetch", "todo_write", "skill", "structured_output", "send_message"],
    "diagnoser": ["read", "bash", "glob", "grep"],
    "debater": ["read", "glob", "grep", "skill", "structured_output", "send_message"],
    "test_writer": ["read", "write", "glob", "grep", "skill"],
}
```

- [ ] Validación: agente no puede usar tool fuera de su allowlist
- [ ] Tests: code_critic con bash debe fallar con PermissionDenied

---

### Fase 3 — Tool Executor con Permission Enforcement

**Objetivo:** Crear el executor que valida permissions antes de ejecutar

**Entregables:**
- [ ] `ToolExecutor` que recibe `GlobalToolRegistry` + `PermissionPolicy`
- [ ] `execute_tool(name, input)` → valida permission → ejecuta o raise PermissionDenied
- [ ] Integrar con `run.py` pipeline existente
- [ ] Logs con trace_id para auditoría

**Criterio de aceptación:**
```python
executor = ToolExecutor(registry, policy)
executor.execute("bash", {"command": "rm -rf /"})  
# → PermissionDenied: code_critic not allowed to use bash
```

---

### Fase 4 — Agent Manifest y Persistence

**Objetivo:** Agents guardan su output en formato estructurado (inspirado en claw-code AgentOutput)

**Entregables:**
- [ ] `AgentManifest` dataclass: agent_id, name, description, status, output_file, created_at, started_at, completed_at, error
- [ ] `AgentOutput` — formato del output de cada agent
- [ ] Persistencia en `.agent_store/` por proyecto
- [ ] `get_agent_status(agent_id)` — consultar estado
- [ ] Tests de manifest creation y persistence

---

### Fase 5 — Sub-agent Spawning (delegación)

**Objetivo:** Un agente puede spawnear sub-agents con tools restringidas (como claw-code Agent tool)

**Inspirado en:** `claw-code/rust/crates/tools/src/lib.rs` → `execute_agent()`

**Entregables:**
- [ ] `spawn_agent(name, prompt, subagent_type, allowed_tools)` 
- [ ] Subagent types: `Explore`, `Plan`, `Verification`, `general-purpose`
- [ ] Output persistence con manifest
- [ ] Integración con `run_redblue.py`

**Nota:** Usará Ollama local (no API externa como claw-code)

---

### Fase 6 — Skill Loader Mejorado

**Objetivo:** Integrar skill loading como tool (como claw-code Skill tool)

**Entregables:**
- [ ] `SkillLoader` que busca en paths configurables:
  - `$CODEX_HOME/skills/`
  - `$HOME/.agents/skills/`
  - `/home/administrador/.openclaw/skills/`
- [ ] Tool `skill` → carga SKILL.md, retorna prompt
- [ ] Soporte para `$skill` y `/skill` aliases
- [ ] Tests: cargar skill existente

---

## Dependencias

```
Fase 0 → Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5 → Fase 6
```

Cada fase requiere que la anterior esté aprobada por tests.

---

## Hitos

| Hito | Descripción | Criterio |
|------|-------------|----------|
| H1 | Tool Registry básico | `ToolRegistry().list_tools()` funciona |
| H2 | Permission system | `PermissionMode.DangerFullAccess` enforced |
| H3 | Agents con policies | `code_critic` no puede hacer `bash` |
| H4 | Executor en pipeline | Pipeline existente usa executor con permisos |
| H5 | Agent manifest | `AgentManifest` persiste en `.agent_store/` |
| H6 | Sub-agent spawning | `planner` puede delegar a `Explore` sub-agent |
| H7 | Skill tool | `skill("coding-agent")` retorna prompt |

---

## Ubicación archivos nuevos

```
~/.openclaw/workspace/ollama-agents/
├── agents/
│   ├── registry.py      # NEW: Tool registry
│   ├── permissions.py   # NEW: Permission modes + policies
│   ├── executor.py      # NEW: Tool executor con permission enforcement
│   ├── agent_base.py    # NEW: Clase base Agent
│   ├── manifest.py      # NEW: AgentManifest + persistence
│   ├── skill_loader.py  # NEW: Skill loading
│   └── *.yaml           # EXISTING: agent configs
├── pipeline/
│   ├── run.py           # MODIFY: usar executor
│   ├── run_redblue.py   # MODIFY: usar executor
│   └── run_with_permissions.py  # NEW: pipeline con permisos
├── tests/
│   ├── test_registry.py
│   ├── test_permissions.py
│   ├── test_executor.py
│   └── test_manifest.py
└── .agent_store/         # NEW: agent output persistence
```

---

## Empezar por: Fase 0

**Acción inmediata:**
1. Crear `agents/registry.py` con `ToolSpec` y `ToolRegistry`
2. Crear `agents/permissions.py` con `PermissionMode` y `PermissionPolicy`
3. Escribir tests en `tests/test_registry.py` y `tests/test_permissions.py`
4. Correr tests → verde → siguiente fase

**Comando para iniciar:**
```bash
cd ~/.openclaw/workspace/ollama-agents
python -m pytest tests/test_registry.py tests/test_permissions.py -v
```
