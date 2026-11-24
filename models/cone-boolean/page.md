# Cone as a native Boolean feature

**Group:** `features`
**Saved-design required:** `false`

> Documentation provenance: Forge #785 promotes the released #746 Cone Boolean capability to public Verification.

## Goal

Prove that a placed `Cone` can participate in native Boolean feature compilation after the target body already owns ordered feature history.

## Forge API

`Box(...).fillet(...)`, `Cone(...).at(...)` and the normal `+` Boolean operator.

## Forge model

A 50 × 40 × 20 mm bottom-anchored Box receives R2 vertical fillets. An Ø18→Ø10 × 8 mm Cone starts at Z18, overlaps the Box by 2 mm and extends the model to Z26.

## How Forge builds it in SolidCraft

The Box and fillet establish ordered feature history. Forge then delegates the placed Cone operand to the shared primitive Boolean lowering and emits native `solid.cone` with `operation=join`, the existing body as target and the authored placed base.

## SolidCraft result

One connected native body retains the filleted Box history and the joined tapered Cone.

## Saved-design test

Not required for this focused compiler-route case. Parameterized Cone expressions, direct joins and Cone cuts remain covered by the #746 reusable compiler tests.

## Geometry evidence

> Geometry-rationale provenance: Forge #785 / #746 public capability promotion.
**Bounds sufficient:** `true`

The focused native model must remain one body with the unchanged Box footprint and a top extent of Z26. The command-contract test separately proves that the taper is authored as native `solid.cone` Boolean history rather than a temporary solid approximation.

## Reference notes

- **Native SolidCraft history** — This case verifies Forge-to-SolidCraft native feature lowering; external kernel references are optional and are not fabricated.
