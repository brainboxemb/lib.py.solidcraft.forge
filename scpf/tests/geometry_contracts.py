"""Shared data for geometry contract tests.

The registries in this module are the maintenance boundary for geometry tests.
When Forge gains a new general body kind, add one BodyCase here. Shared
contracts then exercise every compatible feature automatically.
"""
from dataclasses import dataclass
from typing import Callable

from scpf import Anchor, Box, Cylinder, Hole, Rectangle2D, Sketch, Sphere


@dataclass(frozen=True)
class BodyCase:
    name: str
    kind: str | None
    native_command: str | None
    build: Callable[[], object]
    build_parameterized: Callable[[object], object] | None
    entry_z: float
    through_depth: float
    capabilities: frozenset[str]


@dataclass(frozen=True)
class FeatureCase:
    name: str
    capability: str
    native_command: str
    apply: Callable[[object, BodyCase], object]
    expected_count: int = 1


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


def _box_parameterized(size):
    return Box(size, 40, 20, anchor=Anchor.BOTTOM)


def _cylinder_parameterized(size):
    return Cylinder(d=size, h=20, anchor=Anchor.BOTTOM)


def _sphere_parameterized(size):
    return Sphere(size / 2)


PRIMITIVE_BODY_CASES = (
    BodyCase(
        "box", "box", "solid.box", _box, _box_parameterized, 20, 20,
        frozenset((GENERAL_SOLID, PRIMITIVE, CSG, NATIVE_HOLE, JOINABLE)),
    ),
    BodyCase(
        "cylinder", "cylinder", "solid.cylinder", _cylinder,
        _cylinder_parameterized, 20, 20,
        frozenset((GENERAL_SOLID, PRIMITIVE, CSG, NATIVE_HOLE, JOINABLE)),
    ),
    BodyCase(
        "sphere", "sphere", "solid.sphere", _sphere, _sphere_parameterized,
        20, 40,
        frozenset((GENERAL_SOLID, PRIMITIVE, CSG, NATIVE_HOLE, JOINABLE)),
    ),
)

FEATURE_BODY_CASES = PRIMITIVE_BODY_CASES + (
    BodyCase(
        "sketch-extrusion", None, None, _sketch_extrusion, None, 20, 20,
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


def _apply_native_hole(body, case):
    return body + Hole(
        d=6,
        depth=case.through_depth,
        direction=(0, 0, -1),
    ).at(0, 0, case.entry_z)


FEATURE_CASES = (
    FeatureCase(
        "native-hole",
        NATIVE_HOLE,
        "solid.hole",
        _apply_native_hole,
    ),
)
