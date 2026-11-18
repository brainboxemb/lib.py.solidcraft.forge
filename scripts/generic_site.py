#!/usr/bin/env python3
"""Materialize Forge site evidence from a complete generic tool.cad.ci build view.

The durable build branch stores generic item directories. The public site still
uses Forge-specific concepts such as qualification levels and reference
implementations. This module translates the generic store into local site
inputs plus a small compatibility manifest; it never changes the durable store.
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

from qualification.cases import (
    reference_implementations_for,
    supported_case_slugs,
)
from qualification.case_selection import CASE_BY_SLUG
from qualification.project_metadata import scpf_version
from scpf.version import TESTED_SOLIDCRAFT_VERSION


def _now() -> str:
    """Return a stable UTC timestamp for the compatibility manifest."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _read_json(path: Path) -> dict:
    """Read one required JSON object."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing generic build file: {path}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"generic build JSON must be an object: {path}")
    return data


def _copy_tree(source: Path, target: Path) -> None:
    """Copy one required evidence tree into the local site view."""

    if not source.is_dir() or not any(source.iterdir()):
        raise RuntimeError(f"missing generic evidence directory: {source}")
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def _scope(
    item_id: str,
    *,
    overlay_items: frozenset[str],
    pull_request: int | None,
) -> str:
    """Return the public build-branch scope that physically owns an item."""

    if pull_request and item_id in overlay_items:
        return f"pr/{pull_request}"
    return "main"


def _record(
    *,
    row: dict,
    build_scope: str,
    verification_level: str,
    artifact_path: str,
    command_path: str | None = None,
) -> dict:
    """Build one Forge compatibility record from a generic item manifest row."""

    fingerprint = str(row.get("input_fingerprint", ""))
    if not fingerprint:
        raise RuntimeError("generic item manifest row has no input_fingerprint")
    result = {
        "source_commit": row.get("source_commit"),
        "build_scope": build_scope,
        "input_hash": (
            fingerprint
            if fingerprint.startswith("sha256:")
            else f"sha256:{fingerprint}"
        ),
        "verification_level": verification_level,
        "status": "pass",
        "generated_at": _now(),
        "artifact_path": artifact_path,
    }
    if command_path is not None:
        result["command_path"] = command_path
    return result


def materialize(
    *,
    generic_root: Path,
    out: Path,
    pull_request: int | None = None,
    overlay_items: tuple[str, ...] = (),
    mask_cases: tuple[str, ...] = (),
) -> dict:
    """Create local native/reference/diagram inputs and a Forge site manifest."""

    generic_root = generic_root.resolve()
    manifest = _read_json(generic_root / "build.json")
    if manifest.get("schema") != 1 or manifest.get("scope") != "main":
        raise RuntimeError("site input must be a complete resolved generic main view")
    item_rows = manifest.get("items")
    if not isinstance(item_rows, dict):
        raise RuntimeError("generic build manifest has no item map")

    if out.exists():
        shutil.rmtree(out)
    native_root = out / "native"
    reference_root = out / "references"
    diagram_root = out / "diagrams"
    native_root.mkdir(parents=True)
    reference_root.mkdir(parents=True)

    overlay = frozenset(overlay_items)
    masked = frozenset(mask_cases)
    cases: dict[str, dict] = {}

    for slug in supported_case_slugs():
        item_path = f"examples/{slug}"
        row = item_rows.get(item_path)
        if not isinstance(row, dict):
            raise RuntimeError(f"generic build is missing example item: {item_path}")

        implementations: dict[str, dict] = {}
        if slug not in masked:
            native_source = (
                generic_root
                / item_path
                / "case"
                / "native"
                / slug
            )
            result_file = native_source / "qualification-result.json"
            if not result_file.is_file() or result_file.stat().st_size == 0:
                raise RuntimeError(
                    f"{slug}: generic item has no structured qualification result"
                )
            _copy_tree(native_source, native_root / slug)
            implementations["scpf"] = _record(
                row=row,
                build_scope=_scope(
                    slug,
                    overlay_items=overlay,
                    pull_request=pull_request,
                ),
                verification_level="affected-q1-q6",
                artifact_path=f"{item_path}/case/native/{slug}",
                command_path=f"{item_path}/case/{slug}.json",
            )
        cases[slug] = {"implementations": implementations}

    reference_row = item_rows.get("qualification/reference_suite")
    if isinstance(reference_row, dict):
        source = (
            generic_root
            / "qualification"
            / "reference_suite"
            / "references"
        )
        _copy_tree(source, reference_root)
        reference_scope = _scope(
            "reference-suite",
            overlay_items=overlay,
            pull_request=pull_request,
        )
        for slug in supported_case_slugs():
            implementations = cases[slug]["implementations"]
            for implementation in reference_implementations_for(
                CASE_BY_SLUG[slug]
            ):
                evidence = source / slug / implementation
                if not evidence.is_dir():
                    continue
                implementations[implementation] = _record(
                    row=reference_row,
                    build_scope=reference_scope,
                    verification_level="reference",
                    artifact_path=(
                        "qualification/reference_suite/references/"
                        f"{slug}/{implementation}"
                    ),
                )

    diagram_row = item_rows.get("qualification/diagrams")
    if isinstance(diagram_row, dict):
        _copy_tree(
            generic_root / "qualification/diagrams/rendered",
            diagram_root,
        )

    compatibility = {
        "schema_version": 2,
        "scope": "main",
        "source_ref": "generic-build",
        "source_commit": manifest.get("source_commit"),
        "base_commit": None,
        "pull_request": pull_request,
        "workflow_run_id": "generic-store",
        "toolchain": {
            "forge_version": scpf_version(),
            "solidcraft_version": TESTED_SOLIDCRAFT_VERSION,
        },
        "verification": {"level": "per-case", "status": "pass"},
        "generated_at": _now(),
        "cases": cases,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "build.json").write_text(
        json.dumps(compatibility, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return compatibility


def main() -> int:
    """Parse a generic build-view materialization request."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generic-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--overlay-items", nargs="*", default=())
    parser.add_argument("--mask-cases", nargs="*", default=())
    args = parser.parse_args()
    materialize(
        generic_root=args.generic_root,
        out=args.out,
        pull_request=args.pull_request,
        overlay_items=tuple(args.overlay_items),
        mask_cases=tuple(args.mask_cases),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
