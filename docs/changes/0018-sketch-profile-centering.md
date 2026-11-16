# Change 0018 — Center sketch profiles by semantic anchor

Status: implementation  
SolidCraft target: **0.42.0**

## Problem

The normative Forge API already says that a profile inside an explicit Sketch is
placed with:

```python
sketch.add(profile, anchor=CENTER)
```

and that `CENTER` is the default.

The implementation does not match that contract. `Sketch.add()` only accepts a
numeric `offset=(x, y)`. Rectangle and rounded-rectangle profiles therefore use
the offset as a hidden lower-left correction:

```python
offset=(-width / 2, -depth / 2)
```

That hides the design intent and makes `offset` mean two different things:
centering and a real local displacement.

## Contract

`Sketch.add()` becomes:

```python
sketch.add(profile, anchor=Anchor.CENTER, offset=(0, 0))
```

`CENTER` is exported as the short form of `Anchor.CENTER`.

For Circle2D, Rectangle2D and RoundedRectangle2D:

- the profile centre is placed on the Sketch origin by default;
- `offset=(u, v)` then moves that centred profile by the deliberate local
  displacement `(u, v)`;
- symbolic profile dimensions remain symbolic in emitted SolidCraft commands.

For a Sketch supported by a body, its local origin remains the centre of the
selected support face.

For a standalone Sketch, its origin is the selected plane origin, so a default
rectangle spans equally to both sides of zero.

## Coordinate-defined profiles

Polygon2D already contains explicit 2D vertex coordinates. Text2D uses a native
text insertion point. This change does not invent a bounding-box centre or text
alignment rule for those profiles.

Automatic capture therefore preserves their authored/insertion coordinates.
Explicit `Sketch.add(..., anchor=CENTER)` is rejected for Polygon2D and Text2D
until Forge has a qualified semantic centre for those profile types.

## Lowering

Centered rectangle and rounded rectangle lowering uses symmetric half-width /
half-depth coordinates around the requested profile centre.

Circle2D already lowers through `sketch.circle.center`.

No corrective `sketch.move` operation is introduced.

## Migration

Tests and examples that used `(-width/2, -depth/2)` only to centre a rectangle
or rounded rectangle are changed to the semantic default. Real design offsets,
such as placing repeated bays at different Y positions, remain as offsets from
the centred profile.

The anchored-holes qualification is migrated from a lower-left world origin to
a centred XY sketch origin. Its PythonSCAD, pyBOSL2 and CadQuery references are
updated to the same geometry.

Signed extrusion remains separate work under change 0006.

## Qualification

Required evidence:

- centered standalone Rectangle2D;
- centered Circle2D;
- centered attached RoundedRectangle2D;
- symbolic width/depth remain native expressions;
- deliberate local offset is applied after centering;
- Polygon2D coordinate-defined examples keep their current geometry;
- PythonSCAD, pyBOSL2 and CadQuery references match affected qualification
  geometry;
- full Q1-Q6 qualification remains green.

## Exit condition

> Profile centering is an explicit Sketch semantic. Numeric offset is only a
> deliberate local displacement, never a hidden centering correction.
