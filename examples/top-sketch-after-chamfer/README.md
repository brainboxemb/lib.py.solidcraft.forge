# TOP Sketch after chamfer

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `features`

## Goal

Verify that a TOP-attached Sketch still selects the resulting planar +Z face after a native chamfer changes the body's topology.

## Forge API

Box(...).chamfer(..., edges=Edges.VERTICAL); with Sketch(on=plate, parent=Anchor.TOP): Circle2D(...); cut through all

## Forge model

One 100 x 70 x 10 mm plate, four 8 mm plan-view corner chamfers, then one native TOP-attached Sketch containing a centered 12 mm through hole.

## How Forge builds it in SolidCraft

Forge emits solid.chamfer before model.faces. Replay selects the largest +Z planar face by plane_normal and area, tolerating only tiny numeric-vector noise from the native kernel, then passes its point/index to face-attached sketch.create.

## SolidCraft result

SolidCraft 0.42 builds one chamfered plate with one centered through hole. The Top hole Sketch remains a solved feature attached to the actual post-chamfer top face.

## Saved-design test

No saved-design mutation in this fixture; it isolates stable face lookup after topology-changing native features.

## Reference notes

- **PythonSCAD** — Independent CSG reference cuts the four corner wedges before subtracting the central through hole.
- **CadQuery** — Independent feature reference applies a vertical-edge chamfer before creating the top-face hole.
- **build123d** — Independent builder reference applies the same feature order: Box, vertical-edge chamfer, top-face hole.
