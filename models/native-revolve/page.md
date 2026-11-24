# Native sketch revolve

> Documentation provenance: authored for Forge issue #843 from the qualified SolidCraft 0.48.1 `solid.revolve` command contract and this fixture's native replay evidence.

- **Group:** `fundamentals`
- **Saved-design required:** `true`

## Goal

Qualify a small public Forge API for native profile-driven revolve so downstream
mechanical models such as the latch can create turned pins and rivets without
approximating them with cylinders, extrusions or fused primitives.

## Forge API

`Sketch.revolve(axis=Axis.X, angle=..., sym=False)` on one completed standalone
closed profile whose world axis lies in the Sketch plane.

## Forge model

A 10 mm long radial rectangle with a 4 mm radius is authored on XZ and revolved
360 degrees around world X. Length, radius and sweep remain editable model
parameters.

## How Forge builds it in SolidCraft

Forge emits the native Sketch and profile commands followed by
`solid.revolve`. Root use creates a named body; Boolean use selects SolidCraft
`join`, `cut` or `intersect` directly on the Revolve feature. No temporary
body or primitive approximation is introduced.

## SolidCraft result

One closed native revolved solid with one solved source Sketch and one native
Revolve history feature. SolidCraft stores angle-valued parameters internally
in radians while Forge authors and exposes their unit as degrees.

## Saved-design test

The saved design changes radius from 4 mm to 5 mm and sweep from 360 degrees to
180 degrees. Native recompute must produce a half-cylinder with the expected
analytic volume while preserving the Sketch/Revolve history.

## Geometry evidence

> Geometry-rationale provenance: authored for Forge issue #843 from the analytic volume of a revolved rectangular radial profile and native saved-design measurements.

**Bounds sufficient:** `false`

Bounds alone cannot distinguish a full revolved cylinder from another solid
with the same envelope. Verification therefore requires body count, closed
body state, analytic volume, parameter mutation and native timeline evidence.

## Reference notes

- **SolidCraft** — SolidCraft 0.48.1 supplies the native `solid.revolve` feature and saved-design recompute used by this qualification.
- **Downstream latch** — CAD issue #30 needs native turned rivets/pins; this fixture isolates only the reusable Revolve primitive required by that model.
