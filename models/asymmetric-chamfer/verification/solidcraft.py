"""Native verification for asymmetric-chamfer."""

from __future__ import annotations

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftInspection,
    SolidCraftInspectionCheck,
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
        name="Chamfer profile",
        check_name=True,
        check_error=False,
        check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "ExtrudeFeature",
        check_error=False,
        check_warning=False,
    ),
    SolidCraftTimelineExpectation(
        "ChamferFeature",
        check_error=False,
        check_warning=False,
    ),
)

SKETCH = SolidCraftSketchExpectation(
    name="Chamfer profile",
    curves=4,
    profiles=1,
    status="solved",
)

BASE_VOLUME = 40.0 * 20.0 * 10.0 - 0.18 * 0.65 * 40.0
MUTATED_VOLUME = 50.0 * 24.0 * 12.0 - 0.3 * 0.8 * 50.0


VERIFICATION = SolidCraftVerification(
    verification_id="asymmetric-chamfer",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope((-20.0, -10.0, 0.0), (20.0, 10.0, 10.0)),
        ),
        bounds_tolerance=0.01,
        parameters={
            "width": 40.0,
            "depth": 20.0,
            "height": 10.0,
            "primary_distance": 0.18,
            "secondary_distance": 0.65,
        },
        parameter_match="subset",
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=BASE_VOLUME,
                volume_tolerance=0.02,
            ),
        ),
        sketch_count=1,
        sketches=(SKETCH,),
        timeline=TIMELINE,
    ),
    inspections=(
        SolidCraftInspection(
            id="chamfer-definition",
            command_path=HERE / "inspect_chamfer.json",
            checks=(
                SolidCraftInspectionCheck(
                    id="primary-distance",
                    path=(0, "definition", "distance"),
                    expected="primary_distance",
                ),
                SolidCraftInspectionCheck(
                    id="secondary-distance",
                    path=(0, "definition", "distance2"),
                    expected="secondary_distance",
                ),
                SolidCraftInspectionCheck(
                    id="flipped-face-order",
                    path=(0, "definition", "flip"),
                    expected=True,
                ),
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="resized_asymmetric_chamfer",
            command_path=HERE / "change_size.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                body_envelopes=(
                    BodyEnvelope((-25.0, -12.0, 0.0), (25.0, 12.0, 12.0)),
                ),
                bounds_tolerance=0.01,
                parameters={
                    "width": 50.0,
                    "depth": 24.0,
                    "height": 12.0,
                    "primary_distance": 0.3,
                    "secondary_distance": 0.8,
                },
                parameter_match="subset",
                named_bodies=(
                    SolidCraftBodyExpectation(
                        volume_mm3=MUTATED_VOLUME,
                        volume_tolerance=0.03,
                    ),
                ),
                sketch_count=1,
                sketches=(SKETCH,),
                timeline=TIMELINE,
            ),
            changes=(
                SolidCraftMeasurementChangeExpectation(
                    id="asymmetric_chamfer_volume",
                    path=("bodies", 0, "volume_mm3"),
                    minimum_absolute_delta=1000.0,
                ),
            ),
        ),
    ),
)
