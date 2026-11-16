# 0027 — native sketch slot family

Status: **implemented; full qualification required before merge**  
Issue: **#216**  
SolidCraft target: **0.42.0**

## Problem

SolidCraft exposes a dedicated Slot sketch family. Forge previously did not.

Using `RoundedRectangle2D` as a substitute is incorrect: it emits
`sketch.rectangle.rounded`, while SolidCraft has five separate native Slot
creation commands.

## Decision

Forge exposes five explicit constructors:

```text
SlotCenterToCenter2D -> sketch.slot.center_to_center
SlotOverall2D        -> sketch.slot.overall
SlotCenterPoint2D    -> sketch.slot.center_point
SlotArcThreePoint2D  -> sketch.slot.arc_three_point
SlotArcCenter2D      -> sketch.slot.arc_center
```

The constructor name states the SolidCraft construction method. There is no
generic `Slot(type=...)` switch.

SolidCraft 0.42's direct `sketch.slot.*` creators require fixed numeric
coordinates **and a numeric width**. Forge follows that contract exactly.

Parametric Slot dimensions are not faked by sending expressions to fields that
reject them. SolidCraft provides a separate `sketch.draw.dimensioned` authoring
route for parameter-backed dimensions; that capability is outside change 0027
and must be qualified separately before SCPF exposes it.

## Qualification

Forge qualifies the complete family itself with one small plate and one sketch
containing all five variants. Q1/Q2 must prove exact one-to-one native command
lowering. Native qualification uses a fixed negative cut from the TOP support
face and must prove SolidCraft 0.42 actually removes material, builds and saves
the sketch/cut without feature errors, and visually distinguishes the variants.

`Depth.THROUGH_ALL` on an attached explicit Sketch is deliberately not part of
this case: qualification exposed a separate no-op cut-direction problem, tracked
independently in issue #218.

No Slot qualification may lower through `sketch.rectangle.rounded`, a polygon
or hand-built line/arc geometry.

## Relationship to change 0026

Change 0026 / issue #215 concerns native **solid feature patterns**.
Change 0027 / issue #216 concerns native **sketch Slot construction**.
They are independently qualified before a downstream CAD model combines them.

## Qualification finding

The first native qualification used an attached Sketch with
`Depth.THROUGH_ALL`. SolidCraft saved an error-free timeline but removed no
material. That is a separate existing cut-direction problem tracked by issue
#218.

The Slot-family fixture therefore uses the already-qualified signed extrusion
path (`-5 mm`) and Q4 explicitly checks the resulting volume, face count and
face types. This prevents a visually plausible feature history from passing
when the body was not actually cut.
