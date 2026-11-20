"""Model-specific declarative verification for circle-negative-extrude."""

import math

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="circle-negative-extrude",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-10.0, -10.0, -30.0), (10.0, 10.0, 0.0)),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=math.pi * 10.0**2 * 30.0,
                volume_tolerance=0.5,
                face_type_counts={"cylinder": 1},
            ),
        ),
        timeline=(
            SolidCraftTimelineExpectation(
                "Sketch", name="Profile", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature", name="Extrude1", check_name=True,
                check_error=False, check_warning=False,
            ),
        ),
    ),
)
