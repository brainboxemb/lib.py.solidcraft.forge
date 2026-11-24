"""Model-specific declarative verification for components."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyGroupExpectation,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="components",
    baseline=SolidCraftModelExpectation(
        body_groups=(
            SolidCraftBodyGroupExpectation(
                name_prefix="Block",
                count=2,
                body_envelopes=(
                    BodyEnvelope((-20.0, -15.0, 0.0), (20.0, 15.0, 10.0)),
                    BodyEnvelope((20.0, -15.0, 0.0), (60.0, 15.0, 10.0)),
                ),
                bounds_tolerance=0.001,
            ),
        ),
    ),
)
