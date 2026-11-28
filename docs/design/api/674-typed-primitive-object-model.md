# #674 — typed primitive frontend object model

Status: accepted for implementation on the normal `dev` lane.

## Problem

The public primitive spelling is concise, but the implementation historically
encoded Box, Sphere, Cylinder and Cone as generic `Shape(kind, data)` values.
Primitive meaning was then decoded repeatedly from string tags and positional
tuples by alignment, placement, semantic normalization and legacy compilation.

That representation is a compatibility format, not a maintainable authoring
object model.

## Contract

The public authoring calls remain unchanged:

~~~python
Box(80, 50, 12, anchor=Anchor.BOTTOM)
Cylinder(d=8, h=20, axis=Axis.X)
~~~

Those constructors now return typed `Primitive` Shape subclasses. Each
primitive owns named semantic state such as dimensions, axis and anchor plus
the primitive-specific geometry needed for anchor/center placement.

`Shape` continues to own generic composition and feature operations.

## Compatibility boundary

`Shape.kind` and `Shape.data` remain available as an immutable compatibility
snapshot because legacy compiler paths still consume them. New frontend and IR
normalization code must use typed primitive state instead of adding new
string-kind decoding.

Raw `Shape("box", ...)` values remain accepted at the semantic normalizer as a
bounded compatibility path. They are not the preferred public construction
model.

## Dependency boundary

Frontend primitive objects remain backend-neutral. They may answer semantic
geometry questions such as center, base or corner for an anchor, but they do not
emit SolidCraft/Mitcad commands and do not import backend modules.

The intended flow stays:

~~~text
typed authoring objects
-> semantic IR normalization
-> backend lowering
~~~

## Completion

The change is complete when typed primitive ownership, alignment/placement,
semantic IR normalization, legacy compatibility and full Forge qualification
are green without model-source changes.
