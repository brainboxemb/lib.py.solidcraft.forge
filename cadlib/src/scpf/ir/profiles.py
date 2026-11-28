"""Profile and region semantic IR.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite
from typing import Any

from ..core import _pv as pv

@dataclass(frozen=True)
class CircleProfileIR:
    """One closed circular 2D profile inside a semantic Sketch."""

    diameter: Any
    center: tuple[Any, Any] = (0, 0)
    source_kind: str = "circle"


@dataclass(frozen=True)
class RectangleProfileIR:
    """Dimension-defined rectangle around one semantic sketch-local centre."""

    width: Any
    depth: Any
    center: tuple[Any, Any] = (0, 0)
    source_kind: str = "rectangle"

    def __post_init__(self):
        if (
            isinstance(self.width, bool)
            or isinstance(self.depth, bool)
            or not isfinite(pv(self.width))
            or not isfinite(pv(self.depth))
            or pv(self.width) <= 0
            or pv(self.depth) <= 0
        ):
            raise ValueError(
                "RectangleProfileIR width/depth must be positive CAD dimensions"
            )
        if (
            not isinstance(self.center, tuple)
            or len(self.center) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.center
            )
        ):
            raise ValueError(
                "RectangleProfileIR center must contain two finite CAD dimensions"
            )


@dataclass(frozen=True)
class RoundedRectangleProfileIR:
    """Rectangle profile whose four corners share one circular radius."""

    width: Any
    depth: Any
    radius: Any
    center: tuple[Any, Any] = (0, 0)
    source_kind: str = "rounded_rectangle"

    def __post_init__(self):
        if (
            isinstance(self.width, bool)
            or isinstance(self.depth, bool)
            or isinstance(self.radius, bool)
            or not isfinite(pv(self.width))
            or not isfinite(pv(self.depth))
            or not isfinite(pv(self.radius))
            or pv(self.width) <= 0
            or pv(self.depth) <= 0
            or pv(self.radius) <= 0
            or pv(self.radius) * 2 >= min(pv(self.width), pv(self.depth))
        ):
            raise ValueError(
                "RoundedRectangleProfileIR requires positive dimensions and "
                "radius below half the shorter side"
            )
        if (
            not isinstance(self.center, tuple)
            or len(self.center) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.center
            )
        ):
            raise ValueError(
                "RoundedRectangleProfileIR center must contain two finite CAD dimensions"
            )


@dataclass(frozen=True)
class SlotProfileIR:
    """One authored native Slot construction in semantic sketch coordinates."""

    construction: str
    points: tuple[tuple[Any, Any], ...]
    width: Any
    sweep: float | None = None
    offset: tuple[Any, Any] = (0, 0)
    source_kind: str = "slot"

    def __post_init__(self):
        expected = {
            "center_to_center": 2,
            "overall": 2,
            "center_point": 2,
            "arc_three_point": 3,
            "arc_center_end": 3,
            "arc_center_sweep": 2,
        }
        if self.construction not in expected:
            raise ValueError("SlotProfileIR construction is unsupported")
        if (
            not isinstance(self.points, tuple)
            or len(self.points) != expected[self.construction]
            or any(
                not isinstance(point, tuple)
                or len(point) != 2
                or any(
                    isinstance(value, bool) or not isfinite(pv(value))
                    for value in point
                )
                for point in self.points
            )
        ):
            raise ValueError(
                "SlotProfileIR points do not match the construction contract"
            )
        if (
            isinstance(self.width, bool)
            or not isfinite(pv(self.width))
            or pv(self.width) <= 0
        ):
            raise ValueError("SlotProfileIR width must be positive")
        if (
            not isinstance(self.offset, tuple)
            or len(self.offset) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.offset
            )
        ):
            raise ValueError(
                "SlotProfileIR offset must contain two finite CAD dimensions"
            )

        numeric = tuple(
            tuple(float(pv(value)) for value in point)
            for point in self.points
        )
        if self.construction in {
            "center_to_center",
            "overall",
            "center_point",
        }:
            if numeric[0] == numeric[1]:
                raise ValueError("straight SlotProfileIR endpoints must differ")
            if self.construction == "overall":
                if hypot(
                    numeric[1][0] - numeric[0][0],
                    numeric[1][1] - numeric[0][1],
                ) <= pv(self.width):
                    raise ValueError(
                        "overall SlotProfileIR length must exceed width"
                    )
        elif self.construction == "arc_three_point":
            if len(set(numeric)) != 3:
                raise ValueError(
                    "arc-three-point SlotProfileIR points must be distinct"
                )
        else:
            if numeric[0] == numeric[1]:
                raise ValueError(
                    "arc-center SlotProfileIR center and start must differ"
                )
            if self.construction == "arc_center_sweep":
                if (
                    self.sweep is None
                    or isinstance(self.sweep, bool)
                    or not isinstance(self.sweep, (int, float))
                    or not isfinite(self.sweep)
                    or not 0 < self.sweep < 360
                ):
                    raise ValueError(
                        "arc-center SlotProfileIR sweep must be fixed in (0, 360)"
                    )
            elif self.sweep is not None:
                raise ValueError(
                    "arc-center end SlotProfileIR must not also carry sweep"
                )


@dataclass(frozen=True)
class PolygonProfileIR:
    """One closed straight-segment profile in Sketch-local coordinates."""

    points: tuple[tuple[Any, Any], ...]
    segment_ids: tuple[str, ...] | None = None
    source_kind: str = "polygon"

    def __post_init__(self):
        if (
            not isinstance(self.points, tuple)
            or len(self.points) < 3
            or any(
                not isinstance(point, tuple) or len(point) != 2
                for point in self.points
            )
        ):
            raise ValueError(
                "PolygonProfileIR points must be at least three 2D tuples"
            )
        if self.segment_ids is not None:
            if (
                not isinstance(self.segment_ids, tuple)
                or len(self.segment_ids) != len(self.points)
                or any(
                    not isinstance(value, str) or not value
                    for value in self.segment_ids
                )
                or len(set(self.segment_ids)) != len(self.segment_ids)
            ):
                raise ValueError(
                    "PolygonProfileIR segment_ids must uniquely name every edge"
                )


ProfileIR = (
    CircleProfileIR
    | RectangleProfileIR
    | RoundedRectangleProfileIR
    | SlotProfileIR
    | PolygonProfileIR
)

@dataclass(frozen=True)
class RegionIR:
    """Closed Sketch region by profile membership or authored local selector."""

    outer: int | None = None
    holes: tuple[int, ...] = ()
    selector: tuple[float, float] | None = None
    exact: bool = False

    def __post_init__(self):
        membership = self.outer is not None
        selected = self.selector is not None
        if membership == selected:
            raise ValueError(
                "RegionIR requires exactly one membership or selector representation"
            )
        if membership:
            if type(self.outer) is not int or self.outer < 0:
                raise ValueError(
                    "RegionIR outer must be a non-negative profile index"
                )
            if (
                not isinstance(self.holes, tuple)
                or any(
                    type(index) is not int or index < 0
                    for index in self.holes
                )
            ):
                raise ValueError(
                    "RegionIR holes must contain non-negative profile indexes"
                )
            if self.outer in self.holes:
                raise ValueError(
                    "RegionIR outer profile cannot also be a hole"
                )
            if len(set(self.holes)) != len(self.holes):
                raise ValueError(
                    "RegionIR hole profile indexes must be unique"
                )
            if self.exact:
                raise ValueError(
                    "membership RegionIR does not need exact selector mode"
                )
            return

        if self.holes:
            raise ValueError("selector RegionIR cannot carry profile holes")
        if (
            not isinstance(self.selector, tuple)
            or len(self.selector) != 2
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                for value in self.selector
            )
        ):
            raise ValueError(
                "RegionIR selector must be one fixed finite Sketch-local point"
            )
        if not isinstance(self.exact, bool):
            raise ValueError("RegionIR exact must be bool")
