"""Model-specific declarative verification for top-sketch-after-chamfer."""

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftSketchExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="top-sketch-after-chamfer",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-50.0, -35.0, 0.0), (50.0, 35.0, 10.0)),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=67589.02664470767,
                volume_tolerance=0.5,
                face_type_counts={"cylinder": 1},
            ),
        ),
        sketch_count=1,
        sketches=(
            SolidCraftSketchExpectation(name="Top hole", status="solved"),
        ),
        timeline=(
            SolidCraftTimelineExpectation(
                "BoxFeature", check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ChamferFeature", check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "Sketch", check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature", check_error=False, check_warning=False,
            ),
        ),
    ),
)
