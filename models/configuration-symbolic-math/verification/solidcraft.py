"""Native symbolic-math configuration qualification."""
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
    verification_id="configuration-symbolic-math",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope(
                (-33.5410196625, -33.75, 0.0),
                (33.5410196625, 33.75, 9.0),
            ),
        ),
        bounds_tolerance=0.002,
        parameters={"size": 70.0},
        parameter_match="subset",
    ),
    inspections=(
        SolidCraftInspection(
            id="table",
            command_path=HERE / "table.json",
            checks=(
                SolidCraftInspectionCheck(id="rows", path=(0, "rows"), count=3),
                SolidCraftInspectionCheck(id="active", path=(0, "active"), expected="Medium"),
                SolidCraftInspectionCheck(id="matches", path=(0, "matches"), expected=True),
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="small",
            command_path=HERE / "small.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope(
                        (-28.2842712475, -30.0, 0.0),
                        (28.2842712475, 30.0, 9.0),
                    ),
                ),
                bounds_tolerance=0.002,
                parameters={"size": 60.0},
                parameter_match="subset",
            ),
        ),
        SolidCraftSavedDesign(
            id="large",
            command_path=HERE / "large.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope(
                        (-38.7298334621, -48.75, 0.0),
                        (38.7298334621, 48.75, 12.0),
                    ),
                ),
                bounds_tolerance=0.002,
                parameters={"size": 100.0},
                parameter_match="subset",
            ),
        ),
    ),
)
