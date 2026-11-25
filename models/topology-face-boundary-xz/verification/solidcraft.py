"""Native verification for two-face XZ topology boundary selection."""

from cad_verification import (
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftSketchExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="topology-face-boundary-xz",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        named_bodies=(
            SolidCraftBodyExpectation(closed=True),
        ),
        sketch_count=1,
        sketches=(
            SolidCraftSketchExpectation(name="Hook profile", status="solved"),
        ),
        timeline=(
            SolidCraftTimelineExpectation(
                "Sketch", name="Hook profile", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ExtrudeFeature", check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ChamferFeature", check_error=False, check_warning=False,
            ),
        ),
    ),
)
