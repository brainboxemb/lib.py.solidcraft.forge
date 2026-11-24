"""Model-specific declarative verification for rectangular-pattern."""

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
        "Sketch", name="Slot", check_name=True,
        check_error=False, check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "ExtrudeFeature", name="Slot", check_name=True,
        check_error=False, check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "RectangularPatternFeature", name="RectangularPattern1", check_name=True,
        check_error=False, check_warning=False,
    ),
)

SLOT_VOLUME = (10.0 * 6.0 + math.pi * 3.0**2) * 4.0

VERIFICATION = SolidCraftVerification(
    verification_id="rectangular-pattern",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-60.0, -40.0, 0.0), (60.0, 40.0, 4.0)),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=120.0 * 80.0 * 4.0 - 6.0 * SLOT_VOLUME,
                volume_tolerance=0.01,
                face_count=30,
                face_type_counts={"cylinder": 12, "plane": 18},
            ),
        ),
        sketches=(
            SolidCraftSketchExpectation(
                name="Slot", curves=5, profiles=1, status="solved",
            ),
        ),
        timeline=TIMELINE,
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="columns_2_pitch_30",
            command_path=HERE / "change_columns_pitch.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                body_envelopes=(
                    BodyEnvelope((-60.0, -40.0, 0.0), (60.0, 40.0, 4.0)),
                ),
                bounds_tolerance=0.01,
                parameters={
                    "columns": 2.0,
                    "pitch": 30.0,
                    "rows": 2.0,
                    "row_pitch": 28.0,
                },
                named_bodies=(
                    SolidCraftBodyExpectation(
                        volume_mm3=120.0 * 80.0 * 4.0 - 4.0 * SLOT_VOLUME,
                        volume_tolerance=0.01,
                        face_count=22,
                        face_type_counts={"cylinder": 8, "plane": 14},
                        center_of_mass=(
                            -(4.0 * SLOT_VOLUME * 15.0)
                            / (120.0 * 80.0 * 4.0 - 4.0 * SLOT_VOLUME),
                            -(4.0 * SLOT_VOLUME * 14.0)
                            / (120.0 * 80.0 * 4.0 - 4.0 * SLOT_VOLUME),
                            2.0,
                        ),
                        center_of_mass_tolerance=0.001,
                    ),
                ),
                sketches=(
                    SolidCraftSketchExpectation(
                        name="Slot", curves=5, profiles=1, status="solved",
                    ),
                ),
                timeline=TIMELINE,
            ),
        ),
    ),
)
