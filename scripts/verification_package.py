#!/usr/bin/env python3
"""Build one exact released CAD-verification wheel for CAD-CI consumers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "ci" / "cad-verification-package" / "package.json"
WHEEL_PREFIX = "brainboxemb_cad_verification_lib-"


def output_root() -> Path:
    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    path = Path(value).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_config() -> dict:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise RuntimeError("unsupported verification package config schema")
    for key in ("repository", "version", "commit"):
        value = data.get(key)
        if not isinstance(value, str) or not value:
            raise RuntimeError(f"verification package config requires {key}")
    return data


def wheel_version(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/METADATA")
        ]
        if len(candidates) != 1:
            raise RuntimeError(
                f"expected one wheel METADATA file, found {len(candidates)}"
            )
        text = archive.read(candidates[0]).decode("utf-8")
    for line in text.splitlines():
        if line.startswith("Version: "):
            return line.removeprefix("Version: ").strip()
    raise RuntimeError("wheel metadata has no Version field")


def main() -> int:
    config = read_config()
    out = output_root()
    dist = out / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    url = (
        f"https://github.com/{config['repository']}/archive/"
        f"{config['commit']}.zip"
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(dist),
            url,
        ],
        check=True,
    )

    wheels = tuple(sorted(dist.glob(f"{WHEEL_PREFIX}*.whl")))
    if len(wheels) != 1:
        raise RuntimeError(
            f"expected one CAD-verification wheel, found {len(wheels)}"
        )
    wheel = wheels[0]
    actual_version = wheel_version(wheel)
    if actual_version != config["version"]:
        raise RuntimeError(
            "CAD-verification wheel version mismatch: "
            f"expected {config['version']}, got {actual_version}"
        )

    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    provenance = {
        "schema": 1,
        "repository": config["repository"],
        "version": config["version"],
        "commit": config["commit"],
        "source_url": url,
        "wheel": wheel.name,
        "sha256": digest,
    }
    (out / "package.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "CAD verification package: "
        f"{config['version']} {config['commit']} {wheel.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
