"""Native SolidCraft verification for revolute-joint."""

from pathlib import Path

from cad_verification import (
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftMeasurementChangeExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="revolute-joint",
    baseline=SolidCraftModelExpectation(
        body_count=2,
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="drive_120",
            command_path=HERE / "drive_120.json",
            expectation=SolidCraftModelExpectation(
                body_count=2,
            ),
            changes=(
                SolidCraftMeasurementChangeExpectation(
                    id="moving_z_changes",
                    path=("bodies", 1, "bbox", "max", 2),
                    minimum_absolute_delta=5.0,
                ),
            ),
        ),
    ),
    inspections=(
        SolidCraftInspection(
            id="joint",
            command_path=HERE / "inspect_joint.json",
            checks=(
                SolidCraftInspectionCheck(
                    id="type",
                    path=("joints", 0, "type"),
                    expected="revolute",
                ),
                SolidCraftInspectionCheck(
                    id="name",
                    path=("joints", 0, "name"),
                    expected="Hinge",
                ),
                SolidCraftInspectionCheck(
                    id="value",
                    path=("joints", 0, "values", 0, "value"),
                    expected=60.0,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="unit",
                    path=("joints", 0, "values", 0, "unit"),
                    expected="deg",
                ),
                SolidCraftInspectionCheck(
                    id="limits",
                    path=("joints", 0, "values", 0, "limits"),
                    expected=[0.0, 180.0],
                ),
            ),
        ),
    ),
)
