# Minimal L-profile

A simple XZ L-profile provides a clean reusable geometry baseline.

An L-shaped polygon is authored in XZ and symmetrically extruded without holes,
fillets or secondary features.

- **Group:** `fundamentals`
- **Parameters:** 24 mm extrusion width; 40 mm arms; 12 mm arm thickness
- **Model:** [`scpf/model.py`](scpf/model.py)
- **Verification:** [`verification/solidcraft.py`](verification/solidcraft.py)
- **Page metadata:** [`model.yml`](model.yml)

## Build stages

1. Create the L-shaped XZ polygon.
2. Finish the explicit Profile sketch.
3. Extrude the profile symmetrically through 24 mm.

## Goal

Provide a deliberately simple reusable L-shaped reference component for later attachment/orientation qualification.

## Forge API

with Sketch(plane='XZ'): Polygon2D(..., plane='XZ'); sketch.extrude(width, direction=Direction.SYMMETRIC)

## Forge model

One symbolic L profile extruded symmetrically through its width; no holes, fillets, anchors or secondary features.

## How Forge builds it in SolidCraft

Native XZ sketch/polygon plus symmetric extrusion. No assembly commands are present yet.

## SolidCraft result

A clean 40 mm L profile with 12 mm arms and 24 mm symmetric extrusion width.

## Saved-design test

Not yet an attachment mutation case. This component is intentionally the geometry baseline for upcoming multi-orientation anchor tests.

## Geometry evidence

**Bounds sufficient:** `false`

A filled box can share the L-profile envelope. L-profile volume and a probe in the missing corner are required.

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

## Reference notes

- **OpenSCAD** — Equivalent baseline is a 2D L polygon followed by linear_extrude(center=true).
- **BOSL2** — Later attachment cases can reuse this simple shape while testing anchor/orient semantics independently of bracket feature complexity.

## Source provenance

The engineering statements under Goal, Forge API, Forge model, SolidCraft
lowering/result, Saved-design test and Reference notes are preserved verbatim
from the last canonical `qualification/cases.py` source before its removal,
commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

Current machine verification lives in
[`verification/solidcraft.py`](verification/solidcraft.py); accepted measured results
come from durable `build/main`.
