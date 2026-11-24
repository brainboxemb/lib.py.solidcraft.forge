"""Model-specific declarative verification for sketch-pattern-mirror."""

from __future__ import annotations

import math
from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftMeasurementChangeExpectation,
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
        "Sketch", name="Dog holes", check_name=True,
        check_error=False, check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "ExtrudeFeature", name="Dog holes", check_name=True,
        check_error=False, check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "Sketch", name="Clamp slots", check_name=True,
        check_error=False, check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "ExtrudeFeature", name="Clamp slots", check_name=True,
        check_error=False, check_warning=False,
    ),
)

BASE_SLOT_AREA = 20.0 * 8.0 + math.pi * 4.0**2
BASE_VOLUME = (
    240.0 * 160.0 * 5.0
    - 8.0 * math.pi * 4.0**2 * 5.0
    - 8.0 * BASE_SLOT_AREA * 5.0
)
MUTATED_VOLUME = (
    240.0 * 160.0 * 5.0
    - 8.0 * math.pi * 5.0**2 * 5.0
    - 8.0 * BASE_SLOT_AREA * 5.0
)

SKETCHES = (
    SolidCraftSketchExpectation(name="Dog holes", status="solved"),
    SolidCraftSketchExpectation(name="Clamp slots", status="solved"),
)

VERIFICATION = SolidCraftVerification(
    verification_id="sketch-pattern-mirror",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-120.0, -80.0, 0.0), (120.0, 80.0, 5.0)),
        ),
        bounds_tolerance=0.01,
        parameters={
            "hole_columns": 4.0,
            "hole_diameter": 8.0,
            "hole_pitch": 25.0,
            "slot_count": 2.0,
            "slot_pitch": 50.0,
        },
        parameter_match="subset",
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=BASE_VOLUME,
                volume_tolerance=0.05,
            ),
        ),
        sketch_count=2,
        sketches=SKETCHES,
        timeline=TIMELINE,
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="patterns_mutated",
            command_path=HERE / "change_patterns.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                body_envelopes=(
                    BodyEnvelope((-120.0, -80.0, 0.0), (120.0, 80.0, 5.0)),
                ),
                bounds_tolerance=0.01,
                parameters={
                    "hole_columns": 4.0,
                    "hole_diameter": 10.0,
                    "hole_pitch": 30.0,
                    "slot_count": 2.0,
                    "slot_pitch": 30.0,
                },
                parameter_match="subset",
                named_bodies=(
                    SolidCraftBodyExpectation(
                        volume_mm3=MUTATED_VOLUME,
                        volume_tolerance=0.05,
                    ),
                ),
                sketch_count=2,
                sketches=SKETCHES,
                timeline=TIMELINE,
            ),
            changes=(
                SolidCraftMeasurementChangeExpectation(
                    id="layout_center_x",
                    path=("bodies", 0, "center_of_mass", 0),
                    minimum_absolute_delta=0.01,
                ),
            ),
        ),
    ),
)
