"""Model-specific declarative verification for parent-derived-child-size."""

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
    verification_id="parent-derived-child-size",
    baseline=SolidCraftModelExpectation(
        body_count=2,
        body_envelopes=(
            BodyEnvelope((-60.0, -40.0, 0.0), (60.0, 40.0, 10.0)),
            BodyEnvelope((-30.0, -20.0, 20.0), (30.0, 20.0, 26.0)),
        ),
        bounds_tolerance=0.001,
        parameters={"base_width": 120.0, "base_depth": 80.0},
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="size_160x120",
            command_path=HERE / "change_size.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope((-80.0, -60.0, 0.0), (80.0, 60.0, 10.0)),
                    BodyEnvelope((-40.0, -30.0, 20.0), (40.0, 30.0, 26.0)),
                ),
                bounds_tolerance=0.001,
                parameters={"base_width": 160.0, "base_depth": 120.0},
            ),
        ),
    ),
)
