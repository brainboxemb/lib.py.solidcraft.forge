"""Native saved-design verification for the #682 edge-flange fixture."""

from __future__ import annotations

from pathlib import Path
import math

from cad_verification import (
    SolidCraftBodyExpectation,
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftSketchExpectation,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

COMMON_BODY = SolidCraftBodyExpectation(
    sheet_metal=True,
    closed=True,
)

COMMON_SKETCH = SolidCraftSketchExpectation(
    name="Blank",
    profiles=1,
    curves=4,
    status="solved",
)


VERIFICATION = SolidCraftVerification(
    verification_id="sheet-edge-flange",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        parameters={
            "width": 80.0,
            "depth": 40.0,
            "thickness": 2.0,
            "bend_radius": 2.0,
            "k_factor": 0.5,
            "flange_height": 20.0,
            "flange_angle": math.radians(90.0),
        },
        parameter_match="subset",
        named_bodies=(COMMON_BODY,),
        sketch_count=1,
        sketches=(COMMON_SKETCH,),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="resize_edge_flange",
            command_path=HERE / "change_flange.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                parameters={
                    "flange_height": 25.0,
                    "flange_angle": math.radians(75.0),
                },
                parameter_match="subset",
                named_bodies=(COMMON_BODY,),
                sketch_count=1,
                sketches=(COMMON_SKETCH,),
            ),
        ),
    ),
    inspections=(
        SolidCraftInspection(
            id="flat_pattern",
            command_path=HERE / "inspect_flat_pattern.json",
            checks=(
                SolidCraftInspectionCheck(id="result_count", count=1),
                SolidCraftInspectionCheck(
                    id="bend_count",
                    path=(0, "bends"),
                    count=1,
                ),
                SolidCraftInspectionCheck(
                    id="bend_angle",
                    path=(0, "bends", 0, "angle_deg"),
                    expected=90.0,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="bend_radius",
                    path=(0, "bends", 0, "radius"),
                    expected=2.0,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="sheet_rule",
                    path=(0, "rule"),
                    expected="Edge Flange Rule",
                ),
                SolidCraftInspectionCheck(
                    id="sheet_thickness",
                    path=(0, "thickness"),
                    expected=2.0,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="sheet_k_factor",
                    path=(0, "k_factor"),
                    expected=0.5,
                    tolerance=0.001,
                ),
            ),
        ),
    ),
)
