# Native contour flange

**Group:** `sheet-metal`
**Saved-design required:** `true`

> Documentation provenance: Forge #785 promotes the released #684 contour-flange fixture to public Verification.

## Goal

Prove that a reusable connected open Sketch chain can create one native contour-flange sheet body with an explicit material rule.

## Forge API

`Sketch.chain(...)`, `line_to()`, `tangent_arc_to()`, `finish()` and `Shape.contour_flange(...)`.

## Forge model

An XZ line/tangent-arc/line chain creates a 50 mm wide, 2.5 mm thick contour flange using R2.5 and K=0.44.

## How Forge builds it in SolidCraft

Forge authors the ordered open Sketch chain, retains replay-bound native curve identity and passes the exact chain to one native contour-flange operation with one sheet rule.

## SolidCraft result

One native contour-flange sheet body preserves the connected Sketch source and recoverable developed geometry.

## Saved-design test

Mutate sheet width from 50 to 60 mm and the authored contour end height from 30 to 35 mm, then verify the rebuilt native sheet history.

## Geometry evidence

> Geometry-rationale provenance: Forge #785 / #684 public capability promotion.
**Bounds sufficient:** `false`

Bounds cannot prove ordered-chain replay identity or sheet-rule ownership; native history and flat-pattern inspection are required.

## Reference notes

- **Native SolidCraft history** — This is a native-history capability; external solid references are optional and must not be invented when they cannot express the same intent.
