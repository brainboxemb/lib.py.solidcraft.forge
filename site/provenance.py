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
    qualification_source_commit: str | None = None,
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
            **(
                {"source_commit": qualification_source_commit}
                if qualification_source_commit
                else {}
            ),
        },
        "generated_at": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
    }


def create_reused_provenance(
    *,
    stage: str,
    source_ref: str,
    source_commit: str,
    evidence_file: Path,
    workflow_run_id: str,
    qualification_level: str = "q1-q6-full",
) -> dict:
    evidence = json.loads(Path(evidence_file).read_text(encoding="utf-8"))
    if evidence.get("verified") is not True:
        raise ValueError("reused qualification evidence is not verified")
    for field in ("source_commit", "forge_version", "solidcraft_version"):
        if not evidence.get(field):
            raise ValueError(
                f"reused qualification evidence is missing {field}"
            )
    return create_provenance(
        stage=stage,
        source_ref=source_ref,
        source_commit=source_commit,
        forge_version=evidence["forge_version"],
        solidcraft_version=evidence["solidcraft_version"],
        workflow_run_id=workflow_run_id,
        qualification_level=qualification_level,
        qualification_status="pass",
        qualification_source_commit=evidence["source_commit"],
    )


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

    reused = sub.add_parser("write-reused")
    reused.add_argument("--out", type=Path, required=True)
    reused.add_argument("--stage", choices=sorted(VALID_STAGES), required=True)
    reused.add_argument("--source-ref", required=True)
    reused.add_argument("--source-commit", required=True)
    reused.add_argument("--evidence", type=Path, required=True)
    reused.add_argument("--workflow-run-id", required=True)
    reused.add_argument(
        "--qualification-level",
        default="q1-q6-full",
    )

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

    if args.command == "write-reused":
        data = create_reused_provenance(
            stage=args.stage,
            source_ref=args.source_ref,
            source_commit=args.source_commit,
            evidence_file=args.evidence,
            workflow_run_id=args.workflow_run_id,
            qualification_level=args.qualification_level,
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
