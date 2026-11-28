"""Core semantic IR values, primitive geometry and placement.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from ..core import Anchor, _pv as pv

class ParameterIR:
    """One named editable Forge parameter with semantic use roles."""

    name: str
    value: float
    roles: tuple[str, ...] = ("length",)

    def __post_init__(self):
        if (
            not isinstance(self.roles, tuple)
            or not self.roles
            or any(
                role not in {"length", "angle", "count", "ratio"}
                for role in self.roles
            )
            or len(set(self.roles)) != len(self.roles)
            or self.roles != tuple(
                role
                for role in ("length", "angle", "count", "ratio")
                if role in self.roles
            )
        ):
            raise ValueError(
                "ParameterIR roles must be canonical length/angle/count/ratio roles"
            )

    @property
    def unit(self) -> str:
        """Compatibility view for native single-role parameter spelling."""
        if self.roles == ("length",):
            return "mm"
        if self.roles == ("angle",):
            return "deg"
        return ""


@dataclass(frozen=True)
class BoxIR:
    """Axis-aligned box geometry independent of placement."""

    length: Any
    width: Any
    height: Any
    source_kind: str = "box"


@dataclass(frozen=True)
class CylinderIR:
    """Principal-axis cylinder geometry independent of placement."""

    height: Any
    diameter: Any
    axis: str
    source_kind: str = "cylinder"


@dataclass(frozen=True)
class ConeIR:
    """Principal-axis cone/frustum geometry independent of placement."""

    height: Any
    diameter: Any
    top_diameter: Any
    axis: str
    source_kind: str = "cone"


@dataclass(frozen=True)
class SphereIR:
    """Spherical primitive geometry independent of native diameter spelling."""

    radius: Any
    source_kind: str = "sphere"


PrimitiveIR = BoxIR | CylinderIR | ConeIR | SphereIR


class BodyIR:
    """Marker for one engine-neutral typed body result/history node."""


@dataclass(frozen=True)
class BoundOffsetIR:
    """Semantic offset from one named X/Y bound of a parent body."""

    axis: str
    reference: str
    delta: Any = 0

    def __post_init__(self):
        if self.axis not in {"X", "Y"}:
            raise ValueError("BoundOffsetIR axis must be X or Y")
        if self.reference not in {"min", "center", "max"}:
            raise ValueError(
                "BoundOffsetIR reference must be min, center or max"
            )
        if isinstance(self.delta, bool) or not isfinite(pv(self.delta)):
            raise ValueError("BoundOffsetIR delta must be one finite CAD dimension")


@dataclass(frozen=True)
class FeaturePlacementIR:
    """Engine-neutral placement of one history feature on an existing body.

    Absolute placement retains an authored XYZ point. Anchored placement keeps
    parent/child anchor meaning plus two in-plane offsets. Backends resolve
    body topology/pick coordinates only after semantic normalization.
    """

    mode: str
    point: tuple[Any, Any, Any] | None = None
    parent_anchor: str | None = None
    child_anchor: str | None = None
    offset: tuple[Any, Any] = (0, 0)
    source_kind: str = "feature_placement"

    def __post_init__(self):
        if self.mode not in {"absolute", "anchored"}:
            raise ValueError(
                "FeaturePlacementIR mode must be absolute or anchored"
            )

        if self.mode == "absolute":
            if (
                not isinstance(self.point, tuple)
                or len(self.point) != 3
                or any(
                    isinstance(value, bool) or not isfinite(pv(value))
                    for value in self.point
                )
            ):
                raise ValueError(
                    "absolute FeaturePlacementIR requires three finite CAD dimensions"
                )
            if self.parent_anchor is not None or self.child_anchor is not None:
                raise ValueError(
                    "absolute FeaturePlacementIR cannot carry parent/child anchors"
                )
            if self.offset != (0, 0):
                raise ValueError(
                    "absolute FeaturePlacementIR cannot carry anchored offsets"
                )
            return

        if self.point is not None:
            raise ValueError(
                "anchored FeaturePlacementIR must not contain an absolute point"
            )
        try:
            parent = Anchor(self.parent_anchor)
            child = Anchor(self.child_anchor)
        except (TypeError, ValueError):
            raise ValueError(
                "anchored FeaturePlacementIR requires valid parent/child anchors"
            ) from None
        object.__setattr__(self, "parent_anchor", parent.value)
        object.__setattr__(self, "child_anchor", child.value)

        if not isinstance(self.offset, tuple) or len(self.offset) != 2:
            raise ValueError(
                "anchored FeaturePlacementIR offset must contain X/Y values"
            )
        for index, value in enumerate(self.offset):
            expected_axis = "X" if index == 0 else "Y"
            if isinstance(value, BoundOffsetIR):
                if value.axis != expected_axis:
                    raise ValueError(
                        f"FeaturePlacementIR offset {index} requires {expected_axis} bounds"
                    )
            elif isinstance(value, bool) or not isfinite(pv(value)):
                raise ValueError(
                    "FeaturePlacementIR offsets must be finite CAD dimensions"
                )


@dataclass(frozen=True)
class PlacementIR(BodyIR):
    """Absolute placement of one typed primitive.

    point is the world-space point at which the selected semantic anchor is
    placed. The native backend decides how that placement maps to its own
    primitive plane, centre/corner or base representation.
    """

    primitive: PrimitiveIR
    point: tuple[Any, Any, Any]
    anchor: tuple[int, int, int]
    explicit: bool = False
    source_kind: str = "placement"


@dataclass(frozen=True)
