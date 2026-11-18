#!/usr/bin/env python3
"""Run every registered post-build native qualification inspection."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from qualification.native_cases import (
    POST_BUILD_INSPECTIONS,
    ROOT,
    validate_runtime_metadata,
)


def run_post_build_inspections(
    native_root: Path,
    summary: Path,
    *,
    solidcraft_cli: str = "solidcraft-cli",
) -> None:
    """Execute every inspection registered in POST_BUILD_INSPECTIONS."""
    validate_runtime_metadata()
    summary.parent.mkdir(parents=True, exist_ok=True)

    rows = ["case\tinspection\tstatus"]
    for slug, spec in POST_BUILD_INSPECTIONS.items():
        case_root = native_root / slug
        model = case_root / "model.sc"
        command = ROOT / spec["command"]
        output = case_root / spec["output"]

        if not model.is_file():
            raise FileNotFoundError(
                f"missing native baseline for {slug}: {model}"
            )

        subprocess.run(
            [
                solidcraft_cli,
                "run",
                str(command),
                "--in",
                str(model),
                "--param-check",
                "strict",
                "--results",
                "--json-out",
                str(output),
            ],
            check=True,
        )
        rows.append(f"{slug}\t{spec['command']}\tPRODUCED")

    summary.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--solidcraft-cli", default="solidcraft-cli")
    args = parser.parse_args()

    run_post_build_inspections(
        args.native_root,
        args.summary,
        solidcraft_cli=args.solidcraft_cli,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
