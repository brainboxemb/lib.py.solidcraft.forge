"""Model-specific declarative verification for assembly-decorator."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="assembly-decorator",
    baseline=SolidCraftModelExpectation(
        body_count=2,
        body_envelopes=(
            BodyEnvelope((-20.0, -5.0, 0.0), (-10.0, 5.0, 20.0)),
            BodyEnvelope((10.0, -5.0, 0.0), (20.0, 5.0, 20.0)),
        ),
    ),
)
