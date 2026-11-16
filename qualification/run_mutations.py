#!/usr/bin/env python3
"""Run every registered Q5 saved-design mutation in native SolidCraft."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from qualification.native_cases import MUTATIONS, ROOT, validate_runtime_metadata


def run_mutations(
    native_root: Path,
    summary: Path,
    *,
    solidcraft_cli: str = "solidcraft-cli",
) -> None:
    """Execute the Q5 mutation registered for every required qualification case."""
    validate_runtime_metadata()
    summary.parent.mkdir(parents=True, exist_ok=True)

    rows = ["case\tmutation\tstatus"]
    for slug, spec in MUTATIONS.items():
        case_root = native_root / slug
        model = case_root / "model.sc"
        command = ROOT / spec["command"]
        saved = case_root / spec["save"]
        measurements = case_root / spec["measurements"]

        if not model.is_file():
            raise FileNotFoundError(f"missing native baseline for {slug}: {model}")

        subprocess.run(
            [
                solidcraft_cli,
                "run",
                str(command),
                "--in",
                str(model),
                "--param-check",
                "strict",
                "--save",
                str(saved),
            ],
            check=True,
        )
        subprocess.run(
            [
                solidcraft_cli,
                "eval",
                str(saved),
                "--json-out",
                str(measurements),
            ],
            check=True,
        )
        rows.append(f"{slug}\t{spec['label']}\tPRODUCED")

    summary.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--solidcraft-cli", default="solidcraft-cli")
    args = parser.parse_args()

    run_mutations(
        args.native_root,
        args.summary,
        solidcraft_cli=args.solidcraft_cli,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
