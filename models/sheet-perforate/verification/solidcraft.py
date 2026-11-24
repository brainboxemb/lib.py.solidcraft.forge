"""Native saved-design verification for the #779 perforation case."""

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
    name="Blank",
    profiles=1,
    curves=4,
    status="solved",
)


VERIFICATION = SolidCraftVerification(
    verification_id="sheet-perforate",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        parameters={
            "width": 60.0,
            "depth": 40.0,
            "thickness": 2.0,
            "bend_radius": 2.0,
            "k_factor": 0.5,
            "perforation_diameter": 5.0,
            "perforation_pitch": 10.0,
            "perforation_margin": 5.0,
        },
        parameter_match="subset",
        named_bodies=(COMMON_BODY,),
        sketch_count=1,
        sketches=(COMMON_SKETCH,),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="resize_perforation",
            command_path=HERE / "change_perforation.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                parameters={
                    "perforation_diameter": 6.0,
                    "perforation_pitch": 12.0,
                    "perforation_margin": 6.0,
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
                    id="perforation_count",
                    path=(0, "perforations", 0, "count"),
                    expected=15,
                ),
                SolidCraftInspectionCheck(
                    id="perforation_diameter",
                    path=(0, "perforations", 0, "diameter"),
                    expected=5.0,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="perforation_pitch",
                    path=(0, "perforations", 0, "pitch"),
                    expected=10.0,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="perforation_margin",
                    path=(0, "perforations", 0, "margin"),
                    expected=5.0,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="perforation_pattern",
                    path=(0, "perforations", 0, "pattern"),
                    expected="square",
                ),
                SolidCraftInspectionCheck(
                    id="perforation_open_area",
                    path=(0, "perforations", 0, "open_area_mm2"),
                    expected=294.5243112740431,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="sheet_rule",
                    path=(0, "rule"),
                    expected="Perforation Rule",
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
