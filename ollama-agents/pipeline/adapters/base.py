from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class CheckResult:
    ok: bool
    summary: str
    stdout: str = ""
    stderr: str = ""
    command: str = ""
    cwd: str = ""


class Adapter(Protocol):
    id: str

    def detect(self, project: Path) -> bool: ...

    def describe(self) -> str: ...

    def commands(self, project: Path) -> list[list[str]]:
        """Return ordered commands to run as quality gates."""
        ...
