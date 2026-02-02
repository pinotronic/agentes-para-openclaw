from __future__ import annotations

from pathlib import Path


class RustCargoAdapter:
    id = "rust-cargo"

    def detect(self, project: Path) -> bool:
        return (project / "Cargo.toml").exists()

    def describe(self) -> str:
        return "Rust project (cargo test/clippy/fmt)."

    def commands(self, project: Path) -> list[list[str]]:
        return [
            ["cargo", "fmt", "--all", "--", "--check"],
            ["cargo", "clippy", "--all-targets", "--all-features", "--", "-D", "warnings"],
            ["cargo", "test"],
        ]
