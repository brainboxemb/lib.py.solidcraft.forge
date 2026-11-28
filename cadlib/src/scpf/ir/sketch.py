"""Sketch frame, relation and entity-graph semantic IR.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from ..core import Anchor, _dim_add, _pv as pv
from .base import BodyIR
from .profiles import (
    CircleProfileIR,
    PolygonProfileIR,
    ProfileIR,
    RectangleProfileIR,
    RoundedRectangleProfileIR,
    SlotProfileIR,
)

@dataclass(frozen=True)
class PlaneIR:
    """Principal-orientation reference plane at a semantic XYZ origin."""

    orientation: str
    origin: tuple[Any, Any, Any] = (0, 0, 0)
    source_kind: str = "plane"

    def __post_init__(self):
        if self.orientation not in {"XY", "XZ", "YZ"}:
            raise ValueError("PlaneIR orientation must be XY, XZ or YZ")
        if (
            not isinstance(self.origin, tuple)
            or len(self.origin) != 3
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.origin
            )
        ):
            raise ValueError(
                "PlaneIR origin must contain three finite CAD dimensions"
            )


@dataclass(frozen=True)
class SketchPointIR:
    """One Sketch-local semantic point with authored symbolic coordinates."""

    position: tuple[Any, Any]

    def __post_init__(self):
        if (
            not isinstance(self.position, tuple)
            or len(self.position) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.position
            )
        ):
            raise ValueError(
                "SketchPointIR position must contain two finite CAD dimensions"
            )


@dataclass(frozen=True)
class SketchLineIR:
    """Straight Sketch entity referencing semantic point tuple positions."""

    start: int
    end: int

    def __post_init__(self):
        if (
            type(self.start) is not int
            or type(self.end) is not int
            or self.start < 0
            or self.end < 0
            or self.start == self.end
        ):
            raise ValueError(
                "SketchLineIR endpoints must be distinct non-negative point indexes"
            )


@dataclass(frozen=True)
class SketchOrientationConstraintIR:
    """Horizontal/vertical semantic relation on one Sketch-local line."""

    line: int
    orientation: str

    def __post_init__(self):
        if type(self.line) is not int or self.line < 0:
            raise ValueError(
                "SketchOrientationConstraintIR line must be a non-negative index"
            )
        if self.orientation not in {"horizontal", "vertical"}:
            raise ValueError(
                "SketchOrientationConstraintIR orientation must be horizontal or vertical"
            )


@dataclass(frozen=True)
class SketchLengthDimensionIR:
    """One symbolic driving length attached to a Sketch-local line."""

    line: int
    value: Any

    def __post_init__(self):
        if type(self.line) is not int or self.line < 0:
            raise ValueError(
                "SketchLengthDimensionIR line must be a non-negative index"
            )
        if isinstance(self.value, bool) or not isfinite(pv(self.value)):
            raise ValueError(
                "SketchLengthDimensionIR value must be one finite CAD dimension"
            )
        if pv(self.value) <= 0:
            raise ValueError(
                "SketchLengthDimensionIR value must be positive"
            )


@dataclass(frozen=True)
class SketchCoordinateDimensionIR:
    """Signed Sketch-local point coordinate relative to the Sketch origin."""

    point: int
    axis: str
    value: Any

    def __post_init__(self):
        if type(self.point) is not int or self.point < 0:
            raise ValueError(
                "SketchCoordinateDimensionIR point must be a non-negative index"
            )
        if self.axis not in {"x", "y"}:
            raise ValueError(
                "SketchCoordinateDimensionIR axis must be x or y"
            )
        if isinstance(self.value, bool) or not isfinite(pv(self.value)):
            raise ValueError(
                "SketchCoordinateDimensionIR value must be one finite CAD dimension"
            )


@dataclass(frozen=True)
class SketchRelationsIR:
    """Explicit Sketch entity/constraint/dimension graph.

    Integer references are positions inside these semantic tuples. They are
    never native ids, replay names or backend command indexes.
    """

    points: tuple[SketchPointIR, ...]
    lines: tuple[SketchLineIR, ...]
    constraints: tuple[SketchOrientationConstraintIR, ...] = ()
    dimensions: tuple[SketchLengthDimensionIR, ...] = ()
    coordinate_dimensions: tuple[SketchCoordinateDimensionIR, ...] = ()

    def __post_init__(self):
        if (
            not isinstance(self.points, tuple)
            or not self.points
            or any(not isinstance(point, SketchPointIR) for point in self.points)
        ):
            raise ValueError("SketchRelationsIR requires semantic points")
        if (
            not isinstance(self.lines, tuple)
            or not self.lines
            or any(not isinstance(line, SketchLineIR) for line in self.lines)
        ):
            raise ValueError("SketchRelationsIR requires semantic lines")
        point_count = len(self.points)
        if any(
            line.start >= point_count or line.end >= point_count
            for line in self.lines
        ):
            raise ValueError(
                "SketchRelationsIR line references a missing semantic point"
            )
        line_count = len(self.lines)
        if any(
            constraint.line >= line_count
            for constraint in self.constraints
        ):
            raise ValueError(
                "SketchRelationsIR constraint references a missing semantic line"
            )
        if any(
            dimension.line >= line_count
            for dimension in self.dimensions
        ):
            raise ValueError(
                "SketchRelationsIR dimension references a missing semantic line"
            )
        if any(
            dimension.point >= point_count
            for dimension in self.coordinate_dimensions
        ):
            raise ValueError(
                "SketchRelationsIR coordinate dimension references a missing semantic point"
            )


@dataclass(frozen=True)
class SketchSupportIR:
    """Semantic support of one Sketch on an existing typed body.

    parent is a public Anchor value when the Sketch is attached to a target
    surface. parent=None means the Sketch uses an explicit world frame while
    still modifying target.
    """

    target: BodyIR
    parent: str | None = None

    def __post_init__(self):
        if not isinstance(self.target, BodyIR):
            raise ValueError("SketchSupportIR target must be BodyIR")
        if self.parent is not None and self.parent not in {
            "top", "bottom", "center", "inner_bottom",
        }:
            raise ValueError("SketchSupportIR parent anchor is unsupported")


@dataclass(frozen=True)
class SketchIR:
    """2D sketch geometry plus backend-neutral support/frame semantics."""

    name: str
    plane: PlaneIR
    profiles: tuple[ProfileIR, ...]
    relations: SketchRelationsIR | None = None
    support: SketchSupportIR | None = None
    rotation: tuple[float, float, float] | None = None
    graph: "SketchEntityGraphIR | None" = None
    source_kind: str = "sketch"

    def __post_init__(self):
        if not isinstance(self.plane, PlaneIR):
            raise ValueError("SketchIR plane must be PlaneIR")
        if self.relations is not None and not isinstance(
            self.relations, SketchRelationsIR
        ):
            raise ValueError("SketchIR relations must be SketchRelationsIR")
        if self.support is not None and not isinstance(
            self.support, SketchSupportIR
        ):
            raise ValueError("SketchIR support must be SketchSupportIR")
        if self.rotation is not None:
            if (
                not isinstance(self.rotation, tuple)
                or len(self.rotation) != 3
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not isfinite(value)
                    for value in self.rotation
                )
            ):
                raise ValueError(
                    "SketchIR rotation must be a fixed finite XYZ degree tuple"
                )
        if self.graph is not None and not isinstance(
            self.graph, SketchEntityGraphIR
        ):
            raise ValueError("SketchIR graph must be SketchEntityGraphIR")

@dataclass(frozen=True)
class SketchChainSegmentIR:
    """One semantic segment in an authored connected Sketch chain."""

    kind: str
    start: tuple[Any, Any]
    end: tuple[Any, Any]
    through: tuple[Any, Any] | None = None
    center: tuple[Any, Any] | None = None
    clockwise: bool | None = None

    def __post_init__(self):
        if self.kind not in {
            "line",
            "arc_tangent",
            "arc_three_point",
            "arc_center_point",
        }:
            raise ValueError("SketchChainSegmentIR kind is unsupported")
        for label, point in (
            ("start", self.start),
            ("end", self.end),
            ("through", self.through),
            ("center", self.center),
        ):
            if point is None:
                continue
            if (
                not isinstance(point, tuple)
                or len(point) != 2
                or any(
                    isinstance(value, bool) or not isfinite(pv(value))
                    for value in point
                )
            ):
                raise ValueError(
                    f"SketchChainSegmentIR {label} must be a finite 2D point"
                )
        if self.kind == "arc_three_point":
            if self.through is None or self.center is not None:
                raise ValueError(
                    "arc_three_point requires through and no center"
                )
        elif self.kind == "arc_center_point":
            if self.center is None or not isinstance(self.clockwise, bool):
                raise ValueError(
                    "arc_center_point requires center and clockwise"
                )
        elif self.through is not None or self.center is not None:
            raise ValueError(
                "line/tangent SketchChainSegmentIR cannot carry arc control points"
            )


@dataclass(frozen=True)
class SketchChainIR:
    """Engine-neutral connected line/arc Sketch chain."""

    name: str
    plane: PlaneIR | None
    segments: tuple[SketchChainSegmentIR, ...]
    closed: bool
    source_kind: str = "sketch_chain"

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("SketchChainIR name must be non-empty")
        if self.plane is not None and not isinstance(self.plane, PlaneIR):
            raise ValueError("SketchChainIR plane must be PlaneIR or None")
        if (
            not isinstance(self.segments, tuple)
            or not self.segments
            or any(
                not isinstance(segment, SketchChainSegmentIR)
                for segment in self.segments
            )
        ):
            raise ValueError("SketchChainIR requires semantic segments")
        if not isinstance(self.closed, bool):
            raise ValueError("SketchChainIR closed must be bool")


@dataclass(frozen=True)
class TextEntityIR:
    """Editable Sketch text independent of support/native ids."""

    text: str
    height: Any
    font: str
    position: tuple[Any, Any] = (0, 0)
    source_kind: str = "text"

    def __post_init__(self):
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("TextEntityIR text must be non-empty")
        if not isinstance(self.font, str) or not self.font.strip():
            raise ValueError("TextEntityIR font must be non-empty")
        if (
            isinstance(self.height, bool)
            or not isfinite(pv(self.height))
            or pv(self.height) <= 0
        ):
            raise ValueError("TextEntityIR height must be positive")
        if (
            not isinstance(self.position, tuple)
            or len(self.position) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.position
            )
        ):
            raise ValueError(
                "TextEntityIR position must contain two finite CAD dimensions"
            )


SketchGraphEntityIR = ProfileIR | SketchChainIR | TextEntityIR


@dataclass(frozen=True)
class SketchEntityRefIR:
    """Sketch-local semantic source reference for pattern/mirror operations."""

    kind: str
    index: int

    def __post_init__(self):
        if self.kind not in {"entity", "operation"}:
            raise ValueError("SketchEntityRefIR kind must be entity or operation")
        if type(self.index) is not int or self.index < 0:
            raise ValueError("SketchEntityRefIR index must be non-negative")


@dataclass(frozen=True)
class SketchRectangularPatternIR:
    """Native Sketch rectangular-pattern meaning over one semantic source."""

    source: SketchEntityRefIR
    count: Any
    spacing: Any
    direction: tuple[float, float]
    count2: Any = 1
    spacing2: Any | None = None
    direction2: tuple[float, float] | None = None
    alignment: str = "right"
    alignment2: str = "right"
    reversed: bool = False
    reversed2: bool = False
    source_kind: str = "sketch_pattern_rectangular"

    def __post_init__(self):
        if not isinstance(self.source, SketchEntityRefIR):
            raise ValueError(
                "SketchRectangularPatternIR source must be SketchEntityRefIR"
            )
        for value, label in ((self.count, "count"), (self.count2, "count2")):
            concrete = pv(value)
            if (
                isinstance(value, bool)
                or not isfinite(concrete)
                or not 1 <= concrete <= 500
                or not float(concrete).is_integer()
            ):
                raise ValueError(
                    f"SketchRectangularPatternIR {label} must be 1..500"
                )
        if pv(self.count) * pv(self.count2) > 500:
            raise ValueError(
                "SketchRectangularPatternIR supports at most 500 instances"
            )
        for value, label in (
            (self.spacing, "spacing"),
            (self.spacing2, "spacing2"),
        ):
            if value is not None and (
                isinstance(value, bool) or not isfinite(pv(value))
            ):
                raise ValueError(
                    f"SketchRectangularPatternIR {label} must be finite"
                )
        for vector, label, optional in (
            (self.direction, "direction", False),
            (self.direction2, "direction2", True),
        ):
            if vector is None and optional:
                continue
            if (
                not isinstance(vector, tuple)
                or len(vector) != 2
                or any(
                    isinstance(component, bool)
                    or not isinstance(component, (int, float))
                    or not isfinite(component)
                    for component in vector
                )
                or sum(component * component for component in vector) <= 0
            ):
                raise ValueError(
                    f"SketchRectangularPatternIR {label} must be a fixed non-zero 2D vector"
                )
        if self.alignment not in {"left", "center", "right"}:
            raise ValueError("SketchRectangularPatternIR alignment is invalid")
        if self.alignment2 not in {"left", "center", "right"}:
            raise ValueError("SketchRectangularPatternIR alignment2 is invalid")
        if not isinstance(self.reversed, bool) or not isinstance(
            self.reversed2, bool
        ):
            raise ValueError(
                "SketchRectangularPatternIR reversed flags must be bool"
            )


@dataclass(frozen=True)
class SketchMirrorIR:
    """Mirror one semantic Sketch source over a local origin axis."""

    source: SketchEntityRefIR
    axis: str
    source_kind: str = "sketch_mirror"

    def __post_init__(self):
        if not isinstance(self.source, SketchEntityRefIR):
            raise ValueError("SketchMirrorIR source must be SketchEntityRefIR")
        if self.axis not in {"x", "y"}:
            raise ValueError("SketchMirrorIR axis must be x or y")


SketchOperationIR = SketchRectangularPatternIR | SketchMirrorIR


@dataclass(frozen=True)
class SketchEntityGraphIR:
    """Support-independent semantic contents authored inside one Sketch."""

    entities: tuple[SketchGraphEntityIR, ...]
    open_chains: tuple[SketchChainIR, ...] = ()
    operations: tuple[SketchOperationIR, ...] = ()
    source_kind: str = "sketch_entity_graph"

    def __post_init__(self):
        if (
            not isinstance(self.entities, tuple)
            or any(
                not isinstance(
                    entity,
                    (
                        CircleProfileIR,
                        RectangleProfileIR,
                        RoundedRectangleProfileIR,
                        SlotProfileIR,
                        PolygonProfileIR,
                        SketchChainIR,
                        TextEntityIR,
                    ),
                )
                for entity in self.entities
            )
        ):
            raise ValueError(
                "SketchEntityGraphIR entities contain unsupported semantic nodes"
            )
        if any(
            isinstance(entity, SketchChainIR) and not entity.closed
            for entity in self.entities
        ):
            raise ValueError(
                "SketchEntityGraphIR entities require closed SketchChainIR"
            )
        if (
            not isinstance(self.open_chains, tuple)
            or any(
                not isinstance(chain, SketchChainIR) or chain.closed
                for chain in self.open_chains
            )
        ):
            raise ValueError(
                "SketchEntityGraphIR open_chains require open SketchChainIR"
            )
        if (
            not isinstance(self.operations, tuple)
            or any(
                not isinstance(
                    operation,
                    (SketchRectangularPatternIR, SketchMirrorIR),
                )
                for operation in self.operations
            )
        ):
            raise ValueError(
                "SketchEntityGraphIR operations contain unsupported nodes"
            )
        for index, operation in enumerate(self.operations):
            source = operation.source
            if source.kind == "entity":
                if source.index >= len(self.entities):
                    raise ValueError(
                        "Sketch operation references missing semantic entity"
                    )
            elif source.index >= index:
                raise ValueError(
                    "Sketch operation must reference an earlier operation"
                )
