"""Model-specific CAD verification data for parametric-move."""

from pathlib import Path
from cad_verification import BodyEnvelope, SolidCraftModelExpectation, SolidCraftSavedDesign, SolidCraftVerification

HERE = Path(__file__).resolve().parent
VERIFICATION = SolidCraftVerification(
    verification_id="parametric-move",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope((-10.0, -10.0, -5.0), (10.0, 10.0, 5.0)),
            BodyEnvelope((30.0, -10.0, -5.0), (50.0, 10.0, 5.0)),
        ),
        bounds_tolerance=0.001,
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="offset_70",
            command_path=HERE / "change_offset.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope((-10.0, -10.0, -5.0), (10.0, 10.0, 5.0)),
                    BodyEnvelope((60.0, -10.0, -5.0), (80.0, 10.0, 5.0)),
                ),
                bounds_tolerance=0.001,
            ),
        ),
    ),
)
