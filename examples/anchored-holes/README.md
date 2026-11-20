# Face-relative hole with native pattern

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `features`

## Goal

Verify one TOP-face source hole cut followed by one native rectangular history pattern.

## Forge API

with Sketch(on=plate, parent=Anchor.TOP): Circle2D(...); source_cut = sketch.extrude(Depth.THROUGH_ALL); plate.rectangular_pattern(source_cut, ...)

## Forge model

A feature-based plate with one face-attached source hole cut and one native rectangular pattern that creates the second hole.

## How Forge builds it in SolidCraft

Forge emits one attached Hole sketch/cut and one native solid.pattern.rectangular history feature. No Forge-side repeat helper or expanded duplicate profiles are used.

## SolidCraft result

One plate with two through holes at the requested Y spacing, one source cut and one native rectangular pattern feature.

## Saved-design test

No saved-design mutation in this fixture; geometry and feature placement are measured at geometry.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `false`

The holes do not change the outer plate bounds. Volume and 3D hole-wall probes are required.

## Reference notes

- **OpenSCAD** — Comparable geometry normally uses difference() and repeated cylinders. This case instead qualifies one semantic TOP-face source cut plus native SolidCraft pattern history; native solid.hole itself is qualified separately by hole-family.
