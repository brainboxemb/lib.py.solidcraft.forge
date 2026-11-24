# Rotated standalone Sketch cutters

**Group:** `features`
**Saved-design required:** `false`

> Documentation provenance: Forge #785 promotes the released #750 regression fixture to public Verification.

## Goal

Prove that standalone Sketches with explicit local rotation frames remain native Sketch history when their extrusions are used as non-axis-aligned Boolean cutters.

## Forge API

`Sketch(..., origin=..., rotation=...)`, `Polygon2D(...)`, `Sketch.extrude(...)` and normal Boolean subtraction.

## Forge model

A 60 × 60 × 30 mm Box is cut by two triangular 8 mm extrusions authored in local Sketch frames rotated ±45 degrees.

## How Forge builds it in SolidCraft

Forge creates each standalone Sketch with its explicit origin and native frame directions, authors the Polygon2D in that local frame, extrudes it and applies the result directly as a cut against the parent body.

## SolidCraft result

One Box body contains two native subtractive extrusions sourced from separately named rotated Sketches.

## Saved-design test

No separate parameter mutation is required for this focused frame/lowering case; native Sketch-frame and cut-target command contracts are the primary evidence.

## Geometry evidence

> Geometry-rationale provenance: Forge #785 / #750 public capability promotion.
**Bounds sufficient:** `false`

Bounds alone cannot prove that the two triangular cutters were authored in the intended rotated local frames, so native Sketch-frame inspection is required.

## Reference notes

- **Native SolidCraft history** — This verifies a Forge/SolidCraft local-frame capability rather than cross-kernel shape equivalence; no artificial external reference is required.
