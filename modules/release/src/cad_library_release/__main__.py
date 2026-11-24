"""Validate stable CAD-library build evidence for one exact release source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


_SHA = re.compile(r"^[0-9a-f]{40}$")


class ReleaseQualificationError(RuntimeError):
    """Stable durable evidence does not qualify the requested source."""


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise ReleaseQualificationError(f"missing release evidence: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseQualificationError(f"invalid release evidence: {path}") from exc
    if not isinstance(value, dict):
        raise ReleaseQualificationError(f"release evidence is not an object: {path}")
    return value


def validate_build_scope(build_scope: Path, source_sha: str) -> dict:
    """Require one complete stable build scope for the exact requested source."""

    build_scope = build_scope.resolve()
    source_sha = source_sha.strip().lower()
    if _SHA.fullmatch(source_sha) is None:
        raise ReleaseQualificationError("source_sha must be exactly 40 lowercase hex characters")

    plan = _read_json(build_scope / "build-plan.json")
    if plan.get("schema") != 2:
        raise ReleaseQualificationError("unsupported build-plan schema")
    if plan.get("source_sha") != source_sha:
        raise ReleaseQualificationError("stable build source does not match release source")
    if plan.get("full") is not True:
        raise ReleaseQualificationError("release requires a full stable build")
    if plan.get("library") is not True:
        raise ReleaseQualificationError("stable build did not qualify the library")

    active = plan.get("active")
    selected = plan.get("selected")
    if not isinstance(active, list) or not all(isinstance(item, str) for item in active):
        raise ReleaseQualificationError("build plan has invalid active model owners")
    if not isinstance(selected, list) or selected != active:
        raise ReleaseQualificationError("release requires every active model owner to be selected")

    rows = plan.get("models")
    if not isinstance(rows, list):
        raise ReleaseQualificationError("build plan has invalid model rows")
    row_ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(row_ids) != len(rows) or row_ids != active:
        raise ReleaseQualificationError("build plan model rows do not match active owners")

    for owner in active:
        root = build_scope / "models" / owner
        result = _read_json(root / "result.json")
        if result.get("id") != owner or result.get("status") != "pass":
            raise ReleaseQualificationError(f"model is not successful: {owner}")
        provenance = _read_json(root / "source.json")
        if provenance.get("source_sha") != source_sha:
            raise ReleaseQualificationError(f"model source does not match release source: {owner}")

    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-scope", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    validate_build_scope(args.build_scope, args.source_sha)
    print(f"qualified stable CAD-library build {args.source_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
