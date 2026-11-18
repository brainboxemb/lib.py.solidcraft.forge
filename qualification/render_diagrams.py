#!/usr/bin/env python3
"""Render all version-pinned CADCraft qualification diagrams."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def render_all(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    run(["bash", "qualification/setup_cadcraft.sh"])
    plans = sorted((ROOT / "qualification" / "diagrams").glob("*.cadcraft.json"))
    if not plans:
        raise RuntimeError("no CADCraft qualification diagrams found")
    for plan in plans:
        run(
            [
                "bash",
                "qualification/render_cadcraft_diagram.sh",
                str(plan),
                str(out),
            ]
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    render_all(args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
