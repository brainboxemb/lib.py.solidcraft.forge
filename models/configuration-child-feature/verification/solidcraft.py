"""Native qualification for parent-owned suppression of a reusable-child feature."""
from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftMeasurementChangeExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)

HERE = Path(__file__).resolve().parent

MEDIUM = (
    BodyEnvelope((-70.0, -12.0, 0.0), (-30.0, 12.0, 12.0)),
    BodyEnvelope((30.0, -12.0, 0.0), (70.0, 12.0, 12.0)),
)
SMALL = (
    BodyEnvelope((-65.0, -12.0, 0.0), (-35.0, 12.0, 12.0)),
    BodyEnvelope((35.0, -12.0, 0.0), (65.0, 12.0, 12.0)),
)

VERIFICATION = SolidCraftVerification(
    verification_id="configuration-child-feature",
    baseline=SolidCraftModelExpectation(
        body_count=2,
        body_envelopes=MEDIUM,
        bounds_tolerance=0.001,
        parameters={"coupler_width": 40.0},
        parameter_match="subset",
    ),
    inspections=(
        SolidCraftInspection(
            id="table",
            command_path=HERE / "table.json",
            checks=(
                SolidCraftInspectionCheck(id="rows", path=(0, "rows"), count=3),
                SolidCraftInspectionCheck(id="columns", path=(0, "columns"), count=2),
                SolidCraftInspectionCheck(
                    id="active",
                    path=(0, "active"),
                    expected="Medium",
                ),
                SolidCraftInspectionCheck(
                    id="matches",
                    path=(0, "matches"),
                    expected=True,
                ),
                SolidCraftInspectionCheck(
                    id="small-width",
                    path=(0, "rows", 0, "values", "param:coupler_width"),
                    expected="30 mm",
                ),
                SolidCraftInspectionCheck(
                    id="medium-width",
                    path=(0, "rows", 1, "values", "param:coupler_width"),
                    expected="40 mm",
                ),
                SolidCraftInspectionCheck(
                    id="large-width",
                    path=(0, "rows", 2, "values", "param:coupler_width"),
                    expected="40 mm",
                ),
                SolidCraftInspectionCheck(
                    id="small-suppression",
                    path=(0, "rows", 0, "values", "suppress:Hole1"),
                    expected="true",
                ),
                SolidCraftInspectionCheck(
                    id="medium-suppression",
                    path=(0, "rows", 1, "values", "suppress:Hole1"),
                    expected="true",
                ),
                SolidCraftInspectionCheck(
                    id="large-suppression",
                    path=(0, "rows", 2, "values", "suppress:Hole1"),
                    expected="false",
                ),
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="small",
            command_path=HERE / "small.json",
            expectation=SolidCraftModelExpectation(
                body_count=2,
                body_envelopes=SMALL,
                bounds_tolerance=0.001,
                parameters={"coupler_width": 30.0},
                parameter_match="subset",
            ),
        ),
        SolidCraftSavedDesign(
            id="large",
            command_path=HERE / "large.json",
            expectation=SolidCraftModelExpectation(
                body_count=2,
                body_envelopes=MEDIUM,
                bounds_tolerance=0.001,
                parameters={"coupler_width": 40.0},
                parameter_match="subset",
            ),
            changes=(
                SolidCraftMeasurementChangeExpectation(
                    id="child-feature-geometry",
                    path=("bodies", 0, "volume_mm3"),
                    minimum_absolute_delta=1.0,
                ),
            ),
        ),
    ),
)
