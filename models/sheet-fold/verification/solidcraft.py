"""Model-specific declarative verification for sheet-fold."""

from __future__ import annotations

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftModelExpectation,
    SolidCraftSketchExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="sheet-fold",
    baseline=SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope(
                (-40.0, -20.0, 0.0),
                (21.64380551, 20.0, 21.64380551),
            ),
        ),
        bounds_tolerance=0.01,
        named_bodies=(
            SolidCraftBodyExpectation(
                volume_mm3=6343.451332235384,
                volume_tolerance=0.01,
                sheet_metal=True,
                closed=True,
            ),
        ),
        timeline=(
            SolidCraftTimelineExpectation(
                "Sketch", name="Blank", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "BaseFlangeFeature", name="BaseFlange1", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "HoleFeature", name="Hole1", check_name=True,
                check_error=False, check_warning=False,
            ),
            SolidCraftTimelineExpectation(
                "FoldFeature", name="Fold1", check_name=True,
                check_error=False, check_warning=False,
            ),
        ),
        sketches=(
            SolidCraftSketchExpectation(
                name="Blank", profiles=1, curves=4, status="solved",
            ),
        ),
    ),
    inspections=(
        SolidCraftInspection(
            id="flat_pattern",
            command_path=HERE / "inspect_flat_pattern.json",
            checks=(
                SolidCraftInspectionCheck(id="result_count", count=1),
                SolidCraftInspectionCheck(
                    id="flat_size", path=(0, "flat_size_mm"),
                    expected=[80.0, 40.0, 2.0], tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="cutout_count", path=(0, "cutout_shapes"), count=1,
                ),
                SolidCraftInspectionCheck(
                    id="hole_center",
                    path=(0, "cutout_shapes", 0, "circle", "center"),
                    expected=[-20.0, 0.0], tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="hole_radius",
                    path=(0, "cutout_shapes", 0, "circle", "radius"),
                    expected=3.0, tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="bend_count", path=(0, "bends"), count=1,
                ),
                SolidCraftInspectionCheck(
                    id="bend_angle", path=(0, "bends", 0, "angle_deg"),
                    expected=90.0, tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="bend_radius", path=(0, "bends", 0, "radius"),
                    expected=2.0, tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="bend_allowance", path=(0, "bends", 0, "allowance"),
                    expected=4.71238898038469, tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="sheet_rule", path=(0, "rule"),
                    expected="SheetFold Rule",
                ),
                SolidCraftInspectionCheck(
                    id="sheet_thickness", path=(0, "thickness"),
                    expected=2.0, tolerance=0.001,
                ),
                SolidCraftInspectionCheck(
                    id="sheet_k_factor", path=(0, "k_factor"),
                    expected=0.5, tolerance=0.001,
                ),
            ),
        ),
    ),
)
