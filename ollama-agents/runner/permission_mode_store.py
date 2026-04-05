from __future__ import annotations

import json
import os
from pathlib import Path


VALID_PERMISSION_MODES = {"permissive", "strict"}
DEFAULT_PERMISSION_MODE = "permissive"


def resolve_permission_mode(
    workspace: Path | None = None,
    explicit_mode: str | None = None,
) -> tuple[str, str, Path | None]:
    if explicit_mode:
        return _normalize_mode(explicit_mode), "cli", None

    env_mode = os.environ.get("OLLAMA_AGENT_PERMISSION_MODE", "").strip()
    if env_mode:
        return _normalize_mode(env_mode), "env", None

    project_path = project_config_path(workspace)
    project_mode = _read_mode_from_path(project_path)
    if project_mode:
        return project_mode, "project", project_path

    user_path = user_config_path()
    user_mode = _read_mode_from_path(user_path)
    if user_mode:
        return user_mode, "user", user_path

    return DEFAULT_PERMISSION_MODE, "default", None


def save_permission_mode(mode: str, *, workspace: Path | None = None, scope: str = "project") -> Path:
    normalized = _normalize_mode(mode)
    if scope == "project":
        path = project_config_path(workspace)
    elif scope == "user":
        path = user_config_path()
    else:
        raise ValueError(f"Unsupported permission scope: {scope}")

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"permission_mode": normalized}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def project_config_path(workspace: Path | None = None) -> Path:
    base = workspace.resolve() if workspace is not None else Path.cwd().resolve()
    return base / ".openclaw" / "ollama-agents.json"


def user_config_path() -> Path:
    return Path.home() / ".openclaw" / "ollama-agents.json"


def _read_mode_from_path(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    value = data.get("permission_mode")
    if not isinstance(value, str) or not value.strip():
        return None
    return _normalize_mode(value)


def _normalize_mode(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in VALID_PERMISSION_MODES:
        raise ValueError(f"Invalid permission mode: {value!r}")
    return normalized