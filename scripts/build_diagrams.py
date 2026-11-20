#!/usr/bin/env python3
"""Render the versioned Forge CADCraft verification diagrams."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "verification" / "diagrams" / "sources"
CADCRAFT_VERSION = "0.20.1"


def _sha256(path: Path) -> str:
    """Return one file SHA-256."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_output_root() -> Path:
    """Return the CAD-CI diagram output directory."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required when --out is omitted")
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


def cadcraft_cli() -> tuple[Path, str]:
    """Return CADCraft supplied by the released reference runtime."""

    value = shutil.which("cadcraft-cli")
    if not value:
        raise RuntimeError(
            "cadcraft-cli is required from the released reference runtime"
        )
    binary = Path(value).resolve()
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


def render_all(output: Path) -> int:
    """Render every versioned diagram and write structured provenance."""

    sources = sorted(SOURCE_ROOT.glob("*.cadcraft.json"))
    if not sources:
        raise RuntimeError(f"no CADCraft diagram sources found: {SOURCE_ROOT}")

    output = output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    binary, cli_version = cadcraft_cli()
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


def main() -> int:
    """Render diagrams using CADCraft from the released reference runtime."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    return render_all(args.out or default_output_root())


if __name__ == "__main__":
    raise SystemExit(main())
