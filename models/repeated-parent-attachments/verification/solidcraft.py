"""Model-specific declarative verification for repeated-parent-attachments."""

from __future__ import annotations

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyGroupExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="repeated-parent-attachments",
    baseline=SolidCraftModelExpectation(
        body_count=4,
        body_envelopes=(
            BodyEnvelope((-10.0, -10.0, 0.0), (10.0, 10.0, 40.0)),
            BodyEnvelope((50.0, -10.0, 0.0), (70.0, 10.0, 40.0)),
            BodyEnvelope((-5.0, -5.0, 40.0), (5.0, 5.0, 50.0)),
            BodyEnvelope((55.0, -5.0, 40.0), (65.0, 5.0, 50.0)),
        ),
        bounds_tolerance=0.001,
        parameters={"parent_height": 40.0},
        parameter_match="subset",
        body_groups=(
            SolidCraftBodyGroupExpectation(
                name_prefix="Marker",
                count=2,
                body_envelopes=(
                    BodyEnvelope((-5.0, -5.0, 40.0), (5.0, 5.0, 50.0)),
                    BodyEnvelope((55.0, -5.0, 40.0), (65.0, 5.0, 50.0)),
                ),
                bounds_tolerance=0.001,
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="height_60",
            command_path=HERE / "change_height.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope((-10.0, -10.0, 0.0), (10.0, 10.0, 60.0)),
                    BodyEnvelope((50.0, -10.0, 0.0), (70.0, 10.0, 60.0)),
                    BodyEnvelope((-5.0, -5.0, 60.0), (5.0, 5.0, 70.0)),
                    BodyEnvelope((55.0, -5.0, 60.0), (65.0, 5.0, 70.0)),
                ),
                bounds_tolerance=0.001,
                parameters={"parent_height": 60.0},
                parameter_match="subset",
                body_groups=(
                    SolidCraftBodyGroupExpectation(
                        name_prefix="Marker",
                        count=2,
                        body_envelopes=(
                            BodyEnvelope((-5.0, -5.0, 60.0), (5.0, 5.0, 70.0)),
                            BodyEnvelope((55.0, -5.0, 60.0), (65.0, 5.0, 70.0)),
                        ),
                        bounds_tolerance=0.001,
                    ),
                ),
            ),
        ),
    ),
)
