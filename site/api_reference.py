"""Generated API-reference metadata derived from the public Forge API.

Public names, signatures, enum members and explanatory text come from the
Python implementation and its public docstrings. This module contains only
grouping and navigation metadata.
"""

from enum import Enum
import inspect

import scpf as public_api
from scpf import (
    Anchor,
    Axis,
    Depth,
    Edges,
    Faces,
    Placement,
    Shape,
    Sketch,
    assembly,
    component,
)
from scpf.model_objects import Assembly, ModelInstance


def _signature(obj, name):
    try:
        return f"{name}{inspect.signature(obj)}"
    except (TypeError, ValueError):
        return None


def _doc_sections(obj):
    """Split one public docstring into generated reference sections."""
    doc = inspect.getdoc(obj) or ""
    sections = {
        "summary": [],
        "use_when": [],
        "limits": [],
        "parameters": [],
        "example": [],
    }
    current = "summary"
    headings = {
        "Use when:": "use_when",
        "Limits:": "limits",
        "Parameters:": "parameters",
        "Example:": "example",
    }
    for raw_line in doc.splitlines():
        line = raw_line.strip()
        if line in headings:
            current = headings[line]
            continue
        if line:
            sections[current].append(line)

    parameters = []
    for line in sections["parameters"]:
        if ":" in line:
            name, description = line.split(":", 1)
            parameters.append({
                "name": name.strip(),
                "description": description.strip(),
            })
        elif parameters:
            parameters[-1]["description"] += " " + line
        else:
            raise ValueError(
                "parameter documentation must use 'name: description': " + line
            )

    return {
        "summary": " ".join(sections["summary"]).strip(),
        "use_when": " ".join(sections["use_when"]).strip(),
        "limits": " ".join(sections["limits"]).strip(),
        "parameters": parameters,
        "example": "\n".join(sections["example"]).strip(),
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


def _group(slug, title, member_names, *, summary, guide=None, guide_anchor=None):
    """Describe navigation only; member API facts are introspected separately."""
    return {
        "kind": "group",
        "slug": slug,
        "title": title,
        "member_names": tuple(member_names),
        "summary": summary,
        "guide": guide,
        "guide_anchor": guide_anchor,
    }


def _is_enum_type(obj):
    return inspect.isclass(obj) and issubclass(obj, Enum)


def public_member(name):
    """Build generated reference data for one exported public symbol."""
    obj = getattr(public_api, name)
    if _is_enum_type(obj):
        kind = "enum"
        doc_obj = obj
    elif callable(obj):
        kind = "callable"
        doc_obj = obj
    else:
        kind = "constant"
        # X/Y/Z are public instances of the private implementation type. Its
        # docstring is still the authoritative explanation of their semantics.
        doc_obj = type(obj)

    result = {
        "kind": kind,
        "name": name,
        "object": obj,
        **_doc_sections(doc_obj),
    }
    if kind == "enum":
        result["members"] = [
            {"name": name, "value": member.value}
            for name, member in obj.__members__.items()
        ]
    elif kind == "callable":
        result["signature"] = _signature(obj, name)
    else:
        result["value"] = str(obj)
    return result


def anchor_aliases():
    """Return exported convenience names that are actual Anchor values."""
    return tuple(
        name
        for name in public_api.__all__
        if name != "Anchor" and isinstance(getattr(public_api, name), Anchor)
    )


ENUM_REFERENCES = (
    _enum("Faces", Faces, guide="features", guide_anchor="hole"),
    _enum("Anchor", Anchor, guide="assembly-basics", guide_anchor="anchor-choice"),
    _enum("Axis", Axis, guide="geometry", guide_anchor="solids"),
    _enum("Depth", Depth, guide="features", guide_anchor="hole"),
    _enum("Edges", Edges, guide="features", guide_anchor="fillet"),
)


METHOD_REFERENCES = (
    _method("Shape", "Shape", Shape, guide="model-objects", guide_anchor="shape"),
    _method(
        "component",
        "component() / @component",
        component,
        guide="assembly-basics",
        guide_anchor="simple-component",
    ),
    _method(
        "assembly",
        "assembly() / @assembly",
        assembly,
        guide="assembly-basics",
        guide_anchor="reusable-assembly",
    ),
    _method(
        "Occurrence.copy",
        "Occurrence.copy()",
        ModelInstance.copy,
        guide="assembly-basics",
        guide_anchor="collection",
    ),
    _method(
        "Occurrence.attach",
        "Occurrence.attach()",
        ModelInstance.attach,
        guide="assembly-basics",
        guide_anchor="relationship",
    ),
    _method(
        "Occurrence.group",
        "Occurrence.group()",
        ModelInstance.group,
        guide="assembly-basics",
        guide_anchor="group",
    ),
    _method(
        "Assembly.group",
        "Assembly.group()",
        Assembly.group,
        guide="assembly-basics",
        guide_anchor="group",
    ),
    _method(
        "Assembly.with_anchor",
        "Assembly.with_anchor()",
        Assembly.with_anchor,
        guide="components",
        guide_anchor="assembly-anchor",
    ),
    _method(
        "Assembly.anchor",
        "Assembly.anchor()",
        Assembly.anchor,
        guide="components",
        guide_anchor="assembly-anchor",
    ),
    _method("Shape.at", "Shape.at()", Shape.at, guide="geometry", guide_anchor="solids"),
    _method("Shape.on", "Shape.on()", Shape.on, guide="features", guide_anchor="hole"),
    _method(
        "Shape.attach",
        "Shape.attach()",
        Shape.attach,
        guide="features",
        guide_anchor="anchors",
    ),
    _method("Shape.fillet", "Shape.fillet()", Shape.fillet, guide="features", guide_anchor="fillet"),
    _method("Shape.chamfer", "Shape.chamfer()", Shape.chamfer, guide="features", guide_anchor="fillet"),
    _method("Shape.shell", "Shape.shell()", Shape.shell, guide="features", guide_anchor="shell"),
    _method(
        "Shape.repeat_linear",
        "Shape.repeat_linear()",
        Shape.repeat_linear,
        guide="features",
        guide_anchor="features",
    ),
    _method(
        "Shape.rectangular_pattern",
        "Shape.rectangular_pattern()",
        Shape.rectangular_pattern,
        guide="features",
        guide_anchor="feature-patterns",
    ),
    _method(
        "Shape.circular_pattern",
        "Shape.circular_pattern()",
        Shape.circular_pattern,
        guide="features",
        guide_anchor="feature-patterns",
    ),
    _method("Sketch", "Sketch", Sketch, guide="geometry", guide_anchor="profiles"),
    _method("Sketch.add", "Sketch.add()", Sketch.add, guide="geometry", guide_anchor="profiles"),
    _method(
        "Sketch.rectangular_pattern",
        "Sketch.rectangular_pattern()",
        Sketch.rectangular_pattern,
        guide="geometry",
        guide_anchor="pattern-mirror",
    ),
    _method(
        "Sketch.mirror",
        "Sketch.mirror()",
        Sketch.mirror,
        guide="geometry",
        guide_anchor="pattern-mirror",
    ),
    _method(
        "Sketch.extrude",
        "Sketch.extrude()",
        Sketch.extrude,
        guide="geometry",
        guide_anchor="profile-selection",
    ),
)


GROUP_REFERENCES = (
    _group(
        "geometry-constructors",
        "Geometry constructors",
        (
            "Box", "Cylinder", "Sphere",
            "Rectangle2D", "RoundedRectangle2D", "Circle2D", "Polygon2D",
        ),
        summary="Direct 3D primitives and 2D profile constructors.",
        guide="geometry",
        guide_anchor="solids",
    ),
    _group(
        "sketch-slot-constructors",
        "Native Slot constructors",
        (
            "SlotCenterToCenter2D",
            "SlotOverall2D",
            "SlotCenterPoint2D",
            "SlotArcThreePoint2D",
            "SlotArcCenter2D",
        ),
        summary="Five explicit 2D Slot construction methods mapped directly to SolidCraft sketch.slot.* commands.",
        guide="geometry",
        guide_anchor="profiles",
    ),
    _group(
        "feature-constructors",
        "Feature constructors",
        (
            "Hole",
            "CounterboreHole",
            "CountersinkHole",
            "ThreadedHole",
            "Lip",
            "SnapFit",
            "Boss",
            "Rest",
        ),
        summary="Mechanical Hole-family and plastic-feature intent added to supported bodies.",
        guide="features",
        guide_anchor="features",
    ),
    _group(
        "parameters-positioning",
        "Parameters and positioning helpers",
        (
            "Parameter", "Placement", "X", "Y", "Z",
            "up", "down", "left", "right", "front", "back",
            "half", "midpoint", "pv",
        ),
        summary="Keep dimensions symbolic and express readable offsets or parent-bound positions.",
        guide="model-objects",
        guide_anchor="parameter-intent",
    ),
    _group(
        "attachment-references",
        "Custom attachment references",
        ("AnchorFrame", "AnchorTopology"),
        summary="Use richer local or topology-backed datums when a standard Anchor is not enough.",
        guide="assembly-basics",
        guide_anchor="anchor-choice",
    ),
    _group(
        "execution-api",
        "Compiler and runner API",
        ("compile_model", "run_script"),
        summary="Lower-level entry points for compiling Shapes or trusted model source files.",
        guide="getting-started",
        guide_anchor="run",
    ),
    _group(
        "diagnostics",
        "Errors and warnings",
        ("ModelError", "ModelParameterWarning"),
        summary="Public diagnostics for invalid model intent and lost symbolic parameter dependencies.",
    ),
)


def enum_members(spec):
    """Return exact public member names/values from the implementation."""
    return [
        (name, member.value)
        for name, member in spec["object"].__members__.items()
    ]


def group_members(spec):
    """Return generated member descriptions for one navigation group."""
    return tuple(public_member(name) for name in spec["member_names"])


def all_references():
    return (*ENUM_REFERENCES, *METHOD_REFERENCES, *GROUP_REFERENCES)


def references_for_guide(slug):
    """Return generated-reference specs relevant to one guide chapter."""
    return tuple(
        spec for spec in all_references()
        if spec.get("guide") == slug
    )


def _guide_path(spec):
    if not spec.get("guide"):
        return None
    return f"guide/{spec['guide']}/#{spec['guide_anchor']}"


def public_reference(spec):
    """Return one JSON-serialisable public API reference entry."""
    result = {
        "kind": spec["kind"],
        "name": spec["slug"],
        "summary": spec["summary"],
        "guide": _guide_path(spec),
        "reference": f"reference/{spec['slug']}/",
    }

    if spec["kind"] == "group":
        members = []
        for member in group_members(spec):
            row = {
                key: value
                for key, value in member.items()
                if key != "object"
            }
            row["reference"] = f"reference/{spec['slug']}/#{member['name']}"
            members.append(row)
        result["members"] = members
        return result

    result["use_when"] = spec["use_when"]
    result["limits"] = spec["limits"]
    result["parameters"] = spec["parameters"]
    result["example"] = spec["example"]
    if spec["kind"] == "enum":
        result["members"] = [
            {"name": name, "value": value}
            for name, value in enum_members(spec)
        ]
        if spec["slug"] == "Anchor":
            result["aliases"] = list(anchor_aliases())
    else:
        result["signature"] = spec["signature"]
    return result


def export_reference_targets():
    """Map every public scpf export to its generated reference location."""
    targets = {}

    for spec in ENUM_REFERENCES:
        if spec["slug"] in public_api.__all__:
            targets[spec["slug"]] = f"reference/{spec['slug']}/"

    for spec in METHOD_REFERENCES:
        if spec["slug"] in public_api.__all__:
            targets[spec["slug"]] = f"reference/{spec['slug']}/"

    for spec in GROUP_REFERENCES:
        for name in spec["member_names"]:
            targets[name] = f"reference/{spec['slug']}/#{name}"

    for name in anchor_aliases():
        targets[name] = "reference/Anchor/"

    return targets


def unmapped_public_exports():
    targets = export_reference_targets()
    return tuple(name for name in public_api.__all__ if name not in targets)


def api_manifest():
    """Return the complete machine-readable API reference used by the website."""
    missing = unmapped_public_exports()
    if missing:
        raise ValueError(
            "public API exports missing from reference: " + ", ".join(missing)
        )
    return {
        "schema": 2,
        "generated_from": "scpf public objects and docstrings",
        "references": [public_reference(spec) for spec in all_references()],
    }


def _compact_symbol(row, *, guide=None):
    result = {
        "kind": row["kind"],
        "summary": row.get("summary", ""),
        "reference": row["reference"],
    }
    if guide:
        result["guide"] = guide
    if row["kind"] == "enum":
        result["members"] = {
            item["name"]: item["value"]
            for item in row["members"]
        }
    elif row["kind"] == "callable" and row.get("signature"):
        result["signature"] = row["signature"]
    elif row["kind"] == "constant":
        result["value"] = row["value"]
    return result


def agent_manifest():
    """Return the small first-read API index intended for coding agents.

    Detailed use/limit prose deliberately remains in the source docstrings,
    human guide and full site manifest. The local index is only for routing and
    exact current names/signatures/values.
    """
    full = api_manifest()
    symbols = {}

    for row in full["references"]:
        if row["kind"] == "group":
            for member in row["members"]:
                symbols[member["name"]] = _compact_symbol(
                    member, guide=row.get("guide")
                )
            continue

        symbols[row["name"]] = _compact_symbol(
            row, guide=row.get("guide")
        )

    anchor = next(
        row for row in full["references"]
        if row["name"] == "Anchor"
    )
    for alias in anchor.get("aliases", ()):
        target = getattr(public_api, alias)
        symbols[alias] = {
            "kind": "alias",
            "target": f"Anchor.{target.name}",
            "reference": "reference/Anchor/",
            "guide": anchor.get("guide"),
        }

    return {
        "schema": 1,
        "generated_from": "scpf public objects and docstrings",
        "symbols": symbols,
    }


if __name__ == "__main__":
    import json
    import sys
    manifest = agent_manifest() if "--agent" in sys.argv[1:] else api_manifest()
    print(json.dumps(manifest, indent=2))
