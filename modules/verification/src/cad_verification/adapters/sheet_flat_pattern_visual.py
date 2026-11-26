"""Visual verification for native SolidCraft sheet manufacturing DXF output."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from ..evidence import artifact_record
from ..process import run_command


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _point(value: Any, name: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must contain two numbers")
    return (_number(value[0], f"{name}[0]"), _number(value[1], f"{name}[1]"))


def _load_policy(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise ValueError("sheet flat-pattern visual policy must use schema 1")
    if value.get("approval") != "approved":
        raise ValueError("sheet flat-pattern visual policy must be approved")
    body = value.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("sheet flat-pattern visual policy requires body")
    outline = value.get("outline")
    if not isinstance(outline, dict):
        raise ValueError("sheet flat-pattern visual policy requires outline")
    minimum = _point(outline.get("minimum"), "outline.minimum")
    maximum = _point(outline.get("maximum"), "outline.maximum")
    if maximum[0] <= minimum[0] or maximum[1] <= minimum[1]:
        raise ValueError("sheet flat-pattern visual outline is inverted")
    value["outline"] = {"minimum": minimum, "maximum": maximum}

    circles = value.get("perforations")
    if not isinstance(circles, list) or not circles:
        raise ValueError("sheet flat-pattern visual policy requires perforations")
    normalized = []
    for index, row in enumerate(circles):
        if not isinstance(row, dict):
            raise ValueError(f"perforations[{index}] must be an object")
        diameter = _number(row.get("diameter"), f"perforations[{index}].diameter")
        if diameter <= 0:
            raise ValueError(f"perforations[{index}].diameter must be positive")
        normalized.append({
            "center": _point(row.get("center"), f"perforations[{index}].center"),
            "diameter": diameter,
        })
    value["perforations"] = normalized
    tolerance = _number(value.get("tolerance_mm", 0.001), "tolerance_mm")
    if tolerance < 0:
        raise ValueError("tolerance_mm may not be negative")
    value["tolerance_mm"] = tolerance
    return value


def _dxf_pairs(text: str) -> list[tuple[str, str]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) % 2:
        raise ValueError("DXF must contain group-code/value pairs")
    return [(lines[i].strip(), lines[i + 1].strip()) for i in range(0, len(lines), 2)]


def parse_perforation_circles(text: str) -> list[dict[str, Any]]:
    """Read CIRCLE entities from the native PERFORATION DXF layer."""
    entities = []
    current = None
    for code, value in _dxf_pairs(text):
        if code == "0":
            if current is not None:
                entities.append(current)
            current = {"type": value, "values": {}}
            continue
        if current is not None:
            current["values"].setdefault(code, []).append(value)
    if current is not None:
        entities.append(current)

    result = []
    for entity in entities:
        values = entity["values"]
        layer = (values.get("8") or [""])[0]
        if entity["type"] != "CIRCLE" or layer != "PERFORATION":
            continue
        try:
            center = (float(values["10"][0]), float(values["20"][0]))
            radius = float(values["40"][0])
        except (KeyError, IndexError, ValueError) as exc:
            raise ValueError("invalid PERFORATION CIRCLE in native DXF") from exc
        if not all(math.isfinite(v) for v in (*center, radius)) or radius <= 0:
            raise ValueError("invalid PERFORATION CIRCLE geometry in native DXF")
        result.append({"center": center, "diameter": radius * 2.0})
    return sorted(result, key=lambda row: (row["center"][1], row["center"][0], row["diameter"]))


def _match_perforations(actual, expected, tolerance):
    expected = sorted(expected, key=lambda row: (row["center"][1], row["center"][0], row["diameter"]))
    if len(actual) != len(expected):
        return False, {
            "expected_count": len(expected),
            "actual_count": len(actual),
            "maximum_center_error_mm": None,
            "maximum_diameter_error_mm": None,
            "tolerance_mm": tolerance,
        }
    center_errors = [
        math.dist(observed["center"], wanted["center"])
        for observed, wanted in zip(actual, expected)
    ]
    diameter_errors = [
        abs(observed["diameter"] - wanted["diameter"])
        for observed, wanted in zip(actual, expected)
    ]
    maximum_center = max(center_errors, default=0.0)
    maximum_diameter = max(diameter_errors, default=0.0)
    return maximum_center <= tolerance and maximum_diameter <= tolerance, {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "maximum_center_error_mm": maximum_center,
        "maximum_diameter_error_mm": maximum_diameter,
        "tolerance_mm": tolerance,
    }


def _svg(outline: Mapping[str, tuple[float, float]], circles, *, expected=None) -> str:
    minimum = outline["minimum"]
    maximum = outline["maximum"]
    width = maximum[0] - minimum[0]
    height = maximum[1] - minimum[1]
    pad = max(width, height) * 0.06
    x0 = minimum[0] - pad
    y0 = -(maximum[1] + pad)
    vw = width + 2 * pad
    vh = height + 2 * pad

    def circle(row, css):
        x, y = row["center"]
        radius = row["diameter"] / 2.0
        return f'<circle class="{css}" cx="{x:g}" cy="{-y:g}" r="{radius:g}" />'

    rows = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{x0:g} {y0:g} {vw:g} {vh:g}" '
        'role="img" aria-label="sheet flat-pattern perforation field">',
        '<style>'
        '.sheet{fill:#f8f8f8;stroke:#222;stroke-width:.45}'
        '.actual{fill:white;stroke:#111;stroke-width:.45}'
        '.expected{fill:none;stroke:#777;stroke-width:.3;stroke-dasharray:1.2 1}'
        '</style>',
        f'<rect class="sheet" x="{minimum[0]:g}" y="{-maximum[1]:g}" '
        f'width="{width:g}" height="{height:g}" />',
    ]
    if expected is not None:
        rows.extend(circle(row, "expected") for row in expected)
    rows.extend(circle(row, "actual") for row in circles)
    rows.append("</svg>")
    return "\n".join(rows) + "\n"


def _write_native_dxf(model_path: Path, output_dir: Path, body: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    dxf = (output_dir / "actual.dxf").resolve()
    commands = output_dir / "export-dxf.json"
    results = output_dir / "export-results.json"
    commands.write_text(
        json.dumps(
            {"commands": [{"command": "sheet.export_dxf", "params": {
                "body": body, "path": str(dxf), "curves": "exact"
            }}]},
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    run_command([
        "solidcraft-cli", "run", str(commands),
        "--in", str(Path(model_path).resolve()),
        "--param-check", "strict",
        "--results", "--json-out", str(results.resolve()),
    ])
    if not dxf.is_file() or dxf.stat().st_size == 0:
        raise ValueError("SolidCraft sheet.export_dxf did not produce a DXF")
    return dxf


def run_sheet_flat_pattern_visual_verification_file(
    model_path: Path,
    output_dir: Path,
    policy_path: Path,
    *,
    verification_id: str,
) -> dict[str, Any]:
    """Verify and visualize native SolidCraft flat-pattern perforation output."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    policy = _load_policy(policy_path)
    dxf = _write_native_dxf(model_path, output_dir, policy["body"])
    actual = parse_perforation_circles(dxf.read_text(encoding="utf-8"))
    expected = policy["perforations"]
    passed, comparison = _match_perforations(actual, expected, policy["tolerance_mm"])

    actual_svg = output_dir / "actual.svg"
    goal_svg = output_dir / "goal.svg"
    overlay_svg = output_dir / "overlay.svg"
    actual_svg.write_text(_svg(policy["outline"], actual), encoding="utf-8")
    goal_svg.write_text(_svg(policy["outline"], expected), encoding="utf-8")
    overlay_svg.write_text(_svg(policy["outline"], actual, expected=expected), encoding="utf-8")

    status = "pass" if passed else "fail"
    evidence = {
        "view": "manufacturing-flat-pattern",
        "context": (
            "Native sheet.export_dxf manufacturing output; the ordinary 3D "
            "B-rep preview intentionally remains unperforated."
        ),
        "baseline_status": "not-applicable",
        "expected_shape_status": status,
        "actual_image": "actual.svg",
        "goal_image": "goal.svg",
        "overlay_image": "overlay.svg",
        "perforation_field": {
            "label": "Native DXF perforation field",
            "expected": {"count": len(expected), "diameter_mm": expected[0]["diameter"]},
            "actual": {
                "count": len(actual),
                "diameter_mm": actual[0]["diameter"] if actual else None,
            },
            "pass": passed,
        },
        "geometry_errors": comparison,
    }
    artifacts = [
        artifact_record(dxf, output_dir),
        artifact_record(actual_svg, output_dir),
        artifact_record(goal_svg, output_dir),
        artifact_record(overlay_svg, output_dir),
    ]
    report = {
        "schema": "cad-verification",
        "schema_version": 1,
        "verification_id": verification_id,
        "status": status,
        "input": str(Path(model_path).resolve()),
        "metadata": {
            "kind": "solidcraft-sheet-flat-pattern-visual",
            "approval": policy["approval"],
            "source": "sheet.export_dxf",
        },
        "checks": [{
            "id": "manufacturing-flat-pattern",
            "status": status,
            "reason": None,
            "error": None if passed else "native DXF perforation field differs from approved expectation",
            "evidence": evidence,
            "artifacts": artifacts,
        }],
    }
    (output_dir / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
