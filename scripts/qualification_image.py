#!/usr/bin/env python3
"""Calculate immutable qualification-image metadata from versioned inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
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

    namespace: dict[str, object] = {}
    exec(VERSION_FILE.read_text(encoding="utf-8"), namespace)
    solidcraft = str(namespace["TESTED_SOLIDCRAFT_VERSION"])
    digest = image_id()
    image = f"ghcr.io/{repository.lower()}/qualification"
    return {
        "image": image,
        "image_id": digest,
        "tag": f"toolchain-{digest}",
        "reference": f"{image}:toolchain-{digest}",
        "alias": (
            f"{image}:sc-{solidcraft}-py-{python_version}"
        ),
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


def resolve_cached_image(reference: str, image_id: str) -> dict[str, str]:
    """Pull an existing immutable image, or identify a genuinely missing one.

    A slow or transiently failing registry request is not the same as a cache
    miss. Only an explicit not-found response allows CI to rebuild the image.
    """

    completed = subprocess.run(
        ["docker", "pull", reference],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="")

    if completed.returncode == 0:
        return {
            "exists": "true",
            "run_image": reference,
        }

    detail = f"{completed.stdout}\n{completed.stderr}".lower()
    missing_markers = (
        "manifest unknown",
        "no such manifest",
        "not found",
    )
    if any(marker in detail for marker in missing_markers):
        return {
            "exists": "false",
            "run_image": f"qualification-local:{image_id}",
        }

    raise RuntimeError(
        f"could not resolve qualification image {reference!r}; "
        "registry failure is not treated as a cache miss"
    )


def write_github_output(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository")
    parser.add_argument("--resolve-cache", action="store_true")
    parser.add_argument("--reference")
    parser.add_argument("--image-id")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    if args.resolve_cache:
        if not args.reference or not args.image_id:
            parser.error("--resolve-cache requires --reference and --image-id")
        values = resolve_cached_image(args.reference, args.image_id)
    else:
        if not args.repository:
            parser.error("--repository is required unless --resolve-cache is used")
        values = metadata(args.repository)

    for key, value in values.items():
        print(f"{key}={value}")
    if args.github_output:
        write_github_output(args.github_output, values)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
