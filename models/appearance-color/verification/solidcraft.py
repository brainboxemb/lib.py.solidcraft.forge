"""Native SolidCraft verification for appearance-color."""

from pathlib import Path

from cad_verification import (
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="appearance-color",
    baseline=SolidCraftModelExpectation(
        body_count=1,
    ),
    inspections=(
        SolidCraftInspection(
            id="appearance",
            command_path=HERE / "inspect_appearance.json",
            checks=(
                SolidCraftInspectionCheck(
                    id="active",
                    path=(0, "active"),
                    expected="body",
                ),
                SolidCraftInspectionCheck(
                    id="color",
                    path=(0, "steps", 0, "look", "color"),
                    expected="#FFD21A",
                ),
            ),
        ),
    ),
)
