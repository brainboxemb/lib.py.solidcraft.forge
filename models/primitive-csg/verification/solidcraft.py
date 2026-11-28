"""Model-specific declarative verification for primitive-csg."""
from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftMeasurementChangeExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

CLIPPED = SolidCraftModelExpectation(
    body_count=1,
    body_envelopes=(
        BodyEnvelope(
            (-19.595917942265423, -20.0, 0.0),
            (25.0, 20.0, 20.0),
        ),
    ),
    bounds_tolerance=0.01,
    named_bodies=(
        SolidCraftBodyExpectation(
            face_type_counts={"sphere": 1, "cylinder": 1},
        ),
    ),
)


VERIFICATION = SolidCraftVerification(
    verification_id="primitive-csg",
    baseline=CLIPPED,
    saved_designs=(
        SolidCraftSavedDesign(
            id="unclipped",
            command_path=HERE / "unclipped.json",
            expectation=SolidCraftModelExpectation(body_count=1),
            changes=(
                SolidCraftMeasurementChangeExpectation(
                    id="clip-plane-release",
                    path=("bodies", 0, "bbox", "min", 2),
                    minimum_absolute_delta=10.0,
                ),
                SolidCraftMeasurementChangeExpectation(
                    id="clip-volume-release",
                    path=("bodies", 0, "volume_mm3"),
                    minimum_absolute_delta=100.0,
                ),
            ),
        ),
        SolidCraftSavedDesign(
            id="restore-clipped",
            command_path=HERE / "restore_clipped.json",
            expectation=CLIPPED,
        ),
    ),
)
