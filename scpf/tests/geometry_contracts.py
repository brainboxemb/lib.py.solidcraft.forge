"""Shared body factories for geometry contract tests.

Keep this file data-driven. Public feature tests should iterate these registries
instead of adding one regression test per body type.
"""
from dataclasses import dataclass
from typing import Callable

from scpf import Anchor, Box, Cylinder, Rectangle2D, Sketch, Sphere


@dataclass(frozen=True)
class BodyCase:
    name: str
    kind: str | None
    build: Callable[[], object]
    hole_position: tuple[float, float, float]
    hole_depth: float


def _box():
    return Box(40, 40, 20, anchor=Anchor.BOTTOM)


def _cylinder():
    return Cylinder(d=40, h=20, anchor=Anchor.BOTTOM)


def _sphere():
    return Sphere(20)


def _sketch_extrusion():
    with Sketch(name="Base", plane="XY") as sketch:
        Rectangle2D(40, 40)
    return sketch.extrude(20)


PRIMITIVE_BODY_CASES = (
    BodyCase("box", "box", _box, (0, 0, 20), 20),
    BodyCase("cylinder", "cylinder", _cylinder, (0, 0, 20), 20),
    BodyCase("sphere", "sphere", _sphere, (0, 0, 20), 40),
)

FEATURE_BODY_CASES = PRIMITIVE_BODY_CASES + (
    BodyCase("sketch-extrusion", None, _sketch_extrusion, (0, 0, 20), 20),
)


def joined_body_cases():
    cases = []
    for case in PRIMITIVE_BODY_CASES:
        def build(case=case):
            body = case.build()
            boss = Cylinder(d=16, h=10, anchor=Anchor.BOTTOM).at(
                0, 0, 15, anchor=Anchor.BOTTOM
            )
            return body + boss

        cases.append(
            BodyCase(
                f"{case.name}+cylinder",
                case.kind,
                build,
                case.hole_position,
                case.hole_depth,
            )
        )
    return tuple(cases)


DERIVED_FEATURE_BODY_CASES = joined_body_cases()
ALL_FEATURE_BODY_CASES = FEATURE_BODY_CASES + DERIVED_FEATURE_BODY_CASES
