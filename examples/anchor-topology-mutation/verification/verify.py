"""Model-specific CAD verification data for anchor-topology-mutation."""

from __future__ import annotations

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="anchor-topology-mutation",
    baseline=SolidCraftModelExpectation(
        body_count=2,
        body_envelopes=(
            BodyEnvelope(
                (-20.0, -10.0, 0.0),
                (20.0, 10.0, 20.0),
            ),
            BodyEnvelope(
                (-25.0, -20.0, 15.0),
                (-15.0, -10.0, 25.0),
            ),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                name_prefix="Marker",
                minimum=(-25.0, -20.0, 15.0),
                maximum=(-15.0, -10.0, 25.0),
                bounds_tolerance=0.001,
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="size_80x40",
            command_path=HERE / "change_size.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope(
                        (-40.0, -10.0, 0.0),
                        (40.0, 10.0, 40.0),
                    ),
                    BodyEnvelope(
                        (-45.0, -20.0, 35.0),
                        (-35.0, -10.0, 45.0),
                    ),
                ),
                bounds_tolerance=0.001,
                parameters={
                    "base_width": 80.0,
                    "base_height": 40.0,
                },
                named_bodies=(
                    SolidCraftBodyExpectation(
                        name_prefix="Marker",
                        minimum=(-45.0, -20.0, 35.0),
                        maximum=(-35.0, -10.0, 45.0),
                        bounds_tolerance=0.001,
                    ),
                ),
            ),
        ),
    ),
)
