"""Native saved-design verification for #843."""
import math
from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)

HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="native-revolve",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(BodyEnvelope((0, -4, -4), (10, 4, 4)),),
        bounds_tolerance=0.01,
        parameters={"length": 10, "radius": 4, "sweep": math.tau},
        parameter_match="subset",
        named_bodies=(SolidCraftBodyExpectation(
            closed=True,
            volume_mm3=math.pi * 4**2 * 10,
            volume_tolerance=0.5,
        ),),
        sketch_count=1,
        timeline=(
            SolidCraftTimelineExpectation(
                "Sketch", name="RadialProfile", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "RevolveFeature", check_name=False,
                check_error=False, check_warning=False,
            ),
        ),
    ),
    saved_designs=(
        SolidCraftSavedDesign(
            id="resize_revolved_solid",
            command_path=HERE / "change_geometry.json",
            expectation=SolidCraftModelExpectation(
                body_count=1,
                parameters={"length": 10, "radius": 5, "sweep": math.pi},
                parameter_match="subset",
                named_bodies=(SolidCraftBodyExpectation(
                    closed=True,
                    volume_mm3=math.pi * 5**2 * 10 / 2,
                    volume_tolerance=0.5,
                ),),
                sketch_count=1,
            ),
        ),
    ),
)
