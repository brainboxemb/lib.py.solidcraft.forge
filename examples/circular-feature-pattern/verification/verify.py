"""Model-specific declarative verification for circular-feature-pattern."""

from __future__ import annotations

import math
from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftSketchExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

TIMELINE = (
    SolidCraftTimelineExpectation(
        "BoxFeature", name="Box1", check_name=True,
        check_error=False, check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "Sketch", name="BoltHole", check_name=True,
        check_error=False, check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "ExtrudeFeature", name="BoltHole", check_name=True,
        check_error=False, check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "CircularPatternFeature", name="CircularPattern1", check_name=True,
        check_error=False, check_warning=False,
    ),
)

VERIFICATION = SolidCraftVerification(
    verification_id="circular-feature-pattern",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-50.0, -50.0, 0.0), (50.0, 50.0, 6.0)),
        ),
        bounds_tolerance=0.01,
        parameters={"bolts": 6.0, "pcd": 60.0},
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=100.0 * 100.0 * 6.0 - 6.0 * math.pi * 4.0**2 * 6.0,
                volume_tolerance=0.01,
                face_type_counts={"cylinder": 6},
            ),
        ),
        sketches=(
            SolidCraftSketchExpectation(
                name="BoltHole", curves=1, profiles=1, status="solved",
            ),
        ),
        timeline=TIMELINE,
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="bolts_4",
            command_path=HERE / "change_count.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                parameters={"bolts": 4.0, "pcd": 60.0},
                named_bodies=(
                    SolidCraftBodyExpectation(
                        volume_mm3=100.0 * 100.0 * 6.0 - 4.0 * math.pi * 4.0**2 * 6.0,
                        volume_tolerance=0.01,
                        face_type_counts={"cylinder": 4},
                    ),
                ),
                timeline=TIMELINE,
            ),
        ),
    ),
)
