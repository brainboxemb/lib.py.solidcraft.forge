"""Native Free/Installed physical-state qualification."""
from pathlib import Path

from cad_verification import (
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftInspectionSelect,
    SolidCraftMeasurementChangeExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)

HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="configuration-installed-state",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        parameters={"fit_diameter": 20.4},
        parameter_match="subset",
    ),
    inspections=(
        SolidCraftInspection(
            id="table",
            command_path=HERE / "table.json",
            checks=(
                SolidCraftInspectionCheck(id="rows", path=(0, "rows"), count=2),
                SolidCraftInspectionCheck(id="active", path=(0, "active"), expected="Free"),
                SolidCraftInspectionCheck(id="matches", path=(0, "matches"), expected=True),
                SolidCraftInspectionCheck(
                    id="free-diameter",
                    path=(
                        0,
                        "rows",
                        SolidCraftInspectionSelect("name", "Free"),
                        "values",
                        "param:fit_diameter",
                    ),
                    expected="20.4 mm",
                ),
                SolidCraftInspectionCheck(
                    id="installed-diameter",
                    path=(
                        0,
                        "rows",
                        SolidCraftInspectionSelect("name", "Installed"),
                        "values",
                        "param:fit_diameter",
                    ),
                    expected="20.0 mm",
                ),
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="installed",
            command_path=HERE / "installed.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                parameters={"fit_diameter": 20.0},
                parameter_match="subset",
            ),
            changes=(
                SolidCraftMeasurementChangeExpectation(
                    id="physical-geometry",
                    path=("bodies", 0, "volume_mm3"),
                    minimum_absolute_delta=1.0,
                ),
            ),
        ),
    ),
)
