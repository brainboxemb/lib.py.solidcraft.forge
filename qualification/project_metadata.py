"""Repository project metadata used by qualification and site tooling."""

from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def scpf_version(root: Path = ROOT) -> str:
    """Read the single SCPF package version from scpf/pyproject.toml."""
    with (root / "scpf" / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return str(data["project"]["version"])
