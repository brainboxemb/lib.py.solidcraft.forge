"""Verify independent PythonSCAD, pyBOSL2, CadQuery and build123d references.

Each reference source must expose a final 3-D object as model. The verifier\nexports that object with the reference library itself, checks the resulting STL\nagainst the independent Forge geometry contract and renders fixed comparison\nviews from that STL.
"""

from __future__ import annotations

import argparse
import json
import os
import runpy
import subprocess
import sys

import yaml
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verification.geometry_contracts import geometry_contract

DEFAULT_REFERENCE_IMPLEMENTATIONS = (
    "pythonscad",
    "pybosl2",
    "cadquery",
    "build123d",
)
VIEWS = {
    "front": (0, -90),
    "right": (0, 0),
    "iso": (28, -45),
}


def expected_envelope(slug: str) -> tuple[np.ndarray, np.ndarray]:
    boxes = geometry_contract(slug)["bounds"]
    lo = np.min(np.asarray([row["min"] for row in boxes], dtype=float), axis=0)
    hi = np.max(np.asarray([row["max"] for row in boxes], dtype=float), axis=0)
    return lo, hi


def load_reference(path: Path):
    namespace = runpy.run_path(str(path))
    if "model" not in namespace:
        raise RuntimeError(f"{path} must expose final geometry as model")
    return namespace["model"]


def supported_model_slugs() -> tuple[str, ...]:
    """Discover the current model-verification catalog from item ownership."""

    slugs = []
    for config_path in sorted((ROOT / "examples").glob("*/ci.yml")):
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("kind") != "model":
            continue
        slug = data.get("id")
        if not isinstance(slug, str) or not slug:
            raise RuntimeError(f"invalid model item id: {config_path}")
        if config_path.parent.name != slug:
            raise RuntimeError(
                f"model item id/path mismatch: {config_path.parent.name} != {slug}"
            )
        slugs.append(slug)
    if not slugs:
        raise RuntimeError("no model verification items discovered")
    return tuple(slugs)


def parse_case_selection(value: str) -> tuple[str, ...]:
    """Parse 'all' or a comma/space-separated model list."""

    available = supported_model_slugs()
    if value.strip().lower() == "all":
        return available

    requested = tuple(
        token
        for token in value.replace(",", " ").split()
        if token
    )
    unknown = sorted(set(requested) - set(available))
    if unknown:
        raise ValueError("unknown model(s): " + ", ".join(unknown))
    return requested


def implementations_for(slug: str) -> tuple[str, ...]:
    """Require the four historical independent reference implementations."""

    missing = [
        implementation
        for implementation in DEFAULT_REFERENCE_IMPLEMENTATIONS
        if not (
            ROOT
            / "examples"
            / slug
            / implementation
            / "model.py"
        ).is_file()
    ]
    if missing:
        raise RuntimeError(
            f"{slug}: missing reference implementation(s): "
            + ", ".join(missing)
        )
    return DEFAULT_REFERENCE_IMPLEMENTATIONS


def export_build123d_reference(source: Path, stl: Path):
    """Run build123d in its isolated environment and export one STL."""
    python = os.environ.get("BUILD123D_PYTHON", sys.executable)
    helper = ROOT / "verification" / "build123d_export.py"
    completed = subprocess.run(
        [python, str(helper), str(source), str(stl)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(
            f"build123d export failed with exit {completed.returncode}: {detail}"
        )
    return None


def export_reference(model, implementation: str, stl: Path):
    if implementation == "cadquery":
        export = getattr(model, "export", None)
        if not callable(export):
            raise RuntimeError("CadQuery reference model must expose export()")
        export(str(stl), exportType="STL")
        return None

    export = getattr(model, "export", None)
    if not callable(export):
        raise RuntimeError(
            f"{implementation} reference model has no export() method"
        )
    return export(str(stl))


def render_mesh(mesh: trimesh.Trimesh, path: Path, view: str) -> None:
    elev, azim = VIEWS[view]
    triangles = np.asarray(mesh.triangles)
    if len(triangles) > 60000:
        step = max(1, len(triangles) // 60000)
        triangles = triangles[::step]

    fig = plt.figure(figsize=(7.2, 5.4), dpi=100)
    ax = fig.add_subplot(111, projection="3d")
    collection = Poly3DCollection(
        triangles,
        linewidths=0.08,
        edgecolors=(0.15, 0.15, 0.15, 0.45),
        facecolors=(0.72, 0.76, 0.82, 1.0),
    )
    ax.add_collection3d(collection)

    lo, hi = mesh.bounds
    center = (lo + hi) / 2.0
    span = max(float(np.max(hi - lo)), 1.0)
    radius = span * 0.62
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.tight_layout(pad=0)
    fig.savefig(path, transparent=False)
    plt.close(fig)


def validate_one(slug: str, implementation: str, out: Path, tolerance: float) -> dict:
    source = ROOT / "examples" / slug / implementation / "model.py"
    target = out / slug / implementation
    target.mkdir(parents=True, exist_ok=True)
    stl = target / "model.stl"

    if implementation == "build123d":
        exported = export_build123d_reference(source, stl)
    else:
        model = load_reference(source)
        exported = export_reference(model, implementation, stl)
    if not stl.is_file() and exported is not None:
        candidate = Path(exported)
        if candidate.is_file():
            stl = candidate
    if not stl.is_file() or stl.stat().st_size == 0:
        raise RuntimeError(f"{implementation} did not export a non-empty STL for {slug}")

    loaded = trimesh.load_mesh(stl, process=True)
    if isinstance(loaded, trimesh.Scene):
        mesh = loaded.dump(concatenate=True)
    else:
        mesh = loaded
    if not isinstance(mesh, trimesh.Trimesh) or mesh.vertices.size == 0:
        raise RuntimeError(f"{implementation} exported no measurable mesh for {slug}")

    expected_min, expected_max = expected_envelope(slug)
    actual_min, actual_max = np.asarray(mesh.bounds[0]), np.asarray(mesh.bounds[1])
    delta = np.maximum(np.abs(actual_min - expected_min), np.abs(actual_max - expected_max))
    checks = {
        "bounds": {
            "status": "pass" if np.all(delta <= tolerance) else "fail",
            "actual": {"min": actual_min.tolist(), "max": actual_max.tolist()},
            "expected": {"min": expected_min.tolist(), "max": expected_max.tolist()},
            "max_delta_mm": float(np.max(delta)),
            "tolerance_mm": tolerance,
        }
    }

    contract = geometry_contract(slug)
    if not contract["bounds_sufficient"] and not (
        "volume_mm3" in contract or contract.get("surface_distance_probes")
    ):
        raise RuntimeError(
            f"{slug}: bounds are declared insufficient but no detailed geometry check exists"
        )
    if contract:
        expected_watertight = contract.get("watertight")
        if expected_watertight is not None:
            # STL commonly duplicates vertices and may contain duplicate
            # or degenerate facets at Boolean seams. Normalize only a copy used
            # for the topology check; bounds, volume and probes still use the
            # original exported mesh.
            topology_mesh = mesh.copy()
            topology_mesh.process(validate=True)
            actual_watertight = bool(topology_mesh.is_watertight)
            checks["watertight"] = {
                "status": (
                    "pass"
                    if actual_watertight == expected_watertight
                    else "fail"
                ),
                "actual": actual_watertight,
                "expected": bool(expected_watertight),
            }

        if "volume_mm3" in contract:
            actual_volume = abs(float(mesh.volume))
            expected_volume = float(contract["volume_mm3"])
            volume_tolerance = float(contract.get("volume_tolerance_mm3", 1.0))
            checks["volume"] = {
                "status": (
                    "pass"
                    if abs(actual_volume - expected_volume) <= volume_tolerance
                    else "fail"
                ),
                "actual_mm3": actual_volume,
                "expected_mm3": expected_volume,
                "delta_mm3": abs(actual_volume - expected_volume),
                "tolerance_mm3": volume_tolerance,
            }

        probes = contract.get("surface_distance_probes", [])
        if probes:
            probe_points = np.asarray([probe["point"] for probe in probes], dtype=float)
            _, probe_distances, _ = trimesh.proximity.closest_point_naive(
                mesh, probe_points
            )
            probe_rows = []
            probes_pass = True
            for probe, actual_distance in zip(probes, probe_distances):
                expected_distance = float(probe["distance_mm"])
                probe_tolerance = float(probe.get("tolerance_mm", tolerance))
                delta_distance = abs(float(actual_distance) - expected_distance)
                passed = delta_distance <= probe_tolerance
                probes_pass = probes_pass and passed
                probe_rows.append({
                    "label": probe["label"],
                    "point": probe["point"],
                    "actual_mm": float(actual_distance),
                    "expected_mm": expected_distance,
                    "delta_mm": delta_distance,
                    "tolerance_mm": probe_tolerance,
                    "status": "pass" if passed else "fail",
                })
            checks["surface_distance_probes"] = {
                "status": "pass" if probes_pass else "fail",
                "probes": probe_rows,
            }

    status = (
        "pass"
        if all(check["status"] == "pass" for check in checks.values())
        else "fail"
    )

    images = []
    for view in VIEWS:
        image = target / f"model-{view}.png"
        render_mesh(mesh, image, view)
        if not image.is_file() or image.stat().st_size == 0:
            raise RuntimeError(f"empty {implementation} render for {slug}: {view}")
        images.append(image.name)

    result = {
        "case": slug,
        "implementation": implementation,
        "status": status,
        "source": str(source.relative_to(ROOT)),
        "stl": stl.name,
        "images": images,
        "bounds": {"min": actual_min.tolist(), "max": actual_max.tolist()},
        "expected": {"min": expected_min.tolist(), "max": expected_max.tolist()},
        "max_delta_mm": float(np.max(delta)),
        "tolerance_mm": tolerance,
        "checks": checks,
        "bounds_sufficient": contract["bounds_sufficient"],
        "bounds_reason": contract["bounds_reason"],
    }
    (target / "result.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="all")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--tolerance", type=float, default=0.5)
    args = parser.parse_args()

    selected = parse_case_selection(args.cases)
    results = {}
    failures = []
    for slug in selected:
        results[slug] = {}
        for implementation in implementations_for(slug):
            print(f"reference {implementation}: {slug}")
            try:
                result = validate_one(slug, implementation, args.out, args.tolerance)
            except Exception as exc:
                result = {
                    "case": slug,
                    "implementation": implementation,
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            results[slug][implementation] = result
            if result["status"] != "pass":
                failures.append(
                    f"{slug}/{implementation}: "
                    f"{result.get('error') or result.get('max_delta_mm')}"
                )

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(
        json.dumps(
            {"schema": 1, "source_commit": args.source_sha, "results": results},
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    if failures:
        print("Reference verification failures:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
