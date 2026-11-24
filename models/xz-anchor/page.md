# Anchors on XZ-profile extrusion

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Legacy group:** `anchors`

**Saved-design required:** `true`

## Goal

Verify standard corner anchors on geometry authored as an XZ polygon and extruded in Y.

## Forge API

with Sketch(plane='XZ'): Polygon2D(..., plane='XZ', world=True); sketch.extrude(...); standard corner Anchors

## Forge model

Forge recovers rectangular bounds/topology from the XZ profile while preserving symbolic width and height. RightMarker and LeftMarker are separate small test parts so this case tests the board anchors, not copied-occurrence addressing.

## How Forge builds it in SolidCraft

Two joint.create commands use the Board corner topology plus explicit RightMarker and LeftMarker occurrence references. No generated Component:N name is required.

## SolidCraft result

Left and right markers attach to their respective front-top corners with mirrored spatial results.

## Saved-design test

Change board width/height from 40x20 to 80x40 mm; both markers follow their own corners.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

The board and marker positions describe the visible XZ placement. After resizing the saved model, the markers must still use the same selected anchors.

## Reference notes

- **OpenSCAD** — The profile/extrusion resembles polygon()+linear_extrude(), but Forge retains native SolidCraft parameters and attachment topology.
- **BOSL2** — Mirrored corner anchors are a useful check that local anchor frames, not a single global direction assumption, control attachment.
