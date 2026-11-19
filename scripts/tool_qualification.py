#!/usr/bin/env python3
"""Write the final Forge tool qualification from completed CI dependencies.

This script performs no CAD work. tool.cad.ci has already required the Forge
tool item and every registered example item to pass before this item can run.
Forge then checks each model's semantic result and records one aggregate
qualification artifact.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

from qualification.cases import supported_case_slugs
from qualification.project_metadata import scpf_version
from scpf.version import TESTED_SOLIDCRAFT_VERSION


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"


def read_json(path: Path) -> dict:
    """Read one required JSON object."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing qualification dependency: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"qualification dependency is not an object: {path}")
    return value


def output_path() -> Path:
    """Return the aggregate result path owned by this CI item."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required for tool_qualification")
    return Path(value).resolve() / "tool-qualification.json"


def source_sha() -> str:
    """Return the exact repository revision being qualified."""

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def qualify() -> dict:
    """Validate all required model results and write one tool qualification."""

    tool_state = read_json(BUILD / "scpf" / "item.json")
    if tool_state.get("status") != "pass":
        raise RuntimeError("Forge tool_build/tool_test item is not passing")

    models: dict[str, dict[str, str]] = {}
    for slug in supported_case_slugs():
        path = (
            BUILD
            / "examples"
            / slug
            / "case"
            / "model_verify"
            / slug
            / "qualification-result.json"
        )
        result = read_json(path)
        if result.get("status") != "pass":
            raise RuntimeError(f"{slug}: model_verify is not passing")
        models[slug] = {
            "status": "pass",
            "result": str(path.relative_to(ROOT)).replace("\\", "/"),
        }

    record = {
        "schema": 1,
        "status": "pass",
        "source_commit": source_sha(),
        "forge_version": scpf_version(),
        "solidcraft_version": TESTED_SOLIDCRAFT_VERSION,
        "qualified_at": (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "tool": {
            "tool_build": "pass",
            "tool_test": "pass",
        },
        "models": models,
    }
    target = output_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> int:
    qualify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
