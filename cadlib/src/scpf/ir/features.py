"""Hole, plastic-feature and pattern semantic IR.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from ..core import Parameter, _pv as pv
from .base import BodyIR, FeaturePlacementIR
from .configuration import FeatureRefIR
from .operations import AxisLineIR

class HoleIR(BodyIR):
    """One semantic Hole-family history feature over generic feature placement."""

    target: BodyIR
    placement: FeaturePlacementIR
    hole_type: str
    diameter: Any | None = None
    depth_mode: str = "through_all"
    depth: Any | None = None
    direction: tuple[float, float, float] | None = None
    counterbore_diameter: Any | None = None
    counterbore_depth: Any | None = None
    countersink_diameter: Any | None = None
    countersink_angle: Any | None = None
    thread: str | None = None
    hand: str = "right"
    thread_depth: Any | None = None
    modeled: bool = False
    ease_out: Any | None = None
    source_kind: str = "hole"

    def __post_init__(self):
        if not isinstance(self.target, BodyIR):
            raise ValueError("HoleIR target must be one typed BodyIR result")
        if not isinstance(self.placement, FeaturePlacementIR):
            raise ValueError("HoleIR placement must be FeaturePlacementIR")

        if self.hole_type not in {
            "simple",
            "counterbore",
            "countersink",
            "threaded",
        }:
            raise ValueError("HoleIR has unsupported hole_type")

        if self.direction is not None:
            if (
                not isinstance(self.direction, tuple)
                or len(self.direction) != 3
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not isfinite(value)
                    for value in self.direction
                )
                or all(value == 0 for value in self.direction)
            ):
                raise ValueError(
                    "HoleIR direction must be a fixed finite non-zero XYZ vector"
                )

        if self.depth_mode not in {"through_all", "distance"}:
            raise ValueError("HoleIR depth_mode must be through_all or distance")
        if self.depth_mode == "through_all":
            if self.depth is not None:
                raise ValueError("HoleIR through_all depth must not carry distance")
        elif (
            self.depth is None
            or isinstance(self.depth, bool)
            or not isfinite(pv(self.depth))
            or pv(self.depth) <= 0
        ):
            raise ValueError("HoleIR distance depth must be positive")

        def positive(value, label, *, optional=False):
            if value is None and optional:
                return
            if (
                value is None
                or isinstance(value, bool)
                or not isfinite(pv(value))
                or pv(value) <= 0
            ):
                raise ValueError(f"HoleIR {label} must be positive")

        if self.hole_type in {"simple", "counterbore", "countersink"}:
            positive(self.diameter, "diameter")
        else:
            positive(self.diameter, "diameter", optional=True)

        if self.hole_type == "counterbore":
            positive(self.counterbore_diameter, "counterbore diameter")
            positive(self.counterbore_depth, "counterbore depth")
            if pv(self.counterbore_diameter) <= pv(self.diameter):
                raise ValueError(
                    "HoleIR counterbore diameter must exceed hole diameter"
                )
        elif (
            self.counterbore_diameter is not None
            or self.counterbore_depth is not None
        ):
            raise ValueError("HoleIR counterbore fields require counterbore type")

        if self.hole_type == "countersink":
            positive(self.countersink_diameter, "countersink diameter")
            if pv(self.countersink_diameter) <= pv(self.diameter):
                raise ValueError(
                    "HoleIR countersink diameter must exceed hole diameter"
                )
            if (
                self.countersink_angle is None
                or isinstance(self.countersink_angle, bool)
                or not isfinite(pv(self.countersink_angle))
                or not 0 < pv(self.countersink_angle) < 180
            ):
                raise ValueError(
                    "HoleIR countersink angle must be fixed between 0 and 180 degrees"
                )
        elif (
            self.countersink_diameter is not None
            or self.countersink_angle is not None
        ):
            raise ValueError("HoleIR countersink fields require countersink type")

        if self.hole_type == "threaded":
            if not isinstance(self.thread, str) or not self.thread.strip():
                raise ValueError("HoleIR threaded type requires thread designation")
            if self.hand not in {"right", "left"}:
                raise ValueError("HoleIR hand must be right or left")
            positive(self.thread_depth, "thread depth", optional=True)
            if not isinstance(self.modeled, bool):
                raise ValueError("HoleIR modeled must be bool")
            if self.ease_out is not None:
                if isinstance(self.ease_out, str):
                    if self.ease_out not in {"standard", "short"}:
                        raise ValueError(
                            "HoleIR ease_out must be standard, short or positive length"
                        )
                else:
                    positive(self.ease_out, "ease_out")
        else:
            if self.thread is not None:
                raise ValueError("HoleIR thread requires threaded type")
            if self.hand != "right":
                raise ValueError("HoleIR non-threaded hole cannot change hand")
            if self.thread_depth is not None or self.modeled or self.ease_out is not None:
                raise ValueError(
                    "HoleIR thread metadata requires threaded type"
                )

    @property
    def point(self):
        """Compatibility view for absolute Hole placement."""
        return self.placement.point


def _positive_feature_dimension(value, label: str, *, optional=False):
    if value is None and optional:
        return
    if (
        value is None
        or isinstance(value, bool)
        or not isfinite(pv(value))
        or pv(value) <= 0
    ):
        raise ValueError(f"{label} must be a positive CAD dimension")


def _fixed_feature_vector(value, label: str, *, optional=False):
    if value is None and optional:
        return
    if (
        not isinstance(value, tuple)
        or len(value) != 3
        or any(
            isinstance(component, bool)
            or not isinstance(component, (int, float))
            or not isfinite(component)
            for component in value
        )
        or all(component == 0 for component in value)
    ):
        raise ValueError(f"{label} must be a fixed finite non-zero XYZ vector")


@dataclass(frozen=True)
class LipFeatureIR:
    width: Any
    height: Any
    source_kind: str = "lip"

    def __post_init__(self):
        _positive_feature_dimension(self.width, "LipFeatureIR width")
        _positive_feature_dimension(self.height, "LipFeatureIR height")


@dataclass(frozen=True)
class SnapFitFeatureIR:
    length: Any
    thickness: Any
    width: Any
    catch_depth: Any
    catch_length: Any
    hook: tuple[float, float, float]
    direction: tuple[float, float, float] | None = None
    source_kind: str = "snap_fit"

    def __post_init__(self):
        for value, label in (
            (self.length, "length"),
            (self.thickness, "thickness"),
            (self.width, "width"),
            (self.catch_depth, "catch depth"),
            (self.catch_length, "catch length"),
        ):
            _positive_feature_dimension(value, f"SnapFitFeatureIR {label}")
        _fixed_feature_vector(self.hook, "SnapFitFeatureIR hook")
        _fixed_feature_vector(
            self.direction,
            "SnapFitFeatureIR direction",
            optional=True,
        )


@dataclass(frozen=True)
class BossFeatureIR:
    diameter: Any
    height: Any
    hole_diameter: Any | None = None
    direction: tuple[float, float, float] | None = None
    source_kind: str = "boss"

    def __post_init__(self):
        _positive_feature_dimension(self.diameter, "BossFeatureIR diameter")
        _positive_feature_dimension(self.height, "BossFeatureIR height")
        _positive_feature_dimension(
            self.hole_diameter,
            "BossFeatureIR hole diameter",
            optional=True,
        )
        _fixed_feature_vector(
            self.direction,
            "BossFeatureIR direction",
            optional=True,
        )


@dataclass(frozen=True)
class RestFeatureIR:
    width: Any
    height: Any
    length: Any | None = None
    along: tuple[float, float, float] | None = None
    direction: tuple[float, float, float] | None = None
    source_kind: str = "rest"

    def __post_init__(self):
        _positive_feature_dimension(self.width, "RestFeatureIR width")
        _positive_feature_dimension(self.height, "RestFeatureIR height")
        _positive_feature_dimension(
            self.length,
            "RestFeatureIR length",
            optional=True,
        )
        _fixed_feature_vector(
            self.along,
            "RestFeatureIR along",
            optional=True,
        )
        _fixed_feature_vector(
            self.direction,
            "RestFeatureIR direction",
            optional=True,
        )


PlasticFeatureSpecIR = (
    LipFeatureIR
    | SnapFitFeatureIR
    | BossFeatureIR
    | RestFeatureIR
)


@dataclass(frozen=True)
class PlasticFeatureIR(BodyIR):
    """One native plastic/mechanical history feature on typed body history."""

    target: BodyIR
    placement: FeaturePlacementIR
    feature: PlasticFeatureSpecIR
    source_kind: str = "plastic_feature"

    def __post_init__(self):
        if not isinstance(self.target, BodyIR):
            raise ValueError(
                "PlasticFeatureIR target must be one typed BodyIR result"
            )
        if not isinstance(self.placement, FeaturePlacementIR):
            raise ValueError(
                "PlasticFeatureIR placement must be FeaturePlacementIR"
            )
        if not isinstance(
            self.feature,
            (LipFeatureIR, SnapFitFeatureIR, BossFeatureIR, RestFeatureIR),
        ):
            raise ValueError(
                "PlasticFeatureIR feature must be one typed plastic feature spec"
            )


def _positive_pattern_count(value, label: str):
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer or Parameter")
    number = pv(value)
    if not isfinite(number) or number < 1 or not float(number).is_integer():
        raise ValueError(f"{label} must evaluate to a positive integer")


@dataclass(frozen=True)
class RectangularPatternIR(BodyIR):
    """Native-history rectangular repetition of semantic authored features."""

    base: BodyIR
    sources: tuple["FeatureRefIR", ...]
    direction1: tuple[float, float, float]
    count1: Any
    spacing1: Any
    direction2: tuple[float, float, float] | None = None
    count2: Any | None = None
    spacing2: Any | None = None
    alignment1: str = "right"
    alignment2: str = "right"
    reversed1: bool = False
    reversed2: bool = False
    source_kind: str = "rectangular_pattern"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("RectangularPatternIR base must be BodyIR")
        if (
            not isinstance(self.sources, tuple)
            or not self.sources
            or any(not isinstance(ref, FeatureRefIR) for ref in self.sources)
        ):
            raise ValueError(
                "RectangularPatternIR requires semantic FeatureRefIR sources"
            )
        for name, direction in (
            ("direction1", self.direction1),
            ("direction2", self.direction2),
        ):
            if direction is None:
                continue
            if (
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
                    f"RectangularPatternIR {name} must be fixed non-zero XYZ"
                )
        _positive_pattern_count(self.count1, "rectangular count1")
        if (
            isinstance(self.spacing1, bool)
            or not isfinite(pv(self.spacing1))
            or pv(self.spacing1) <= 0
        ):
            raise ValueError("RectangularPatternIR spacing1 must be positive")
        second = self.direction2 is not None
        if second != (self.count2 is not None and self.spacing2 is not None):
            raise ValueError(
                "RectangularPatternIR second direction requires direction/count/spacing"
            )
        if second:
            _positive_pattern_count(self.count2, "rectangular count2")
            if (
                isinstance(self.spacing2, bool)
                or not isfinite(pv(self.spacing2))
                or pv(self.spacing2) <= 0
            ):
                raise ValueError("RectangularPatternIR spacing2 must be positive")
        if self.alignment1 not in {"left", "center", "right"}:
            raise ValueError("RectangularPatternIR alignment1 is invalid")
        if self.alignment2 not in {"left", "center", "right"}:
            raise ValueError("RectangularPatternIR alignment2 is invalid")
        if not isinstance(self.reversed1, bool) or not isinstance(
            self.reversed2, bool
        ):
            raise ValueError("RectangularPatternIR reversed flags must be bool")


@dataclass(frozen=True)
class CircularPatternIR(BodyIR):
    """Native-history circular repetition around one semantic axis line."""

    base: BodyIR
    sources: tuple["FeatureRefIR", ...]
    axis: AxisLineIR
    count: Any
    angle: Any | None = None
    alignment: str = "right"
    reversed: bool = False
    source_kind: str = "circular_pattern"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("CircularPatternIR base must be BodyIR")
        if (
            not isinstance(self.sources, tuple)
            or not self.sources
            or any(not isinstance(ref, FeatureRefIR) for ref in self.sources)
        ):
            raise ValueError(
                "CircularPatternIR requires semantic FeatureRefIR sources"
            )
        if not isinstance(self.axis, AxisLineIR):
            raise ValueError("CircularPatternIR axis must be AxisLineIR")
        _positive_pattern_count(self.count, "circular count")
        if self.angle is not None:
            angle = pv(self.angle)
            if not isfinite(angle) or not 0 < angle <= 360:
                raise ValueError(
                    "CircularPatternIR angle must be above 0 and at most 360"
                )
        if self.alignment not in {"left", "center", "right"}:
            raise ValueError("CircularPatternIR alignment is invalid")
        if not isinstance(self.reversed, bool):
            raise ValueError("CircularPatternIR reversed must be bool")


@dataclass(frozen=True)
