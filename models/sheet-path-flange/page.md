# Native path flange

**Group:** `sheet-metal`
**Saved-design required:** `true`

> Documentation provenance: Forge #785 promotes the released #776 path-flange fixture to public Verification.

## Goal

Prove that an existing sheet edge can follow a reusable line-only open Sketch path as one native path-flange feature.

## Forge API

`Sketch.chain(...)`, `line_to()`, `finish()` and `Shape.path_flange(edge=..., path=..., radius=...)`.

## Forge model

An 80 × 40 × 2 mm sheet uses a 14 mm open path and a 3 mm feature-radius override on the right edge.

## How Forge builds it in SolidCraft

Forge authors the reusable open path, resolves the fixed sheet edge and emits one native path-flange feature. Thickness and K-factor remain owned by the active rule.

## SolidCraft result

One native sheet body contains one path flange with a recoverable flat pattern and one bend record.

## Saved-design test

Mutate path height from 14 to 18 mm and feature radius from 3 to 4 mm, then verify the rebuilt native history and flat pattern.

## Geometry evidence

> Geometry-rationale provenance: Forge #785 / #776 public capability promotion.
**Bounds sufficient:** `false`

The formed envelope cannot prove path reuse, feature-radius ownership or native flat-pattern history.

## Reference notes

- **Native SolidCraft history** — Path-flange verification targets native sheet history; external references are optional when they cannot represent the same feature contract.
