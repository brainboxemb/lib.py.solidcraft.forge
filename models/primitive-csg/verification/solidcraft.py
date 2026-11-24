"""Model-specific declarative verification for primitive-csg."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="primitive-csg",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope(
                (-19.595917942265423, -20.0, 0.0),
                (25.0, 20.0, 20.0),
            ),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                face_type_counts={"sphere": 1, "cylinder": 1},
            ),
        ),
    ),
)
