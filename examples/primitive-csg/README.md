# Primitive CSG

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `fundamentals`

## Goal

Qualify direct primitive/CSG modelling independently of feature-history geometry: Sphere and Box union, translated primitives, one native X-axis Cylinder cut and intersection.

## Forge API

Sphere(); Box(...).move(...); Cylinder(..., axis=Axis.X).at(...); + / - / &

## Forge model

A Shape CSG tree rooted in Sphere so Forge deliberately selects the direct CSG compiler instead of the feature-history Box compiler.

## How Forge builds it in SolidCraft

solid.sphere(new), solid.box(join), one X-axis solid.cylinder(cut), then solid.box(intersect).

## SolidCraft result

SolidCraft accepts the complete CSG command path, produces one valid clipped body and evaluates the native timeline without errors.

## Saved-design test

No saved-design mutation in this case; it isolates primitive CSG lowering. Parametric edits are covered by dedicated saved-design cases.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `false`

Many different Boolean results can share this envelope. Surface probes must prove the surviving sphere, bore, clipped box and unioned extension.

## Reference notes

- **OpenSCAD** — Closest to ordinary union()/difference()/intersection() with translate()/rotate() around primitives.
- **PythonSCAD** — Useful comparison for Python objects and operators while Forge still delegates all geometry to SolidCraft.
