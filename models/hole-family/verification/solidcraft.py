"""Model-specific declarative verification for hole-family."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="hole-family",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-60.0, -20.0, 0.0), (60.0, 20.0, 12.0)),
        ),
        bounds_tolerance=0.01,
        timeline_type_counts={"HoleFeature": 4},
        sketch_count=0,
    ),
)
