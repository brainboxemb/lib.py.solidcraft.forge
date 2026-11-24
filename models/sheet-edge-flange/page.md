# Native sheet edge flange

**Group:** `sheet-metal`
**Saved-design required:** `true`

> Documentation provenance: Forge #785 promotes the released #682 edge-flange fixture to public Verification.

## Goal

Prove that an existing sheet edge can grow one native editable flange while material values remain owned by the active sheet rule.

## Forge API

`Sketch.sheet_metal(...)` creates the blank; `Shape.flange(edges=..., height=..., angle=...)` adds the existing-edge feature.

## Forge model

An 80 × 40 × 2 mm sheet receives a flange on its right edge. Height starts at 20 mm and angle at 90 degrees.

## How Forge builds it in SolidCraft

Forge creates one sheet rule and flat sheet body, resolves the fixed edge pick and emits one native edge-flange feature. Height and angle remain feature dimensions.

## SolidCraft result

One native sheet body has one inherited-rule edge flange and a recoverable flat pattern.

## Saved-design test

Mutate flange height from 20 to 25 mm and bend angle from 90 to 75 degrees, then verify rebuilt native feature and flat-pattern evidence.

## Geometry evidence

> Geometry-rationale provenance: Forge #785 / #682 public capability promotion.
**Bounds sufficient:** `false`

The formed bounds do not prove inherited rule ownership or native flange/flat-pattern history; inspection of sheet and bend records is required.

## Reference notes

- **Native SolidCraft history** — The verification target is native sheet-rule and flange history, so independent solid-only references are optional rather than fabricated.
