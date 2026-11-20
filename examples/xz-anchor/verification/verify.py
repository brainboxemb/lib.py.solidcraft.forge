"""Model-specific CAD verification data for xz-anchor."""

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
    verification_id="xz-anchor",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope(
                (-20.0, 0.0, 0.0),
                (20.0, 12.0, 20.0),
            ),
            BodyEnvelope(
                (10.0, -10.0, 10.0),
                (20.0, 0.0, 20.0),
            ),
            BodyEnvelope(
                (-20.0, -10.0, 10.0),
                (-10.0, 0.0, 20.0),
            ),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                name_prefix="RightMarker",
                minimum=(10.0, -10.0, 10.0),
                maximum=(20.0, 0.0, 20.0),
                bounds_tolerance=0.001,
            ),
            SolidCraftBodyExpectation(
                name_prefix="LeftMarker",
                minimum=(-20.0, -10.0, 10.0),
                maximum=(-10.0, 0.0, 20.0),
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
                        (-40.0, 0.0, 0.0),
                        (40.0, 12.0, 40.0),
                    ),
                    BodyEnvelope(
                        (30.0, -10.0, 30.0),
                        (40.0, 0.0, 40.0),
                    ),
                    BodyEnvelope(
                        (-40.0, -10.0, 30.0),
                        (-30.0, 0.0, 40.0),
                    ),
                ),
                bounds_tolerance=0.001,
                named_bodies=(
                    SolidCraftBodyExpectation(
                        name_prefix="RightMarker",
                        minimum=(30.0, -10.0, 30.0),
                        maximum=(40.0, 0.0, 40.0),
                        bounds_tolerance=0.001,
                    ),
                    SolidCraftBodyExpectation(
                        name_prefix="LeftMarker",
                        minimum=(-40.0, -10.0, 30.0),
                        maximum=(-30.0, 0.0, 40.0),
                        bounds_tolerance=0.001,
                    ),
                ),
            ),
        ),
    ),
)
