"""Native verification for multi-profile-extrude."""

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
        "Sketch",
        name="Tube profile",
        check_name=True,
        check_error=False,
        check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "ExtrudeFeature",
        name="Extrude1",
        check_name=True,
        check_error=False,
        check_warning=False,
    ),
)

SKETCH = SolidCraftSketchExpectation(
    name="Tube profile",
    curves=2,
    status="solved",
)

BASE_VOLUME = math.pi * (5.0**2 - 4.0**2) * 30.0
MUTATED_VOLUME = math.pi * (6.0**2 - 5.0**2) * 40.0


VERIFICATION = SolidCraftVerification(
    verification_id="multi-profile-extrude",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-5.0, -5.0, 0.0), (5.0, 5.0, 30.0)),
        ),
        bounds_tolerance=0.01,
        parameters={
            "outer_diameter": 10.0,
            "inner_diameter": 8.0,
            "length": 30.0,
        },
        parameter_match="subset",
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=BASE_VOLUME,
                volume_tolerance=0.02,
                face_type_counts={"cylinder": 2, "plane": 2},
            ),
        ),
        sketch_count=1,
        sketches=(SKETCH,),
        timeline=TIMELINE,
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="tube_resized",
            command_path=HERE / "change_size.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                body_envelopes=(
                    BodyEnvelope((-6.0, -6.0, 0.0), (6.0, 6.0, 40.0)),
                ),
                bounds_tolerance=0.01,
                parameters={
                    "outer_diameter": 12.0,
                    "inner_diameter": 10.0,
                    "length": 40.0,
                },
                parameter_match="subset",
                named_bodies=(
                    SolidCraftBodyExpectation(
                        volume_mm3=MUTATED_VOLUME,
                        volume_tolerance=0.03,
                        face_type_counts={"cylinder": 2, "plane": 2},
                    ),
                ),
                sketch_count=1,
                sketches=(SKETCH,),
                timeline=TIMELINE,
            ),
            changes=(
                SolidCraftMeasurementChangeExpectation(
                    id="tube_volume",
                    path=("bodies", 0, "volume_mm3"),
                    minimum_absolute_delta=100.0,
                ),
            ),
        ),
    ),
)
