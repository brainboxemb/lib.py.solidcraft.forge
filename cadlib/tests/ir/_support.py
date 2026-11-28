"""Contracts for the engine-neutral Forge semantic IR boundary."""
import unittest

from scpf import (
    Anchor,
    Axis,
    AxisLine,
    Boss,
    Box,
    Circle2D,
    Cone,
    CounterboreHole,
    CountersinkHole,
    Cylinder,
    Depth,
    Edges,
    Faces,
    feature,
    FRONT,
    Hole,
    LEFT,
    Lip,
    Parameter,
    Polygon2D,
    Rectangle2D,
    RoundedRectangle2D,
    Sketch,
    SlotArcCenter2D,
    SlotArcThreePoint2D,
    SlotCenterPoint2D,
    SlotCenterToCenter2D,
    SlotOverall2D,
    Rest,
    SnapFit,
    Sphere,
    ThreadedHole,
    X,
    Y,
)
from scpf.backends.mitcad import compile_ir as compile_mitcad_ir
from scpf.backends.solidcraft import compile_ir as compile_solidcraft_ir
from scpf.core import Expression
from scpf.compiler import (
    ModelError,
    _compile_model_with_dependencies,
    _compile_shape_legacy_with_dependencies,
)
from scpf.ir import (
    AxisLineIR,
    BodyIR,
    BossFeatureIR,
    BoundOffsetIR,
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    CircularPatternIR,
    ConeIR,
    CylinderIR,
    DirectionPairEdgeSetIR,
    ExplicitEdgePicksIR,
    ExtrudeIR,
    FaceBoundaryIR,
    FaceSetIR,
    FeaturePlacementIR,
    FeatureRefIR,
    FilletIR,
    HoleIR,
    LipFeatureIR,
    PlasticFeatureIR,
    RestFeatureIR,
    SnapFitFeatureIR,
    ConfigurationIR,
    ConfigurationRowIR,
    SuppressionColumnIR,
    LegacyShapeIR,
    ModelIR,
    NamedFeatureIR,
    ParameterIR,
    ParallelEdgeSetIR,
    PlacementIR,
    PlaneIR,
    PolygonProfileIR,
    ProfileEdgeSetIR,
    RegionIR,
    RectangleProfileIR,
    RectangularPatternIR,
    RevolveIR,
    RoundedRectangleProfileIR,
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    SketchIR,
    TextEntityIR,
    TranslationIR,
    SketchCoordinateDimensionIR,
    SketchLengthDimensionIR,
    SketchLineIR,
    SketchOrientationConstraintIR,
    SketchPointIR,
    SketchRelationsIR,
    SketchChainIR,
    SheetBaseIR,
    SheetContourFlangeIR,
    SheetEdgeFlangeIR,
    SheetFoldIR,
    SheetHemIR,
    SheetPathFlangeIR,
    SheetPerforateIR,
    SheetRuleIR,
    ShellIR,
    SlotProfileIR,
    SphereIR,
    normalize_model,
    normalize_shape,
    resolve_feature_ref,
)



class SemanticIRTestCase(unittest.TestCase):
    def assert_solidcraft_compatibility(self, shape, name):
        model = normalize_shape(shape)
        self.assertNotIsInstance(model.root, LegacyShapeIR)
        current = compile_solidcraft_ir(model, name)
        legacy = _compile_shape_legacy_with_dependencies(shape, name)[0]
        self.assertEqual(current, legacy)
        return model


__all__ = [name for name in globals() if not name.startswith("__")]
