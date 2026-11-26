"""Native configuration-table qualification; inspect the saved design and switch rows."""
from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
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
                SolidCraftInspectionCheck(id="matches", path=(0, "matches"), expected=True),
                SolidCraftInspectionCheck(id="row-small", path=(0, "rows", 0, "name"), expected="Small"),
                SolidCraftInspectionCheck(id="row-medium", path=(0, "rows", 1, "name"), expected="Medium"),
                SolidCraftInspectionCheck(id="row-large", path=(0, "rows", 2, "name"), expected="Large"),
                SolidCraftInspectionCheck(id="small-suppress-a", path=(0, "rows", 0, "values", "suppress:Hole1"), expected="true"),
                SolidCraftInspectionCheck(id="medium-suppress-a", path=(0, "rows", 1, "values", "suppress:Hole1"), expected="true"),
                SolidCraftInspectionCheck(id="large-suppress-a", path=(0, "rows", 2, "values", "suppress:Hole1"), expected="false"),
                SolidCraftInspectionCheck(id="large-width", path=(0, "rows", 2, "values", "param:width"), expected="100 mm"),
            ),
        ),
        SolidCraftInspection(
            id="switch",
            command_path=HERE / "switch.json",
            checks=(
                SolidCraftInspectionCheck(id="active", path=(1, "active"), expected="Large"),
                SolidCraftInspectionCheck(id="matches", path=(1, "matches"), expected=True),
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="large",
            command_path=HERE / "switch_large.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope((-50.0, -25.0, 0.0), (50.0, 25.0, 6.0)),
                ),
                bounds_tolerance=0.001,
                parameters={
                    "width": 100.0,
                    "depth": 50.0,
                    "thickness": 6.0,
                    "diameter": 6.0,
                },
                parameter_match="subset",
            ),
        ),
    ),
)
