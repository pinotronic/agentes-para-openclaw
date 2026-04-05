from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DefinitionSource:
    kind: str
    label: str


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    path: Path
    source: DefinitionSource
    shadowed_by: str | None = None


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    path: Path
    source: DefinitionSource
    description: str | None = None
    shadowed_by: str | None = None


PROJECT_OPENCLAW = DefinitionSource("project", "project-openclaw")
PROJECT_OLLAMA = DefinitionSource("project", "project-ollama-agents")
USER_HOME = DefinitionSource("user", "user-home")
USER_OPENCLAW = DefinitionSource("user", "user-openclaw")
USER_AGENTS = DefinitionSource("user", "user-agents")
ENV_HOME = DefinitionSource("env", "env-ollama-agents-home")
CORE = DefinitionSource("core", "core")


def _base_search_path(workspace: Path | None) -> Path:
    return workspace.resolve() if workspace is not None else Path.cwd().resolve()


def discover_agent_roots(workspace: Path | None, core_root: Path) -> list[tuple[DefinitionSource, Path]]:
    roots: list[tuple[DefinitionSource, Path]] = []
    seen: set[Path] = set()
    base = _base_search_path(workspace)

    for ancestor in [base, *base.parents]:
        for source, candidate in [
            (PROJECT_OPENCLAW, ancestor / ".openclaw" / "agents"),
            (PROJECT_OLLAMA, ancestor / ".ollama-agents" / "agents"),
        ]:
            if candidate.is_dir() and candidate not in seen:
                roots.append((source, candidate))
                seen.add(candidate)

    env_home = os.environ.get("OLLAMA_AGENTS_HOME", "").strip()
    if env_home:
        candidate = Path(env_home).expanduser().resolve() / "agents"
        if candidate.is_dir() and candidate not in seen:
            roots.append((ENV_HOME, candidate))
            seen.add(candidate)

    home = Path.home()
    for source, candidate in [
        (USER_OPENCLAW, home / ".openclaw" / "agents"),
        (USER_AGENTS, home / ".agents" / "agents"),
        (USER_HOME, home / ".ollama-agents" / "agents"),
    ]:
        if candidate.is_dir() and candidate not in seen:
            roots.append((source, candidate))
            seen.add(candidate)

    core_agents = core_root / "agents"
    if core_agents.is_dir() and core_agents not in seen:
        roots.append((CORE, core_agents))

    return roots


def discover_skill_roots(workspace: Path | None, core_root: Path) -> list[tuple[DefinitionSource, Path]]:
    roots: list[tuple[DefinitionSource, Path]] = []
    seen: set[Path] = set()
    base = _base_search_path(workspace)

    for ancestor in [base, *base.parents]:
        for source, candidate in [
            (PROJECT_OPENCLAW, ancestor / ".openclaw" / "skills"),
            (PROJECT_OPENCLAW, ancestor / ".openclaw" / "commands"),
            (PROJECT_OLLAMA, ancestor / ".ollama-agents" / "skills"),
            (PROJECT_OLLAMA, ancestor / ".ollama-agents" / "commands"),
        ]:
            if candidate.is_dir() and candidate not in seen:
                roots.append((source, candidate))
                seen.add(candidate)

    env_home = os.environ.get("OLLAMA_AGENTS_HOME", "").strip()
    if env_home:
        for leaf in ["skills", "commands"]:
            candidate = Path(env_home).expanduser().resolve() / leaf
            if candidate.is_dir() and candidate not in seen:
                roots.append((ENV_HOME, candidate))
                seen.add(candidate)

    home = Path.home()
    for source, candidate in [
        (USER_OPENCLAW, home / ".openclaw" / "skills"),
        (USER_OPENCLAW, home / ".openclaw" / "commands"),
        (USER_AGENTS, home / ".agents" / "skills"),
        (USER_HOME, home / ".ollama-agents" / "skills"),
    ]:
        if candidate.is_dir() and candidate not in seen:
            roots.append((source, candidate))
            seen.add(candidate)

    for leaf in ["skills", "commands"]:
        candidate = core_root / leaf
        if candidate.is_dir() and candidate not in seen:
            roots.append((CORE, candidate))
            seen.add(candidate)

    return roots


def discover_hook_roots(workspace: Path | None, core_root: Path) -> list[tuple[DefinitionSource, Path]]:
    roots: list[tuple[DefinitionSource, Path]] = []
    seen: set[Path] = set()
    base = _base_search_path(workspace)

    for ancestor in [base, *base.parents]:
        for source, candidate in [
            (PROJECT_OPENCLAW, ancestor / ".openclaw" / "hooks"),
            (PROJECT_OLLAMA, ancestor / ".ollama-agents" / "hooks"),
        ]:
            if candidate.is_dir() and candidate not in seen:
                roots.append((source, candidate))
                seen.add(candidate)

    env_home = os.environ.get("OLLAMA_AGENTS_HOME", "").strip()
    if env_home:
        candidate = Path(env_home).expanduser().resolve() / "hooks"
        if candidate.is_dir() and candidate not in seen:
            roots.append((ENV_HOME, candidate))
            seen.add(candidate)

    home = Path.home()
    for source, candidate in [
        (USER_OPENCLAW, home / ".openclaw" / "hooks"),
        (USER_AGENTS, home / ".agents" / "hooks"),
        (USER_HOME, home / ".ollama-agents" / "hooks"),
    ]:
        if candidate.is_dir() and candidate not in seen:
            roots.append((source, candidate))
            seen.add(candidate)

    core_hooks = core_root / "hooks"
    if core_hooks.is_dir() and core_hooks not in seen:
        roots.append((CORE, core_hooks))

    return roots


def list_agent_definitions(workspace: Path | None, core_root: Path) -> list[AgentDefinition]:
    definitions: list[AgentDefinition] = []
    active: dict[str, str] = {}

    for source, root in discover_agent_roots(workspace, core_root):
        local_defs = [
            AgentDefinition(name=path.stem, path=path, source=source)
            for path in sorted(root.glob("*.y*ml"))
        ]
        for definition in local_defs:
            key = definition.name.lower()
            if key in active:
                definitions.append(
                    AgentDefinition(
                        name=definition.name,
                        path=definition.path,
                        source=definition.source,
                        shadowed_by=active[key],
                    )
                )
            else:
                active[key] = definition.source.label
                definitions.append(definition)

    return definitions


def resolve_agent_definition(agent_id: str, workspace: Path | None, core_root: Path) -> AgentDefinition | None:
    for definition in list_agent_definitions(workspace, core_root):
        if definition.shadowed_by is None and definition.name == agent_id:
            return definition
    return None


def list_skill_definitions(workspace: Path | None, core_root: Path) -> list[SkillDefinition]:
    definitions: list[SkillDefinition] = []
    active: dict[str, str] = {}

    for source, root in discover_skill_roots(workspace, core_root):
        local_defs: list[SkillDefinition] = []
        for path in sorted(root.iterdir()):
            skill_path = _resolve_skill_file(path)
            if skill_path is None:
                continue
            name, description = _parse_skill_metadata(skill_path)
            resolved_name = name or (skill_path.parent.name if skill_path.name == "SKILL.md" else skill_path.stem)
            local_defs.append(
                SkillDefinition(
                    name=resolved_name,
                    path=skill_path,
                    source=source,
                    description=description,
                )
            )
        for definition in sorted(local_defs, key=lambda item: item.name.lower()):
            key = definition.name.lower()
            if key in active:
                definitions.append(
                    SkillDefinition(
                        name=definition.name,
                        path=definition.path,
                        source=definition.source,
                        description=definition.description,
                        shadowed_by=active[key],
                    )
                )
            else:
                active[key] = definition.source.label
                definitions.append(definition)

    return definitions


def resolve_skill_definition(skill_name: str, workspace: Path | None, core_root: Path) -> SkillDefinition | None:
    for definition in list_skill_definitions(workspace, core_root):
        if definition.shadowed_by is None and definition.name.lower() == skill_name.lower():
            return definition
    return None


def _resolve_skill_file(path: Path) -> Path | None:
    if path.is_dir():
        candidate = path / "SKILL.md"
        return candidate if candidate.is_file() else None
    if path.is_file() and path.suffix.lower() == ".md":
        return path
    return None


def _parse_skill_metadata(path: Path) -> tuple[str | None, str | None]:
    try:
        contents = path.read_text(encoding="utf-8")
    except Exception:
        return None, None

    lines = iter(contents.splitlines())
    if next(lines, "").strip() != "---":
        return None, None

    name = None
    description = None
    for line in lines:
        trimmed = line.strip()
        if trimmed == "---":
            break
        if trimmed.startswith("name:"):
            value = trimmed.split(":", 1)[1].strip().strip('"\'')
            name = value or None
        elif trimmed.startswith("description:"):
            value = trimmed.split(":", 1)[1].strip().strip('"\'')
            description = value or None

    return name, description