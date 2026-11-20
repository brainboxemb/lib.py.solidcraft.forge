"""Run Forge-owned independent reference implementations and verify their STL output."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import traceback
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
    """Export one build123d source using its isolated runtime interpreter."""

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


def export_build123d_batch(
    slugs: tuple[str, ...],
    output: Path,
) -> dict[str, str | None]:
    """Export all build123d cases in one isolated interpreter/import."""

    python = os.environ.get("BUILD123D_PYTHON", sys.executable)
    helper = ROOT / "verification" / "build123d_export.py"
    work = output / ".build123d-batch"
    work.mkdir(parents=True, exist_ok=True)
    manifest = work / "manifest.json"
    result = work / "result.json"

    rows = []
    for slug in slugs:
        target = output / slug / "build123d" / "model.stl"
        target.parent.mkdir(parents=True, exist_ok=True)
        rows.append(
            {
                "slug": slug,
                "source": str(source_path(slug, "build123d")),
                "target": str(target),
            }
        )

    manifest.write_text(
        json.dumps({"schema": 1, "cases": rows}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            python,
            str(helper),
            "--batch",
            str(manifest),
            "--result",
            str(result),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if not result.is_file():
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(
            "build123d batch did not produce structured results"
            + (f": {detail}" if detail else "")
        )

    payload = json.loads(result.read_text(encoding="utf-8"))
    errors = {
        row["slug"]: row.get("error")
        for row in payload.get("cases", [])
        if row.get("status") != "pass"
    }
    return {slug: errors.get(slug) for slug in slugs}


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


def verify_exported(
    slug: str,
    implementation: str,
    output: Path,
) -> dict[str, Any]:
    """Verify an already-exported reference STL and write case evidence."""

    target = output / slug / implementation
    stl = target / "model.stl"
    if not stl.is_file() or stl.stat().st_size == 0:
        raise RuntimeError(
            f"{slug}/{implementation}: no non-empty STL was exported"
        )
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


def write_failure(
    slug: str,
    implementation: str,
    output: Path,
    exc: Exception | str,
) -> dict[str, Any]:
    """Write structured per-case failure evidence and return it."""

    target = output / slug / implementation
    target.mkdir(parents=True, exist_ok=True)
    error = str(exc)
    result = {
        "implementation": implementation,
        "status": "fail",
        "source": str(
            source_path(slug, implementation).relative_to(ROOT)
        )
        if source_path(slug, implementation).is_file()
        else None,
        "error": error,
    }
    (target / "verification.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def verify_one(
    slug: str,
    implementation: str,
    output: Path,
) -> dict[str, Any]:
    """Export and verify one reference implementation."""

    target = output / slug / implementation
    target.mkdir(parents=True, exist_ok=True)
    export_reference(slug, implementation, target / "model.stl")
    return verify_exported(slug, implementation, output)


def selected_implementations(value: str) -> tuple[str, ...]:
    """Parse and validate one implementation selection."""

    if value.strip().lower() == "all":
        return IMPLEMENTATIONS

    selected = tuple(
        item
        for item in value.replace(",", " ").split()
        if item
    )
    if not selected:
        raise RuntimeError("at least one implementation must be selected")

    unknown = sorted(set(selected) - set(IMPLEMENTATIONS))
    if unknown:
        raise RuntimeError(
            "unknown reference implementation(s): " + ", ".join(unknown)
        )
    return selected


def selected_slugs(value: str) -> tuple[str, ...]:
    """Parse explicit cases or discover every reference contract."""

    if value.strip().lower() == "all":
        return tuple(
            path.parents[1].name
            for path in sorted(
                (ROOT / "examples").glob(
                    "*/verification/reference_geometry.json"
                )
            )
        )
    return tuple(
        item for item in value.replace(",", " ").split() if item
    )


def verify_batch(
    slugs: tuple[str, ...],
    implementations: tuple[str, ...],
    output: Path,
) -> tuple[list[dict[str, Any]], bool]:
    """Verify all cases, grouping execution by implementation."""

    by_slug: dict[str, list[dict[str, Any]]] = {
        slug: [] for slug in slugs
    }
    failed = False

    for implementation in implementations:
        build123d_errors: dict[str, str | None] | None = None
        if implementation == "build123d":
            try:
                build123d_errors = export_build123d_batch(slugs, output)
            except Exception as exc:
                build123d_errors = {slug: str(exc) for slug in slugs}

        for slug in slugs:
            try:
                if implementation == "build123d":
                    assert build123d_errors is not None
                    error = build123d_errors.get(slug)
                    if error:
                        raise RuntimeError(error)
                    result = verify_exported(slug, implementation, output)
                else:
                    result = verify_one(slug, implementation, output)
            except Exception as exc:  # continue through the complete batch
                failed = True
                result = write_failure(
                    slug,
                    implementation,
                    output,
                    "".join(
                        traceback.format_exception_only(type(exc), exc)
                    ).strip(),
                )
            by_slug[slug].append(result)

    models = []
    for slug in slugs:
        rows = by_slug[slug]
        models.append(
            {
                "model": slug,
                "status": (
                    "pass"
                    if rows and all(row["status"] == "pass" for row in rows)
                    else "fail"
                ),
                "implementations": rows,
            }
        )
    return models, failed


def main() -> int:
    """Verify explicitly selected model references."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True)
    parser.add_argument(
        "--implementations",
        default="all",
        help="all or a comma/space-separated implementation list",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()

    slugs = selected_slugs(args.cases)
    if not slugs:
        raise RuntimeError("at least one model must be selected")
    implementations = selected_implementations(args.implementations)

    args.out.mkdir(parents=True, exist_ok=True)
    models, failed = verify_batch(slugs, implementations, args.out)
    report = {
        "schema": 1,
        "source_sha": args.source_sha,
        "status": "fail" if failed else "pass",
        "models": models,
    }
    (args.out / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "reference verification: "
        + ", ".join(
            row["model"] + "=" + row["status"] for row in models
        ),
        flush=True,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
