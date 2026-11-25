# Contour flange recess replay

**Group:** `sheet-metal`
**Saved-design required:** `false`

> Documentation provenance: Forge #845 live/headless contour-flange recess investigation.

## Goal

Reproduce the smallest known downstream divergence around a valid recess on a
native contour flange without carrying the Mounting Rail M8 assembly or repeat
pattern.

## Forge API

`Sketch.chain(...)`, `Shape.contour_flange(...)`, face-attached
`Sketch(..., on=..., parent=Anchor.TOP)`, `Circle2D(...)` and
`Sketch.extrude(Depth.THROUGH_ALL)`.

## Forge model

The fixture uses a 250 mm long 27 × 18 × 1.25 mm C-profile with a 15 mm
opening, R1.25 bend rule and K=0.40. One Ø12.5 mm circular cut is centred
across the broad 27 mm back face at Y=37.5 mm.

This is the exact first-cut position from the downstream standalone rail that
fails through live replay. The 1000 mm assembly variant also fails with its
first cut at Y=12.5 mm.

## How Forge builds it in SolidCraft

Forge authors one open XZ contour, creates one native contour-flange sheet
body, resolves the broad +Z planar face through `model.faces`, attaches the
circular Sketch to that exact face and emits one through-all cut.

The replay document therefore contains the same face-binding boundary that is
present in the downstream failure.

## SolidCraft result

A successful replay produces one closed native sheet-metal body with the
circular recess on the broad planar face and keeps both source Sketches in
native history.

## Saved-design test

No parameter mutation is required for this regression. The baseline native
replay itself is the qualification: SolidCraft must accept the valid recess and
save the resulting native sheet body.

## Geometry evidence

> Geometry-rationale provenance: Forge #845 minimal downstream reproduction.

**Bounds sufficient:** `false`

Bounds alone cannot prove that the circular cut was accepted as a valid recess
on the intended sheet face or that the face-binding/replay boundary behaved
correctly. Native saved-design history is required.

## Reference notes

- **Downstream Mounting Rail M8** — The fixture preserves the physical C-profile and first broad-face recess geometry that exposed Forge #845; no product pattern or assembly behavior is needed to reproduce the native operation.
