"""Native SolidCraft verification for rotated-sketch-cutter."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="rotated-sketch-cutter",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-30.0, -30.0, -15.0), (30.0, 30.0, 15.0)),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=107488.0,
                volume_tolerance=1.0,
            ),
        ),
    ),
)
