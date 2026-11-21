"""Model-specific CAD verification data for rotated-copy-placement."""

from cad_verification import BodyEnvelope, SolidCraftModelExpectation, SolidCraftVerification

VERIFICATION = SolidCraftVerification(
    verification_id="rotated-copy-placement",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope((-45.0, -10.0, -2.0), (-35.0, 10.0, 2.0)),
            BodyEnvelope((35.0, -10.0, -2.0), (45.0, 10.0, 2.0)),
        ),
        bounds_tolerance=0.001,
    ),
)
