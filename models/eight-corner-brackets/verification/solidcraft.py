"""Model-specific CAD verification data for eight-corner-brackets."""

from __future__ import annotations

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="eight-corner-brackets",
    baseline=SolidCraftModelExpectation(
        body_count=9,
        body_envelopes=(
            BodyEnvelope(
                (-60.0, -40.0, 0.0),
                (60.0, 40.0, 60.0),
            ),
            BodyEnvelope(
                (-64.0, -44.0, 0.0),
                (-32.0, -12.0, 16.0),
            ),
            BodyEnvelope(
                (-64.0, -44.0, 44.0),
                (-32.0, -12.0, 60.0),
            ),
            BodyEnvelope(
                (32.0, -44.0, 0.0),
                (64.0, -12.0, 16.0),
            ),
            BodyEnvelope(
                (32.0, -44.0, 44.0),
                (64.0, -12.0, 60.0),
            ),
            BodyEnvelope(
                (32.0, 12.0, 0.0),
                (64.0, 44.0, 16.0),
            ),
            BodyEnvelope(
                (32.0, 12.0, 44.0),
                (64.0, 44.0, 60.0),
            ),
            BodyEnvelope(
                (-64.0, 12.0, 0.0),
                (-32.0, 44.0, 16.0),
            ),
            BodyEnvelope(
                (-64.0, 12.0, 44.0),
                (-32.0, 44.0, 60.0),
            ),
        ),
        bounds_tolerance=0.001,
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="size_160x120x90",
            command_path=HERE / "change_size.json",
            expectation=SolidCraftModelExpectation(
                body_count=9,
                body_envelopes=(
                    BodyEnvelope(
                        (-80.0, -60.0, 0.0),
                        (80.0, 60.0, 90.0),
                    ),
                    BodyEnvelope(
                        (-84.0, -64.0, 0.0),
                        (-52.0, -32.0, 16.0),
                    ),
                    BodyEnvelope(
                        (-84.0, -64.0, 74.0),
                        (-52.0, -32.0, 90.0),
                    ),
                    BodyEnvelope(
                        (52.0, -64.0, 0.0),
                        (84.0, -32.0, 16.0),
                    ),
                    BodyEnvelope(
                        (52.0, -64.0, 74.0),
                        (84.0, -32.0, 90.0),
                    ),
                    BodyEnvelope(
                        (52.0, 32.0, 0.0),
                        (84.0, 64.0, 16.0),
                    ),
                    BodyEnvelope(
                        (52.0, 32.0, 74.0),
                        (84.0, 64.0, 90.0),
                    ),
                    BodyEnvelope(
                        (-84.0, 32.0, 0.0),
                        (-52.0, 64.0, 16.0),
                    ),
                    BodyEnvelope(
                        (-84.0, 32.0, 74.0),
                        (-52.0, 64.0, 90.0),
                    ),
                ),
                bounds_tolerance=0.001,
            ),
        ),
    ),
)
