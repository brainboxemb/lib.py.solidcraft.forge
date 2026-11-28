"""Sheet-metal semantic IR.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from ..core import _pv as pv
from .base import BodyIR
from .sketch import SketchChainIR, SketchIR

class SheetRuleIR:
    """Semantic material/bend rule shared by one native sheet history."""

    name: str
    thickness: Any
    bend_radius: Any
    k_factor: Any

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("SheetRuleIR name must be non-empty")
        for value, label in (
            (self.thickness, "thickness"),
            (self.bend_radius, "bend_radius"),
        ):
            if (
                isinstance(value, bool)
                or not isfinite(pv(value))
                or pv(value) <= 0
            ):
                raise ValueError(f"SheetRuleIR {label} must be positive")
        if (
            isinstance(self.k_factor, bool)
            or not isfinite(pv(self.k_factor))
            or not 0 < pv(self.k_factor) < 1
        ):
            raise ValueError("SheetRuleIR k_factor must be between 0 and 1")


class SheetBodyIR(BodyIR):
    """Marker for typed native sheet-metal body/history results."""


@dataclass(frozen=True)
class SheetBaseIR(SheetBodyIR):
    """Flat sheet body created from one closed semantic Sketch/profile."""

    blank: SketchIR | SketchChainIR
    rule: SheetRuleIR
    source_kind: str = "sheet_base"

    def __post_init__(self):
        if not isinstance(self.blank, (SketchIR, SketchChainIR)):
            raise ValueError("SheetBaseIR blank must be typed Sketch intent")
        if isinstance(self.blank, SketchChainIR) and not self.blank.closed:
            raise ValueError("SheetBaseIR chain blank must be closed")
        if not isinstance(self.rule, SheetRuleIR):
            raise ValueError("SheetBaseIR rule must be SheetRuleIR")


@dataclass(frozen=True)
class SheetContourFlangeIR(SheetBodyIR):
    contour: SketchChainIR
    distance: Any
    rule: SheetRuleIR
    flip: bool = False
    reverse: bool = False
    source_kind: str = "sheet_contour_flange"

    def __post_init__(self):
        if not isinstance(self.contour, SketchChainIR) or self.contour.closed:
            raise ValueError("SheetContourFlangeIR contour must be open SketchChainIR")
        if (
            isinstance(self.distance, bool)
            or not isfinite(pv(self.distance))
            or pv(self.distance) <= 0
        ):
            raise ValueError("SheetContourFlangeIR distance must be positive")
        if not isinstance(self.rule, SheetRuleIR):
            raise ValueError("SheetContourFlangeIR rule must be SheetRuleIR")
        if not isinstance(self.flip, bool) or not isinstance(self.reverse, bool):
            raise ValueError("SheetContourFlangeIR flip/reverse must be bool")


@dataclass(frozen=True)
class SheetFoldIR(SheetBodyIR):
    base: BodyIR
    line: tuple[tuple[float, float, float], tuple[float, float, float]] | SketchChainIR
    angle: Any
    fixed: tuple[float, float, float] | None = None
    position: str = "centerline"
    flip: bool = False
    source_kind: str = "sheet_fold"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("SheetFoldIR base must be BodyIR")
        if isinstance(self.line, SketchChainIR):
            if self.line.closed or len(self.line.segments) != 1 or self.line.segments[0].kind != "line":
                raise ValueError("SheetFoldIR Sketch line must be one open straight segment")
        elif (
            not isinstance(self.line, tuple)
            or len(self.line) != 2
            or any(
                not isinstance(point, tuple)
                or len(point) != 3
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not isfinite(value)
                    for value in point
                )
                for point in self.line
            )
        ):
            raise ValueError("SheetFoldIR fixed line must contain two finite XYZ points")
        if (
            isinstance(self.angle, bool)
            or not isfinite(pv(self.angle))
            or pv(self.angle) == 0
            or abs(pv(self.angle)) >= 180
        ):
            raise ValueError("SheetFoldIR angle must be non-zero and below 180 degrees")
        if self.position not in {"centerline", "start", "end", "mould"}:
            raise ValueError("SheetFoldIR position is invalid")
        if not isinstance(self.flip, bool):
            raise ValueError("SheetFoldIR flip must be bool")


@dataclass(frozen=True)
class SheetEdgeFlangeIR(SheetBodyIR):
    base: BodyIR
    edges: tuple[tuple[float, float, float], ...]
    height: Any
    angle: Any = 90
    height_from: str | None = None
    position: str | None = None
    flip: bool = False
    source_kind: str = "sheet_edge_flange"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("SheetEdgeFlangeIR base must be BodyIR")
        if (
            not isinstance(self.edges, tuple)
            or not self.edges
            or any(
                not isinstance(point, tuple)
                or len(point) != 3
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not isfinite(value)
                    for value in point
                )
                for point in self.edges
            )
        ):
            raise ValueError("SheetEdgeFlangeIR edges must be fixed finite XYZ points")
        if (
            isinstance(self.height, bool)
            or not isfinite(pv(self.height))
            or pv(self.height) <= 0
        ):
            raise ValueError("SheetEdgeFlangeIR height must be positive")
        if (
            isinstance(self.angle, bool)
            or not isfinite(pv(self.angle))
            or pv(self.angle) == 0
            or abs(pv(self.angle)) >= 180
        ):
            raise ValueError("SheetEdgeFlangeIR angle must be non-zero and below 180")
        if self.height_from not in {None, "outer", "inner", "tangent"}:
            raise ValueError("SheetEdgeFlangeIR height_from is invalid")
        if self.position not in {
            None, "inside", "outside", "middle", "material_outside", "tangent",
        }:
            raise ValueError("SheetEdgeFlangeIR position is invalid")
        if not isinstance(self.flip, bool):
            raise ValueError("SheetEdgeFlangeIR flip must be bool")


@dataclass(frozen=True)
class SheetHemIR(SheetBodyIR):
    base: BodyIR
    edges: tuple[tuple[float, float, float], ...]
    length: Any
    gap: Any | None = None
    flip: bool = False
    source_kind: str = "sheet_hem"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("SheetHemIR base must be BodyIR")
        if (
            not isinstance(self.edges, tuple)
            or not self.edges
            or any(
                not isinstance(point, tuple)
                or len(point) != 3
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not isfinite(value)
                    for value in point
                )
                for point in self.edges
            )
        ):
            raise ValueError("SheetHemIR edges must be fixed finite XYZ points")
        if (
            isinstance(self.length, bool)
            or not isfinite(pv(self.length))
            or pv(self.length) <= 0
        ):
            raise ValueError("SheetHemIR length must be positive")
        if self.gap is not None and (
            isinstance(self.gap, bool)
            or not isfinite(pv(self.gap))
            or pv(self.gap) <= 0
        ):
            raise ValueError("SheetHemIR gap must be positive")
        if not isinstance(self.flip, bool):
            raise ValueError("SheetHemIR flip must be bool")


@dataclass(frozen=True)
class SheetPathFlangeIR(SheetBodyIR):
    base: BodyIR
    edge: tuple[float, float, float]
    path: SketchChainIR
    radius: Any | None = None
    source_kind: str = "sheet_path_flange"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("SheetPathFlangeIR base must be BodyIR")
        if (
            not isinstance(self.edge, tuple)
            or len(self.edge) != 3
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                for value in self.edge
            )
        ):
            raise ValueError("SheetPathFlangeIR edge must be one fixed finite XYZ point")
        if not isinstance(self.path, SketchChainIR) or self.path.closed:
            raise ValueError("SheetPathFlangeIR path must be open SketchChainIR")
        if any(segment.kind != "line" for segment in self.path.segments):
            raise ValueError("SheetPathFlangeIR currently requires line-only path")
        if self.radius is not None and (
            isinstance(self.radius, bool)
            or not isfinite(pv(self.radius))
            or pv(self.radius) <= 0
        ):
            raise ValueError("SheetPathFlangeIR radius must be positive")


@dataclass(frozen=True)
class SheetPerforateIR(SheetBodyIR):
    base: BodyIR
    diameter: Any
    pitch: Any
    margin: Any | None = None
    pattern: str = "staggered"
    source_kind: str = "sheet_perforate"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("SheetPerforateIR base must be BodyIR")
        for value, label in (
            (self.diameter, "diameter"),
            (self.pitch, "pitch"),
        ):
            if isinstance(value, bool) or not isfinite(pv(value)) or pv(value) <= 0:
                raise ValueError(f"SheetPerforateIR {label} must be positive")
        if self.margin is not None and (
            isinstance(self.margin, bool)
            or not isfinite(pv(self.margin))
            or pv(self.margin) <= 0
        ):
            raise ValueError("SheetPerforateIR margin must be positive")
        if self.pattern not in {"staggered", "square"}:
            raise ValueError("SheetPerforateIR pattern must be staggered or square")


@dataclass(frozen=True)
