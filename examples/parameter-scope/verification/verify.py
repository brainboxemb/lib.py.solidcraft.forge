"""Model-specific declarative verification for parameter-scope."""

from __future__ import annotations

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="parameter-scope",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope((-20.0, -10.0, 0.0), (20.0, 10.0, 10.0)),
            BodyEnvelope((70.0, -10.0, 0.0), (130.0, 10.0, 10.0)),
            BodyEnvelope((180.0, -10.0, 0.0), (260.0, 10.0, 10.0)),
            BodyEnvelope((300.0, -10.0, 0.0), (380.0, 10.0, 10.0)),
            BodyEnvelope((440.0, -10.0, 0.0), (480.0, 10.0, 10.0)),
        ),
        bounds_tolerance=0.001,
        parameters={
            "d1_Panel_width": 40.0,
            "d2_Panel_2_width": 60.0,
            "shared_width": 80.0,
        },
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="shared_width_100",
            command_path=HERE / "change_shared_width.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope((-20.0, -10.0, 0.0), (20.0, 10.0, 10.0)),
                    BodyEnvelope((70.0, -10.0, 0.0), (130.0, 10.0, 10.0)),
                    BodyEnvelope((170.0, -10.0, 0.0), (270.0, 10.0, 10.0)),
                    BodyEnvelope((290.0, -10.0, 0.0), (390.0, 10.0, 10.0)),
                    BodyEnvelope((435.0, -10.0, 0.0), (485.0, 10.0, 10.0)),
                ),
                bounds_tolerance=0.001,
                parameters={"shared_width": 100.0},
                parameter_match="subset",
            ),
        ),
    ),
)
