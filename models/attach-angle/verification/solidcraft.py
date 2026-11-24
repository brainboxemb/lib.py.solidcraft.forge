"""Model-specific CAD verification data for attach-angle."""

from __future__ import annotations

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="attach-angle",
    baseline=SolidCraftModelExpectation(
        body_count=2,
        body_envelopes=(
            BodyEnvelope(
                (-30.0, -30.0, 0.0),
                (30.0, 30.0, 10.0),
            ),
            BodyEnvelope(
                (-5.0, -15.0, 10.0),
                (5.0, 15.0, 16.0),
            ),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                name_prefix="Arm",
                minimum=(-5.0, -15.0, 10.0),
                maximum=(5.0, 15.0, 16.0),
                bounds_tolerance=0.001,
            ),
        ),
    ),
)
