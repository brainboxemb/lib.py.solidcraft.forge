"""Body-operation, topology and modifier semantic IR.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from ..core import _pv as pv
from .base import BodyIR, PlacementIR
from .sketch import RegionIR, SketchIR

@dataclass(frozen=True)
class ExtrudeIR(BodyIR):
    """One authored extrusion over semantic Sketch region selection."""

    sketch: SketchIR
    regions: tuple[RegionIR, ...]
    distance: Any | None
    direction: str
    operation: str = "new_body"
    target: BodyIR | None = None
    through_all: bool = False
    source_kind: str = "sketch_base_extrusion"

    def __post_init__(self):
        if not isinstance(self.sketch, SketchIR):
            raise ValueError("ExtrudeIR sketch must be SketchIR")
        if (
            not isinstance(self.regions, tuple)
            or any(not isinstance(region, RegionIR) for region in self.regions)
        ):
            raise ValueError("ExtrudeIR regions must contain RegionIR")
        if self.direction not in {"positive", "negative", "symmetric"}:
            raise ValueError("ExtrudeIR direction is unsupported")
        if self.operation not in {"new_body", "join", "cut"}:
            raise ValueError("ExtrudeIR operation is unsupported")
        if self.operation == "new_body":
            if self.target is not None or self.sketch.support is not None:
                raise ValueError(
                    "new-body ExtrudeIR cannot carry target/support body"
                )
        else:
            if not isinstance(self.target, BodyIR):
                raise ValueError(
                    "join/cut ExtrudeIR requires typed target BodyIR"
                )
            if (
                self.sketch.support is None
                or self.sketch.support.target is not self.target
            ):
                raise ValueError(
                    "attached ExtrudeIR support must reference its semantic target"
                )
        if self.through_all:
            if self.operation != "cut":
                raise ValueError("through-all ExtrudeIR requires cut operation")
            if self.distance is not None:
                raise ValueError(
                    "through-all ExtrudeIR must not carry finite distance"
                )
            if self.direction == "symmetric":
                raise ValueError(
                    "through-all ExtrudeIR cannot be symmetric"
                )
        elif (
            self.distance is None
            or isinstance(self.distance, bool)
            or not isfinite(pv(self.distance))
            or pv(self.distance) <= 0
        ):
            raise ValueError(
                "finite ExtrudeIR requires positive CAD distance"
            )


@dataclass(frozen=True)
class AxisLineIR:
    """Engine-neutral fixed-direction axis through a semantic XYZ point."""

    direction: "str | tuple[float, float, float]"
    origin: tuple[Any, Any, Any] = (0, 0, 0)
    source_kind: str = "axis_line"

    def __post_init__(self):
        direction = self.direction
        if isinstance(direction, str):
            if direction not in {"X", "Y", "Z"}:
                raise ValueError(
                    "AxisLineIR string direction must be X, Y or Z"
                )
        elif (
            not isinstance(direction, tuple)
            or len(direction) != 3
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                for value in direction
            )
            or all(value == 0 for value in direction)
        ):
            raise ValueError(
                "AxisLineIR vector direction must be one fixed finite non-zero XYZ tuple"
            )
        else:
            object.__setattr__(
                self,
                "direction",
                tuple(float(value) for value in direction),
            )
        if (
            not isinstance(self.origin, tuple)
            or len(self.origin) != 3
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.origin
            )
        ):
            raise ValueError(
                "AxisLineIR origin must contain three finite CAD dimensions"
            )


@dataclass(frozen=True)
class RevolveIR(BodyIR):
    """Angular sweep of one completed semantic Sketch result."""

    sketch: SketchIR
    region: RegionIR | None
    axis: AxisLineIR
    angle: Any
    direction: str | None = None
    operation: str = "new_body"
    target: PlacementIR | None = None
    source_kind: str = "sketch_base_revolve"

    def __post_init__(self):
        if not isinstance(self.sketch, SketchIR):
            raise ValueError("RevolveIR sketch must be SketchIR")
        if self.region is not None and not isinstance(self.region, RegionIR):
            raise ValueError("RevolveIR region must be RegionIR or None")
        if not isinstance(self.axis, AxisLineIR):
            raise ValueError("RevolveIR axis must be AxisLineIR")
        if self.direction not in (None, "symmetric"):
            raise ValueError("RevolveIR direction must be None or symmetric")
        if (
            isinstance(self.angle, bool)
            or not isfinite(pv(self.angle))
            or pv(self.angle) <= 0
            or pv(self.angle) > 360
        ):
            raise ValueError(
                "RevolveIR angle must be finite, above 0 and at most 360"
            )
        if self.operation not in {"new_body", "cut"}:
            raise ValueError("RevolveIR operation must be new_body or cut")
        if self.operation == "new_body" and self.target is not None:
            raise ValueError("new-body RevolveIR must not have a target")
        if self.operation == "cut" and not isinstance(self.target, PlacementIR):
            raise ValueError("cut RevolveIR requires one typed target placement")


@dataclass(frozen=True)
class FaceSetIR:
    """Semantic set of cardinal planar faces themselves."""

    faces: tuple[str, ...]

    def __post_init__(self):
        if (
            not isinstance(self.faces, tuple)
            or not self.faces
            or any(
                face not in {"top", "bottom", "left", "right", "front", "back"}
                for face in self.faces
            )
        ):
            raise ValueError(
                "FaceSetIR requires one or more cardinal face names"
            )


@dataclass(frozen=True)
class FaceBoundaryIR:
    """Semantic request for all boundary edges of cardinal planar faces."""

    faces: tuple[str, ...]

    def __post_init__(self):
        if (
            not isinstance(self.faces, tuple)
            or not self.faces
            or any(
                face not in {"top", "bottom", "left", "right", "front", "back"}
                for face in self.faces
            )
        ):
            raise ValueError(
                "FaceBoundaryIR requires one or more cardinal face names"
            )


@dataclass(frozen=True)
class ParallelEdgeSetIR:
    """Semantic request for straight edges parallel to one principal axis."""

    axis: str

    def __post_init__(self):
        if self.axis not in {"X", "Y", "Z"}:
            raise ValueError("ParallelEdgeSetIR axis must be X, Y or Z")


@dataclass(frozen=True)
class DirectionPairEdgeSetIR:
    """One or more rectangular-solid edges selected by two cardinal directions."""

    vectors: tuple[tuple[int, int, int], ...]

    def __post_init__(self):
        if (
            not isinstance(self.vectors, tuple)
            or not self.vectors
            or any(
                not isinstance(vector, tuple)
                or len(vector) != 3
                or any(component not in {-1, 0, 1} for component in vector)
                or sum(component != 0 for component in vector) != 2
                for vector in self.vectors
            )
        ):
            raise ValueError(
                "DirectionPairEdgeSetIR requires rank-two cardinal direction vectors"
            )


@dataclass(frozen=True)
class ProfileEdgeSetIR:
    """Named polygon-profile segment or vertex edge intent."""

    patterns: tuple[str, ...]
    kind: str
    sides: str

    def __post_init__(self):
        if (
            not isinstance(self.patterns, tuple)
            or not self.patterns
            or any(not isinstance(pattern, str) or not pattern for pattern in self.patterns)
        ):
            raise ValueError("ProfileEdgeSetIR requires non-empty name patterns")
        if self.kind not in {"segments", "vertices"}:
            raise ValueError("ProfileEdgeSetIR kind must be segments or vertices")
        expected_sides = "both" if self.kind == "segments" else "axis"
        if self.sides != expected_sides:
            raise ValueError(
                f"ProfileEdgeSetIR {self.kind} requires sides={expected_sides!r}"
            )


@dataclass(frozen=True)
class ExplicitEdgePicksIR:
    """Authored fixed XYZ points used to select native edges."""

    points: tuple[tuple[Any, Any, Any], ...]

    def __post_init__(self):
        if (
            not isinstance(self.points, tuple)
            or not self.points
            or any(
                not isinstance(point, tuple)
                or len(point) != 3
                or any(
                    isinstance(value, bool) or not isfinite(pv(value))
                    for value in point
                )
                for point in self.points
            )
        ):
            raise ValueError(
                "ExplicitEdgePicksIR requires one or more finite XYZ points"
            )


EdgeSelectionIR = (
    FaceBoundaryIR
    | ParallelEdgeSetIR
    | DirectionPairEdgeSetIR
    | ProfileEdgeSetIR
    | ExplicitEdgePicksIR
)


@dataclass(frozen=True)
class FilletIR(BodyIR):
    """Constant-radius fillet over one typed body and semantic edge selection."""

    base: BodyIR
    radius: Any
    edges: EdgeSelectionIR
    source_kind: str = "fillet"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("FilletIR base must be BodyIR")
        if not isinstance(
            self.edges,
            (
                FaceBoundaryIR,
                ParallelEdgeSetIR,
                DirectionPairEdgeSetIR,
                ProfileEdgeSetIR,
                ExplicitEdgePicksIR,
            ),
        ):
            raise ValueError("FilletIR edges must be semantic EdgeSelectionIR")
        if (
            isinstance(self.radius, bool)
            or not isfinite(pv(self.radius))
            or pv(self.radius) <= 0
        ):
            raise ValueError("FilletIR radius must be one positive CAD dimension")


@dataclass(frozen=True)
class ChamferIR(BodyIR):
    """One semantic chamfer over a typed body and semantic edge selection."""

    base: BodyIR
    distance: Any
    edges: EdgeSelectionIR
    distance2: Any | None = None
    flip: bool = False
    source_kind: str = "chamfer"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("ChamferIR base must be BodyIR")
        if not isinstance(
            self.edges,
            (
                FaceBoundaryIR,
                ParallelEdgeSetIR,
                DirectionPairEdgeSetIR,
                ProfileEdgeSetIR,
                ExplicitEdgePicksIR,
            ),
        ):
            raise ValueError("ChamferIR edges must be semantic EdgeSelectionIR")
        if not isinstance(self.flip, bool):
            raise ValueError("ChamferIR flip must be bool")
        if self.flip and self.distance2 is None:
            raise ValueError("ChamferIR flip requires distance2")
