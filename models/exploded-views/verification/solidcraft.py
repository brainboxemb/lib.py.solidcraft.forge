"""Declarative native verification for exploded assembly views."""

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyGroupExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

ASSEMBLED = SolidCraftModelExpectation(
    body_groups=(
        SolidCraftBodyGroupExpectation(
            name_prefix="ExplodeBlock",
            count=3,
            body_envelopes=(
                BodyEnvelope((-15.0, -10.0, 0.0), (15.0, 10.0, 10.0)),
                BodyEnvelope((25.0, -10.0, 0.0), (55.0, 10.0, 10.0)),
                BodyEnvelope((65.0, -10.0, 0.0), (95.0, 10.0, 10.0)),
            ),
            bounds_tolerance=0.001,
        ),
    ),
)


VERIFICATION = SolidCraftVerification(
    verification_id="exploded-views",
    baseline=ASSEMBLED,
    saved_designs=(
        SolidCraftSavedDesign(
            id="show_automatic",
            command_path=HERE / "show_automatic.json",
            expectation=ASSEMBLED,
        ),
        SolidCraftSavedDesign(
            id="show_instructions_then_assembled",
            command_path=HERE / "show_instructions_then_assembled.json",
            expectation=ASSEMBLED,
        ),
    ),
)
