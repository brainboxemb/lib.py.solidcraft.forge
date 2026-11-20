"""Model-specific declarative verification for selective-profile-extrude."""

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
        "Sketch", name="Selected holes", check_name=True,
        check_error=False, check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "ExtrudeFeature", name="Selected holes", check_name=True,
        check_error=False, check_warning=False,
    ),
)


def center_x(radius: float, positions_sum: float) -> float:
    """Return the historical expected X center for the selected cuts."""

    removed_volume = math.pi * radius**2 * 5.0
    volume = 120.0 * 60.0 * 5.0 - 3.0 * removed_volume
    return -(removed_volume * positions_sum) / volume


VERIFICATION = SolidCraftVerification(
    verification_id="selective-profile-extrude",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-60.0, -30.0, 0.0), (60.0, 30.0, 5.0)),
        ),
        bounds_tolerance=0.01,
        parameters={"hole_diameter": 8.0, "hole_pitch": 20.0},
        parameter_match="subset",
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=120.0 * 60.0 * 5.0 - 3.0 * math.pi * 4.0**2 * 5.0,
                volume_tolerance=0.05,
                face_type_counts={"cylinder": 3},
                center_of_mass=(
                    center_x(4.0, -30.0 - 10.0 + 30.0),
                    None,
                    None,
                ),
                center_of_mass_tolerance=0.001,
            ),
        ),
        sketch_count=1,
        sketches=(
            SolidCraftSketchExpectation(
                name="Selected holes", status="solved",
            ),
        ),
        timeline=TIMELINE,
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="pattern_mutated",
            command_path=HERE / "change_pattern.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                body_envelopes=(
                    BodyEnvelope((-60.0, -30.0, 0.0), (60.0, 30.0, 5.0)),
                ),
                bounds_tolerance=0.01,
                parameters={"hole_diameter": 10.0, "hole_pitch": 24.0},
                parameter_match="subset",
                named_bodies=(
                    SolidCraftBodyExpectation(
                        volume_mm3=120.0 * 60.0 * 5.0 - 3.0 * math.pi * 5.0**2 * 5.0,
                        volume_tolerance=0.05,
                        face_type_counts={"cylinder": 3},
                        center_of_mass=(
                            center_x(5.0, -30.0 - 6.0 + 42.0),
                            None,
                            None,
                        ),
                        center_of_mass_tolerance=0.001,
                    ),
                ),
                sketch_count=1,
                sketches=(
                    SolidCraftSketchExpectation(
                        name="Selected holes", status="solved",
                    ),
                ),
                timeline=TIMELINE,
            ),
        ),
    ),
)
