"""Model-specific CAD verification data for as-built-attach."""

from cad_verification import BodyEnvelope, SolidCraftModelExpectation, SolidCraftVerification

VERIFICATION = SolidCraftVerification(
    verification_id="as-built-attach",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope((-20.0, -15.0, -5.0), (20.0, 15.0, 5.0)),
            BodyEnvelope((45.0, 5.0, 11.0), (55.0, 35.0, 19.0)),
        ),
        bounds_tolerance=0.001,
    ),
)
