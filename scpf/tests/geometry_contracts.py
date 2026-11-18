"""Shared data for geometry contract tests.

The registries in this module are the maintenance boundary for geometry tests.
When Forge gains a new general body kind, add one BodyCase here. Shared
contracts then exercise every compatible feature automatically.
"""
from dataclasses import dataclass
from typing import Callable

from scpf import Anchor, Box, Cylinder, Rectangle2D, Sketch, Sphere


@dataclass(frozen=True)
class BodyCase:
    name: str
    kind: str | None
    build: Callable[[], object]
    entry_z: float
    through_depth: float
    capabilities: frozenset[str]


GENERAL_SOLID = "general-solid"
PRIMITIVE = "primitive"
CSG = "csg"
NATIVE_HOLE = "native-hole"
JOINABLE = "joinable"


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
    BodyCase(
        "box", "box", _box, 20, 20,
        frozenset((GENERAL_SOLID, PRIMITIVE, CSG, NATIVE_HOLE, JOINABLE)),
    ),
    BodyCase(
        "cylinder", "cylinder", _cylinder, 20, 20,
        frozenset((GENERAL_SOLID, PRIMITIVE, CSG, NATIVE_HOLE, JOINABLE)),
    ),
    BodyCase(
        "sphere", "sphere", _sphere, 20, 40,
        frozenset((GENERAL_SOLID, PRIMITIVE, CSG, NATIVE_HOLE, JOINABLE)),
    ),
)

FEATURE_BODY_CASES = PRIMITIVE_BODY_CASES + (
    BodyCase(
        "sketch-extrusion", None, _sketch_extrusion, 20, 20,
        frozenset((GENERAL_SOLID, NATIVE_HOLE, JOINABLE)),
    ),
)


def cases_with(capability):
    return tuple(
        case for case in FEATURE_BODY_CASES
        if capability in case.capabilities
    )


def build_joined(case):
    body = case.build()
    boss = Cylinder(d=16, h=10, anchor=Anchor.BOTTOM).at(
        0, 0, 15, anchor=Anchor.BOTTOM
    )
    return body + boss
