# 0027 — native sketch slot family

Status: **active design**  
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

Straight and arc Slot widths may remain symbolic CAD dimensions. Authored Slot
point coordinates are currently fixed numeric sketch coordinates, matching the
qualified Forge path.

## Qualification

Forge qualifies the complete family itself with one small plate and one sketch
containing all five variants. Q1/Q2 must prove exact one-to-one native command
lowering. Native qualification must prove SolidCraft 0.42 builds and saves the
sketch/cut without feature errors and visual output distinguishes the variants.

No Slot qualification may lower through `sketch.rectangle.rounded`, a polygon
or hand-built line/arc geometry.

## Relationship to change 0026

Change 0026 / issue #215 concerns native **solid feature patterns**.
Change 0027 / issue #216 concerns native **sketch Slot construction**.
They are independently qualified before a downstream CAD model combines them.
