"""Model-specific CAD verification data for parametric-offset."""

from __future__ import annotations

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="parametric-offset",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope(
                (-20.0, -15.0, 0.0),
                (20.0, 15.0, 20.0),
            ),
            BodyEnvelope(
                (10.0, -25.0, 15.0),
                (20.0, -15.0, 25.0),
            ),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                name_prefix="Marker",
                minimum=(10.0, -25.0, 15.0),
                maximum=(20.0, -15.0, 25.0),
                bounds_tolerance=0.001,
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="shift_10",
            command_path=HERE / "change_shift.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope(
                        (-20.0, -15.0, 0.0),
                        (20.0, 15.0, 20.0),
                    ),
                    BodyEnvelope(
                        (10.0, -25.0, 20.0),
                        (20.0, -15.0, 30.0),
                    ),
                ),
                bounds_tolerance=0.001,
                named_bodies=(
                    SolidCraftBodyExpectation(
                        name_prefix="Marker",
                        minimum=(10.0, -25.0, 20.0),
                        maximum=(20.0, -15.0, 30.0),
                        bounds_tolerance=0.001,
                    ),
                ),
            ),
        ),
    ),
)
