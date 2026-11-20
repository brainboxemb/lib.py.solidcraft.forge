"""Model-specific verification data for the simple-box example."""

from __future__ import annotations

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent


VERIFICATION = SolidCraftVerification(
    verification_id="simple-box",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope(
                (-20.0, -15.0, 0.0),
                (20.0, 15.0, 10.0),
            ),
        ),
        bounds_tolerance=0.000001,
        parameters={
            "length": 40.0,
            "width": 30.0,
            "height": 10.0,
        },
        timeline=(
            SolidCraftTimelineExpectation(
                feature_type="BoxFeature",
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="length_50",
            command_path=HERE / "change_length.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                body_envelopes=(
                    BodyEnvelope(
                        (-25.0, -15.0, 0.0),
                        (25.0, 15.0, 10.0),
                    ),
                ),
                bounds_tolerance=0.000001,
                parameters={
                    "length": 50.0,
                    "width": 30.0,
                    "height": 10.0,
                },
            ),
        ),
    ),
)
