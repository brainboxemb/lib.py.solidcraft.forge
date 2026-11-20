"""Model-specific declarative verification for slot-family."""

import math

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftSketchExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


SLOT_AREA_SUM = (
    (20.0 * 8.0 + math.pi * 4.0**2)
    + (22.0 * 8.0 + math.pi * 4.0**2)
    + (20.0 * 8.0 + math.pi * 4.0**2)
    + (
        15.153846153846153
        * math.radians(163.65753288010052)
        * 8.0
        + math.pi * 4.0**2
    )
    + (12.0 * math.radians(120.0) * 8.0 + math.pi * 4.0**2)
)

VERIFICATION = SolidCraftVerification(
    verification_id="slot-family",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-80.0, -60.0, 0.0), (80.0, 60.0, 5.0)),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=160.0 * 120.0 * 5.0 - 5.0 * SLOT_AREA_SUM,
                volume_tolerance=0.01,
                face_count=26,
                face_type_counts={"cylinder": 14, "plane": 12},
            ),
        ),
        sketch_count=1,
        sketches=(
            SolidCraftSketchExpectation(
                name="Slot family",
                profiles=5,
                curves=29,
                status="solved",
            ),
        ),
        timeline=(
            SolidCraftTimelineExpectation(
                "BoxFeature", name="Box1", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "Sketch", name="Slot family", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature", name="Slot family", check_name=True,
                check_error=False, check_warning=False,
            ),
        ),
    ),
)
