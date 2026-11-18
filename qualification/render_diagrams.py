#!/usr/bin/env python3
"""Render all version-pinned CADCraft qualification diagrams."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def render_all(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    run(["bash", "qualification/setup_cadcraft.sh"])
    install_dir = (
        Path.home()
        / ".cache"
        / "cadcraft"
        / "0.20.1-linux-x86_64"
    )
    cli = install_dir / "cadcraft-cli"
    if not cli.is_file():
        raise RuntimeError(f"CADCraft CLI not found after setup: {cli}")
    env = dict(os.environ)
    env["PATH"] = str(install_dir) + os.pathsep + env.get("PATH", "")
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
            ],
            env=env,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    render_all(args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
