"""Native SolidCraft verification for Cone Boolean feature compilation."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="cone-boolean",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope(
                (-25.0, -20.0, 0.0),
                (25.0, 20.0, 26.0),
            ),
        ),
        bounds_tolerance=0.01,
    ),
)
