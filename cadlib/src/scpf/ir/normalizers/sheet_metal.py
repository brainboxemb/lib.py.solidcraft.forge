"""Sheet-metal normalization.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from ...core import Shape
from ..base import BodyIR
from ..body import BooleanIR, ShellIR
from ..features import CircularPatternIR, HoleIR, PlasticFeatureIR, RectangularPatternIR
from ..operations import ChamferIR, FilletIR
from ..sheet_metal import (
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
from ..sketch import PlaneIR, SketchIR
from .body import _normalize_node
from .sketch import _profile_ir_from_shape, _sketch_chain_ir

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
