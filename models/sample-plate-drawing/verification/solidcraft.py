"""Native geometry qualification for the Sample Plate Drawing owner.

Drawing structure is qualified during the SCPF build from replay-bound native
drawing.inspect evidence published beside the PDF/PNG artifacts.
"""

from cad_verification import (
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="sample-plate-drawing",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        named_bodies=(
            SolidCraftBodyExpectation(closed=True),
        ),
    ),
)
