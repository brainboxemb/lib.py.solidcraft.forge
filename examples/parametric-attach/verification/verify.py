"""Model-specific CAD verification data for parametric-attach."""

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
    verification_id="parametric-attach",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope(
                (-20.0, -15.0, 0.0),
                (20.0, 15.0, 10.0),
            ),
            BodyEnvelope(
                (30.0, -10.0, 0.0),
                (50.0, 10.0, 10.0),
            ),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                name_prefix="Base",
                minimum=(-20.0, -15.0, 0.0),
                maximum=(20.0, 15.0, 10.0),
                bounds_tolerance=0.001,
            ),
            SolidCraftBodyExpectation(
                name_prefix="Block",
                minimum=(30.0, -10.0, 0.0),
                maximum=(50.0, 10.0, 10.0),
                bounds_tolerance=0.001,
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="gap_30",
            command_path=HERE / "change_gap.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope(
                        (-20.0, -15.0, 0.0),
                        (20.0, 15.0, 10.0),
                    ),
                    BodyEnvelope(
                        (50.0, -10.0, 0.0),
                        (70.0, 10.0, 10.0),
                    ),
                ),
                bounds_tolerance=0.001,
                named_bodies=(
                    SolidCraftBodyExpectation(
                        name_prefix="Block",
                        minimum=(50.0, -10.0, 0.0),
                        maximum=(70.0, 10.0, 10.0),
                        bounds_tolerance=0.001,
                    ),
                ),
            ),
        ),
    ),
)
