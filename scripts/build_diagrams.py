#!/usr/bin/env python3
"""Render the versioned Forge CADCraft verification diagrams."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "verification" / "diagrams" / "sources"

CADCRAFT_VERSION = "0.20.1"
CADCRAFT_ARCH = "x86_64"
CADCRAFT_ARCHIVE_SHA256 = (
    "57b6f1b41b4f3c542a82f103202ed1a779440e5ff8d25c08ef66abda1a8cb1b9"
)
CADCRAFT_ARCHIVE = (
    f"cadcraft-{CADCRAFT_VERSION}-linux-{CADCRAFT_ARCH}.tar.gz"
)
CADCRAFT_URL = (
    "https://github.com/storytold/cadcraft/releases/download/"
    f"v{CADCRAFT_VERSION}/{CADCRAFT_ARCHIVE}"
)
CADCRAFT_MEMBER = (
    f"cadcraft-{CADCRAFT_VERSION}-linux-{CADCRAFT_ARCH}/bin/cadcraft-cli"
)


def _sha256(path: Path) -> str:
    """Return one file SHA-256."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def output_root() -> Path:
    """Return this CAD-CI item's diagram output directory."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    return Path(value).resolve() / "diagrams"


def load_source(path: Path) -> dict[str, Any]:
    """Load and validate one versioned CADCraft diagram source."""

    path = Path(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"diagram source must contain one object: {path}")
    if value.get("cadcraft_version") != CADCRAFT_VERSION:
        raise ValueError(
            f"diagram source must declare CADCraft {CADCRAFT_VERSION}: {path}"
        )
    title = value.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"diagram source requires a title: {path}")

    commands = value.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ValueError(f"diagram source requires commands: {path}")
    for index, row in enumerate(commands):
        if not isinstance(row, dict):
            raise ValueError(f"commands[{index}] must be an object: {path}")
        command = row.get("command")
        params = row.get("params")
        if not isinstance(command, str) or not command.strip():
            raise ValueError(f"commands[{index}] requires command text: {path}")
        if not isinstance(params, dict):
            raise ValueError(f"commands[{index}] requires params: {path}")
    return value


def command_arguments(source: dict[str, Any]) -> list[str]:
    """Return the historical repeated --cmd arguments for one source."""

    result: list[str] = []
    for row in source["commands"]:
        result.extend(
            [
                "--cmd",
                row["command"]
                + " "
                + json.dumps(row["params"], separators=(",", ":")),
            ]
        )
    return result


def ensure_cadcraft() -> tuple[Path, str]:
    """Return the exact verified CADCraft CLI and its reported version."""

    cache_root = Path(
        os.environ.get(
            "CADCRAFT_CACHE_DIR",
            str(ROOT / ".cache" / "cadcraft"),
        )
    ).resolve()
    install_root = (
        cache_root / f"{CADCRAFT_VERSION}-linux-{CADCRAFT_ARCH}"
    )
    binary = install_root / "cadcraft-cli"

    if not binary.is_file():
        install_root.mkdir(parents=True, exist_ok=True)
        temp_root = Path(
            os.environ.get("RUNNER_TEMP", str(cache_root / "tmp"))
        ).resolve()
        temp_root.mkdir(parents=True, exist_ok=True)
        archive = temp_root / CADCRAFT_ARCHIVE

        subprocess.run(
            [
                "curl",
                "--proto",
                "=https",
                "-fsSL",
                CADCRAFT_URL,
                "-o",
                str(archive),
            ],
            check=True,
        )
        actual = _sha256(archive)
        if actual != CADCRAFT_ARCHIVE_SHA256:
            raise RuntimeError(
                "CADCraft archive SHA-256 mismatch: "
                f"expected {CADCRAFT_ARCHIVE_SHA256}, got {actual}"
            )

        with tarfile.open(archive, "r:gz") as tar:
            member = tar.getmember(CADCRAFT_MEMBER)
            source = tar.extractfile(member)
            if source is None:
                raise RuntimeError(
                    f"CADCraft archive is missing {CADCRAFT_MEMBER}"
                )
            with binary.open("wb") as target:
                shutil.copyfileobj(source, target)

        binary.chmod(
            binary.stat().st_mode
            | stat.S_IXUSR
            | stat.S_IXGRP
            | stat.S_IXOTH
        )

    version = subprocess.check_output(
        [str(binary), "--version"],
        text=True,
    ).strip()
    if CADCRAFT_VERSION not in version:
        raise RuntimeError(
            f"unexpected CADCraft CLI version: {version!r}"
        )
    return binary, version


def render_source(
    binary: Path,
    source_path: Path,
    output: Path,
) -> dict[str, Any]:
    """Render one source and return provenance for its artifacts."""

    source = load_source(source_path)
    name = source_path.name.removesuffix(".cadcraft.json")

    source_out = output / "sources" / source_path.name
    rendered = output / "rendered"
    rendered.mkdir(parents=True, exist_ok=True)
    source_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, source_out)

    dxf = rendered / f"{name}.dxf"
    svg = rendered / f"{name}.svg"

    args = [str(binary), "run", "--metric"]
    args.extend(command_arguments(source))
    args.extend(
        [
            "--save",
            str(dxf),
            "--export",
            str(svg),
            "--view",
            "extents",
        ]
    )

    env = os.environ.copy()
    env["CADCRAFT_CONFIG_DIR"] = ""
    subprocess.run(args, check=True, env=env)

    for artifact in (dxf, svg):
        if not artifact.is_file() or artifact.stat().st_size == 0:
            raise RuntimeError(
                f"CADCraft did not create a non-empty artifact: {artifact}"
            )
    if "<svg" not in svg.read_text(encoding="utf-8", errors="replace"):
        raise RuntimeError(f"CADCraft SVG is not valid SVG evidence: {svg}")

    return {
        "name": name,
        "title": source["title"],
        "command_count": len(source["commands"]),
        "source": f"sources/{source_path.name}",
        "source_sha256": _sha256(source_out),
        "dxf": f"rendered/{dxf.name}",
        "dxf_sha256": _sha256(dxf),
        "svg": f"rendered/{svg.name}",
        "svg_sha256": _sha256(svg),
    }


def main() -> int:
    """Render every versioned diagram and write structured provenance."""

    sources = sorted(SOURCE_ROOT.glob("*.cadcraft.json"))
    if not sources:
        raise RuntimeError(f"no CADCraft diagram sources found: {SOURCE_ROOT}")

    output = output_root()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    binary, cli_version = ensure_cadcraft()
    diagrams = []
    failed = False
    for source_path in sources:
        try:
            row = render_source(binary, source_path, output)
            row["status"] = "pass"
        except Exception as exc:  # keep later diagrams observable
            failed = True
            row = {
                "name": source_path.name.removesuffix(".cadcraft.json"),
                "status": "fail",
                "error": f"{type(exc).__name__}: {exc}",
            }
            print(
                f"CADCraft diagram failed: {source_path.name}: {exc}",
                flush=True,
            )
        diagrams.append(row)

    provenance = {
        "schema": "forge-verification-diagrams",
        "schema_version": 1,
        "status": "fail" if failed else "pass",
        "cadcraft_version": CADCRAFT_VERSION,
        "cadcraft_cli_version": cli_version,
        "archive": CADCRAFT_ARCHIVE,
        "archive_sha256": CADCRAFT_ARCHIVE_SHA256,
        "source_count": len(diagrams),
        "diagrams": diagrams,
    }
    (output / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    passed = sum(row.get("status") == "pass" for row in diagrams)
    print(
        f"diagram verification: {passed}/{len(diagrams)} passed "
        f"with CADCraft {CADCRAFT_VERSION}",
        flush=True,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
