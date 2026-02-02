from __future__ import annotations

from pathlib import Path


class NodeAdapter:
    id = "node"

    def detect(self, project: Path) -> bool:
        return (project / "package.json").exists()

    def describe(self) -> str:
        return "Node/JS/TS project (npm scripts)."

    def commands(self, project: Path) -> list[list[str]]:
        # Prefer npm scripts if present; fall back gracefully.
        cmds: list[list[str]] = []
        cmds.append(["npm", "test", "--silent"])
        cmds.append(["npm", "run", "lint", "--silent"])
        cmds.append(["npm", "run", "typecheck", "--silent"])
        return cmds
