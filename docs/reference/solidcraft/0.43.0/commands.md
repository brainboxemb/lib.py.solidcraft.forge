# SolidCraft 0.43.0 — focused command reference

Pinned source: `tangency-labs/solidcraft` commit
`8ba46e9e2181396a9b5903b98031399aef61cf26`.

This file records only the native commands materially relevant to Forge's
0.42.0 -> 0.43.0 compatibility move.

## Native Slot creators

SolidCraft exposes five native Slot commands:

```text
sketch.slot.center_to_center
sketch.slot.overall
sketch.slot.center_point
sketch.slot.arc_three_point
sketch.slot.arc_center
```

For all five creators, `width` accepts a number or an expression over design
parameters. An expression naming a parameter drives the native Slot width.

The three straight variants use numeric authoring points:

- `center_to_center`: `p0`, `p1` are the two round-end centres;
- `overall`: `p0`, `p1` are the two overall ends;
- `center_point`: `center` is the Slot centre and `end` one round-end
  centre.

The arc variants retain their native geometric point inputs plus `width`.

## Dimensioned authoring roles

`sketch.draw.dimensioned` exposes the following Slot roles in 0.43.0:

| Creator | Roles |
| --- | --- |
| `slot.center_to_center` | `length`, `width` |
| `slot.overall` | `length`, `width` |
| `slot.center_point` | `length`, `width` |
| `slot.arc_center` | `radius`, `sweep`, `width` |
| `slot.arc_three_point` | `width` |

These roles are native sketch dimensions. Forge must preserve that semantic
authoring model rather than replacing Slots with rounded rectangles or other
approximated geometry.
