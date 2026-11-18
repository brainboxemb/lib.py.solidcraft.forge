#!/usr/bin/env python3
"""Install pinned reference-library environments from toolchain.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import venv


ROOT = Path(__file__).resolve().parents[1]


def load_toolchain(path: Path = ROOT / "qualification" / "toolchain.json") -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 2:
        raise ValueError("unsupported toolchain schema")
    return data


def pip_specs(data: dict) -> list[str]:
    refs = data["references"]
    return [
        f"pythonscad=={refs['pythonscad']}",
        "git+https://github.com/pinkfish/pybosl2@"
        + refs["pybosl2"],
        f"cadquery=={refs['cadquery']}",
        f"trimesh{refs['trimesh']}",
        f"matplotlib{refs['matplotlib']}",
    ]


def install(build123d_venv: Path) -> Path:
    data = load_toolchain()
    subprocess.run(
        [sys.executable, "-m", "pip", "install", *pip_specs(data)],
        check=True,
    )
    venv.EnvBuilder(with_pip=True).create(build123d_venv)
    python = build123d_venv / "bin" / "python"
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            f"build123d=={data['references']['build123d']}",
        ],
        check=True,
    )
    return python


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build123d-venv", type=Path, required=True)
    parser.add_argument("--github-env", type=Path)
    args = parser.parse_args()
    python = install(args.build123d_venv.resolve())
    print(python)
    if args.github_env:
        with args.github_env.open("a", encoding="utf-8") as handle:
            handle.write(f"BUILD123D_PYTHON={python}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
