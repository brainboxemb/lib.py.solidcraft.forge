"""Model-specific declarative verification for round-top-sketch."""

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
    verification_id="round-top-sketch",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-50.0, -50.0, 0.0), (50.0, 50.0, 26.0)),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=math.pi * 50.0**2 * 10.0 + math.pi * 22.0**2 * 16.0,
                volume_tolerance=0.5,
                face_type_counts={"cylinder": 2},
            ),
        ),
        sketch_count=2,
        sketches=(
            SolidCraftSketchExpectation(name="Disc", status="solved"),
            SolidCraftSketchExpectation(name="Hub", status="solved"),
        ),
        timeline=(
            SolidCraftTimelineExpectation(
                "Sketch", name="Disc", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature", name="Extrude1", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "Sketch", name="Hub", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature", name="Hub", check_name=True,
                check_error=False, check_warning=False,
            ),
        ),
    ),
)
