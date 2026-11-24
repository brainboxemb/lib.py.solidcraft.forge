"""Model-specific declarative verification for eight-flightcase-corners."""

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

BASE_PROTECTORS = (
    BodyEnvelope((-64.0, -44.0, -4.0), (-40.0, -20.0, 20.0)),
    BodyEnvelope((40.0, -44.0, -4.0), (64.0, -20.0, 20.0)),
    BodyEnvelope((40.0, 20.0, -4.0), (64.0, 44.0, 20.0)),
    BodyEnvelope((-64.0, 20.0, -4.0), (-40.0, 44.0, 20.0)),
    BodyEnvelope((-64.0, -44.0, 40.0), (-40.0, -20.0, 64.0)),
    BodyEnvelope((40.0, -44.0, 40.0), (64.0, -20.0, 64.0)),
    BodyEnvelope((40.0, 20.0, 40.0), (64.0, 44.0, 64.0)),
    BodyEnvelope((-64.0, 20.0, 40.0), (-40.0, 44.0, 64.0)),
)

MUTATED_PROTECTORS = (
    BodyEnvelope((-84.0, -64.0, -4.0), (-60.0, -40.0, 20.0)),
    BodyEnvelope((60.0, -64.0, -4.0), (84.0, -40.0, 20.0)),
    BodyEnvelope((60.0, 40.0, -4.0), (84.0, 64.0, 20.0)),
    BodyEnvelope((-84.0, 40.0, -4.0), (-60.0, 64.0, 20.0)),
    BodyEnvelope((-84.0, -64.0, 70.0), (-60.0, -40.0, 94.0)),
    BodyEnvelope((60.0, -64.0, 70.0), (84.0, -40.0, 94.0)),
    BodyEnvelope((60.0, 40.0, 70.0), (84.0, 64.0, 94.0)),
    BodyEnvelope((-84.0, 40.0, 70.0), (-60.0, 64.0, 94.0)),
)

VERIFICATION = SolidCraftVerification(
    verification_id="eight-flightcase-corners",
    baseline=SolidCraftModelExpectation(
        body_count=9,
        body_envelopes=(
            BodyEnvelope((-60.0, -40.0, 0.0), (60.0, 40.0, 60.0)),
            *BASE_PROTECTORS,
        ),
        bounds_tolerance=0.001,
        body_groups=(
            SolidCraftBodyGroupExpectation(
                name_prefix="FlightcaseCorner",
                count=8,
                body_envelopes=BASE_PROTECTORS,
                bounds_tolerance=0.001,
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="size_160x120x90",
            command_path=HERE / "change_size.json",
            expectation=SolidCraftModelExpectation(
                body_count=9,
                body_envelopes=(
                    BodyEnvelope((-80.0, -60.0, 0.0), (80.0, 60.0, 90.0)),
                    *MUTATED_PROTECTORS,
                ),
                bounds_tolerance=0.001,
                parameters={
                    "case_width": 160.0,
                    "case_depth": 120.0,
                    "case_height": 90.0,
                },
                body_groups=(
                    SolidCraftBodyGroupExpectation(
                        name_prefix="FlightcaseCorner",
                        count=8,
                        body_envelopes=MUTATED_PROTECTORS,
                        bounds_tolerance=0.001,
                    ),
                ),
            ),
        ),
    ),
)
