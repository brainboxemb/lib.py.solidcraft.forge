"""Model-specific CAD verification data for four-corner-l."""

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
    verification_id="four-corner-l",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope(
                (-60.0, -40.0, 0.0),
                (60.0, 40.0, 60.0),
            ),
            BodyEnvelope(
                (-64.0, -44.0, 22.0),
                (-32.0, -12.0, 38.0),
            ),
            BodyEnvelope(
                (32.0, -44.0, 22.0),
                (64.0, -12.0, 38.0),
            ),
            BodyEnvelope(
                (32.0, 12.0, 22.0),
                (64.0, 44.0, 38.0),
            ),
            BodyEnvelope(
                (-64.0, 12.0, 22.0),
                (-32.0, 44.0, 38.0),
            ),
        ),
        bounds_tolerance=0.001,
        named_bodies=(
            SolidCraftBodyExpectation(
                name_prefix="FrameBlock",
                minimum=(-60.0, -40.0, 0.0),
                maximum=(60.0, 40.0, 60.0),
                bounds_tolerance=0.001,
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="size_160x120",
            command_path=HERE / "change_size.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope(
                        (-80.0, -60.0, 0.0),
                        (80.0, 60.0, 60.0),
                    ),
                    BodyEnvelope(
                        (-84.0, -64.0, 22.0),
                        (-52.0, -32.0, 38.0),
                    ),
                    BodyEnvelope(
                        (52.0, -64.0, 22.0),
                        (84.0, -32.0, 38.0),
                    ),
                    BodyEnvelope(
                        (52.0, 32.0, 22.0),
                        (84.0, 64.0, 38.0),
                    ),
                    BodyEnvelope(
                        (-84.0, 32.0, 22.0),
                        (-52.0, 64.0, 38.0),
                    ),
                ),
                bounds_tolerance=0.001,
            ),
        ),
    ),
)
