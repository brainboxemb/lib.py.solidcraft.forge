"""Project Forge-owned landing metadata without importing scpf."""

from __future__ import annotations

import json
from pathlib import Path
import re
import tomllib


_TESTED = re.compile(
    r'^TESTED_SOLIDCRAFT_VERSION = "([^"]+)"$',
    re.MULTILINE,
)


def landing_metadata(source_root: Path) -> dict[str, str]:
    source_root = source_root.resolve()
    pyproject = tomllib.loads(
        (source_root / "cadlib/pyproject.toml").read_text(encoding="utf-8")
    )
    package_version = str(pyproject["project"]["version"])

    version_source = (
        source_root / "cadlib/src/scpf/version.py"
    ).read_text(encoding="utf-8")
    match = _TESTED.search(version_source)
    if match is None:
        raise ValueError("cannot read TESTED_SOLIDCRAFT_VERSION for Pages")

    return {
        "package_version": package_version,
        "tested_solidcraft_version": match.group(1),
    }


def prepare_landing(source_root: Path, site: Path) -> None:
    data = site / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "forge.json").write_text(
        json.dumps(landing_metadata(source_root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
