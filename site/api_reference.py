"""Generated API reference definitions for the public Forge website.

Exact enum members and Python signatures come from the public implementation.
This module only supplies human-readable grouping/navigation. Public semantics
remain normative in docs/05-cad-api-design.md.
"""

import inspect

from scpf import (
    Anchor,
    Axis,
    Depth,
    Direction,
    Edges,
    Faces,
    Shape,
    Sketch,
)


def _signature(obj, name):
    return f"{name}{inspect.signature(obj)}"


ENUM_REFERENCES = (
    {
        "slug": "Faces",
        "title": "Faces",
        "object": Faces,
        "summary": "Named planar face selectors used by within-component feature operations.",
        "notes": (
            "Shape.on() currently accepts Faces.TOP and Faces.BOTTOM. "
            "The enum itself defines all six cardinal planar faces.",
        ),
    },
    {
        "slug": "Anchor",
        "title": "Anchor",
        "object": Anchor,
        "summary": "Component alignment and assembly attachment references.",
        "notes": (
            "TOP/BOTTOM/LEFT/RIGHT/FRONT/BACK are cardinal references. "
            "Corner anchors and INNER_BOTTOM are also part of the public enum.",
        ),
    },
    {
        "slug": "Axis",
        "title": "Axis",
        "object": Axis,
        "summary": "Principal X, Y and Z axes used by supported primitives and patterns.",
        "notes": (),
    },
    {
        "slug": "Direction",
        "title": "Direction",
        "object": Direction,
        "summary": "Extrusion direction relative to a sketch plane normal.",
        "notes": (),
    },
    {
        "slug": "Depth",
        "title": "Depth",
        "object": Depth,
        "summary": "Depth policies for supported features such as Hole.",
        "notes": (),
    },
    {
        "slug": "Edges",
        "title": "Edges",
        "object": Edges,
        "summary": "Named and profile-derived edge selectors for fillet/chamfer operations.",
        "notes": (
            "Edges.from_profile(...) and Edges.from_vertices(...) are public helper constructors "
            "in addition to enum members.",
        ),
    },
)


METHOD_REFERENCES = (
    {
        "slug": "Shape.at",
        "title": "Shape.at()",
        "signature": _signature(Shape.at, "Shape.at"),
        "summary": "Absolute placement or supported shape-to-shape alignment.",
        "contract": "at() is geometric placement/alignment; it does not select a support face.",
    },
    {
        "slug": "Shape.on",
        "title": "Shape.on()",
        "signature": _signature(Shape.on, "Shape.on"),
        "summary": "Place a supported within-component feature on a selected target face.",
        "contract": "on() uses Faces vocabulary. Current implementation supports TOP and BOTTOM.",
    },
    {
        "slug": "Shape.attach",
        "title": "Shape.attach()",
        "signature": _signature(Shape.attach, "Shape.attach"),
        "summary": "Legacy explicit feature anchoring for supported within-component features.",
        "contract": "For simple feature placement prefer on(); component assembly attachment is separate.",
    },
    {
        "slug": "Shape.shell",
        "title": "Shape.shell()",
        "signature": _signature(Shape.shell, "Shape.shell"),
        "summary": "Hollow a supported solid while leaving selected Faces open.",
        "contract": "The open= argument uses Faces selectors.",
    },
    {
        "slug": "Sketch",
        "title": "Sketch",
        "signature": _signature(Sketch, "Sketch"),
        "summary": "Explicit named 2D sketch scope, standalone or supported by an existing shape.",
        "contract": "Sketch(on=target) selects support; sketch-local profile placement is a separate concern.",
    },
    {
        "slug": "Sketch.add",
        "title": "Sketch.add()",
        "signature": _signature(Sketch.add, "Sketch.add"),
        "summary": "Add a supported 2D profile to an explicit Sketch.",
        "contract": (
            "Normative API design requires semantic 2D anchor placement. "
            "If the signature shown here lacks anchor=, implementation has not caught up with that contract."
        ),
    },
    {
        "slug": "Sketch.extrude",
        "title": "Sketch.extrude()",
        "signature": _signature(Sketch.extrude, "Sketch.extrude"),
        "summary": "Extrude a completed explicit Sketch with a Direction.",
        "contract": "Direction is relative to the sketch plane normal.",
    },
)


def enum_members(spec):
    """Return exact public member names/values from the implementation."""
    return [(member.name, member.value) for member in spec["object"]]


def all_references():
    return (*ENUM_REFERENCES, *METHOD_REFERENCES)
