"""Native verification for one-face topology boundary selection."""

from cad_verification import (
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="topology-face-boundary-box",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        named_bodies=(
            SolidCraftBodyExpectation(closed=True),
        ),
        timeline=(
            SolidCraftTimelineExpectation(
                "BoxFeature", check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "ChamferFeature", check_error=False, check_warning=False,
            ),
        ),
    ),
)
