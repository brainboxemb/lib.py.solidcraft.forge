"""Native SolidCraft verification for attached-through-all."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="attached-through-all",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-40.0, -30.0, 0.0), (40.0, 30.0, 5.0)),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=22400.0,
                volume_tolerance=0.5,
            ),
        ),
    ),
)
