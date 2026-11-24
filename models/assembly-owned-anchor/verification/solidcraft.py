"""Model-specific CAD verification data for assembly-owned-anchor."""

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
    verification_id="assembly-owned-anchor",
    baseline=SolidCraftModelExpectation(
        body_count=3,
        body_envelopes=(
            BodyEnvelope(
                (-20.0, -15.0, 0.0),
                (20.0, 15.0, 20.0),
            ),
            BodyEnvelope(
                (65.0, -5.0, 0.0),
                (75.0, 5.0, 10.0),
            ),
            BodyEnvelope(
                (10.0, -25.0, 10.0),
                (20.0, -15.0, 20.0),
            ),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                name_prefix="Marker",
                minimum=(10.0, -25.0, 10.0),
                maximum=(20.0, -15.0, 20.0),
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
                        (-40.0, -15.0, 0.0),
                        (40.0, 15.0, 40.0),
                    ),
                    BodyEnvelope(
                        (65.0, -5.0, 0.0),
                        (75.0, 5.0, 10.0),
                    ),
                    BodyEnvelope(
                        (30.0, -25.0, 30.0),
                        (40.0, -15.0, 40.0),
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
                        minimum=(30.0, -25.0, 30.0),
                        maximum=(40.0, -15.0, 40.0),
                        bounds_tolerance=0.001,
                    ),
                ),
            ),
        ),
    ),
)
