# Attached Polygon through-all cutter

**Group:** `features`
**Saved-design required:** `false`

> Documentation provenance: Forge #785 promotes the released #747 regression fixture to public Verification.

## Goal

Prove that authored Polygon2D coordinates lower correctly inside a named face-attached explicit Sketch and can drive native THROUGH_ALL cutting.

## Forge API

`Sketch(on=..., parent=...)`, `Polygon2D(...)`, `Sketch.extrude(Depth.THROUGH_ALL)` and normal Boolean subtraction.

## Forge model

An 80 × 60 × 5 mm bottom-anchored Box receives a 20 × 16 mm rectangular Polygon2D in a Sketch attached to its top face.

## How Forge builds it in SolidCraft

Forge creates the parent Box, creates the attached native Sketch on the top face, authors the Polygon2D curves in that Sketch frame and lowers the extrusion as a native through-all cut against the parent.

## SolidCraft result

One native Box body contains a named attached Sketch and one native through-all subtractive extrusion.

## Saved-design test

No separate parameter mutation is required for this focused lowering case; the native attached Sketch/through-all command contract and model verification are the primary evidence.

## Geometry evidence

> Geometry-rationale provenance: Forge #785 / #747 public capability promotion.
**Bounds sufficient:** `true`

The rectangular through-cut is fully characterized by the parent envelope and the resulting through opening for this focused case.

## Reference notes

- **Native SolidCraft history** — This case verifies Forge-to-SolidCraft attached-Sketch semantics; no fabricated external equivalent is required.
