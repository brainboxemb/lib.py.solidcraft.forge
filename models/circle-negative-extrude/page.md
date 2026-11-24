# Negative circle profile extrusion

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/solidcraft.py`](verification/solidcraft.py).

**Legacy group:** `fundamentals`

## Goal

Qualify Circle2D authored inside an explicit Sketch and a negative signed extrusion distance with one minimal native model.

## Forge API

with Sketch(plane='XY'): Circle2D(d=20); sketch.extrude(-30)

## Forge model

One circular 2D profile authored in an explicit XY Sketch and extruded 30 mm along negative Z; no CSG or attachment is involved.

## How Forge builds it in SolidCraft

The signed Forge distance is normalized to a positive native distance plus solid.extrude(direction='negative').

## SolidCraft result

One 20 mm diameter cylindrical body spans X/Y -10..10 mm and Z -30..0 mm, with an error-free saved SolidCraft timeline.

## Saved-design test

No saved-design mutation in this fixture; it isolates direct circle-profile lowering and negative extrusion semantics.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `false`

A box can share the same envelope as this cylinder. Circular volume and a radial surface probe are required.

## Reference notes

- **OpenSCAD** — Comparable to a circle followed by linear_extrude(height=30) after selecting the opposite extrusion direction.
- **SolidCraft** — The persisted native extrusion direction and measured Z bounds are the source of truth for negative-direction semantics.
