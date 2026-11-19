#!/usr/bin/env python3
"""Build-time metadata and registry checks for the immutable Forge runtime.

The runtime contains SolidCraft plus the pinned reference, visual and diagram
toolchain used by Forge verification. This script belongs to runtime
build/publication. Normal Forge CI receives its expected immutable image through
root cad-ci.yml instead of resolving it here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "docker" / "solidcraft_runtime"
DOCKERFILE = RUNTIME_DIR / "Dockerfile"
CONFIG = RUNTIME_DIR / "runtime.json"
VERSION_FILE = ROOT / "scpf" / "scpf" / "version.py"

ABSENT_MARKERS = (
    "manifest unknown",
    "no such manifest",
    "manifest_unknown",
)

REQUIRED_CONFIG_FIELDS = {
    "python_image",
    "cadcraft_version",
    "cadcraft_sha256",
    "pythonscad_version",
    "pybosl2_commit",
    "cadquery_version",
    "build123d_version",
    "pillow_spec",
    "trimesh_spec",
    "scipy_spec",
}


class ImageLookupError(RuntimeError):
    """Registry lookup failed without proving that the image is absent."""


def load_config() -> dict:
    """Load and validate every versioned runtime input."""

    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported verification runtime schema")
    missing = sorted(REQUIRED_CONFIG_FIELDS - set(data))
    if missing:
        raise ValueError(
            "missing verification runtime fields: " + ", ".join(missing)
        )
    return data


def solidcraft_version() -> str:
    """Read the tested SolidCraft version from Forge's source of truth."""

    namespace: dict[str, object] = {}
    exec(VERSION_FILE.read_text(encoding="utf-8"), namespace)
    return str(namespace["TESTED_SOLIDCRAFT_VERSION"])


def image_id() -> str:
    """Hash every versioned input that changes the runtime image."""

    digest = hashlib.sha256()
    for path in (DOCKERFILE, CONFIG, VERSION_FILE):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def metadata(repository: str) -> dict[str, str]:
    """Return immutable runtime metadata for one Forge repository."""

    config = load_config()
    digest = image_id()
    image = f"ghcr.io/{repository.lower()}/solidcraft-runtime"
    reference = f"{image}:runtime-{digest}"

    values = {
        "image": image,
        "image_id": digest,
        "reference": reference,
        "solidcraft_version": solidcraft_version(),
    }
    values.update(
        {
            key: str(value)
            for key, value in config.items()
            if key != "schema"
        }
    )
    return values


def image_exists(reference: str) -> bool:
    """Return False only when the registry explicitly reports absence."""

    completed = subprocess.run(
        ["docker", "manifest", "inspect", reference],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode == 0:
        return True

    message = (
        completed.stderr.strip()
        or completed.stdout.strip()
        or "docker manifest inspect failed"
    )
    normalized = message.lower()
    if any(marker in normalized for marker in ABSENT_MARKERS):
        return False

    raise ImageLookupError(
        f"could not inspect container image {reference}: {message}"
    )


def require_image(reference: str) -> None:
    """Fail clearly when the immutable runtime image has not been published."""

    if image_exists(reference):
        print(f"present: {reference}")
        return

    raise RuntimeError(
        "required Forge verification runtime image is missing: "
        f"{reference}. Run the 'SolidCraft runtime' workflow first."
    )


def write_github_output(path: Path, values: dict[str, str]) -> None:
    """Append scalar outputs to a GitHub Actions output file."""

    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    """Expose runtime metadata, status, or a strict presence check."""

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    metadata_parser = commands.add_parser("metadata")
    metadata_parser.add_argument("--repository", required=True)
    metadata_parser.add_argument("--github-output", type=Path)

    status_parser = commands.add_parser("status")
    status_parser.add_argument("--reference", required=True)
    status_parser.add_argument("--github-output", type=Path)

    require_parser = commands.add_parser("require")
    require_parser.add_argument("--reference", required=True)

    args = parser.parse_args()

    try:
        if args.command == "metadata":
            values = metadata(args.repository)
            for key, value in values.items():
                print(f"{key}={value}")
            if args.github_output:
                write_github_output(args.github_output, values)
            return 0

        if args.command == "require":
            require_image(args.reference)
            return 0

        exists = image_exists(args.reference)
        value = "true" if exists else "false"
        print("present" if exists else "absent")
        if args.github_output:
            write_github_output(args.github_output, {"exists": value})
        return 0
    except (ImageLookupError, OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
