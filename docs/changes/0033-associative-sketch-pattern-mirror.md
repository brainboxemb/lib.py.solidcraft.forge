# 0033 — associative Sketch pattern and mirror handles

Status: **implemented**  
Issue: **#272**  
SolidCraft target: **0.42.0**

## Problem

Forge could create native Circle and Slot profiles, but repeated sketch
geometry had to be expanded into independent profile calls. That produced the
shape but lost SolidCraft's editable relationship between a master profile and
its copies.

## Public API

A profile authored in a `Sketch` can now seed a native rectangular sketch
pattern:

```python
with Sketch(name="Dog holes", on=board, parent=Anchor.TOP) as sketch:
    seed = sketch.add(Circle2D(d=20), offset=(-304, 0))
    row = sketch.rectangular_pattern(
        seed,
        count=9,
        spacing=76,
        direction=Axis.X,
    )
    sketch.mirror(row, axis=Axis.Y)
```

The same generic mechanism works with native Slot profiles:

```python
with Sketch(name="Clamp slots", on=board, parent=Anchor.TOP) as sketch:
    seed = SlotCenterToCenter2D((20, 20), (40, 20), 8)
    arm = sketch.rectangular_pattern(
        seed,
        count=2,
        spacing=50,
        direction=Axis.X,
    )
    opposite = sketch.mirror(arm, axis=Axis.Y)
    sketch.mirror(arm, axis=Axis.X)
    sketch.mirror(opposite, axis=Axis.X)
```

Both methods return a Sketch operation handle that can be used as the source of
a later supported sketch operation.

## Native lowering

Forge never predicts SolidCraft curve ids.

A seed profile command binds the returned `curves` field to a replay variable.
`sketch.pattern.rectangular` consumes those curves and can bind its own
returned `curves`. `sketch.mirror` does the same. The repeated geometry
therefore remains inside one native Sketch and one final extrusion/cut can use
all resulting profiles.

Pattern `count` and `count2` may be dimensionless Forge Parameters. Spacing
values may be length Parameters. Those values stay editable in the saved
SolidCraft design.

## Replay

Replay version 2 is the only supported replay document version after this
change. The simple direct-field binding form remains valid in v2. Replay
variables are execution values returned by SolidCraft, not a public modelling
API.

## Initial limits

This issue qualifies only what the current models need:

- attached Sketches;
- native rectangular sketch pattern;
- fixed 2D direction vectors or `Axis.X` / `Axis.Y`;
- mirror over the Sketch X or Y origin axis;
- no per-instance pattern suppression.

Circular sketch patterns and arbitrary mirror-line support are separate future
capabilities.

## Qualification

The focused `sketch-pattern-mirror` case proves:

- one Circle seed → native rectangular pattern → native mirror;
- one `SlotCenterToCenter2D` seed → native rectangular pattern → chained
  native mirrors;
- one cut per Sketch;
- independent PythonSCAD, pyBOSL2, CadQuery and build123d reference geometry;
- saved-design mutation of seed diameter, pattern count and pattern spacing
  under SolidCraft 0.42 without rerunning Python.

The Simple MFT conversion is a downstream CAD-model follow-up and is not part
of this Forge issue.
