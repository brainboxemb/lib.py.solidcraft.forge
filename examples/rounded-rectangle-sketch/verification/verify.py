"""Model-specific declarative verification for rounded-rectangle-sketch."""

import math

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftSketchExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="rounded-rectangle-sketch",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-40.0, -30.0, 0.0), (40.0, 30.0, 13.0)),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=(
                    80.0 * 60.0 * 5.0
                    + (40.0 * 30.0 - (4.0 - math.pi) * 5.0**2) * 8.0
                ),
                volume_tolerance=0.5,
                face_type_counts={"cylinder": 4},
            ),
        ),
        sketch_count=1,
        sketches=(
            SolidCraftSketchExpectation(
                name="Rounded pad",
                curves=9,
                profiles=1,
                status="solved",
                dof=0,
            ),
        ),
        timeline=(
            SolidCraftTimelineExpectation(
                "BoxFeature", name="Box1", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "Sketch", name="Rounded pad", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature", name="Rounded pad", check_name=True,
                check_error=False, check_warning=False,
            ),
        ),
    ),
)
