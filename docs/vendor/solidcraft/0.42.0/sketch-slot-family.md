# SolidCraft 0.42.0 — sketch Slot family

Pinned source: `tangency-labs/solidcraft` commit
`1b1e940cc48e4d1d5d01971a4be20e2e55647066`.

SolidCraft exposes one Slot UI family with five native commands:

```text
sketch.slot.center_to_center
sketch.slot.overall
sketch.slot.center_point
sketch.slot.arc_three_point
sketch.slot.arc_center
```

Relevant input contracts:

- center-to-center: `p0`, `p1` are the two round-end centres; `width`.
- overall: `p0`, `p1` are the two outer overall ends; `width`.
- center-point: `center`, one end-arc `end`; `width`.
- arc-three-point: centre-arc `start`, `through`, `end`; `width`.
- arc-center: arc `center`, centre-arc `start`, `width`, and exactly one
  of `end` or `sweep` (degrees, 0 < sweep < 360).

The direct Slot creator schemas require numeric point coordinates and a numeric
`width`; `SlotWidth` is explicitly a JSON number. SolidCraft's separate
`sketch.draw.dimensioned` command can attach semantic dimensions after/during
creation. Its dimension roles are length/width for the three straight variants,
radius/sweep/width for the center arc variant, and width for the three-point arc
variant. Forge change 0027 qualifies the direct creator family only.

These are native Slot creators. `sketch.rectangle.rounded` is a different
command and is not a Slot substitute for qualification.
