"""Model-specific declarative verification for slot-family."""

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
PLATE_VOLUME = 160.0 * 120.0 * 5.0

ARC_THREE_POINT_RADIUS = 15.153846153846153
ARC_THREE_POINT_SWEEP = math.radians(163.65753288010052)
ARC_CENTER_RADIUS = 12.0
ARC_CENTER_SWEEP = math.radians(120.0)


def straight_slot_area(centerline_length, width):
    return centerline_length * width + math.pi * (width / 2.0) ** 2


def arc_slot_area(radius, sweep, width):
    return radius * sweep * width + math.pi * (width / 2.0) ** 2


BASELINE_WIDTH = 8.0
BASELINE_SLOT_AREA_SUM = (
    straight_slot_area(20.0, BASELINE_WIDTH)
    # Overall endpoints are 30 mm apart; native overall Slot centre-line length
    # is the overall length minus the 8 mm cap diameter.
    + straight_slot_area(22.0, BASELINE_WIDTH)
    # Center-point authoring uses centre to one cap centre: 10 mm, so the
    # complete native centre line is 20 mm.
    + straight_slot_area(20.0, BASELINE_WIDTH)
    + arc_slot_area(
        ARC_THREE_POINT_RADIUS,
        ARC_THREE_POINT_SWEEP,
        BASELINE_WIDTH,
    )
    + arc_slot_area(
        ARC_CENTER_RADIUS,
        ARC_CENTER_SWEEP,
        BASELINE_WIDTH,
    )
)
BASELINE_VOLUME = PLATE_VOLUME - 5.0 * BASELINE_SLOT_AREA_SUM

MUTATED_WIDTH = 10.0
MUTATED_SLOT_AREA_SUM = (
    # c2c: -60 .. -35 -> 25 mm centre distance.
    straight_slot_area(25.0, MUTATED_WIDTH)
    # overall: -10 .. 25 -> 35 mm overall, hence 25 mm centre line at width 10.
    + straight_slot_area(25.0, MUTATED_WIDTH)
    # center point: 55 .. 70 -> 15 mm to one cap centre, 30 mm complete line.
    + straight_slot_area(30.0, MUTATED_WIDTH)
    + arc_slot_area(
        ARC_THREE_POINT_RADIUS,
        ARC_THREE_POINT_SWEEP,
        MUTATED_WIDTH,
    )
    + arc_slot_area(
        ARC_CENTER_RADIUS,
        ARC_CENTER_SWEEP,
        MUTATED_WIDTH,
    )
)
MUTATED_VOLUME = PLATE_VOLUME - 5.0 * MUTATED_SLOT_AREA_SUM


COMMON_SKETCH = SolidCraftSketchExpectation(
    name="Slot family",
    profiles=5,
    curves=29,
    status="solved",
)


VERIFICATION = SolidCraftVerification(
    verification_id="slot-family",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-80.0, -60.0, 0.0), (80.0, 60.0, 5.0)),
        ),
        bounds_tolerance=0.01,
        parameters={
            "slot_width": 8.0,
            "straight_y": -35.0,
            "c2c_start_x": -60.0,
            "c2c_end_x": -40.0,
            "overall_start_x": -10.0,
            "overall_end_x": 20.0,
            "center_point_x": 55.0,
            "center_point_end_x": 65.0,
        },
        parameter_match="subset",
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=BASELINE_VOLUME,
                volume_tolerance=0.01,
                face_count=26,
                face_type_counts={"cylinder": 14, "plane": 12},
            ),
        ),
        sketch_count=1,
        sketches=(COMMON_SKETCH,),
        timeline=(
            SolidCraftTimelineExpectation(
                "BoxFeature",
                name="Box1",
                check_name=True,
                check_error=False,
                check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "Sketch",
                name="Slot family",
                check_name=True,
                check_error=False,
                check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature",
                name="Slot family",
                check_name=True,
                check_error=False,
                check_warning=False,
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="parametric_slots",
            command_path=HERE / "change_size.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                body_envelopes=(
                    BodyEnvelope(
                        (-80.0, -60.0, 0.0),
                        (80.0, 60.0, 5.0),
                    ),
                ),
                bounds_tolerance=0.01,
                parameters={
                    "slot_width": 10.0,
                    "straight_y": -20.0,
                    "c2c_end_x": -35.0,
                    "overall_end_x": 25.0,
                    "center_point_end_x": 70.0,
                },
                parameter_match="subset",
                named_bodies=(
                    SolidCraftBodyExpectation(
                        volume_mm3=MUTATED_VOLUME,
                        volume_tolerance=0.02,
                        face_count=26,
                        face_type_counts={"cylinder": 14, "plane": 12},
                    ),
                ),
                sketch_count=1,
                sketches=(COMMON_SKETCH,),
            ),
        ),
    ),
)
