# SolidCraft 0.43.0 — sketch Slot family

Pinned source: `tangency-labs/solidcraft` commit
`8ba46e9e2181396a9b5903b98031399aef61cf26`.

## Qualified change from 0.42.0

The relevant compatibility change is upstream #15857:

- 0.42.0 rejected expression-valued native Slot `width` at replay time;
- 0.43.0 accepts `width` as a number or expression;
- a parameter expression drives the native diameter dimension of the Slot end
  geometry.

This is the exact runtime contract required by Forge #355's first parametric
slice.

## Native family

```text
sketch.slot.center_to_center
sketch.slot.overall
sketch.slot.center_point
sketch.slot.arc_three_point
sketch.slot.arc_center
```

Relevant native input contracts:

- center-to-center: numeric `p0`, numeric `p1`, expression-capable `width`;
- overall: numeric `p0`, numeric `p1`, expression-capable `width`;
- center-point: numeric `center`, numeric `end`, expression-capable
  `width`;
- arc-three-point: centre-arc `start`, `through`, `end`,
  expression-capable `width`;
- arc-center: `center`, centre-arc `start`, expression-capable `width`,
  and exactly one of `end` or `sweep`.

## Parametric boundary

Do not generalize the width fix into a claim that every Slot authoring point is
expression-capable.

The straight Slot schemas use `PlainPoint` for their authoring coordinates and
explicitly reject expressions, point ids and snaps there. Parametric
length/position must therefore use the native dimension/constraint authoring
contract, not direct symbolic point substitution.

`sketch.draw.dimensioned` provides:

- `length` + `width` for the three straight variants;
- `radius` + `sweep` + `width` for center-arc Slot;
- `width` for three-point arc Slot.

Forge #355 must qualify each additional degree of freedom separately.
