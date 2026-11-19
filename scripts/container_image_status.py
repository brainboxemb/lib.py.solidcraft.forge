#!/usr/bin/env python3
"""Inspect one container image reference without downloading its layers.

The workflow must distinguish three states before deciding whether to build an
immutable Forge runtime image:

- present: the registry manifest exists;
- absent: the registry explicitly reports that the manifest/tag is unknown;
- error: authentication, network, timeout or another lookup failure.

Only the explicit absent state is allowed to trigger a local image build.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


ABSENT_MARKERS = (
    "manifest unknown",
    "no such manifest",
    "manifest_unknown",
)


class ImageLookupError(RuntimeError):
    """Raised when registry lookup failed without proving image absence."""


def inspect(reference: str) -> bool:
    """Return True when the reference exists and False only for explicit absence."""

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


def write_github_output(path: Path, *, exists: bool) -> None:
    """Write the explicit image-presence result for GitHub Actions."""

    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"exists={'true' if exists else 'false'}\n")


def main() -> int:
    """Inspect one immutable image reference and expose its explicit state."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    exists = inspect(args.reference)
    print("present" if exists else "absent")
    if args.github_output:
        write_github_output(args.github_output, exists=exists)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
