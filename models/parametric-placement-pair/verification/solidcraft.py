"""Model-specific CAD verification data for parametric-placement-pair."""

from pathlib import Path
from cad_verification import BodyEnvelope, SolidCraftModelExpectation, SolidCraftSavedDesign, SolidCraftVerification

HERE = Path(__file__).resolve().parent
VERIFICATION = SolidCraftVerification(
    verification_id="parametric-placement-pair",
    baseline=SolidCraftModelExpectation(
        body_envelopes=(
            BodyEnvelope((-50.0, -10.0, -5.0), (-30.0, 10.0, 5.0)),
            BodyEnvelope((30.0, -10.0, -5.0), (50.0, 10.0, 5.0)),
        ),
        bounds_tolerance=0.001,
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="spacing_120",
            command_path=HERE / "change_spacing.json",
            expectation=SolidCraftModelExpectation(
                body_envelopes=(
                    BodyEnvelope((-70.0, -10.0, -5.0), (-50.0, 10.0, 5.0)),
                    BodyEnvelope((50.0, -10.0, -5.0), (70.0, 10.0, 5.0)),
                ),
                bounds_tolerance=0.001,
            ),
        ),
    ),
)
