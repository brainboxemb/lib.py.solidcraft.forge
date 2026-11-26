"""Saved-design qualification for assembly placement configurations."""
from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
)

HERE = Path(__file__).resolve().parent

SCREEN = BodyEnvelope((-40.0, -5.0, -25.0), (40.0, 5.0, 25.0))

VERIFICATION = SolidCraftVerification(
    verification_id="configuration-position",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            SCREEN,
            BodyEnvelope((-40.0, 7.0, -25.0), (40.0, 9.0, 25.0)),
        ),
        bounds_tolerance=0.001,
        parameters={"plate_y": 8.0, "plate_z": 0.0},
        parameter_match="subset",
    ),
    inspections=(
        SolidCraftInspection(
            id="table",
            command_path=HERE / "table.json",
            checks=(
                SolidCraftInspectionCheck(id="rows", path=(0, "rows"), count=3),
                SolidCraftInspectionCheck(id="columns", path=(0, "columns"), count=2),
                SolidCraftInspectionCheck(id="active", path=(0, "active"), expected="Front"),
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="below",
            command_path=HERE / "below.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    SCREEN,
                    BodyEnvelope((-40.0, -1.0, -80.0), (40.0, 1.0, -30.0)),
                ),
                bounds_tolerance=0.001,
                parameters={"plate_y": 0.0, "plate_z": -55.0},
                parameter_match="subset",
            ),
        ),
        SolidCraftSavedDesign(
            id="service",
            command_path=HERE / "service.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    SCREEN,
                    BodyEnvelope((-40.0, 24.0, -25.0), (40.0, 26.0, 25.0)),
                ),
                bounds_tolerance=0.001,
                parameters={"plate_y": 25.0, "plate_z": 0.0},
                parameter_match="subset",
            ),
        ),
    ),
)
