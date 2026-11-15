"""Execute PythonSCAD and pyBOSL2 qualification references.

Each reference source must expose a final 3-D object as model. The runner
exports that object with the reference library itself, checks the resulting STL
against the independent qualification envelope and renders fixed comparison
views from that STL.
"""

from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qualification.case_selection import CASE_BY_SLUG, format_selection_help, parse_case_selection
from qualification.expectations import EXPECTED_BOUNDS


DEFAULT_IMPLEMENTATIONS = ("pythonscad", "pybosl2")
VIEWS = {
    "front": (0, -90),
    "right": (0, 0),
    "iso": (28, -45),
}


def expected_envelope(slug: str) -> tuple[np.ndarray, np.ndarray]:
    boxes = EXPECTED_BOUNDS[slug]
    lo = np.min(np.asarray([row["min"] for row in boxes], dtype=float), axis=0)
    hi = np.max(np.asarray([row["max"] for row in boxes], dtype=float), axis=0)
    return lo, hi


def load_reference(path: Path):
    namespace = runpy.run_path(str(path))
    if "model" not in namespace:
        raise RuntimeError(f"{path} must expose final geometry as model")
    return namespace["model"]


def implementations_for(slug: str) -> tuple[str, ...]:
    return tuple(
        CASE_BY_SLUG[slug].get(
            "reference_implementations",
            DEFAULT_IMPLEMENTATIONS,
        )
    )


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

    model = load_reference(source)
    exported = export_reference(model, implementation, stl)
    if not stl.is_file() and exported is not None:
        candidate = Path(exported)
        if candidate.is_file():
            stl = candidate
    if not stl.is_file() or stl.stat().st_size == 0:
        raise RuntimeError(f"{implementation} did not export a non-empty STL for {slug}")

    loaded = trimesh.load_mesh(stl, process=False)
    if isinstance(loaded, trimesh.Scene):
        mesh = loaded.dump(concatenate=True)
    else:
        mesh = loaded
    if not isinstance(mesh, trimesh.Trimesh) or mesh.vertices.size == 0:
        raise RuntimeError(f"{implementation} exported no measurable mesh for {slug}")

    expected_min, expected_max = expected_envelope(slug)
    actual_min, actual_max = np.asarray(mesh.bounds[0]), np.asarray(mesh.bounds[1])
    delta = np.maximum(np.abs(actual_min - expected_min), np.abs(actual_max - expected_max))
    status = "pass" if np.all(delta <= tolerance) else "fail"

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
    }
    (target / "result.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=format_selection_help(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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
        print("Reference qualification failures:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
