#!/usr/bin/env python3
"""Collect results from completed generic Forge example items.

Each example owns one self-contained item output. This module materializes those
outputs into the temporary aggregate tree used by the Forge site/build adapter.
It does not run SolidCraft and does not invent a second verification model.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.project_metadata import scpf_version
from qualification.results import collect as collect_results
from scpf.version import TESTED_SOLIDCRAFT_VERSION


def _now() -> str:
    """Return the UTC timestamp format used by qualification results."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _read_json(path: Path) -> dict:
    """Read one required JSON object and name a missing or invalid file."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing item evidence: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"item evidence must be a JSON object: {path}")
    return value


def _copy_file(source: Path, target: Path) -> None:
    """Copy one required file while creating its destination directory."""

    if not source.is_file() or source.stat().st_size == 0:
        raise RuntimeError(f"missing or empty item evidence: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _copy_tree(source: Path, target: Path) -> None:
    """Copy one required non-empty evidence directory."""

    if not source.is_dir() or not any(source.iterdir()):
        raise RuntimeError(f"missing or empty item evidence directory: {source}")
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def validate_item(build_root: Path, slug: str) -> Path:
    """Return the case output of one completed generic example item."""

    item_root = build_root / "examples" / slug
    state = _read_json(item_root / "item.json")
    if state.get("item") != slug or state.get("status") != "pass":
        raise RuntimeError(f"{slug}: generic CI item is not complete and passing")
    return item_root / "case"


def materialize_case(
    build_root: Path,
    aggregate_root: Path,
    slug: str,
) -> None:
    """Copy one completed example item into Forge's aggregate result tree."""

    case = validate_item(build_root, slug)
    _copy_file(case / f"{slug}.json", aggregate_root / f"{slug}.json")
    _copy_tree(
        case / "stages" / slug,
        aggregate_root / "stages" / slug,
    )
    _copy_tree(
        case / "model_verify" / slug,
        aggregate_root / "model_verify" / slug,
    )


def collect_from_items(
    *,
    build_root: Path,
    out: Path,
    cases: tuple[str, ...],
    source_sha: str,
) -> dict:
    """Collect selected completed items without rerunning any CAD operation."""

    if not cases:
        raise ValueError("at least one example item is required")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for slug in cases:
        materialize_case(build_root, out, slug)

    result = collect_results(
        out,
        source_sha,
        scpf_version(),
        TESTED_SOLIDCRAFT_VERSION,
        _now(),
        cases=cases,
    )
    incomplete = [
        slug
        for slug, record in result.get("cases", {}).items()
        if record.get("status") != "pass"
    ]
    if incomplete:
        raise RuntimeError(
            "item qualification result is not passing: "
            + ", ".join(incomplete)
        )
    return result


def main() -> int:
    """Parse collector arguments and materialize selected item results."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, default=ROOT / "build")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()

    cases = tuple(
        value.strip()
        for value in args.cases.replace(" ", ",").split(",")
        if value.strip()
    )
    collect_from_items(
        build_root=args.build_root,
        out=args.out,
        cases=cases,
        source_sha=args.source_sha,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
