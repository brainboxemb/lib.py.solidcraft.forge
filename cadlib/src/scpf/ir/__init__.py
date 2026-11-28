"""Engine-neutral Forge semantic intermediate representation.

This package is the stable compatibility facade for semantic IR. Domain modules
are private implementation ownership boundaries; callers should continue to use
`from scpf.ir import ...`.
"""
from __future__ import annotations

from ..scalar_ir import (
    ScalarBinaryIR,
    ScalarExpressionIR,
    ScalarFunctionIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarPowerIR,
    ScalarUnaryIR,
)
from .base import *
from .sketch import *
from .operations import *
from .configuration import *
from .features import *
from .sheet_metal import *
from .body import *
from .sketch import _polygon_region_interior_point, _region_interior_point
from .normalizers.configuration import normalize_configured_design, resolve_feature_ref
from .normalizers.sketch import normalize_sketch_entities
from .normalize import is_portable, normalize_model, normalize_shape

__all__ = [
    "AxisLineIR",
    "BodyIR",
    "BossFeatureIR",
    "BoundOffsetIR",
    "BooleanIR",
    "BoxIR",
    "ChamferIR",
    "CircleProfileIR",
    "CircularPatternIR",
    "RectangleProfileIR",
    "RoundedRectangleProfileIR",
    "CylinderIR",
    "ConeIR",
    "ExtrudeIR",
    "FaceBoundaryIR",
    "FaceSetIR",
    "FeaturePlacementIR",
    "FeatureRefIR",
    "FilletIR",
    "HoleIR",
    "LipFeatureIR",
    "ConfiguredDesignIR",
    "ConfigurationIR",
    "ConfigurationRowIR",
    "ParameterCellIR",
    "ParameterColumnIR",
    "SuppressionColumnIR",
    "IRNode",
    "LegacyShapeIR",
    "ModelIR",
    "NamedFeatureIR",
    "ParameterIR",
    "ParallelEdgeSetIR",
    "DirectionPairEdgeSetIR",
    "ProfileEdgeSetIR",
    "ExplicitEdgePicksIR",
    "EdgeSelectionIR",
    "PlacementIR",
    "PlasticFeatureIR",
    "PlasticFeatureSpecIR",
    "PolygonProfileIR",
    "PrimitiveIR",
    "ProfileIR",
    "RegionIR",
    "RectangularPatternIR",
    "RevolveIR",
    "ScalarBinaryIR",
    "ScalarExpressionIR",
    "ScalarFunctionIR",
    "ScalarLiteralIR",
    "ScalarParameterRefIR",
    "ScalarPowerIR",
    "ScalarUnaryIR",
    "SketchIR",
    "SketchSupportIR",
    "SketchChainIR",
    "SketchChainSegmentIR",
    "SketchEntityGraphIR",
    "SketchEntityRefIR",
    "SketchGraphEntityIR",
    "SketchMirrorIR",
    "SketchRectangularPatternIR",
    "TextEntityIR",
    "TranslationIR",
    "SheetRuleIR",
    "SheetBodyIR",
    "SheetBaseIR",
    "SheetContourFlangeIR",
    "SheetFoldIR",
    "SheetEdgeFlangeIR",
    "SheetHemIR",
    "SheetPathFlangeIR",
    "SheetPerforateIR",
    "SketchCoordinateDimensionIR",
    "SketchLengthDimensionIR",
    "SketchLineIR",
    "SketchOrientationConstraintIR",
    "SketchPointIR",
    "SketchRelationsIR",
    "ShellIR",
    "SlotProfileIR",
    "SnapFitFeatureIR",
    "SphereIR",
    "RestFeatureIR",
    "_polygon_region_interior_point",
    "_region_interior_point",
    "is_portable",
    "normalize_configured_design",
    "normalize_model",
    "normalize_shape",
    "normalize_sketch_entities",
    "resolve_feature_ref"
]
