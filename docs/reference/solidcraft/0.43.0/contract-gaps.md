# SolidCraft 0.43.0 contract gaps relevant to Forge

Pinned source: `tangency-labs/solidcraft` commit
`8ba46e9e2181396a9b5903b98031399aef61cf26`.

This file records only gaps relevant to the compatibility work that moved Forge
to SolidCraft 0.43.0.

## Slot authored points remain numeric

The native Slot `width` contract now accepts expressions, but straight Slot
authoring points remain `PlainPoint` values.

Therefore Forge must not lower a `Parameter` or `Expression` directly into:

- `center_to_center.p0` / `p1`;
- `overall.p0` / `p1`;
- `center_point.center` / `end`.

Parametric Slot length or placement requires a separately qualified native
dimension/constraint path.

## Width fix is not a fallback license

SolidCraft 0.43.0 fixes native expression-valued Slot width. Forge must use that
native contract. It must not silently bake the current parameter value to a
number or replace the Slot with rounded-rectangle geometry when a symbolic
width is requested.

## Unrelated command gaps

The 0.42.0 snapshot records several unrelated `engine.describe` typed-contract
gaps. This 0.43.0 compatibility slice does not claim those gaps are resolved.
Any future Forge feature that depends on an unrelated 0.43.0 command/result
field must capture and qualify that contract explicitly before use.
