# Explicit rounded-rectangle sketch pad

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `features`

## Goal

Qualify RoundedRectangle2D in the explicit named Sketch API using true native rounded-rectangle sketch geometry.

## Forge API

with Sketch(name='Rounded pad', on=body): add(RoundedRectangle2D(...)); body + sketch.extrude(...)

## Forge model

One 80 x 60 x 5 mm base plate plus a centered 40 x 30 mm rounded-rectangle pad with 5 mm corner radius and 8 mm height.

## How Forge builds it in SolidCraft

The named explicit Sketch emits one sketch.rectangle.rounded with true arc corners, then a native solid.extrude(operation='join').

## SolidCraft result

The result is one joined body: an 80 x 60 x 5 mm base plate with a centered 40 x 30 x 8 mm rounded pad on top. The Rounded pad sketch has one closed profile made from four straight edges and four corner arcs. SolidCraft 0.42 also adds one construction diagonal between opposite arc centres; that construction line is not part of the profile.

## Saved-design test

No saved-design mutation in this fixture; it isolates explicit rounded-rectangle sketch geometry and native join extrusion.

## Reference notes

- **SolidCraft** — Native rounded sketch rectangles preserve true arc geometry and remain inspectable in the saved sketch.
- **PythonSCAD** — The explicit Sketch scope keeps 2D profile authoring separate from the subsequent 3D extrusion.
