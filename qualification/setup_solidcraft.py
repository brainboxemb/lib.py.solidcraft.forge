#!/usr/bin/env python3
"""Install the checksum-verified SolidCraft release used by Forge qualification."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import tarfile
import urllib.request

from scpf.version import TESTED_SOLIDCRAFT_VERSION


def checksum_for(text: str, archive: str) -> str:
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == archive:
            value = parts[0].lower()
            if len(value) == 64 and all(ch in "0123456789abcdef" for ch in value):
                return value
    raise ValueError(f"checksum not found for {archive}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def install(destination: Path) -> Path:
    version = TESTED_SOLIDCRAFT_VERSION
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    archive = f"solidcraft-{version}-linux-x86_64.tar.gz"
    base = (
        "https://github.com/tangency-labs/solidcraft/releases/download/"
        f"v{version}"
    )
    sums_path = destination / "SHA256SUMS.txt"
    archive_path = destination / archive
    urllib.request.urlretrieve(f"{base}/SHA256SUMS.txt", sums_path)
    urllib.request.urlretrieve(f"{base}/{archive}", archive_path)

    expected = checksum_for(sums_path.read_text(encoding="utf-8"), archive)
    actual = sha256(archive_path)
    if actual != expected:
        raise RuntimeError(
            f"SolidCraft checksum mismatch: expected {expected}, got {actual}"
        )

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(destination, filter="data")
    bin_dir = (
        destination
        / f"solidcraft-{version}-linux-x86_64"
        / "bin"
    )
    if not (bin_dir / "solidcraft-cli").is_file():
        raise RuntimeError(f"SolidCraft CLI not found after extraction: {bin_dir}")
    return bin_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--github-path", type=Path)
    args = parser.parse_args()
    bin_dir = install(args.destination)
    print(bin_dir)
    if args.github_path:
        with args.github_path.open("a", encoding="utf-8") as handle:
            handle.write(str(bin_dir) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
