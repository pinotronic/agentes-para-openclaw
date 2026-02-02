from __future__ import annotations

from pathlib import Path


class PythonPytestAdapter:
    id = "python-pytest"

    def detect(self, project: Path) -> bool:
        if (project / "pyproject.toml").exists():
            return True
        if (project / "pytest.ini").exists() or (project / "tox.ini").exists():
            return True
        if any(project.glob("tests/test_*.py")):
            return True
        return False

    def describe(self) -> str:
        return "Python project (pytest)."

    def commands(self, project: Path) -> list[list[str]]:
        # Conservative defaults; project can override by providing a .openclaw-pipeline.json later.
        cmds: list[list[str]] = []
        # Prefer uv if present
        if (project / "uv.lock").exists():
            cmds.append(["uv", "run", "pytest", "-q"])
        else:
            cmds.append(["python3", "-m", "pytest", "-q"])
        # Optional: ruff if available
        cmds.append(["python3", "-m", "ruff", "check", "."])
        return cmds
