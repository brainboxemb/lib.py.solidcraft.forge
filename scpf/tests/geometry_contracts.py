"""Shared data for geometry contract tests.

The registries in this module are the maintenance boundary for geometry tests.
When Forge gains a new general body kind, add one BodyCase here. Shared
contracts then exercise every compatible feature automatically.
"""
from dataclasses import dataclass
from typing import Callable

from scpf import (
    Anchor,
    Box,
    CounterboreHole,
    CountersinkHole,
    Cylinder,
    Hole,
    Rectangle2D,
    Sketch,
    Sphere,
    ThreadedHole,
)


@dataclass(frozen=True)
class BodyCase:
    name: str
    kind: str | None
    native_command: str | None
    build: Callable[[], object]
    build_parameterized: Callable[[object], object] | None
    bottom_at_expected: tuple[str, tuple[float, float, float]] | None
    entry_z: float
    through_depth: float
    capabilities: frozenset[str]


@dataclass(frozen=True)
class OperationCase:
    name: str
    native_operation: str
    apply: Callable[[object, object], object]


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
DERIVED = "derived"


CSG_OPERATION_CASES = (
    OperationCase("join", "join", lambda left, right: left + right),
    OperationCase("cut", "cut", lambda left, right: left - right),
    OperationCase(
        "intersection",
        "intersect",
        lambda left, right: left & right,
    ),
)


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
        "box", "box", "solid.box", _box, _box_parameterized,
        ("corner", (-15, -14, 7)), 20, 20,
        frozenset((GENERAL_SOLID, PRIMITIVE, CSG, NATIVE_HOLE, JOINABLE)),
    ),
    BodyCase(
        "cylinder", "cylinder", "solid.cylinder", _cylinder,
        _cylinder_parameterized, ("base", (5, 6, 7)), 20, 20,
        frozenset((GENERAL_SOLID, PRIMITIVE, CSG, NATIVE_HOLE, JOINABLE)),
    ),
    BodyCase(
        "sphere", "sphere", "solid.sphere", _sphere, _sphere_parameterized,
        ("center", (5, 6, 27)), 20, 40,
        frozenset((GENERAL_SOLID, PRIMITIVE, CSG, NATIVE_HOLE, JOINABLE)),
    ),
)

DIRECT_FEATURE_BODY_CASES = PRIMITIVE_BODY_CASES + (
    BodyCase(
        "sketch-extrusion", None, None, _sketch_extrusion, None, None, 20, 20,
        frozenset((GENERAL_SOLID, NATIVE_HOLE, JOINABLE)),
    ),
)


def _derived_primitive_cases():
    cases = []
    for base in PRIMITIVE_BODY_CASES:
        for operation in CSG_OPERATION_CASES:
            def build(base=base, operation=operation):
                modifier = Cylinder(
                    d=16,
                    h=30,
                    anchor=Anchor.BOTTOM,
                ).at(0, 0, -5, anchor=Anchor.BOTTOM)
                return operation.apply(base.build(), modifier)

            cases.append(
                BodyCase(
                    f"{base.name}-{operation.name}",
                    None,
                    None,
                    build,
                    None,
                    None,
                    base.entry_z,
                    base.through_depth,
                    (base.capabilities - frozenset((PRIMITIVE, CSG)))
                    | frozenset((DERIVED,)),
                )
            )
    return tuple(cases)


DERIVED_FEATURE_BODY_CASES = _derived_primitive_cases()
FEATURE_BODY_CASES = DIRECT_FEATURE_BODY_CASES + DERIVED_FEATURE_BODY_CASES


def cases_with(capability):
    return tuple(
        case for case in FEATURE_BODY_CASES
        if capability in case.capabilities
    )


def _place_hole(body, case, feature):
    return body + feature.at(0, 0, case.entry_z)


def _apply_native_hole(body, case):
    return _place_hole(
        body,
        case,
        Hole(
            d=6,
            depth=case.through_depth,
            direction=(0, 0, -1),
        ),
    )


def _apply_counterbore_hole(body, case):
    return _place_hole(
        body,
        case,
        CounterboreHole(
            d=6,
            counterbore_d=10,
            counterbore_depth=3,
            depth=case.through_depth,
            direction=(0, 0, -1),
        ),
    )


def _apply_countersink_hole(body, case):
    return _place_hole(
        body,
        case,
        CountersinkHole(
            d=6,
            countersink_d=10,
            countersink_angle=90,
            depth=case.through_depth,
            direction=(0, 0, -1),
        ),
    )


def _apply_threaded_hole(body, case):
    return _place_hole(
        body,
        case,
        ThreadedHole(
            thread="M6",
            d=5,
            depth=case.through_depth,
            direction=(0, 0, -1),
        ),
    )


FEATURE_CASES = (
    FeatureCase(
        "hole",
        NATIVE_HOLE,
        "solid.hole",
        _apply_native_hole,
    ),
    FeatureCase(
        "counterbore-hole",
        NATIVE_HOLE,
        "solid.hole",
        _apply_counterbore_hole,
    ),
    FeatureCase(
        "countersink-hole",
        NATIVE_HOLE,
        "solid.hole",
        _apply_countersink_hole,
    ),
    FeatureCase(
        "threaded-hole",
        NATIVE_HOLE,
        "solid.hole",
        _apply_threaded_hole,
    ),
)

