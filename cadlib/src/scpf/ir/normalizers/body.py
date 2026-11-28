"""Recursive body-history normalization and dispatch.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from ...core import Shape, _dim_add
from ..base import BodyIR, BoxIR, ConeIR, CylinderIR, PlacementIR, SphereIR
from ..body import BooleanIR, IRNode, LegacyShapeIR, TranslationIR

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
    from .features import (
        _portable_hole,
        _portable_pattern,
        _portable_plastic_feature,
        _portable_shell,
    )
    from .operations import _portable_chamfer, _portable_fillet, _portable_revolve
    from .placement import _portable_placement
    from .sheet_metal import _portable_sheet
    from .sketch import _portable_attached_extrude, _portable_extrude

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
