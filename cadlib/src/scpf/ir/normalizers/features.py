"""Hole, plastic feature, pattern and shell normalization.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from math import isfinite

from ...core import Depth, Faces, Shape, _BoundOffset, _hole_spec, _pv as pv, parameters_in
from ..base import BodyIR, BoundOffsetIR, FeaturePlacementIR
from ..body import IRNode, LegacyShapeIR, ShellIR
from ..features import (
    BossFeatureIR,
    CircularPatternIR,
    HoleIR,
    LipFeatureIR,
    PlasticFeatureIR,
    PlasticFeatureSpecIR,
    RectangularPatternIR,
    RestFeatureIR,
    SnapFitFeatureIR,
)
from ..operations import AxisLineIR, FaceSetIR
from .body import _normalize_node
from .configuration import _pattern_authored_feature_ref, resolve_feature_ref

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
