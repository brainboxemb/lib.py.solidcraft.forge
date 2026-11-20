"""Model-specific declarative verification for bracket."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="bracket",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((0.0, -12.0, -40.0), (40.0, 12.0, 0.0)),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=19584.0,
                volume_tolerance=1.0,
            ),
        ),
    ),
)
