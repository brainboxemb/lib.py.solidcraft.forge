"""Native shifted-axis revolve and exact suppression qualification."""
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
    verification_id="shifted-axis-revolve",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        parameters={"axis_x": 8.0, "axis_z": 3.0},
        parameter_match="subset",
    ),
    inspections=(
        SolidCraftInspection(
            id="table",
            command_path=HERE / "table.json",
            checks=(
                SolidCraftInspectionCheck(id="rows", path=(0, "rows"), count=2),
                SolidCraftInspectionCheck(id="columns", path=(0, "columns"), count=1),
                SolidCraftInspectionCheck(id="active", path=(0, "active"), expected="Cut"),
                SolidCraftInspectionCheck(id="matches", path=(0, "matches"), expected=True),
            ),
        ),
        SolidCraftInspection(
            id="revolve-axis",
            command_path=HERE / "revolve.json",
            checks=(
                SolidCraftInspectionCheck(
                    id="axis-x",
                    path=(0, "definition", "axis", "origin", 0),
                    expected="axis_x",
                ),
                SolidCraftInspectionCheck(
                    id="axis-z",
                    path=(0, "definition", "axis", "origin", 2),
                    expected="axis_z",
                ),
                SolidCraftInspectionCheck(
                    id="axis-dir",
                    path=(0, "definition", "axis", "dir"),
                    expected=[0.0, 1.0, 0.0],
                ),
                SolidCraftInspectionCheck(
                    id="axis-type",
                    path=(0, "definition", "axis", "type"),
                    expected="line",
                ),
                SolidCraftInspectionCheck(
                    id="operation",
                    path=(0, "definition", "operation"),
                    expected="cut",
                ),
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="suppressed",
            command_path=HERE / "suppressed.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                parameters={"axis_x": 8.0, "axis_z": 3.0},
                parameter_match="subset",
            ),
            changes=(
                SolidCraftMeasurementChangeExpectation(
                    id="whole-revolve-cut",
                    path=("bodies", 0, "volume_mm3"),
                    minimum_absolute_delta=10.0,
                ),
            ),
        ),
    ),
)
