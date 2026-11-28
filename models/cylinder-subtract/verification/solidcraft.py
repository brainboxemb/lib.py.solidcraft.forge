"""Native SolidCraft verification for Cylinder subtract IR."""


from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="cylinder-subtract",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope(
                (-30.0, -20.0, 0.0),
                (30.0, 20.0, 12.0),
            ),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                closed=True,
                face_type_counts={"cylinder": 1},
            ),
        ),
    ),
)
