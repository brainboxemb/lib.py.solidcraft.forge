"""Compatibility facade for Forge frontend authoring implementation domains."""

from .frontend.scalars import (
    number_text, _NativeExpression, _native_expression, _native_dependencies,
    _plain_command_value, _scalar_ir_value, _scalar_binary_ir, _scalar_power_ir,
    _scalar_negation_ir, Parameter, Expression, _scaled_direction,
    up, down, left, right, front, back, half, midpoint, _pv, _track_pv_reads,
    pv, command_value, parameters_in, _dim_add, _dim_sub, _dim_abs,
)
from .frontend.selectors import (
    _DirectionSelector, Anchor, _direction_selector, _combine_direction_selectors,
    _selector_rank, _selector_anchor, AnchorFrame, AnchorTopology, Depth, Axis,
    Edges, _ProfileEdgeSelection, _feature_edge_selection, Faces,
    _FaceBoundarySelection, _BoundOffset, _AxisRef, _pattern_direction, AxisLine,
    X, Y, Z, CENTER, TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK, UP, DOWN,
)
from .frontend.shape import (
    _shape_center, _pattern_count, _pattern_angle, _circular_pattern_axis,
    _shape_contains, _feature_pattern_sources, _feature_history_step_count,
    _FeatureHandle, _FeatureScope, feature, Shape, _shape,
)
from .frontend.profiles import (
    Text2D, Rectangle2D, RoundedRectangle2D,
    _slot_point, _slot_points_equal, _slot_width,
    SlotCenterToCenter2D, SlotOverall2D, SlotCenterPoint2D,
    SlotArcThreePoint2D, SlotArcCenter2D, Circle2D, Polygon2D,
)
from .frontend.primitives import (
    _box_corner_from_anchor, _primitive_center_from_anchor,
    _cylinder_base_from_anchor, _cone_base_from_anchor,
    _sphere_center_from_anchor, Box, Sphere, Cylinder, Cone,
)
from .frontend.features import (
    _hole_spec, _validate_hole_direction, _hole_feature,
    Hole, CounterboreHole, CountersinkHole, ThreadedHole,
    Lip, SnapFit, Boss, Rest,
)
