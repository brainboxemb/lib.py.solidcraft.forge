# 0032 — associative Sketch pattern and mirror handles

Status: **implemented**  
Issue: **#272**  
SolidCraft target: **0.42.0**

## Problem

Forge could author native Circle and Slot profiles, but repeated sketch
geometry had to be expanded into independent profile calls. That lost the
editable SolidCraft relationship between a master profile and its copies.

## Public API

A profile authored in a `Sketch` can now be used as the source of a native
rectangular sketch pattern:

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

The same mechanism works with native Slot profiles:

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

Both methods return a Sketch operation handle that may be used as the source of
a later supported sketch operation.

## Native lowering

Forge does not predict SolidCraft curve ids.

The seed command binds SolidCraft's returned `curves` value to a replay
variable. `sketch.pattern.rectangular` consumes that variable and can bind its
own returned `curves`; `sketch.mirror` does the same. All geometry remains
inside one native Sketch and can be cut/extruded once.

Pattern `count`/`count2` may be dimensionless Forge Parameters and spacing
values may be length Parameters. They remain native editable expressions in the
saved SolidCraft design.

## Replay

Replay version 2 is now the only accepted replay document version. Old
replay-v1 files are intentionally unsupported. The direct field-binding form
remains valid in v2; replay variables are runtime values returned by SolidCraft,
not a public modelling API.

## Qualification

The focused `sketch-pattern-mirror` case covers both Circle and
`SlotCenterToCenter2D` seeds, native rectangular patterns, chained mirrors,
one cut per Sketch, independent comparison geometry and saved-design parameter
mutation under SolidCraft 0.42.

The Simple MFT conversion is a downstream CAD-model follow-up and is not part
of this Forge change.
