# 0024 — signed Sketch extrusion distance

## Problem

`Sketch.extrude(distance, direction=Direction...)` states the same direction
twice: once as a magnitude and once as a separate enum. It is verbose for the
common positive and negative cases.

## Decision

The public API is:

```python
sketch.extrude(height)
sketch.extrude(-height)
sketch.extrude(height, sym=True)
```

Positive distance follows the sketch-plane normal. Negative distance uses the
opposite direction. `sym=True` requires a positive distance and divides that
distance equally over both sides of the sketch plane.

The public Extrude `Direction` enum and `direction=` argument are removed.
`Depth.THROUGH_ALL` remains supported for attached sketch cuts and cannot be
combined with `sym=True`.

## Lowering

Forge normalizes a finite signed distance to the positive native SolidCraft
distance plus its existing `positive`, `negative` or `symmetric` extrusion
direction. Symbolic Parameter/Expression dependencies remain symbolic.

## Qualification

The existing circle-negative-extrude geometry remains unchanged and now uses
`sketch.extrude(-self.height)`. The bracket case uses `sym=True`.
Focused Q1/Q2 tests cover positive, negative, symmetric, zero and invalid
symmetric distances.
