"""Native proof that size rows and Installed rule state stay independent."""
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


def expected(*, height, fit):
    return SolidCraftModelExpectation(
        body_count=1,
        parameters={
            "tube_d": 20.0,
            "clamp_interference": 0.2,
            "sleeve_height": height,
            "fit_diameter": fit,
        },
        parameter_match="subset",
    )


def changed_geometry(change_id):
    return (
        SolidCraftMeasurementChangeExpectation(
            id=change_id,
            path=("bodies", 0, "volume_mm3"),
            minimum_absolute_delta=1.0,
        ),
    )


VERIFICATION = SolidCraftVerification(
    verification_id="configuration-installed-state",
    baseline=expected(height=30.0, fit=19.8),
    inspections=(
        SolidCraftInspection(
            id="table",
            command_path=HERE / "table.json",
            checks=(
                SolidCraftInspectionCheck(id="rows", path=(0, "rows"), count=3),
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
                    id="medium-size",
                    path=(
                        0,
                        "rows",
                        SolidCraftInspectionSelect("name", "Medium"),
                        "values",
                        "param:sleeve_height",
                    ),
                    expected="30 mm",
                ),
                SolidCraftInspectionCheck(
                    id="medium-free-fit",
                    path=(
                        0,
                        "rows",
                        SolidCraftInspectionSelect("name", "Medium"),
                        "values",
                        "param:fit_diameter",
                    ),
                    expected="tube_d - clamp_interference",
                ),
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="installed-medium",
            command_path=HERE / "installed.json",
            expectation=expected(height=30.0, fit=20.0),
            changes=changed_geometry("installed-fit"),
        ),
        SolidCraftSavedDesign(
            id="installed-large",
            command_path=HERE / "installed-large.json",
            expectation=expected(height=40.0, fit=20.0),
            changes=changed_geometry("installed-large-geometry"),
        ),
        SolidCraftSavedDesign(
            id="free-large",
            command_path=HERE / "free-large.json",
            expectation=expected(height=40.0, fit=19.8),
            changes=changed_geometry("free-large-geometry"),
        ),
    ),
)
