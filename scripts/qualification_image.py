#!/usr/bin/env python3
"""Resolve the immutable qualification-container identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "docker" / "qualification" / "Dockerfile"
TOOLCHAIN = ROOT / "qualification" / "toolchain.json"
VERSION_FILE = ROOT / "scpf" / "scpf" / "version.py"


def load_toolchain() -> dict:
    data = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))
    if data.get("schema") != 2:
        raise ValueError("unsupported qualification toolchain schema")
    required = {"python_image", "cadcraft", "references"}
    missing = sorted(required - set(data))
    if missing:
        raise ValueError("missing toolchain fields: " + ", ".join(missing))
    return data


def tested_solidcraft_version() -> str:
    namespace: dict[str, object] = {}
    exec(VERSION_FILE.read_text(encoding="utf-8"), namespace)
    return str(namespace["TESTED_SOLIDCRAFT_VERSION"])


def image_id() -> str:
    digest = hashlib.sha256()
    for path in (DOCKERFILE, TOOLCHAIN, VERSION_FILE):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def metadata(repository: str) -> dict[str, str]:
    data = load_toolchain()
    refs = data["references"]
    cadcraft = data["cadcraft"]
    if not isinstance(cadcraft, dict):
        raise ValueError("cadcraft toolchain entry must be an object")
    missing_cadcraft = sorted({"version", "sha256"} - set(cadcraft))
    if missing_cadcraft:
        raise ValueError(
            "missing cadcraft toolchain fields: " + ", ".join(missing_cadcraft)
        )

    match = re.search(r"python:(\d+\.\d+)", data["python_image"])
    if match is None:
        raise ValueError(
            "python_image must contain a major.minor Python tag"
        )
    python_version = match.group(1)
    solidcraft = tested_solidcraft_version()
    digest = image_id()
    image = f"ghcr.io/{repository.lower()}/qualification"

    return {
        "image": image,
        "image_id": digest,
        "reference": f"{image}:toolchain-{digest}",
        "alias": f"{image}:sc-{solidcraft}-py-{python_version}",
        "python": python_version,
        "python_image": data["python_image"],
        "solidcraft": solidcraft,
        "cadcraft": str(cadcraft["version"]),
        "cadcraft_sha256": str(cadcraft["sha256"]),
        "pythonscad": refs["pythonscad"],
        "pybosl2": refs["pybosl2"],
        "cadquery": refs["cadquery"],
        "build123d": refs["build123d"],
        "trimesh": refs["trimesh"],
        "matplotlib": refs["matplotlib"],
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    values = metadata(args.repository)
    for key, value in values.items():
        print(f"{key}={value}")
    if args.github_output:
        write_github_output(args.github_output, values)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
