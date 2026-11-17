# 0030 — fixed Slot coordinates on parametric attached Sketches

Status: **implemented; qualification required before merge**  
Issue: **#266**  
SolidCraft target: **0.42.0**

## Problem

The public Sketch contract already says that for:

```python
Sketch(on=target, parent=Anchor.TOP)
```

the local Sketch origin `(0, 0)` is the centre of the selected target face.
Profile coordinates are relative to that local origin.

For a centered, TOP-anchored or BOTTOM-anchored Box, that XY face centre is
fixed at `(0, 0)` even when the Box width and depth are editable parameters.

Forge previously rebuilt the same centre as:

```text
corner_x + width / 2
corner_y + depth / 2
```

For a parametric centered Box this produced expressions equivalent to:

```text
-width / 2 + width / 2
-depth / 2 + depth / 2
```

The numeric result is zero, but the expression still carried parameter
dependencies. The native Slot compiler therefore rejected otherwise fixed
Slot points because SolidCraft 0.42 direct `sketch.slot.*` commands accept
numeric coordinates only.

## Decision

Forge now keeps the rectangular base centre as its own datum.

For a Box, the centre is derived directly from the authored Box anchor instead
of reconstructed from its corner plus half the dimensions. For a centered
Rectangle2D extrusion, the authored sketch offset is likewise already the
profile centre.

Attached explicit Sketch lowering uses that preserved centre for sketch-local
coordinates.

This means a fixed Slot such as:

```python
SlotCenterToCenter2D((-60, -35), (-40, -35), 8)
```

stays numeric when placed on a parametrically sized Box whose face centre is
itself fixed.

## SolidCraft behaviour

SolidCraft 0.42 direct Slot creators require numeric point coordinates and a
numeric width. Forge does not send parameter expressions to those fields.

The fix only removes a false dependency introduced by Forge. It does not turn
a genuinely parameter-dependent Slot position into a fixed value.

If the selected target-face centre genuinely moves with a parameter, for
example because a side/corner Box anchor makes the face centre depend on the
Box width or depth, the direct Slot command still cannot represent that
relationship. Supporting that case requires the separate dimensioned-sketch
route and is outside issue #266.

## Qualification

The existing `slot-family` case keeps the same visible geometry but its SCPF
parent Box now uses editable `width`, `depth` and `thickness` model
parameters.

Q1/Q2 must prove:

- the Box dimensions remain native parameter expressions;
- all five Slot constructors still lower one-to-one to `sketch.slot.*`;
- every Slot point coordinate remains numeric;
- no rounded-rectangle or polygon fallback is introduced.

Native qualification must continue to prove the Slot sketch cuts the body in
SolidCraft 0.42 without feature errors.
