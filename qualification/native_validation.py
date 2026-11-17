#!/usr/bin/env python3
"""Validate native SolidCraft qualification evidence against Forge semantics.

The validator intentionally reads only generated native evidence. It does not
reuse Forge's placement implementation to calculate expected positions; doing
so would let the code under test validate itself.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qualification.case_selection import parse_case_selection
from qualification.cases import supported_case_slugs
from qualification.expectations import EXPECTED_MUTATION_BOUNDS
from qualification.geometry_contracts import geometry_contract


TOL = 1e-3


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def close(a: float, b: float, tol: float = TOL) -> bool:
    return abs(float(a) - float(b)) <= tol


def vector_close(actual, expected, tol: float = TOL) -> bool:
    return len(actual) == len(expected) and all(close(a, b, tol) for a, b in zip(actual, expected))


def bbox(body: dict) -> tuple[list[float], list[float]]:
    return body["bbox"]["min"], body["bbox"]["max"]


def bbox_close(body: dict, expected_min, expected_max, tol: float = TOL) -> bool:
    actual_min, actual_max = bbox(body)
    return vector_close(actual_min, expected_min, tol) and vector_close(actual_max, expected_max, tol)


def widths(data: dict) -> list[float]:
    return sorted(round(body["bbox"]["max"][0] - body["bbox"]["min"][0], 6) for body in data["bodies"])


def body_size(body: dict) -> tuple[float, float, float]:
    return tuple(
        round(float(hi) - float(lo), 6)
        for lo, hi in zip(body["bbox"]["min"], body["bbox"]["max"])
    )


def _bounds_match(data: dict, expected: list[dict], tol: float = TOL) -> bool:
    actual = [
        (body["bbox"]["min"], body["bbox"]["max"])
        for body in data.get("bodies", [])
        if body.get("bbox")
    ]
    if len(actual) != len(expected):
        return False

    unmatched = list(actual)
    for target in expected:
        hit = next(
            (
                index for index, (lo, hi) in enumerate(unmatched)
                if vector_close(lo, target["min"], tol)
                and vector_close(hi, target["max"], tol)
            ),
            None,
        )
        if hit is None:
            return False
        unmatched.pop(hit)
    return not unmatched


def _check_declared_bounds(
    validation,
    data: dict,
    case: str,
    *,
    level: str = "q4",
    mutation: bool = False,
    tol: float = TOL,
):
    expected = (
        EXPECTED_MUTATION_BOUNDS.get(case)
        if mutation
        else geometry_contract(case)["bounds"]
    )
    if expected is None:
        return
    validation.check(
        "declared target geometry" if not mutation else "declared mutation target geometry",
        _bounds_match(data, expected, tol),
        expected,
        [
            {"min": body["bbox"]["min"], "max": body["bbox"]["max"]}
            for body in data.get("bodies", [])
            if body.get("bbox")
        ],
        level,
    )


def _check_contract_volume(validation, body: dict, case: str, *, tol: float | None = None):
    contract = geometry_contract(case)
    if "volume_mm3" not in contract:
        return
    expected = float(contract["volume_mm3"])
    tolerance = (
        float(tol)
        if tol is not None
        else float(contract.get("volume_tolerance_mm3", TOL))
    )
    actual = float(body["volume_mm3"])
    validation.check(
        "shared geometry volume",
        close(actual, expected, tolerance),
        {"volume_mm3": expected, "tolerance_mm3": tolerance},
        {"volume_mm3": actual},
    )


def params(data: dict) -> dict[str, float]:
    return {row["name"]: float(row["value"]) for row in data.get("params", [])}


def bodies_named(data: dict, prefix: str) -> list[dict]:
    return [body for body in data["bodies"] if body["name"].startswith(prefix)]


def one_body(data: dict, prefix: str) -> dict:
    rows = bodies_named(data, prefix)
    if len(rows) != 1:
        raise AssertionError(f"expected one body starting with {prefix!r}, found {len(rows)}")
    return rows[0]


class Validation:
    def __init__(self, case: str):
        self.case = case
        self.checks: list[dict[str, Any]] = []

    def check(self, name: str, condition: bool, expected=None, actual=None, level: str = "q4"):
        self.checks.append({
            "name": name,
            "level": level,
            "status": "pass" if condition else "fail",
            "expected": expected,
            "actual": actual,
        })

    def status(self, level: str) -> str:
        rows = [row for row in self.checks if row["level"] == level]
        if not rows:
            return "not-required" if level == "q5" else "review"
        return "pass" if all(row["status"] == "pass" for row in rows) else "fail"

    def result(self) -> dict:
        return {
            "case": self.case,
            "q4": self.status("q4"),
            "q5": self.status("q5"),
            "checks": self.checks,
        }


def validate_simple_box(root: Path) -> Validation:
    v = Validation("simple-box")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "simple-box")
    v.check("one body", d["body_count"] == 1, 1, d["body_count"])
    b = d["bodies"][0]
    v.check("40x30x10 bounds", bbox_close(b, [-20, -15, 0], [20, 15, 10]),
            {"min": [-20, -15, 0], "max": [20, 15, 10]}, b["bbox"])
    v.check("parameters", params(d) == {"length": 40.0, "width": 30.0, "height": 10.0},
            {"length": 40.0, "width": 30.0, "height": 10.0}, params(d))

    m = load(root / "measurements-length-50.json")
    _check_declared_bounds(
        v,
        m,
        "simple-box",
        level="q5",
        mutation=True,
    )
    v.check(
        "length parameter changed in saved design",
        params(m) == {"length": 50.0, "width": 30.0, "height": 10.0},
        {"length": 50.0, "width": 30.0, "height": 10.0},
        params(m),
        "q5",
    )
    v.check(
        "native Box rebuilds after length mutation",
        m["body_count"] == 1
        and bbox_close(m["bodies"][0], [-25, -15, 0], [25, 15, 10]),
        {"min": [-25, -15, 0], "max": [25, 15, 10]},
        m["bodies"][0]["bbox"] if m.get("bodies") else None,
        "q5",
    )

    return v


def validate_anchored_holes(root: Path) -> Validation:
    v = Validation("anchored-holes")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "anchored-holes")
    v.check("one plate body", d["body_count"] == 1, 1, d["body_count"])
    b = d["bodies"][0]
    v.check("plate outer bounds", bbox_close(b, [0, 0, 0], [100, 60, 10]),
            {"min": [0, 0, 0], "max": [100, 60, 10]}, b["bbox"])
    cylinders = b.get("face_types", {}).get("cylinder", 0)
    v.check("two cylindrical hole walls", cylinders == 2, 2, cylinders)
    _check_contract_volume(v, b, "anchored-holes", tol=0.5)
    return v


def validate_parameter_scope(root: Path) -> Validation:
    v = Validation("parameter-scope")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "parameter-scope")
    v.check("baseline widths", widths(d) == [40.0, 40.0, 60.0, 80.0, 80.0],
            [40, 40, 60, 80, 80], widths(d))
    expected_parameters = {
        "d1_Panel_width": 40.0,
        "d2_Panel_2_width": 60.0,
        "shared_width": 80.0,
    }
    v.check(
        "baseline parameters",
        params(d) == expected_parameters,
        expected_parameters,
        params(d),
    )

    m = load(root / "measurements-shared-width-100.json")
    _check_declared_bounds(v, m, "parameter-scope", level="q5", mutation=True)
    v.check("mutated shared width", params(m).get("shared_width") == 100.0, 100.0,
            params(m).get("shared_width"), "q5")
    v.check("dependent widths rebuild", widths(m) == [40.0, 50.0, 60.0, 100.0, 100.0],
            [40, 50, 60, 100, 100], widths(m), "q5")
    return v


def validate_parent_derived_child_size(root: Path) -> Validation:
    v = Validation("parent-derived-child-size")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "parent-derived-child-size")
    v.check("two bodies", d["body_count"] == 2, 2, d["body_count"])
    v.check(
        "baseline parent parameters",
        params(d) == {"base_width": 120.0, "base_depth": 80.0},
        {"base_width": 120.0, "base_depth": 80.0},
        params(d),
    )
    v.check(
        "child is half parent width/depth",
        sorted(body_size(body) for body in d["bodies"])
        == [(60.0, 40.0, 6.0), (120.0, 80.0, 10.0)],
        [(60.0, 40.0, 6.0), (120.0, 80.0, 10.0)],
        sorted(body_size(body) for body in d["bodies"]),
    )

    m = load(root / "measurements-size-160x120.json")
    _check_declared_bounds(
        v,
        m,
        "parent-derived-child-size",
        level="q5",
        mutation=True,
    )
    v.check(
        "parent parameters changed",
        params(m) == {"base_width": 160.0, "base_depth": 120.0},
        {"base_width": 160.0, "base_depth": 120.0},
        params(m),
        "q5",
    )
    v.check(
        "child rebuilds from parent expressions",
        sorted(body_size(body) for body in m["bodies"])
        == [(80.0, 60.0, 6.0), (160.0, 120.0, 10.0)],
        [(80.0, 60.0, 6.0), (160.0, 120.0, 10.0)],
        sorted(body_size(body) for body in m["bodies"]),
        "q5",
    )
    return v


def validate_components(root: Path) -> Validation:
    v = Validation("components")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "components")
    rows = bodies_named(d, "Block")
    v.check("two block occurrences", len(rows) == 2, 2, len(rows))
    actual = sorted(rows, key=lambda body: body["bbox"]["min"][0])
    expected = [
        ([-20, -15, 0], [20, 15, 10]),
        ([20, -15, 0], [60, 15, 10]),
    ]
    touch_ok = (
        len(actual) == 2
        and all(
            bbox_close(body, minimum, maximum)
            for body, (minimum, maximum) in zip(actual, expected)
        )
    )
    v.check(
        "blocks touch face-to-face",
        touch_ok,
        expected,
        [(body["bbox"]["min"], body["bbox"]["max"]) for body in actual],
    )
    return v



def validate_repeated_parent_attachments(root: Path) -> Validation:
    v = Validation("repeated-parent-attachments")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "repeated-parent-attachments")
    v.check("four bodies", d["body_count"] == 4, 4, d["body_count"])
    v.check(
        "shared parent height parameter",
        params(d).get("parent_height") == 40.0,
        40.0,
        params(d).get("parent_height"),
    )
    markers = bodies_named(d, "Marker")
    baseline_marker_bounds = sorted(
        (
            round(body["bbox"]["min"][0], 6),
            round(body["bbox"]["min"][2], 6),
            round(body["bbox"]["max"][2], 6),
        )
        for body in markers
    )
    v.check(
        "both baseline markers sit on parent top faces",
        len(markers) == 2
        and baseline_marker_bounds == [
            (-5.0, 40.0, 50.0),
            (55.0, 40.0, 50.0),
        ],
        [(-5.0, 40.0, 50.0), (55.0, 40.0, 50.0)],
        baseline_marker_bounds,
    )

    m = load(root / "measurements-height-60.json")
    _check_declared_bounds(
        v,
        m,
        "repeated-parent-attachments",
        level="q5",
        mutation=True,
    )
    v.check(
        "parent height changed in saved design",
        params(m).get("parent_height") == 60.0,
        60.0,
        params(m).get("parent_height"),
        "q5",
    )
    markers2 = bodies_named(m, "Marker")
    mutated_marker_bounds = sorted(
        (
            round(body["bbox"]["min"][0], 6),
            round(body["bbox"]["min"][2], 6),
            round(body["bbox"]["max"][2], 6),
        )
        for body in markers2
    )
    v.check(
        "both disconnected joint graphs follow height mutation",
        len(markers2) == 2
        and mutated_marker_bounds == [
            (-5.0, 60.0, 70.0),
            (55.0, 60.0, 70.0),
        ],
        [(-5.0, 60.0, 70.0), (55.0, 60.0, 70.0)],
        mutated_marker_bounds,
        "q5",
    )
    return v


def validate_assembly_decorator(root: Path) -> Validation:
    v = Validation("assembly-decorator")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "assembly-decorator")
    v.check("two native post bodies", d["body_count"] == 2, 2, d["body_count"])
    actual = sorted(
        (body["bbox"]["min"], body["bbox"]["max"])
        for body in d["bodies"]
    )
    expected = sorted([
        ([-20, -5, 0], [-10, 5, 20]),
        ([10, -5, 0], [20, 5, 20]),
    ])
    v.check(
        "imported assembly placement",
        actual == expected,
        expected,
        actual,
    )
    return v


def validate_group_hierarchy(root: Path) -> Validation:
    v = Validation("group-hierarchy")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "group-hierarchy")
    v.check("three native bodies", d["body_count"] == 3, 3, d["body_count"])

    inspection = load(root / "results-bom.json")
    v.check(
        "BOM and component inspections",
        len(inspection) == 3,
        3,
        len(inspection),
    )
    if len(inspection) == 3:
        top, flat, component_list = inspection
        top_rows = {
            row["definition"]: row["count"]
            for row in top.get("rows", [])
        }
        flat_rows = {
            row["definition"]: row["count"]
            for row in flat.get("rows", [])
        }
        v.check(
            "top BOM preserves named subassembly",
            top.get("levels") == "top"
            and top_rows == {"Frame": 1, "PanelGroup": 1}
            and top.get("total_occurrences") == 2,
            {"Frame": 1, "PanelGroup": 1, "total_occurrences": 2},
            {**top_rows, "total_occurrences": top.get("total_occurrences")},
        )
        v.check(
            "flat BOM expands grouped panel occurrences",
            flat.get("levels") == "flat"
            and flat_rows == {"Frame": 1, "Panel": 2}
            and flat.get("total_occurrences") == 3,
            {"Frame": 1, "Panel": 2, "total_occurrences": 3},
            {**flat_rows, "total_occurrences": flat.get("total_occurrences")},
        )

        components = {
            component["name"]: component
            for component in component_list.get("components", [])
        }
        group_occurrences = components.get("PanelGroup", {}).get(
            "occurrences", []
        )
        panel_occurrences = components.get("Panel", {}).get(
            "occurrences", []
        )
        v.check(
            "browser group is not grounded",
            len(group_occurrences) == 1
            and group_occurrences[0].get("grounded") is False,
            {"count": 1, "grounded": False},
            {
                "count": len(group_occurrences),
                "grounded": (
                    group_occurrences[0].get("grounded")
                    if group_occurrences else None
                ),
            },
        )
        v.check(
            "physical first panel remains grounded",
            len(panel_occurrences) == 2
            and panel_occurrences[0].get("grounded") is True,
            {"count": 2, "first_grounded": True},
            {
                "count": len(panel_occurrences),
                "first_grounded": (
                    panel_occurrences[0].get("grounded")
                    if panel_occurrences else None
                ),
            },
        )
    return v

def validate_attach_angle(root: Path) -> Validation:
    v = Validation("attach-angle")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "attach-angle")
    v.check("two bodies", d["body_count"] == 2, 2, d["body_count"])
    arm = one_body(d, "Arm")
    v.check(
        "90 degree joint swaps 30x10 footprint to 10x30",
        bbox_close(
            arm,
            [-5, -15, 10],
            [5, 15, 16],
        ),
        {"min": [-5, -15, 10], "max": [5, 15, 16]},
        arm["bbox"],
    )
    return v


def validate_parametric_attach(root: Path) -> Validation:
    v = Validation("parametric-attach")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "parametric-attach")
    base = one_body(d, "Base")
    block = one_body(d, "Block")
    v.check("base bounds", bbox_close(base, [-20, -15, 0], [20, 15, 10]))
    v.check("10 mm gap", bbox_close(block, [30, -10, 0], [50, 10, 10]),
            {"min": [30, -10, 0], "max": [50, 10, 10]}, block["bbox"])

    m = load(root / "measurements-gap-30.json")
    _check_declared_bounds(v, m, "parametric-attach", level="q5", mutation=True)
    block2 = one_body(m, "Block")
    v.check("30 mm gap mutation", bbox_close(block2, [50, -10, 0], [70, 10, 10]),
            {"min": [50, -10, 0], "max": [70, 10, 10]}, block2["bbox"], "q5")
    return v


def validate_parametric_offset(root: Path) -> Validation:
    v = Validation("parametric-offset")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "parametric-offset")
    marker = one_body(d, "Marker")
    # FRONT_TOP_RIGHT of the parent meets BACK_TOP_RIGHT of the child.
    # The child top therefore ends at parent z=20. The planar v=-5 offset
    # follows +Z in this parent corner frame, moving it upward by 5 mm.
    v.check("top-right anchor + 5 mm local offset",
            bbox_close(marker, [10, -25, 15], [20, -15, 25]),
            {"min": [10, -25, 15], "max": [20, -15, 25]}, marker["bbox"])

    m = load(root / "measurements-shift-10.json")
    _check_declared_bounds(v, m, "parametric-offset", level="q5", mutation=True)
    marker2 = one_body(m, "Marker")
    v.check("10 mm local offset mutation",
            bbox_close(marker2, [10, -25, 20], [20, -15, 30]),
            {"min": [10, -25, 20], "max": [20, -15, 30]}, marker2["bbox"], "q5")
    return v


def validate_parametric_anchor(root: Path) -> Validation:
    v = Validation("parametric-anchor")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "parametric-anchor")
    v.check("RIGHT-to-LEFT baseline",
            bbox_close(one_body(d, "Block"), [20, -10, 0], [40, 10, 10]))
    m = load(root / "measurements-width-80.json")
    _check_declared_bounds(v, m, "parametric-anchor", level="q5", mutation=True)
    v.check("RIGHT anchor follows width mutation",
            bbox_close(one_body(m, "Block"), [40, -10, 0], [60, 10, 10]),
            {"min": [40, -10, 0], "max": [60, 10, 10]},
            one_body(m, "Block")["bbox"], "q5")
    return v


def validate_corner_anchor(root: Path) -> Validation:
    v = Validation("corner-anchor")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "corner-anchor")
    marker = one_body(d, "Marker")
    # BACK_TOP_RIGHT is the child's top/back/right corner. Aligning it with
    # parent FRONT_TOP_RIGHT means the child's top ends at z=20.
    v.check("BACK_TOP_RIGHT meets parent FRONT_TOP_RIGHT",
            bbox_close(marker, [10, -25, 10], [20, -15, 20]),
            {"min": [10, -25, 10], "max": [20, -15, 20]}, marker["bbox"])

    m = load(root / "measurements-size-80x40.json")
    _check_declared_bounds(v, m, "corner-anchor", level="q5", mutation=True)
    marker2 = one_body(m, "Marker")
    v.check("corner follows 80x40 mutation",
            bbox_close(marker2, [30, -25, 30], [40, -15, 40]),
            {"min": [30, -25, 30], "max": [40, -15, 40]}, marker2["bbox"], "q5")
    return v


def validate_assembly_owned_anchor(root: Path) -> Validation:
    v = Validation("assembly-owned-anchor")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "assembly-owned-anchor")
    v.check("three bodies", d["body_count"] == 3, 3, d["body_count"])
    v.check(
        "named anchor reaches baseline corner",
        bbox_close(
            one_body(d, "Marker"),
            [10, -25, 10],
            [20, -15, 20],
        ),
        {"min": [10, -25, 10], "max": [20, -15, 20]},
        one_body(d, "Marker")["bbox"],
    )

    m = load(root / "measurements-size-80x40.json")
    _check_declared_bounds(
        v,
        m,
        "assembly-owned-anchor",
        level="q5",
        mutation=True,
    )
    v.check(
        "base dimensions changed",
        params(m) == {"base_width": 80.0, "base_height": 40.0},
        {"base_width": 80.0, "base_height": 40.0},
        params(m),
        "q5",
    )
    v.check(
        "named anchor keeps native corner associativity",
        bbox_close(
            one_body(m, "Marker"),
            [30, -25, 30],
            [40, -15, 40],
        ),
        {"min": [30, -25, 30], "max": [40, -15, 40]},
        one_body(m, "Marker")["bbox"],
        "q5",
    )
    return v


def validate_anchor_topology_mutation(root: Path) -> Validation:
    v = Validation("anchor-topology-mutation")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "anchor-topology-mutation")
    v.check("two bodies", d["body_count"] == 2, 2, d["body_count"])
    v.check(
        "marker touches baseline topology corner outside front face",
        bbox_close(
            one_body(d, "Marker"),
            [-25, -20, 15],
            [-15, -10, 25],
        ),
        {"min": [-25, -20, 15], "max": [-15, -10, 25]},
        one_body(d, "Marker")["bbox"],
    )

    m = load(root / "measurements-size-80x40.json")
    _check_declared_bounds(
        v,
        m,
        "anchor-topology-mutation",
        level="q5",
        mutation=True,
    )
    v.check(
        "parent dimensions changed",
        params(m) == {"base_width": 80.0, "base_height": 40.0},
        {"base_width": 80.0, "base_height": 40.0},
        params(m),
        "q5",
    )
    v.check(
        "fixed topology pick follows resized corner",
        bbox_close(
            one_body(m, "Marker"),
            [-45, -20, 35],
            [-35, -10, 45],
        ),
        {"min": [-45, -20, 35], "max": [-35, -10, 45]},
        one_body(m, "Marker")["bbox"],
        "q5",
    )
    return v


def validate_four_corner_l(root: Path) -> Validation:
    v = Validation("four-corner-l")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "four-corner-l")
    frame = one_body(d, "FrameBlock")
    v.check("frame bounds", bbox_close(frame, [-60, -40, 0], [60, 40, 60]))

    m = load(root / "measurements-size-160x120.json")
    _check_declared_bounds(v, m, "four-corner-l", level="q5", mutation=True)
    return v


def validate_eight_flightcase_corners(root: Path) -> Validation:
    v = Validation("eight-flightcase-corners")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "eight-flightcase-corners")
    v.check("nine bodies: case plus eight flightcase corners",
            d["body_count"] == 9, 9, d["body_count"])

    baseline_corners = bodies_named(d, "FlightcaseCorner")
    baseline_sizes = sorted(body_size(body) for body in baseline_corners)
    v.check(
        "eight fixed 24x24x24 protector envelopes",
        baseline_sizes == [(24.0, 24.0, 24.0)] * 8,
        [(24.0, 24.0, 24.0)] * 8,
        baseline_sizes,
    )

    m = load(root / "measurements-size-160x120x90.json")
    _check_declared_bounds(
        v,
        m,
        "eight-flightcase-corners",
        level="q5",
        mutation=True,
    )
    v.check("nine bodies after saved-design mutation",
            m["body_count"] == 9, 9, m["body_count"], "q5")
    v.check(
        "case dimensions changed",
        params(m) == {
            "case_width": 160.0,
            "case_depth": 120.0,
            "case_height": 90.0,
        },
        {"case_width": 160.0, "case_depth": 120.0, "case_height": 90.0},
        params(m),
        "q5",
    )
    mutated_sizes = sorted(
        body_size(body)
        for body in bodies_named(m, "FlightcaseCorner")
    )
    v.check(
        "protector envelopes remain fixed after parent resize",
        mutated_sizes == baseline_sizes == [(24.0, 24.0, 24.0)] * 8,
        [(24.0, 24.0, 24.0)] * 8,
        mutated_sizes,
        "q5",
    )
    return v


def validate_eight_corner_brackets(root: Path) -> Validation:
    v = Validation("eight-corner-brackets")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "eight-corner-brackets")
    v.check("nine bodies: frame plus eight brackets",
            d["body_count"] == 9, 9, d["body_count"])

    m = load(root / "measurements-size-160x120x90.json")
    _check_declared_bounds(
        v,
        m,
        "eight-corner-brackets",
        level="q5",
        mutation=True,
    )
    v.check("nine bodies after saved-design mutation",
            m["body_count"] == 9, 9, m["body_count"], "q5")
    return v


def _xz_expected(width: float, height: float):
    return {
        "right": ([width / 2 - 10, -10, height - 10], [width / 2, 0, height]),
        "left": ([-width / 2, -10, height - 10], [-width / 2 + 10, 0, height]),
    }


def validate_xz_anchor(root: Path) -> Validation:
    v = Validation("xz-anchor")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "xz-anchor")
    markers = (
        bodies_named(d, "RightMarker")
        + bodies_named(d, "LeftMarker")
    )
    expected = _xz_expected(40, 20)
    actual_boxes = [(b["bbox"]["min"], b["bbox"]["max"]) for b in markers]
    v.check("two markers", len(markers) == 2, 2, len(markers))
    for side, (emin, emax) in expected.items():
        hit = any(bbox_close(b, emin, emax) for b in markers)
        v.check(f"{side} BACK_TOP corner alignment", hit,
                {"min": emin, "max": emax}, actual_boxes)

    m = load(root / "measurements-size-80x40.json")
    markers2 = (
        bodies_named(m, "RightMarker")
        + bodies_named(m, "LeftMarker")
    )
    expected2 = _xz_expected(80, 40)
    actual2 = [(b["bbox"]["min"], b["bbox"]["max"]) for b in markers2]
    for side, (emin, emax) in expected2.items():
        hit = any(bbox_close(b, emin, emax) for b in markers2)
        v.check(f"{side} corner follows size mutation", hit,
                {"min": emin, "max": emax}, actual2, "q5")
    return v



def validate_circle_negative_extrude(root: Path) -> Validation:
    v = Validation("circle-negative-extrude")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "circle-negative-extrude", tol=0.01)
    v.check("single cylindrical body", d["body_count"] == 1, 1, d["body_count"])
    if d["bodies"]:
        b = d["bodies"][0]
        v.check(
            "negative extrusion bounds",
            bbox_close(b, [-10, -10, -30], [10, 10, 0], 0.01),
            {"min": [-10, -10, -30], "max": [10, 10, 0]},
            b["bbox"],
        )
        _check_contract_volume(v, b, "circle-negative-extrude", tol=0.5)
        v.check(
            "one cylindrical side face",
            b.get("face_types", {}).get("cylinder") == 1,
            1,
            b.get("face_types", {}).get("cylinder"),
        )

    timeline = [
        (row.get("type"), row.get("name"))
        for row in d.get("timeline", [])
    ]
    expected_timeline = [
        ("Sketch", "Profile"),
        ("ExtrudeFeature", "Extrude1"),
    ]
    v.check(
        "explicit circle Sketch remains native sketch/extrude history",
        timeline == expected_timeline,
        expected_timeline,
        timeline,
    )
    return v


def validate_sketch_pattern_mirror(root: Path) -> Validation:
    v = Validation("sketch-pattern-mirror")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "sketch-pattern-mirror", tol=0.01)
    v.check("single patterned plate body", d["body_count"] == 1, 1, d["body_count"])

    expected_parameters = {
        "hole_columns": 4.0,
        "hole_diameter": 8.0,
        "hole_pitch": 25.0,
        "slot_count": 2.0,
        "slot_pitch": 50.0,
    }
    actual_parameters = params(d)
    v.check(
        "baseline seed/pattern parameters",
        all(
            actual_parameters.get(name) == value
            for name, value in expected_parameters.items()
        ),
        expected_parameters,
        {
            name: actual_parameters.get(name)
            for name in expected_parameters
        },
    )

    if d["bodies"]:
        body = d["bodies"][0]
        v.check(
            "baseline associative cuts remove expected material",
            close(
                body["volume_mm3"],
                geometry_contract("sketch-pattern-mirror")["volume_mm3"],
                0.05,
            ),
            geometry_contract("sketch-pattern-mirror")["volume_mm3"],
            body["volume_mm3"],
        )

    sketches = {
        row.get("name"): row
        for row in d.get("sketches", [])
    }
    v.check(
        "one Dog holes and one Clamp slots sketch",
        "Dog holes" in sketches
        and "Clamp slots" in sketches
        and len(sketches) == 2,
        ["Dog holes", "Clamp slots"],
        sorted(sketches),
    )
    v.check(
        "both associative sketches solve",
        all(
            sketches.get(name, {}).get("status") == "solved"
            for name in ("Dog holes", "Clamp slots")
        ),
        {"Dog holes": "solved", "Clamp slots": "solved"},
        {
            name: sketches.get(name, {}).get("status")
            for name in ("Dog holes", "Clamp slots")
        },
    )

    timeline = [
        (row.get("type"), row.get("name"))
        for row in d.get("timeline", [])
    ]
    expected_timeline = [
        ("BoxFeature", "Box1"),
        ("Sketch", "Dog holes"),
        ("ExtrudeFeature", "Dog holes"),
        ("Sketch", "Clamp slots"),
        ("ExtrudeFeature", "Clamp slots"),
    ]
    v.check(
        "pattern/mirror geometry stays inside two Sketch features",
        timeline == expected_timeline,
        expected_timeline,
        timeline,
    )

    # Q5 mutates only the already-saved SolidCraft design. Python is not rerun.
    m = load(root / "measurements-patterns-mutated.json")
    _check_declared_bounds(
        v,
        m,
        "sketch-pattern-mirror",
        level="q5",
        mutation=True,
        tol=0.01,
    )
    mutated_parameters = {
        "hole_columns": 4.0,
        "hole_diameter": 10.0,
        "hole_pitch": 30.0,
        "slot_count": 2.0,
        "slot_pitch": 30.0,
    }
    actual_mutated_parameters = params(m)
    v.check(
        "saved pattern parameters changed",
        all(
            actual_mutated_parameters.get(name) == value
            for name, value in mutated_parameters.items()
        ),
        mutated_parameters,
        {
            name: actual_mutated_parameters.get(name)
            for name in mutated_parameters
        },
        "q5",
    )

    if m["bodies"]:
        body = m["bodies"][0]
        slot_area = 20.0 * 8.0 + math.pi * 4.0**2
        expected_volume = (
            240.0 * 160.0 * 5.0
            - 8.0 * math.pi * 5.0**2 * 5.0
            - 8.0 * slot_area * 5.0
        )
        v.check(
            "saved design keeps 8 holes and 8 slots after associative edits",
            close(body["volume_mm3"], expected_volume, 0.05),
            expected_volume,
            body["volume_mm3"],
            "q5",
        )
        hole_volume = math.pi * 5.0**2 * 5.0
        expected_center_x = (
            -hole_volume * (2.0 * sum((-60.0, -30.0, 0.0, 30.0)))
            / expected_volume
        )
        v.check(
            "saved hole pitch moves the repeated Circle geometry",
            close(body["center_of_mass"][0], expected_center_x, 0.001),
            expected_center_x,
            body["center_of_mass"][0],
            "q5",
        )

    mutated_sketches = {
        row.get("name"): row
        for row in m.get("sketches", [])
    }
    v.check(
        "mutation keeps the same two solved Sketch features",
        set(mutated_sketches) == {"Dog holes", "Clamp slots"}
        and all(
            mutated_sketches[name].get("status") == "solved"
            for name in ("Dog holes", "Clamp slots")
        ),
        {"Dog holes": "solved", "Clamp slots": "solved"},
        {
            name: mutated_sketches.get(name, {}).get("status")
            for name in ("Dog holes", "Clamp slots")
        },
        "q5",
    )
    mutated_timeline = [
        (row.get("type"), row.get("name"))
        for row in m.get("timeline", [])
    ]
    v.check(
        "mutation preserves the two-sketch history",
        mutated_timeline == expected_timeline,
        expected_timeline,
        mutated_timeline,
        "q5",
    )

    return v


def validate_rectangular_pattern(root: Path) -> Validation:
    v = Validation("rectangular-pattern")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "rectangular-pattern", tol=0.01)
    v.check("single patterned plate body", d["body_count"] == 1, 1, d["body_count"])

    if d["bodies"]:
        body = d["bodies"][0]
        v.check(
            "pattern keeps the plate outer bounds",
            bbox_close(body, [-60, -40, 0], [60, 40, 4], 0.01),
            {"min": [-60, -40, 0], "max": [60, 40, 4]},
            body["bbox"],
        )
        faces = body.get("face_types", {})
        v.check(
            "3 x 2 rectangular Slot pattern has qualified native geometry",
            close(body["volume_mm3"], geometry_contract("rectangular-pattern")["volume_mm3"], 0.01)
            and body["faces"] == 30
            and faces.get("cylinder") == 12
            and faces.get("plane") == 18,
            {
                "volume_mm3": geometry_contract("rectangular-pattern")["volume_mm3"],
                "faces": 30,
                "face_types": {"cylinder": 12, "plane": 18},
            },
            {
                "volume_mm3": body["volume_mm3"],
                "faces": body["faces"],
                "face_types": faces,
            },
        )

    sketch = next(
        (row for row in d.get("sketches", []) if row.get("name") == "Slot"),
        None,
    )
    v.check(
        "source Slot remains one solved native sketch profile",
        sketch is not None
        and sketch.get("curves") == 5
        and sketch.get("profiles") == 1
        and sketch.get("status") == "solved",
        {"name": "Slot", "curves": 5, "profiles": 1, "status": "solved"},
        sketch,
    )

    timeline = [
        (row.get("type"), row.get("name"))
        for row in d.get("timeline", [])
    ]
    expected_timeline = [
        ("BoxFeature", "Box1"),
        ("Sketch", "Slot"),
        ("ExtrudeFeature", "Slot"),
        ("RectangularPatternFeature", "RectangularPattern1"),
    ]
    v.check(
        "source cut stays single and pattern is one native History feature",
        timeline == expected_timeline,
        expected_timeline,
        timeline,
    )

    # Q5: mutate the existing saved design, never rerun the Python model.
    # Decreasing columns to 2 lets pitch grow to 30 mm while all four slots
    # remain fully inside the 120 x 80 mm plate.
    m = load(root / "measurements-columns-2-pitch-30.json")
    _check_declared_bounds(
        v,
        m,
        "rectangular-pattern",
        level="q5",
        mutation=True,
        tol=0.01,
    )
    expected_parameters = {
        "columns": 2.0,
        "pitch": 30.0,
        "rows": 2.0,
        "row_pitch": 28.0,
    }
    v.check(
        "pattern parameters changed in saved design",
        params(m) == expected_parameters,
        expected_parameters,
        params(m),
        "q5",
    )
    v.check(
        "mutated pattern remains one body",
        m["body_count"] == 1,
        1,
        m["body_count"],
        "q5",
    )
    if m["bodies"]:
        body = m["bodies"][0]
        slot_volume = (10.0 * 6.0 + math.pi * 3.0**2) * 4.0
        expected_volume = 120.0 * 80.0 * 4.0 - 4.0 * slot_volume
        # 2 columns at X=0,30 and 2 rows at Y=0,28. The plate starts
        # centred at the origin, so subtracting those four cuts shifts the
        # remaining body's centre of mass by a calculable amount.
        expected_center = [
            -(4.0 * slot_volume * 15.0) / expected_volume,
            -(4.0 * slot_volume * 14.0) / expected_volume,
            2.0,
        ]
        faces = body.get("face_types", {})
        v.check(
            "2 x 2 pattern rebuilds four Slot cuts",
            close(body["volume_mm3"], expected_volume, 0.01)
            and body["faces"] == 22
            and faces.get("cylinder") == 8
            and faces.get("plane") == 14,
            {
                "volume_mm3": expected_volume,
                "faces": 22,
                "face_types": {"cylinder": 8, "plane": 14},
            },
            {
                "volume_mm3": body["volume_mm3"],
                "faces": body["faces"],
                "face_types": faces,
            },
            "q5",
        )
        v.check(
            "30 mm pitch moves the rebuilt Slot layout",
            vector_close(body["center_of_mass"], expected_center, 0.001),
            expected_center,
            body["center_of_mass"],
            "q5",
        )

    mutated_sketch = next(
        (row for row in m.get("sketches", []) if row.get("name") == "Slot"),
        None,
    )
    v.check(
        "mutation keeps one solved source Slot profile",
        mutated_sketch is not None
        and mutated_sketch.get("curves") == 5
        and mutated_sketch.get("profiles") == 1
        and mutated_sketch.get("status") == "solved",
        {"name": "Slot", "curves": 5, "profiles": 1, "status": "solved"},
        mutated_sketch,
        "q5",
    )
    mutated_timeline = [
        (row.get("type"), row.get("name"))
        for row in m.get("timeline", [])
    ]
    v.check(
        "mutation keeps one source cut and one native pattern feature",
        mutated_timeline == expected_timeline,
        expected_timeline,
        mutated_timeline,
        "q5",
    )

    return v


def validate_slot_family(root: Path) -> Validation:
    v = Validation("slot-family")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "slot-family", tol=0.01)
    v.check("single cut plate body", d["body_count"] == 1, 1, d["body_count"])
    if d["bodies"]:
        body = d["bodies"][0]
        v.check(
            "plate outer bounds remain unchanged by five slot cuts",
            bbox_close(body, [-80, -60, 0], [80, 60, 5], 0.01),
            {"min": [-80, -60, 0], "max": [80, 60, 5]},
            body["bbox"],
        )
        faces = body.get("face_types", {})
        v.check(
            "five slot cuts remove the qualified amount of material",
            close(body["volume_mm3"], geometry_contract("slot-family")["volume_mm3"], 0.01)
            and body["faces"] == 26
            and faces.get("cylinder") == 14
            and faces.get("plane") == 12,
            {
                "volume_mm3": geometry_contract("slot-family")["volume_mm3"],
                "faces": 26,
                "face_types": {"cylinder": 14, "plane": 12},
            },
            {
                "volume_mm3": body["volume_mm3"],
                "faces": body["faces"],
                "face_types": faces,
            },
        )

    sketch = next(
        (row for row in d.get("sketches", []) if row.get("name") == "Slot family"),
        None,
    )
    v.check(
        "native sketch contains five closed slot profiles",
        sketch is not None
        and sketch.get("profiles") == 5
        and sketch.get("curves") == 29
        and sketch.get("status") == "solved",
        {
            "name": "Slot family",
            "profiles": 5,
            "curves": 29,
            "status": "solved",
        },
        sketch,
    )

    timeline = [
        (row.get("type"), row.get("name"))
        for row in d.get("timeline", [])
    ]
    expected_timeline = [
        ("BoxFeature", "Box1"),
        ("Sketch", "Slot family"),
        ("ExtrudeFeature", "Slot family"),
    ]
    v.check(
        "slot family remains one native sketch plus one cut feature",
        timeline == expected_timeline,
        expected_timeline,
        timeline,
    )
    return v


def validate_rounded_rectangle_sketch(root: Path) -> Validation:
    v = Validation("rounded-rectangle-sketch")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "rounded-rectangle-sketch", tol=0.01)
    v.check("single joined rounded-pad body", d["body_count"] == 1, 1, d["body_count"])
    if d["bodies"]:
        b = d["bodies"][0]
        v.check(
            "rounded sketch pad bounds",
            bbox_close(b, [-40, -30, 0], [40, 30, 13], 0.01),
            {"min": [-40, -30, 0], "max": [40, 30, 13]},
            b["bbox"],
        )
        _check_contract_volume(v, b, "rounded-rectangle-sketch", tol=0.5)
        v.check(
            "four true rounded corner faces",
            b.get("face_types", {}).get("cylinder") == 4,
            4,
            b.get("face_types", {}).get("cylinder"),
        )

    rounded = next(
        (row for row in d.get("sketches", []) if row.get("name") == "Rounded pad"),
        None,
    )
    v.check(
        "rounded pad remains one solved profile with construction diagonal",
        rounded is not None
        and rounded.get("curves") == 9
        and rounded.get("profiles") == 1
        and rounded.get("status") == "solved"
        and rounded.get("dof") == 0,
        {"curves": 9, "profiles": 1, "status": "solved", "dof": 0},
        rounded,
    )

    timeline = [
        (row.get("type"), row.get("name"))
        for row in d.get("timeline", [])
    ]
    expected_timeline = [
        ("BoxFeature", "Box1"),
        ("Sketch", "Rounded pad"),
        ("ExtrudeFeature", "Rounded pad"),
    ]
    v.check(
        "explicit rounded sketch remains distinct native history",
        timeline == expected_timeline,
        expected_timeline,
        timeline,
    )
    return v

def validate_primitive_csg(root: Path) -> Validation:
    v = Validation("primitive-csg")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "primitive-csg", tol=0.01)
    v.check("single resulting CSG body", d["body_count"] == 1, 1, d["body_count"])
    b = d["bodies"][0]
    faces = b.get("face_types", {})
    v.check("sphere survives CSG", faces.get("sphere") == 1, 1, faces.get("sphere"))
    v.check("cylindrical bore survives CSG", faces.get("cylinder") == 1, 1, faces.get("cylinder"))
    expected_min = [-19.595917942265423, -20, 0]
    expected_max = [25, 20, 20]
    v.check(
        "clipped bounds",
        bbox_close(b, expected_min, expected_max, 0.01),
        {"min": expected_min, "max": expected_max},
        b["bbox"],
    )
    return v


def validate_bracket(root: Path) -> Validation:
    v = Validation("bracket")
    d = load(root / "measurements.json")
    _check_declared_bounds(v, d, "bracket")
    b = d["bodies"][0]
    v.check("single L body", d["body_count"] == 1, 1, d["body_count"])
    v.check("L-profile bounds", bbox_close(b, [0, -12, -40], [40, 12, 0]),
            {"min": [0, -12, -40], "max": [40, 12, 0]}, b["bbox"])
    _check_contract_volume(v, b, "bracket")
    return v


VALIDATORS = {
    "simple-box": validate_simple_box,
    "anchored-holes": validate_anchored_holes,
    "parameter-scope": validate_parameter_scope,
    "parent-derived-child-size": validate_parent_derived_child_size,
    "components": validate_components,
    "repeated-parent-attachments": validate_repeated_parent_attachments,
    "assembly-decorator": validate_assembly_decorator,
    "group-hierarchy": validate_group_hierarchy,
    "attach-angle": validate_attach_angle,
    "parametric-attach": validate_parametric_attach,
    "parametric-offset": validate_parametric_offset,
    "parametric-anchor": validate_parametric_anchor,
    "corner-anchor": validate_corner_anchor,
    "assembly-owned-anchor": validate_assembly_owned_anchor,
    "anchor-topology-mutation": validate_anchor_topology_mutation,
    "four-corner-l": validate_four_corner_l,
    "eight-flightcase-corners": validate_eight_flightcase_corners,
    "eight-corner-brackets": validate_eight_corner_brackets,
    "xz-anchor": validate_xz_anchor,
    "circle-negative-extrude": validate_circle_negative_extrude,
    "sketch-pattern-mirror": validate_sketch_pattern_mirror,
    "rectangular-pattern": validate_rectangular_pattern,
    "slot-family": validate_slot_family,
    "rounded-rectangle-sketch": validate_rounded_rectangle_sketch,
    "primitive-csg": validate_primitive_csg,
    "bracket": validate_bracket,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--qualification-dir", type=Path, required=True)
    parser.add_argument(
        "--cases",
        default="all",
        help="comma/space separated case slugs, group:<name>, or all",
    )
    args = parser.parse_args()

    requested = parse_case_selection(args.cases)
    supported = set(supported_case_slugs())
    selected = tuple(case for case in requested if case in supported)
    args.qualification_dir.mkdir(parents=True, exist_ok=True)
    rows = ["case\tq4\tq5\n"]
    summary = {}

    for case in selected:
        validator = VALIDATORS[case]
        result = validator(args.native_root / case).result()
        summary[case] = result
        case_dir = args.native_root / case
        (case_dir / "validation.json").write_text(
            json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
        rows.append(f"{case}\t{result['q4'].upper()}\t{result['q5'].upper()}\n")

    (args.qualification_dir / "native-validation.tsv").write_text(
        "".join(rows), encoding="utf-8"
    )
    (args.qualification_dir / "native-validation.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    failed = [
        case for case, result in summary.items()
        if "fail" in (result["q4"], result["q5"])
    ]
    print(f"Validated {len(summary)} native cases")
    if failed:
        print("Native semantic failures: " + ", ".join(failed))
    # Validation failures are data for the report. A final workflow gate may
    # fail the PR after artifacts and Pages have been published.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
