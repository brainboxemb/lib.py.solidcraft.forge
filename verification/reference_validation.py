"""Run Forge-owned independent reference implementations and verify their STL output."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from typing import Any

from cad_verification import (
    GeometryContract,
    SurfaceDistanceProbe,
    VerificationFailure,
    validate_mesh_geometry,
)


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATIONS = ("pythonscad", "pybosl2", "cadquery", "build123d")


def load_contract(slug: str) -> GeometryContract:
    """Load one model-local reference geometry contract."""

    path = ROOT / "examples" / slug / "verification" / "reference_geometry.json"
    if not path.is_file():
        raise RuntimeError(f"{slug}: missing local reference contract: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise RuntimeError(f"{slug}: unsupported reference contract schema")
    probes = tuple(
        SurfaceDistanceProbe(
            label=row["label"],
            point=tuple(row["point"]),
            distance_mm=row["distance_mm"],
            tolerance_mm=row["tolerance_mm"],
        )
        for row in data.get("surface_distance_probes", [])
    )
    return GeometryContract(
        bounds_min=tuple(data["bounds_min"]),
        bounds_max=tuple(data["bounds_max"]),
        bounds_tolerance_mm=data["bounds_tolerance_mm"],
        volume_mm3=data.get("volume_mm3"),
        volume_tolerance_mm3=data.get("volume_tolerance_mm3"),
        watertight=data.get("watertight"),
        bounds_sufficient=data.get("bounds_sufficient", True),
        surface_distance_probes=probes,
    )


def source_path(slug: str, implementation: str) -> Path:
    """Return one required reference source."""

    path = ROOT / "examples" / slug / implementation / "model.py"
    if not path.is_file():
        raise RuntimeError(
            f"{slug}: missing {implementation} reference source: {path}"
        )
    return path


def load_reference(path: Path):
    """Execute one reference source and return its exported model object."""

    namespace = runpy.run_path(str(path))
    if "model" not in namespace:
        raise RuntimeError(f"{path} must expose final geometry as model")
    return namespace["model"]


def export_build123d(source: Path, target: Path) -> None:
    """Export build123d using its isolated runtime interpreter."""

    python = os.environ.get("BUILD123D_PYTHON", sys.executable)
    helper = ROOT / "verification" / "build123d_export.py"
    completed = subprocess.run(
        [python, str(helper), str(source), str(target)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(
            f"build123d export failed with status "
            f"{completed.returncode}: {detail}"
        )


def export_reference(
    slug: str,
    implementation: str,
    target: Path,
) -> None:
    """Run one independent implementation and export one STL."""

    source = source_path(slug, implementation)
    target.parent.mkdir(parents=True, exist_ok=True)

    if implementation == "build123d":
        export_build123d(source, target)
    else:
        model = load_reference(source)
        export = getattr(model, "export", None)
        if not callable(export):
            raise RuntimeError(
                f"{slug}/{implementation}: model has no export() method"
            )
        if implementation == "cadquery":
            export(str(target), exportType="STL")
        else:
            exported = export(str(target))
            if not target.is_file() and exported is not None:
                candidate = Path(exported)
                if candidate.is_file():
                    target.write_bytes(candidate.read_bytes())

    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError(
            f"{slug}/{implementation}: no non-empty STL was exported"
        )


def verify_one(
    slug: str,
    implementation: str,
    output: Path,
) -> dict[str, Any]:
    """Export and verify one reference implementation."""

    target = output / slug / implementation
    target.mkdir(parents=True, exist_ok=True)
    stl = target / "model.stl"
    export_reference(slug, implementation, stl)
    try:
        evidence = validate_mesh_geometry(stl, load_contract(slug))
    except VerificationFailure as exc:
        raise RuntimeError(
            f"{slug}/{implementation}: reference geometry failed: {exc}"
        ) from exc

    result = {
        "implementation": implementation,
        "status": "pass",
        "source": str(
            source_path(slug, implementation).relative_to(ROOT)
        ),
        "stl": str(stl.relative_to(output)),
        "geometry": evidence,
    }
    (target / "verification.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def verify_model(
    slug: str,
    output: Path,
) -> dict[str, Any]:
    """Verify all four required independent implementations."""

    results = [
        verify_one(slug, implementation, output)
        for implementation in IMPLEMENTATIONS
    ]
    return {
        "model": slug,
        "status": "pass",
        "implementations": results,
    }


def main() -> int:
    """Verify explicitly selected model references."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()

    if args.cases.strip().lower() == "all":
        slugs = tuple(
            path.parents[1].name
            for path in sorted(
                (ROOT / "examples").glob(
                    "*/verification/reference_geometry.json"
                )
            )
        )
    else:
        slugs = tuple(
            value
            for value in args.cases.replace(",", " ").split()
            if value
        )
    if not slugs:
        raise RuntimeError("at least one model must be selected")

    args.out.mkdir(parents=True, exist_ok=True)
    models = [verify_model(slug, args.out) for slug in slugs]
    report = {
        "schema": 1,
        "source_sha": args.source_sha,
        "status": "pass",
        "models": models,
    }
    (args.out / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "reference verification: "
        + ", ".join(slug + "=pass" for slug in slugs)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
