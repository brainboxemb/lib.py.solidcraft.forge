"""Native SolidCraft verification for revolute-joint."""

from pathlib import Path

from cad_verification import (
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="revolute-joint",
    baseline=SolidCraftModelExpectation(
        body_count=1,
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
        SolidCraftInspection(
            id="drive_120",
            command_path=HERE / "drive_120.json",
            checks=(
                SolidCraftInspectionCheck(
                    id="moved",
                    path=("moved",),
                    expected=True,
                ),
                SolidCraftInspectionCheck(
                    id="value",
                    path=("values", 0, "value"),
                    expected=120.0,
                    tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="unit",
                    path=("values", 0, "unit"),
                    expected="deg",
                ),
                SolidCraftInspectionCheck(
                    id="limits",
                    path=("values", 0, "limits"),
                    expected=[0.0, 180.0],
                ),
            ),
        ),
    ),
)
