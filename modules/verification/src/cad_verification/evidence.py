"""Validation and deterministic hashing of verification artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import ArtifactError


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of one regular file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(path: Path, root: Path) -> tuple[Path, Path]:
    """Resolve one artifact and prove that it belongs to the output root."""

    root = root.resolve()
    candidate = path if path.is_absolute() else root / path

    # Check the authored path before resolving it. Otherwise an in-tree symlink
    # to another in-tree file would be indistinguishable from the real file.
    if candidate.is_symlink():
        raise ArtifactError(f"symlink artifact is not supported: {path}")

    candidate = candidate.resolve()

    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ArtifactError(
            f"artifact escapes verification output directory: {path}"
        ) from exc

    if relative.as_posix() == "verification.json":
        raise ArtifactError(
            "verification.json is owned by the verification library"
        )

    return candidate, relative


def _directory_digest(path: Path) -> tuple[str, int]:
    """Hash lexical directory membership, empty directories and file bytes."""

    records: list[dict[str, Any]] = []
    entries = 0

    for child in sorted(path.rglob("*"), key=lambda value: value.as_posix()):
        if child.is_symlink():
            raise ArtifactError(f"symlink artifact is not supported: {child}")

        relative = child.relative_to(path).as_posix()
        if child.is_dir():
            records.append({"kind": "directory", "path": relative})
            entries += 1
        elif child.is_file():
            records.append(
                {
                    "kind": "file",
                    "path": relative,
                    "size": child.stat().st_size,
                    "sha256": _sha256(child),
                }
            )
            entries += 1
        else:
            raise ArtifactError(f"unsupported artifact entry: {child}")

    payload = json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest(), entries


def artifact_record(path: Path, output_dir: Path) -> dict[str, Any]:
    """Return deterministic evidence for one declared verification artifact."""

    candidate, relative = _safe_relative(path, output_dir)

    if not candidate.exists():
        raise ArtifactError(f"declared artifact does not exist: {relative}")
    if candidate.is_symlink():
        raise ArtifactError(f"symlink artifact is not supported: {relative}")

    if candidate.is_file():
        return {
            "path": relative.as_posix(),
            "kind": "file",
            "size": candidate.stat().st_size,
            "sha256": _sha256(candidate),
        }

    if candidate.is_dir():
        digest, entries = _directory_digest(candidate)
        return {
            "path": relative.as_posix(),
            "kind": "directory",
            "entries": entries,
            "sha256": digest,
        }

    raise ArtifactError(f"unsupported artifact type: {relative}")
