from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from discovery import discover_hook_roots, resolve_agent_definition

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


@dataclass(frozen=True)
class HookExecutionResult:
    allowed: bool
    messages: tuple[str, ...] = ()
    error: str | None = None


class HookRunner:
    def __init__(self, *, agent_id: str, workspace: Path):
        self.agent_id = agent_id
        self.workspace = workspace.expanduser().resolve()
        self.core_root = Path(__file__).resolve().parents[1]
        self.pre_tool_use_hooks: tuple[str, ...] = ()
        self.post_tool_use_hooks: tuple[str, ...] = ()
        self._load_hooks()

    def has_hooks(self) -> bool:
        return bool(self.pre_tool_use_hooks or self.post_tool_use_hooks)

    def run_pre_tool_use(self, *, tool_name: str, arguments: dict) -> HookExecutionResult:
        return self._run_hooks(self.pre_tool_use_hooks, tool_name=tool_name, arguments=arguments, result=None)

    def run_post_tool_use(self, *, tool_name: str, arguments: dict, result: dict) -> HookExecutionResult:
        return self._run_hooks(self.post_tool_use_hooks, tool_name=tool_name, arguments=arguments, result=result)

    def _load_hooks(self) -> None:
        if yaml is None:
            return

        pre_hooks: list[str] = []
        post_hooks: list[str] = []

        inline_hooks = self._load_inline_hooks()
        if inline_hooks is not None:
            pre_hooks = list(inline_hooks.get("pre_tool_use", []))
            post_hooks = list(inline_hooks.get("post_tool_use", []))

        for hooks_config in reversed(self._load_external_hook_configs()):
            inherit = hooks_config.get("inherit", True)
            if not isinstance(inherit, bool):
                inherit = True
            if not inherit:
                pre_hooks = []
                post_hooks = []

            if isinstance(hooks_config.get("pre_tool_use"), list):
                pre_hooks = [str(item) for item in hooks_config["pre_tool_use"] if str(item).strip()]
            if isinstance(hooks_config.get("post_tool_use"), list):
                post_hooks = [str(item) for item in hooks_config["post_tool_use"] if str(item).strip()]

            if isinstance(hooks_config.get("add_pre_tool_use"), list):
                pre_hooks.extend(str(item) for item in hooks_config["add_pre_tool_use"] if str(item).strip())
            if isinstance(hooks_config.get("add_post_tool_use"), list):
                post_hooks.extend(str(item) for item in hooks_config["add_post_tool_use"] if str(item).strip())

        self.pre_tool_use_hooks = tuple(pre_hooks)
        self.post_tool_use_hooks = tuple(post_hooks)

    def _load_inline_hooks(self) -> dict | None:
        definition = resolve_agent_definition(self.agent_id, self.workspace, self.core_root)
        if definition is None:
            return None
        try:
            profile = yaml.safe_load(definition.path.read_text(encoding="utf-8")) or {}
        except Exception:
            return None

        hooks = profile.get("hooks")
        return hooks if isinstance(hooks, dict) else None

    def _load_external_hook_configs(self) -> list[dict]:
        configs: list[dict] = []
        for _source, root in discover_hook_roots(self.workspace, self.core_root):
            for candidate in [root / f"{self.agent_id}.yaml", root / f"{self.agent_id}.yml"]:
                if not candidate.is_file():
                    continue
                try:
                    data = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
                except Exception:
                    continue
                if isinstance(data, dict):
                    configs.append(data)
                break
        return configs

    def _run_hooks(self, commands: tuple[str, ...], *, tool_name: str, arguments: dict, result: dict | None) -> HookExecutionResult:
        if not commands:
            return HookExecutionResult(allowed=True)

        messages: list[str] = []
        env = os.environ.copy()
        env.update({
            "OLLAMA_AGENT_ID": self.agent_id,
            "OLLAMA_TOOL_NAME": tool_name,
            "OLLAMA_TOOL_ARGS_JSON": json.dumps(arguments, ensure_ascii=False),
            "OLLAMA_TOOL_RESULT_JSON": json.dumps(result, ensure_ascii=False) if result is not None else "",
        })

        for command in commands:
            completed = subprocess.run(
                ["bash", "-lc", command],
                cwd=str(self.workspace),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            stdout = completed.stdout.strip()
            stderr = completed.stderr.strip()
            if stdout:
                messages.append(stdout)
            if completed.returncode != 0:
                error = stderr or stdout or f"hook failed with exit code {completed.returncode}"
                return HookExecutionResult(allowed=False, messages=tuple(messages), error=error)
            if stderr:
                messages.append(stderr)

        return HookExecutionResult(allowed=True, messages=tuple(messages))