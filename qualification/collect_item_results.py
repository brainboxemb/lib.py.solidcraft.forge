#!/usr/bin/env python3
"""Collect Forge qualification evidence from completed tool.cad.ci example items.

The generic runner stores each example below build/examples/<slug>. This module
translates those consumer-owned item outputs into the aggregate shape still
used by Forge's result collector and website. It never runs SolidCraft.
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
    """Read one required JSON object and name the missing/invalid file."""

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
    """Return the case output of one completed generic example item.

    The runner writes item.json only when the final configured step completed.
    Requiring that state prevents a cheap integration-only run from being
    mistaken for a native-qualified item.
    """

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
    """Copy one completed item into Forge's temporary aggregate result shape."""

    case = validate_item(build_root, slug)

    # Keep this translation local to Forge. The generic store deliberately does
    # not know that these files are commands, stage records or native evidence.
    _copy_file(case / f"{slug}.json", aggregate_root / f"{slug}.json")
    _copy_tree(
        case / "stages" / slug,
        aggregate_root / "stages" / slug,
    )
    _copy_tree(
        case / "native" / slug,
        aggregate_root / "native" / slug,
    )
    for level in ("q1", "q2"):
        _copy_file(
            case / "qualification" / "case-evidence" / level / f"{slug}.txt",
            aggregate_root
            / "qualification"
            / "case-evidence"
            / level
            / f"{slug}.txt",
        )


def write_validation_summaries(
    aggregate_root: Path,
    cases: tuple[str, ...],
) -> None:
    """Write the two legacy TSV summaries still consumed by results.collect."""

    qualification = aggregate_root / "qualification"
    qualification.mkdir(parents=True, exist_ok=True)
    native_rows = ["case\tq4\tq5\n"]
    visual_rows = ["case\tstatus\n"]

    for slug in cases:
        native = _read_json(
            aggregate_root / "native" / slug / "validation.json"
        )
        visual = _read_json(
            aggregate_root / "native" / slug / "visual-validation.json"
        )
        q4 = str(native.get("q4", "missing")).upper()
        q5 = str(native.get("q5", "missing")).upper()
        status = str(visual.get("status", "missing")).upper()
        native_rows.append(f"{slug}\t{q4}\t{q5}\n")
        visual_rows.append(f"{slug}\t{status}\n")

    (qualification / "native-validation.tsv").write_text(
        "".join(native_rows),
        encoding="utf-8",
    )
    (qualification / "visual-validation.tsv").write_text(
        "".join(visual_rows),
        encoding="utf-8",
    )


def collect_from_items(
    *,
    build_root: Path,
    out: Path,
    cases: tuple[str, ...],
    source_sha: str,
) -> dict:
    """Collect selected completed items without rerunning any qualification."""

    if not cases:
        raise ValueError("at least one example item is required")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for slug in cases:
        materialize_case(build_root, out, slug)
    write_validation_summaries(out, cases)

    result = collect_results(
        out / "qualification",
        out / "native",
        source_sha,
        scpf_version(),
        TESTED_SOLIDCRAFT_VERSION,
        _now(),
        output_root=out,
        stages_root=out / "stages",
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
