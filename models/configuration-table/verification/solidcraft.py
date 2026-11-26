"""Native configuration-table qualification; inspect the saved design and switch rows."""
from pathlib import Path

from cad_verification import (
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)

HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="configuration-table",
    baseline=SolidCraftModelExpectation(body_count=1),
    inspections=(
        SolidCraftInspection(
            id="table",
            command_path=HERE / "table.json",
            checks=(
                SolidCraftInspectionCheck(id="row-count", path=(0, "rows"), count=3),
                SolidCraftInspectionCheck(id="column-count", path=(0, "columns"), count=6),
                SolidCraftInspectionCheck(id="active", path=(0, "active"), expected="Medium"),
            ),
        ),
        SolidCraftInspection(
            id="switch",
            command_path=HERE / "switch.json",
            checks=(
                SolidCraftInspectionCheck(id="active", path=(1, "active"), expected="Large"),
            ),
        ),
    ),
)
