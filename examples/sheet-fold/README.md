# Flat sheet, through hole and 90° fold

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `features`

## Goal

Qualify the fabrication workflow used by later bent parts: create one flat sheet blank, cut an ordinary Hole while flat, fold existing material, and recover the developed flat pattern.

## Forge API

with Sketch(...): Rectangle2D(...); blank.sheet_metal(thickness=..., bend_radius=..., k_factor=...); sheet + Hole(...).at(...); sheet.fold(line=..., angle=..., fixed=...)

## Forge model

One 80 x 40 mm rectangular flat blank with a shared 2 mm sheet rule, one Ø6 through hole in the fixed flat, and one 90 degree fold along the Y direction near the right side.

## How Forge builds it in SolidCraft

Forge emits one sheet.manage_rules, one Blank sketch, one sheet.flange(type='base'), one native solid.hole and one native sheet.fold. No solid.extrude or fused-solid bend approximation is used.

## SolidCraft result

SolidCraft 0.42 keeps one connected sheet-metal body with the Ø6 hole on the fixed flat, one native Fold feature and a flat pattern that recovers the original rectangular blank and cutout.

## Saved-design test

No saved-design mutation is required in this first sheet-metal qualification. unit, integration and native geometry checks prove the shared rule, native feature history and formed geometry; a post-build flat-pattern inspection proves recoverability of the developed blank.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `false`

The formed bounding box does not prove sheet thickness, the Ø6 cutout or that the upright region came from a native bend. Volume and native sheet history/flat-pattern evidence are required.

## Reference notes

- **build123d** — The pinned build123d 0.12.0 reference uses make_brake_formed for an independent final-geometry comparison. Its newer BuildSheet/bend API is design input only and is not silently substituted into the pinned reference runtime.
- **CadQuery** — Independent final geometry is built from flat and bent solid envelopes; CadQuery does not provide the same native sheet-history contract.
- **PythonSCAD** — Constructive geometry independently represents the formed envelope and through hole; native sheet rules/history remain SolidCraft-only evidence.
- **pyBOSL2** — Constructive geometry independently represents the formed envelope and through hole; native sheet rules/history remain SolidCraft-only evidence.
