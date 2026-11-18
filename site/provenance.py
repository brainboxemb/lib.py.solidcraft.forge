#!/usr/bin/env python3
"""Create and validate generated site provenance metadata."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


SCHEMA_VERSION = 1
VALID_STAGES = {"preview", "stable"}
VALID_STATUSES = {"pass"}


def create_provenance(
    *,
    stage: str,
    source_ref: str,
    source_commit: str,
    forge_version: str,
    solidcraft_version: str | None,
    workflow_run_id: str,
    qualification_level: str,
    qualification_status: str,
    pull_request: str | None = None,
) -> dict:
    if stage not in VALID_STAGES:
        raise ValueError(f"unsupported publication stage: {stage}")
    if qualification_status not in VALID_STATUSES:
        raise ValueError(
            "only passing output may be published to generated branches"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "source_ref": source_ref,
        "source_commit": source_commit,
        "pull_request": pull_request,
        "forge_version": forge_version,
        "solidcraft_version": solidcraft_version,
        "workflow_run_id": str(workflow_run_id),
        "qualification": {
            "level": qualification_level,
            "status": qualification_status,
        },
        "generated_at": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
    }


def validate_provenance(
    data: dict,
    *,
    stage: str,
    source_commit: str,
    qualification_status: str = "pass",
) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported provenance schema")
    if data.get("stage") != stage:
        raise ValueError(
            f"provenance stage {data.get('stage')!r} != {stage!r}"
        )
    if data.get("source_commit") != source_commit:
        raise ValueError(
            "provenance source commit does not match the promoted build"
        )
    qualification = data.get("qualification") or {}
    if qualification.get("status") != qualification_status:
        raise ValueError(
            "provenance qualification status is not publishable"
        )
    for field in (
        "source_ref",
        "forge_version",
        "workflow_run_id",
        "generated_at",
    ):
        if not data.get(field):
            raise ValueError(f"missing provenance field: {field}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    write = sub.add_parser("write")
    write.add_argument("--out", type=Path, required=True)
    write.add_argument("--stage", choices=sorted(VALID_STAGES), required=True)
    write.add_argument("--source-ref", required=True)
    write.add_argument("--source-commit", required=True)
    write.add_argument("--pull-request")
    write.add_argument("--forge-version", required=True)
    write.add_argument("--solidcraft-version")
    write.add_argument("--workflow-run-id", required=True)
    write.add_argument("--qualification-level", required=True)
    write.add_argument("--qualification-status", default="pass")

    verify = sub.add_parser("verify")
    verify.add_argument("--file", type=Path, required=True)
    verify.add_argument("--stage", choices=sorted(VALID_STAGES), required=True)
    verify.add_argument("--source-commit", required=True)

    args = parser.parse_args()
    if args.command == "write":
        data = create_provenance(
            stage=args.stage,
            source_ref=args.source_ref,
            source_commit=args.source_commit,
            pull_request=args.pull_request,
            forge_version=args.forge_version,
            solidcraft_version=args.solidcraft_version,
            workflow_run_id=args.workflow_run_id,
            qualification_level=args.qualification_level,
            qualification_status=args.qualification_status,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )
        return 0

    data = json.loads(args.file.read_text(encoding="utf-8"))
    validate_provenance(
        data,
        stage=args.stage,
        source_commit=args.source_commit,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
