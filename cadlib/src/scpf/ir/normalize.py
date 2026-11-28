"""Semantic normalization from public SCPF authoring objects.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from math import isfinite
from typing import Any

from ..core import (
    Anchor,
    Depth,
    Edges,
    Expression,
    Faces,
    Parameter,
    Shape,
    _BoundOffset,
    _DirectionSelector,
    _FaceBoundarySelection,
    _ProfileEdgeSelection,
    _dim_add,
    _hole_spec,
    _pv as pv,
    parameters_in,
)
from ..scalar_ir import (
    ScalarBinaryIR,
    ScalarExpressionIR,
    ScalarFunctionIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarPowerIR,
    ScalarUnaryIR,
)
from .base import (
    BodyIR,
    BoundOffsetIR,
    BoxIR,
    ConeIR,
    CylinderIR,
    FeaturePlacementIR,
    ParameterIR,
    PlacementIR,
    PrimitiveIR,
    SphereIR,
)
from .sketch import (
    CircleProfileIR,
    PlaneIR,
    PolygonProfileIR,
    ProfileIR,
    RectangleProfileIR,
    RegionIR,
    RoundedRectangleProfileIR,
    SketchChainIR,
    SketchChainSegmentIR,
    SketchCoordinateDimensionIR,
    SketchEntityGraphIR,
    SketchEntityRefIR,
    SketchIR,
    SketchLengthDimensionIR,
    SketchLineIR,
    SketchMirrorIR,
    SketchOperationIR,
    SketchOrientationConstraintIR,
    SketchPointIR,
    SketchRectangularPatternIR,
    SketchRelationsIR,
    SketchSupportIR,
    SlotProfileIR,
    TextEntityIR,
    _circle_profile_radii,
    _concentric_circle_region_from_pick,
    _polygon_region_interior_point,
    _region_interior_point,
)
from .operations import (
    AxisLineIR,
    ChamferIR,
    DirectionPairEdgeSetIR,
    EdgeSelectionIR,
    ExplicitEdgePicksIR,
    ExtrudeIR,
    FaceBoundaryIR,
    FaceSetIR,
    FilletIR,
    ParallelEdgeSetIR,
    ProfileEdgeSetIR,
    RevolveIR,
)
from .configuration import (
    ConfiguredDesignIR,
    ConfigurationIR,
    ConfigurationRowIR,
    FeatureRefIR,
    ModelIR,
    NamedFeatureIR,
    ParameterCellIR,
    ParameterColumnIR,
    SuppressionColumnIR,
)
from .features import (
    BossFeatureIR,
    CircularPatternIR,
    HoleIR,
    LipFeatureIR,
    PlasticFeatureIR,
    RectangularPatternIR,
    RestFeatureIR,
    SnapFitFeatureIR,
)
from .sheet_metal import (
    SheetBaseIR,
    SheetBodyIR,
    SheetContourFlangeIR,
    SheetEdgeFlangeIR,
    SheetFoldIR,
    SheetHemIR,
    SheetPathFlangeIR,
    SheetPerforateIR,
    SheetRuleIR,
)
from .body import BooleanIR, IRNode, LegacyShapeIR, ShellIR, TranslationIR

def _collect_parameters(value, found=None):
    """Collect named symbolic parameters in deterministic first-use order."""
    if found is None:
        found = {}

    if isinstance(value, Shape):
        _collect_parameters(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _collect_parameters(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _collect_parameters(item, found)
        return found

    for parameter in parameters_in(value):
        previous = found.setdefault(parameter.name, parameter.value)
        if previous != parameter.value:
            raise ValueError(
                f"conflicting values for parameter {parameter.name}"
            )
    return found


def _count_parameter_names(value, found=None):
    """Collect direct Parameters used as unitless native feature counts."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "rectangular_pattern":
            (
                original,
                _sources,
                _dir1,
                count1,
                _spacing1,
                _dir2,
                count2,
                _spacing2,
                _alignment1,
                _alignment2,
                _reversed1,
                _reversed2,
            ) = value.data
            found.update(
                parameter.name
                for parameter in parameters_in(count1, count2)
            )
            _count_parameter_names(original, found)
            return found
        if value.kind == "sketch_pattern_rectangular":
            (
                source,
                count,
                _spacing,
                _direction,
                count2,
                _spacing2,
                _direction2,
                _alignment,
                _alignment2,
                _reversed,
                _reversed2,
            ) = value.data
            found.update(
                parameter.name
                for parameter in parameters_in(count, count2)
            )
            _count_parameter_names(source, found)
            return found
        if value.kind == "circular_pattern":
            (
                original,
                _sources,
                _axis,
                count,
                _angle,
                _alignment,
                _reversed,
            ) = value.data
            found.update(
                parameter.name for parameter in parameters_in(count)
            )
            _count_parameter_names(original, found)
            return found
        _count_parameter_names(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _count_parameter_names(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _count_parameter_names(item, found)
    return found


def _angle_parameter_names(value, found=None):
    """Collect parameters whose qualified semantic role is an angle."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "hole":
            angle = _hole_spec(value)["countersink_angle"]
            if angle is not None:
                found.update(
                    parameter.name for parameter in parameters_in(angle)
                )
            return found
        if value.kind == "sheet_fold":
            original, _line, angle, _fixed, _position, _flip = value.data
            found.update(parameter.name for parameter in parameters_in(angle))
            _angle_parameter_names(original, found)
            return found
        if value.kind == "sheet_edge_flange":
            original, _edges, _height, angle, _height_from, _position, _flip = value.data
            found.update(parameter.name for parameter in parameters_in(angle))
            _angle_parameter_names(original, found)
            return found
        if value.kind == "circular_pattern":
            (
                original,
                _sources,
                _axis,
                _count,
                angle,
                _alignment,
                _reversed,
            ) = value.data
            if angle is not None:
                found.update(
                    parameter.name for parameter in parameters_in(angle)
                )
            _angle_parameter_names(original, found)
            return found
        if value.kind == "sketch_base_revolve":
            (
                _sketch_name,
                _plane,
                _origin,
                _plane_offset,
                _profiles,
                angle,
                _axis,
                _direction,
                _operations,
                _rotation,
            ) = value.data
            found.update(parameter.name for parameter in parameters_in(angle))
        _angle_parameter_names(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _angle_parameter_names(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _angle_parameter_names(item, found)
    return found


def _length_parameter_names(value, found=None):
    """Collect parameters used in the currently-qualified length-valued slots."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "hole":
            spec = _hole_spec(value)
            for field in (
                "diameter",
                "depth",
                "counterbore_diameter",
                "counterbore_depth",
                "countersink_diameter",
                "thread_depth",
            ):
                candidate = spec[field]
                if candidate is not None and candidate is not Depth.THROUGH_ALL:
                    _length_parameter_names(candidate, found)
            ease_out = spec["ease_out"]
            if ease_out is not None and not isinstance(ease_out, str):
                _length_parameter_names(ease_out, found)
            # Parameter-driven direction is outside typed Hole semantics in
            # #550. Retain its compatibility role while such a model remains
            # on LegacyShapeIR instead of misclassifying countersink angle.
            direction = spec["direction"]
            if direction is not None:
                _length_parameter_names(direction, found)
            return found
        if value.kind == "sheet_base":
            (
                _sketch_name, _plane, origin, plane_offset, profiles, operations,
                thickness, bend_radius, _k_factor, _rule_name,
            ) = value.data
            _length_parameter_names(
                (origin, plane_offset, profiles, operations, thickness, bend_radius),
                found,
            )
            return found
        if value.kind == "sheet_contour_flange":
            contour, distance, thickness, bend_radius, _k_factor, _rule_name, _flip, _reverse = value.data
            _length_parameter_names(
                (contour, distance, thickness, bend_radius),
                found,
            )
            return found
        if value.kind == "sheet_fold":
            original, line, _angle, fixed, _position, _flip = value.data
            _length_parameter_names((original, line, fixed), found)
            return found
        if value.kind == "sheet_edge_flange":
            original, _edges, height, _angle, _height_from, _position, _flip = value.data
            _length_parameter_names((original, height), found)
            return found
        if value.kind == "sheet_hem":
            original, _edges, length, gap, _flip = value.data
            _length_parameter_names((original, length, gap), found)
            return found
        if value.kind == "sheet_path_flange":
            original, _edge, path, radius = value.data
            _length_parameter_names((original, path, radius), found)
            return found
        if value.kind == "sheet_perforate":
            original, diameter, pitch, margin, _pattern = value.data
            _length_parameter_names((original, diameter, pitch, margin), found)
            return found
        if value.kind == "rectangular_pattern":
            (
                original,
                _sources,
                _dir1,
                _count1,
                spacing1,
                _dir2,
                _count2,
                spacing2,
                _alignment1,
                _alignment2,
                _reversed1,
                _reversed2,
            ) = value.data
            _length_parameter_names(original, found)
            _length_parameter_names(spacing1, found)
            if spacing2 is not None:
                _length_parameter_names(spacing2, found)
            return found
        if value.kind == "sketch_pattern_rectangular":
            (
                source,
                _count,
                spacing,
                _direction,
                _count2,
                spacing2,
                _direction2,
                _alignment,
                _alignment2,
                _reversed,
                _reversed2,
            ) = value.data
            _length_parameter_names(source, found)
            _length_parameter_names(spacing, found)
            if spacing2 is not None:
                _length_parameter_names(spacing2, found)
            return found
        if value.kind == "circular_pattern":
            (
                original,
                _sources,
                axis,
                _count,
                _angle,
                _alignment,
                _reversed,
            ) = value.data
            _length_parameter_names(original, found)
            if not isinstance(axis, str):
                origin, _direction = axis
                _length_parameter_names(origin, found)
            return found
        if value.kind == "sketch_base_revolve":
            # The Revolve sweep is the only currently-qualified angle-valued
            # Shape payload. Every other symbolic value in this payload retains
            # the pre-existing CAD-length interpretation.
            for index, item in enumerate(value.data):
                if index != 5:
                    _length_parameter_names(item, found)
            return found
        _length_parameter_names(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _length_parameter_names(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _length_parameter_names(item, found)
        return found

    found.update(parameter.name for parameter in parameters_in(value))
    return found


def _ratio_parameter_names(value, found=None):
    """Collect dimensionless continuous sheet-rule parameters."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "sheet_base":
            _sketch_name, _plane, _origin, _offset, _profiles, _operations, _thickness, _radius, k_factor, _rule = value.data
            found.update(parameter.name for parameter in parameters_in(k_factor))
            return found
        if value.kind == "sheet_contour_flange":
            contour, _distance, _thickness, _radius, k_factor, _rule, _flip, _reverse = value.data
            found.update(parameter.name for parameter in parameters_in(k_factor))
            _ratio_parameter_names(contour, found)
            return found
        _ratio_parameter_names(value.data, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _ratio_parameter_names(item, found)
    return found


def _parameter_ir(shape: Shape) -> tuple[ParameterIR, ...]:
    values = _collect_parameters(shape)
    length_parameters = _length_parameter_names(shape)
    angle_parameters = _angle_parameter_names(shape)
    count_parameters = _count_parameter_names(shape)
    ratio_parameters = _ratio_parameter_names(shape)
    return tuple(
        ParameterIR(
            name,
            value,
            roles=tuple(
                role
                for role, names in (
                    ("length", length_parameters),
                    ("angle", angle_parameters),
                    ("count", count_parameters),
                    ("ratio", ratio_parameters),
                )
                if name in names
            ),
        )
        for name, value in values.items()
    )


def _anchor_vector(anchor) -> tuple[int, int, int]:
    return tuple(int(value) for value in anchor.vector)


def _shift_point(point, delta):
    return tuple(
        _dim_add(current, added)
        for current, added in zip(point, delta)
    )


def _portable_placement(shape: Shape) -> PlacementIR | None:
    """Normalize supported primitive/placement authoring into one IR form."""
    if shape.kind == "box":
        length, width, height, anchor = shape.data
        return PlacementIR(
            primitive=BoxIR(length=length, width=width, height=height),
            point=(0, 0, 0),
            anchor=_anchor_vector(anchor),
        )

    if shape.kind == "cylinder":
        height, diameter, axis, anchor = shape.data
        return PlacementIR(
            primitive=CylinderIR(
                height=height,
                diameter=diameter,
                axis=axis,
            ),
            point=(0, 0, 0),
            anchor=_anchor_vector(anchor),
        )

    if shape.kind == "cone":
        height, diameter, top_diameter, axis, anchor = shape.data
        return PlacementIR(
            primitive=ConeIR(
                height=height,
                diameter=diameter,
                top_diameter=top_diameter,
                axis=axis,
            ),
            point=(0, 0, 0),
            anchor=_anchor_vector(anchor),
        )

    if shape.kind == "sphere":
        radius, anchor = shape.data
        return PlacementIR(
            primitive=SphereIR(radius=radius),
            point=(0, 0, 0),
            anchor=_anchor_vector(anchor),
        )

    if shape.kind == "placed_box":
        box, x, y, z, anchor = shape.data
        if box.kind != "box":
            return None
        length, width, height, _constructor_anchor = box.data
        return PlacementIR(
            primitive=BoxIR(length=length, width=width, height=height),
            point=(x, y, z),
            anchor=_anchor_vector(anchor),
            explicit=True,
        )

    if shape.kind == "placed3d":
        child, x, y, z = shape.data
        if child.kind == "cylinder":
            height, diameter, axis, anchor = child.data
            primitive = CylinderIR(
                height=height,
                diameter=diameter,
                axis=axis,
            )
        elif child.kind == "cone":
            height, diameter, top_diameter, axis, anchor = child.data
            primitive = ConeIR(
                height=height,
                diameter=diameter,
                top_diameter=top_diameter,
                axis=axis,
            )
        else:
            return None
        return PlacementIR(
            primitive=primitive,
            point=(x, y, z),
            anchor=_anchor_vector(anchor),
            explicit=True,
        )

    if shape.kind == "translated":
        child, delta = shape.data
        placement = _portable_placement(child)
        if placement is None:
            return None
        return PlacementIR(
            primitive=placement.primitive,
            point=_shift_point(placement.point, delta),
            anchor=placement.anchor,
            explicit=True,
            source_kind="translated",
        )

    return None


def _portable_csg_placement(node: IRNode) -> bool:
    """Accept the already-qualified primitive PlacementIR forms inside CSG."""
    return (
        isinstance(node, PlacementIR)
        and isinstance(node.primitive, (BoxIR, CylinderIR, ConeIR, SphereIR))
    )


_PLANE_NORMAL_INDEX = {"XY": 2, "XZ": 1, "YZ": 0}
_PLANE_AXES = {
    "XY": {"X", "Y"},
    "XZ": {"X", "Z"},
    "YZ": {"Y", "Z"},
}


def _plane_ir(orientation: str, offset=None) -> PlaneIR | None:
    """Normalize one principal standalone Sketch plane without native ids."""
    if orientation not in _PLANE_NORMAL_INDEX:
        return None
    distance = 0 if offset is None else offset
    origin = [0, 0, 0]
    origin[_PLANE_NORMAL_INDEX[orientation]] = distance
    try:
        return PlaneIR(orientation=orientation, origin=tuple(origin))
    except ValueError:
        return None


def _semantic_dimension_key(value):
    """Identity key for authored CAD dimensions without evaluating symbols."""
    parameters = parameters_in(value)
    if not parameters:
        return ("number", float(pv(value)))
    expression = getattr(value, "expression", None)
    if not isinstance(expression, str) or not expression:
        return None
    return (
        "expression",
        expression,
        tuple(parameter.name for parameter in parameters),
    )


def _same_semantic_dimension(left, right) -> bool:
    """Compare authored dimension intent, using values only when non-symbolic."""
    if left is right:
        return True
    left_key = _semantic_dimension_key(left)
    right_key = _semantic_dimension_key(right)
    if left_key is None or right_key is None:
        return False
    if left_key[0] == right_key[0] == "number":
        return abs(left_key[1] - right_key[1]) <= 1e-12
    return left_key == right_key


def _parameterized_rectangle_relations(
    profile: PolygonProfileIR,
) -> SketchRelationsIR | None:
    """Normalize the bounded #440 rectangle relation graph before lowering."""
    if (
        not isinstance(profile, PolygonProfileIR)
        or len(profile.points) != 4
        or not any(
            parameters_in(value)
            for point in profile.points
            for value in point
        )
    ):
        return None

    p1, p2, p3, p4 = profile.points
    values = tuple(
        tuple(float(pv(value)) for value in point)
        for point in profile.points
    )
    if any(not isfinite(value) for point in values for value in point):
        return None

    # This first slice is deliberately the already-qualified origin-based
    # axis-aligned rectangle from native-revolve. Compare symbolic equality
    # without baking current values into semantic identity.
    if any(parameters_in(value) for value in (p1[0], p1[1], p2[0], p4[1])):
        return None
    if (
        abs(values[0][0]) > 1e-12
        or abs(values[0][1]) > 1e-12
        or abs(values[1][0]) > 1e-12
        or abs(values[3][1]) > 1e-12
        or not _same_semantic_dimension(p2[1], p3[1])
        or not _same_semantic_dimension(p3[0], p4[0])
        or values[1][1] <= 0
        or values[2][0] <= 0
    ):
        return None

    return SketchRelationsIR(
        points=tuple(
            SketchPointIR(position=tuple(point))
            for point in profile.points
        ),
        lines=(
            SketchLineIR(0, 1),
            SketchLineIR(1, 2),
            SketchLineIR(2, 3),
            SketchLineIR(3, 0),
        ),
        constraints=(
            SketchOrientationConstraintIR(0, "vertical"),
            SketchOrientationConstraintIR(1, "horizontal"),
            SketchOrientationConstraintIR(2, "vertical"),
            SketchOrientationConstraintIR(3, "horizontal"),
        ),
        dimensions=(
            SketchLengthDimensionIR(0, p2[1]),
            SketchLengthDimensionIR(1, p3[0]),
        ),
    )


def _parameterized_polygon_coordinate_relations(
    profile: PolygonProfileIR,
) -> SketchRelationsIR | None:
    """Normalize generic parameterized Polygon point coordinates into Sketch IR."""
    if (
        not isinstance(profile, PolygonProfileIR)
        or not any(
            parameters_in(value)
            for point in profile.points
            for value in point
        )
    ):
        return None

    values = tuple(
        tuple(float(pv(value)) for value in point)
        for point in profile.points
    )
    if any(not isfinite(value) for point in values for value in point):
        return None

    point_count = len(profile.points)
    return SketchRelationsIR(
        points=tuple(
            SketchPointIR(position=tuple(point))
            for point in profile.points
        ),
        lines=tuple(
            SketchLineIR(index, (index + 1) % point_count)
            for index in range(point_count)
        ),
        coordinate_dimensions=tuple(
            SketchCoordinateDimensionIR(
                point=index,
                axis=axis,
                value=point[coordinate],
            )
            for index, point in enumerate(profile.points)
            for coordinate, axis in enumerate(("x", "y"))
        ),
    )


def _profile_ir_from_shape(
    profile: Shape,
    profile_anchor,
    offset,
    plane: str,
) -> ProfileIR | None:
    try:
        offset = tuple(offset)
        if len(offset) != 2:
            return None

        if profile.kind == "circle":
            if profile_anchor is not Anchor.CENTER:
                return None
            (diameter,) = profile.data
            return CircleProfileIR(
                diameter=diameter,
                center=offset,
            )

        if profile.kind == "rectangle":
            if profile_anchor is not Anchor.CENTER:
                return None
            width, depth = profile.data
            return RectangleProfileIR(
                width=width,
                depth=depth,
                center=offset,
            )

        if profile.kind == "rounded_rectangle":
            if profile_anchor is not Anchor.CENTER:
                return None
            width, depth, radius = profile.data
            return RoundedRectangleProfileIR(
                width=width,
                depth=depth,
                radius=radius,
                center=offset,
            )

        if profile.kind == "polygon":
            if profile_anchor is not None:
                return None
            points, profile_plane, ids = profile.data
            if profile_plane != plane:
                return None
            shifted = tuple(
                tuple(
                    _dim_add(value, offset[index])
                    for index, value in enumerate(point)
                )
                for point in points
            )
            return PolygonProfileIR(
                points=shifted,
                segment_ids=tuple(ids) if ids is not None else None,
            )

        if profile_anchor is not None:
            return None

        if profile.kind == "slot_center_to_center":
            p0, p1, width = profile.data
            return SlotProfileIR(
                construction="center_to_center",
                points=(tuple(p0), tuple(p1)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_overall":
            p0, p1, width = profile.data
            return SlotProfileIR(
                construction="overall",
                points=(tuple(p0), tuple(p1)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_center_point":
            center, end, width = profile.data
            return SlotProfileIR(
                construction="center_point",
                points=(tuple(center), tuple(end)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_arc_three_point":
            start, through, end, width = profile.data
            return SlotProfileIR(
                construction="arc_three_point",
                points=(tuple(start), tuple(through), tuple(end)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_arc_center":
            center, start, end, sweep, width = profile.data
            if end is not None:
                return SlotProfileIR(
                    construction="arc_center_end",
                    points=(tuple(center), tuple(start), tuple(end)),
                    width=width,
                    offset=offset,
                )
            return SlotProfileIR(
                construction="arc_center_sweep",
                points=(tuple(center), tuple(start)),
                width=width,
                sweep=float(sweep),
                offset=offset,
            )
    except (TypeError, ValueError):
        return None

    return None


def _sketch_graph_from_payload(
    sketch_name,
    plane,
    profiles,
    operations,
) -> SketchEntityGraphIR | None:
    """Normalize stored Sketch entities/operations without requiring Sketch object state."""
    class _PayloadSketch:
        pass

    sketch = _PayloadSketch()
    sketch.name = sketch_name
    sketch.plane = plane

    entities = []
    references = {}
    for index, (profile, profile_anchor, offset) in enumerate(profiles):
        semantic = _sketch_graph_profile_ir(
            sketch,
            profile,
            profile_anchor,
            offset,
        )
        if semantic is None:
            return None
        entities.append(semantic)
        references[id(profile)] = SketchEntityRefIR("entity", index)

    semantic_operations = []
    for index, operation in enumerate(operations):
        source = operation.data[0]
        source_ref = references.get(id(source))
        if source_ref is None:
            return None
        try:
            if operation.kind == "sketch_pattern_rectangular":
                (
                    _source,
                    count,
                    spacing,
                    direction,
                    count2,
                    spacing2,
                    direction2,
                    alignment,
                    alignment2,
                    reversed1,
                    reversed2,
                ) = operation.data
                semantic = SketchRectangularPatternIR(
                    source=source_ref,
                    count=count,
                    spacing=spacing,
                    direction=tuple(direction),
                    count2=count2,
                    spacing2=spacing2,
                    direction2=(
                        tuple(direction2)
                        if direction2 is not None
                        else None
                    ),
                    alignment=alignment,
                    alignment2=alignment2,
                    reversed=reversed1,
                    reversed2=reversed2,
                )
            elif operation.kind == "sketch_mirror":
                _source, axis = operation.data
                semantic = SketchMirrorIR(
                    source=source_ref,
                    axis=axis,
                )
            else:
                return None
        except (TypeError, ValueError):
            return None
        semantic_operations.append(semantic)
        references[id(operation)] = SketchEntityRefIR(
            "operation",
            index,
        )

    try:
        return SketchEntityGraphIR(
            entities=tuple(entities),
            operations=tuple(semantic_operations),
        )
    except ValueError:
        return None


def _sketch_ir_from_payload(
    sketch_name,
    plane,
    origin,
    plane_offset,
    profiles,
    operations,
    rotation,
    *,
    support: SketchSupportIR | None = None,
) -> SketchIR | None:
    if plane not in ("XY", "XZ", "YZ"):
        return None
    if origin is not None and plane_offset is not None:
        return None
    if origin is not None:
        try:
            plane_ir = PlaneIR(
                orientation=plane,
                origin=tuple(origin),
            )
        except (TypeError, ValueError):
            return None
    else:
        plane_ir = _plane_ir(plane, plane_offset)
    if plane_ir is None:
        return None

    graph = _sketch_graph_from_payload(
        sketch_name,
        plane,
        profiles,
        operations,
    )
    if graph is None:
        return None

    semantic_profiles = tuple(
        entity
        for entity in graph.entities
        if isinstance(
            entity,
            (
                CircleProfileIR,
                RectangleProfileIR,
                RoundedRectangleProfileIR,
                SlotProfileIR,
                PolygonProfileIR,
            ),
        )
    )
    relations = None
    if (
        len(semantic_profiles) == 1
        and isinstance(semantic_profiles[0], PolygonProfileIR)
    ):
        polygon = semantic_profiles[0]
        relations = (
            _parameterized_rectangle_relations(polygon)
            or _parameterized_polygon_coordinate_relations(polygon)
        )

    try:
        return SketchIR(
            name=sketch_name,
            plane=plane_ir,
            profiles=semantic_profiles,
            relations=relations,
            support=support,
            rotation=(
                None
                if rotation is None
                else tuple(float(value) for value in rotation)
            ),
            graph=graph,
        )
    except (TypeError, ValueError):
        return None


def _extrude_regions(
    sketch: SketchIR,
    profile_picks,
    exact_regions,
) -> tuple[RegionIR, ...] | None:
    """Normalize public all-region or point-selected region intent.

    Existing directly-resolvable concentric/polygon families retain stronger
    semantic boundary membership. General picks remain authored selector intent.
    """
    if profile_picks is not None:
        if not isinstance(profile_picks, (tuple, list)):
            return None

        # A single explicitly selected profile remains explicit selector intent
        # so the native command preserves its authored profiles=[...] spelling.
        if len(sketch.profiles) == 1:
            try:
                return tuple(
                    RegionIR(
                        selector=tuple(float(value) for value in point),
                        exact=exact_regions,
                    )
                    for point in profile_picks
                )
            except (TypeError, ValueError):
                return None

        # Preserve the already-qualified stronger membership model only when
        # the source really is the bounded concentric-circle family.
        concentric = (
            exact_regions
            and sketch.graph is not None
            and not sketch.graph.operations
            and sketch.profiles
            and all(
                isinstance(profile, CircleProfileIR)
                for profile in sketch.profiles
            )
            and len(sketch.profiles) == len(sketch.graph.entities)
        )
        if concentric:
            try:
                _circle_profile_radii(sketch)
            except ValueError:
                concentric = False

        if concentric:
            try:
                return tuple(
                    _concentric_circle_region_from_pick(sketch, point)
                    for point in profile_picks
                )
            except ValueError:
                return None

        # Preserve exact single-polygon membership for the older qualified
        # profile contract (normally reached above only if graph/profile
        # composition changes later).
        if (
            exact_regions
            and sketch.graph is not None
            and not sketch.graph.operations
            and len(sketch.profiles) == 1
            and isinstance(sketch.profiles[0], PolygonProfileIR)
            and len(profile_picks) == 1
        ):
            try:
                return (
                    _polygon_region_from_exact_pick(
                        sketch,
                        profile_picks[0],
                    ),
                )
            except ValueError:
                return None

        try:
            return tuple(
                RegionIR(
                    selector=tuple(float(value) for value in point),
                    exact=exact_regions,
                )
                for point in profile_picks
            )
        except (TypeError, ValueError):
            return None

    if exact_regions:
        return None

    if (
        sketch.graph is not None
        and not sketch.graph.operations
        and len(sketch.profiles) == 1
        and len(sketch.graph.entities) == 1
        and not isinstance(sketch.graph.entities[0], TextEntityIR)
    ):
        try:
            region = RegionIR(outer=0)
            _region_interior_point(sketch, region)
            return (region,)
        except ValueError:
            pass
    return ()


def _portable_extrude(shape: Shape) -> ExtrudeIR | None:
    """Normalize standalone Sketch + Extrude semantics."""
    if shape.kind != "sketch_base_extrusion":
        return None

    (
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        distance,
        direction,
        operations,
        profile_picks,
        exact_regions,
        rotation,
    ) = shape.data

    sketch = _sketch_ir_from_payload(
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        operations,
        rotation,
    )
    if sketch is None or direction not in {
        "positive", "negative", "symmetric"
    }:
        return None
    regions = _extrude_regions(
        sketch,
        profile_picks,
        exact_regions,
    )
    if regions is None:
        return None
    if distance is Depth.THROUGH_ALL:
        return None

    try:
        return ExtrudeIR(
            sketch=sketch,
            regions=regions,
            distance=distance,
            direction=direction,
        )
    except ValueError:
        return None


def _portable_attached_extrude(
    target: IRNode,
    target_shape: Shape,
    tool_shape: Shape,
    operation: str,
) -> ExtrudeIR | None:
    """Normalize Sketch(on=...) extrusion over one already-typed target."""
    if (
        not isinstance(target, BodyIR)
        or tool_shape.kind != "explicit_sketch_extrusion"
        or operation not in {"join", "cut"}
    ):
        return None

    (
        sketch_name,
        authored_target,
        parent_anchor,
        plane_info,
        profiles,
        distance,
        direction,
        operations,
        profile_picks,
        exact_regions,
    ) = tool_shape.data
    if authored_target is not target_shape:
        return None
    plane_name, sketch_origin, sketch_rotation = plane_info

    # A default supported Sketch uses the public anchor surface. An explicit
    # plane remains a world frame while target still owns the body operation.
    if plane_name is None:
        try:
            parent = Anchor(parent_anchor).value
        except (TypeError, ValueError):
            return None
        plane_name = "XY"
        support = SketchSupportIR(
            target=target,
            parent=parent,
        )
        semantic_origin = None
    else:
        support = SketchSupportIR(
            target=target,
            parent=None,
        )
        semantic_origin = sketch_origin

    sketch = _sketch_ir_from_payload(
        sketch_name,
        plane_name,
        semantic_origin,
        None,
        profiles,
        operations,
        sketch_rotation,
        support=support,
    )
    if sketch is None or direction not in {
        "positive", "negative", "symmetric"
    }:
        return None
    regions = _extrude_regions(
        sketch,
        profile_picks,
        exact_regions,
    )
    if regions is None:
        return None

    through_all = distance is Depth.THROUGH_ALL
    if through_all and operation != "cut":
        return None

    try:
        return ExtrudeIR(
            sketch=sketch,
            regions=regions,
            distance=None if through_all else distance,
            direction=direction,
            operation=operation,
            target=target,
            through_all=through_all,
            source_kind="explicit_sketch_extrusion",
        )
    except ValueError:
        return None


def _axis_line_ir(axis) -> AxisLineIR | None:
    """Normalize public principal/custom axis intent without native ids."""
    if isinstance(axis, str):
        if axis not in {"X", "Y", "Z"}:
            return None
        return AxisLineIR(direction=axis)

    if (
        not isinstance(axis, (tuple, list))
        or len(axis) != 2
    ):
        return None
    origin, direction = axis
    if (
        not isinstance(origin, (tuple, list))
        or len(origin) != 3
        or not isinstance(direction, (tuple, list))
        or len(direction) != 3
    ):
        return None

    vector = tuple(float(value) for value in direction)
    principal = {
        "X": (1.0, 0.0, 0.0),
        "Y": (0.0, 1.0, 0.0),
        "Z": (0.0, 0.0, 1.0),
    }
    semantic_direction = next(
        (
            name
            for name, expected in principal.items()
            if all(
                abs(actual - wanted) <= 1e-12
                for actual, wanted in zip(vector, expected)
            )
        ),
        None,
    )
    if semantic_direction is None:
        return None

    try:
        return AxisLineIR(
            direction=semantic_direction,
            origin=tuple(origin),
        )
    except ValueError:
        return None


def _axis_line_in_sketch_plane(axis: AxisLineIR, plane: PlaneIR) -> bool:
    """Check semantic coplanarity for the bounded principal-plane slice."""
    if (
        not isinstance(plane, PlaneIR)
        or axis.direction not in _PLANE_AXES[plane.orientation]
    ):
        return False
    normal_index = _PLANE_NORMAL_INDEX[plane.orientation]
    return _same_semantic_dimension(
        axis.origin[normal_index],
        plane.origin[normal_index],
    )


def _contains_untyped_expression(value) -> bool:
    """Return whether authored intent contains compatibility-only expression text."""
    if isinstance(value, Expression):
        return value.scalar_ir is None
    if isinstance(value, Shape):
        return _contains_untyped_expression(value.data)
    if isinstance(value, dict):
        return any(
            _contains_untyped_expression(key)
            or _contains_untyped_expression(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list)):
        return any(_contains_untyped_expression(item) for item in value)
    return False


def _portable_revolve(
    shape: Shape,
    *,
    operation: str = "new_body",
    target: PlacementIR | None = None,
) -> RevolveIR | None:
    """Normalize the complete current public standalone Sketch Revolve grammar."""
    if shape.kind != "sketch_base_revolve":
        return None

    (
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        angle,
        axis,
        direction,
        operations,
        rotation,
    ) = shape.data

    if origin is not None or rotation is not None or len(profiles) != 1:
        return None
    if operations:
        return None
    if _contains_untyped_expression(
        (profiles, angle, axis, plane_offset)
    ):
        return None
    if direction not in (None, "symmetric"):
        return None
    if operation not in {"new_body", "cut"}:
        return None
    if operation == "new_body" and target is not None:
        return None
    if operation == "cut" and not isinstance(target, PlacementIR):
        return None

    sketch = _sketch_ir_from_payload(
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        operations,
        rotation,
    )
    if (
        sketch is None
        or sketch.support is not None
        or sketch.graph is None
        or len(sketch.graph.entities) != 1
        or sketch.graph.operations
        or not isinstance(
            sketch.graph.entities[0],
            (
                CircleProfileIR,
                RectangleProfileIR,
                RoundedRectangleProfileIR,
                PolygonProfileIR,
                SketchChainIR,
            ),
        )
    ):
        return None

    axis_ir = _axis_line_ir(axis)
    if axis_ir is None or not _axis_line_in_sketch_plane(
        axis_ir,
        sketch.plane,
    ):
        return None

    # A direct supported closed profile retains one explicit semantic region.
    # A connected profile is a completed Sketch-chain result; public Revolve
    # consumes that result as a whole and has no profile-selector argument.
    region = None
    if (
        sketch.graph is not None
        and not sketch.graph.operations
        and len(sketch.profiles) == 1
        and len(sketch.graph.entities) == 1
    ):
        candidate = RegionIR(outer=0)
        try:
            _region_interior_point(sketch, candidate)
        except ValueError:
            pass
        else:
            region = candidate

    try:
        return RevolveIR(
            sketch=sketch,
            region=region,
            axis=axis_ir,
            angle=angle,
            direction=direction,
            operation=operation,
            target=target,
        )
    except ValueError:
        return None



def _edge_selection_ir(edges) -> EdgeSelectionIR | None:
    """Normalize the public shared fillet/chamfer selector vocabulary."""
    if edges is Edges.VERTICAL:
        return ParallelEdgeSetIR("Z")

    if isinstance(edges, _FaceBoundarySelection):
        try:
            return FaceBoundaryIR(
                tuple(Faces(face).value for face in edges.faces)
            )
        except (TypeError, ValueError):
            return None

    if isinstance(edges, _ProfileEdgeSelection):
        try:
            return ProfileEdgeSetIR(
                patterns=tuple(edges.patterns),
                kind=edges.kind,
                sides=edges.sides,
            )
        except (TypeError, ValueError):
            return None

    if (
        isinstance(edges, (tuple, list))
        and edges
        and all(isinstance(edge, (Anchor, _DirectionSelector)) for edge in edges)
    ):
        vectors = []
        for edge in edges:
            try:
                vector = (
                    tuple(int(value) for value in edge.vector)
                    if isinstance(edge, Anchor)
                    else tuple(edge.vector)
                )
            except (TypeError, ValueError):
                return None
            vectors.append(vector)
        try:
            return DirectionPairEdgeSetIR(tuple(vectors))
        except ValueError:
            return None

    if isinstance(edges, (tuple, list)) and edges:
        try:
            return ExplicitEdgePicksIR(
                tuple(tuple(point) for point in edges)
            )
        except (TypeError, ValueError):
            return None

    return None


def _portable_fillet(shape: Shape) -> FilletIR | None:
    """Normalize public constant-radius Fillet with shared selector semantics."""
    if shape.kind != "fillet" or len(shape.data) != 3:
        return None

    base_shape, radius, edges = shape.data
    semantic_edges = _edge_selection_ir(edges)
    if semantic_edges is None:
        return None
    if (
        isinstance(radius, bool)
        or not isinstance(radius, (int, float, Parameter, Expression))
        or not isfinite(pv(radius))
        or pv(radius) <= 0
    ):
        return None

    base = _normalize_node(base_shape)
    if not isinstance(base, BodyIR):
        return None

    try:
        return FilletIR(base=base, radius=radius, edges=semantic_edges)
    except ValueError:
        return None


def _portable_chamfer(shape: Shape) -> ChamferIR | None:
    """Normalize public Chamfer with the shared semantic edge vocabulary."""
    if shape.kind != "chamfer":
        return None

    if len(shape.data) == 3:
        base_shape, distance, edges = shape.data
        distance2 = None
        flip = False
    elif len(shape.data) == 5:
        base_shape, distance, edges, distance2, flip = shape.data
    else:
        return None

    if not isinstance(flip, bool) or (flip and distance2 is None):
        return None
    semantic_edges = _edge_selection_ir(edges)
    if semantic_edges is None:
        return None

    base = _normalize_node(base_shape)
    if not isinstance(base, BodyIR):
        return None

    try:
        return ChamferIR(
            base=base,
            distance=distance,
            edges=semantic_edges,
            distance2=distance2,
            flip=flip,
        )
    except ValueError:
        return None


def _semantic_feature_offset(value):
    if isinstance(value, _BoundOffset):
        return BoundOffsetIR(
            axis=value.axis,
            reference=value.reference,
            delta=value.delta,
        )
    return value


def _anchored_feature_placement(
    tool_shape: Shape,
    target_shape: Shape,
) -> tuple[Shape, FeaturePlacementIR] | None:
    if tool_shape.kind != "anchored":
        return None
    child, authored_target, parent_anchor, child_anchor, offset = tool_shape.data
    if authored_target is not target_shape and authored_target != target_shape:
        return None
    try:
        placement = FeaturePlacementIR(
            mode="anchored",
            parent_anchor=parent_anchor.value,
            child_anchor=child_anchor.value,
            offset=tuple(
                _semantic_feature_offset(value)
                for value in offset
            ),
        )
    except (AttributeError, TypeError, ValueError):
        return None
    return child, placement


def _absolute_feature_placement(
    tool_shape: Shape,
) -> tuple[Shape, FeaturePlacementIR] | None:
    if tool_shape.kind != "placed3d":
        return None
    feature, x, y, z = tool_shape.data
    if not isinstance(feature, Shape):
        return None
    try:
        placement = FeaturePlacementIR(
            mode="absolute",
            point=(x, y, z),
        )
    except (TypeError, ValueError):
        return None
    return feature, placement


def _hole_ir_from_feature(
    target: BodyIR,
    feature: Shape,
    placement: FeaturePlacementIR,
) -> HoleIR | None:
    if feature.kind != "hole":
        return None
    spec = _hole_spec(feature)
    direction = spec["direction"]
    if direction is not None:
        if (
            not isinstance(direction, (tuple, list))
            or len(direction) != 3
            or any(parameters_in(value) for value in direction)
        ):
            return None
        try:
            semantic_direction = tuple(float(pv(value)) for value in direction)
        except (TypeError, ValueError):
            return None
        if (
            any(not isfinite(value) for value in semantic_direction)
            or all(value == 0 for value in semantic_direction)
        ):
            return None
    else:
        semantic_direction = None

    countersink_angle = spec["countersink_angle"]
    if countersink_angle is not None:
        try:
            angle_value = pv(countersink_angle)
        except (TypeError, ValueError):
            return None
        if not isfinite(angle_value) or not 0 < angle_value < 180:
            return None

    depth = spec["depth"]
    if depth is Depth.THROUGH_ALL:
        depth_mode = "through_all"
        semantic_depth = None
    else:
        depth_mode = "distance"
        semantic_depth = depth

    try:
        return HoleIR(
            target=target,
            placement=placement,
            hole_type=spec["type"],
            diameter=spec["diameter"],
            depth_mode=depth_mode,
            depth=semantic_depth,
            direction=semantic_direction,
            counterbore_diameter=spec["counterbore_diameter"],
            counterbore_depth=spec["counterbore_depth"],
            countersink_diameter=spec["countersink_diameter"],
            countersink_angle=countersink_angle,
            thread=spec["thread"],
            hand=spec["hand"],
            thread_depth=spec["thread_depth"],
            modeled=spec["modeled"],
            ease_out=spec["ease_out"],
        )
    except ValueError:
        return None


def _portable_hole(
    target: IRNode,
    target_shape: Shape,
    tool_shape: Shape,
) -> HoleIR | None:
    """Normalize absolute or stable anchored Hole-family feature placement."""
    if not isinstance(target, BodyIR):
        return None

    while tool_shape.kind == "exported_feature":
        tool_shape, _name = tool_shape.data

    absolute = _absolute_feature_placement(tool_shape)
    if absolute is not None:
        feature, placement = absolute
        return _hole_ir_from_feature(target, feature, placement)

    anchored = _anchored_feature_placement(tool_shape, target_shape)
    if anchored is None:
        return None
    feature, placement = anchored
    if feature.kind != "hole":
        return None

    # Placement semantics are backend-neutral. Backend support for a
    # particular anchor/variant is checked during lowering, not by forcing
    # valid authored Hole intent back through LegacyShapeIR.
    return _hole_ir_from_feature(target, feature, placement)


def _fixed_vector_from_shape(value):
    if value is None:
        return None
    if (
        not isinstance(value, (tuple, list))
        or len(value) != 3
        or any(parameters_in(component) for component in value)
    ):
        return None
    try:
        vector = tuple(float(pv(component)) for component in value)
    except (TypeError, ValueError):
        return None
    if (
        any(not isfinite(component) for component in vector)
        or all(component == 0 for component in vector)
    ):
        return None
    return vector


def _plastic_feature_spec_ir(feature: Shape) -> PlasticFeatureSpecIR | None:
    try:
        if feature.kind == "lip":
            width, height = feature.data
            return LipFeatureIR(width=width, height=height)

        if feature.kind == "snap_fit":
            (
                length,
                thickness,
                width,
                catch_depth,
                catch_length,
                hook,
                direction,
            ) = feature.data
            hook_ir = _fixed_vector_from_shape(hook)
            direction_ir = _fixed_vector_from_shape(direction)
            if hook_ir is None or (
                direction is not None and direction_ir is None
            ):
                return None
            return SnapFitFeatureIR(
                length=length,
                thickness=thickness,
                width=width,
                catch_depth=catch_depth,
                catch_length=catch_length,
                hook=hook_ir,
                direction=direction_ir,
            )

        if feature.kind == "boss":
            diameter, height, hole_diameter, direction = feature.data
            direction_ir = _fixed_vector_from_shape(direction)
            if direction is not None and direction_ir is None:
                return None
            return BossFeatureIR(
                diameter=diameter,
                height=height,
                hole_diameter=hole_diameter,
                direction=direction_ir,
            )

        if feature.kind == "rest":
            width, height, length, along, direction = feature.data
            along_ir = _fixed_vector_from_shape(along)
            direction_ir = _fixed_vector_from_shape(direction)
            if (
                (along is not None and along_ir is None)
                or (direction is not None and direction_ir is None)
            ):
                return None
            return RestFeatureIR(
                width=width,
                height=height,
                length=length,
                along=along_ir,
                direction=direction_ir,
            )
    except (TypeError, ValueError):
        return None
    return None


def _portable_plastic_feature(
    target: IRNode,
    target_shape: Shape,
    tool_shape: Shape,
) -> PlasticFeatureIR | None:
    if not isinstance(target, BodyIR):
        return None

    while tool_shape.kind == "exported_feature":
        tool_shape, _name = tool_shape.data

    placed = _absolute_feature_placement(tool_shape)
    if placed is None:
        placed = _anchored_feature_placement(tool_shape, target_shape)
    if placed is None:
        return None

    feature, placement = placed
    spec = _plastic_feature_spec_ir(feature)
    if spec is None:
        return None
    try:
        return PlasticFeatureIR(
            target=target,
            placement=placement,
            feature=spec,
        )
    except ValueError:
        return None


def _pattern_axis_ir(axis_spec) -> AxisLineIR | None:
    if isinstance(axis_spec, str):
        try:
            return AxisLineIR(direction=axis_spec)
        except ValueError:
            return None
    if (
        not isinstance(axis_spec, (tuple, list))
        or len(axis_spec) != 2
    ):
        return None
    origin, direction = axis_spec
    if (
        not isinstance(origin, (tuple, list))
        or len(origin) != 3
        or not isinstance(direction, (tuple, list))
        or len(direction) != 3
        or any(parameters_in(value) for value in direction)
    ):
        return None
    try:
        return AxisLineIR(
            direction=tuple(float(pv(value)) for value in direction),
            origin=tuple(origin),
        )
    except (TypeError, ValueError):
        return None


def _portable_pattern(shape: Shape) -> BodyIR | None:
    if shape.kind == "rectangular_pattern":
        (
            original,
            sources,
            direction1,
            count1,
            spacing1,
            direction2,
            count2,
            spacing2,
            alignment1,
            alignment2,
            reversed1,
            reversed2,
        ) = shape.data
        base = _normalize_node(original)
        if not isinstance(base, BodyIR):
            return None
        try:
            refs = tuple(
                _pattern_authored_feature_ref(original, base, source)
                for source in sources
            )
            if any(ref is None for ref in refs):
                return None
            node = RectangularPatternIR(
                base=base,
                sources=refs,
                direction1=tuple(float(value) for value in direction1),
                count1=count1,
                spacing1=spacing1,
                direction2=(
                    tuple(float(value) for value in direction2)
                    if direction2 is not None
                    else None
                ),
                count2=count2,
                spacing2=spacing2,
                alignment1=alignment1,
                alignment2=alignment2,
                reversed1=reversed1,
                reversed2=reversed2,
            )
            for ref in refs:
                resolve_feature_ref(base, ref)
            return node
        except (TypeError, ValueError):
            return None

    if shape.kind == "circular_pattern":
        (
            original,
            sources,
            axis_spec,
            count,
            angle,
            alignment,
            reversed,
        ) = shape.data
        base = _normalize_node(original)
        axis = _pattern_axis_ir(axis_spec)
        if not isinstance(base, BodyIR) or axis is None:
            return None
        try:
            refs = tuple(
                _pattern_authored_feature_ref(original, base, source)
                for source in sources
            )
            if any(ref is None for ref in refs):
                return None
            node = CircularPatternIR(
                base=base,
                sources=refs,
                axis=axis,
                count=count,
                angle=angle,
                alignment=alignment,
                reversed=reversed,
            )
            for ref in refs:
                resolve_feature_ref(base, ref)
            return node
        except (TypeError, ValueError):
            return None

    return None


def _portable_shell(shape: Shape) -> ShellIR | None:
    """Normalize shell intent over any already typed body history."""
    if shape.kind != "shell" or len(shape.data) != 3:
        return None

    base_shape, thickness, faces = shape.data
    base = _normalize_node(base_shape)
    if not isinstance(base, BodyIR):
        return None

    try:
        semantic_faces = FaceSetIR(
            tuple(Faces(face).value for face in faces)
        )
        return ShellIR(
            base=base,
            thickness=thickness,
            open_faces=semantic_faces,
        )
    except (TypeError, ValueError):
        return None


def _sketch_chain_ir(
    shape: Shape,
    *,
    closed: bool | None = None,
    name: str | None = None,
    plane: str | None = None,
    offset=(0, 0),
) -> SketchChainIR | None:
    """Normalize authored connected Sketch paths without native curve ids."""
    if shape.kind == "sketch_open_chain":
        sketch_name, orientation, plane_offset, _start, segments = shape.data
        if closed is True:
            return None
        plane_ir = _plane_ir(orientation, plane_offset)
        if plane_ir is None:
            return None
        chain_name = sketch_name
        is_closed = False
        profile_offset = (0, 0)
    elif shape.kind == "connected_profile":
        if closed is False or name is None:
            return None
        _start, segments = shape.data
        plane_ir = _plane_ir(plane) if plane is not None else None
        if plane is not None and plane_ir is None:
            return None
        chain_name = name
        is_closed = True
        profile_offset = tuple(offset)
        if len(profile_offset) != 2:
            return None
    else:
        return None

    semantic = []
    for segment in segments:
        kind = segment[0]
        if kind == "line":
            _kind, start, end = segment
            through = center = None
            clockwise = None
        elif kind == "arc_tangent":
            _kind, start, end = segment
            through = center = None
            clockwise = None
        elif kind == "arc_three_point":
            _kind, start, end, through = segment
            center = None
            clockwise = None
        elif kind == "arc_center_point":
            _kind, start, end, center, clockwise = segment
            through = None
        else:
            return None

        def shifted(point):
            if point is None:
                return None
            return tuple(
                _dim_add(point[index], profile_offset[index])
                for index in range(2)
            )

        try:
            semantic.append(
                SketchChainSegmentIR(
                    kind=kind,
                    start=shifted(start),
                    end=shifted(end),
                    through=shifted(through),
                    center=shifted(center),
                    clockwise=clockwise,
                )
            )
        except ValueError:
            return None

    try:
        return SketchChainIR(
            name=chain_name,
            plane=plane_ir,
            segments=tuple(semantic),
            closed=is_closed,
        )
    except ValueError:
        return None


def _sketch_graph_profile_ir(
    sketch,
    profile: Shape,
    profile_anchor,
    offset,
) -> SketchGraphEntityIR | None:
    if profile.kind == "text":
        if profile_anchor is not None:
            return None
        text, height, font = profile.data
        try:
            return TextEntityIR(
                text=text,
                height=height,
                font=font,
                position=tuple(offset),
            )
        except (TypeError, ValueError):
            return None

    if profile.kind == "connected_profile":
        if profile_anchor is not None:
            return None
        return _sketch_chain_ir(
            profile,
            closed=True,
            name=sketch.name,
            plane=sketch.plane,
            offset=offset,
        )

    semantic_plane = sketch.plane
    if semantic_plane is None and profile.kind == "polygon":
        semantic_plane = profile.data[1]
    if semantic_plane is None:
        semantic_plane = "XY"
    return _profile_ir_from_shape(
        profile,
        profile_anchor,
        offset,
        semantic_plane,
    )


def normalize_sketch_entities(sketch) -> SketchEntityGraphIR:
    """Normalize public Sketch contents independently from support/consumers."""
    from ..explicit_sketch import Sketch

    if not isinstance(sketch, Sketch):
        raise TypeError("Sketch entity normalization requires a Sketch")
    if not sketch._closed or sketch._token is not None:
        raise ValueError(
            "Sketch entity normalization requires a completed Sketch scope"
        )

    entities = []
    references = {}
    for index, (profile, profile_anchor, offset) in enumerate(
        sketch._profiles
    ):
        semantic = _sketch_graph_profile_ir(
            sketch,
            profile,
            profile_anchor,
            offset,
        )
        if semantic is None:
            raise ValueError(
                f"Sketch entity {profile.kind!r} is outside semantic graph IR"
            )
        entities.append(semantic)
        references[id(profile)] = SketchEntityRefIR("entity", index)

    open_chains = []
    for chain in sketch._chains:
        semantic = _sketch_chain_ir(chain, closed=False)
        if semantic is None:
            raise ValueError(
                "Sketch open chain is outside semantic SketchChainIR"
            )
        open_chains.append(semantic)

    operations = []
    for index, operation in enumerate(sketch._operations):
        source = operation.data[0]
        source_ref = references.get(id(source))
        if source_ref is None:
            raise ValueError(
                "Sketch operation source has no semantic graph identity"
            )

        if operation.kind == "sketch_pattern_rectangular":
            (
                _source,
                count,
                spacing,
                direction,
                count2,
                spacing2,
                direction2,
                alignment,
                alignment2,
                reversed1,
                reversed2,
            ) = operation.data
            semantic = SketchRectangularPatternIR(
                source=source_ref,
                count=count,
                spacing=spacing,
                direction=tuple(direction),
                count2=count2,
                spacing2=spacing2,
                direction2=(
                    tuple(direction2)
                    if direction2 is not None
                    else None
                ),
                alignment=alignment,
                alignment2=alignment2,
                reversed=reversed1,
                reversed2=reversed2,
            )
        elif operation.kind == "sketch_mirror":
            _source, axis = operation.data
            semantic = SketchMirrorIR(
                source=source_ref,
                axis=axis,
            )
        else:
            raise ValueError(
                f"unsupported Sketch operation {operation.kind!r}"
            )

        operations.append(semantic)
        references[id(operation)] = SketchEntityRefIR(
            "operation",
            index,
        )

    return SketchEntityGraphIR(
        entities=tuple(entities),
        open_chains=tuple(open_chains),
        operations=tuple(operations),
    )


def _sheet_rule_ir(
    name,
    thickness,
    bend_radius,
    k_factor,
) -> SheetRuleIR | None:
    try:
        return SheetRuleIR(
            name=name,
            thickness=thickness,
            bend_radius=bend_radius,
            k_factor=k_factor,
        )
    except ValueError:
        return None


def _portable_sheet_base(shape: Shape) -> SheetBaseIR | None:
    if shape.kind != "sheet_base":
        return None
    (
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        operations,
        thickness,
        bend_radius,
        k_factor,
        rule_name,
    ) = shape.data
    if (
        plane != "XY"
        or origin is not None
        or plane_offset is not None
        or operations
        or len(profiles) != 1
    ):
        return None

    rule = _sheet_rule_ir(rule_name, thickness, bend_radius, k_factor)
    if rule is None:
        return None

    profile, profile_anchor, offset = profiles[0]
    if profile.kind == "connected_profile":
        if profile_anchor is not None:
            return None
        blank = _sketch_chain_ir(
            profile,
            closed=True,
            name=sketch_name,
            plane=plane,
            offset=offset,
        )
    else:
        semantic = _profile_ir_from_shape(
            profile,
            profile_anchor,
            offset,
            plane,
        )
        if semantic is None:
            return None
        blank = SketchIR(
            name=sketch_name,
            plane=PlaneIR("XY"),
            profiles=(semantic,),
        )
    if blank is None:
        return None
    try:
        return SheetBaseIR(blank=blank, rule=rule)
    except ValueError:
        return None


def _is_sheet_history(node: BodyIR) -> bool:
    """Return whether a typed body history originates from sheet material."""
    if isinstance(node, SheetBodyIR):
        return True
    if isinstance(node, (HoleIR, PlasticFeatureIR)):
        return _is_sheet_history(node.target)
    if isinstance(node, (ChamferIR, FilletIR, ShellIR)):
        return _is_sheet_history(node.base)
    if isinstance(node, (RectangularPatternIR, CircularPatternIR)):
        return _is_sheet_history(node.base)
    if isinstance(node, BooleanIR) and isinstance(node.target, BodyIR):
        return _is_sheet_history(node.target)
    return False


def _portable_sheet(shape: Shape) -> SheetBodyIR | None:
    base = _portable_sheet_base(shape)
    if base is not None:
        return base

    if shape.kind == "sheet_contour_flange":
        (
            contour, distance, thickness, bend_radius, k_factor,
            rule_name, flip, reverse,
        ) = shape.data
        chain = _sketch_chain_ir(contour, closed=False)
        rule = _sheet_rule_ir(rule_name, thickness, bend_radius, k_factor)
        if chain is None or rule is None:
            return None
        try:
            return SheetContourFlangeIR(
                contour=chain,
                distance=distance,
                rule=rule,
                flip=flip,
                reverse=reverse,
            )
        except ValueError:
            return None

    if shape.kind not in {
        "sheet_fold",
        "sheet_edge_flange",
        "sheet_hem",
        "sheet_path_flange",
        "sheet_perforate",
    }:
        return None

    original = shape.data[0]
    typed_base = _portable_sheet(original)
    if typed_base is None:
        # Sheet history may contain another already-typed body operation, such
        # as a Hole between the flat blank and a Fold.
        normalized = _normalize_node(original)
        if not isinstance(normalized, BodyIR) or not _is_sheet_history(normalized):
            return None
        typed_base = normalized

    try:
        if shape.kind == "sheet_fold":
            _original, line, angle, fixed, position, flip = shape.data
            if isinstance(line, Shape):
                semantic_line = _sketch_chain_ir(line, closed=False)
                if semantic_line is None:
                    return None
            else:
                semantic_line = tuple(tuple(float(v) for v in point) for point in line)
            return SheetFoldIR(
                base=typed_base,
                line=semantic_line,
                angle=angle,
                fixed=None if fixed is None else tuple(float(v) for v in fixed),
                position=position,
                flip=flip,
            )

        if shape.kind == "sheet_edge_flange":
            (
                _original, edges, height, angle,
                height_from, position, flip,
            ) = shape.data
            return SheetEdgeFlangeIR(
                base=typed_base,
                edges=tuple(tuple(point) for point in edges),
                height=height,
                angle=angle,
                height_from=height_from,
                position=position,
                flip=flip,
            )

        if shape.kind == "sheet_hem":
            _original, edges, length, gap, flip = shape.data
            return SheetHemIR(
                base=typed_base,
                edges=tuple(tuple(point) for point in edges),
                length=length,
                gap=gap,
                flip=flip,
            )

        if shape.kind == "sheet_path_flange":
            _original, edge, path, radius = shape.data
            semantic_path = _sketch_chain_ir(path, closed=False)
            if semantic_path is None:
                return None
            return SheetPathFlangeIR(
                base=typed_base,
                edge=tuple(edge),
                path=semantic_path,
                radius=radius,
            )

        _original, diameter, pitch, margin, pattern = shape.data
        return SheetPerforateIR(
            base=typed_base,
            diameter=diameter,
            pitch=pitch,
            margin=margin,
            pattern=pattern,
        )
    except (TypeError, ValueError):
        return None


def _translation_compatible_body(node: IRNode) -> bool:
    """Return whether current stable body translation supports this typed tree."""
    if isinstance(node, PlacementIR):
        return isinstance(
            node.primitive,
            (BoxIR, CylinderIR, ConeIR, SphereIR),
        )
    if isinstance(node, TranslationIR):
        return _translation_compatible_body(node.body)
    if isinstance(node, BooleanIR):
        return (
            _translation_compatible_body(node.target)
            and _translation_compatible_body(node.tool)
        )
    return False


def _translation_ir(shape: Shape) -> TranslationIR | None:
    """Normalize current working translated primitive/CSG body semantics."""
    if shape.kind != "translated":
        return None
    child, offset = shape.data
    body = _normalize_node(child)
    if not _translation_compatible_body(body):
        return None
    if isinstance(body, TranslationIR):
        offset = tuple(
            _dim_add(body.offset[index], offset[index])
            for index in range(3)
        )
        body = body.body
    try:
        return TranslationIR(
            body=body,
            offset=tuple(offset),
        )
    except (TypeError, ValueError):
        return None


def _normalize_node(shape: Shape) -> IRNode:
    if shape.kind == "exported_feature":
        source, _name = shape.data
        return _normalize_node(source)
    if shape.kind == "named_feature":
        source, _name, _suppressed = shape.data
        return _normalize_node(source)

    sheet = _portable_sheet(shape)
    if sheet is not None:
        return sheet

    placement = _portable_placement(shape)
    if placement is not None:
        return placement

    translation = _translation_ir(shape)
    if translation is not None:
        return translation

    if shape.kind in {"union", "difference", "intersection"}:
        target_shape, tool_shape = shape.data

        # Preserve an authored subtractive Revolve as that feature rather than
        # manufacturing a new-body Revolve followed by a generic Boolean.
        if shape.kind == "difference":
            target_placement = _portable_placement(target_shape)
            if (
                target_placement is not None
                and isinstance(target_placement.primitive, BoxIR)
            ):
                revolve_cut = _portable_revolve(
                    tool_shape,
                    operation="cut",
                    target=target_placement,
                )
                if revolve_cut is not None:
                    return revolve_cut

        target = _normalize_node(target_shape)
        if shape.kind in {"union", "difference"}:
            attached_extrude = _portable_attached_extrude(
                target,
                target_shape,
                tool_shape,
                "join" if shape.kind == "union" else "cut",
            )
            if attached_extrude is not None:
                return attached_extrude
            hole = _portable_hole(target, target_shape, tool_shape)
            if hole is not None:
                return hole
        if shape.kind == "union":
            plastic = _portable_plastic_feature(
                target,
                target_shape,
                tool_shape,
            )
            if plastic is not None:
                return plastic

        tool = _normalize_node(tool_shape)
        if isinstance(target, BodyIR) and isinstance(tool, BodyIR):
            operation = {
                "union": "join",
                "difference": "cut",
                "intersection": "intersect",
            }[shape.kind]
            return BooleanIR(
                operation=operation,
                target=target,
                tool=tool,
            )
        return LegacyShapeIR(shape=shape, source_kind=shape.kind)

    extrude = _portable_extrude(shape)
    if extrude is not None:
        return extrude

    revolve = _portable_revolve(shape)
    if revolve is not None:
        return revolve

    fillet = _portable_fillet(shape)
    if fillet is not None:
        return fillet

    chamfer = _portable_chamfer(shape)
    if chamfer is not None:
        return chamfer

    pattern = _portable_pattern(shape)
    if pattern is not None:
        return pattern

    shell = _portable_shell(shape)
    if shell is not None:
        return shell

    return LegacyShapeIR(shape=shape, source_kind=shape.kind)


def resolve_feature_ref(root: IRNode, reference: FeatureRefIR) -> IRNode:
    """Resolve one semantic feature path without backend/native identity."""
    if not isinstance(reference, FeatureRefIR):
        raise TypeError("feature reference resolution requires FeatureRefIR")
    if reference.path[0] != "root":
        raise ValueError("FeatureRefIR path must begin at root")

    node = root
    for segment in reference.path[1:]:
        if isinstance(node, TranslationIR) and segment == "body":
            node = node.body
            continue
        if isinstance(node, BooleanIR) and segment in {"target", "tool"}:
            node = getattr(node, segment)
            continue
        if isinstance(node, (HoleIR, PlasticFeatureIR)) and segment == "target":
            node = node.target
            continue
        if isinstance(node, (ChamferIR, FilletIR, ShellIR)) and segment == "base":
            node = node.base
            continue
        if (
            isinstance(node, RevolveIR)
            and segment == "target"
            and node.target is not None
        ):
            node = node.target
            continue
        if isinstance(
            node,
            (RectangularPatternIR, CircularPatternIR),
        ) and segment == "base":
            node = node.base
            continue
        raise ValueError(
            f"FeatureRefIR path segment {segment!r} is not valid for "
            f"{type(node).__name__}"
        )
    return node


def _pattern_authored_feature_ref(
    design: Shape,
    root: BodyIR,
    feature: Shape,
    *,
    path: tuple[str, ...] = ("root",),
) -> FeatureRefIR | None:
    """Map exact authored source identity to semantic body-history roles."""
    if design is feature:
        return FeatureRefIR(path=path)

    if design.kind in {"exported_feature", "named_feature"}:
        source = design.data[0]
        return _pattern_authored_feature_ref(
            source,
            root,
            feature,
            path=path,
        )

    if (
        isinstance(root, (HoleIR, PlasticFeatureIR, BooleanIR))
        and design.kind in {"union", "difference", "intersection"}
    ):
        target_shape, tool_shape = design.data
        while tool_shape.kind == "exported_feature":
            tool_shape, _name = tool_shape.data
        if feature is tool_shape:
            return FeatureRefIR(path=path)
        target = root.target
        if isinstance(target, BodyIR):
            return _pattern_authored_feature_ref(
                target_shape,
                target,
                feature,
                path=(*path, "target"),
            )
        return None

    if (
        isinstance(root, (ChamferIR, FilletIR, ShellIR))
        and design.kind in {"chamfer", "fillet", "shell"}
    ):
        base_shape = design.data[0]
        return _pattern_authored_feature_ref(
            base_shape,
            root.base,
            feature,
            path=(*path, "base"),
        )

    if (
        isinstance(root, RevolveIR)
        and root.operation == "cut"
        and design.kind == "difference"
    ):
        target_shape, tool_shape = design.data
        if feature is tool_shape:
            return FeatureRefIR(path=path)
        if isinstance(root.target, BodyIR):
            return _pattern_authored_feature_ref(
                target_shape,
                root.target,
                feature,
                path=(*path, "target"),
            )
        return None

    if (
        isinstance(root, (RectangularPatternIR, CircularPatternIR))
        and design.kind in {"rectangular_pattern", "circular_pattern"}
    ):
        original = design.data[0]
        return _pattern_authored_feature_ref(
            original,
            root.base,
            feature,
            path=(*path, "base"),
        )

    return None


def _boolean_authored_feature_ref(
    design: Shape,
    root: BooleanIR,
    feature: Shape,
    *,
    path: tuple[str, ...] = ("root",),
) -> FeatureRefIR | None:
    """Map authored CSG object identity to typed semantic history roles."""
    if design is feature:
        return FeatureRefIR(path=path)
    if design.kind in {"exported_feature", "named_feature"}:
        return _boolean_authored_feature_ref(
            design.data[0],
            root,
            feature,
            path=path,
        )
    if design.kind not in {"union", "difference", "intersection"}:
        return None

    target_shape, tool_shape = design.data
    if feature is tool_shape:
        return FeatureRefIR(path=(*path, "tool"))

    if feature is target_shape and isinstance(root.target, BodyIR):
        return FeatureRefIR(path=(*path, "target"))

    if isinstance(root.target, BooleanIR):
        nested = _boolean_authored_feature_ref(
            target_shape,
            root.target,
            feature,
            path=(*path, "target"),
        )
        if nested is not None:
            return nested

    if isinstance(root.tool, BooleanIR):
        nested = _boolean_authored_feature_ref(
            tool_shape,
            root.tool,
            feature,
            path=(*path, "tool"),
        )
        if nested is not None:
            return nested
    return None


def _configuration_feature_ref(
    design: Shape,
    feature: Shape,
    root: IRNode,
) -> FeatureRefIR:
    """Resolve authored identity to semantic IR before native ids exist."""
    if feature is design and isinstance(root, BodyIR):
        return FeatureRefIR(path=("root",))

    if isinstance(root, TranslationIR) and design.kind == "translated":
        child, _offset = design.data
        reference = _configuration_feature_ref(
            child,
            feature,
            root.body,
        )
        translated = FeatureRefIR(
            path=("root", "body", *reference.path[1:]),
        )
        resolve_feature_ref(root, translated)
        return translated

    # Keep the already-qualified #424 authored Revolve-cut identity stable: the
    # source tool becomes the semantic root feature rather than a Boolean tool.
    if (
        isinstance(root, RevolveIR)
        and root.operation == "cut"
        and design.kind == "difference"
    ):
        _target, authored_tool = design.data
        if feature is not authored_tool:
            raise ValueError(
                "suppression feature is not the authored root Revolve feature"
            )
        return FeatureRefIR(path=("root",))

    if isinstance(root, BooleanIR):
        reference = _boolean_authored_feature_ref(design, root, feature)
        if reference is not None:
            # Resolve immediately so malformed semantic paths fail during
            # frontend normalization rather than in a backend.
            resolve_feature_ref(root, reference)
            return reference
        raise ValueError(
            "suppression feature is not a member of the typed Boolean history"
        )

    if isinstance(root, BodyIR):
        reference = _pattern_authored_feature_ref(
            design,
            root,
            feature,
        )
        if reference is not None:
            resolve_feature_ref(root, reference)
            return reference

    raise ValueError(
        "portable suppression requires a qualified semantic feature history"
    )


def _normalize_configuration(configured, feature_resolver) -> ConfigurationIR:
    """Normalize the v0.26 final-model configuration table semantics."""
    from ..configurations import (
        _Configuration,
        _ParameterColumn,
        _SuppressionColumn,
    )

    if not isinstance(configured, _Configuration):
        raise TypeError("configuration normalization requires _Configuration")

    columns = []
    for column in configured.columns:
        if isinstance(column, _ParameterColumn):
            columns.append(ParameterColumnIR(column.name))
        elif isinstance(column, _SuppressionColumn):
            columns.append(
                SuppressionColumnIR(
                    feature=feature_resolver(column.feature)
                )
            )
        else:
            raise ValueError(
                "configuration column is outside current public semantics"
            )

    rows = []
    for name, cells in configured.rows:
        converted = []
        for column, cell in zip(columns, cells):
            if isinstance(column, SuppressionColumnIR):
                if cell == "true":
                    converted.append(True)
                elif cell == "false":
                    converted.append(False)
                else:
                    raise ValueError(
                        "suppression configuration cell must be bool"
                    )
            else:
                converted.append(ParameterCellIR(cell))
        rows.append(
            ConfigurationRowIR(
                name=name,
                cells=tuple(converted),
            )
        )

    return ConfigurationIR(
        active=configured.active,
        columns=tuple(columns),
        rows=tuple(rows),
    )


def _authored_assembly(value):
    """Return one authored Assembly without importing backend assembly lowering."""
    from ..model_objects import Assembly, ModelInstance

    if isinstance(value, ModelInstance):
        return Assembly((value,))
    if isinstance(value, Assembly):
        return value
    raise TypeError(
        "configured assembly target must be ModelInstance or Assembly"
    )


def _assembly_configuration_feature_ref(
    authored_design,
    assembly_ir,
    feature,
):
    """Resolve assembly suppression identity to semantic definition identity."""
    from ..assembly_ir import ComponentFeatureRefIR
    from ..model_objects import _ComponentFeatureReference

    assembly = _authored_assembly(authored_design)
    definition_ids = {}
    definition_instances = {}
    for instance in assembly.instances:
        key = instance.definition.key
        if key in definition_ids:
            continue
        definition_ids[key] = f"definition_{len(definition_ids) + 1}"
        definition_instances[key] = instance

    if isinstance(feature, _ComponentFeatureReference):
        try:
            definition_id = definition_ids[feature.definition_key]
        except KeyError as exc:
            raise ValueError(
                "component feature reference is not part of configured design"
            ) from exc
        definition = next(
            item
            for item in assembly_ir.definitions
            if item.id == definition_id
        )
        if feature.name not in definition.exported_features:
            raise ValueError(
                f"component definition has no exported feature {feature.name!r}"
            )
        return ComponentFeatureRefIR(
            definition=definition_id,
            name=feature.name,
        )

    if not isinstance(feature, Shape):
        raise ValueError(
            "assembly suppression requires Shape or exported component feature"
        )

    exported_matches = []
    for key, instance in definition_instances.items():
        for name, exported in instance.definition.features:
            if feature is exported:
                exported_matches.append(
                    ComponentFeatureRefIR(
                        definition=definition_ids[key],
                        name=name,
                    )
                )
    if len(exported_matches) == 1:
        return exported_matches[0]
    if len(exported_matches) > 1:
        raise ValueError(
            "exported suppression Shape is ambiguous across component definitions"
        )

    raise ValueError(
        "Assembly suppression Shape must be an explicitly exported component feature"
    )


def _named_feature_ir(design: Shape, root: IRNode) -> tuple[NamedFeatureIR, ...]:
    """Collect public feature() identity/state without backend-native names."""
    found = []

    def visit(value):
        if isinstance(value, Shape):
            if value.kind == "named_feature":
                _source, name, suppressed = value.data
                reference = _configuration_feature_ref(
                    design,
                    value,
                    root,
                )
                found.append(
                    NamedFeatureIR(
                        name=name,
                        feature=reference,
                        suppressed=suppressed,
                    )
                )
                visit(value.data[0])
                return
            visit(value.data)
            return
        if isinstance(value, (tuple, list)):
            for item in value:
                visit(item)

    visit(design)
    return tuple(found)


def normalize_configured_design(
    design,
) -> ModelIR | ConfiguredDesignIR:
    """Normalize v0.26 final-model configuration over Shape or Assembly."""
    from ..configurations import _Configuration
    from ..model_objects import Assembly, ModelInstance

    configured = getattr(design, "_configuration", None)
    if not isinstance(configured, _Configuration):
        raise TypeError(
            "configured Forge IR normalization requires final-model configuration"
        )

    if isinstance(design, Shape):
        root = _normalize_node(design)
        if isinstance(root, LegacyShapeIR):
            raise ValueError(
                "configured design is outside the qualified portable IR slice"
            )
        configuration = _normalize_configuration(
            configured,
            lambda feature: _configuration_feature_ref(
                design,
                feature,
                root,
            ),
        )
        return ModelIR(
            root=root,
            parameters=_parameter_ir(design),
            configuration=configuration,
            named_features=_named_feature_ir(design, root),
        )

    if isinstance(design, (ModelInstance, Assembly)):
        from ..assembly_ir import normalize_assembly

        assembly_ir = normalize_assembly(design)
        configuration = _normalize_configuration(
            configured,
            lambda feature: _assembly_configuration_feature_ref(
                design,
                assembly_ir,
                feature,
            ),
        )
        return ConfiguredDesignIR(
            design=assembly_ir,
            configuration=configuration,
        )

    raise TypeError(
        "configured design target is outside current public semantics"
    )


def normalize_model(value) -> ModelIR | ConfiguredDesignIR:
    """Normalize one current Forge result into backend-independent semantic IR."""
    from ..model_objects import Assembly, ModelInstance

    if isinstance(value, Shape):
        if getattr(value, "_configuration", None) is not None:
            return normalize_configured_design(value)
        root = _normalize_node(value)
        return ModelIR(
            root=root,
            parameters=_parameter_ir(value),
            named_features=(
                _named_feature_ir(value, root)
                if isinstance(root, BodyIR)
                else ()
            ),
        )
    if isinstance(value, (ModelInstance, Assembly)):
        if getattr(value, "_configuration", None) is not None:
            return normalize_configured_design(value)
    raise TypeError(
        "Forge IR normalization requires Shape or configured ModelInstance/Assembly"
    )

def normalize_shape(shape: Shape) -> ModelIR:
    """Normalize one Forge Shape into backend-independent semantic IR."""
    if not isinstance(shape, Shape):
        raise TypeError("Forge IR normalization requires a Shape")
    return normalize_model(shape)


def is_portable(model: ModelIR | ConfiguredDesignIR) -> bool:
    """Return whether one semantic design no longer depends on LegacyShapeIR."""
    if isinstance(model, ModelIR):
        return not isinstance(model.root, LegacyShapeIR)
    if isinstance(model, ConfiguredDesignIR):
        from ..assembly_ir import AssemblyIR

        if isinstance(model.design, ModelIR):
            return is_portable(model.design)
        if isinstance(model.design, AssemblyIR):
            return all(
                is_portable(definition.model)
                for definition in model.design.definitions
            )
    return False
