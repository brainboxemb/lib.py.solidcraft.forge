"""Native size-row plus independent Installed-rule qualification."""
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
        body_count=2,
        parameters={
            "frame_width": 80.0,
            "tube_d": 20.0,
            "fit_diameter": 20.0,
        },
        parameter_match="subset",
    ),
    inspections=(
        SolidCraftInspection(
            id="table",
            command_path=HERE / "table.json",
            checks=(
                SolidCraftInspectionCheck(id="rows", path=(0, "rows"), count=3),
                SolidCraftInspectionCheck(id="rules", path=(0, "rules"), count=1),
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
                    id="medium-free-cell",
                    path=(
                        0,
                        "rows",
                        SolidCraftInspectionSelect("name", "Medium"),
                        "values",
                        "param:fit_diameter",
                    ),
                    expected="20.4 mm",
                ),
                SolidCraftInspectionCheck(
                    id="installed-enabled",
                    path=(
                        0,
                        "rules",
                        SolidCraftInspectionSelect("id", "installed"),
                        "enabled",
                    ),
                    expected=True,
                ),
                SolidCraftInspectionCheck(
                    id="installed-name",
                    path=(
                        0,
                        "rules",
                        SolidCraftInspectionSelect("id", "installed"),
                        "name",
                    ),
                    expected="Installed",
                ),
                SolidCraftInspectionCheck(
                    id="installed-target",
                    path=(
                        0,
                        "rules",
                        SolidCraftInspectionSelect("id", "installed"),
                        "effect",
                        "parameter",
                    ),
                    expected="fit_diameter",
                ),
                SolidCraftInspectionCheck(
                    id="installed-expression",
                    path=(
                        0,
                        "rules",
                        SolidCraftInspectionSelect("id", "installed"),
                        "effect",
                        "expression",
                    ),
                    expected="tube_d",
                ),
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="free",
            command_path=HERE / "free.json",
            expectation=SolidCraftModelExpectation(
                body_count=2,
                parameters={
                    "frame_width": 80.0,
                    "tube_d": 20.0,
                    "fit_diameter": 20.4,
                },
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
        SolidCraftSavedDesign(
            id="large-installed",
            command_path=HERE / "large_installed.json",
            expectation=SolidCraftModelExpectation(
                body_count=2,
                parameters={
                    "frame_width": 100.0,
                    "tube_d": 20.0,
                    "fit_diameter": 20.0,
                },
                parameter_match="subset",
            ),
        ),
        SolidCraftSavedDesign(
            id="large-free",
            command_path=HERE / "large_free.json",
            expectation=SolidCraftModelExpectation(
                body_count=2,
                parameters={
                    "frame_width": 100.0,
                    "tube_d": 20.0,
                    "fit_diameter": 20.4,
                },
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
