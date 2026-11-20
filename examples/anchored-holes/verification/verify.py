"""Model-specific declarative verification for anchored-holes."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="anchored-holes",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((0.0, 0.0, 0.0), (100.0, 60.0, 10.0)),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=58994.69035085127,
                volume_tolerance=0.5,
                face_type_counts={"cylinder": 2},
            ),
        ),
        timeline=(
            SolidCraftTimelineExpectation(
                "Sketch", name="Base", check_name=True,
                check_error=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature", check_error=False,
            ),
            SolidCraftTimelineExpectation(
                "Sketch", name="Hole", check_name=True,
                check_error=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature", name="Hole", check_name=True,
                check_error=False,
            ),
            SolidCraftTimelineExpectation(
                "RectangularPatternFeature",
                name="RectangularPattern1",
                check_name=True,
                check_error=False,
            ),
        ),
    ),
)
