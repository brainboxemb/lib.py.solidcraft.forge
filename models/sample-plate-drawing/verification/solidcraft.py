"""Native qualification for the Sample Plate Drawing example."""

from cad_verification import (
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="sample-plate-drawing",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        named_bodies=(
            SolidCraftBodyExpectation(closed=True),
        ),
    ),
)
