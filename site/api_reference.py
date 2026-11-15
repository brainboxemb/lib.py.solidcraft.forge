"""Generated API-reference metadata derived from the public Forge API.

Public names, signatures, enum members and explanatory text come from the
Python implementation and its public docstrings. This module contains only
grouping and navigation metadata.
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


def _doc_sections(obj):
    """Split one public docstring into summary, use-when and limits sections."""
    doc = inspect.getdoc(obj) or ""
    sections = {"summary": [], "use_when": [], "limits": []}
    current = "summary"
    for raw_line in doc.splitlines():
        line = raw_line.strip()
        if line == "Use when:":
            current = "use_when"
            continue
        if line == "Limits:":
            current = "limits"
            continue
        if line:
            sections[current].append(line)
    return {
        key: " ".join(lines).strip()
        for key, lines in sections.items()
    }


def _enum(slug, obj, *, guide, guide_anchor):
    return {
        "kind": "enum",
        "slug": slug,
        "title": slug,
        "object": obj,
        "guide": guide,
        "guide_anchor": guide_anchor,
        **_doc_sections(obj),
    }


def _method(slug, title, obj, *, guide, guide_anchor):
    return {
        "kind": "callable",
        "slug": slug,
        "title": title,
        "object": obj,
        "signature": _signature(obj, slug),
        "guide": guide,
        "guide_anchor": guide_anchor,
        **_doc_sections(obj),
    }


ENUM_REFERENCES = (
    _enum("Faces", Faces, guide="features", guide_anchor="hole"),
    _enum("Anchor", Anchor, guide="components", guide_anchor="attach"),
    _enum("Axis", Axis, guide="geometry", guide_anchor="solids"),
    _enum("Direction", Direction, guide="geometry", guide_anchor="profiles"),
    _enum("Depth", Depth, guide="features", guide_anchor="hole"),
    _enum("Edges", Edges, guide="features", guide_anchor="fillet"),
)


METHOD_REFERENCES = (
    _method("Shape.at", "Shape.at()", Shape.at, guide="geometry", guide_anchor="solids"),
    _method("Shape.on", "Shape.on()", Shape.on, guide="features", guide_anchor="hole"),
    _method(
        "Shape.attach",
        "Shape.attach()",
        Shape.attach,
        guide="features",
        guide_anchor="anchors",
    ),
    _method("Shape.shell", "Shape.shell()", Shape.shell, guide="features", guide_anchor="shell"),
    _method("Sketch", "Sketch", Sketch, guide="geometry", guide_anchor="profiles"),
    _method("Sketch.add", "Sketch.add()", Sketch.add, guide="geometry", guide_anchor="profiles"),
    _method(
        "Sketch.extrude",
        "Sketch.extrude()",
        Sketch.extrude,
        guide="geometry",
        guide_anchor="profiles",
    ),
)


def enum_members(spec):
    """Return exact public member names/values from the implementation."""
    return [(member.name, member.value) for member in spec["object"]]


def all_references():
    return (*ENUM_REFERENCES, *METHOD_REFERENCES)


def references_for_guide(slug):
    """Return generated-reference specs relevant to one guide chapter."""
    return tuple(spec for spec in all_references() if spec["guide"] == slug)


def public_reference(spec):
    """Return one JSON-serialisable public API reference entry."""
    result = {
        "kind": spec["kind"],
        "name": spec["slug"],
        "summary": spec["summary"],
        "use_when": spec["use_when"],
        "limits": spec["limits"],
        "guide": f"guide/{spec['guide']}/#{spec['guide_anchor']}",
        "reference": f"reference/{spec['slug']}/",
    }
    if spec["kind"] == "enum":
        result["members"] = [
            {"name": name, "value": value}
            for name, value in enum_members(spec)
        ]
    else:
        result["signature"] = spec["signature"]
    return result


def api_manifest():
    """Return the compact API index used by both site checks and agents."""
    return {
        "schema": 1,
        "generated_from": "scpf public objects and docstrings",
        "references": [public_reference(spec) for spec in all_references()],
    }
