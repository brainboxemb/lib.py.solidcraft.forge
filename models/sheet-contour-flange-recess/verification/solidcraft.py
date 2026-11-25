"""Native verification for the #845 contour-flange recess replay fixture."""

from cad_verification import (
    SolidCraftBodyExpectation,
    SolidCraftModelExpectation,
    SolidCraftSketchExpectation,
    SolidCraftVerification,
)


VERIFICATION = SolidCraftVerification(
    verification_id="sheet-contour-flange-recess",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        parameters={
            "length": 250.0,
        },
        parameter_match="subset",
        named_bodies=(
            SolidCraftBodyExpectation(
                sheet_metal=True,
                closed=True,
            ),
        ),
        sketch_count=2,
        sketches=(
            SolidCraftSketchExpectation(
                name="C profile",
                profiles=0,
                curves=5,
            ),
            SolidCraftSketchExpectation(
                name="Broad face recess",
                profiles=1,
                curves=1,
            ),
        ),
    ),
)
