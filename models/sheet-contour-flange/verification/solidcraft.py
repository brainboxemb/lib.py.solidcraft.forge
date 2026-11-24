"""Native saved-design verification for the #684 contour-flange fixture."""

from __future__ import annotations

from pathlib import Path

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
    name="Contour",
    profiles=0,
    curves=3,
)


VERIFICATION = SolidCraftVerification(
    verification_id="sheet-contour-flange",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        parameters={
            "end_height": 30.0,
            "contour_width": 50.0,
            "thickness": 2.5,
            "bend_radius": 2.5,
            "k_factor": 0.44,
        },
        parameter_match="subset",
        named_bodies=(COMMON_BODY,),
        sketch_count=1,
        sketches=(COMMON_SKETCH,),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="resize_contour_flange",
            command_path=HERE / "change_contour.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                parameters={
                    "contour_width": 60.0,
                    "end_height": 35.0,
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
                    id="sheet_rule",
                    path=(0, "rule"),
                    expected="Contour Flange Rule",
                ),
                SolidCraftInspectionCheck(
                    id="sheet_thickness",
                    path=(0, "thickness"),
                    expected=2.5,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="sheet_k_factor",
                    path=(0, "k_factor"),
                    expected=0.44,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="bend_count",
                    path=(0, "bends"),
                    count=0,
                ),
            ),
        ),
    ),
)
