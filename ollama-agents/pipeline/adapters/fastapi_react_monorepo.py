from __future__ import annotations

from pathlib import Path


class FastAPIReactMonorepoAdapter:
    """Adapter for a simple monorepo with:

    - backend/ (Python + pytest) with optional .venv
    - frontend/ (React/TS) with pnpm scripts

    The pipeline will run quality gates in each subproject.
    """

    id = "fastapi-react-monorepo"

    def detect(self, project: Path) -> bool:
        backend = project / "backend"
        frontend = project / "frontend"
        if not backend.is_dir() or not frontend.is_dir():
            return False

        backend_ok = (backend / "pyproject.toml").exists() or (backend / "pytest.ini").exists()
        frontend_ok = (frontend / "package.json").exists()

        # Ensure it smells like React/Vite (optional heuristic)
        if frontend_ok:
            pkg = (frontend / "package.json").read_text(encoding="utf-8", errors="ignore").lower()
            frontend_ok = "react" in pkg

        return bool(backend_ok and frontend_ok)

    def describe(self) -> str:
        return "Monorepo: backend (FastAPI/pytest) + frontend (React/TS via pnpm)."

    def commands(self, project: Path) -> list[list[str]]:
        backend = project / "backend"
        frontend = project / "frontend"

        cmds: list[list[str]] = []

        # Backend gates
        if (backend / ".venv").exists():
            # Use venv if present
            cmds.append([
                "bash",
                "-lc",
                "cd backend && . .venv/bin/activate && pytest -q",
            ])
        else:
            # Fallback: system python (may fail if deps missing)
            cmds.append(["bash", "-lc", "cd backend && python3 -m pytest -q"])

        # Frontend gates (pnpm)
        cmds.append(["bash", "-lc", "cd frontend && pnpm -s test"])
        cmds.append(["bash", "-lc", "cd frontend && pnpm -s lint"])
        cmds.append(["bash", "-lc", "cd frontend && pnpm -s build"])

        return cmds
