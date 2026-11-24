"""Model-specific CAD verification data for parametric-anchor."""

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
    verification_id="parametric-anchor",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope(
                (-20.0, -15.0, 0.0),
                (20.0, 15.0, 10.0),
            ),
            BodyEnvelope(
                (20.0, -10.0, 0.0),
                (40.0, 10.0, 10.0),
            ),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                name_prefix="Block",
                minimum=(20.0, -10.0, 0.0),
                maximum=(40.0, 10.0, 10.0),
                bounds_tolerance=0.001,
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="base_width_80",
            command_path=HERE / "change_base_width.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope(
                        (-40.0, -15.0, 0.0),
                        (40.0, 15.0, 10.0),
                    ),
                    BodyEnvelope(
                        (40.0, -10.0, 0.0),
                        (60.0, 10.0, 10.0),
                    ),
                ),
                bounds_tolerance=0.001,
                named_bodies=(
                    SolidCraftBodyExpectation(
                        name_prefix="Block",
                        minimum=(40.0, -10.0, 0.0),
                        maximum=(60.0, 10.0, 10.0),
                        bounds_tolerance=0.001,
                    ),
                ),
            ),
        ),
    ),
)
